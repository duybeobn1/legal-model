import json
import tempfile
import unittest
from pathlib import Path

from legal_model_ingest.manifest import inspect_document, scan_directory, write_jsonl


class ManifestTests(unittest.TestCase):
    def test_text_manifest_contains_hash_but_not_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "note.txt"
            source.write_text("nội dung thử nghiệm", encoding="utf-8")
            record = inspect_document(source)

            self.assertEqual(record.document_kind, "text")
            self.assertEqual(record.total_text_chars, len("nội dung thử nghiệm"))
            self.assertEqual(record.status, "ok")
            self.assertNotIn("nội dung thử nghiệm", record.to_json())
            self.assertEqual(len(record.sha256), 64)

    def test_unsupported_file_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "image.png"
            source.write_bytes(b"not a real image")
            record = inspect_document(source)

            self.assertEqual(record.document_kind, "unsupported")
            self.assertEqual(record.status, "skipped")

    def test_scan_and_write_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")
            output = root / "manifests" / "documents.jsonl"

            records = scan_directory(root)
            write_jsonl(records, output)

            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(records), 2)
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["status"], "ok")


if __name__ == "__main__":
    unittest.main()
