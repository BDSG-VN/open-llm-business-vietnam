# BDSG Open Chat — giao diện trò chuyện

Giao diện trò chuyện đang chạy thật tại `chat.bdsg.vn`, phát hành nguyên trạng.

**1.272 dòng, không có bước đóng gói, không có phụ thuộc.** Ba tệp tĩnh: một
HTML, một JavaScript thuần dạng mô-đun, một CSS. Mở bằng bất kỳ máy chủ tĩnh nào.

## Vì sao không dùng khung giao diện nào

Một khung giao diện hiện đại sẽ mang theo bước đóng gói, cây phụ thuộc vài trăm
gói, và một lớp trạng thái phải học trước khi sửa được một nút. Đổi lại, nó cho
gì ở đây? Giao diện này có **một** màn hình, **một** danh sách, và **một** dòng
chảy chữ. Không đủ phức tạp để trả cái giá ấy.

Hệ quả đo được: sửa một dòng CSS là thấy ngay, không chờ đóng gói; và cả giao
diện đọc hết trong một buổi.

## Chạy thử

```bash
cd chat
python3 -m http.server 8080
```

Mở `http://localhost:8080`. Nó sẽ gọi `/api/*` và **hỏng** — vì chưa có máy chủ.
Xem phần hợp đồng bên dưới để nối vào máy chủ của bạn.

## Có gì

| | |
|---|---|
| Dòng chảy chữ | SSE, chữ hiện dần |
| **Dừng sinh** | nút gửi đổi vai thành nút dừng; **giữ phần đã nhận** |
| Chép câu trả lời | có đường lùi khi `navigator.clipboard` không dùng được |
| Sinh lại | gỡ cả cặp hỏi–đáp cũ rồi hỏi lại |
| Khối mã | tên ngôn ngữ + nút chép riêng |
| Trích dẫn | nhãn `[1] [2]` nối xuống danh sách nguồn |
| Hội thoại | danh sách, mở lại, **xoá** (có hỏi lại) |
| Chọn mô hình | một tên + mức nỗ lực, đặt trong thanh nhập |
| Cuộn | chỉ cuộn khi người đọc đang ở gần đáy |
| Màn hẹp | thanh bên thu lại, bảng chọn không tràn |
| Sáng / tối | theo hệ điều hành |

## Bốn quyết định đã trả giá để học

**1. Nút gửi đổi vai, không phải hai nút.** Hai nút cạnh nhau thì lúc nào cũng
có một cái vô nghĩa, và ở màn hẹp chúng ăn mất chỗ của ô chữ.

**2. Bảng chọn mô hình mở NGƯỢC LÊN TRÊN.** Khung nhập nằm sát đáy màn hình; một
bảng mở xuống dưới vẫn tồn tại trong DOM, vẫn bấm được bằng bàn phím, chỉ là
không ai thấy. Hỏng mà không báo.

**3. Nút xoá nằm CẠNH liên kết, không nằm TRONG nó.** Nút trong thẻ `<a>` thì bấm
nút cũng kích hoạt liên kết — người dùng vừa xoá vừa bị chuyển sang hội thoại vừa
xoá.

**4. Cuộn có điều kiện.** Cuộn xuống đáy vô điều kiện sau mỗi mẩu chữ làm người
đang đọc lại đoạn giữa bị giật xuống đáy mỗi vài trăm mili giây.

## Hợp đồng với máy chủ

Giao diện gọi **năm** đường. Cài đủ năm là nó chạy.

### `GET /api/mo-hinh`

```json
{
  "moHinh":        { "ma": "vi-du-v1", "ten": "Tên hiện ra", "moTa": "một câu" },
  "mucNoLuc":      [{ "muc": "nhanh", "ten": "Nhanh", "moTa": "…" }],
  "mucNoLucMacDinh": "nhanh",
  "danhSach":      [{ "ma": "vi-du-v1", "ten": "Tên hiện ra", "moTa": "", "suyLuan": false }]
}
```

`danhSach` **bắt buộc**, kể cả khi bạn chỉ có một mô hình: giao diện dùng nó để
đổi mã đọc được trong phản hồi thành tên người đọc được. Bỏ đi thì nhãn "câu trả
lời đến từ …" hiện ra mã trần — hỏng ngay tại chỗ có nhiệm vụ chống khai sai tên
mô hình.

### `POST /api/hoi` → `text/event-stream`

Thân yêu cầu:

```json
{ "hoiThoaiId": "uuid hoặc null", "noiDung": "câu hỏi", "mucNoLuc": "nhanh" }
```

Bốn loại sự kiện:

```
event: batdau
data: {"hoiThoaiId":"<uuid>"}

event: chu
data: {"chu":"một mẩu chữ"}

event: loi
data: {"thongBao":"câu báo lỗi cho người đọc"}

event: xong
data: {"trichDan":[…], "moHinhThat":"vi-du-v1"}
```

Khách bấm dừng thì giao diện `abort()` yêu cầu. Máy chủ nên nhận biết và ngừng
sinh; nếu không, bạn vẫn trả tiền cho phần chữ không ai đọc.

### `GET /api/hoi-thoai`

```json
{ "danhSach": [{ "id": "uuid", "tieuDe": "…", "suaLuc": "…" }] }
```

### `GET /api/hoi-thoai/:id`

```json
{ "id": "uuid", "tinNhan": [{ "vaiTro": "nguoi|may", "noiDung": "…", "moHinh": null, "trichDan": null }] }
```

### `DELETE /api/hoi-thoai/:id`

Trả `{"daXoa": true}` hoặc **404**.

> ⚠ Trả **404** cho cả "không có" lẫn "của người khác". Trả 403 là nói "có thứ
> đó, bạn không được đụng" — tức cho người lạ một cách dò xem một mã hội thoại
> có tồn tại hay không. Và hãy đặt điều kiện sở hữu **trong chính câu lệnh xoá**,
> đừng đọc lên rồi so ở tầng trên: cách kia có hai câu lệnh và một khoảng hở, và
> ngày nào ai đó gọi thẳng hàm xoá mà quên bước so thì dữ liệu người khác biến mất.

### `GET /api/toi` · `POST /api/dang-xuat`

Không bắt buộc. Thiếu thì phần chân thanh bên để trống, phần còn lại chạy bình
thường — giao diện **không có cổng đăng nhập**.

## Điều bản phát hành này KHÔNG gồm

**Máy chủ.** Phần máy chủ của `chat.bdsg.vn` chưa phát hành, và lý do phải nói
thẳng: nó gắn với một hệ đăng nhập một lần có **một lỗ hổng ghép-danh-tính-bằng-email
chưa vá phần gốc**. Đăng mã ấy lên là phát hành một công thức tấn công dùng được
ngay. Khi phần gốc được sửa, phần máy chủ sẽ theo sau.

Hợp đồng năm đường ở trên là đủ để tự viết máy chủ — và với một mô hình tương
thích OpenAI thì `POST /api/hoi` gần như chỉ là chuyển tiếp dòng chảy.

## Giấy phép

Apache-2.0, xem [`../LICENSE-CODE`](../LICENSE-CODE).
