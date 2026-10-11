"""Synthetic fixture tests: no Nintendo binaries, ROMs, or title files."""
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import struct
import zlib
from snes_vc_injector.wiiu_rpx import RpxInspectionError, inspect_wiiu_rpx

def make_fixture(broken_pointer=False):
    rom = bytearray(0x100000)
    off = 0x7FC0
    rom[off:off + 13] = b'SYNTHETIC ROM'
    rom[off + 0x15] = 0x30
    rom[off + 0x16] = 0x02
    rom[off + 0x1C:off + 0x1E] = (0xEDCB).to_bytes(2, 'little')
    rom[off + 0x1E:off + 0x20] = (0x1234).to_bytes(2, 'little')
    data = bytearray(0x20)
    header = bytearray(0x30)
    header[:4] = (0x100).to_bytes(4, 'little')
    header[4:8] = (0x30 + len(rom) + 64).to_bytes(4, 'little')
    header[8:12] = (0x30).to_bytes(4, 'little')
    header[12:16] = (0x30 + len(rom) + (10000000 if broken_pointer else 0)).to_bytes(4, 'little')
    header[0x24:0x2C] = b'WUP-JTST'
    data.extend(header)
    data.extend(rom)
    data.extend(bytes(64))
    raw = zlib.compress(data)
    section = len(data).to_bytes(4, 'big') + raw
    output = bytearray(0x200 + len(section))
    struct.pack_into('>16sHHIIIIIHHHHHH', output, 0, b'\x7fELF\x01\x02' + bytes(10),
                     0xFE01, 20, 1, 0, 0, 0x40, 0, 52, 0, 0, 40, 2, 0)
    struct.pack_into('>10I', output, 0x40 + 40, 0, 1, 0x08000003, 0x10000000, 0x200,
                     len(section), 0, 0, 4, 0)
    output[0x200:] = section
    return bytes(output)

class RpxTests(unittest.TestCase):
    def write_test(self, content, suffix='.rpx'):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / ('test' + suffix)
            if suffix == '.zip':
                with ZipFile(path, 'w') as z:
                    z.writestr('code/WUP-JTST.rpx', content)
            else:
                path.write_bytes(content)
            return inspect_wiiu_rpx(path)

    def test_rom_structure(self):
        result = self.write_test(make_fixture())
        self.assertEqual(result.title_code, 'WUP-JTST')
        self.assertEqual(result.internal_title, 'SYNTHETIC ROM')
        self.assertEqual(result.mapping, 'LoROM')
        self.assertEqual(result.rom_size, 0x100000)
        self.assertEqual(result.rom_offset, 0x50)
        self.assertEqual(result.extra_data_offset, 0x100050)
        self.assertEqual(result.extra_data_bytes, 64)

    def test_zipped_decrypted_donor(self):
        self.assertEqual(self.write_test(make_fixture(), '.zip').rom_size, 0x100000)

    def test_wrong_pointer_rejected(self):
        with self.assertRaises(RpxInspectionError):
            self.write_test(make_fixture(broken_pointer=True))

    def test_invalid_elf_rejected(self):
        with self.assertRaises(RpxInspectionError):
            self.write_test(bytes(100))

if __name__ == '__main__':
    unittest.main()
