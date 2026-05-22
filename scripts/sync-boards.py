#!/usr/bin/env python3
"""
Marlin Board Synchronizer — Sync board-matrix.json with upstream sources.

On each Marlin release, this script fetches ALL boards from Configurations repo,
compares with existing matrix, adds new boards (determining env via MOTHERBOARD
define or pattern matching), and preserves custom boards.

Usage:
    python3 sync-boards.py --board-matrix board-matrix.json [--marlin-version 2.1.2.7]
"""

import argparse
import json
import os
import re
import subprocess
import sys

# MOTHERBOARD -> PlatformIO env mapping
# Keys are C preprocessor #define MOTHERBOARD values from Configuration.h
MOTHERBOARD_TO_ENV = {
    # === AVR (mega2560-based) ===
    'BOARD_RAMPS_14_EFB': 'mega2560',
    'BOARD_RAMPS_14_EEB': 'mega2560',
    'BOARD_RAMPS_14_EFF': 'mega2560',
    'BOARD_RAMPS_14_EEF': 'mega2560',
    'BOARD_RAMPS_14_SF': 'mega2560',
    'BOARD_RAMPS_14_SF_V2': 'mega2560',
    'BOARD_RAMPS_14_HFB': 'mega2560',
    'BOARD_RAMPS_14_HHC': 'mega2560',
    'BOARD_RAMPS_4': 'mega2560',
    'BOARD_RAMPS_CREALITY': 'mega2560',
    'BOARD_RAMPS_CREALITY_V4': 'mega2560',
    'BOARD_RAMPS_CREALITY_V422': 'mega2560',
    'BOARD_RAMPS_CREALITY_V427': 'mega2560',
    'BOARD_CREALITY_V1': 'mega2560',
    'BOARD_CREALITY_V2': 'mega2560',
    'BOARD_CREALITY_V4': 'mega2560',
    'BOARD_CREALITY_V422': 'mega2560',
    'BOARD_CREALITY_V427': 'mega2560',
    'BOARD_CREALITY_V24S4': 'mega2560',  # Ender-2 Pro
    'BOARD_TRIGORILLA_14': 'mega2560',
    'BOARD_TRIGORILLA': 'mega2560',
    'BOARD_MKS_BASE_14': 'mega2560',
    'BOARD_MKS_BASE_15': 'mega2560',
    'BOARD_MKS_BASE_V2': 'mega2560',
    'BOARD_MKS_BASE_HEROIC': 'mega2560',
    'BOARD_MKS_GEN_L': 'mega2560',
    'BOARD_MKS_SGEN_L': 'mega2560',
    'BOARD_MKS_ROBIN': 'mega2560',
    'BOARD_MKS_ROBIN_LITE': 'mega2560',
    'BOARD_MKS_ROBIN_LITE3': 'mega2560',
    'BOARD_MKS_ROBIN_PRO': 'mega2560',
    'BOARD_MKS_SBASE': 'LPC1769',
    'BOARD_HJC2560C_REV1': 'mega2560',
    'BOARD_HJC2560C_REV2': 'mega2560',
    'BOARD_LONGER3D_LK': 'mega2560',
    'BOARD_MELZI': 'melzi_optiboot_optimized',
    'BOARD_MELZI_CREALITY': 'melzi_optiboot_optimized',
    'BOARD_ANET_10': 'sanguino1284p_optimized',
    'BOARD_ANET_ET4': 'Anet_ET4_no_bootloader',
    'BOARD_EINSY_RAMBO': 'rambo',
    'BOARD_PRINTRBOARD_G2': 'mega2560',
    'BOARD_PRINTRBOARD_REVF': 'mega2560',
    'BOARD_RURAMPS4D_11': 'mega2560',
    'BOARD_ULTRATRONICS': 'mega2560',
    'BOARD_RUMBA': 'mega2560',
    'BOARD_RUMBA_V2': 'mega2560',
    'BOARD_FELIX': 'mega2560',
    'BOARD_WANHAO_ONEPLUS': 'mega2560',
    'BOARD_WANHAO_DUPLICATOR_I3_PLUS': 'mega2560',
    'BOARD_TEENSY2': 'mega2560',
    'BOARD_TEENSYLU': 'mega2560',
    'BOARD_SANGUINOLOLU_11': 'sanguino1284p_optimized',
    'BOARD_SANGUINOLOLU_12': 'sanguino1284p_optimized',
    'BOARD_MINIRAMBO': 'rambo',
    'BOARD_BRAINWAVE': 'mega2560',
    'BOARD_GEN7_CUSTOM': 'mega2560',
    'BOARD_GEN7_14': 'mega2560',
    'BOARD_OMCA_A': 'mega2560',
    'BOARD_OMCA': 'mega2560',
    'BOARD_ADVI3PP_BOARD': 'mega2560',
    'BOARD_SAINSMART_2Y2': 'mega2560',
    'BOARD_RAMPS_FD_V2': 'mega2560',
    'BOARD_BAM_DICE': 'mega2560',
    'BOARD_MECREATOR': 'mega2560',
    'BOARD_AZTEEG_X3': 'mega2560',
    'BOARD_AZTEEG_X3_PRO': 'mega2560',
    'BOARD_RAPIDE_LITE_RL200': 'mega2560',
    'BOARD_ARDUINO_MICRO': 'mega2560',
    'BOARD_STM32F103RE': 'melzi_optiboot_optimized',  # weird but correct for some
    'BOARD_3DRAG': 'mega2560',
    'BOARD_K8400': 'mega2560',
    'BOARD_CHELL': 'mega2560',
    'BOARD_CNYSTL': 'mega2560',
    'BOARD_MEGATRONICS': 'mega2560',
    'BOARD_MEGATRONICS_2560': 'mega2560',
    'BOARD_TINYBOY2': 'mega2560',
    'BOARD_TEVO_TARANTULA': 'mega2560',
    'BOARD_BQ_ZUM_MEGA_3D': 'mega2560',
    'BOARD_RIGIDBOARD_V2': 'mega2560',
    'BOARD_TRIXLE': 'mega2560',
    # === LPC1768 / LPC1769 ===
    'BOARD_BTT_SKR_V1_3': 'LPC1768',
    'BOARD_BTT_SKR_V1_4': 'LPC1769',
    'BOARD_BTT_SKR_V1_4_TURBO': 'LPC1769',
    'BOARD_BTT_SKR_E3_DIP_V1_1': 'LPC1769',
    'BOARD_AZTEEG_X5GT': 'LPC1769',
    'BOARD_MKS_SGEN': 'LPC1769',
    # === STM32F1 (BTT SKR, Manta, etc) ===
    'BOARD_BTT_SKR_MINI_E3_V1_0': 'STM32F103RC_btt',
    'BOARD_BTT_SKR_MINI_E3_V1_2': 'STM32F103RC_btt',
    'BOARD_BTT_SKR_MINI_E3_V2_0': 'STM32F103RC_btt',
    'BOARD_BTT_SKR_MINI_E3_V3_0': 'STM32G0B1RE_btt',
    'BOARD_BTT_SKR_E3_TURBO': 'STM32F103RC_btt',
    'BOARD_BTT_SKR_MINI_MZ_V1_0': 'STM32F103RC_btt',
    'BOARD_BTT_BTT002_V1_0': 'BIGTREE_BTT002',
    'BOARD_BTT_SKR_V2_0_REV_B': 'BIGTREE_SKR_2',
    'BOARD_BTT_SKR_V3_0': 'STM32H743VI_btt',
    'BOARD_BTT_SKR_SE_BX': 'BTT_SKR_SE_BX',
    'BOARD_BTT_MANTA_E3_EZ': 'STM32G0B1RE_btt',
    'BOARD_BTT_MANTA_M4P_V2_1': 'STM32G0B1RE_manta_btt',
    'BOARD_BTT_OCTOPUS_V1_0': 'STM32H743VI_btt',
    'BOARD_BTT_OCTOPUS_V1_1': 'STM32H743VI_btt',
    'BOARD_BTT_GTR_V1_0': 'STM32H743VI_btt',
    'BOARD_FYSETC_AIO_II': 'STM32F103RC_btt',
    'BOARD_FYSETC_F6_13': 'STM32F103RC_btt',
    'BOARD_FYSETC_CHEETAH': 'STM32F103RC_btt',  # V1.2
    'BOARD_FYSETC_CHEETAH_V20': 'FYSETC_CHEETAH_V20',
    'BOARD_FYSETC_S6': 'STM32F103RC_btt',
    'BOARD_MKS_ROBIN_NANO_V1_3_F4': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_NANO_V2': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_NANO_V3': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_MINI': 'mks_robin_mini',
    'BOARD_MKS_ROBIN_E3': 'mega2560',  # Actually AVR
    'BOARD_MKS_ROBIN_E3P': 'mega2560',
    'BOARD_TH3D_EZBOARD': 'STM32F103RC_btt',
    'BOARD_TH3D_EZBOARD_LITE': 'mega2560',
    'BOARD_MEEB_3DP': 'STM32F103RC_btt',
    'BOARD_EINSTART_S': 'STM32F103RC_btt',
    'BOARD_LERDGE': 'STM32F103RC_btt',
    'BOARD_BIQU_B1': 'STM32F103RC_btt',
    # === STM32F4 ===
    'BOARD_CREALITY_V24S1_301F4': 'STM32F401RC_creality',
    'BOARD_CREALITY_V24S1_301': 'STM32F401RC_creality',
    'BOARD_ARTILLERY_RUBY': 'Artillery_Ruby',
    'BOARD_BIQU_BX': 'BTT_SKR_SE_BX',
    'BOARD_OVERNATOR': 'STM32F401RC_creality',
    # === STM32F1 Creality ===
    'BOARD_CREALITY_V452': 'STM32F103RE_creality',
    'BOARD_CREALITY_V45S1': 'STM32F103RE_creality',
    'BOARD_CREALITY_V46S1': 'STM32F103RE_creality',
    'BOARD_CREALITY_V47S1': 'STM32F103RE_creality',
    'BOARD_MACHINE_NAME': 'mega2560',  # Special/fix
    # === Trigorilla ===
    'BOARD_TRIGORILLA_PRO': 'trigorilla_pro',
    'BOARD_TRIGORILLA_PRO_V3': 'trigorilla_pro',
    # === FLSUN / Delta ===
    'BOARD_FLSUN_V1': 'mega2560',
    'BOARD_FLSUN_V2': 'mega2560',
    'BOARD_FLSUN_Q5': 'mega2560',
    'BOARD_FLSUN_DELTA': 'mega2560',
    'BOARD_FLSUN_SPEEDER_PAD': 'mega2560',
    'BOARD_MICROMAKE_D1': 'mega2560',
    'BOARD_MICROMAKE_DELTA': 'mega2560',
    'BOARD_HATCHBOX_ALPHA': 'mega2560',
    'BOARD_MALYAN_M300': 'mega2560',
    'BOARD_MALYAN_M150': 'mega2560',
    'BOARD_MALYAN_M180': 'mega2560',
    'BOARD_MALYAN_M200': 'mega2560',
    # === Voron ===
    'BOARD_VORON_DESIGN': 'STM32F103RC_btt',
    # === Geeetech (AVR) ===
    'BOARD_GT2560_V3': 'mega2560',
    'BOARD_GT2560_V4': 'mega2560',
    'BOARD_GTM32': 'mega2560',
    # === Wanhao ===
    'BOARD_WANHAO': 'mega2560',
    'BOARD_WANHAO_I3_MINI': 'mega2560',
    'BOARD_WANHAO_DUPLICATOR_I3_2_1': 'mega2560',
    'BOARD_WANHAO_DUPLICATOR_4S': 'mega2560',
    'BOARD_WANHAO_DUPLICATOR_6': 'mega2560',
    'BOARD_WANHAO_DUPLICATOR_9': 'mega2560',
    # === Tronxy ===
    'BOARD_TRONXY_V1': 'mega2560',
    'BOARD_TRONXY_X3A': 'mega2560',
    'BOARD_TRONXY_X5S': 'mega2560',
    'BOARD_TRONXY_X5SA': 'mega2560',
    'BOARD_TRONXY_XY100': 'mega2560',
    'BOARD_TRONXY_XY2': 'mega2560',
    'BOARD_CHITU_V5': 'mega2560',
    'BOARD_CHITU_V6': 'mega2560',
    # === Two Trees ===
    'BOARD_TWO_TREES': 'mega2560',
    'BOARD_TWO_TREES_BLUER': 'mega2560',
    # === MKS Robin Nano v1/v2 ===
    'BOARD_MKS_ROBIN_LITE_V1': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_LITE_V2': 'mks_robin_nano_v1v2',
    # === Ultimaker ===
    'BOARD_ULTIMAIN_2': 'mega2560',
    'BOARD_ULTIMAKER': 'mega2560',
    'BOARD_ULTIMAKER_2': 'mega2560',
    # === BQ ===
    'BOARD_BQ_WITBOX': 'mega2560',
    # === MakerFarm / RigidBot ===
    'BOARD_MAKERFARM': 'mega2560',
    # === Other ===
    'BOARD_MAKEBLOCK': 'mega2560',
    'BOARD_MAKEBLOCK_V2': 'mega2560',
    'BOARD_ARCHIM1': 'STM32F103RC_btt',
    'BOARD_ARCHIM2': 'STM32F103RC_btt',
    'BOARD_VOYAGER_V3': 'STM32F103RC_btt',
    'BOARD_MODIX_BIG60': 'STM32F103RC_btt',
    'BOARD_BIG_DUAL': 'STM32F103RC_btt',
    'BOARD_MEER_CAT': 'STM32F103RC_btt',
    # === Printrbot ===
    'BOARD_PRINTRBOARD': 'mega2560',
    # === Copymaster ===
    'BOARD_COPYMASTER': 'mega2560',
    # === MakerGear ===
    'BOARD_MAKERGEAR': 'mega2560',
    # === FlashForge ===
    'BOARD_FLASHFORGE': 'mega2560',
    # === Velleman ===
    'BOARD_VELLEMAN': 'mega2560',
    'BOARD_VELLEMAN_K8200': 'mega2560',
    'BOARD_VELLEMAN_K8400': 'mega2560',
    'BOARD_K8800': 'mega2560',
    # === JGAurora ===
    'BOARD_JGAURORA_A1': 'mega2560',
    'BOARD_JGAURORA_A3': 'mega2560',
    'BOARD_JGAURORA_A5': 'mega2560',
    'BOARD_JGAURORA_A5S': 'mega2560',
    'BOARD_JGAURORA_MAGIC': 'mega2560',
    # === Flying Bear ===
    'BOARD_FLYING_BEAR': 'mega2560',
    'BOARD_FLYING_BEAR_GHOST': 'mega2560',
    'BOARD_FB_P902': 'mega2560',
    'BOARD_FB_P905': 'mega2560',
    # === Eryone ===
    'BOARD_ERYONE': 'mega2560',
    # === Robo3D ===
    'BOARD_ROBO': 'mega2560',
    # === EasyThreed ===
    'BOARD_EASYTHREED': 'mega2560',
    # === HMS434 ===
    'BOARD_HMS434': 'mega2560',
    # === Kingroon ===
    'BOARD_KINGROON': 'mega2560',
    # === FolgerTech ===
    'BOARD_FOLGER_TECH': 'mega2560',
    # === Ortur (laser) ===
    'BOARD_ORTUR_4': 'mega2560',
    # === Sunlu ===
    'BOARD_SUNLU': 'mega2560',
    # === Zonestar ===
    'BOARD_ZONESTAR': 'mega2560',
    'BOARD_ZONESTAR_V2': 'mega2560',
    # === Tevo ===
    'BOARD_TEVO_MICHELANGELO': 'mega2560',
    'BOARD_TEVO_NEREUS': 'mega2560',
    'BOARD_TEVO_LITTLE_MONSTER': 'mega2560',
    # === FoamCutter ===
    'BOARD_FOAM_CUTTER': 'mega2560',
    # === Manta / Octopus ===
    'BOARD_MANTA_E3_EZ': 'STM32G0B1RE_btt',
    'BOARD_MANTA_M4P': 'STM32G0B1RE_manta_btt',
    'BOARD_MANTA_M8P': 'STM32G0B1RE_manta_btt',
    # === MKS Robin Nano F4 ===
    'BOARD_MKS_ROBIN_NANO_F4': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_LITE_V3': 'mks_robin_nano_v1v2',
    # === WASP ===
    'BOARD_WASP': 'mega2560',
    # === Geeetech A30T ===
    'BOARD_A30T': 'mega2560',
    # === FYSETC Cheetah v1.x ===
    'BOARD_FYSETC_CHEETAH': 'STM32F103RC_btt',
    # === Eazao ===
    'BOARD_EAZOA_ZERO': 'mega2560',
    # === Rolohaun ===
    'BOARD_ROLOHAUN': 'STM32G0B1RE_btt',
    # === Longer3D ===
    'BOARD_LONGER3D_LK': 'mega2560',
    # === mTiny / MeeB ===
    'BOARD_MEEB_3DP': 'STM32F103RC_btt',
    # === Micromake ===
    'BOARD_MICROMAKE_C1': 'mega2560',
    # === Hictop ===
    'BOARD_HICTOP': 'mega2560',
    # === TPARA ===
    'BOARD_TPARA': 'mega2560',
    # === Simulator ===
    'BOARD_SIMULATOR': 'mega2560',
    # === Creality free-run (no MOTHERBOARD) ===
    'BOARD_CREALITY_FREERUN': 'mega2560',
    # === Artillery Hornet ===
    'BOARD_ARTILLERY_HORNET': 'mega2560',
    # === Artillery Genius ===
    'BOARD_ARTILLERY_GENIUS': 'mega2560',
    # === gCreate ===
    'BOARD_GCREATOR': 'mega2560',
    # === Voxelab ===
    'BOARD_VOXELAB': 'STM32F103RC_btt',
    # === SOVOL SV-0x ===
    'BOARD_SOVOL_SV02': 'mega2560',
    'BOARD_SOVOL_SV03': 'mega2560',
    'BOARD_SOVOL_SV05': 'mega2560',
    'BOARD_SOVOL_SV06': 'STM32F103RC_btt',
    'BOARD_SOVOL_SV06_PLUS': 'STM32F103RC_btt',
    # === QIDI ===
    'BOARD_QIDI_TECH': 'mega2560',
    # === BIBO ===
    'BOARD_BIBO': 'mega2560',
    # === Labists ===
    'BOARD_LABISTS': 'Anet_ET4_no_bootloader',
    # === Dagoma ===
    'BOARD_DAGOMA': 'mega2560',
    # === Renkforce ===
    'BOARD_RENKF_RF100': 'mega2560',
    'BOARD_RENKF_RF100V2': 'mega2560',
    'BOARD_RENKF_RF100XL': 'mega2560',
    # === Weedo ===
    'BOARD_WEEDO': 'mega2560',
    # === Weistek ===
    'BOARD_WEISTEK': 'mega2560',
    # === Intamsys ===
    'BOARD_INTAMSYS': 'mega2560',
    # === Tronxy D01 ===
    'BOARD_TRONXY_D01': 'mega2560',
    # === SANGUINOLOLU ===
    'BOARD_SANGUINOLOLU': 'sanguino1284p_optimized',
    # === AZSMZ ===
    'BOARD_AZSMZ': 'mega2560',
    # === Unmapped from previous runs ===
    'BOARD_5DPRINT': 'mega2560',
    'BOARD_ARMED': 'mega2560',
    'BOARD_BIQU_B300_V1_0': 'STM32F103RC_btt',
    'BOARD_BLACK_STM32F407VE': 'STM32F407VE_black',
    'BOARD_BRAINWAVE_PRO': 'mega2560',
    'BOARD_BTT_E3_RRF': 'STM32F103RC_btt',
    'BOARD_BTT_SKR_SE_BX_V3': 'BTT_SKR_SE_BX',
    'BOARD_CCROBOT_MEEB_3DP': 'STM32F103RC_btt',
    'BOARD_CHITU3D_V5': 'mega2560',
    'BOARD_CHITU3D_V6': 'mega2560',
    'BOARD_CHITU3D_V9': 'mega2560',
    'BOARD_CNCONTROLS_15': 'mega2560',
    'BOARD_COPYMASTER_3D': 'mega2560',
    'BOARD_CREALITY_CR4NTXXC10': 'mega2560',
    'BOARD_CREALITY_F401RE': 'STM32F401RC_creality',
    'BOARD_CREALITY_V4210': 'mega2560',
    'BOARD_CREALITY_V431': 'mega2560',
    'BOARD_DAGOMA_F5': 'mega2560',
    'BOARD_DUPLICATOR_I3_PLUS': 'mega2560',
    'BOARD_FELIX2': 'mega2560',
    'BOARD_FLSUN_HISPEED': 'mega2560',
    'BOARD_FORMBOT_RAPTOR': 'mega2560',
    'BOARD_FYSETC_CHEETAH_V12': 'STM32F103RC_btt',
    'BOARD_INTAMSYS40': 'mega2560',
    'BOARD_JGAURORA_A5S_A1': 'mega2560',
    'BOARD_K8200': 'mega2560',
    'BOARD_LONGER3D_LKx_PRO': 'mega2560',
    'BOARD_MAKEBOARD_MINI': 'mega2560',
    'BOARD_MEGACONTROLLER': 'mega2560',
    'BOARD_MELZI_MALYAN': 'melzi_optiboot_optimized',
    'BOARD_MELZI_TRONXY': 'melzi_optiboot_optimized',
    'BOARD_MIGHTYBOARD_REVE': 'mega2560',
    'BOARD_MKS_GEN_13': 'mega2560',
    'BOARD_MKS_GEN_L_V2': 'mega2560',
    'BOARD_MKS_ROBIN_NANO': 'mks_robin_nano_v1v2',
    'BOARD_MKS_ROBIN_NANO_V3_1': 'mks_robin_nano_v1v2',
    'BOARD_OPULO_LUMEN_REV3': 'mega2560',
    'BOARD_OPULO_LUMEN_REV4': 'mega2560',
    'BOARD_OPULO_LUMEN_REV5': 'mega2560',
    'BOARD_OVERLORD': 'mega2560',
    'BOARD_RAMBO': 'rambo',
    'BOARD_RAMBO_THINKERV2': 'rambo',
    'BOARD_RAMPS_13_EEB': 'mega2560',
    'BOARD_RAMPS_13_EFB': 'mega2560',
    'BOARD_RAMPS_DUO_EFB': 'mega2560',
    'BOARD_RAMPS_ENDER_4': 'mega2560',
    'BOARD_RL200': 'mega2560',
    'BOARD_RUMBA_E3D': 'mega2560',
    'BOARD_SIMULATED': 'mega2560',
    'BOARD_SOVOL_V131': 'mega2560',
    'BOARD_TH3D_EZBOARD_V2': 'mega2560',
    'BOARD_TRIGORILLA_V006': 'mega2560',
    'BOARD_TRONXY_V3_1_0': 'mega2560',
    'BOARD_VORON': 'STM32F103RC_btt',
    'BOARD_WANHAO_D9': 'mega2560',
    'BOARD_WEEDO_62A': 'mega2560',
}

# Pattern fallback env matching (when MOTHERBOARD define not found in source)
ENV_PATTERNS = {
    'sanguino1284p_optimized': ['Anet/A', 'Sanguinololu'],
    'mega2560': [
        'CrealityV', 'RAMPS', 'Geeetech', 'Melzi',
        'BQ/', 'CTC/', 'Cartesio', 'RepRapWorld',
        'Sovol/SV-01/CrealityV', 'Anet/ET',
        'Artillery/Genius', 'Artillery/Hornet',
        'AnyCubic/i3', 'AnyCubic/Chiron',
        'Kingroon/KP', 'Creality/CR-20', 'Creality/CR-8',
        'Creality/CR-10 V2', 'Creality/CR-10 V3/Stock',
        'Creality/Ender-3 Max', 'Creality/Ender-3 Neo',
        'Creality/Ender-2 Pro', 'Tevo/Tarantula', 'Tevo/Tornado',
        'Tinkerine/Ditto Pro', 'delta/Geeetech', 'delta/MKS/',
        'linear_axes/RAMPS', 'MKS/', 'Renkforce/RF',
        'Sovol/SV-01/CrealityV', 'Sovol/SV-01/CrealityV',
    ],
    'STM32F103RC_btt': [
        'SKR Mini E3 2.0', 'SKR E3 Turbo', 'SKR E3-DIP',
        'BTT SKR 1.3', 'SKR 1.4', 'SKR 1.3', 'SKR_1.3',
        'SKR E3 Turbo', 'BigTreeTech SKR Mini MZ',
    ],
    'Artillery_Ruby': ['Artillery/Sidewinder X', 'Artillery/Genius Pro'],
    'LPC1768': ['Anet/E16', 'LPC1768'],
    'LPC1769': ['MKS/Sbase', 'Azteeg/X5GT', 'MKS/SBASE'],
    'trigorilla_pro': ['Trigorilla Pro'],
    'Anet_ET4_no_bootloader': ['Anet/ET4', 'Anet/ET5'],
    'STM32G0B1RE_btt': ['SKR Mini E3 v3', 'Manta E3'],
    'STM32G0B1RE_manta_btt': ['Manta', 'BIQU/Hurakan'],
    'STM32H743VI_btt': ['SKR 3', 'SKR Pro', 'Octopus'],
}


def download_motherboard(official_path):
    """Download Configuration.h and extract MOTHERBOARD define."""
    url_path = official_path.replace(' ', '%20')
    url = f"https://raw.githubusercontent.com/MarlinFirmware/Configurations/import-2.1.x/config/examples/{url_path}/Configuration.h"
    try:
        result = subprocess.run(
            ["curl", "-sL", url],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout:
            match = re.search(r'#define\s+MOTHERBOARD\s+(\S+)', result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def fetch_config_tree():
    """Fetch the Configurations repo tree listing."""
    url = "https://api.github.com/repos/MarlinFirmware/Configurations/git/trees/import-2.1.x?recursive=1"
    result = subprocess.run(
        ["curl", "-sL", url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print("ERROR: Failed to fetch Configurations tree")
        sys.exit(1)
    data = json.loads(result.stdout)
    boards = set()
    for item in data.get('tree', []):
        path = item['path']
        if path.startswith('config/examples/') and path.endswith('/Configuration.h'):
            board_path = path.replace('config/examples/', '').replace('/Configuration.h', '')
            boards.add(board_path)
    return boards


def normalize_board_path(board_path):
    """Convert Configurations path to our board_path format."""
    bp = board_path.strip()
    bp = bp.replace(' ', '_')
    bp = bp.replace('+', '_Plus')
    return bp


def load_matrix(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_matrix(path, matrix):
    with open(path, 'w') as f:
        json.dump(matrix, f, indent=2)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser(description='Sync board-matrix.json with upstream')
    parser.add_argument('--board-matrix', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    output_path = args.output or args.board_matrix

    existing = load_matrix(args.board_matrix)
    existing_by_official = {}
    existing_by_bp = {}
    for entry in existing:
        official = entry.get('official_path', '').strip() or entry.get('board_path', '').strip()
        existing_by_official[official] = entry
        existing_by_bp[entry.get('board_path', '').strip()] = entry

    print(f"Existing boards: {len(existing)}")

    print("Fetching Configurations tree...")
    upstream = fetch_config_tree()
    print(f"Upstream boards found: {len(upstream)}")

    matched = 0
    added = 0
    pending_count = 0
    motherboard_cache = {}

    for official_path in sorted(upstream):
        if official_path in existing_by_official:
            entry = existing_by_official[official_path]
            # Try to resolve pending entries
            if entry.get('board') == 'pending':
                mb = download_motherboard(official_path)
                env = None
                if mb:
                    env = MOTHERBOARD_TO_ENV.get(mb)
                if not env:
                    bp_lower = official_path.lower()
                    for env_name, patterns in ENV_PATTERNS.items():
                        for pattern in patterns:
                            if pattern.lower() in bp_lower:
                                env = env_name
                                break
                        if env:
                            break
                if env:
                    entry['board'] = env
                    print(f"  ✓ RESOLVED [{env:30s}] {official_path}")
                else:
                    if mb:
                        print(f"  ? UNMAPPED MB: {mb:30s} {official_path}")
            matched += 1
            continue
        norm = normalize_board_path(official_path)
        if norm in existing_by_bp:
            entry = existing_by_bp[norm]
            if entry.get('board') == 'pending':
                mb = download_motherboard(official_path)
                env = None
                if mb:
                    env = MOTHERBOARD_TO_ENV.get(mb)
                if not env:
                    bp_lower = official_path.lower()
                    for env_name, patterns in ENV_PATTERNS.items():
                        for pattern in patterns:
                            if pattern.lower() in bp_lower:
                                env = env_name
                                break
                        if env:
                            break
                if env:
                    entry['board'] = env
                    print(f"  ✓ RESOLVED [{env:30s}] {official_path}")
            matched += 1
            continue

        # Try MOTHERBOARD lookup
        env = None
        mb = motherboard_cache.get(official_path)
        if mb is None:
            mb = download_motherboard(official_path)
            motherboard_cache[official_path] = mb

        if mb:
            env = MOTHERBOARD_TO_ENV.get(mb)
            if env:
                new_entry = {
                    'board': env,
                    'config_path': f"Firmware/Configuration/{norm}",
                    'board_path': norm,
                    'official_path': official_path,
                }
                existing.append(new_entry)
                added += 1
                print(f"  + [{env:30s}] (MB:{mb}) {official_path}")
                continue

        # Pattern fallback
        if not env:
            bp_lower = official_path.lower()
            for env_name, patterns in ENV_PATTERNS.items():
                for pattern in patterns:
                    if pattern.lower() in bp_lower:
                        new_entry = {
                            'board': env_name,
                            'config_path': f"Firmware/Configuration/{norm}",
                            'board_path': norm,
                            'official_path': official_path,
                        }
                        existing.append(new_entry)
                        added += 1
                        print(f"  + [{env_name:30s}] (pattern) {official_path}")
                        env = env_name
                        break
                if env:
                    break

        if not env:
            new_entry = {
                'board': 'pending',
                'config_path': f"Firmware/Configuration/{norm}",
                'board_path': norm,
                'official_path': official_path,
            }
            existing.append(new_entry)
            pending_count += 1
            if mb:
                print(f"  ? [{mb:30s}] (UNMAPPED MB) {official_path}")
            else:
                print(f"  ? [{'pending':30s}] (no MB found) {official_path}")

    print(f"\nSUMMARY:")
    print(f"  Existing in matrix: {len(existing_by_bp)}")
    print(f"  Matched already:    {matched}")
    print(f"  Added (auto):       {added}")
    print(f"  Still pending:      {pending_count}")
    print(f"  Total:              {len(existing)}")

    save_matrix(output_path, existing)
    print(f"\nSaved: {output_path}")


if __name__ == '__main__':
    main()
