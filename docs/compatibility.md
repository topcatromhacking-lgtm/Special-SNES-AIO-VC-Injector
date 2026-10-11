# Compatibility verification matrix

**Unverified until evidence is documented.** A valid package does not establish successful boot, graphics, audio, SRAM, restore points, or hardware support.

| ROM family | Wii SNES VC | Wii U SNES VC | New 3DS SNES VC |
|---|---|---|---|
| Standard LoROM | Not tested | Not tested | Not tested |
| Standard HiROM | Not tested | Not tested | Not tested |
| ExHiROM (expanded DQIII) | Not tested | Not tested | Not tested |
| S-DD1 (Street Fighter Alpha 2) | Not tested | Not tested | Not tested |
| S-DD1 (Star Ocean) | Not tested | Not tested | Not tested |

This yields 15 game/platform exercises covering four initial compatibility families (standard includes separate LoROM and HiROM checks).

For each exercise preserve locally: ROM and donor hashes, exact donor/emulator revision, transformation method, packaging outcome, hardware vs emulator environment, boot outcome, scene coverage, audio/video, controls, in-game SRAM after close/reopen, and persistent restore-point behavior after fully exiting the title.

Do not conflate Wii's Dragon Quest 25th Anniversary Collection shvc.dol, a custom SNES9x DOL and ordinary Wii retail SNES VC; their compatibility evidence is independent.
