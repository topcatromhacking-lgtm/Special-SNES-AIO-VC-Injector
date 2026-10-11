"""Synthetic Wii U SNES RPX LoROM replacement tests; no commercial assets."""
import unittest
import tempfile
import struct
import zlib
from pathlib import Path
from snes_vc_injector.wiiu_inject import InjectionError, patch_rpx_bytes
from snes_vc_injector.wiiu_rpx import inspect_wiiu_rpx
from test_wiiu_rpx import make_fixture as make_fixture_original


def make_small_lorom(size=0x80000, cart=0x02):
    rom = bytearray(size)
    rom[0x7FC0:0x7FC0+16] = b'SYNTHETIC TARGET'
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = cart
    rom[0x7FDC:0x7FDE] = (0x1234).to_bytes(2,'little')
    rom[0x7FDE:0x7FE0] = (0xEDCB).to_bytes(2,'little')
    return bytes(rom)


def make_fixture():
    raw=bytearray(make_fixture_original())
    struct.pack_into('>H',raw,0x30,3)
    struct.pack_into('>10I',raw,0x40+2*40,0,0x80000003,0,0,0x160,12,0,0,4,0)
    section_offset=0x200
    from_zlib=zlib.decompress(raw[section_offset+4:])
    struct.pack_into('>I',raw,0x160+4,zlib.crc32(from_zlib))
    # Reserve synthetic disk allocation that can accept a larger new zlib stream.
    current=struct.unpack_from('>I',raw,0x40+40+20)[0]
    raw.extend(bytes(4096))
    struct.pack_into('>I',raw,0x40+40+20,current+4096)
    return bytes(raw)


class InjectTests(unittest.TestCase):
    def test_replace_and_preserve_trailing_assets(self):
        original = make_fixture()
        injected, report = patch_rpx_bytes(original, make_small_lorom())
        self.assertEqual(len(injected),len(original))
        self.assertEqual(report['game_title'],'SYNTHETIC TARGET')
        self.assertEqual(report['target_rom_bytes'],0x80000)
        self.assertEqual(report['donor_rom_capacity_bytes'],0x100000)
        self.assertEqual(report['mirroring_count'],2)
        self.assertEqual(report['padding_bytes'],0)
        self.assertEqual(inspect_wiiu_from_bytes(injected).internal_title,'SYNTHETIC TARGET')
        self.assertEqual(original[:0x7C], injected[:0x7C])
        self.assertEqual(original[0x80:0x90], injected[0x80:0x90])
        self.assertEqual(injected[-8:], original[-8:])

    def test_copier_header_removed(self):
        _, report = patch_rpx_bytes(make_fixture(), bytes(512) + make_small_lorom())
        self.assertEqual(report['removed_copier_header_bytes'],512)

    def test_special_chip_rejected(self):
        with self.assertRaises(InjectionError):
            patch_rpx_bytes(make_fixture(), make_small_lorom(cart=0x45))

    def test_target_too_large_rejected(self):
        with self.assertRaises(InjectionError):
            patch_rpx_bytes(make_fixture(), make_small_lorom(size=0x200000))

    def test_invalid_input_rejected(self):
        with self.assertRaises(InjectionError):
            patch_rpx_bytes(b'not an ELF',make_small_lorom())


def inspect_wiiu_from_bytes(binary):
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'synthetic.rpx'
        path.write_bytes(binary)
        return inspect_wiiu_rpx(path)


if __name__=='__main__':
    unittest.main()
