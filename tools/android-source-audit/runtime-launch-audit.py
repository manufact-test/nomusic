#!/usr/bin/env python3
"""Lab-only driver for the signed publisher APK. No app privileges are granted.

ADB/UI access belongs to the test harness, not to a production CELIKOM app.
No account login, TLS interception, private app data or source APK modification.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

BASE_HASH = 'a3e4d3aedd24ea0370ead4f25c4f0085a1f43b94e458ee949da86797df27fc61'

def run(adb, *args, timeout=45):
    result = subprocess.run([adb, '-s', 'emulator-5554', *args], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    if result.returncode:
        raise RuntimeError('adb_command_failed:' + args[0])
    return result.stdout

def capture(adb, destination, name):
    run(adb, 'shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=60)
    data = run(adb, 'shell', 'cat', '/sdcard/window.xml')
    root = ET.fromstring(data)
    rows = []
    texts = []
    for node in root.iter('node'):
        attrs = node.attrib
        texts.append((attrs.get('text', '') + ' ' + attrs.get('content-desc', '')).casefold())
        if attrs.get('package') in ('ru.yandex.music', 'com.android.permissioncontroller'):
            rows.append({key: attrs.get(key, '') for key in ('resource-id', 'class', 'package', 'clickable', 'enabled', 'bounds')})
    combined = ' '.join(texts)
    state = {'nodes': rows,
             'login_controls_present': any(word in combined for word in ('войти', 'вход', 'log in', 'sign in')),
             'share_controls_present': any(word in combined for word in ('поделиться', 'share')),
             'network_error_text_present': any(word in combined for word in ('нет подключения', 'нет соединения', 'no connection', 'no internet'))}
    (destination / (name + '.json')).write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n')
    return state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--xapk', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = pathlib.Path(args.output); out.mkdir(parents=True, exist_ok=True)
    packages = out / 'publisher-packages'; packages.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.xapk) as archive:
        base = archive.read('ru.yandex.music.apk')
        if hashlib.sha256(base).hexdigest() != BASE_HASH:
            raise RuntimeError('publisher_build_mismatch')
        paths = []
        for name in ('ru.yandex.music.apk', 'config.arm64_v8a.apk', 'config.en.apk', 'config.ru.apk', 'config.xhdpi.apk'):
            path = packages / name; path.write_bytes(archive.read(name)); paths.append(str(path.resolve()))
    report = {'schema': 1, 'base_sha256': BASE_HASH, 'lab_privileged_driver': True,
              'ordinary_app_exact_id_verified': False, 'replacement_verified': False, 'account_login_performed': False}
    report['device_abis'] = run(args.adb, 'shell', 'getprop', 'ro.product.cpu.abilist').strip().split(',')
    report['native_bridge'] = run(args.adb, 'shell', 'getprop', 'ro.dalvik.vm.native.bridge').strip()
    run(args.adb, 'install-multiple', '-r', *paths, timeout=180)
    report['publisher_install_verified'] = True
    run(args.adb, 'shell', 'am', 'start', '-W', '-n', 'ru.yandex.music/ru.yandex.music.main.MainScreenActivity')
    time.sleep(8)
    report['initial_screen'] = capture(args.adb, out, 'initial-screen')
    for index, track in enumerate(('142820338', '141103805')):
        run(args.adb, 'shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d',
            'https://music.yandex.ru/track/' + track, '-p', 'ru.yandex.music')
        time.sleep(6)
        report['incoming_track_' + str(index + 1)] = capture(args.adb, out, 'incoming-track-' + str(index + 1))
    # The two URIs are supplied inputs. They never count as observed current IDs.
    report['incoming_links_are_not_current_identity_proof'] = True
    (out / 'runtime-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: value for key, value in report.items() if not key.startswith(('initial_screen', 'incoming_track_'))}))

if __name__ == '__main__':
    main()
