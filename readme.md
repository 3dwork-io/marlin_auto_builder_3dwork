[![Auto-Update](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml/badge.svg)](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml) [![Boards](https://img.shields.io/badge/boards-421-blue)](board-matrix.json)

**Marlin [2.1.2.7](https://github.com/MarlinFirmware/Marlin/releases/tag/2.1.2.7) | 421 boards | 22 PlatformIO envs | 100 vendors**

> [!TIP]
> 📋 **[BUILD_STATUS.md](BUILD_STATUS.md)** — Check compiled firmwares per board with download links and official config sources.

---

> [!WARNING]
> Binaries are compiled from official Marlin Configurations, **use at your own risk**.  
> We recommend you take the config files and compile them yourself — [compilation guide](https://marlin.3dwork.io/marlin/marlin-guia-compilacion).

## Auto-Update

The [auto-update workflow](.github/workflows/auto-update.yml):

- **Runs weekly** (Sunday 06:00 UTC) and can be triggered manually
- **Detects** new Marlin releases via GitHub API
- **Auto-syncs** board list from [MarlinFirmware/Configurations](https://github.com/MarlinFirmware/Configurations)
- **Resolves** PlatformIO env via `MOTHERBOARD` define + 190-entry lookup table
- **Builds** firmwares in parallel Docker containers (max 4 concurrent)
- **Pushes** configs + binaries to `Firmware/Configuration/` and `Firmware/Builds/`

## Customizations

- **Bootscreen**: 3Dwork logo applied to all boards with `SHOW_CUSTOM_BOOTSCREEN` enabled
- **Author string**: `STRING_CONFIG_H_AUTHOR = (3Dwork, https://3dwork.io)` applied via config.ini parser
- **Official configs only**: no local custom configs — everything comes from [MarlinFirmware/Configurations](https://github.com/MarlinFirmware/Configurations) at the exact version tag

## Workflow Groups

Boards are split into 6 parallel matrix groups:

| Group | Boards |
|---|---|
| Creality | 125 |
| delta + Geeetech | 56 |
| Wanhao + Anet + Tronxy | 44 |
| BIQU + Sovol + AnyCubic + TwoTrees | 36 |
| Artillery + Tevo + Kingroon + JGAurora + Ultimaker | 28 |
| others | 132 |

## Environment Distribution

| Env | Boards | MCU Family |
|---|---|---|
| mega2560 | 252 | AVR (RAMPS, MKS, Trigorilla, etc.) |
| STM32F103RC_btt | 45 | STM32F1 (SKR Mini E3, SKR E3, etc.) |
| STM32G0B1RE_btt | 21 | STM32G0 (SKR Mini E3 v3, Manta E3) |
| melzi_optiboot_optimized | 18 | AVR (Melzi/Creality V1) |
| mks_robin_nano_v1v2 | 14 | STM32F1 (MKS Robin Nano) |
| sanguino1284p_optimized | 11 | AVR (Anet, Sanguinololu) |
| STM32F103RE_creality | 9 | STM32F1 (Creality 4.2.7, 4.2.2) |
| Anet_ET4_no_bootloader | 8 | STM32F4 (Anet ET4/ET5) |
| LPC1769 | 8 | LPC1769 (SKR 1.4 Turbo, MKS Sbase) |
| rambo | 6 | AVR (Prusa, Eryone) |
| Artillery_Ruby | 4 | STM32F4 (Artillery Ruby) |
| BIGTREE_SKR_2 | 4 | STM32H7 (SKR 2) |
| STM32F401RC_creality | 4 | STM32F4 (Creality V4S1) |
| LPC1768 | 3 | LPC1768 (SKR 1.3) |
| BTT_SKR_SE_BX | 3 | STM32F4 (BTT SKR SE BX) |
| STM32H743VI_btt | 3 | STM32H7 (SKR 3, Octopus) |
| trigorilla_pro | 2 | STM32F1 (Anycubic) |
| mks_robin_mini | 2 | STM32F1 (MKS Robin Mini) |
| STM32G0B1RE_manta_btt | 1 | STM32G0 (Manta M4P/M8P) |
| FYSETC_CHEETAH_V20 | 1 | STM32F4 (FYSETC Cheetah 2.0) |
| BIGTREE_BTT002 | 1 | STM32F4 (BTT BTT002) |
| STM32F407VE_black | 1 | STM32F4 (Black STM32F407VET6) |

## Supported Boards by Vendor

| Vendor | Boards |
|---|---|
| Creality | 125 |
| delta | 29 |
| Geeetech | 27 |
| Wanhao | 17 |
| Anet | 16 |
| Tronxy | 11 |
| BIQU | 10 |
| Sovol | 10 |
| AnyCubic | 8 |
| Two Trees | 8 |
| Artillery | 7 |
| ... and 89 more vendors | |

📋 **[Full board list → board-matrix.json](board-matrix.json)** (421 entries with per-board config_path, board_path, official_path)

[![Auto-Update](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml/badge.svg)](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml) 