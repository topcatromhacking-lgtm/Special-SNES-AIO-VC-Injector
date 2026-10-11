"""Read-only SNES ROM, Wii U encrypted WUP, and decrypted Wii U RPX inspection."""
from __future__ import annotations
import argparse
import json
import sys
from .analyzer import RomAnalysisError, analyze_rom
from .donor import DonorInspectionError, inspect_wup_zip
from .wiiu_rpx import RpxInspectionError, inspect_wiiu_rpx

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Inspect SNES ROM and Wii U VC metadata')
    parser.add_argument('input', help='ROM file, encrypted WUP donor ZIP, RPX, or decrypted donor ZIP')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--donor', action='store_true', help='Inspect encrypted Wii U WUP/NUS ZIP metadata')
    mode.add_argument('--rpx', action='store_true', help='Inspect local Wii U SNES RPX or decrypted donor ZIP')
    parser.add_argument('--json', action='store_true', help='Output a JSON report')
    args = parser.parse_args(argv)
    try:
        if args.rpx:
            info = inspect_wiiu_rpx(args.input)
        elif args.donor:
            info = inspect_wup_zip(args.input)
        else:
            info = analyze_rom(args.input)
    except (RomAnalysisError, DonorInspectionError, RpxInspectionError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(info.as_dict(), indent=2, ensure_ascii=False))
    elif args.rpx:
        print(f'VC title: {info.title_code}; Embedded ROM: {info.internal_title}')
        print(f'Mapping: {info.mapping}; ROM bytes: {info.rom_size}')
        print(f'Compressed RPX size: {info.rpx_size}; Data section: {info.section_index}')
        print(f'ROM position in uncompressed data: 0x{info.rom_offset:X}')
        print(f'Additional data: 0x{info.extra_data_offset:X} ({info.extra_data_bytes} bytes)')
        for note in info.notes:
            print(f'Note: {note}')
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
