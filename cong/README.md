# cong/ — cổng kiểm tự động trước khi đẩy lên kho công khai

Thư mục này có bốn cổng và một kịch bản chạy tất cả. Chúng chạy **trước** khi đẩy, không
phải sau.

## Vì sao phải chặn trước, không phải dọn sau

Đẩy lên kho công khai là việc **một chiều**. GitHub giữ lịch sử, các bản fork giữ bản sao,
bộ nhớ đệm máy tìm kiếm giữ nội dung. `git push --force` xoá được nhánh, nhưng không xoá
được thứ người khác đã lấy về.

Hệ quả thực tế, theo đúng thứ tự phải làm:

| Lỡ đẩy thứ gì | Xoá commit có cứu được không | Việc thật phải làm |
|---|---|---|
| Khoá API, token | **Không** | Thu hồi khoá, cấp khoá mới |
| Địa chỉ máy chủ, đường dẫn nội bộ | **Không** | Không có cách thu hồi. Chỉ còn cách đổi hạ tầng |
| Dữ liệu khách hàng | **Không** | Đây là lý do cổng 3 là cổng tuyệt đối |
| Đường khai thác lỗ hổng chưa vá | **Không** | Chạy đua vá trong khi người khác đã có bản sao |

Không cột nào trong bảng trên có chữ "có". Đó là toàn bộ lý do tồn tại của thư mục này.

## Chạy

```bash
cong/chay-tat-ca.sh                 # tự kiểm + quét toàn kho  ← chạy cái này trước khi đẩy
cong/chay-tat-ca.sh --goc <thư mục> # quét một thư mục khác
cong/chay-tat-ca.sh --chi-tu-kiem   # chỉ bắt các cổng chứng minh chúng cắn

python3 cong/khong-bi-mat.py            # chạy riêng một cổng
python3 cong/khong-bi-mat.py --tu-kiem  # bài thử ngược của riêng cổng đó
```

Mã thoát của mọi cổng và của kịch bản: `0` đạt · `1` có vi phạm · `2` cổng tự vỡ.
**Mã 2 cũng là hỏng.** Cổng không chạy được thì kết luận duy nhất được phép rút ra là
"chưa biết", không phải "sạch".

`chay-tat-ca.sh` **luôn chạy bài tự kiểm trước khi quét**. Một cổng luôn trả "sạch" trông
y hệt một cổng hỏng; phải bắt nó cắn được chuỗi cố tình cài vào rồi mới tin lời nó nói về
kho. Cổng nào trượt tự kiểm thì bước quét của nó bị **bỏ hẳn** và tính là hỏng — chứ không
phải chạy rồi lấy kết quả.

## Bốn cổng

| Cổng | Chặn gì | Vì sao | Miễn trừ nội dòng |
|---|---|---|---|
| `khong-bi-mat.py` | khoá API (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, Slack, Google), khoá riêng PEM, JWT, chuỗi kết nối có mật khẩu, tệp `.env`, tệp khoá `.pem/.key/.p12` | Lộ khoá là mất quyền kiểm soát tài khoản. Xoá commit vô ích, phải thu hồi khoá | **Không** |
| `khong-ha-tang.py` | IPv4 công cộng, đường dẫn vận hành, tên container, tên miền quản trị, số cổng nội bộ | Hạ tầng **không có nút thu hồi**. Lộ là lộ vĩnh viễn, và là bản đồ cho người dò | Có |
| `khong-du-lieu-cam.py` | bản ghi không chứng minh được nguồn; nguồn bị cấm (dữ liệu CRM khách hàng, tài liệu có cấp phép bên thứ ba, nội dung người khác, đầu ra máy sinh) | Dữ liệu của người khác thì không có lý do kỹ thuật nào biến thành của mình | **Không** |
| `khong-lo-hong.py` | cookie phiên kèm giá trị, cờ bảo mật bị tắt, đường dẫn và số dòng của hệ đang chạy, mô tả khai thác gắn với vật thể cụ thể | Viết đường khai thác mất 10 giây, vá hệ mất nhiều ngày. Khoảng chênh ấy là cửa sổ tấn công | Có |

Chi tiết đầy đủ nằm trong phần đầu mỗi tệp `.py`, kèm số đo và ngày đo.

## Hai nguyên tắc mà cổng nào cũng phải giữ

### 1. Cổng phải TỰ KHAI PHẠM VI

Mỗi cổng mở đầu bằng mục **PHẠM VI TỰ KHAI**: nó quét cái gì, và **nó không quét cái gì**.
Phần thứ hai quan trọng hơn. Một cổng không nói rõ chỗ mù của mình sẽ được người ta hiểu
là bảo vệ toàn diện, và đó là lúc nó nguy hiểm hơn cả không có cổng.

Những chỗ mù đã biết, tính đến 25/09/2026:

- **Ảnh chụp màn hình**: không cổng nào đọc. Một ảnh terminal lộ nhiều hơn mọi thứ bốn cổng
  bắt được. Phải soi bằng mắt.
- **IPv6**: chưa có luật. Chưa đo, đừng tưởng đã chặn.
- **Tệp nhị phân và trọng số mô hình**: không mở ra đọc. Bí mật nằm trong trọng số là thứ
  **chưa đo**. Riêng cổng bí mật thì báo hỏng nếu gặp tệp nhị phân có đuôi chưa khai —
  thà bắt khai còn hơn im lặng bỏ qua.
- **Lịch sử git**: các cổng quét cây thư mục hiện tại, không quét commit cũ.

Vì vậy, dòng cuối của bảng tổng kết viết đúng như nó là: *"không tìm thấy thứ đã biết cách
tìm"*, chứ không phải *"kho đã an toàn"*.

### 2. Cổng phải được THỬ NGƯỢC — phải chứng minh nó CẮN

Mọi cổng đều có `--tu-kiem`: dựng một thư mục tạm, **cố tình cài vào đó thứ phải bị bắt**,
chạy chính hàm quét ấy, rồi đòi hai điều — bắt đủ mọi mẫu đã cài, và **không** bắt nhầm các
dòng sạch làm đối chứng.

Nguyên tắc này không phải lý thuyết. Nó sinh ra từ một phép đo sai suýt cho kết luận ngược:

> Câu lệnh dò địa chỉ IP viết cho `git grep` có dùng `\b`. `git grep` chạy biểu thức chính
> quy POSIX ERE, **không hiểu `\b`**, nên trả về 0 kết quả — trong khi dữ liệu có IP thật.
> Suýt kết luận "kho sạch".

Cho nên: mọi cổng ở đây viết bằng `re` của Python, **không** dựa vào `git grep`; và
`khong-ha-tang.py --tu-kiem` cài sẵn một chuỗi IP công cộng để chứng minh cổng cắn được nó.

Cùng họ với bẫy ấy, hai thứ nữa đã gặp thật và đã được xử trong mã:

- **Một byte NUL** làm `grep` im lặng coi cả tệp là nhị phân rồi bỏ qua; `file` chỉ báo
  `data`. Ở đây tệp nhị phân đuôi lạ bị **báo hỏng**, không được bỏ qua im lặng.
- **Số tiền kiểu Việt Nam trông y hệt địa chỉ IP.** Lần quét ngữ liệu 25/09/2026 có 5 khớp
  "địa chỉ IP" thì cả 5 đều là số tiền. Cách xử **không phải** nới luật, mà là siết đúng
  chỗ: octet có số 0 đứng đầu thì không phải IP (`086`, `000`), hai bên khớp không được
  dính chữ số hay dấu chấm, và ngay sau khớp là "đồng"/"VND" thì là tiền.

## Thêm ngoại lệ cho đúng cách

### Cổng nào cho miễn trừ, cổng nào không — và vì sao lệch nhau

- `khong-ha-tang` và `khong-lo-hong` **có** miễn trừ nội dòng. Hai cổng này là heuristic,
  chắc chắn có dương tính giả thật, và một cổng không có đường thoát hợp pháp sẽ bị người
  ta tắt hẳn — mất cả cổng.
- `khong-bi-mat` và `khong-du-lieu-cam` **không** có. Hai cổng này tuyệt đối: không có lý do
  nào đủ tốt để giữ một khoá thật hay dữ liệu khách hàng trong kho công khai. Nếu bị bắt
  oan thì phải sửa **luật**, không phải mở **lỗ**.

### Cú pháp miễn trừ

Ghi ngay trên chính dòng bị bắt, theo dạng:

```
<dấu miễn trừ> <tên-cổng> ly-do=<lý do cụ thể>
```

- `<dấu miễn trừ>` là chuỗi `cong` nối với `:bo-qua`.
- `<tên-cổng>` là `khong-ha-tang` hoặc `khong-lo-hong`.
- Phần `ly-do=` là **bắt buộc**. Miễn trừ thiếu lý do thì chính nó bị tính là vi phạm, mã
  `mien-tru-khong-ly-do`. Một ngoại lệ không lý do là một lỗ thủng mà vài tháng sau không
  ai nhớ vì sao đã mở — và vì không ai nhớ, không ai dám đóng.

> Tài liệu này **cố ý không viết ví dụ đầy đủ đã ghép sẵn**. Một ví dụ đầy đủ sẽ bị chính
> cổng đếm là "một miễn trừ đang dùng", và con số trên bảng tổng kết sẽ sai ngay từ dòng
> đầu tiên. Hiện tại số ấy là **0**, và nó đáng được giữ đúng.

Mọi miễn trừ đang dùng đều được **đếm và in ra** ở đầu báo cáo mỗi cổng. Đó là chủ ý: ngoại
lệ phải nhìn thấy được, không được trở thành thứ vô hình.

### Ba việc phải làm khi thêm ngoại lệ

1. **Ưu tiên sửa nội dung trước.** Cần một địa chỉ IP làm ví dụ? Dùng dải RFC5737 —
   `192.0.2.x`, `198.51.100.x`, `203.0.113.x` — vốn sinh ra để làm ví dụ và không trỏ tới
   máy nào.
2. **Viết lý do cụ thể.** "dương tính giả" không phải lý do. "số tiền trong báo cáo tài
   chính, không phải địa chỉ máy chủ" mới là lý do.
3. **Thêm một ca vào `tu_kiem()`.** Nếu ngoại lệ mở rộng tới mức làm thủng một trường hợp
   khác, bài thử ngược phải phát hiện được. **Ngoại lệ không có bài thử là lỗ thủng.**

### Nới luật thì phải khai số đo

Muốn thêm một nguồn vào `NGUON_DUOC_PHEP` của `khong-du-lieu-cam.py`, phải kèm **số đo và
ngày đo**, như các nguồn đang có. Nguồn chưa khai thì mặc định là **chưa được phát hành** —
cổng không đoán hộ. Đây là ý nghĩa của chữ *fail-closed*: bản ghi thiếu trường `nguon` bị
tính là hỏng không phải vì nó chắc chắn bẩn, mà vì **nó không chứng minh được là sạch**.

Ngoại lệ tốt nhất là ngoại lệ không phải tồn tại. `NGOAI_LE_TEP` trong
`khong-du-lieu-cam.py` hiện **rỗng**, và đó là kết quả của một lần sửa thật: bản đầu bắt
dấu hiệu nguồn cấm trên mọi tệp văn bản, chạy ngày 25/09/2026 thì bắt 15 chỗ trong
`MODEL-CARD.md`, `README.md` và `bo-du-lieu/README.md` — toàn bộ là bảng liệt kê *"đã loại
nguồn nào và vì sao"*. Cổng đang phạt người viết vì họ ghi rõ mình đã loại cái gì. Thay vì
mở ngoại lệ cho từng tệp, ranh giới được sửa lại: xét **hình dạng** chứ không xét **chuỗi**.
Nhắc tên nguồn trong câu văn là tài liệu; một bản ghi của nguồn ấy dán vào giữa tài liệu mới
là rò rỉ. Sau khi sửa, không tệp nào cần ngoại lệ nữa.

## Khi thêm một cổng mới

Khai tên tệp vào mảng `CONG_MONG_DOI` trong `chay-tat-ca.sh`. Kịch bản **cố ý không dùng**
`*.py`: glob im lặng bỏ qua cổng bị xoá, và bảng tổng kết vẫn "toàn ĐẠT" trong khi kho đã
mất một cổng. Ngược lại, tệp `.py` nằm trong `cong/` mà không có trong danh sách sẽ bị báo
hỏng — vì một cổng không bao giờ được gọi thì không bảo vệ gì cả, nó chỉ tạo cảm giác an
toàn. Đó là kiểu hỏng tệ nhất: hỏng mà không báo.

Cổng mới phải có đủ: mục **PHẠM VI TỰ KHAI** (gồm phần *không* quét), `--tu-kiem` với cả
mẫu-phải-bắt lẫn dòng-sạch-đối-chứng, mã thoát `0/1/2`, và **không bao giờ in ra giá trị bí
mật** — chỉ in vị trí. In giá trị ra là làm lộ lần thứ hai, lần này vào log CI, mà log CI
thường dễ đọc hơn cả kho.
