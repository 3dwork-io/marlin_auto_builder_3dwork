[![Auto-Update](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml/badge.svg)](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml) [![Boards](https://img.shields.io/badge/boards-421-blue)](board-matrix.json)

**Marlin [2.1.2.7](https://github.com/MarlinFirmware/Marlin/releases/tag/2.1.2.7) | 421 boards (410 upstream + 11 custom) | 22 PlatformIO envs | 87 vendors**

[Auto-Update workflow](.github/workflows/auto-update.yml) — [Board Matrix](board-matrix.json) — [Sync Script](scripts/sync-boards.py) — [Build Process](build_process.md)

---

> [!WARNING]
> Binaries are compiled from official Marlin pre-configuration repositories, **use at your own risk**.  
> We recommend you take the config files and compile them yourself — [compilation guide](https://3dwork-qitec-net.translate.goog/guias-impresion-3d/mejoras-upgrades/marlin-guia-compilacion?_x_tr_sl=es&_x_tr_tl=en&_x_tr_hl=es&_x_tr_pto=wapp). See [build_process.md](build_process.md) for details.

## Auto-Update

This repo includes an [auto-update workflow](.github/workflows/auto-update.yml) that:

- **Runs weekly** (Sunday 06:00 UTC) and can be triggered manually
- **Detects** new Marlin releases by checking GitHub API
- **Auto-syncs** board list from [MarlinFirmware/Configurations](https://github.com/MarlinFirmware/Configurations)
- **Resolves** PlatformIO env via `MOTHERBOARD` define + 190-entry lookup table
- **Builds** all firmwares via parallel matrix (max 4 concurrent) in Docker
- **Pushes** configs + binaries to `Firmware/Configuration/` and `Firmware/Builds/`
- For each board, check `Firmware/Configuration/{vendor}/{printer}/config.ini` for overrides

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

| Vendor | Boards | Envs |
|---|---|---|
| Creality | 125 | mega2560, STM32F103RC_btt, STM32F103RE_creality, STM32G0B1RE_btt, STM32F401RC_creality, LPC1768, LPC1769, STM32H743VI_btt, BIGTREE_SKR_2, FYSETC_CHEETAH_V20, melzi_optiboot_optimized |
| delta | 29 | mega2560, mks_robin_nano_v1v2, mks_robin_mini, LPC1769, trigorilla_pro |
| Geeetech | 27 | mega2560 |
| Wanhao | 17 | mega2560, melzi_optiboot_optimized |
| Anet | 16 | sanguino1284p_optimized, Anet_ET4_no_bootloader, LPC1768 |
| Tronxy | 11 | mega2560, melzi_optiboot_optimized |
| BIQU | 10 | BIGTREE_SKR_2, BTT_SKR_SE_BX, LPC1768, LPC1769, STM32F103RC_btt, STM32G0B1RE_manta_btt |
| Sovol | 10 | mega2560, STM32F103RC_btt, STM32G0B1RE_btt |
| AnyCubic | 8 | mega2560, melzi_optiboot_optimized, STM32F103RC_btt, trigorilla_pro |
| Two Trees | 8 | mks_robin_nano_v1v2 |
| Artillery | 7 | mega2560, Artillery_Ruby |
| ... and 76 more vendors | | |

📋 **[Full board list → board-matrix.json](board-matrix.json)** (421 entries with per-board config_path, board_path, official_path)

[![Auto-Update](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml/badge.svg)](https://github.com/3dwork-io/marlin_auto_builder_3dwork/actions/workflows/auto-update.yml) 