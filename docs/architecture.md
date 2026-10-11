# Technical architecture and scope

The project targets Nintendo's original SNES Virtual Console environment on Wii, Wii U and New Nintendo 3DS, **not** DS or GameCube VC. A SNES9x replacement engine, if investigated, must be described as a separate experimental backend, not Nintendo native emulation.

## Stages

1. Analyze SNES header candidates, size, mapping, 512-byte copier prefix, enhancement chip, SRAM metadata and hashes, with explicit confidence.
2. Select a compatibility profile only after a specific donor/emulator version is validated, allowing deliberate manual identification for translations and hacks.
3. Transform expanded mapping or S-DD1 supplemental data only using documented reproducible recipes. Star Ocean and SFA2 are separate profiles. Expanded chip-free Star Ocean is a distinct route from native S-DD1.
4. Package with platform-specific Wii, Wii U and New 3DS adapters, operating on users' local legally obtained donor assets.
5. Verify boot, audio/video, controls, in-game SRAM across exits, and persistent native Virtual Console restore points. Home-menu behavior alone does not prove snapshot compatibility.

## Current stage

v0.1 is metadata-only. It does not modify ROM files, modify native emulators, produce WAD/WUP/CIA titles, or establish compatibility. S-DD1 game-name matching is provisional, and unidentified S-DD1 ROMs are intentionally not forced into either game-specific treatment. Other enhancement-chip detection is tentative.

Keep copyrighted games and Nintendo binaries outside the repository. Ignore rules are not a substitute for reviewing changes before uploading.
