#!/usr/bin/env python3
"""
Generate GitHub Actions build matrix from board-matrix.json.

Usage:
    python3 scripts/generate-matrix.py 2_1_2_7
    python3 scripts/generate-matrix.py 2_1_2_7 --group Creality
    python3 scripts/generate-matrix.py 2_1_2_7 --group delta_Geeetech
    python3 scripts/generate-matrix.py 2_1_2_7 --group others
"""

import argparse
import json
import os
import sys

# Vendor groups: name -> list of vendor directory names
# Each group must stay under GHA's 256 config limit
VENDOR_GROUPS = {
    'Creality': ['Creality'],
    'delta_Geeetech': ['delta', 'Geeetech'],
    'Wanhao_Anet_Tronxy': ['Wanhao', 'Anet', 'Tronxy'],
    'BIQU_Sovol_AnyCubic_TwoTrees': ['BIQU', 'Sovol', 'AnyCubic', 'Two Trees'],
    'Artillery_Tevo_Kingroon_JGAurora_Ultimaker': ['Artillery', 'Tevo', 'Kingroon', 'JGAurora', 'Ultimaker'],
}


def get_vendor(board_path):
    return board_path.split('/')[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('version_dir', nargs='?', default='2_1_2_2')
    parser.add_argument('--group', help='Vendor group name')
    args = parser.parse_args()

    version_dir = args.version_dir
    matrix_path = 'board-matrix.json'
    if not os.path.exists(matrix_path):
        print("ERROR: board-matrix.json not found")
        sys.exit(1)

    with open(matrix_path) as f:
        entries = json.load(f)

    # Determine which vendors belong to this group
    group_vendors = set()
    if args.group:
        if args.group in VENDOR_GROUPS:
            group_vendors = set(VENDOR_GROUPS[args.group])
        elif args.group == 'others':
            # Everything not in any named group
            named = set()
            for vlist in VENDOR_GROUPS.values():
                named.update(vlist)
            group_vendors = None  # signal: exclude named

    filtered = []
    for e in entries:
        board = e.get('board', '')
        if board == 'pending':
            continue
        vendor = get_vendor(e.get('board_path', ''))
        if args.group:
            if args.group == 'others':
                if vendor in named:
                    continue
            elif vendor not in group_vendors:
                continue
        filtered.append(e)

    for e in filtered:
        rel = e['config_path'].replace('Firmware/Configuration/', '')
        e['build_path'] = 'Firmware/Builds/' + rel + '/' + version_dir
        e['label'] = rel.replace('/', ' - ')
        e['board_path'] = rel
        e.setdefault('official_path', e['board_path'])

    result = {'include': filtered}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
