# Lần huấn luyện đầu tiên — 26/09/2026

Đây là lần đầu BDSG có **trọng số do chính mình huấn luyện**. Trước ngày này,
mọi mô hình BDSG phục vụ đều trả `bdsg_la_trong_so_bdsg = false`.

Mô hình này **không dùng được cho việc gì**. Nó tồn tại để chứng minh toàn tuyến
chạy được từ đầu tới cuối, và để mọi con số ước lượng có một điểm neo thật.

## Chạy gì

| | |
|---|---|
| Máy | Apple M1, 8 GB RAM dùng chung với hệ thống, không GPU rời |
| Thiết bị | MPS |
| Ngữ liệu | 11.699 đoạn · 7.474.485 ký tự · **2.068.295 token** |
| Tokenizer | byte-level BPE, từ vựng 6.400 — đo lại trên chính ngữ liệu này: **3,61 ký tự/token** |
| Kiến trúc | 512 chiều ẩn · 8 lớp · 8 đầu truy vấn / 4 đầu khoá-giá trị · ngữ cảnh 512 |
| Tham số | **26.878.464** — công thức tính ra và phép đếm thật **khớp tuyệt đối** |
| Chia tập | 3.999 khối học / 40 khối kiểm |

## Kết quả

| bước | loss học | perplexity học | loss kiểm | perplexity kiểm |
|---:|---:|---:|---:|---:|
| 1 | 8,8824 | 7.203,9 | | |
| 100 | 4,0780 | 59,0 | | |
| 200 | 3,2865 | 26,7 | | |
| 300 | 3,2642 | 26,2 | 4,7426 | 114,7 |
| **400** | **2,9900** | **19,9** | **4,6302** | **102,5** |

- **3.276.800 token đã học** trong **53 phút 54 giây**, tốc độ cuối 1.675 token/giây.
- Trọng số xuất ra: **74 tensor · 26.878.464 tham số · 107,5 MB**, không cảnh báo.

## Nó sinh ra gì

Ba câu mồi, nhiệt độ 0,8, top-p 0,9:

> **Công ty** Cổ phần Dịch vụ Quốc tế Hạt và Giải pháp lý truyền thống nền tảng AI
> tư vấn chuyên nghiệp, quản lý, phần mềm quản lý giải pháp lý…

> **Doanh nghiệp hoạt động trong lĩnh vực** phần mềm và dịch vụ CNTT, chuyên cung
> cấp các giải pháp tài chính như tổng hợp, công nghệ và quản lý công nghệ…

> **Dự án bất động sản tại** Thái Nguyên. Công ty TNHH Thương mại và Thương mại Xây
> dựng Đầu tư & Phát hoạt động trong lĩnh vực xây dựng và phát triển bất động sản
> tại khu vực Hà Nội…

Ngữ pháp tiếng Việt đúng, đúng lĩnh vực, cấu trúc câu hợp lý. Và **nó bịa** — tên
công ty không có thật, "Thương mại và Thương mại" lặp, "Giải pháp lý" vô nghĩa.

## Hai con số nói thẳng vì sao mô hình này chưa dùng được

**1. Quá khớp, đo được.** Perplexity học 19,9 nhưng phần kiểm 102,5 — gấp **5,2
lần**. Mô hình đang thuộc lòng ngữ liệu chứ chưa khái quát hoá.

**2. Ngữ liệu thiếu khoảng 348 lần.** Tỉ lệ tính-toán-tối-ưu khoảng 20 token cho
mỗi tham số ([Hoffmann và cộng sự 2022](https://arxiv.org/abs/2203.15556)). Với
26,88 triệu tham số, mức ấy là ~538 triệu token. Ngữ liệu hiện có 2,07 triệu —
**0,38%**. Hai con số này giải thích nhau: không phải mô hình dở, mà là **ngữ liệu
quá ít cho cỡ mô hình này**.

Đây là điều phải quyết **trước** khi thuê GPU, không phải sau. Ba hướng:

| Hướng | Nghĩa là |
|---|---|
| Thu thêm ngữ liệu tiếng Việt mở | Đúng hướng, nhưng phải kiểm giấy phép từng nguồn |
| Thu nhỏ mô hình cho vừa ngữ liệu | Rẻ và nhanh, nhưng trần chất lượng thấp |
| Chấp nhận mô hình hẹp, chỉ làm một việc | Hợp nếu việc ấy là sinh văn mô tả doanh nghiệp |

Chưa chọn. Phải chọn bằng số, không bằng cảm tính.

## Trọng số nằm ở đâu

**Không nằm trong kho này.** 107,5 MB vượt xa mức hợp lý cho một kho mã, và
`.gitignore` chặn `*.safetensors` có chủ ý. Trọng số của lần chạy này nằm ở máy
đã huấn luyện. Ngày có bản đáng phát hành, nó sẽ đi qua một kênh phát hành riêng
kèm thẻ mô hình và số đo, không phải đi qua git.

## Điều lần chạy này KHÔNG chứng minh

- **Chưa chạy bộ chuyển đổi sang định dạng máy chủ suy luận cục bộ.** Tệp xuất ra
  đúng hình dạng và qua 7/7 phép kiểm, nhưng chưa ai chạy bộ chuyển đổi thật lên nó.
- **Chưa thử nạp bằng công cụ khác.** Giữ tên trường theo chuẩn chung là ĐỂ việc
  đó khả thi, chưa phải bằng chứng là nó chạy.
- **Chưa tinh chỉnh theo chỉ dẫn.** Mô hình này chỉ biết nối chữ, chưa biết trả lời.
- **Chưa chạy bộ đánh giá 227 câu.** Chưa có gì để so với đường cơ sở.
