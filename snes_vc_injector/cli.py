"""Read-only SNES ROM and encrypted Wii U WUP donor inspection CLI."""
from __future__ import annotations
import argparse
import json
import sys
from .analyzer import RomAnalysisError, analyze_rom
from .donor import DonorInspectionError, inspect_wup_zip

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Inspect SNES ROMs or encrypted Wii U WUP donor ZIPs')
    parser.add_argument('input', help='SNES .sfc/.smc file or Wii U donor ZIP')
    parser.add_argument('--donor', action='store_true', help='Inspect Wii U WUP/NUS donor metadata instead of a ROM')
    parser.add_argument('--json', action='store_true', help='Output a JSON report')
    args = parser.parse_args(argv)
    try:
        if args.donor:
            info = inspect_wup_zip(args.input)
        else:
            info = analyze_rom(args.input)
    except (RomAnalysisError, DonorInspectionError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(info.as_dict(), indent=2, ensure_ascii=False))
    elif args.donor:
        print(f'Title ID: {info.title_id}\nTitle version: {info.title_version}')
        print(f'Content files: {info.contents_count}; metadata consistent: {info.metadata_consistent}')
        for content in info.contents:
            print(f'  {content.content_id}.app: {content.archive_bytes} bytes; {content.status}; '
                  f'H3 match: {content.h3_hash_matches_tmd}')
        for warning in info.warnings:
            print(f'Note: {warning}')
    else:
        print(f'Title: {info.title}\nFamily: {info.family}\nMapping: {info.header_mapping}')
        print(f'Map mode: {info.map_mode}; Cartridge type: {info.cartridge_type}')
        print(f'Enhancement chip: {info.enhancement_chip}; Header confidence: {info.header_confidence}')
        print(f'ROM size: {info.rom_bytes} bytes; Copier header: {info.copier_header_bytes} bytes')
        print(f'Original-file SHA-256: {info.sha256}')
        for warning in info.warnings:
            print(f'Note: {warning}')
    return 0
