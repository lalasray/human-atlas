#!/usr/bin/env python3
"""Inventory and download bounded NLM Visible Human Female full-color sections.

The source contains 5,189 2048 x 1216 planar-RGB sections at 0.33 mm spacing.
A full download is roughly 40 GB, so this command inventories by default and only
transfers an explicit inclusive range when --download is supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/nlm-vhf"
BASE = "https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/"
TERMS = "https://www.nlm.nih.gov/databases/download/terms_and_conditions.html"
INDEX_URL = BASE + "INDEX"
README_URL = BASE + "Fullcolor/README"
SECTION_RE = re.compile(r"^(?P<prefix>[a-z]+vf)(?P<number>\d{4})(?P<suffix>[abc])\.raw\.Z$")
CHANNELS = "abc"
WIDTH = 2048
HEIGHT = 1216
SPACING_MM = 0.33
EXPECTED_UNCOMPRESSED_BYTES = WIDTH * HEIGHT * 3


@dataclass(frozen=True)
class CryoFile:
    filename: str
    url: str
    region: str
    source_number: int
    source_suffix: str
    source_ordinal: int
    listed_bytes: int | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="download the explicit --first/--last range")
    parser.add_argument("--first", help="first section, for example avf1800a")
    parser.add_argument("--last", help="last section, for example avf1866c")
    parser.add_argument("--max-bytes", type=int, default=2_000_000_000,
                        help="maximum listed compressed bytes per run (default: 2 GB)")
    parser.add_argument("--timeout", type=int, default=120)
    return parser


def section_ordinal(filename: str) -> int:
    match = SECTION_RE.fullmatch(filename)
    if not match:
        raise ValueError(f"unsupported full-color filename: {filename}")
    return (int(match["number"]) - 1001) * 3 + CHANNELS.index(match["suffix"]) + 1


def _listed_bytes(line: str, filename: str) -> int | None:
    prefix = line[: line.rfind(filename)]
    match = re.search(r"(?:\s|VhpFemale)(\d+)\s+[A-Z][a-z]{2}\s+\d+\s+\d{4}\s*$", prefix)
    return int(match.group(1)) if match else None


def parse_fullcolor_inventory(index_text: str, region: str = "fullbody") -> list[CryoFile]:
    heading = f"./Fullcolor/{region}:"
    active = False
    records: list[CryoFile] = []
    for line in index_text.splitlines():
        if line.strip() == heading:
            active = True
            continue
        if active and line.startswith("./"):
            break
        if not active:
            continue
        filename_match = re.search(r"([a-z]+vf\d{4}[abc]\.raw\.Z)\s*$", line)
        if not filename_match:
            continue
        filename = filename_match.group(1)
        parsed = SECTION_RE.fullmatch(filename)
        assert parsed is not None
        records.append(CryoFile(
            filename=filename,
            url=f"{BASE}Fullcolor/{region}/{filename}",
            region=region,
            source_number=int(parsed["number"]),
            source_suffix=parsed["suffix"],
            source_ordinal=section_ordinal(filename),
            listed_bytes=_listed_bytes(line, filename),
        ))
    records.sort(key=lambda item: item.source_ordinal)
    if not records:
        raise ValueError(f"no cryosection files found under {heading}")
    if len({record.filename for record in records}) != len(records):
        raise ValueError("duplicate cryosection filenames in NLM INDEX")
    return records


def inventory_gaps(records: Iterable[CryoFile]) -> list[int]:
    ordinals = sorted(record.source_ordinal for record in records)
    return sorted(set(range(ordinals[0], ordinals[-1] + 1)) - set(ordinals))


def select_range(records: list[CryoFile], first: str, last: str) -> list[CryoFile]:
    first_name = first if first.endswith(".raw.Z") else first + ".raw.Z"
    last_name = last if last.endswith(".raw.Z") else last + ".raw.Z"
    first_ordinal = section_ordinal(first_name)
    last_ordinal = section_ordinal(last_name)
    if first_ordinal > last_ordinal:
        raise ValueError("--first must not follow --last")
    selected = [record for record in records if first_ordinal <= record.source_ordinal <= last_ordinal]
    expected = list(range(first_ordinal, last_ordinal + 1))
    actual = [record.source_ordinal for record in selected]
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        raise ValueError(f"selected range is incomplete in the NLM INDEX; missing ordinals: {missing}")
    return selected


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_text(session: requests.Session, url: str, destination: Path, timeout: int) -> dict:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return {"url": url, "local": str(destination.relative_to(ROOT)), "bytes": destination.stat().st_size,
            "sha256": sha256(destination), "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def download_file(session: requests.Session, record: CryoFile, destination: Path, timeout: int) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    with session.get(record.url, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        with partial.open("wb") as handle:
            for block in response.iter_content(1 << 20):
                if block:
                    handle.write(block)
        response_bytes = response.headers.get("Content-Length")
        if response_bytes is not None and partial.stat().st_size != int(response_bytes):
            partial.unlink(missing_ok=True)
            raise ValueError(f"short download for {record.filename}")
    partial.replace(destination)
    result = asdict(record)
    result.update({"local": str(destination.relative_to(ROOT)), "bytes": destination.stat().st_size,
                   "sha256": sha256(destination), "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "expected_uncompressed_bytes": EXPECTED_UNCOMPRESSED_BYTES})
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.download and (not args.first or not args.last):
        raise SystemExit("--download requires explicit --first and --last section names")
    if not args.download and (args.first or args.last):
        raise SystemExit("--first/--last require --download")

    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "female-open-human-atlas/fetch-nlm-vhf-cryo (research; contact via repository)"
    evidence = [
        fetch_text(session, TERMS, RAW / "terms_and_conditions.html", args.timeout),
        fetch_text(session, BASE + "README", RAW / "README", args.timeout),
        fetch_text(session, README_URL, RAW / "Fullcolor-README", args.timeout),
        fetch_text(session, INDEX_URL, RAW / "INDEX", args.timeout),
    ]
    terms = (RAW / "terms_and_conditions.html").read_text(errors="replace")
    if "Courtesy of the U.S. National Library of Medicine" not in terms:
        raise ValueError("NLM attribution text changed; terms require manual re-verification")
    readme = (RAW / "Fullcolor-README").read_text(errors="replace")
    required_evidence = ("2048,1216", ".33mm,.33mm, .33mm", "RGB 24 BIT NON INTERLEAVED")
    if not all(value in readme for value in required_evidence):
        raise ValueError("NLM Fullcolor format evidence changed; decoder requires manual re-verification")

    records = parse_fullcolor_inventory((RAW / "INDEX").read_text(errors="replace"))
    inventory = {
        "source": "NLM Visible Human Female Fullcolor/fullbody",
        "source_url": BASE + "Fullcolor/fullbody/",
        "terms_url": TERMS,
        "format": "RGB 24-bit non-interleaved, one complete section per .raw.Z file",
        "width": WIDTH,
        "height": HEIGHT,
        "spacing_mm": [SPACING_MM, SPACING_MM, SPACING_MM],
        "alignment_status": "unaligned-original",
        "files": [asdict(record) for record in records],
        "missing_ordinals": inventory_gaps(records),
        "evidence": evidence,
    }
    inventory_path = RAW / "cryo-inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n")
    summary = {"inventory": str(inventory_path.relative_to(ROOT)), "files": len(records),
               "listed_bytes": sum(record.listed_bytes or 0 for record in records),
               "missing_ordinals": inventory["missing_ordinals"], "downloaded": 0}
    if not args.download:
        print(json.dumps(summary, indent=2))
        return 0

    selected = select_range(records, args.first, args.last)
    if any(record.listed_bytes is None for record in selected):
        raise ValueError("selected files lack byte sizes in the NLM INDEX; refusing an unbounded transfer")
    selected_bytes = sum(record.listed_bytes or 0 for record in selected)
    if selected_bytes > args.max_bytes:
        raise ValueError(f"selected transfer is {selected_bytes} bytes, above --max-bytes={args.max_bytes}")
    downloaded: list[dict] = []
    for index, record in enumerate(selected, 1):
        destination = RAW / "Fullcolor" / "fullbody" / record.filename
        existing = destination.exists() and destination.stat().st_size == record.listed_bytes
        if existing:
            item = asdict(record)
            item.update({"local": str(destination.relative_to(ROOT)), "bytes": destination.stat().st_size,
                         "sha256": sha256(destination), "expected_uncompressed_bytes": EXPECTED_UNCOMPRESSED_BYTES})
        else:
            item = download_file(session, record, destination, args.timeout)
        downloaded.append(item)
        print(f"{index}/{len(selected)} {'kept' if existing else 'fetched'} {record.filename}", flush=True)
    manifest = {"source": inventory["source"], "terms_url": TERMS, "format": inventory["format"],
                "width": WIDTH, "height": HEIGHT, "spacing_mm": inventory["spacing_mm"],
                "alignment_status": "unaligned-original", "selection": {"first": args.first, "last": args.last},
                "files": downloaded}
    manifest_path = RAW / "cryo-download-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    summary.update({"manifest": str(manifest_path.relative_to(ROOT)), "selected_bytes": selected_bytes,
                    "downloaded": len(downloaded)})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
