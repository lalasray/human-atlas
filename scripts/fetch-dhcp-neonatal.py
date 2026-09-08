#!/usr/bin/env python3
"""Fetch the pinned dHCP 40-week PMA neonatal brain atlas with source hashes."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/dhcp-neonatal"
REVISION = "d699540b1820d8224a07db3c1d727d0c747218dc"
BASE = f"https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise/raw/{REVISION}/"
FILES = {
    "structures.nii.gz": "mean/ga_40/structures.nii.gz",
    "structures.txt": "config/structures.txt",
    "ages.csv": "config/ages.csv",
    "ga_40.dof": "scale/ga_40.dof",
    "LICENSE.md": "LICENSE.md",
    "README.md": "README.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "human-atlas/dhcp-neonatal-import (research; contact via repository)"
    records = []
    for local_name, source_path in FILES.items():
        target = RAW / local_name
        url = BASE + source_path
        response = session.get(url, timeout=120, stream=True)
        response.raise_for_status()
        temporary = target.with_suffix(target.suffix + ".part")
        with temporary.open("wb") as handle:
            for block in response.iter_content(1 << 20):
                if block:
                    handle.write(block)
        temporary.replace(target)
        records.append({"url": url, "source_path": source_path, "local": str(target.relative_to(ROOT)),
                        "bytes": target.stat().st_size, "sha256": sha256(target),
                        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        print(f"fetched {source_path}", flush=True)
    license_text = (RAW / "LICENSE.md").read_text(errors="replace")
    if "Creative Commons Attribution 4.0 International" not in license_text:
        raise ValueError("Pinned dHCP license evidence changed")
    labels = (RAW / "structures.txt").read_text(errors="replace")
    if not labels.startswith("irtkSegmentTable: 87"):
        raise ValueError("Pinned dHCP structure table no longer defines 87 labels")
    manifest = {"source": "dHCP morphological atlas of neonatal brain development",
                "doi": "10.12751/g-node.d2b353", "revision": REVISION,
                "reference_age": "40 weeks post-menstrual age", "region": "brain",
                "population": "aggregate atlas from structurally normal neonatal MRI; mixed sex",
                "license": "CC-BY-4.0", "files": records}
    path = RAW / "download-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(path.relative_to(ROOT)), "files": len(records),
                      "bytes": sum(record["bytes"] for record in records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
