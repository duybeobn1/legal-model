from __future__ import annotations

import hashlib
import json
import mimetypes
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@dataclass
class DocumentRecord:
    document_id: str
    source_path: str
    filename: str
    extension: str
    mime_type: str | None
    size_bytes: int
    sha256: str
    modified_at: str
    scanned_at: str
    document_kind: str
    page_count: int | None = None
    pages_with_text: int | None = None
    pages_without_text: int | None = None
    total_text_chars: int | None = None
    paragraph_count: int | None = None
    table_count: int | None = None
    status: str = "ok"
    error_code: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_base(path: Path, document_id: str) -> dict[str, Any]:
    stat = path.stat()
    return {
        "document_id": document_id,
        "source_path": str(path.resolve()),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "mime_type": mimetypes.guess_type(path.name)[0],
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(),
        "scanned_at": utc_now(),
    }


def _pdf_fields(path: Path) -> dict[str, Any]:
    try:
        import fitz  # type: ignore
    except ImportError:
        return {
            "document_kind": "pdf_uninspected",
            "status": "dependency_missing",
            "error_code": "pymupdf_not_installed",
        }

    try:
        with fitz.open(path) as pdf:
            page_char_counts = [len(page.get_text("text").strip()) for page in pdf]
    except Exception:
        return {
            "document_kind": "pdf_unreadable",
            "status": "error",
            "error_code": "pdf_open_failed",
        }

    page_count = len(page_char_counts)
    pages_with_text = sum(chars > 0 for chars in page_char_counts)
    pages_without_text = page_count - pages_with_text
    if page_count == 0:
        kind = "pdf_empty"
    elif pages_with_text == page_count:
        kind = "pdf_text"
    elif pages_with_text == 0:
        kind = "pdf_scanned"
    else:
        kind = "pdf_mixed"

    return {
        "document_kind": kind,
        "page_count": page_count,
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "total_text_chars": sum(page_char_counts),
    }


def _docx_fields(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
    except (KeyError, OSError, ElementTree.ParseError):
        return {
            "document_kind": "docx_unreadable",
            "status": "error",
            "error_code": "docx_open_failed",
        }

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = root.findall(f".//{namespace}p")
    tables = root.findall(f".//{namespace}tbl")
    return {
        "document_kind": "docx",
        "paragraph_count": len(paragraphs),
        "table_count": len(tables),
    }


def inspect_document(path: Path, document_id: str | None = None) -> DocumentRecord:
    path = path.resolve()
    document_id = document_id or path.stem
    fields: dict[str, Any] = _record_base(path, document_id)
    if path.suffix.lower() == ".pdf":
        fields.update(_pdf_fields(path))
    elif path.suffix.lower() == ".docx":
        fields.update(_docx_fields(path))
    elif path.suffix.lower() == ".txt":
        fields.update(
            {
                "document_kind": "text",
                "total_text_chars": len(path.read_text(encoding="utf-8")),
            }
        )
    else:
        fields.update(
            {
                "document_kind": "unsupported",
                "status": "skipped",
                "error_code": "unsupported_extension",
            }
        )
    return DocumentRecord(**fields)


def scan_directory(input_dir: Path) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    for path in sorted(input_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            records.append(inspect_document(path))
    return records


def write_jsonl(records: list[DocumentRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(record.to_json() + "\n")
