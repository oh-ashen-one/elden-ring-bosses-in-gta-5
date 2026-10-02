#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only pre-play verification of a private GTA candidate and optional profile.

Never loads a plugin, starts a game, changes a profile or edits registry/saves.
Hash agreement is packaging evidence, not a gameplay or visual acceptance test.
"""
import argparse
import json
import re
import struct
import subprocess
from pathlib import Path, PurePosixPath

from profile_manager import EXPECTED_VERSION, RUNTIME_FILES, digest, version

REQUIRED = RUNTIME_FILES | {'newmods/dlcpacks/ergt/dlc.rpf', 'newmods/common/data/dlclist.xml'}


def payload_path(root, name):
    relative = PurePosixPath(name)
    if not name or '\\' in name or relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Invalid payload path: {name}')
    if name not in RUNTIME_FILES and (not relative.parts or relative.parts[0] != 'newmods'):
        raise ValueError(f'Unexpected payload path: {name}')
    target = root.joinpath(*relative.parts)
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Payload escapes its directory: {name}')
    return target


def verify(bundle, profile_root=None, source=None):
    bundle = Path(bundle)
    manifest = json.loads((bundle / 'manifest.json').read_text())
    issues = []
    report = {'candidate': manifest.get('candidate'), 'source_commit': manifest.get('source_commit'),
              'gameplay_verified_by_this_check': False, 'files': [], 'issues': issues}
    files = manifest.get('files', {})
    if not isinstance(files, dict) or not files:
        raise ValueError('Candidate has no payload manifest')
    missing = REQUIRED - files.keys()
    if missing:
        issues.append('Required payloads absent from manifest: ' + ', '.join(sorted(missing)))
    if manifest.get('expected_game_version') != '.'.join(map(str, EXPECTED_VERSION)):
        issues.append('Manifest game version differs from the supported Legacy build')
    state = None
    profile = None
    if profile_root is not None:
        profile_root = Path(profile_root)
        state = json.loads((profile_root / 'profile-state.json').read_text())
        profile = Path(state['profile'])
        if state.get('phase') != 'active' or Path(state['install']).resolve() != profile.resolve():
            issues.append('Mod profile is not active at the configured install path')
        if state.get('files') != files:
            issues.append('Installed profile manifest differs from this candidate')
        for label, path in [('retail', Path(state['retail']) / 'GTA5.exe'), ('profile', profile / 'GTA5.exe')]:
            try:
                actual = digest(path)
                report[label + '_exe_sha256'] = actual
                if actual != state['original_exe_sha256']:
                    issues.append(label + ' game executable differs from the preserved original')
                if version(path) != EXPECTED_VERSION:
                    issues.append(label + ' game executable has an unsupported version')
            except (OSError, ValueError, struct.error) as error:
                issues.append(f'Cannot verify {label} executable: {error}')
    roots = {'package': bundle / 'payload'}
    if profile is not None:
        roots['profile'] = profile
    for name, expected in sorted(files.items()):
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError(f'Invalid SHA-256 for {name}')
        row = {'name': name, 'expected_sha256': expected}
        for label, root in roots.items():
            target = payload_path(root, name)
            try:
                actual = digest(target)
                row[label] = {'sha256': actual, 'matches': actual == expected, 'bytes': target.stat().st_size}
                if actual != expected:
                    issues.append(f'{label} checksum mismatch: {name}')
            except OSError as error:
                row[label] = {'matches': False, 'error': str(error)}
                issues.append(f'{label} payload unavailable: {name}')
        report['files'].append(row)
    for label, root in roots.items():
        if (root / 'EldenLosSantosProbe.asi').exists():
            issues.append(f'{label} includes both encounter and diagnostic plugins; their hotkeys overlap')
        queued = (root / 'EldenLosSantos.import-check.request').exists()
        report[label + '_automatic_import_request_queued'] = queued
        if queued:
            issues.append(f'{label} has a queued automatic import diagnostic')
    if source is not None:
        source = Path(source)
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        report['checked_source_commit'] = head
        if manifest.get('source_commit') != head:
            issues.append('Candidate source commit does not match the inspected checkout')
        dirty = subprocess.check_output(['git', '--no-optional-locks', '-C', str(source), 'status',
                                         '--porcelain', '--untracked-files=normal', '--', 'gta'], text=True).strip()
        report['checked_source_gta_dirty'] = bool(dirty)
        if dirty:
            issues.append('Inspected GTA source contains uncommitted changes')
        for name in ('launch_owner.py', 'profile_manager.py'):
            packaged = bundle / 'Tools' / name
            original = source / 'gta/tools' / name
            try:
                if digest(packaged) != digest(original):
                    issues.append('Packaged tool differs from inspected source: ' + name)
            except OSError:
                issues.append('Packaged tool unavailable: ' + name)
    report['ok'] = not issues
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--profile-root', type=Path)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.bundle, args.profile_root, args.source)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report = {'ok': False, 'gameplay_verified_by_this_check': False, 'issues': [str(error)]}
    print(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
