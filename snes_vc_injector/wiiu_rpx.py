"""Read-only Wii U SNES Virtual Console RPX embedded-ROM inspector.

Parses compressed ELF sections and SNES payload pointers; does not extract,
modify, or redistribute ROMs, tickets, keys, or proprietary emulator files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import struct
from zipfile import BadZipFile, ZipFile
import zlib

MAX_RPX = 64 * 1024 * 1024
MAX_SECTION = 64 * 1024 * 1024
RPL_ZLIB_FLAG = 0x08000000


class RpxInspectionError(ValueError):
    """Unsupported or malformed SNES Wii U VC RPX."""


@dataclass(frozen=True)
class EmbeddedSnesRom:
    source: str
    rpx_sha256: str
    rpx_size: int
    section_index: int
    section_decompressed_bytes: int
    title_code: str
    internal_title: str
    mapping: str
    cartridge_type_hex: str
    rom_size: int
    rom_sha256: str
    vc_header_offset: int
    rom_offset: int
    extra_data_offset: int
    extra_data_bytes: int
    notes: tuple[str, ...]

    def as_dict(self) -> dict:
        result = asdict(self)
        result['notes'] = list(self.notes)
        return result


def _read_rpx(path: Path) -> bytes:
    try:
        if path.suffix.lower() == '.zip':
            with ZipFile(path) as archive:
                matches = [x for x in archive.infolist()
                           if not x.is_dir() and x.filename.lower().startswith('code/')
                           and x.filename.lower().endswith('.rpx')]
                if len(matches) != 1:
                    raise RpxInspectionError('ZIP must contain exactly one code/*.rpx')
                if matches[0].file_size > MAX_RPX:
                    raise RpxInspectionError('RPX exceeds inspection size limit')
                return archive.read(matches[0])
        if path.stat().st_size > MAX_RPX:
            raise RpxInspectionError('RPX exceeds inspection size limit')
        return path.read_bytes()
    except (OSError, BadZipFile, RuntimeError, EOFError) as exc:
        raise RpxInspectionError(f'Cannot read RPX: {exc}') from exc


def _sections(rpx: bytes):
    if len(rpx) < 52 or rpx[:6] != b'\x7fELF\x01\x02':
        raise RpxInspectionError('Expected 32-bit big-endian ELF/RPX')
    hdr = struct.unpack_from('>16sHHIIIIIHHHHHH', rpx)
    shoff, shentsize, shnum = hdr[6], hdr[11], hdr[12]
    if shnum == 0 or shnum > 200 or shentsize != 40 or shoff + shentsize * shnum > len(rpx):
        raise RpxInspectionError('Invalid ELF section table')
    for idx in range(shnum):
        _, stype, flags, addr, pos, size, _, _, _, _ = struct.unpack_from(
            '>10I', rpx, shoff + idx * shentsize)
        if stype != 1 or size == 0 or pos + size > len(rpx):
            continue
        if flags & RPL_ZLIB_FLAG:
            if size < 6:
                raise RpxInspectionError('Truncated compressed RPX section')
            declared = int.from_bytes(rpx[pos:pos + 4], 'big')
            if declared > MAX_SECTION:
                raise RpxInspectionError('Uncompressed RPX section exceeds safety limit')
            try:
                inflator = zlib.decompressobj()
                data = inflator.decompress(rpx[pos + 4:pos + size], MAX_SECTION + 1)
                data += inflator.flush(MAX_SECTION + 1 - len(data))
            except zlib.error as exc:
                raise RpxInspectionError(f'RPX section {idx} failed decompression') from exc
            if len(data) != declared or not inflator.eof:
                raise RpxInspectionError(f'RPX section {idx} uncompressed size mismatch')
        else:
            data = rpx[pos:pos + size]
        yield idx, data


def _identify_header(rom: bytes) -> tuple[str, str, str]:
    candidates = []
    for mapping, offset in (('LoROM', 0x7FC0), ('HiROM', 0xFFC0), ('ExHiROM', 0x40FFC0)):
        if len(rom) < offset + 0x40:
            continue
        h = rom[offset:offset + 0x40]
        title = h[:21].rstrip(b'\x00 ')
        if not title or not all(0x20 <= b <= 0x7E for b in title):
            continue
        complementary = (int.from_bytes(h[0x1C:0x1E], 'little') ^
                         int.from_bytes(h[0x1E:0x20], 'little')) == 0xFFFF
        mode = h[0x15]
        consistent = (mapping == 'LoROM' and mode in (0x20, 0x22, 0x30, 0x32)) or (
            mapping == 'HiROM' and mode in (0x21, 0x31)) or (
            mapping == 'ExHiROM' and mode in (0x25, 0x35))
        if complementary and consistent:
            candidates.append((mapping, title.decode('ascii'), f'0x{h[0x16]:02X}'))
    if len(candidates) != 1:
        raise RpxInspectionError('ROM mapping header missing or ambiguous')
    return candidates[0]


def inspect_wiiu_rpx(path: str | Path) -> EmbeddedSnesRom:
    """Locate an SNES VC payload inside one local RPX or decrypted-donor ZIP."""
    source = Path(path)
    rpx = _read_rpx(source)
    found = []
    for section_index, data in _sections(rpx):
        cursor = 0
        while True:
            marker = data.find(b'WUP-J', cursor)
            if marker == -1:
                break
            cursor = marker + 5
            base = marker - 0x24
            if base < 0 or len(data) < base + 0x30:
                continue
            header = data[base:base + 0x30]
            code = header[0x24:0x2C]
            if not code.startswith(b'WUP-J') or not all(0x30 <= x <= 0x5A for x in code[5:]):
                continue
            if header[0x2C:0x30] != b'\x00' * 4:
                continue
            total, rom_rel, extra_rel = struct.unpack_from('<III', header, 4)
            if rom_rel < 0x30 or extra_rel <= rom_rel or total < extra_rel:
                continue
            rom_start, extra_start, end = base + rom_rel, base + extra_rel, base + total
            if end > len(data):
                continue
            rom = data[rom_start:extra_start]
            try:
                mapping, title, cart = _identify_header(rom)
            except RpxInspectionError:
                continue
            found.append(EmbeddedSnesRom(
                source=str(source), rpx_sha256=sha256(rpx).hexdigest(),
                rpx_size=len(rpx), section_index=section_index,
                section_decompressed_bytes=len(data), title_code=code.decode('ascii'),
                internal_title=title, mapping=mapping, cartridge_type_hex=cart,
                rom_size=len(rom), rom_sha256=sha256(rom).hexdigest(),
                vc_header_offset=base, rom_offset=rom_start, extra_data_offset=extra_start,
                extra_data_bytes=end - extra_start,
                notes=(
                    'Offsets are relative to the decompressed RPX section, not the RPX file.',
                    'Additional data must be preserved and pointers updated when growing a ROM.',
                    'The SNES ROM may contain Nintendo VC-specific patches or altered data.',
                    'No ROM injection, native compatibility, or suspend/restore functionality is established.'
                ),
            ))
    if len(found) != 1:
        raise RpxInspectionError(f'Expected one valid SNES VC payload; found {len(found)}')
    return found[0]
