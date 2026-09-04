#!/usr/bin/env python3
"""Create a metadata-only manifest for local legal documents.

The scanner deliberately does not write document text to stdout or the manifest.
It records hashes and structural metadata so that later OCR/RAG steps can be
reproducible without leaking case contents into logs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from legal_model_ingest.manifest import scan_directory, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Input directory")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL manifest path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.is_dir():
        raise SystemExit(f"Input directory does not exist: {args.input}")
    records = scan_directory(args.input)
    write_jsonl(records, args.output)
    print(f"Scanned {len(records)} supported documents.")
    print(f"Manifest: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
