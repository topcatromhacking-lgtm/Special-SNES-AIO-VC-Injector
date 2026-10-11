"""Build an experimental decrypted Wii U SNES LoROM donor ZIP, locally only.

No Nintendo binaries are bundled with this program. Requires user's own
(decrypted) code/content/meta donor ZIP and SNES ROM or ZIP containing ROM.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from .wiiu_inject import InjectionError, patch_rpx_bytes

MAX_ROM_ARCHIVE_SIZE = 12 * 1024 * 1024
MAX_RPX_SIZE = 64 * 1024 * 1024


def read_rom(path: Path) -> bytes:
    if path.suffix.lower() != '.zip':
        if path.stat().st_size > MAX_ROM_ARCHIVE_SIZE:
            raise InjectionError('ROM input exceeds 12 MiB limit')
        return path.read_bytes()
    with ZipFile(path) as src:
        files = [f for f in src.infolist() if not f.is_dir() and f.filename.lower().endswith(('.sfc', '.smc'))]
        if len(files) != 1:
            raise InjectionError('ROM ZIP must contain exactly one .sfc/.smc file')
        if files[0].file_size > MAX_ROM_ARCHIVE_SIZE:
            raise InjectionError('ROM ZIP entry exceeds 12 MiB limit')
        return src.read(files[0])


def build_decrypted_donor(donor_zip: Path, rom: bytes, result_zip: Path) -> dict:
    if donor_zip.resolve() == result_zip.resolve():
        raise InjectionError('Output must not overwrite input donor ZIP')
    with ZipFile(donor_zip) as donor:
        info = [x for x in donor.infolist() if not x.is_dir()]
        rp = [x for x in info if x.filename.startswith('code/') and x.filename.lower().endswith('.rpx')]
        if len(rp) != 1:
            raise InjectionError('Donor ZIP must contain exactly one code/*.rpx')
        if rp[0].file_size > MAX_RPX_SIZE:
            raise InjectionError('Donor RPX exceeds 64 MiB limit')
        names = set(donor.namelist())
        if len(names) != len(donor.namelist()):
            raise InjectionError('Donor ZIP contains duplicate file names')
        if not any(n.startswith('content/') for n in names) or not any(n.startswith('meta/') for n in names):
            raise InjectionError('Donor must contain code/content/meta directories')
        patched, report = patch_rpx_bytes(donor.read(rp[0]),rom)
        report['patched_file_path'] = rp[0].filename
        report['format'] = 'decrypted_code_content_meta_zip'
        result_zip.parent.mkdir(parents=True,exist_ok=True)
        try:
            with ZipFile(result_zip,'w') as out:
                for f in donor.infolist():
                    if f.is_dir():
                        out.writestr(f, b'')
                    else:
                        data = patched if f.filename == rp[0].filename else donor.read(f)
                        out.writestr(f,data)
        except BaseException:
            result_zip.unlink(missing_ok=True)
            raise
    with ZipFile(donor_zip) as donor, ZipFile(result_zip) as result:
        for f in donor.infolist():
            if f.is_dir():
                continue
            if f.filename == report['patched_file_path']:
                if result.read(f.filename) != patched:
                    raise InjectionError('Output RPX content mismatch')
            elif donor.read(f.filename) != result.read(f.filename):
                raise InjectionError('Unintended modification of donor asset: ' + f.filename)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Experimental decrypted Wii U SNES LoROM injector')
    parser.add_argument('--donor',type=Path,required=True,help='Decrypted Wii U VC donor ZIP (code/content/meta)')
    parser.add_argument('--rom',type=Path,required=True,help='Local target .sfc/.smc or ROM ZIP')
    parser.add_argument('--output',type=Path,required=True,help='Output decrypted donor ZIP')
    args = parser.parse_args(argv)
    try:
        result = build_decrypted_donor(args.donor,read_rom(args.rom),args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2,'Injection error: '+str(exc)+'\n')
    report_path=args.output.with_suffix('.json')
    report_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Build completed. Native VC compatibility NOT tested.')
    print('Decrypted output:',args.output)
    print('Build report:',report_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
