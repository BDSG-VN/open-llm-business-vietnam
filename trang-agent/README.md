# trang-agent — trang của agent.bdsg.vn

Trang tĩnh, không có bước đóng gói, không một dòng JavaScript nào. Triển khai
bằng cách chép thẳng `index.html` vào docroot.

## Vì sao không có JavaScript

Chính sách bảo mật nội dung của vhost khai `script-src 'none'`. Khai đúng như
vậy thì một ngày nào đó có ai chèn script vào, trang hỏng **ngay** thay vì chạy
âm thầm. Một lời khai rộng tay hơn sự thật là một lời khai vô dụng.

## Con số trên trang

Mọi con số là **phép đo hoặc phép suy từ phép đo**, ngày 26/09/2026:

| | |
|---|---|
| 1.079.991 doanh nghiệp | `SELECT COUNT(*) FROM map5d.khach_dn` |
| 962.250 tên khác nhau | `COUNT(DISTINCT ten)` cùng bảng |
| 1.228 byte mỗi agent | đo trên 50.000 agent dựng thật, SQLite trên đĩa |
| 19,69 ms tra cứu | cùng phép đo, sau khi đưa khoá phạm vi vào MATCH |
| 1.595 token mỗi bài · $0,383/triệu | mẻ thử 10 lát qua cổng LiteLLM |

## Một con số CỐ Ý không dùng

Bảng 34 tỉnh có `dan_so_quy_doi`, tổng **113.571.926**. Đó là "quy mô dân số
quy đổi" theo NQ 202/2025/QH15, cao hơn dân số thường trú thật **12,1 %**, và
`scripts/sinh-tinh-loi.mjs` của kho landing ghi thẳng: *tuyệt đối không dùng
làm mẫu số*. Số agent quy mô dân số vì vậy lấy **~101,3 triệu**.

Trang nói ra cả hai con số và nói vì sao bỏ một cái. Giấu đi thì lần sau lại có
người cộng nhầm.

## Triển khai

Chép `index.html` vào docroot của tên miền rồi đặt lại chủ sở hữu tệp. Đường dẫn
cụ thể **cố ý không ghi ở đây**: kho này công khai, và bố cục thư mục của máy
chủ là thứ chỉ có ích cho người đang dò nó. Cổng `cong/khong-ha-tang.py` bắt
đúng lỗi ấy khi bản đầu của tệp này ghi ra — giữ nguyên bài học.

Vhost nằm trong tệp cấu hình Apache **dùng chung cho 56 tên miền**. Quy trình
sửa, không được bỏ bước nào:

1. sao lưu tệp cấu hình,
2. `apachectl configtest`,
3. **chỉ khi ĐẠT** mới `apachectl graceful`.

**Không bao giờ `restart`** — restart làm đứt kết nối của cả 56 tên miền, còn
graceful thì không.
