"""Experimental LoROM same-capacity injection in decrypted Wii U SNES RPX.

Only patches a local donor; no Nintendo files or private keys embedded.
Keeps the original ROM section capacity, VC appended data and ELF layout.
Hardware compatibility is unverified.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import struct
import zlib


class InjectionError(ValueError):
    """Unsupported or structurally unsafe injection."""


def _rom_header(rom: bytes) -> tuple[str, int]:
    if len(rom) < 0x8000:
        raise InjectionError('Target SNES ROM is too small')
    header = rom[0x7FC0:0x8000]
    name = header[:21].rstrip(b' \x00')
    if not name or not all(0x20 <= x <= 0x7E for x in name):
        raise InjectionError('Target LoROM header is not readable')
    mode = header[0x15]
    if mode not in (0x20, 0x30, 0x22):
        raise InjectionError(f'Only ordinary LoROM supported (map byte 0x{mode:02X})')
    cart = header[0x16]
    if cart not in (0, 1, 2):
        raise InjectionError(f'Only no-enhancement LoROM supported (cartridge 0x{cart:02X})')
    comp = int.from_bytes(header[0x1C:0x1E], 'little')
    checksum = int.from_bytes(header[0x1E:0x20], 'little')
    if comp ^ checksum != 0xFFFF:
        raise InjectionError('SNES checksum/complement fields are inconsistent')
    return name.decode('ascii'), cart


def _prepare_target(data: bytes, capacity: int) -> tuple[str, bytes, int, int]:
    copier = 512 if len(data) % 0x8000 == 512 else 0
    rom = data[copier:]
    name, _ = _rom_header(rom)
    if len(rom) > capacity:
        raise InjectionError(f'Target ({len(rom)}) exceeds donor ROM capacity ({capacity})')
    if not len(rom) or (len(rom) & (len(rom) - 1)):
        raise InjectionError('Experimental build only mirrors power-of-two-sized LoROMs')
    if capacity % len(rom):
        raise InjectionError('Donor capacity must be an exact multiple of target ROM size')
    return name, rom, copier, capacity // len(rom)


def _get_section(data: bytes, index: int):
    shoff = struct.unpack_from('>I', data, 0x20)[0]
    entry_off = shoff + index * 40
    fields = struct.unpack_from('>10I', data, entry_off)
    return fields, entry_off


def patch_rpx_bytes(original: bytes, target: bytes):
    """Return patched RPX and report for same-capacity ordinary LoROM.

    Finds maximum local ROM repetitions fitting existing compressed section.
    Fails if even one target copy exceeds original compressed allocation.
    """
    if len(original) < 52 or original[:6] != b'\x7fELF\x01\x02':
        raise InjectionError('Not a big-endian ELF32 RPX')
    rpx_sha = sha256(original).hexdigest()
    shnum = struct.unpack_from('>H', original, 0x30)[0]
    if not 1 <= shnum <= 200:
        raise InjectionError('Invalid section count')
    shoff = struct.unpack_from('>I', original, 0x20)[0]
    if shoff + 40 * shnum > len(original):
        raise InjectionError('Section table outside file')
    crc_candidates = []
    sections = []
    for i in range(shnum):
        s, e = _get_section(original, i)
        sections.append(s)
        if s[1] == 0x80000003 and s[5] == shnum * 4:
            crc_candidates.append(i)
    if len(crc_candidates) != 1:
        raise InjectionError('Expected one valid Wii U RPX CRC section')
    crc_index = crc_candidates[0]
    crc_section = sections[crc_index]
    crc_off = crc_section[4]
    if crc_off + shnum * 4 > len(original):
        raise InjectionError('CRC table outside file')
    matching = []
    for i,s in enumerate(sections):
        _, stype, flags, address, off, size, *_ = s
        if stype != 1 or not (flags & 0x08000000) or size < 6 or off + size > len(original):
            continue
        try:
            decoded = zlib.decompress(original[off + 4: off + size])
        except zlib.error:
            continue
        marker = decoded.find(b'WUP-J')
        if marker < 0 or marker < 0x24:
            continue
        base = marker - 0x24
        if base + 0x30 > len(decoded):
            continue
        block = decoded[base:base + 0x30]
        total, rom_rel, extra_rel = struct.unpack_from('<III', block, 4)
        if rom_rel < 0x30 or extra_rel <= rom_rel or base+total > len(decoded):
            continue
        old_rom = decoded[base+rom_rel:base+extra_rel]
        try:
            _rom_header(old_rom)
        except InjectionError:
            continue
        matching.append((i, off, size, decoded, base, rom_rel, extra_rel, old_rom))
    if len(matching) != 1:
        raise InjectionError(f'Expected one LoROM VC payload, got {len(matching)}')
    i, sec_off, sec_size, decoded, base, rom_rel, extra_rel, old_rom = matching[0]
    expected_crc = struct.unpack_from('>I', original, crc_off+i*4)[0]
    if expected_crc != zlib.crc32(decoded):
        raise InjectionError('Original uncompressed data does not match RPX CRC section')
    name, rom, copier, max_mirrors = _prepare_target(target,len(old_rom))
    rom_start=base+rom_rel
    rom_end=base+extra_rel
    # Mirror into as many early banks as possible without exceeding the donor's
    # reserved compressed-section bytes. Leave remaining banks as 0xFF fill.
    # This is experimental, not native bank-mirroring emulation.
    for copies in range(max_mirrors, 0, -1):
        padded = rom * copies + bytes([0xFF]) * (len(old_rom) - len(rom)*copies)
        modified=decoded[:rom_start]+padded+decoded[rom_end:]
        assert len(modified)==len(decoded)
        packed = len(modified).to_bytes(4,'big') + zlib.compress(modified,6)
        if len(packed) <= sec_size:
            break
    else:
        raise InjectionError('All padding choices exceed the donor compressed-section capacity')
    out=bytearray(original)
    out[sec_off:sec_off+len(packed)]=packed
    out[sec_off+len(packed):sec_off+sec_size]=bytes(sec_size-len(packed))
    shoff=struct.unpack_from('>I',original,0x20)[0]
    struct.pack_into('>I',out,shoff+i*40+20,len(packed))
    struct.pack_into('>I',out,crc_off+i*4,zlib.crc32(modified)&0xffffffff)
    new_section=zlib.decompress(out[sec_off+4:sec_off+len(packed)])
    if new_section != modified or new_section[rom_end:] != decoded[rom_end:]:
        raise InjectionError('RPX round-trip data verification failed')
    if out[crc_off:crc_off+shnum*4] != original[crc_off:crc_off+shnum*4][:i*4]+(zlib.crc32(modified)&0xffffffff).to_bytes(4,'big')+ original[crc_off+(i+1)*4:crc_off+shnum*4]:
        raise InjectionError('Unexpected CRC table mutation')
    report={
        'status':'built_unverified_not_installable_wup',
        'donor_title_code':decoded[base+0x24:base+0x2c].decode('ascii'),
        'game_title':name,
        'original_rpx_sha256':rpx_sha,
        'patched_rpx_sha256':sha256(out).hexdigest(),
        'target_rom_sha256':sha256(target).hexdigest(),
        'target_rom_bytes':len(target)-copier,
        'removed_copier_header_bytes':copier,
        'donor_rom_capacity_bytes':len(old_rom),
        'mirroring_count':copies,
        'padding_bytes':len(old_rom)-len(rom)*copies,
        'rom_section':i,
        'rom_section_uncompressed_bytes':len(modified),
        'rom_section_original_compressed_bytes':sec_size,
        'rom_section_new_compressed_bytes':len(packed),
        'section_crc32':f'{zlib.crc32(modified)&0xffffffff:08X}',
        'preserved_appended_vc_bytes':True,
        'preserved_other_elf_sections':True,
        'warnings':[
            'Experimental test only, not boot-tested on Wii U or Cemu.',
            'Donor game-specific PCM/configuration may not suit this game.',
            'Some upper ROM banks are 0xFF padding and not mirrored, so bank mapping is unverified.',
            'Retains Super Metroid title ID, icon and metadata; do not install over your legitimate Super Metroid.',
            'Decrypted RPX/Loadiine folder is not an encrypted installable WUP title.',
            'SNES SRAM, suspend state, graphics, audio and native VC compatibility are unverified.'
        ]
    }
    return bytes(out),report


def patch_rpx_file(donor: str | Path, rom: str | Path, output: str | Path):
    donor_path,rom_path,outpath=Path(donor),Path(rom),Path(output)
    patched,report=patch_rpx_bytes(donor_path.read_bytes(),rom_path.read_bytes())
    if outpath.resolve()==donor_path.resolve():
        raise InjectionError('Refusing to overwrite the donor RPX')
    outpath.parent.mkdir(parents=True,exist_ok=True)
    outpath.write_bytes(patched)
    return report
