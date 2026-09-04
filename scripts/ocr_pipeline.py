#!/usr/bin/env python3
"""Run local Vietnamese OCR on a PDF and save auditable page JSON.

The pipeline renders each PDF page itself so page numbers and image hashes are
stable. It intentionally stores OCR output and provenance, not model prompts
or hidden application state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jsonable(value: Any) -> Any:
    """Convert Paddle/Numpy values to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return jsonable(value.tolist())
    if hasattr(value, "item"):
        try:
            return jsonable(value.item())
        except ValueError:
            pass
    return str(value)


def result_to_dict(result: Any) -> dict[str, Any]:
    """Extract a dict from PaddleOCR 3.x result objects across minor versions."""
    if isinstance(result, dict):
        return jsonable(result)

    for attribute in ("json", "to_dict"):
        if not hasattr(result, attribute):
            continue
        value = getattr(result, attribute)
        value = value() if callable(value) else value
        if isinstance(value, str):
            value = json.loads(value)
        if isinstance(value, dict):
            return jsonable(value)

    if hasattr(result, "res"):
        value = getattr(result, "res")
        if isinstance(value, dict):
            return jsonable(value)

    raise TypeError("Unsupported PaddleOCR result object")


def _first(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def extract_lines(
    result: Any, low_confidence_threshold: float
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normalize common PaddleOCR result fields into auditable text lines."""
    raw = result_to_dict(result)
    payload = raw.get("res", raw)
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise TypeError("PaddleOCR result payload is not a mapping")

    texts = _first(payload, ("rec_texts", "texts", "text"))
    scores = _first(payload, ("rec_scores", "scores", "confidences", "text_scores"))
    polygons = _first(payload, ("dt_polys", "polys", "boxes"))

    if texts is None:
        texts = []
    elif isinstance(texts, str):
        texts = [texts]
    if scores is None:
        scores = []
    elif not isinstance(scores, (list, tuple)):
        scores = [scores]
    if polygons is None:
        polygons = []
    elif not isinstance(polygons, (list, tuple)):
        polygons = [polygons]

    lines: list[dict[str, Any]] = []
    for index, text in enumerate(texts):
        score = float(scores[index]) if index < len(scores) else None
        polygon = polygons[index] if index < len(polygons) else None
        lines.append(
            {
                "line_index": index,
                "text": str(text),
                "score": score,
                "polygon": jsonable(polygon),
                "low_confidence": score is not None
                and score < low_confidence_threshold,
            }
        )
    normalized = {
        "result_keys": sorted(str(key) for key in payload.keys()),
        "line_count": len(lines),
        "low_confidence_count": sum(line["low_confidence"] for line in lines),
    }
    return lines, normalized


def render_pdf_pages(
    pdf_path: Path, pages_dir: Path, dpi: int
) -> list[dict[str, Any]]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required. Install the project package first."
        ) from exc

    pages_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    page_records: list[dict[str, Any]] = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf):
            image_path = pages_dir / f"page-{page_index + 1:04d}.png"
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(zoom, zoom), alpha=False
            )
            pixmap.save(str(image_path))
            page_records.append(
                {
                    "page_index": page_index,
                    "page_number": page_index + 1,
                    "image_path": str(image_path),
                    "image_sha256": sha256_file(image_path),
                }
            )
    return page_records


def build_ocr(lang: str, device: str, use_orientation: bool) -> Any:
    try:
        import paddle
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR and PaddlePaddle are required. Install OCR dependencies first."
        ) from exc

    if device.startswith("gpu") and not paddle.is_compiled_with_cuda():
        raise RuntimeError(
            "GPU device requested but PaddlePaddle was compiled without CUDA support."
        )

    return PaddleOCR(
        lang=lang,
        ocr_version="PP-OCRv5",
        text_recognition_model_name="PP-OCRv5_mobile_rec",
        device=device,
        engine="paddle",
        use_doc_orientation_classify=use_orientation,
        use_doc_unwarping=use_orientation,
        use_textline_orientation=use_orientation,
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    lang: str,
    device: str,
    dpi: int,
    low_confidence_threshold: float,
    use_orientation: bool,
) -> Path:
    pdf_path = pdf_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"
    page_records = render_pdf_pages(pdf_path, pages_dir, dpi)
    ocr = build_ocr(lang, device, use_orientation)

    document = {
        "document_id": pdf_path.stem,
        "source_path": str(pdf_path),
        "source_sha256": sha256_file(pdf_path),
        "source_size_bytes": pdf_path.stat().st_size,
        "scanned_at": utc_now(),
        "device": device,
        "lang": lang,
        "dpi": dpi,
        "ocr_engine": "PaddleOCR",
        "ocr_version": "PP-OCRv5",
        "text_recognition_model": "PP-OCRv5_mobile_rec",
        "orientation_enabled": use_orientation,
        "status": "ok",
        "page_count": len(page_records),
        "pages": [],
    }

    for page in page_records:
        page_number = page["page_number"]
        page_payload = {
            **page,
            "status": "ok",
            "text": "",
            "lines": [],
            "line_count": 0,
            "low_confidence_count": 0,
        }
        try:
            results = list(ocr.predict(page["image_path"]))
            if len(results) != 1:
                raise RuntimeError("Unexpected OCR result count")
            lines, stats = extract_lines(
                results[0], low_confidence_threshold
            )
            page_payload.update(
                {
                    "text": "\n".join(line["text"] for line in lines),
                    "lines": lines,
                    "line_count": stats["line_count"],
                    "low_confidence_count": stats["low_confidence_count"],
                    "result_keys": stats["result_keys"],
                }
            )
        except Exception as exc:
            page_payload.update(
                {
                    "status": "error",
                    "error_code": "ocr_page_failed",
                    "error_type": type(exc).__name__,
                }
            )
            document["status"] = "partial_error"

        page_json = output_dir / f"page-{page_number:04d}.json"
        write_json(page_json, page_payload)
        document["pages"].append(
            {
                "page_number": page_number,
                "status": page_payload["status"],
                "json_path": str(page_json),
                "line_count": page_payload["line_count"],
                "low_confidence_count": page_payload["low_confidence_count"],
            }
        )

    document_json = output_dir / "document.json"
    write_json(document_json, document)
    return document_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Input PDF path")
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="OCR output directory"
    )
    parser.add_argument("--lang", default="vi", help="PaddleOCR language code")
    parser.add_argument(
        "--device", default="gpu", help="Paddle device, e.g. gpu or gpu:0"
    )
    parser.add_argument("--dpi", type=int, default=250, help="PDF render DPI")
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.85,
        help="Flag OCR lines below this score",
    )
    parser.add_argument(
        "--use-orientation",
        action="store_true",
        help="Enable orientation/unwarping modules; slower for rotated scans",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Input PDF does not exist: {args.input}")
    if args.input.suffix.lower() != ".pdf":
        raise SystemExit("Input must be a PDF file")
    document_json = process_pdf(
        pdf_path=args.input,
        output_dir=args.output_dir,
        lang=args.lang,
        device=args.device,
        dpi=args.dpi,
        low_confidence_threshold=args.low_confidence_threshold,
        use_orientation=args.use_orientation,
    )
    print(f"OCR completed: {document_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
