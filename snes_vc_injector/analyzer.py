"""Conservative SNES cartridge header analyzer.

ROM identification does not establish Wii, Wii U, or 3DS VC compatibility.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

HEADER_LOCATIONS = (
    ("LoROM", 0x7FC0, {0x20, 0x22, 0x23, 0x30, 0x32, 0x33}),
    ("HiROM", 0xFFC0, {0x21, 0x25, 0x31, 0x35}),
    ("ExHiROM", 0x40FFC0, {0x25, 0x35}),
)


class RomAnalysisError(ValueError):
    """ROM could not be read or lacked a plausible SNES header."""


@dataclass(frozen=True)
class RomInfo:
    path: str
    sha256: str
    file_bytes: int
    rom_bytes: int
    copier_header_bytes: int
    title: str
    header_mapping: str
    header_offset: int
    map_mode: str
    cartridge_type: str
    rom_size_code: int
    sram_size_code: int
    region_code: int
    enhancement_chip: str
    family: str
    header_confidence: str
    warnings: tuple[str, ...]

    def as_dict(self) -> dict:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result


def _score_header(payload: bytes, offset: int, expected_modes: set[int]) -> int:
    header = payload[offset:offset + 0x40]
    if len(header) != 0x40:
        return -100
    score = 8 if header[0x15] in expected_modes else 0
    complement = int.from_bytes(header[0x1C:0x1E], "little")
    checksum = int.from_bytes(header[0x1E:0x20], "little")
    if complement ^ checksum == 0xFFFF:
        score += 4
    title = header[:21].rstrip(b"\x00 ")
    if title and all(0x20 <= char <= 0x7E for char in title):
        score += 2
    reset = int.from_bytes(header[0x3C:0x3E], "little")
    if 0x8000 <= reset <= 0xFFFF:
        score += 2
    if 7 <= header[0x17] <= 14:
        score += 1
    return score


def _chip(mode: int, cart: int) -> str:
    if mode == 0x32 and cart in (0x43, 0x45):
        return "S-DD1"
    if mode in (0x23, 0x33) and cart in (0x34, 0x35):
        return "SA-1"
    if cart in (0x13, 0x14, 0x15, 0x1A) and mode in (0x20, 0x30):
        return "Super FX family (candidate)"
    if cart in (0x03, 0x05, 0x06):
        return "DSP family (candidate)"
    return "None identified"


def _family(mapping: str, chip: str, title: str) -> str:
    if chip == "S-DD1":
        normalized = " ".join(title.upper().split())
        if normalized.startswith("STAR OCEAN"):
            return "sdd1_star_ocean"
        if normalized.startswith("STREET FIGHTER ALPHA") or normalized.startswith("STREET FIGHTER ZERO"):
            return "sdd1_sfa2"
        return "sdd1_unidentified"
    if chip != "None identified":
        return "other_enhancement_chip"
    if mapping == "ExHiROM":
        return "exhirom"
    if mapping in ("LoROM", "HiROM"):
        return "standard"
    return "unknown"


def analyze_rom(path: str | Path) -> RomInfo:
    rom_path = Path(path)
    try:
        original = rom_path.read_bytes()
    except OSError as exc:
        raise RomAnalysisError(f"Cannot read ROM: {exc}") from exc

    # Heuristic for conventional 512-byte copier headers.
    copier = 512 if len(original) % 0x8000 == 512 else 0
    payload = original[copier:]
    candidates = []
    for mapping, offset, expected_modes in HEADER_LOCATIONS:
        if len(payload) >= offset + 0x40:
            score = _score_header(payload, offset, expected_modes)
            # A 0x25/0x35 HiROM-position header may mirror ExHiROM.
            if mapping == "HiROM" and payload[offset + 0x15] in (0x25, 0x35):
                score -= 3
            candidates.append((score, mapping, offset))
    if not candidates:
        raise RomAnalysisError("File too small for an SNES internal header")
    score, mapping, offset = max(candidates, key=lambda item: item[0])
    if score < 10:
        raise RomAnalysisError("No sufficiently plausible SNES internal header found")

    header = payload[offset:offset + 0x40]
    raw_title = header[:21].rstrip(b"\x00 ")
    title = "".join(chr(c) if 0x20 <= c <= 0x7E else "?" for c in raw_title)
    mode, cart = header[0x15], header[0x16]
    chip = _chip(mode, cart)
    family = _family(mapping, chip, title)
    warnings: list[str] = []
    if copier:
        warnings.append("Possible 512-byte copier header excluded from SNES header offsets")
    if mapping == "HiROM" and mode in (0x25, 0x35):
        warnings.append("Expanded map-mode byte in HiROM-position header: verify ExHiROM layout")
    if family == "sdd1_unidentified":
        warnings.append("S-DD1 present but title does not establish SFA2 or Star Ocean treatment")
    if family in ("sdd1_star_ocean", "sdd1_sfa2"):
        warnings.append("S-DD1 game recognition is title-based and provisional, particularly for ROM hacks")
    if family == "other_enhancement_chip":
        warnings.append("Enhancement-chip identification is tentative, not a native VC support claim")
    if score < 15:
        warnings.append("Incomplete or inconsistent internal header signals; manual inspection recommended")
    warnings.append("Identification does not prove VC packaging, hardware, SRAM or suspend compatibility")

    return RomInfo(
        path=str(rom_path), sha256=sha256(original).hexdigest(),
        file_bytes=len(original), rom_bytes=len(payload),
        copier_header_bytes=copier, title=title, header_mapping=mapping,
        header_offset=offset, map_mode=f"0x{mode:02X}",
        cartridge_type=f"0x{cart:02X}", rom_size_code=header[0x17],
        sram_size_code=header[0x18], region_code=header[0x19],
        enhancement_chip=chip, family=family,
        header_confidence="high" if score >= 15 else "moderate",
        warnings=tuple(warnings),
    )
