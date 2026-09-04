# Kế hoạch kỹ thuật: Local Legal AI chạy offline với Ollama

## 1. Mục tiêu và nguyên tắc thiết kế

Project cần hỗ trợ:

- Nhận PDF text, PDF scan, Word và tài liệu có bảng.
- OCR tiếng Việt, nhận diện bố cục, bảng, con dấu và số trang.
- Tóm tắt hồ sơ, lập dòng thời gian, trích xuất người/sự kiện/tài liệu.
- Tra cứu điều luật và văn bản hướng dẫn có dẫn nguồn.
- Soạn bản nháp báo cáo Word/Excel theo mẫu.
- Hoạt động offline, dữ liệu không rời khỏi máy.

Nguyên tắc bắt buộc:

1. Không huấn luyện từ đầu một LLM. Việc này đòi hỏi lượng token và hạ tầng lớn hơn nhiều so với máy hiện tại.
2. Không đưa toàn bộ hồ sơ vụ án vào trọng số model. Hồ sơ, luật hiện hành và văn bản thay đổi phải nằm trong kho tài liệu có phiên bản, nguồn và quyền truy cập; model chỉ truy xuất phần cần thiết.
3. Fine-tune chủ yếu để model biết cách làm việc, định dạng đầu ra, thuật ngữ và quy trình; RAG mới là cơ chế cung cấp sự kiện và quy định hiện hành.
4. Mọi kết luận pháp lý phải có trích dẫn tới văn bản, điều/khoản, ngày hiệu lực và đoạn nguồn. Không có nguồn phù hợp thì phải trả về “chưa đủ căn cứ”.
5. Tách dữ liệu huấn luyện, dữ liệu truy xuất và dữ liệu đánh giá. Không để cùng một vụ án xuất hiện ở cả train và test.
6. Model chỉ là công cụ hỗ trợ. Nó không xác định sự thật khách quan, tính xác thực của chứng cứ, tội phạm hay trách nhiệm của một người.

## 2. Khuyến nghị model theo phần cứng hiện tại

Phần cứng mục tiêu: Core i5-14400F, RAM 32 GB, RTX 5060 Ti 16 GB VRAM, SSD NVMe 1 TB.

SSD 1 TB phù hợp cho prototype nhưng không phù hợp lâu dài nếu giữ đồng thời PDF gốc, ảnh từng trang, OCR, vector index, nhiều checkpoint và backup. Trước pilot dữ liệu lớn nên nâng lên 2–4 TB hoặc dùng kho lưu trữ nội bộ được mã hóa; không đặt bản gốc và backup duy nhất trên cùng một SSD.

### Lựa chọn chính

**Qwen3-8B Instruct, bản quantized Q4/Q5 chạy qua Ollama** là baseline nên triển khai trước. Qwen3 có các bản 8B và 14B, hỗ trợ hơn 100 ngôn ngữ và chế độ thinking/non-thinking; bản 8B có dung lượng Ollama khoảng 5,2 GB theo thư viện Ollama. Đây là điểm cân bằng tốt cho tiếng Việt, tốc độ, RAM/VRAM và khả năng fine-tune LoRA.

**Qwen3-14B Q4** là challenger để so sánh chất lượng. Dung lượng Ollama được liệt kê khoảng 9,3 GB; có thể chạy một người dùng trên GPU 16 GB nếu giữ context vừa phải, nhưng không nên kỳ vọng nhiều người dùng đồng thời hoặc fine-tune trên máy này. Nếu model bị offload sang RAM, độ trễ sẽ tăng.

Không chọn Qwen3-32B làm model triển khai hiện tại: bản Ollama khoảng 20 GB, chưa tính KV cache và overhead. Không chọn model vision tổng quát làm OCR chính.

### Thành phần ngoài LLM

- OCR text: thử PP-OCRv6 hoặc PP-OCRv5 với lang=vi.
- Bố cục/tài liệu/bảng: PP-StructureV3 hoặc PaddleOCR-VL-1.6. PaddleOCR-VL thuộc pipeline tài liệu 0,9B, hỗ trợ đa ngôn ngữ và nhận diện text, bảng, công thức, biểu đồ; nên chạy riêng hoặc tuần tự vì nó cạnh tranh VRAM với LLM.
- Embedding: baseline BAAI/bge-m3; model đa ngôn ngữ, 1024 chiều, context 8192, có thể dùng dense + sparse retrieval. Sau này benchmark thêm Qwen3-Embedding-0.6B.
- Reranker: BAAI/bge-reranker-v2-m3 hoặc Qwen3-Reranker-0.6B nếu stack triển khai hỗ trợ tốt.
- Tìm kiếm từ khóa: BM25 hoặc SQLite FTS5. Với luật, số điều, khoản, điểm và tên văn bản, không được chỉ dùng vector search.
- Sinh Word/Excel: model xuất JSON có schema cố định; Python dùng python-docx và openpyxl để render. Không để model tự viết trực tiếp XML/binary của file.

Qwen3 có giấy phép Apache-2.0 theo model card; mọi model OCR, embedding, reranker và dữ liệu bên thứ ba vẫn phải được kiểm tra license riêng trước khi đưa vào hệ thống nghiệp vụ.

## 3. Kiến trúc đề xuất

~~~text
PDF/DOCX/TXT
    |
    +--> phát hiện loại tài liệu
    |       +--> PDF text: PyMuPDF/pdfplumber
    |       +--> PDF scan: render trang -> OCR
    |       +--> DOCX: python-docx -> đoạn/bảng
    |
    +--> chuẩn hóa + giữ provenance
            (file hash, vụ án, trang, bbox, người xử lý, phiên bản văn bản)
                    |
                    +--> kho tài liệu gốc mã hóa
                    +--> chỉ mục BM25
                    +--> vector index
                    +--> metadata/access-control index
                              |
                        hybrid retrieve -> rerank
                              |
                    Qwen3-8B/14B + prompt strict
                              |
             JSON schema -> báo cáo Word/Excel + citations
~~~

## 4. Dữ liệu cần chuẩn bị

### 4.1. Bộ văn bản pháp luật có thẩm quyền

Tối thiểu cần có:

- Hiến pháp, Bộ luật Hình sự, Bộ luật Tố tụng hình sự.
- Luật, nghị định, thông tư, nghị quyết, án lệ và văn bản hướng dẫn liên quan đến các nhóm tội mục tiêu.
- Văn bản hợp nhất hoặc bản đang có hiệu lực, nhưng vẫn lưu các phiên bản sửa đổi.
- Hướng dẫn nghiệp vụ được phép sử dụng trong phạm vi cơ quan.
- Mẫu biểu, biểu mẫu tố tụng, mẫu báo cáo và quy trình nội bộ đã được phê duyệt.

Mỗi văn bản cần manifest:

~~~json
{
  "document_id": "BLTTHS_101_2015_QH13",
  "title": "Bộ luật Tố tụng hình sự",
  "issuer": "Quốc hội",
  "number": "101/2015/QH13",
  "issue_date": "2015-11-27",
  "effective_from": "2018-01-01",
  "effective_to": null,
  "status": "partially_amended",
  "source_url": "https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/96172/VanBanGoc_101.2015.QH13.P1.pdf",
  "sha256": "...",
  "access_level": "internal",
  "verified_by": "legal_reviewer",
  "verified_at": "2026-09-03"
}
~~~

Không được trộn văn bản hết hiệu lực với văn bản hiện hành mà không gắn effective_from, effective_to và điều kiện áp dụng theo thời điểm hành vi.

### 4.2. Hồ sơ vụ án và tài liệu thực tế

Nên bắt đầu bằng dữ liệu đã được phép sử dụng, ưu tiên hồ sơ đã kết thúc hoặc dữ liệu tổng hợp/ẩn danh. Nhóm tài liệu có thể gồm:

- Quyết định, biên bản, cáo trạng, bản án, kết luận điều tra trong phạm vi được phép.
- Lời khai, biên bản hỏi cung, đối chất, nhận dạng, thực nghiệm điều tra.
- Tài liệu, vật chứng, dữ liệu điện tử và biên bản thu giữ/bảo quản.
- Kết luận giám định, định giá, tài liệu ngân hàng/viễn thông nếu có căn cứ sử dụng.
- Danh sách người, vai trò tố tụng, mốc thời gian, địa điểm, hành vi được mô tả.

Hồ sơ gốc phải giữ nguyên và bất biến; bản dùng cho huấn luyện phải được tách/ẩn danh. Không dùng việc đổi tên file đơn giản làm ẩn danh. Cần xử lý cả tên trong nội dung, header/footer, chữ ký, dấu, bảng, metadata DOCX/PDF và thông tin trong ảnh.

### 4.3. Dữ liệu tác vụ có nhãn

Các task nên gán nhãn theo đầu ra chuẩn:

- Tóm tắt có cấu trúc: bối cảnh, diễn biến, người, hành vi, chứng cứ, kết quả tố tụng.
- Dòng thời gian sự kiện và nguồn trang.
- Trích xuất thực thể: người, tổ chức, địa điểm, tài sản, tài khoản, số điện thoại, phương tiện, văn bản pháp luật.
- Liên kết phát biểu với người phát biểu và tài liệu nguồn.
- Ma trận “vấn đề pháp lý – tình tiết – chứng cứ – quy định áp dụng”.
- Phát hiện mâu thuẫn giữa các lời khai, có trích dẫn hai nguồn; không tự kết luận ai nói thật.
- Tìm điều/khoản phù hợp và điều/khoản gần giống nhưng không áp dụng.
- Soạn dàn ý báo cáo, bảng Excel, phiếu kiểm tra hồ sơ, danh mục tài liệu.
- Các ví dụ từ chối: thiếu hồ sơ, nguồn mâu thuẫn, câu hỏi vượt phạm vi, yêu cầu suy đoán.

### 4.4. Bộ đánh giá giữ kín

Tạo ít nhất ba tập riêng:

- dev: dùng trong quá trình sửa pipeline.
- test: chỉ đánh giá định kỳ.
- blind_test: do nhóm pháp lý giữ, người train không xem nội dung trước.

Mỗi vụ án phải được split theo case_id, không split ngẫu nhiên theo trang/chunk. Nếu không, các trang của cùng một vụ án có thể rò rỉ sang train và làm kết quả giả tạo.

## 5. OCR: có cần train không?

**Không train OCR ngay từ đầu.** Làm baseline bằng pipeline hiện hành, sau đó đo lỗi trên bộ tài liệu thật.

### Pipeline OCR ban đầu

1. Dùng PyMuPDF kiểm tra mỗi trang có text layer hay không.
2. Nếu text layer đủ tốt, dùng text trực tiếp và vẫn lưu số trang.
3. Nếu là scan, render 250–300 DPI, điều chỉnh xoay, nghiêng, tương phản và chạy OCR tiếng Việt.
4. Với bố cục phức tạp, chạy layout + table recognition, lưu cả Markdown/JSON và ảnh crop.
5. Với đoạn có confidence thấp, đánh dấu cần kiểm tra thủ công; không âm thầm sửa thành text “có vẻ đúng”.
6. Lưu page_no, bbox, text, confidence, engine, model_version cho từng vùng.

### Khi nào fine-tune OCR?

Chỉ fine-tune khi bộ test cho thấy lỗi có tính hệ thống, ví dụ font máy đánh chữ cũ, scan mờ, dấu đóng trên chữ, biểu mẫu địa phương hoặc chữ viết tay. Cần tách bài toán:

- text detection: vị trí dòng/vùng chữ;
- text recognition: ảnh dòng -> chuỗi ký tự;
- layout/table: tiêu đề, đoạn, bảng, ô, con dấu;
- handwriting: chữ viết tay, thường là dự án riêng.

Không dùng output do OCR tự sinh làm ground truth cho chính nó. Nhãn OCR cần người kiểm tra trực tiếp trên ảnh, gồm bounding box/polygon và transcript chính xác, giữ nguyên dấu tiếng Việt, số, ký hiệu điều luật, viết tắt và lỗi nguyên bản khi cần.

## 6. Gán nhãn pháp lý và quy trình kiểm duyệt

### Schema gợi ý cho một ví dụ SFT

~~~json
{
  "messages": [
    {"role": "system", "content": "Chỉ kết luận trong phạm vi nguồn được cung cấp."},
    {"role": "user", "content": "Tóm tắt tài liệu theo mẫu..."},
    {"role": "assistant", "content": "{...JSON hợp lệ...}"}
  ],
  "metadata": {
    "case_id": "CASE_000123",
    "source_ids": ["doc_45:p12", "doc_46:p03"],
    "task": "structured_summary",
    "legal_timepoint": "2024-05-10",
    "review_status": "approved",
    "reviewer_count": 2
  }
}
~~~

Mỗi ví dụ pháp lý quan trọng nên có hai người gán nhãn độc lập và một người adjudicate các điểm bất đồng. Không gán nhãn “có tội/không có tội” như một nhãn máy học nếu quy trình không xác định rõ phạm vi, thời điểm, nguồn chứng cứ và người có thẩm quyền.

## 7. Các bước triển khai và code cần viết

### Giai đoạn A — baseline không fine-tune

1. Cài Ollama, chạy Qwen3-8B và Qwen3-14B Q4.
2. Viết ingest_pdf.py, ingest_docx.py, ocr_pipeline.py.
3. Viết normalize.py để chuẩn hóa Unicode, nhưng giữ bản nguyên bản cạnh bản chuẩn hóa.
4. Viết manifest.py để hash, version và gắn quyền truy cập.
5. Viết chunk.py theo cấu trúc điều/khoản/điểm, không cắt giữa điều và chú thích quan trọng.
6. Viết index_bm25.py, index_vector.py, retrieve.py, rerank.py.
7. Viết answer_strict.py với prompt, JSON schema và citations bắt buộc.
8. Viết render_docx.py, render_xlsx.py từ JSON đã được validate.
9. Viết eval_ocr.py, eval_retrieval.py, eval_groundedness.py.

### Giai đoạn B — LoRA SFT cho hành vi nghiệp vụ

Chỉ bắt đầu sau khi baseline có bộ test và biết lỗi nằm ở model hay retrieval. Dùng TRL + PEFT/QLoRA; chỉ cập nhật adapter, giữ base model cố định. Với 16 GB VRAM, bắt đầu ở Qwen3-8B, sequence length 2k–4k, batch vật lý nhỏ, gradient accumulation và checkpoint thường xuyên.

Ví dụ khung train tối giản:

~~~python
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

base_model = "Qwen/Qwen3-8B"
dataset = load_dataset("json", data_files={
    "train": "data/sft/train.jsonl",
    "validation": "data/sft/validation.jsonl",
})

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    task_type="CAUSAL_LM",
)

args = SFTConfig(
    output_dir="artifacts/qwen3-8b-legal-lora",
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    learning_rate=2e-4,
    max_length=4096,
    packing=False,
    eval_strategy="steps",
    eval_steps=100,
    save_steps=100,
    bf16=True,
    logging_steps=10,
)

trainer = SFTTrainer(
    model=base_model,
    args=args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    peft_config=peft_config,
)
trainer.train()
trainer.save_model()
~~~

Đây là skeleton cần kiểm tra lại theo phiên bản Transformers/TRL/PEFT và chat template của model. Không đưa dữ liệu nhạy cảm thật vào log, TensorBoard hoặc exception trace.

### Giai đoạn C — đóng gói Ollama

Sau khi adapter được đánh giá, dùng cùng base model và adapter đúng cặp:

~~~text
FROM qwen3:8b
ADAPTER /absolute/path/to/legal-lora
PARAMETER temperature 0.1
PARAMETER num_ctx 16384
SYSTEM """
Bạn là trợ lý phân tích hồ sơ pháp lý offline.
Chỉ sử dụng thông tin trong CONTEXT và các nguồn được trích dẫn.
Phân biệt rõ: dữ kiện trong hồ sơ, quy định pháp luật, suy luận và điểm chưa đủ căn cứ.
Không bịa điều luật, số văn bản, tình tiết hoặc nguồn.
Nếu nguồn mâu thuẫn hoặc thiếu, nêu rõ và yêu cầu kiểm tra thủ công.
"""
~~~

Ollama hỗ trợ FROM, ADAPTER, SYSTEM, PARAMETER và import adapter Safetensors/GGUF; base model phải đúng model đã dùng khi fine-tune.

## 8. Đánh giá và tiêu chí nghiệm thu

### OCR

- CER/WER theo loại tài liệu.
- Accuracy của trường quan trọng: số điều, số văn bản, ngày tháng, họ tên, số tiền.
- Table cell accuracy và reading order.
- Tỷ lệ vùng confidence thấp được phát hiện.

### Retrieval

- Recall@5/10, MRR/nDCG trên câu hỏi pháp lý đã có đáp án nguồn.
- Tỷ lệ trích đúng văn bản, điều, khoản, điểm.
- Hiệu quả của hybrid search so với vector-only.

### Generation

- Citation correctness: nguồn có thật và hỗ trợ phát biểu hay không.
- Completeness: có bỏ sót tình tiết quan trọng không.
- Groundedness: phát biểu có nằm trong nguồn không.
- Contradiction handling: nhận ra mâu thuẫn hay tự chọn một phía.
- JSON/schema validity, DOCX/XLSX render validity.
- Abstention rate trên câu hỏi thiếu căn cứ.

### Human acceptance gate

Một nhóm kiểm sát viên/luật gia phải duyệt các nhóm test khó: văn bản sửa đổi, nhiều thời điểm hiệu lực, lời khai mâu thuẫn, OCR sai một chữ/số, tài liệu lẫn vụ án và câu hỏi dẫn dụ. Chỉ triển khai nghiệp vụ khi người duyệt có thể mở nguồn gốc tới đúng trang/đoạn.

## 9. Bảo mật và quản trị dữ liệu

- Phân vùng dữ liệu gốc, dữ liệu đã ẩn danh, dữ liệu train, dữ liệu test và log.
- Mã hóa ổ đĩa/kho dữ liệu, RBAC theo vụ án/chức vụ, audit log truy cập và xuất file.
- Hash tài liệu, hash bản OCR, lưu model/version/prompt/nguồn cho mỗi output.
- Cấm prompt hoặc tài liệu bên ngoài tự ý thay đổi system policy; coi nội dung tài liệu là dữ liệu không đáng tin cậy.
- Không gửi hồ sơ lên API/cloud để OCR hoặc embedding nếu chưa có phê duyệt riêng.
- Có quy trình xóa, thu hồi quyền, xử lý bản sao và sự cố lộ dữ liệu.
- Chuyên gia pháp lý phải rà soát căn cứ xử lý dữ liệu cá nhân, đặc biệt vì dữ liệu về tội phạm/hành vi phạm tội là nhóm nhạy cảm trong các quy định bảo vệ dữ liệu hiện hành.

## 10. Lộ trình thực tế

### Mốc 1: 2–4 tuần

Làm ingestion, OCR baseline, kho provenance, hybrid retrieval và 30–50 câu hỏi test. Chưa fine-tune.

### Mốc 2: 4–8 tuần

Thêm schema tác vụ, pipeline Word/Excel, dashboard đánh giá, bộ dữ liệu đã ẩn danh và 500–2.000 ví dụ chất lượng cao.

### Mốc 3: 8–12 tuần

LoRA Qwen3-8B, benchmark với model base, thử Qwen3-14B Q4, thêm reranker và hard negatives.

### Mốc 4: sau pilot

Chỉ fine-tune OCR/embedding khi metric cho thấy lỗi có hệ thống; mở rộng task và quyền truy cập theo kết quả nghiệm thu.

## Nguồn kỹ thuật và pháp lý cần theo dõi

- [Qwen3 model card](https://huggingface.co/Qwen/Qwen3-14B)
- [Qwen3 trên Ollama](https://ollama.com/library/qwen3)
- [Ollama Modelfile](https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx)
- [Ollama import adapter/model](https://github.com/ollama/ollama/blob/main/docs/import.mdx)
- [PaddleOCR PP-StructureV3 và hỗ trợ tiếng Việt](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PP-StructureV3.html)
- [PaddleOCR-VL-1.6](https://www.paddleocr.ai/main/en/version3.x/algorithm/PaddleOCR-VL/PaddleOCR-VL-1.6.html)
- [TRL/PEFT LoRA và QLoRA](https://huggingface.co/docs/trl/peft_integration)
- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3)
- [Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15](https://vbpl.vn/TW/Pages/ivbpq-toanvan.aspx?ItemID=179252)
- [Bộ luật Tố tụng hình sự số 101/2015/QH13](https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/96172/VanBanGoc_101.2015.QH13.P1.pdf)
