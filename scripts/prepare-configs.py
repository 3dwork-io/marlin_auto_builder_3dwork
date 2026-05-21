#!/usr/bin/env python3
"""
Marlin Build Configurator — MarlinBuilds-style config.ini approach.

Downloads official configs from MarlinFirmware/Configurations for a given
board and version, applies config.ini overrides, and produces version-
compatible Configuration.h + Configuration_adv.h for building.

The generated .h files are saved to output-dir, representing the EXACT
configuration used for the build — these can be committed as reference.

Usage:
    python3 prepare-configs.py \
        --board Creality/Ender-3/CrealityV1 \
        --version 2.1.2.7 \
        --output-dir Firmware/Configuration/Creality/Ender-3/CrealityV1 \
        --custom-dir Firmware/Configuration/Creality/Ender-3/CrealityV1
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

CONFIG_BASE_URL = "https://raw.githubusercontent.com/MarlinFirmware/Configurations"
BLOCKLIST = {
    'CONFIGURATION_H_VERSION',
    'CONFIGURATION_ADV_H_VERSION',
    'CONFIG_EXAMPLES_DIR',
}

SECTION_MAP = {
    'MOTHERBOARD': 'machine',
    'X_BED_SIZE': 'geometry', 'Y_BED_SIZE': 'geometry',
    'X_MIN_POS': 'geometry', 'Y_MIN_POS': 'geometry',
    'Z_MIN_POS': 'geometry', 'Z_MAX_POS': 'geometry',
    'MIN_SOFTWARE_ENDSTOPS': 'geometry', 'MAX_SOFTWARE_ENDSTOPS': 'geometry',
    'DEFAULT_AXIS_STEPS_PER_UNIT': 'motion',
    'DEFAULT_MAX_FEEDRATE': 'motion', 'DEFAULT_MAX_ACCELERATION': 'motion',
    'DEFAULT_ACCELERATION': 'motion', 'DEFAULT_TRAVEL_ACCELERATION': 'motion',
    'DEFAULT_RETRACT_ACCELERATION': 'motion',
    'JUNCTION_DEVIATION_MM': 'motion', 'DEFAULT_MINIMUMFEEDRATE': 'motion',
    'DEFAULT_MINTRAVELFEEDRATE': 'motion', 'MINIMUM_PLANNER_SPEED': 'motion',
    'DEFAULT_MINSEGMENTTIME': 'motion',
    'DEFAULT_EJERK': 'motion', 'INVERT_X_DIR': 'motion',
    'INVERT_Y_DIR': 'motion', 'INVERT_Z_DIR': 'motion',
    'INVERT_E0_DIR': 'extruder',
    'X_HOME_DIR': 'homing', 'Y_HOME_DIR': 'homing', 'Z_HOME_DIR': 'homing',
    'QUICK_HOME': 'homing', 'HOMING_FEEDRATE_MM_M': 'homing',
    'EXTRUDERS': 'extruder', 'DEFAULT_NOMINAL_FILAMENT_DIA': 'extruder',
    'TEMP_SENSOR_0': 'temperature', 'TEMP_SENSOR_BED': 'temperature',
    'HEATER_0_MAXTEMP': 'temperature', 'BED_MAXTEMP': 'temperature',
    'PIDTEMP': 'hotend_temp', 'PIDTEMPBED': 'pid_temp',
    'DEFAULT_Kp': 'hotend_temp', 'DEFAULT_Ki': 'hotend_temp',
    'DEFAULT_Kd': 'hotend_temp',
    'SERIAL_PORT': 'serial', 'BAUDRATE': 'serial',
    'X_DRIVER_TYPE': 'stepper_drivers', 'Y_DRIVER_TYPE': 'stepper_drivers',
    'Z_DRIVER_TYPE': 'stepper_drivers', 'E0_DRIVER_TYPE': 'stepper_drivers',
    'LCD_LANGUAGE': 'interface', 'SDSUPPORT': 'interface',
    'USE_XMIN_PLUG': 'endstops', 'USE_YMIN_PLUG': 'endstops',
    'USE_ZMIN_PLUG': 'endstops', 'USE_XMAX_PLUG': 'endstops',
    'USE_YMAX_PLUG': 'endstops', 'USE_ZMAX_PLUG': 'endstops',
    'STRING_CONFIG_H_AUTHOR': 'info', 'CUSTOM_MACHINE_NAME': 'serial',
}
DEFAULT_SECTION = 'extras'


def curl_download(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        parts = url.split('/', 3)
        if len(parts) == 4:
            base = '/'.join(parts[:3])
            path = parts[3]
            encoded_path = urllib.parse.quote(path, safe='/:@!$&\'()*+,;=')
            url = f"{base}/{encoded_path}"
    except:
        pass
    result = subprocess.run(
        ["curl", "-sSL", "--fail", url, "-o", dest_path],
        capture_output=True, text=True
    )
    return result.returncode == 0


def download_official_config(board, version, output_dir):
    branch = f"release-{version}" if not version.startswith('bugfix-') else version
    url_base = f"{CONFIG_BASE_URL}/{branch}/config/examples/{board}"
    files = ['Configuration.h', 'Configuration_adv.h']
    downloaded = []
    for fname in files:
        url = f"{url_base}/{fname}"
        dest = os.path.join(output_dir, fname)
        if curl_download(url, dest):
            print(f"  Downloaded: {fname}")
            downloaded.append(fname)
        else:
            print(f"  Not found: {url}")
    return downloaded


def extract_defines(path):
    defines = {}
    try:
        with open(path) as f:
            for line in f:
                m = re.match(r'^#define\s+(\w+)\s*(.*)', line.strip())
                if m and not line.strip().startswith('//'):
                    defines[m.group(1)] = m.group(2).strip()
    except:
        pass
    return defines


def diff_to_config_ini(custom_dir, official_dir, output_ini_path):
    custom_h = os.path.join(custom_dir, 'Configuration.h')
    official_h = os.path.join(official_dir, 'Configuration.h')
    if not os.path.exists(custom_h) or not os.path.exists(official_h):
        print("  diff: missing custom or official Configuration.h")
        return None

    custom = extract_defines(custom_h)
    official = extract_defines(official_h)

    diffs = {}
    all_keys = set(custom.keys()) | set(official.keys())
    for key in all_keys:
        if key in BLOCKLIST:
            continue
        cv = custom.get(key, '')
        ov = official.get(key, '')
        if cv != ov:
            diffs[key] = cv

    if not diffs:
        print("  diff: no differences found")
        return None

    overrides = {}
    for key, val in diffs.items():
        section = SECTION_MAP.get(key, DEFAULT_SECTION)
        if section not in overrides:
            overrides[section] = {}
        overrides[section][key.lower()] = val

    sections = list(overrides.keys())
    lines = [
        '# Generated by Marlin Auto-Builder (official vs custom diff)\n',
        f'# Board: {os.path.basename(custom_dir)}\n',
        '[config:base]\n',
        f'ini_use_config = {", ".join(sections)}\n',
        '\n',
    ]
    for section in sections:
        lines.append(f'[config:{section}]\n')
        for key, val in overrides[section].items():
            lines.append(f'{key} = {val}\n')
        lines.append('\n')

    with open(output_ini_path, 'w') as f:
        f.writelines(lines)

    print(f"  diff: generated {len(diffs)} overrides across {len(sections)} sections -> {output_ini_path}")
    return output_ini_path


def parse_config_ini(config_ini_path):
    config = {'sections': {}, 'use_config': []}
    current_section = None
    with open(config_ini_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^\[config:(.+)\]$', line)
            if m:
                current_section = m.group(1)
                config['sections'][current_section] = {}
                continue
            if line.startswith('ini_use_config'):
                value = line.split('=', 1)[1].strip()
                config['use_config'] = [x.strip() for x in value.split(',')]
                continue
            if current_section and '=' in line:
                key, value = line.split('=', 1)
                config['sections'][current_section][key.strip()] = value.strip()
    return config


def apply_override(line, define_key, value):
    v = value.strip()
    on = v.lower() in ('on', 'true')
    off = v.lower() in ('off', 'false')
    indent = ' ' * (len(line) - len(line.lstrip()))
    if on:
        return line
    if off:
        newline = line.lstrip()
        if newline.startswith('//'):
            return line
        return '//' + newline

    stripped = line.strip()
    has_dquote = '"' in stripped.split('//')[0] if '//' in stripped else '"' in stripped
    has_brace = '{' in stripped.split('//')[0] if '//' in stripped else '{' in stripped

    if has_dquote:
        return f"{indent}#define {define_key} \"{v}\"\n"
    elif has_brace:
        return f"{indent}#define {define_key} {v}\n"
    else:
        return f"{indent}#define {define_key} {v}\n"


def apply_config_ini(config_ini_path, config_dir):
    if not os.path.exists(config_ini_path):
        return
    config = parse_config_ini(config_ini_path)
    sections = config.get('use_config', [])
    if not sections or sections == ['none']:
        print("  config.ini: no sections to apply")
        return

    for fname in ['Configuration.h', 'Configuration_adv.h']:
        fpath = os.path.join(config_dir, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            lines = f.readlines()
        modified = []
        for line in lines:
            new_line = line
            m = re.match(r'^#define\s+(\w+)', line.strip())
            if m:
                dk = m.group(1)
                for section_name in sections:
                    section = config['sections'].get(section_name, {})
                    for key, val in section.items():
                        if dk.upper() == key.upper():
                            r = apply_override(new_line, dk, val)
                            if r != new_line:
                                new_line = r
                                break
            modified.append(new_line)
        with open(fpath, 'w') as f:
            f.writelines(modified)
        print(f"  Applied {len(sections)} sections to {fname}")


def fix_version_in_file(fpath, target_version_code):
    if not os.path.exists(fpath):
        return
    with open(fpath) as f:
        content = f.read()
    for key in ['CONFIGURATION_H_VERSION', 'CONFIGURATION_ADV_H_VERSION']:
        content = re.sub(
            rf'#define\s+{key}\s+\d+',
            f'#define {key} {target_version_code}',
            content
        )
    with open(fpath, 'w') as f:
        f.write(content)


def get_version_code(version_str):
    """
    Fetch actual MARLIN_HEX_VERSION from Marlin source for this version.
    This is more reliable than computing it from SHORT_BUILD_VERSION,
    as the hex version is sometimes one behind the release (e.g. 2.1.2.7
    uses MARLIN_HEX_VERSION 02010206, not 02010207).
    """
    url = f"https://raw.githubusercontent.com/MarlinFirmware/Marlin/{version_str}/Marlin/src/inc/Version.h"
    try:
        parts = url.split('/', 3)
        base = '/'.join(parts[:3])
        path = parts[3]
        encoded_path = urllib.parse.quote(path, safe='/:@!$&\'()*+,;=')
        encoded_url = f"{base}/{encoded_path}"
        result = subprocess.run(
            ["curl", "-sL", encoded_url],
            capture_output=True, text=True, timeout=15
        )
        match = re.search(r'#define\s+MARLIN_HEX_VERSION\s+(\d+)', result.stdout)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"  Warning: couldn't fetch MARLIN_HEX_VERSION: {e}", file=sys.stderr)

    # Fallback: compute from version string
    parts = version_str.split('.')
    major = int(parts[0]) if len(parts) > 0 else 2
    minor = int(parts[1]) if len(parts) > 1 else 1
    patch = int(parts[2]) if len(parts) > 2 else 2
    build = int(parts[3]) if len(parts) > 3 else 0
    code = major * 1000000 + minor * 10000 + patch * 100 + build
    return f'{code:08d}'


def main():
    parser = argparse.ArgumentParser(description='Prepare Marlin build configs')
    parser.add_argument('--board', required=True, help='Board path (e.g., Creality/Ender-3/CrealityV1)')
    parser.add_argument('--version', required=True, help='Marlin version tag (e.g., 2.1.2.7)')
    parser.add_argument('--output-dir', required=True, help='Directory for final config files')
    parser.add_argument('--custom-dir', help='Path to custom configs (for diff/ini)')
    parser.add_argument('--official-path', help='Official repo board path if different from --board')
    args = parser.parse_args()

    download_path = args.official_path if args.official_path else args.board
    target_version_code = get_version_code(args.version)
    print(f"Preparing configs for {args.board} @ Marlin {args.version} (code: {target_version_code})")
    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Download official configs to TEMP dir
    print("  Step 1: Downloading official configs...")
    tmpdir = tempfile.mkdtemp(prefix='marlin-official-')
    downloaded = download_official_config(download_path, args.version, tmpdir)

    if not downloaded:
        print("  WARNING: No official configs available for this board")
        if args.custom_dir and os.path.isdir(args.custom_dir):
            h_files = [f for f in os.listdir(args.custom_dir) if f.endswith('.h')]
            if h_files:
                print(f"  Using custom configs from {args.custom_dir} (fixing version)")
                for f in h_files:
                    shutil.copy2(os.path.join(args.custom_dir, f), os.path.join(tmpdir, f))
                downloaded = [f for f in h_files if os.path.exists(os.path.join(tmpdir, f))]
            else:
                print("  SKIP: No .h files found in custom dir")
                shutil.rmtree(tmpdir)
                sys.exit(1)
        else:
            print("  SKIP: No custom configs either")
            shutil.rmtree(tmpdir)
            sys.exit(1)

    # Fix version in downloaded/official configs to match target
    for fname in ['Configuration.h', 'Configuration_adv.h']:
        fpath = os.path.join(tmpdir, fname)
        if os.path.exists(fpath):
            fix_version_in_file(fpath, target_version_code)

    # Step 2: Generate or reuse config.ini
    config_ini_path = os.path.join(args.output_dir, 'config.ini')
    existing_ini = os.path.exists(config_ini_path)

    if existing_ini:
        print(f"  Step 2: Using existing config.ini from output dir")
    elif args.custom_dir and os.path.isdir(args.custom_dir) and downloaded:
        custom_h = os.path.join(args.custom_dir, 'Configuration.h')
        if os.path.exists(custom_h):
            print("  Step 2: Generating config.ini from diff (custom vs official)...")
            diff_to_config_ini(args.custom_dir, tmpdir, config_ini_path)

    # Step 3: Apply config.ini overrides to official configs
    print("  Step 3: Applying overrides...")
    if os.path.exists(config_ini_path):
        print(f"  Applying config.ini: {config_ini_path}")
        apply_config_ini(config_ini_path, tmpdir)
    else:
        print("  No config.ini overrides to apply")

    # Step 4: Copy merged configs to output_dir
    print("  Step 4: Copying merged configs to output...")
    for fname in ['Configuration.h', 'Configuration_adv.h']:
        src = os.path.join(tmpdir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(args.output_dir, fname))
            print(f"  Copied: {fname}")

    # Show result
    config_h = os.path.join(args.output_dir, 'Configuration.h')
    if os.path.exists(config_h):
        version_line = subprocess.run(
            ["grep", "CONFIGURATION_H_VERSION", config_h],
            capture_output=True, text=True
        ).stdout.strip()
        print(f"  Ready: {version_line}")
    print(f"  Output: {args.output_dir}")

    # Cleanup
    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    main()
