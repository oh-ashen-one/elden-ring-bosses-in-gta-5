#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Install a verified private candidate into an existing active GTA mod profile.

No game launch, account/registry/save edits or retail-file writes. Uses the
profile manager's mutation lock, same-directory atomic file replacement and a
rollback journal. Preserve the backup until the owner accepts the new build.
"""
import argparse
import copy
import fcntl
import json
import os
import shutil
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from profile_manager import digest, ensure_game_stopped, write_state
from verify_candidate import REQUIRED, payload_path, verify

TOOLS = ('profile_manager.py','launch_owner.py','verify_candidate.py','upgrade_profile.py')


def require_verified(bundle, root=None):
    result=verify(bundle,root)
    if not result['ok']:raise RuntimeError('; '.join(result['issues']))
    return result


def upgrade(candidate, bundle, root):
    candidate,bundle,root=(Path(p).resolve() for p in (candidate,bundle,root))
    if candidate==bundle or candidate.is_relative_to(bundle):raise ValueError('Candidate must be separate from the installed package')
    if not root.is_dir():raise ValueError('Existing profile root required')
    with (root/'profile.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ensure_game_stopped()
        before=require_verified(bundle,root);require_verified(candidate)
        state_path=root/'profile-state.json';old_state=json.loads(state_path.read_text())
        profile=Path(old_state['profile']).resolve();retail=Path(old_state['retail']).resolve()
        if profile!=root/'Game' or retail!=root/'Retail':raise ValueError('Unexpected profile layout; preserving it')
        new_manifest=json.loads((candidate/'manifest.json').read_text())
        old_manifest=json.loads((bundle/'manifest.json').read_text())
        shortcuts=list(new_manifest.get('shortcut_files',{}))
        if any(p not in ('Check Elden Los Santos.command','Play Elden Los Santos.command') for p in shortcuts):raise ValueError('Unexpected shortcut update')
        if set(new_manifest['files'])!=REQUIRED or set(old_manifest['files'])!=REQUIRED:
            raise ValueError('Upgrade supports the exact six-file encounter payload only')
        sidecars=[*(Path('Tools')/name for name in TOOLS),Path('START-HERE.md'),Path('VERIFICATION.json'),*(Path(name) for name in shortcuts)]
        sidecars_match=all((candidate/p).is_file() and (bundle/p).is_file() and digest(candidate/p)==digest(bundle/p)
                           and stat.S_IMODE((candidate/p).stat().st_mode)==stat.S_IMODE((bundle/p).stat().st_mode) for p in sidecars)
        if old_state.get('candidate')==new_manifest.get('candidate') and old_state['files']==new_manifest['files'] and digest(bundle/'manifest.json')==digest(candidate/'manifest.json') and sidecars_match and old_state.get('source_commit')==new_manifest.get('source_commit'):
            return {'status':'already_installed','candidate':new_manifest.get('candidate'),'game_launched':False}
        token=uuid.uuid4().hex
        backup=bundle/'Backups'/('upgrade-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+token[:8])
        backup.mkdir(parents=True)
        journal={'status':'preparing','from_candidate':old_manifest.get('candidate'),'to_candidate':new_manifest.get('candidate'),
                 'profile_root':str(root),'bundle':str(bundle),'state_before':old_state,'files':[],
                 'game_launched':False,'retail_modified':False}
        journal_path=backup/'upgrade-journal.json';staged=[];changed=[]
        def add(source,destination):
            source,destination=Path(source),Path(destination)
            if source.is_symlink() or not source.is_file():raise ValueError('Missing or linked update input: '+str(source))
            if destination.is_symlink() or not destination.resolve().is_relative_to(profile if destination.is_relative_to(profile) else bundle):
                raise ValueError('Unsafe destination: '+str(destination))
            sha=digest(source)
            mode=stat.S_IMODE(source.stat().st_mode)&0o777
            if destination.exists() and digest(destination)==sha and stat.S_IMODE(destination.stat().st_mode)==mode:return
            destination.parent.mkdir(parents=True,exist_ok=True)
            entry={'destination':str(destination),'sha256':sha,'existed':destination.exists()}
            if entry['existed']:
                saved=backup/'files'/str(len(journal['files']));saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(destination,saved);entry['backup']=str(saved);entry['previous_sha256']=digest(saved)
            temporary=destination.with_name(destination.name+'.upgrade-'+token)
            try:
                with source.open('rb') as inp,temporary.open('xb') as out:
                    shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
                # Finder needs executable .command shortcuts after replacement.
                # Preserve ordinary permissions, never set-id/sticky bits.
                temporary.chmod(mode)
                if digest(temporary)!=sha:raise IOError('Staging checksum mismatch')
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
            entry['temporary']=str(temporary);staged.append(entry);journal['files'].append(entry)
        try:
            for name in sorted(REQUIRED):
                source=payload_path(candidate/'payload',name)
                add(source,payload_path(profile,name));add(source,payload_path(bundle/'payload',name))
            for name in TOOLS:add(candidate/'Tools'/name,bundle/'Tools'/name)
            for name in ('START-HERE.md','VERIFICATION.json'):
                add(candidate/name,bundle/name)
            for name in shortcuts:add(candidate/name,bundle/name)
            # Package manifest commits after its files; profile phase remains
            # upgrading until both copies and helper metadata are consistent.
            add(candidate/'manifest.json',bundle/'manifest.json')
            write_state(journal_path,journal)
            ensure_game_stopped()
            if json.loads(state_path.read_text())!=old_state:raise RuntimeError('Profile changed during staging')
            require_verified(bundle,root);require_verified(candidate)
            pending=copy.deepcopy(old_state);pending['phase']='upgrading';pending['upgrade_journal']=str(journal_path)
            write_state(state_path,pending);journal['status']='applying';write_state(journal_path,journal)
            for entry in staged:
                ensure_game_stopped()
                os.replace(entry['temporary'],entry['destination']);changed.append(entry)
            state=copy.deepcopy(old_state)
            state.update(phase='active',candidate=new_manifest['candidate'],files=new_manifest['files'],
                         source_commit=new_manifest.get('source_commit'),gta_runtime_verified=False,
                         creature_spawn_verified=False,last_upgrade_journal=str(journal_path))
            state.pop('upgrade_journal',None);write_state(state_path,state)
            after=require_verified(bundle,root)
            if after['retail_exe_sha256']!=before['retail_exe_sha256']:raise RuntimeError('Retail executable drift')
            journal['status']='complete';write_state(journal_path,journal)
            return {'status':'installed','candidate':state['candidate'],'backup':str(backup),
                    'changed_files':len(changed),'payload_files_verified':len(after['files']),
                    'game_launched':False,'retail_modified':False}
        except BaseException:
            # Never mutate files back underneath a newly started game. The
            # non-active phase/receipt preserves a visible recovery boundary.
            try:ensure_game_stopped()
            except BaseException:
                failed=copy.deepcopy(old_state);failed['phase']='upgrade_recovery_required';failed['upgrade_journal']=str(journal_path)
                write_state(state_path,failed);journal['status']='recovery_required';write_state(journal_path,journal)
                raise RuntimeError('Game started during update; quit it before recovering from '+str(journal_path))
            for entry in reversed(changed):
                dest=Path(entry['destination'])
                if entry['existed']:
                    temporary=dest.with_name(dest.name+'.rollback-'+token);shutil.copy2(entry['backup'],temporary);os.replace(temporary,dest)
                else:dest.unlink(missing_ok=True)
            write_state(state_path,old_state);journal['status']='rolled_back';write_state(journal_path,journal)
            raise
        finally:
            for entry in staged:Path(entry['temporary']).unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--bundle',type=Path,default=Path.home()/'Applications/EldenLosSantosPreview')
    p.add_argument('--root',type=Path,default=Path.home()/'Library/Application Support/EldenLosSantos')
    a=p.parse_args();print(json.dumps(upgrade(a.candidate,a.bundle,a.root),indent=2))


if __name__=='__main__':main()
