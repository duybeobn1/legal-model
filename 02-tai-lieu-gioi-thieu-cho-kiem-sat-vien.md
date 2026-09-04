# Tài liệu giới thiệu Local Legal AI cho kiểm sát viên

## 1. Hệ thống này là gì?

Đây là một trợ lý AI chạy tại máy nội bộ, không cần kết nối Internet trong lúc sử dụng. Hệ thống có thể đọc PDF/Word, nhận diện PDF scan, tìm kiếm trong kho văn bản được phê duyệt và tạo bản nháp báo cáo.

Hệ thống không phải là “một kiểm sát viên điện tử”. Nó không có thẩm quyền tố tụng, không tự xác định một người có tội, không thay thế đánh giá chứng cứ và không thay thế việc ký/phê duyệt của người có thẩm quyền.

## 2. Hệ thống làm việc như thế nào?

~~~text
Tài liệu -> đọc/OCR -> lập chỉ mục -> tìm nguồn liên quan
         -> AI phân tích trong phạm vi nguồn
         -> hiển thị câu trả lời + trang/đoạn trích dẫn
         -> kiểm sát viên kiểm tra -> xuất bản nháp Word/Excel
~~~

Có hai loại “trí nhớ” cần phân biệt:

- **Kho tài liệu:** chứa luật, hướng dẫn và hồ sơ đã được phép đưa vào hệ thống. Kho này có thể cập nhật, thu hồi hoặc thay phiên bản.
- **Model:** là bộ máy ngôn ngữ học cách đọc, tóm tắt, hỏi đáp và xuất kết quả theo mẫu. Model không nên là nơi lưu bí mật của từng vụ án.

Vì vậy, khi luật thay đổi, cách an toàn là cập nhật kho văn bản và thời điểm hiệu lực, không phải mỗi lần thay luật lại huấn luyện lại toàn bộ model.

## 3. Có thể dùng vào việc gì?

### Có thể hỗ trợ

- Tạo bản tóm tắt theo mẫu, kèm nguồn trang.
- Lập dòng thời gian sự kiện.
- Lập danh sách người, tài liệu, vật chứng và tình tiết được đề cập.
- Tìm các đoạn lời khai liên quan tới một sự kiện.
- So sánh hai lời khai, chỉ ra điểm giống/khác và dẫn cả hai nguồn.
- Tìm điều/khoản, văn bản hướng dẫn và các quy định liên quan.
- Lập bảng theo dõi tài liệu còn thiếu.
- Tạo bản nháp Word/Excel từ dữ liệu có cấu trúc.

### Không được giao toàn quyền

- Kết luận một người có tội hay không có tội.
- Tự đánh giá tính thật/giả hoặc giá trị chứng minh của chứng cứ.
- Tự suy ra tình tiết không có trong hồ sơ.
- Tự chọn văn bản đã hết hiệu lực khi có văn bản mới.
- Tự gửi, ký, ban hành hoặc thay đổi hồ sơ tố tụng.
- Tự xử lý hồ sơ của vụ án mà người dùng không có quyền truy cập.

## 4. Dữ liệu cần chuẩn bị

### Nhóm A — văn bản pháp luật

Đơn vị cần cung cấp danh mục văn bản chính thức được phép sử dụng, gồm:

- Tên, số, ngày ban hành, cơ quan ban hành.
- Ngày có hiệu lực và ngày hết hiệu lực nếu có.
- Văn bản sửa đổi, thay thế hoặc hướng dẫn.
- Phạm vi áp dụng và ghi chú về thời điểm hành vi.
- Người/bộ phận đã kiểm tra bản đúng.

Không nên chỉ gửi một thư mục PDF không có danh mục. Nếu không biết văn bản nào đang có hiệu lực, hệ thống cũng không thể tự bảo đảm câu trả lời đúng.

### Nhóm B — hồ sơ và tài liệu thực tế

Có thể gồm quyết định, biên bản, lời khai, kết luận giám định, tài liệu điện tử, bản cáo trạng, bản án và các tài liệu nghiệp vụ khác trong phạm vi được phép.

Mỗi file nên có:

- Mã vụ án hoặc mã hồ sơ.
- Loại tài liệu.
- Ngày lập/nhận.
- Cơ quan hoặc người lập.
- Số trang và tình trạng bản gốc/bản sao.
- Mức độ mật và nhóm người được xem.
- Ghi chú văn bản đã được kiểm tra hay chưa.

### Nhóm C — mẫu đầu ra

Cần cung cấp các mẫu Word/Excel đã được phê duyệt và giải thích ý nghĩa từng trường, ví dụ:

- Mục nào bắt buộc.
- Mục nào chỉ được lấy nguyên văn.
- Mục nào được tóm tắt.
- Mục nào phải có trích dẫn.
- Quy tắc định dạng ngày, số tiền, điều/khoản và viết tắt.

## 5. OCR là gì và cần kiểm tra gì?

PDF có hai loại thường gặp:

- PDF có lớp chữ: có thể bôi đen/copy chữ. Hệ thống đọc trực tiếp nhưng vẫn phải kiểm tra bố cục.
- PDF dạng ảnh: mỗi trang là hình scan. Hệ thống phải OCR, tức nhận diện chữ từ hình ảnh.

OCR có thể nhầm các ký tự gần nhau, số 1/7, 0/6, dấu tiếng Việt, số văn bản, tên riêng, chữ viết tay, chữ bị che bởi dấu hoặc bảng. Vì vậy, các trường quan trọng phải có bước kiểm tra người thật.

Khi kiểm tra OCR, không chỉ nhìn văn bản liền mạch. Cần đối chiếu bản ảnh ở đúng trang, đặc biệt với tên, ngày, số tiền, số điều, số điện thoại, biển số và nội dung trong bảng.

## 6. Cần hand label những gì?

Hand label nghĩa là chuyên gia xem tài liệu thật và đánh dấu đáp án chuẩn để hệ thống học hoặc để đánh giá.

### Với OCR

- Vùng chữ hoặc dòng chữ trên ảnh.
- Nội dung chính xác của vùng đó.
- Bảng, ô bảng, con dấu, tiêu đề, chân trang.
- Trường hợp chữ không đọc được, đánh dấu “không chắc/không đọc được”, không đoán.

Ví dụ:

~~~text
Ảnh trang 12: “Điều 173 khoản 2 điểm c”
Nhãn chuẩn: vùng chữ + đúng transcript “Điều 173 khoản 2 điểm c”
~~~

### Với tóm tắt

Chuyên gia cung cấp bản tóm tắt chuẩn, mỗi ý có nguồn trang:

~~~text
Ý: Bị can gặp người X tại địa điểm Y vào ngày Z.
Nguồn: hồ sơ A, trang 12; biên bản B, trang 4.
Mức độ: được ghi nhận trong tài liệu, chưa phải kết luận về sự thật.
~~~

### Với mâu thuẫn lời khai

Không gán nhãn đơn giản là “lời khai đúng/sai”. Nên ghi:

~~~text
Chủ đề: thời điểm gặp nhau
Lời khai 1: 20:00, nguồn trang 5
Lời khai 2: 22:00, nguồn trang 18
Loại: mâu thuẫn về thời gian
Yêu cầu: người dùng tự đánh giá bằng các chứng cứ khác
~~~

### Với tham chiếu pháp luật

Mỗi câu trả lời chuẩn cần có:

- Vấn đề pháp lý.
- Tình tiết nào đã được xác định trong nguồn.
- Điều/khoản/điểm được viện dẫn.
- Văn bản và thời điểm hiệu lực.
- Phần nào là suy luận.
- Phần nào chưa đủ căn cứ.

## 7. Ví dụ đầu ra đúng và đầu ra không được chấp nhận

### Được chấp nhận

> “Trong biên bản hỏi cung ngày ..., người A khai ... tại trang 8. Trong lời khai ngày ..., người A trình bày ... tại trang 15. Hai nội dung khác nhau về thời điểm. Chưa đủ căn cứ từ hai tài liệu này để kết luận nguyên nhân mâu thuẫn.”

### Không được chấp nhận

> “Người A chắc chắn khai gian vì lời khai sau là không hợp lý.”

Lý do: hệ thống đã biến nhận xét chủ quan thành kết luận, không chỉ ra căn cứ và không cho người dùng thấy nguồn đối chiếu.

### Được chấp nhận khi tra luật

> “Theo văn bản X, Điều ..., khoản ..., quy định ... . Văn bản được đánh dấu có hiệu lực từ ... . Tình tiết trong hồ sơ hiện mới thể hiện ... . Việc quy định này có áp dụng vào vụ việc cụ thể hay không cần kiểm sát viên kiểm tra thêm các điều kiện ... .”

### Không được chấp nhận khi tra luật

> “Trường hợp này chắc chắn cấu thành tội ... theo Điều ...”

Lý do: thiếu phân tích đầy đủ các dấu hiệu pháp lý, chứng cứ, thời điểm áp dụng và các tình tiết liên quan.

## 8. Quy trình sử dụng an toàn

1. Kiểm tra người dùng đang mở đúng mã vụ án và có quyền truy cập.
2. Nạp tài liệu, kiểm tra số trang và trạng thái OCR.
3. Yêu cầu hệ thống tóm tắt hoặc tra cứu với phạm vi rõ ràng.
4. Đọc câu trả lời cùng các trích dẫn; mở bản gốc tới đúng trang.
5. Sửa bản nháp nếu cần; không coi file Word/Excel do AI tạo là bản chính thức.
6. Đánh dấu lỗi theo loại: OCR, bỏ sót nguồn, trích sai luật, suy diễn, định dạng hoặc quyền truy cập.
7. Người có thẩm quyền phê duyệt trước khi dùng trong nghiệp vụ.

## 9. Cách báo lỗi để hệ thống tốt lên

Mỗi lỗi nên ghi:

- Mã phiên chạy và người dùng.
- Câu hỏi đã nhập.
- Tài liệu/nguồn được hệ thống sử dụng.
- Kết quả sai ở đâu.
- Kết quả đúng mong muốn.
- Lỗi thuộc OCR, tìm kiếm, model, dữ liệu hay mẫu Word/Excel.
- Mức độ nghiêm trọng.

Không đưa nguyên văn hồ sơ sang kênh hỗ trợ bên ngoài nếu chưa được phép. Có thể dùng mã tài liệu, số trang và đoạn đã ẩn danh để trao đổi.

## 10. Điều kiện để hệ thống được đưa vào sử dụng

Trước pilot cần thống nhất:

- Danh mục người dùng và quyền truy cập.
- Kho văn bản pháp luật chính thức và người chịu trách nhiệm cập nhật.
- Quy trình ẩn danh/cho phép sử dụng dữ liệu vụ án.
- Bộ test do kiểm sát viên xây dựng.
- Mức sai sót OCR chấp nhận được theo từng loại trường.
- Mức bắt buộc phải có citation.
- Quy trình xử lý khi hệ thống không chắc chắn hoặc nguồn mâu thuẫn.
- Quy định rằng output AI là bản nháp, cần người kiểm tra.

## 11. Thông điệp quan trọng

Giá trị của hệ thống không nằm ở việc nó “nói giống người” mà ở việc nó:

- tìm đúng tài liệu;
- chỉ đúng trang/đoạn;
- phân biệt dữ kiện với suy luận;
- nhận ra thiếu và mâu thuẫn;
- tôn trọng thời điểm hiệu lực của pháp luật;
- không bịa nguồn;
- để người có chuyên môn kiểm soát quyết định cuối cùng.

## Nguồn tham chiếu

- [Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15](https://vbpl.vn/TW/Pages/ivbpq-toanvan.aspx?ItemID=179252)
- [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=187276)
- [Bộ luật Tố tụng hình sự số 101/2015/QH13](https://vbpl.vn/FileData/TW/Lists/vbpq/Attachments/96172/VanBanGoc_101.2015.QH13.P1.pdf)
- [PaddleOCR hỗ trợ pipeline tài liệu và tiếng Việt](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PP-StructureV3.html)
