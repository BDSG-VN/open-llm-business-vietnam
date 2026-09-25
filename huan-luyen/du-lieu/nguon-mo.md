# Nguồn ngữ liệu mở — tiếng Việt và tiếng Anh

Cập nhật 26/09/2026. Phạm vi ngôn ngữ của dự án rút về đúng **hai**: **tiếng
Việt là chính, tiếng Anh là phụ**. Bảng này trước đó có một cột thứ ba cho một
ngôn ngữ nay đã ra khỏi phạm vi — cột ấy **đã bỏ**, cùng với mọi nhánh xử lý
tương ứng trong `tron.py` và `huan-luyen/tu-vung/`.

## Đọc phần này trước, đừng bỏ qua

**Tôi không kiểm được giấy phép của bất kỳ nguồn nào trong phiên làm việc này.**
Phiên này không truy cập mạng. Mọi dòng "giấy phép" dưới đây là **những gì tôi
biết tính đến lúc viết**, không phải kết quả đọc lại điều khoản hôm nay. Giấy
phép của tập dữ liệu công khai **có đổi** — có tập siết lại sau khi phát hành,
có tập bị gỡ hẳn vì tranh chấp bản quyền.

Quy tắc bắt buộc trước khi tải bất cứ nguồn nào: **mở trang gốc, đọc mục
license, chụp màn hình lại, ghi ngày đọc vào `bo-du-lieu/giay-phep/` cùng tệp
tải về.** Một dự án phát hành công khai không được phép nói "tôi tưởng nó là
mở".

Bảng này cũng **không liệt kê hết** — nó chỉ ghi những tập tôi thật sự biết là
tồn tại. Thiếu một tên trong bảng không có nghĩa tập đó không dùng được; nó có
nghĩa **tôi không đủ chắc để viết tên ra**. Thà thiếu còn hơn bịa một cái tên
nghe hợp lý rồi ai đó đi tìm cả buổi.

## Hai loại quyền, đừng lẫn

| | Ý nghĩa |
|---|---|
| **Tái phân phối được** | BDSG được phép đăng lại chính dữ liệu đó lên kho công khai (thường kèm điều kiện ghi nguồn hoặc chia sẻ tương tự). |
| **Chỉ huấn luyện được** | Được tải về, được huấn luyện, **không** được đăng lại dữ liệu gốc. Kho công khai chỉ chứa *script tải*, không chứa dữ liệu. |

Có một câu hỏi thứ ba mà **chưa ai trả lời dứt khoát trên thế giới**, và BDSG
cũng không trả lời được: *trọng số mô hình có phải là tác phẩm phái sinh của
ngữ liệu huấn luyện không?* Nếu có, điều khoản chia-sẻ-tương-tự của CC BY-SA
(Wikipedia) sẽ lây sang trọng số. Toà án chưa phán, giới học thuật chưa thống
nhất. Cách BDSG xử lý: **ghi đầy đủ nguồn nào đã vào mô hình nào, trong model
card**, để nếu sau này phải xử lý thì còn lần ra được.

---

## Tiếng Việt — ngôn ngữ chính

| Nguồn | Nơi lấy | Giấy phép (theo hiểu biết, CHƯA kiểm lại hôm nay) | Tái phân phối |
|---|---|---|---|
| **Wikipedia tiếng Việt** | `dumps.wikimedia.org` (bản dump chính thức) | CC BY-SA (kèm GFDL cho nội dung cũ) | Được, nhưng dính điều kiện chia-sẻ-tương-tự |
| **FineWeb-2** (phần `vie_Latn`) | HuggingFace `HuggingFaceFW/fineweb-2` | ODC-By 1.0 (theo công bố của nhóm phát hành) | Được, phải ghi nguồn |
| **CulturaX** (phần `vi`) | HuggingFace `uonlp/CulturaX` | Kế thừa mC4 (ODC-BY) và OSCAR; **phải bấm chấp nhận điều khoản trên HuggingFace mới tải được** | Không rõ ràng — coi như chỉ huấn luyện |
| **OSCAR** (phần `vi`) | `oscar-project.org` / HuggingFace | Bản thân tập biên soạn thường để CC0, **nội dung bên trong là của Common Crawl** | Chỉ huấn luyện |
| **mC4** (phần `vi`) | HuggingFace `allenai/c4`, cấu hình multilingual | ODC-BY | Được, phải ghi nguồn |
| **CC-100** (phần `vi`) | StatMT / `data.statmt.org` | Theo điều khoản Common Crawl | Chỉ huấn luyện |
| **Wikisource / Wiktionary tiếng Việt** | dumps Wikimedia | CC BY-SA | Được, dính chia-sẻ-tương-tự |

### Nguồn tiếng Việt CẦN TRÁNH hoặc phải rất cẩn thận

| Nguồn | Vì sao |
|---|---|
| **Kho tin tức cào từ báo Việt Nam** (kể cả các bộ nổi tiếng trên GitHub) | Bản quyền toà soạn. Việc ai đó đã đăng lên GitHub **không** biến nó thành tập mở. Đây đúng là lý do nguồn `tin-tuc` bị loại khỏi ngữ liệu BDSG. |
| **Dữ liệu VLSP / các cuộc thi** | Thường phải ký thoả thuận sử dụng, nhiều bộ giới hạn phi thương mại. |
| **Tập UIT-\*** (ViQuAD, VSFC, …) | Nhiều bộ ghi rõ "research only". Đọc kỹ từng bộ. |
| **Ngữ liệu 20GB của PhoBERT (VinAI)** | Bài báo có mô tả, nhưng bộ dữ liệu **không được phát hành công khai** để tải. Đừng ghi nó vào kế hoạch. |
| **OPUS / OpenSubtitles vi-en** | Phụ đề phim — nguồn gốc bản quyền rắc rối. TED2020 trong OPUS là CC BY-NC-ND: **phi thương mại và cấm tác phẩm phái sinh**, tức là không dùng huấn luyện được. |

---

## Tiếng Anh — ngôn ngữ phụ

Tiếng Anh ở đây **không** phải để mô hình giỏi tiếng Anh. Nó có đúng hai việc:
giữ cho tokenizer không quá thiên lệch (phép đo 25/09/2026: bản chỉ học tiếng
Việt làm tiếng Anh **tệ đi 22,0%**), và giữ được thuật ngữ nghiệp vụ tiếng Anh
vốn nằm lẫn trong hồ sơ doanh nghiệp Việt Nam. Vì vậy trọng số mặc định là
**0,20**, và ngân sách nhỏ này nên tiêu vào văn xuôi sạch chứ không phải khối
lượng lớn.

| Nguồn | Nơi lấy | Giấy phép (CHƯA kiểm lại hôm nay) | Tái phân phối |
|---|---|---|---|
| **FineWeb / FineWeb-Edu** | HuggingFace `HuggingFaceFW/fineweb`, `…/fineweb-edu` | ODC-By 1.0 | Được, ghi nguồn |
| **C4** | HuggingFace `allenai/c4` | ODC-BY | Được, ghi nguồn |
| **Wikipedia tiếng Anh** | dumps Wikimedia | CC BY-SA | Được, chia-sẻ-tương-tự |
| **Project Gutenberg** | `gutenberg.org` | Phần lớn thuộc **phạm vi công cộng tại Mỹ** — không tự động công cộng ở nước khác | Kiểm từng đầu sách |
| **StackExchange data dump** | archive.org | CC BY-SA | Được, chia-sẻ-tương-tự |

### Tiếng Anh CẦN TRÁNH

| Nguồn | Vì sao |
|---|---|
| **The Pile (bản gốc)** | Có chứa **Books3**, phần đã bị gỡ vì vi phạm bản quyền sách. Dùng bản gốc là nhận rủi ro pháp lý không cần thiết. Nếu cần, chỉ lấy các thành phần sạch, từng phần một. |
| **Dolma (AI2)** | Không phải giấy phép mở thông thường mà là **AI2 ImpACT License**, có ràng buộc sử dụng. Không phải "không được dùng" — là "phải đọc mới biết được dùng thế nào". |
| **OpenWebText** | Là các trang web lấy theo link Reddit; bản thân bộ sưu tập không mang giấy phép rõ ràng cho nội dung. |

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

Sau khi chạy `lam_sach.py` (lọc rác cào web): **11.699 đoạn · 7.474.485 ký tự ·
7,13 MB** — bỏ 34 đoạn.

Lớp có cấu trúc trong CSDL `postgres`:

- `business.company_profiles`: 6.672 bản ghi tổng · 5.645 đã xuất bản · 6.439 có
  sản phẩm · 5.952 có tỉnh. **5.424** bản ghi đủ **cả ba** điều kiện (đã xuất
  bản ∧ có ngành ∧ có sản phẩm). **5.424 là con số duy nhất được dùng** khi nói
  "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ".
- `business.capabilities`: 11.927 dòng. Cột `description` **chỉ có 58 giá trị
  khác nhau** trên 11.927 dòng — đó là chuỗi xuất xứ ETL lặp lại, **không phát
  hành**. Một cột lặp 58 giá trị trên gần 12 nghìn dòng không phải là văn bản,
  nó là siêu dữ liệu đội lốt văn bản.
- `business.company_sector_links`: 6.666 công ty có ngành.

### Kiểm dữ liệu cá nhân (tự chạy 25/09/2026, không tin lời khai)

- **0 email · 0 số điện thoại · 0 URL nội bộ.**
- Trong văn bản **có nhãn `[EMAIL]` và `[SĐT]`** ⇒ bước gỡ đã chạy thật, chứ
  không phải dữ liệu vốn đã sạch. Đây là hai khẳng định khác nhau và phải phân
  biệt: "không tìm thấy" có thể là bộ dò hỏng.

---

## Tuyệt đối không phát hành, không huấn luyện

Danh sách này là **quyết định đã chốt**, không phải gợi ý. Nó được cưỡng chế
bằng cổng `cong/khong-du-lieu-cam.py`, không chỉ bằng trang tài liệu này.

| Nguồn | Số đo | Vì sao không |
|---|---|---|
| `map5d.khach_dn` | 1.079.991 bản ghi | 100% mang một giá trị nguồn duy nhất là dấu vết ETL từ CRM ⇒ **dữ liệu khách hàng**. Ngoài ra bảng ấy **không có cột ngành nghề, không có cột sản phẩm** — nên kể cả nếu được phép thì nó cũng không chứa thứ người ta tưởng nó chứa. Cấm vì quyền riêng tư, và cấm luôn vì vô dụng cho việc này. |
| `kho-tri-thuc` | 118 tệp | **118/118** mang dòng cấp phép của một pháp nhân khác. Ta không có quyền phát hành lại. |
| `ocop` | 1.727 sản phẩm | Văn quảng cáo người bán. Bản quyền không thuộc dự án. |
| `tin-tuc` | — | Bản quyền toà soạn. |
| `bai-dang` | — | Nội dung người dùng đăng trên nền tảng. |
| `nao-agent` | 116 đoạn | **Máy sinh qua cổng LLM bên thứ ba** ⇒ điều khoản nhà cung cấp thường cấm dùng đầu ra để huấn luyện mô hình cạnh tranh. Thêm nữa, 3.601 não agent là **cấu hình thương mại của BDSG**. |
| `bai-dang-bds` | 5.939 đoạn | Cùng lý do máy sinh như trên. |

Đây chính là lý do con số phát hành được là **11.733 đoạn / 7,16 MB**: 6.055
đoạn máy sinh đã bị loại **trước** khi đếm.

---

## Cách dựng một tệp nguồn thực tế

1. Tải nguồn về `bo-du-lieu/tho/<ten-nguon>/`, kèm ảnh chụp trang giấy phép và
   ngày tải, đặt trong `bo-du-lieu/giay-phep/`.
2. Chuyển sang JSONL một dòng một đoạn, **kèm xuất xứ ngay từ bước này**:
   `{"text": "...", "nguon": "<ten-nguon>"}`.
3. Lọc rác cào web — nhìn trước rồi mới chạy thật:
   ```bash
   python3 lam_sach.py --vao … --chi-do --xem-thu 20    # chỉ đo, không ghi gì
   python3 lam_sach.py --vao … --ra …                   # chạy thật
   ```
4. Trộn hai ngôn ngữ theo trọng số:
   ```bash
   python3 tron.py --dinh-dang pretrain \
       --nguon-viet <ten>=<duong-dan-vi.jsonl> \
       --nguon-anh  <ten>=<duong-dan-en.jsonl> \
       --ti-le-viet 0.80 --ti-le-anh 0.20 \
       --ra ../../bo-du-lieu/pretrain-tron.jsonl
   ```
5. Ghi vào model card: tên nguồn, ngày tải, giấy phép, **số ký tự thực tế đã
   dùng** — lấy từ `*.bao-cao-tron.json` mà `tron.py` sinh ra, chứ không phải từ
   con số dự định lúc lên kế hoạch.

Bước 5 không phải thủ tục. Một bản phát hành mà không nói được mình học từ đâu
thì không ai kiểm được, kể cả chính BDSG sáu tháng sau. Đó cũng là lý do
`tron.py` **từ chối ghi** một bản ghi không xác định được xuất xứ, thay vì ghi
ra rồi để trống trường `nguon`.

## Tình trạng thật tính đến 26/09/2026

**Chưa tải nguồn mở nào về đĩa.** Thư mục `bo-du-lieu/` hiện chỉ có tài liệu và
`xuat.py`; không có tệp `.jsonl` ngữ liệu nào. Nghĩa là:

- chưa có tệp tiếng Anh nào để trộn ⇒ trọng số 0,20 chưa từng được chạy trên
  dữ liệu thật;
- chưa chạy lại phép đo tokenizer với đối chứng tự sinh (xem
  `../tu-vung/ket-qua/do-luong-25-09-2026.md`);
- mọi con số về ngữ liệu BDSG ở trên là **đo từ CSDL**, không phải đo từ tệp
  trên đĩa.

Viết ra đây để không ai đọc bảng giấy phép dài ở trên rồi tưởng dữ liệu đã sẵn
sàng.
