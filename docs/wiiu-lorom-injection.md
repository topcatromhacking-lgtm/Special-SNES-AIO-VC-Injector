# Wii U native SNES VC LoROM injection, experimental v0.2

## Status: structurally validated, **not** console/emulator-tested

Input privately provided by the tester: a decrypted US Super Metroid Wii U VC donor (title ID 000500001010A600, code/WUP-JAJE.rpx) and Super Mario World (USA) LoROM. No ROM, VC RPX, key, ticket, title package or Nintendo binary is committed.

### Build it locally

Requires Python 3.10+ and only the standard library.

    python -m snes_vc_injector.inject_wiiu --donor "SuperMetroiddec.zip" --rom "Super Mario World (USA).zip" --output "SMW_Experimental.zip"

The donor must be an already decrypted ZIP containing code/content/meta. The target can be one .sfc/.smc or a ZIP containing exactly one such file. Output is a **decrypted code/content/meta ZIP**, not an installable encrypted WUP package. A separate JSON report is created.

For an initial Cemu test, extract the generated ZIP into its own directory and use File > Load with code/WUP-JAJE.rpx. Do not overwrite an installed Super Metroid game: the build retains the donor's title ID and images. Wii U hardware load, SRAM and VC restore-point compatibility remain unverified.

### What was done and why

Super Metroid's RPX section #3 stores a 3 MiB SNES LoROM followed by 1,615,189 bytes of VC supplementary data. Super Mario World USA is 512 KiB, standard LoROM without an enhancement chip.

The prototype replaces ROM bytes inside the existing 3 MiB region, preserves the VC header and supplementary data, recompresses section #3 with zlib, updates its on-disk ELF section size and the Wii U section CRC32 table, and leaves all other executable sections and assets intact. It never changes other section file offsets. It rejects special chips and targets larger than the donor's ROM capacity.

Fully mirroring this particular SMW ROM six times increased the zlib-compressed section by about 661 KiB, exceeding its reserved file space. The build instead uses four repetitions of the 512 KiB ROM, with 1 MiB of 0xFF padding. This fits inside the pre-existing compressed region, allowing a same-size RPX build. It is an experimental compromise and **does not prove correct ROM bank mirroring or VC behavior**.

### Structural verification on supplied input

- Target ROM: 524,288 bytes, checksum/complement consistent, LoROM mapping
- Donor original RPX: 9,465,984 bytes
- Output RPX: unchanged length, 9,465,984 bytes
- Embedded ROM region: unchanged length, 3,145,728 bytes
- ROM copies / padding: four / 1,048,576 bytes 0xFF
- All other 91 donor files unchanged byte-for-byte
- Complete output RPX is readable again by local SNES VC RPX inspector
- All applicable RPX section CRC entries validated after mutation
- VC data preceding and following ROM byte-for-byte unchanged
- Boot, gameplay, audio, SRAM and persistent restore points: NOT TESTED

### Test checklist

First confirm title boots and Mario appears; test controls, audio, and World 1-1. Next create an in-game save, exit and relaunch, and verify save data. Lastly create a native Wii U VC restore point, fully quit, reopen and load it. Record success/failure and the environment (Cemu/version or Wii U hardware). Do not represent the profile as compatible until verified.

### Important limitations

This is not a universal SNES injection solution. Different donor emulator revisions, non-power-of-two ROMs, HiROM, ExHiROM, chip handling, mapping and supplementary PCM/config differences require research. This work does not replace the Nintendo emulator with SNES9x.
