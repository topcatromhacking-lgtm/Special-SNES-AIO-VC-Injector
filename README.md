# Special SNES AIO VC Injector

**Experimental SNES Virtual Console compatibility project** for **Wii, Wii U and New Nintendo 3DS**.

Our goal is to develop and independently verify native Nintendo VC profiles for standard LoROM/HiROM, ExHiROM, S-DD1 Street Fighter Alpha 2/Zero 2 and S-DD1 Star Ocean; other enhancement chips are later research targets.

## v0.2: First experimental Wii U LoROM builder

Given your **own** decrypted Wii U SNES VC donor ZIP and SNES ROM, the tool creates a local decrypted donor ZIP with a standard LoROM embedded into the donor's RPX and a JSON report. Only non-enhancement, power-of-two-sized LoROMs whose padded variants fit the donor's original compressed section are currently accepted.

    python -m snes_vc_injector.inject_wiiu --donor "SuperMetroiddec.zip" --rom "Super Mario World (USA).zip" --output "SMW_Experimental.zip"

**Experimental:** not tested on Wii U hardware or Cemu, not an encrypted installable WUP package, retains donor title ID and game assets, and does not establish working SRAM or native VC suspension. **Never overwrite your existing Super Metroid installation.**

See [first Super Mario World Wii U experiment](docs/wiiu-lorom-injection.md).

## Read-only analysis tools (v0.1)

Requires Python 3.10+ with no external dependencies.

    python -m snes_vc_injector path/to/game.sfc --json
    python -m snes_vc_injector path/to/encrypted-donor.zip --donor --json
    python -m snes_vc_injector path/to/decrypted-donor.zip --rpx --json
    python -m unittest discover -s tests -v

The analyzer reports metadata and hashes, not commercial ROM bytes. Recognition does not establish native hardware compatibility.

See [architecture](docs/architecture.md), [compatibility matrix](docs/compatibility.md), [encrypted Wii U donor](docs/wiiu-donor.md) and [decrypted RPX research](docs/wiiu-rpx.md).

Do not upload commercial ROMs, decrypted Nintendo titles, emulator executables, tickets, keys or other proprietary assets to the repository. Keep private test assets local and independently verify hardware save/restore behavior.
