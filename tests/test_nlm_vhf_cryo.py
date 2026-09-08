from __future__ import annotations

import gzip
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fetch = load_script("fetch-nlm-vhf-cryo.py")
builder = load_script("build-nlm-vhf-cryo-volume.py")


class InventoryTests(unittest.TestCase):
    INDEX = """./Fullcolor/fullbody:
-r--r--r-- 1 root VhpFemale10 Nov 14 1995 avf1001a.raw.Z
-r--r--r-- 1 root VhpFemale11 Nov 14 1995 avf1001b.raw.Z
-r--r--r-- 1 root VhpFemale12 Nov 14 1995 avf1001c.raw.Z
-r--r--r-- 1 root VhpFemale13 Nov 14 1995 avf1002a.raw.Z
./Fullcolor/head:
-r--r--r-- 1 root VhpFemale99 Nov 14 1995 avf1001a.raw.Z
"""

    def test_parse_and_select_range(self):
        records = fetch.parse_fullcolor_inventory(self.INDEX)
        self.assertEqual([record.filename for record in records], [
            "avf1001a.raw.Z", "avf1001b.raw.Z", "avf1001c.raw.Z", "avf1002a.raw.Z"
        ])
        self.assertEqual([record.source_ordinal for record in records], [1, 2, 3, 4])
        self.assertEqual([record.listed_bytes for record in records], [10, 11, 12, 13])
        selected = fetch.select_range(records, "avf1001b", "avf1002a")
        self.assertEqual([record.filename for record in selected], [
            "avf1001b.raw.Z", "avf1001c.raw.Z", "avf1002a.raw.Z"
        ])

    def test_selection_rejects_inventory_gap(self):
        records = fetch.parse_fullcolor_inventory(self.INDEX.replace(
            "-r--r--r-- 1 root VhpFemale11 Nov 14 1995 avf1001b.raw.Z\n", ""
        ))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            fetch.select_range(records, "avf1001a", "avf1001c")

    def test_rejects_unbounded_download(self):
        with self.assertRaises(SystemExit):
            fetch.main(["--download", "--first", "avf1001a"])


class BuilderTests(unittest.TestCase):
    def test_manifest_and_planar_rgb_decoder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "slice.raw.Z"
            # 2 x 1 planar RGB: R=[1,2], G=[3,4], B=[5,6].
            raw = bytes([1, 2, 3, 4, 5, 6])
            with gzip.open(source, "wb") as handle:
                handle.write(raw)
            record = {
                "filename": "avf1001a.raw.Z", "source_ordinal": 1,
                "local": source.name, "bytes": source.stat().st_size,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "expected_uncompressed_bytes": len(raw),
            }
            manifest = {
                "format": builder.EXPECTED_FORMAT, "alignment_status": "unaligned-original",
                "width": 2, "height": 1, "files": [record],
            }
            self.assertEqual(builder.validate_manifest(manifest, root), [record])
            self.assertEqual(builder.read_planar_rgb(source, 2, 1), raw)

    def test_manifest_rejects_noncontiguous_sections(self):
        manifest = {
            "format": builder.EXPECTED_FORMAT, "alignment_status": "unaligned-original",
            "width": 2, "height": 1,
            "files": [{"filename": "a", "source_ordinal": 1}, {"filename": "b", "source_ordinal": 3}],
        }
        with self.assertRaisesRegex(ValueError, "contiguous"):
            builder.validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
