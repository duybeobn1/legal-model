# Local Legal AI

## Bước đầu tiên: document ingestion

Module đầu tiên chưa gọi LLM và chưa chạy OCR. Nó tạo manifest metadata-only
cho PDF, DOCX và TXT:

- SHA-256 của file;
- loại tài liệu;
- số trang và tình trạng text layer của PDF;
- số paragraph/table của DOCX;
- kích thước, thời gian sửa đổi và trạng thái xử lý.

Nội dung tài liệu không được ghi vào stdout hoặc manifest.

## Cài đặt

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
~~~

## Chạy scanner

~~~bash
mkdir -p data/inbox data/manifests
python scripts/scan_documents.py \
  --input data/inbox \
  --output data/manifests/documents.jsonl
~~~

Các giá trị document_kind PDF:

- pdf_text: mọi trang có text layer;
- pdf_scanned: không có text layer;
- pdf_mixed: có cả hai loại trang;
- pdf_empty: PDF không có trang.

## OCR PDF scan

Cài PaddleOCR trong môi trường đã cài PaddlePaddle GPU tương ứng với driver:

~~~bash
python -m pip install -r requirements-ocr.txt
~~~

Chạy OCR cho một PDF:

~~~bash
mkdir -p data/ocr/20260515093231
python scripts/ocr_pipeline.py \
  --input data/inbox/20260515093231.pdf \
  --output-dir data/ocr/20260515093231 \
  --device gpu \
  --lang vi
~~~

Pipeline tạo document.json, từng page-XXXX.json và ảnh trang đã render.
Nó dừng ngay nếu yêu cầu GPU nhưng PaddlePaddle không có CUDA.

## Chạy test

~~~bash
PYTHONPATH=src python -m unittest discover -s tests -v
~~~

Không đưa hồ sơ thật vào data/inbox trước khi có quy trình phân quyền,
ẩn danh/giả danh, mã hóa và backup được phê duyệt.
