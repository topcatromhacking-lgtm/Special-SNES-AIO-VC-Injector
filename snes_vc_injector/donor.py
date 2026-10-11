"""Read-only Wii U encrypted WUP/NUS donor ZIP metadata.

No ticket/key parsing, content decryption, extraction, or ROM modification.
Matching TMD-H3 hashes do NOT validate encrypted .app contents.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha1
from pathlib import Path
from zipfile import BadZipFile, ZipFile

class DonorInspectionError(ValueError):
    """Malformed, unsupported, or unreadable donor metadata."""

@dataclass(frozen=True)
class WupContent:
    content_id: str
    index: int
    content_type: str
    declared_bytes: int
    archive_bytes: int | None
    h3_required: bool
    h3_present: bool
    h3_hash_matches_tmd: bool | None
    status: str

@dataclass(frozen=True)
class WupDonor:
    source: str
    title_id: str
    title_version: int
    contents_count: int
    contents: tuple[WupContent, ...]
    ticket_present: bool
    certificate_present: bool
    metadata_consistent: bool
    warnings: tuple[str, ...]

    def as_dict(self) -> dict:
        result = asdict(self)
        result["contents"] = [asdict(c) for c in self.contents]
        result["warnings"] = list(self.warnings)
        return result

def inspect_wup_zip(path: str | Path) -> WupDonor:
    """Examine installable Wii U title archive; never unpack or decrypt contents."""
    archive_path = Path(path)
    try:
        with ZipFile(archive_path) as z:
            names = [name for name in z.namelist() if not name.endswith("/")]
            tmd_names = [n for n in names if n.rsplit("/", 1)[-1] == "title.tmd"]
            if len(tmd_names) != 1:
                raise DonorInspectionError("Exactly one title.tmd is required")
            prefix = tmd_names[0].rsplit("/", 1)[0] + "/" if "/" in tmd_names[0] else ""
            if len(names) != len(set(names)):
                raise DonorInspectionError("Duplicate file paths in ZIP")
            available = set(names)
            tmd = z.read(prefix + "title.tmd")
            # Wii U RSA-2048/SHA-256 signed TMD: fixed content records at 0xB04.
            if len(tmd) < 0xB04 or int.from_bytes(tmd[:4], "big") != 0x00010004:
                raise DonorInspectionError("Unsupported or truncated Wii U TMD")
            count = int.from_bytes(tmd[0x1DE:0x1E0], "big")
            if not count or 0xB04 + count * 0x30 > len(tmd):
                raise DonorInspectionError("Invalid TMD content count/table")
            title_id = tmd[0x18C:0x194].hex().upper()
            version = int.from_bytes(tmd[0x1DC:0x1DE], "big")
            results = []
            warnings = []
            for index in range(count):
                record = tmd[0xB04 + index * 0x30:0xB04 + (index + 1) * 0x30]
                content_id = record[:4].hex()
                content_index = int.from_bytes(record[4:6], "big")
                ctype = int.from_bytes(record[6:8], "big")
                size = int.from_bytes(record[8:16], "big")
                expected_h3_hash = record[16:36]
                app_name, h3_name = prefix + content_id + ".app", prefix + content_id + ".h3"
                zip_info = z.getinfo(app_name) if app_name in available else None
                actual_size = zip_info.file_size if zip_info else None
                h3_present = h3_name in available
                h3_required = bool(ctype & 0x2)
                h3_matches = sha1(z.read(h3_name)).digest() == expected_h3_hash if h3_present else None
                valid = (actual_size == size) and (not h3_required or h3_matches is True)
                status = "metadata_ok" if valid else "metadata_mismatch"
                if not valid:
                    warnings.append(f"Content {content_id}: missing/mismatched .app or required .h3")
                results.append(WupContent(
                    content_id=content_id, index=content_index, content_type=f"0x{ctype:04X}",
                    declared_bytes=size, archive_bytes=actual_size, h3_required=h3_required,
                    h3_present=h3_present, h3_hash_matches_tmd=h3_matches, status=status,
                ))
            warnings.append("Encrypted .app bytes not decrypted or cryptographically verified")
            warnings.append("Supply a locally decrypted code/content/meta tree for VC emulator and ROM analysis")
            return WupDonor(
                source=str(archive_path), title_id=title_id, title_version=version,
                contents_count=count, contents=tuple(results),
                ticket_present=prefix + "title.tik" in available,
                certificate_present=prefix + "title.cert" in available,
                metadata_consistent=all(c.status == "metadata_ok" for c in results),
                warnings=tuple(warnings),
            )
    except (OSError, BadZipFile, RuntimeError, EOFError, ValueError) as exc:
        if isinstance(exc, DonorInspectionError):
            raise
        raise DonorInspectionError(f"Cannot inspect ZIP: {exc}") from exc
