# Wii U SNES VC RPX embedded-ROM layout (first verified donor)

## First donor: Super Metroid

Tested using a privately supplied decrypted donor ZIP, without uploading binaries to GitHub.

- VC title code: WUP-JAJE
- Wii U title ID: 000500001010A600
- Executable: code/WUP-JAJE.rpx (9,465,984 bytes)
- RPX: ELF32 big-endian PowerPC with zlib-compressed sections (section flags 0x08000000)
- Relevant section: #3, uncompressed length 7,749,820 bytes
- VC container start: section-relative 0x20
- Container header: 0x30 bytes
- SNES ROM starts: section-relative 0x50
- SNES ROM ends / additional-data start: section-relative 0x300050
- Embedded SNES ROM: 3,145,728 bytes (3 MiB), LoROM
- Additional VC data length: 1,615,189 bytes (includes conversion/PCM-related data); format still under investigation
- No native ROM injection performed; no boot or restore-point compatibility tests performed for modified builds

## Running read-only inspection

    python -m snes_vc_injector "SuperMetroiddec.zip" --rpx
    python -m snes_vc_injector "SuperMetroiddec.zip" --rpx --json

Alternatively supply code/WUP-JAJE.rpx directly.

The analyzer finds the 0x30-byte Nintendo VC header, validates its content offsets and a plausible SNES cartridge header, and returns metadata and hashes. All offsets are **section-relative after decompression**; do not seek to the same offset in the raw RPX.

## Why a naive 6 MiB ExHiROM replacement will fail

Super Metroid's container reserves a 3 MiB ROM region followed immediately by extra VC data. A larger game requires moving and preserving appended content, changing all affected pointers and expanding/rewriting RPX sections; more importantly, the emulator must implement the target memory mapping. An increased container size alone does not prove ExHiROM support.

## Technical references

- https://github.com/AwakeEchidna/wiiu-vc-extractor
- https://gbatemp.net/threads/understanding-and-changing-snes-vc-rpx-settings.425474/

No commercial ROM data, tickets, keys, console emulator binaries or copyrighted assets are committed.
