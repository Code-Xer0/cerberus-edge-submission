#!/usr/bin/env python3
"""Read-only host status snapshot for the authenticated Ragnar static route.

This process does not configure links, firewall, Docker, or Ragnar. It copies one
atomic JSON snapshot into the already-running container; its timer survives a
container replacement and restores the compiled UI without rebuilding Ragnar.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ROOT = Path('/opt/cerberus-edge')
DIST = ROOT / 'dist'
TARGET = '/opt/ragnar/web/cerberus-edge'
LANDING = '/opt/ragnar/web/index_modern.html'
LEGACY = '/opt/ragnar/web/index_modern_legacy.html'


def run(*args, timeout=8):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def systemd(name):
    result = run('systemctl', 'is-active', name)
    if result is None:
        return 'unknown'
    return 'online' if result.returncode == 0 else 'offline'


def addr(interface):
    result = run('ip', '-j', '-4', 'addr', 'show', 'dev', interface)
    if not result or result.returncode:
        return None
    try:
        return next((a.get('local') for x in json.loads(result.stdout)
                     for a in x.get('addr_info', []) if a.get('scope') == 'global'), None)
    except (ValueError, KeyError):
        return None


def observed_link_state(operstate, address, service_state=None, present=True):
    if not present or service_state == 'offline' or operstate == 'down':
        return 'offline'
    if operstate == 'up':
        return 'online'
    if operstate == 'unknown' and address:
        return 'online'  # Virtual link with an address; reachability still unverified.
    return 'unknown'


def link(name, interface, service=None):
    address = addr(interface)
    device = Path('/sys/class/net') / interface
    try:
        operstate = (device / 'operstate').read_text().strip()
    except OSError:
        operstate = 'unknown'
    state = observed_link_state(operstate, address, systemd(service) if service else None, device.exists())
    driver = device / 'device/driver'
    phy = device / 'phy80211'
    return {'name': name, 'interface': interface, 'address': address, 'state': state,
            'driver': driver.resolve().name if driver.exists() else None,
            'phy': phy.resolve().name if phy.exists() else None}


def hardware(name, path, detail):
    return {'name': name, 'state': 'online' if Path(path).exists() else 'offline', 'detail': detail}


def interface_inventory():
    known = [('Ethernet', 'end0', None), ('Wi-Fi uplink', 'wld0', None),
             ('Access point', 'ragnar-ap', 'cerberus-hostapd'), ('Tailscale', 'tailscale0', 'tailscaled')]
    result = [link(name, interface, service) for name, interface, service in known]
    names = {item['interface'] for item in result}
    for interface in sorted(Path('/sys/class/net').iterdir()):
        if interface.name not in names:
            result.append(link('Additional interface ' + interface.name, interface.name))
    return result


def radio_inventory():
    root = Path('/sys/class/ieee80211')
    result = []
    if root.exists():
        for phy in sorted(root.iterdir()):
            driver = phy / 'device/driver'
            result.append({'name': 'Wireless radio ' + phy.name, 'state': 'online',
                           'driver': driver.resolve().name if driver.exists() else None,
                           'detail': 'Detected PHY only; container mapping and operation unverified'})
    return result


def vitals():
    result = {'cpu_count': os.cpu_count()}
    try:
        result['uptime_seconds'] = float(Path('/proc/uptime').read_text().split()[0])
        result['load_1m'] = os.getloadavg()[0]
        memory = {}
        for line in Path('/proc/meminfo').read_text().splitlines():
            key, value = line.split(':', 1)
            if key in ('MemTotal', 'MemAvailable'):
                memory['total_bytes' if key == 'MemTotal' else 'available_bytes'] = int(value.split()[0]) * 1024
        result['memory'] = memory
        disk = os.statvfs('/')
        result['root_disk'] = {'total_bytes': disk.f_blocks * disk.f_frsize,
                               'available_bytes': disk.f_bavail * disk.f_frsize}
    except (OSError, ValueError, IndexError):
        pass
    try:
        result['temperature_c'] = int(Path('/sys/class/thermal/thermal_zone0/temp').read_text()) / 1000
    except (OSError, ValueError):
        pass
    return result


def snapshot():
    names = ['ragnar', 'docker', 'cerberus-agent-pi5', 'cerberus-interface', 'cerberus-hostapd',
             'cerberus-dhcp', 'r2-gateway', 'cerberus-nm-bridge', 'cerberus-firewall.timer',
             'tailscaled', 'talos-host-guard']
    services = [{'name': n, 'state': systemd(n)} for n in names]
    nft = run('nft', '-j', 'list', 'tables')
    tables = []
    if nft and nft.returncode == 0:
        try:
            tables = [x['table']['name'] for x in json.loads(nft.stdout).get('nftables', []) if 'table' in x]
        except (ValueError, KeyError):
            pass
    expected = {'talos_host_guard', 'cerberus_guard', 'cerberus_nat'}
    firewall = {'state': 'online' if expected.issubset(set(tables)) else 'warning', 'tables': sorted(tables)}
    inspect = run('docker', 'inspect', 'ragnar', '--format', '{{json .HostConfig.Privileged}}|{{.Config.Image}}')
    container = {'state': 'offline', 'privileged': None}
    if inspect and inspect.returncode == 0:
        values = inspect.stdout.strip().split('|', 1)
        container = {'state': 'online', 'privileged': values[0] == 'true',
                     'image': values[1] if len(values) > 1 else None}
    agent = {'state': 'unknown', 'node_mode': None, 'workers': None, 'model': 'off', 'containment': None}
    try:
        with urllib.request.urlopen('http://127.0.0.1:8766/api/health', timeout=3) as response:
            health = json.load(response)
        agent = {'state': 'online' if health.get('status') == 'ok' else 'warning',
                 'node_mode': health.get('node_mode'), 'workers': None,
                 'model': health.get('agent', {}).get('mode'),
                 'containment': health.get('policy', {}).get('enabled')}
    except (OSError, ValueError):
        agent['state'] = 'offline' if systemd('cerberus-agent-pi5') == 'offline' else 'warning'
    model = Path('/proc/device-tree/model')
    model_name = model.read_bytes().decode(errors='replace').strip('\0') if model.exists() else 'Unknown hardware'
    return {
        'schema': 'cerberus.edge-status.v1',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'hostname': os.uname().nodename, 'model': model_name, 'vitals': vitals(),
        'services': services,
        'links': interface_inventory(),
        'hardware': radio_inventory() + [hardware('Client AP interface', '/sys/class/net/ragnar-ap', 'Virtual radio interface'),
                     hardware('Bluetooth controller', '/sys/class/bluetooth/hci0', 'Availability only'),
                     hardware('Video capture', '/dev/video0', 'Device present; container mapping unverified'),
                     hardware('I²C bus', '/dev/i2c-1', 'Device present; container mapping unverified'),
                     hardware('GPIO chip', '/dev/gpiochip0', 'Device present; container mapping unverified')],
        'firewall': firewall, 'container': container, 'agent': agent,
        'notes': ['Ragnar retains its existing privileged container and local shims.',
                  'Worker and model operation require explicit endpoint evidence.',
                  'Fleet enrollment and reporting require independently verified configuration.']
    }


def main():
    if not (DIST / 'index.html').is_file():
        raise SystemExit('compiled UI missing')
    ROOT.mkdir(exist_ok=True)
    payload = snapshot()
    with tempfile.NamedTemporaryFile('w', dir=ROOT, prefix='edge-status-', suffix='.json', delete=False) as f:
        json.dump(payload, f, separators=(',', ':'))
        tmp = f.name
    os.replace(tmp, ROOT / 'edge-status.json')
    check = run('docker', 'inspect', 'ragnar', '--format', '{{.State.Running}}')
    if not check or check.returncode or check.stdout.strip() != 'true':
        raise SystemExit('Ragnar container not running; snapshot retained on host')
    local_digest = hashlib.sha256((DIST / 'index.html').read_bytes()).hexdigest()
    existing = run('docker', 'exec', 'ragnar', 'sha256sum', TARGET + '/index.html')
    remote_digest = existing.stdout.split()[0] if existing and existing.returncode == 0 else None
    if remote_digest != local_digest:
        run('docker', 'exec', 'ragnar', 'mkdir', '-p', TARGET)
        copied = run('docker', 'cp', str(DIST) + '/.', 'ragnar:' + TARGET, timeout=30)
        if not copied or copied.returncode:
            raise SystemExit('compiled UI copy failed')
    copied = run('docker', 'cp', str(ROOT / 'edge-status.json'), 'ragnar:' + TARGET + '/edge-status.json')
    if not copied or copied.returncode:
        raise SystemExit('status copy failed')
    marker = run('docker', 'exec', 'ragnar', 'grep', '-q', 'cerberus-edge-entrypoint', LANDING)
    if not marker or marker.returncode:
        saved = run('docker', 'exec', 'ragnar', 'test', '-f', LEGACY)
        if not saved or saved.returncode:
            backup = run('docker', 'exec', 'ragnar', 'cp', LANDING, LEGACY)
            if not backup or backup.returncode:
                raise SystemExit('legacy dashboard backup failed; landing unchanged')
        switched = run('docker', 'cp', str(ROOT / 'entrypoint.html'), 'ragnar:' + LANDING)
        if not switched or switched.returncode:
            raise SystemExit('landing switch failed; legacy dashboard preserved')


if __name__ == '__main__':
    main()
