import unittest

from scripts.ocr_pipeline import extract_lines, result_to_dict


class OcrHelperTests(unittest.TestCase):
    def test_extract_lines_normalizes_common_fields(self) -> None:
        result = {
            "res": {
                "rec_texts": ["Điều 1", "Nội dung"],
                "rec_scores": [0.99, 0.70],
                "dt_polys": [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
            }
        }
        lines, stats = extract_lines(result, 0.85)

        self.assertEqual([line["text"] for line in lines], ["Điều 1", "Nội dung"])
        self.assertEqual(stats["line_count"], 2)
        self.assertEqual(stats["low_confidence_count"], 1)
        self.assertTrue(lines[1]["low_confidence"])

    def test_result_to_dict_accepts_dict(self) -> None:
        self.assertEqual(result_to_dict({"a": 1}), {"a": 1})


if __name__ == "__main__":
    unittest.main()
