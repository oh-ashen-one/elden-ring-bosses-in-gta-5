#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""One owner-authorized GTA launch under the Studio's actual exclusive GPU lock.

Never stops another process, changes the shared cap, or retries a crashed game.
The lock stays held until the game exits. --check performs reads only.
"""
import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ENGINES = {'unrealeditor', 'unrealgame', 'unity', 'godot', 'blender',
           'gta5.exe', 'gta5_enhanced.exe', 'eldenring.exe', 'darksoulsremastered.exe'}


def processes():
    commands = {}
    for line in subprocess.check_output(['ps', '-axww', '-o', 'pid=,command='], text=True).splitlines():
        pid, command = line.strip().split(None, 1); commands[int(pid)] = command
    result = []
    for line in subprocess.check_output(['ps', '-axww', '-o', 'pid=,stat=,comm='], text=True).splitlines():
        pid, state, executable = line.strip().split(None, 2)
        result.append({'pid': int(pid), 'state': state,
                       'name': executable.replace('\\', '/').split('/')[-1].lower(),
                       'command': commands.get(int(pid), '')})
    return result


def blockers(table, gpu, console, owner, limit=15):
    reasons = []
    if console != owner: reasons.append('Owner desktop is not logged in')
    if gpu is None or not 0 <= gpu < limit: reasons.append(f'GPU must be readable and below {limit} percent')
    for p in table:
        if p['name'] not in ENGINES: continue
        if p['state'].startswith(('E', 'Z')):
            reasons.append(f"Engine {p['pid']} is stuck exiting")
        elif not (p['name'] == 'unrealeditor' and re.search(r'(?i)(?:^|\s)-nullrhi(?:\s|$)', p['command'])):
            reasons.append(f"Another renderer is running: {p['name']} PID {p['pid']}")
    return reasons


def owner_reservation(gpu_root):
    pause = gpu_root / 'PAUSED'
    return pause.exists() and pause.read_text().startswith('owner opening GTA V ')


def preflight(gpu_root, reserved=False):
    output = subprocess.check_output(['ioreg', '-r', '-d', '1', '-c', 'IOAccelerator'], text=True)
    values = [int(x) for x in re.findall(r'"Device Utilization %"\s*=\s*(\d+)', output)]
    gpu = max(values) if values else None
    # The Unreal coordinator can reserve the GPU for Hari by pausing its own
    # queue explicitly for GTA. Leave that pause intact throughout gameplay.
    # Desktop-only utilization on this Studio is ~20%; ordinary perf mode
    # retains its stricter 15% measurement gate. Neither mode admits a renderer.
    reasons = blockers(processes(), gpu, Path('/dev/console').owner(), Path.home().owner(), 30 if reserved else 15)
    if reserved and not owner_reservation(gpu_root): reasons.append('Explicit owner GTA reservation is missing')
    if (gpu_root / 'PAUSED').exists() and not (reserved and owner_reservation(gpu_root)):
        reasons.append('Shared GPU protocol is PAUSED')
    return {'gpu_percent': gpu, 'blockers': reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-root', type=Path, required=True, help='Actual directory used by the other rendering sessions')
    parser.add_argument('--expected-host', required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--owner-reservation', action='store_true', help='Use only after the other session reserves the GPU explicitly for the owner GTA test')
    parser.add_argument('--inside-slot', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if subprocess.check_output(['hostname'], text=True).strip() != args.expected_host:
        raise RuntimeError('Host mismatch; game not launched')
    root = args.gpu_root.resolve(); wrapper = root / 'bin/gpu_slot.py'
    if not wrapper.is_file() or not (root / 'locks').is_dir():
        raise RuntimeError('Actual shared GPU protocol not found; no fallback lock directory')
    check = preflight(root, args.owner_reservation)
    print(json.dumps(check), flush=True)
    if args.check: return 0 if not check['blockers'] else 75
    if check['blockers']: return 75
    if not args.inside_slot:
        env = dict(os.environ)
        for key in list(env):
            if key.startswith('GPU_SLOT_') or key == 'GPU_LOCK_DIR': env.pop(key)
        env.update(GPU_SLOT_DIR=str(root), GPU_SLOT_PERF_MAX_HOLD='0',
                   GPU_SLOT_UTIL_MAX='15', GPU_SLOT_CALM_SECONDS='10', GPU_SLOT_SAMPLE_INTERVAL='15')
        if args.owner_reservation:
            # Cooperatively use the SAME exclusive lock as the paused Unreal
            # queue. The coordinator's owner reservation gives this one launch
            # priority; no pause file, waiter or other holder is changed.
            with (root / 'locks/perf.lock').open('a') as lock:
                try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: return 75
                holder = root / 'holders' / f'perf-{os.getpid()}.json'
                record = {'pid': os.getpid(), 'start': subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip(),
                          'class':'perf','slot':'perf','label':'gta-owner-exclusive','state':'settling',
                          'since_epoch':time.time(),'cmd':'GTA owner test; exclusive reservation, not a performance measurement'}
                holder.write_text(json.dumps(record))
                try:
                    for _ in range(6):
                        check = preflight(root, True)
                        if check['blockers']: print(json.dumps(check),flush=True); return 75
                        time.sleep(2)
                    record['state']='running';holder.write_text(json.dumps(record))
                    env['GPU_SLOT_HELD']='perf'
                    return subprocess.run([sys.executable,str(Path(__file__).resolve()),'--gpu-root',str(root),
                        '--expected-host',args.expected_host,'--owner-reservation','--inside-slot'],env=env).returncode
                finally:
                    holder.unlink(missing_ok=True)
                    fcntl.flock(lock,fcntl.LOCK_UN)
        # Existing shared perf lock is exclusive; its normal ten-second idle
        # gate runs before this file is invoked again. No cap is raised.
        command = [sys.executable, str(wrapper), 'perf', '--label', 'gta-owner-exclusive', '--timeout', '60', '--',
                   sys.executable, str(Path(__file__).resolve()), '--gpu-root', str(root),
                   '--expected-host', args.expected_host, '--inside-slot']
        return subprocess.run(command, env=env).returncode
    if os.environ.get('GPU_SLOT_HELD') != 'perf' or os.environ.get('GPU_SLOT_DIR') != str(root):
        raise RuntimeError('An exclusive shared GPU slot is required')
    # The inner preflight above closes the gap between queueing and launch.
    from profile_manager import ensure_game_stopped, digest
    ensure_game_stopped()
    local = Path.home() / 'Library/Application Support/EldenLosSantos'
    state = json.loads((local / 'profile-state.json').read_text())
    if state['phase'] != 'active' or Path(state['install']).resolve() != Path(state['profile']).resolve():
        raise RuntimeError('Expected mod profile is not active')
    for name, sha in state['files'].items():
        if digest(Path(state['profile']) / name) != sha: raise RuntimeError('Mod payload checksum mismatch')
    run = local / 'launch'; run.mkdir(exist_ok=True)
    def report(status, **extra):
        record = {'status': status, 'time': time.time(), **extra}
        (run / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record), flush=True)
    report('requesting-steam-launch-exclusive', gpu_root=str(root))
    wine = Path.home() / 'Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine'
    with (run / 'crossover.log').open('a') as log:
        subprocess.Popen([str(wine), '--bottle', 'Steam', '--no-gui', '--no-wait', '--cx-app',
                          r'C:\Program Files (x86)\Steam\steam.exe', '-applaunch', '271590',
                          '-windowed', '-width', '1920', '-height', '1080'],
                         stdout=log, stderr=log, start_new_session=True)
    started = time.monotonic()
    while True:
        table = processes(); games = [p['pid'] for p in table if p['name'] == 'gta5.exe']
        if games: break
        # A login/launcher prompt must keep the reservation until owner action.
        if time.monotonic() - started > 600 and not any(p['name'] == 'playgtav.exe' for p in table):
            report('launch-did-not-start-game'); return 1
        time.sleep(2)
    report('game-running', pids=games)
    while any(p['name'] == 'gta5.exe' for p in processes()): time.sleep(5)
    report('game-exited-no-relaunch')
    return 0


if __name__ == '__main__': raise SystemExit(main())
