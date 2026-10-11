"""Tests only synthesize non-copyrighted SNES-like header data."""
import tempfile
import unittest
from pathlib import Path

from snes_vc_injector.analyzer import RomAnalysisError, analyze_rom


def make_rom(mapping="LoROM", title="TEST GAME", mode=None, cart=0, copier=False):
    positions = {"LoROM": 0x7FC0, "HiROM": 0xFFC0, "ExHiROM": 0x40FFC0}
    modes = {"LoROM": 0x20, "HiROM": 0x21, "ExHiROM": 0x25}
    payload = bytearray(0x600000 if mapping == "ExHiROM" else 0x100000)
    off = positions[mapping]
    title_data = title.encode("ascii")[:21]
    payload[off:off + len(title_data)] = title_data
    payload[off + 0x15] = modes[mapping] if mode is None else mode
    payload[off + 0x16] = cart
    payload[off + 0x17] = 0x0A if mapping == "ExHiROM" else 0x09
    payload[off + 0x1C:off + 0x1E] = (0xEDCB).to_bytes(2, "little")
    payload[off + 0x1E:off + 0x20] = (0x1234).to_bytes(2, "little")
    payload[off + 0x3C:off + 0x3E] = (0x8000).to_bytes(2, "little")
    return (bytes(512) if copier else b"") + bytes(payload)


class AnalyzerTests(unittest.TestCase):
    def analyze(self, rom):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.sfc"
            path.write_bytes(rom)
            return analyze_rom(path)

    def test_lorom(self):
        result = self.analyze(make_rom())
        self.assertEqual((result.family, result.header_mapping), ("standard", "LoROM"))

    def test_hirom(self):
        self.assertEqual(self.analyze(make_rom("HiROM")).header_mapping, "HiROM")

    def test_exhirom(self):
        result = self.analyze(make_rom("ExHiROM", "DRAGON QUEST III"))
        self.assertEqual((result.family, result.header_mapping), ("exhirom", "ExHiROM"))

    def test_sfa2(self):
        result = self.analyze(make_rom(title="STREET FIGHTER ZERO2", mode=0x32, cart=0x45))
        self.assertEqual((result.enhancement_chip, result.family), ("S-DD1", "sdd1_sfa2"))

    def test_star_ocean(self):
        result = self.analyze(make_rom(title="STAR OCEAN", mode=0x32, cart=0x43))
        self.assertEqual(result.family, "sdd1_star_ocean")

    def test_unknown_sdd1(self):
        result = self.analyze(make_rom(title="FAN TRANSLATION", mode=0x32, cart=0x45))
        self.assertEqual(result.family, "sdd1_unidentified")

    def test_copier_header(self):
        result = self.analyze(make_rom(copier=True))
        self.assertEqual((result.copier_header_bytes, result.header_offset), (512, 0x7FC0))

    def test_no_header(self):
        with self.assertRaises(RomAnalysisError):
            self.analyze(bytes(0x100000))

    def test_small_file(self):
        with self.assertRaises(RomAnalysisError):
            self.analyze(bytes(10))


if __name__ == "__main__":
    unittest.main()
