# Special SNES AIO VC Injector

**Experimental SNES Virtual Console compatibility project** for **Wii, Wii U and New Nintendo 3DS**.

The goal is to develop and independently verify native Nintendo VC profiles for standard LoROM/HiROM, ExHiROM, S-DD1 Street Fighter Alpha 2/Zero 2 and S-DD1 Star Ocean; other enhancement chips are later research targets.

## v0.1: Read-only analysis foundation

The current tooling inspects a local SNES ROM, an encrypted Wii U WUP/NUS donor ZIP, or a decrypted Wii U SNES RPX (including a ZIP containing code/WUP-*.rpx). It **does not inject games or generate installable titles**.

Requires Python 3.10+ (standard library only):

    python -m snes_vc_injector path/to/game.sfc --json
    python -m snes_vc_injector path/to/encrypted-donor.zip --donor --json
    python -m snes_vc_injector path/to/decrypted-donor.zip --rpx --json
    python -m snes_vc_injector path/to/code/WUP-JAJE.rpx --rpx
    python -m unittest discover -s tests -v

The analyzer reports metadata and hashes, not ROM bytes. Recognition does not establish native hardware compatibility.

See [architecture](docs/architecture.md), [compatibility matrix](docs/compatibility.md), [encrypted donor inspection](docs/wiiu-donor.md) and [decrypted RPX research](docs/wiiu-rpx.md).

Do not upload commercial ROMs, decrypted Nintendo titles, emulator executables, tickets, keys or other proprietary assets to the repository. Keep private test assets local and independently verify hardware save/restore behavior.
