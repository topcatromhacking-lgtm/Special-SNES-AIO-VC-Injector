# Special SNES AIO VC Injector

**Experimental SNES Virtual Console compatibility project** for **Wii, Wii U and New Nintendo 3DS**.

Our initial goal is to build and independently verify Nintendo native-VC compatibility profiles for ordinary LoROM/HiROM, ExHiROM (including expanded Dragon Quest III), S-DD1 Street Fighter Alpha 2/Zero 2, and S-DD1 Star Ocean. Other enhancement chips are future research targets.

## v0.1: ROM analyzer

The first module inspects local .sfc/.smc files and reports ROM header metadata, probable mapping, SHA-256, and a **provisional** compatibility family. It does **not** patch or distribute ROMs, package console titles, or establish emulator compatibility. It uses Python 3.10+ and only the standard library.

Run from this repository directory:

    python -m snes_vc_injector path/to/your-game.sfc
    python -m snes_vc_injector path/to/your-game.sfc --json
    python -m unittest discover -s tests -v

A translated or hacked game can alter the header title, mapping and special-chip metadata, so review findings before using a future packaging profile.

## Proposed architecture

Shared ROM analyzer and format transformations feed three independent adapters: Wii SNES VC, Wii U SNES VC and New 3DS SNES VC. Star Ocean and Street Fighter Alpha 2 get separate S-DD1 recipes. No Nintendo binaries or game assets are included.

See [architecture and limitations](docs/architecture.md) and the [experimental matrix](docs/compatibility.md).

## Legal / research note

Supply your own legally obtained ROM and donor assets for future tooling. Do not upload commercial ROMs, extracted VC titles, proprietary emulator binaries or encryption keys. A recognized ROM family is not evidence of boot, playability, SRAM or suspend compatibility.
