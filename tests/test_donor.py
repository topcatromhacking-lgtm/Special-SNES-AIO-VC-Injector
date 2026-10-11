"""Synthetic Wii U TMD/H3 fixtures; no Nintendo files are distributed."""
import tempfile
import unittest
from hashlib import sha1
from pathlib import Path
from zipfile import ZipFile
from snes_vc_injector.donor import DonorInspectionError, inspect_wup_zip

def synthetic_tmd(app_size=64, hashed=True):
    tmd = bytearray(0xB04 + 0x30)
    tmd[0:4] = (0x00010004).to_bytes(4, 'big')
    tmd[0x18C:0x194] = bytes.fromhex('000500001010A600')
    tmd[0x1DE:0x1E0] = (1).to_bytes(2, 'big')
    offset = 0xB04
    tmd[offset:offset+4] = (0).to_bytes(4, 'big')
    tmd[offset+6:offset+8] = (0x2003 if hashed else 0x2001).to_bytes(2, 'big')
    tmd[offset+8:offset+16] = app_size.to_bytes(8, 'big')
    if hashed:
        tmd[offset+16:offset+36] = sha1(bytes(20)).digest()
    return bytes(tmd)

class DonorTests(unittest.TestCase):
    def inspect(self, *, tmd=None, app=bytes(64), h3=bytes(20), nested=True):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'donor.zip'
            prefix = 'Super Metroid/' if nested else ''
            with ZipFile(path, 'w') as z:
                if tmd is not False:
                    z.writestr(prefix+'title.tmd', tmd if tmd is not None else synthetic_tmd())
                if app is not None:
                    z.writestr(prefix+'00000000.app', app)
                if h3 is not None:
                    z.writestr(prefix+'00000000.h3', h3)
                z.writestr(prefix+'title.tik', b'dummy bytes')
            return inspect_wup_zip(path)

    def test_valid_nested_metadata(self):
        r = self.inspect()
        self.assertTrue(r.metadata_consistent)
        self.assertEqual(r.title_id, '000500001010A600')
        self.assertTrue(r.ticket_present)
        self.assertTrue(r.contents[0].h3_hash_matches_tmd)

    def test_valid_flat_metadata(self):
        self.assertTrue(self.inspect(nested=False).metadata_consistent)

    def test_mismatched_app_size(self):
        self.assertFalse(self.inspect(app=bytes(32)).metadata_consistent)

    def test_missing_h3(self):
        self.assertFalse(self.inspect(h3=None).metadata_consistent)

    def test_incorrect_h3(self):
        self.assertFalse(self.inspect(h3=bytes(21)).metadata_consistent)

    def test_unhashed_app(self):
        self.assertTrue(self.inspect(tmd=synthetic_tmd(hashed=False), h3=None).metadata_consistent)

    def test_missing_tmd(self):
        with self.assertRaises(DonorInspectionError):
            self.inspect(tmd=False)

    def test_bad_tmd(self):
        with self.assertRaises(DonorInspectionError):
            self.inspect(tmd=b'broken')

if __name__ == '__main__':
    unittest.main()
