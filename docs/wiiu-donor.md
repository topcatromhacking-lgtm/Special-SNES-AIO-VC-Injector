# Wii U SNES donor analysis

## Received test donor

The externally supplied Super Metroid Wii U encrypted install archive reports title ID 000500001010A600. It contains 11 numbered .app content files, seven associated .h3 files, title.tmd, title.tik, and title.cert. TMD file-size records agree with all 11 .app ZIP entries; all seven present H3 files agree with the SHA-1 hashes recorded in TMD. **This is a structural metadata check, not verification of encrypted content or emulator features.**

No commercial game files, tickets, keys, or Nintendo executables are included in the repository.

## Read-only inspection

    python -m snes_vc_injector "Super Metroid [000500001010A600].zip" --donor
    python -m snes_vc_injector "Super Metroid [000500001010A600].zip" --donor --json

The inspector reads TMD content metadata from a flat or single-root ZIP and checks file sizes and H3 SHA-1 values. It does not extract, decrypt, repackage, alter, or upload files; it intentionally does not read or reveal keys in the ticket.

## Why encrypted is not enough

Installable Wii U titles typically comprise encrypted numbered .app and .h3 content files plus a ticket and title metadata. To study VC payloads, ROM placement and emulator assets, we need the locally decrypted **code/content/meta** directory tree. The donor owner may obtain those files with their own lawful backup/decryption workflow, keeping console keys and ticket material private.

Next steps after a decrypted donor is available: identify the RPX/VC payload and configuration, document original restore-point behavior, and prototype ordinary LoROM/HiROM replacement. No Wii U VC ROM injection is yet implemented or verified.
