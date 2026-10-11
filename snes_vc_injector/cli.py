"""Metadata-only command line interface."""
from __future__ import annotations

import argparse
import json
import sys

from .analyzer import RomAnalysisError, analyze_rom


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a SNES ROM without modifying it")
    parser.add_argument("rom", help="Local .sfc or .smc ROM file")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON report")
    args = parser.parse_args(argv)
    try:
        info = analyze_rom(args.rom)
    except RomAnalysisError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(info.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"Title: {info.title}\nFamily: {info.family}\nMapping: {info.header_mapping}")
        print(f"Map mode: {info.map_mode}; Cartridge type: {info.cartridge_type}")
        print(f"Enhancement chip: {info.enhancement_chip}; Header confidence: {info.header_confidence}")
        print(f"ROM size: {info.rom_bytes} bytes; Copier header: {info.copier_header_bytes} bytes")
        print(f"Original-file SHA-256: {info.sha256}")
        for warning in info.warnings:
            print(f"Note: {warning}")
    return 0
