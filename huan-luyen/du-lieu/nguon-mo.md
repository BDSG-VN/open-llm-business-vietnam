# Nguồn ngữ liệu mở cho ba thứ tiếng

Cập nhật 25/09/2026.

## Đọc phần này trước, đừng bỏ qua

**Tôi không kiểm được giấy phép của bất kỳ nguồn nào trong phiên làm việc này.**
Phiên này không truy cập mạng. Mọi dòng "giấy phép" dưới đây là **những gì tôi
biết tính đến lúc viết**, không phải kết quả đọc lại điều khoản hôm nay. Giấy
phép của tập dữ liệu công khai **có đổi** — có tập siết lại sau khi phát hành,
có tập bị gỡ hẳn vì tranh chấp bản quyền.

Quy tắc bắt buộc trước khi tải bất cứ nguồn nào: **mở trang gốc, đọc mục
license, chụp màn hình lại, ghi ngày đọc vào `bo-du-lieu/giay-phep/` cùng file
tải về.** Một dự án phát hành công khai không được phép nói "tôi tưởng nó là
mở".

Bảng này cũng **không liệt kê hết** — nó chỉ ghi những tập tôi thật sự biết là
tồn tại. Thiếu một tên trong bảng không có nghĩa tập đó không dùng được; nó có
nghĩa tôi không đủ chắc để viết tên ra.

## Hai loại quyền, đừng lẫn

| | Ý nghĩa |
|---|---|
| **Tái phân phối được** | BDSG được phép đăng lại chính dữ liệu đó lên GitHub/HuggingFace (thường kèm điều kiện ghi nguồn hoặc chia sẻ tương tự). |
| **Chỉ huấn luyện được** | Được tải về, được huấn luyện, **không** được đăng lại dữ liệu gốc. Repo công khai chỉ chứa *script tải*, không chứa dữ liệu. |

Có một câu hỏi thứ ba mà **chưa ai trả lời dứt khoát trên thế giới**, và BDSG
cũng không trả lời được: *trọng số mô hình có phải là tác phẩm phái sinh của
ngữ liệu huấn luyện không?* Nếu có, điều khoản chia-sẻ-tương-tự của CC BY-SA
(Wikipedia) sẽ lây sang trọng số. Toà án chưa phán, giới học thuật chưa thống
nhất. Cách BDSG xử lý: **ghi đầy đủ nguồn nào đã vào mô hình nào, trong model
card**, để nếu sau này phải xử lý thì còn biết mà lần ra.

---

## Tiếng Việt — ngôn ngữ chính

| Nguồn | Nơi lấy | Giấy phép (theo hiểu biết, CHƯA kiểm lại hôm nay) | Tái phân phối |
|---|---|---|---|
| **Wikipedia tiếng Việt** | `dumps.wikimedia.org` (bản dump chính thức) | CC BY-SA (kèm GFDL cho nội dung cũ) | Được, nhưng dính điều kiện chia-sẻ-tương-tự |
| **FineWeb-2** (phần `vie_Latn`) | HuggingFace `HuggingFaceFW/fineweb-2` | ODC-By 1.0 (theo công bố của nhóm phát hành) | Được, phải ghi nguồn |
| **CulturaX** (phần `vi`) | HuggingFace `uonlp/CulturaX` | Kế thừa mC4 (ODC-BY) và OSCAR; **phải bấm chấp nhận điều khoản trên HuggingFace mới tải được** | Không rõ ràng — coi như chỉ huấn luyện |
| **OSCAR** (phần `vi`) | `oscar-project.org` / HuggingFace | Bản thân tập biên soạn thường để CC0, **nội dung bên trong là của Common Crawl** | Chỉ huấn luyện |
| **mC4** (phần `vi`) | HuggingFace `allenai/c4`, cấu hình multilingual | ODC-BY | Được, phải ghi nguồn |
| **CC-100** (phần `vi`) | StatMT / data.statmt.org | Theo điều khoản Common Crawl | Chỉ huấn luyện |
| **Wikisource / Wiktionary tiếng Việt** | dumps Wikimedia | CC BY-SA | Được, dính chia-sẻ-tương-tự |

### Nguồn tiếng Việt CẦN TRÁNH hoặc phải rất cẩn thận

| Nguồn | Vì sao |
|---|---|
| **Kho tin tức cào từ báo Việt Nam** (kể cả các bộ nổi tiếng trên GitHub) | Bản quyền toà soạn. Việc ai đó đã đăng lên GitHub **không** biến nó thành tập mở. Đây đúng là lý do `tin-tuc` bị loại khỏi ngữ liệu BDSG. |
| **Dữ liệu VLSP / các cuộc thi** | Thường phải ký thoả thuận sử dụng, nhiều bộ giới hạn phi thương mại. |
| **Tập UIT-* (ViQuAD, VSFC, …)** | Nhiều bộ ghi rõ "research only". Đọc kỹ từng bộ. |
| **Ngữ liệu 20GB của PhoBERT (VinAI)** | Bài báo có mô tả, nhưng bộ dữ liệu **không được phát hành công khai** để tải. Đừng ghi nó vào kế hoạch. |
| **OPUS / OpenSubtitles vi-en** | Phụ đề phim — nguồn gốc bản quyền rắc rối. TED2020 trong OPUS là CC BY-NC-ND: **phi thương mại và cấm tác phẩm phái sinh**, tức là không dùng huấn luyện được. |

---

## Tiếng Anh — ngôn ngữ thứ hai

| Nguồn | Nơi lấy | Giấy phép (CHƯA kiểm lại hôm nay) | Tái phân phối |
|---|---|---|---|
| **FineWeb / FineWeb-Edu** | HuggingFace `HuggingFaceFW/fineweb`, `…/fineweb-edu` | ODC-By 1.0 | Được, ghi nguồn |
| **C4** | HuggingFace `allenai/c4` | ODC-BY | Được, ghi nguồn |
| **Wikipedia tiếng Anh** | dumps Wikimedia | CC BY-SA | Được, chia-sẻ-tương-tự |
| **Project Gutenberg** | gutenberg.org | Phần lớn thuộc **phạm vi công cộng tại Mỹ** — không tự động công cộng ở nước khác | Kiểm từng đầu sách |
| **StackExchange data dump** | archive.org | CC BY-SA | Được, chia-sẻ-tương-tự |

### Tiếng Anh CẦN TRÁNH

| Nguồn | Vì sao |
|---|---|
| **The Pile (bản gốc)** | Có chứa **Books3**, phần đã bị gỡ vì vi phạm bản quyền sách. Dùng bản gốc là nhận rủi ro pháp lý không cần thiết. Nếu cần, chỉ lấy các thành phần sạch, từng phần một. |
| **Dolma (AI2)** | Không phải giấy phép mở thông thường mà là **AI2 ImpACT License**, có ràng buộc sử dụng. Không phải "không được dùng" — là "phải đọc mới biết được dùng thế nào". |
| **OpenWebText** | Là các trang web lấy theo link Reddit; bản thân bộ sưu tập không mang giấy phép rõ ràng cho nội dung. |

---

## Tiếng Trung — ngôn ngữ thứ ba

| Nguồn | Nơi lấy | Giấy phép (CHƯA kiểm lại hôm nay) | Tái phân phối |
|---|---|---|---|
| **Wikipedia tiếng Trung** | dumps Wikimedia | CC BY-SA | Được, chia-sẻ-tương-tự |
| **FineWeb-2** (phần `cmn_Hani`) | HuggingFace `HuggingFaceFW/fineweb-2` | ODC-By 1.0 | Được, ghi nguồn |
| **CulturaX** (phần `zh`) | HuggingFace `uonlp/CulturaX` | Như phần tiếng Việt — phải chấp nhận điều khoản | Coi như chỉ huấn luyện |

### Tiếng Trung — các tập phải kiểm kỹ trước khi động vào

| Nguồn | Tình trạng tôi biết |
|---|---|
| **WuDaoCorpora (BAAI)** | Phải nộp đơn xin, có thoả thuận sử dụng riêng. Không phải tải thẳng. |
| **SkyPile-150B (Skywork)** | Phát hành kèm giấy phép riêng của Skywork, **tôi không nhớ chính xác điều khoản** — phải đọc lại trước khi dùng. |
| **MNBVC** | Là dự án gom ngữ liệu từ **rất nhiều nguồn khác nhau**. Giấy phép của cả bộ không nói lên giấy phép của từng phần. Nếu dùng, phải chọn từng phần và kiểm từng phần. |
| **Bộ dữ liệu riêng của MiniMind** (`jingyaogong/minimind_dataset`) | **Mã nguồn** MiniMind là Apache-2.0 — điều đó **không** áp cho dữ liệu. Các tập `pretrain_hq`, `sft_*` của họ được tổng hợp lại từ nguồn bên thứ ba. Phải lần lại xuất xứ từng phần trước khi dùng. |

---

## Ngữ liệu của chính BDSG

Đây là phần BDSG sở hữu và là lý do cả dự án này tồn tại. Số đo ngày 25/09/2026
(CSDL `bdsg_chat`, bảng `doan_tri_thuc`), sau khi loại hai nguồn máy sinh:

| Nguồn | Số đoạn | Dung lượng |
|---|---:|---:|
| `ho-so-niem-yet` | 5.192 | 4,20 MB |
| `ho-so-dn` | 6.434 | 2,83 MB |
| `wiki-crm` | 107 | 0,13 MB |
| **Cộng** | **11.733** | **7,16 MB** (7.509.969 ký tự) |

Lớp có cấu trúc trong CSDL `postgres`:

- `business.company_profiles`: 6.672 bản ghi; **5.424** bản ghi đủ cả ba điều
  kiện (đã xuất bản ∧ có ngành ∧ có sản phẩm). **5.424 là con số duy nhất được
  dùng** khi nói "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ".
  Ký tự: tóm tắt 1.941.353 + sản phẩm 322.477 (trên 5.645 bản đã xuất bản).
- `business.capabilities`: 11.927 dòng, 346.704 ký tự tên (`name` + `name_en`).
  Cột `description` có 696.890 ký tự **nhưng chỉ 58 giá trị khác nhau** trên
  11.927 dòng — đó là chuỗi xuất xứ ETL lặp lại, **không phát hành**.
- `business.company_sector_links`: 6.666 công ty có ngành.

### Kiểm dữ liệu cá nhân (tự chạy 25/09/2026, không tin lời khai)

- 0 email · 0 số điện thoại · 0 URL nội bộ.
- Trong văn bản **có nhãn `[EMAIL]` và `[SĐT]`** ⇒ bước gỡ đã chạy thật.
- 29 khớp "mã số thuế": phần lớn là mã số thuế / số ĐKKD doanh nghiệp — đây là
  **thông tin đăng ký công khai ở Việt Nam** — lẫn vài dương tính giả (tên lớp
  CSS, trường `rev` trong JSON).
- 5 khớp "địa chỉ IP": **tất cả là dương tính giả** — số tiền viết kiểu Việt Nam
  (120.086.720.000 đồng).

---

## Tuyệt đối không phát hành, không huấn luyện

Danh sách này là **quyết định đã chốt**, không phải gợi ý.

| Nguồn | Số đo | Vì sao không |
|---|---|---|
| `map5d.khach_dn` | 1.079.991 bản ghi | 100% `nguon='crm_geocode_dot2'` ⇒ **dữ liệu CRM khách hàng**. Ngoài ra cột chỉ có `id, ten, do_chinh_xac, ma_xa, ma_tinh, geom, nguon, ngay_cap_nhat` — **không có cột ngành nghề, không có cột sản phẩm**. Nên ngay cả nếu được phép thì nó cũng không chứa thứ người ta tưởng nó chứa. |
| `kho-tri-thuc` | 118 tệp | **118/118** mang dòng cấp phép bên thứ ba ("Licensed to RAI Holdings"). |
| `ocop` | 1.727 sản phẩm | Văn quảng cáo người bán; url trỏ buudien.vn. |
| `tin-tuc` | — | Bản quyền toà soạn. |
| `bai-dang` | — | Nội dung người dùng đăng trên nền tảng. |
| `nao-agent` | 116 đoạn | **Máy sinh qua cổng LiteLLM** ⇒ đầu ra mô hình bên thứ ba; điều khoản nhà cung cấp thường cấm dùng để huấn luyện mô hình cạnh tranh. Thêm nữa, 3.601 não agent là **cấu hình thương mại của BDSG**. |
| `bai-dang-bds` | 5.939 đoạn | Cùng lý do máy sinh như trên. |

Đây chính là lý do con số phát hành được là **11.733 đoạn / 7,16 MB** chứ không
phải 17.788 đoạn: 6.055 đoạn máy sinh đã bị loại **trước** khi đếm.

---

## Cách dựng một tệp nguồn thực tế

1. Tải nguồn về `bo-du-lieu/tho/<ten-nguon>/`, kèm ảnh chụp trang giấy phép và
   ngày tải, đặt trong `bo-du-lieu/giay-phep/`.
2. Chuyển sang JSONL một dòng một đoạn: `{"text": "...", "nguon": "<ten-nguon>"}`.
3. Lọc rác cào web: `python3 lam_sach.py --vao … --chi-do --xem-thu 20` để nhìn
   trước, rồi chạy thật.
4. Trộn: `python3 tron.py --dinh-dang pretrain --nguon vi=… --nguon en=… --nguon zh=…`.
5. Ghi vào model card: tên nguồn, ngày tải, giấy phép, số ký tự thực tế đã dùng
   (lấy từ `bao-cao-tron.json` mà `tron.py` sinh ra).

Bước 5 không phải thủ tục. Một bản phát hành mà không nói được mình học từ đâu
thì không ai kiểm được, kể cả chính BDSG sáu tháng sau.
