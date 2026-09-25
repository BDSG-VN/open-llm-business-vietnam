# Open LLM Business Việt Nam

[![Giấy phép mã](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE-CODE)
[![Giấy phép dữ liệu](https://img.shields.io/badge/data-CC--BY--4.0-green.svg)](LICENSE-DATA)
![Trọng số](https://img.shields.io/badge/weights-chua--phat--hanh-lightgrey.svg)
![Dây chuyền](https://img.shields.io/badge/pipeline-MiniMind-orange.svg)
![Ngôn ngữ](https://img.shields.io/badge/ngon%20ngu-vi%20%7C%20en%20%7C%20zh-informational.svg)

**Mô hình ngôn ngữ mở cho tri thức doanh nghiệp Việt Nam, huấn luyện bằng dây chuyền
[MiniMind](https://github.com/jingyaogong/minimind), với tiếng Việt là ngôn ngữ chính,
tiếng Anh thứ hai và tiếng Trung thứ ba.**

Kho này phát hành **dữ liệu, mã và bộ đánh giá trước; trọng số sau**. Ở thời điểm viết
(25/09/2026) BDSG **chưa huấn luyện trọng số nào**. Đọc [bảng trạng thái](#bang-trang-thai-thang-than)
trước khi dùng bất cứ thứ gì ở đây.

> **Số đo trong README này là số đo trên CƠ SỞ DỮ LIỆU NGUỒN và trên hệ đang chạy, không
> phải số tệp bạn nhận được khi clone.** Việc kết xuất ngữ liệu ra tệp và nạp bộ câu hỏi
> vào kho thuộc các mốc phía sau, do các nhóm khác của dự án làm trong `bo-du-lieu/`,
> `danh-gia/` và `huan-luyen/`. Muốn biết bản clone của bạn thật sự có gì thì **liệt kê
> các thư mục ấy**, đừng suy từ tài liệu gốc kho: trạng thái thư mục đổi theo giờ, còn
> tài liệu thì không.

---

## Mục lục

- [Bảng trạng thái thẳng thắn](#bang-trang-thai-thang-than)
- [Vì sao phát hành dữ liệu trước, trọng số sau](#vi-sao-phat-hanh-du-lieu-truoc-trong-so-sau)
- [Thứ tự ngôn ngữ: Việt → Anh → Trung](#thu-tu-ngon-ngu-viet--anh--trung)
- [Bộ dữ liệu: số đo ngày 25/09/2026](#bo-du-lieu-so-do-ngay-25092026)
- [Những gì CỐ Ý không có trong bộ này và vì sao](#nhung-gi-co-y-khong-co-trong-bo-nay-va-vi-sao)
- [Đường cơ sở đánh giá M3](#duong-co-so-danh-gia-m3)
- [Lộ trình M1 → M7](#lo-trinh-m1--m7)
- [Kiến trúc dự kiến](#kien-truc-du-kien)
- [Cách chạy cục bộ](#cach-chay-cuc-bo)
- [Cách gọi API llm.bdsg.vn](#cach-goi-api-llmbdsgvn)
- [Cấu trúc kho](#cau-truc-kho)
- [Giấy phép](#giay-phep)
- [Trích dẫn](#trich-dan)

---

<a id="bang-trang-thai-thang-than"></a>

## Bảng trạng thái thẳng thắn

Cột "Đo ngày" ghi ngày con số trong dòng đó được đo thật. Dòng nào không có số đo thì ghi
thẳng là **chưa đo**, không ước lượng.

| Hạng mục | Trạng thái | Số đo | Đo ngày |
|---|---|---|---|
| Ngữ liệu phát hành được | **ĐÃ CÓ** | 11.733 đoạn · 7.509.969 ký tự · 7,16 MB | 25/09/2026 |
| Lớp doanh nghiệp có cấu trúc | **ĐÃ CÓ** | 5.424 doanh nghiệp đủ ba điều kiện | 25/09/2026 |
| Quét dữ liệu cá nhân trên ngữ liệu | **ĐÃ CHẠY** | 0 email · 0 số điện thoại · 0 URL nội bộ | 25/09/2026 |
| Bộ đánh giá đóng băng | **ĐÃ CÓ** | 227 câu, 5 nhóm | 22/09/2026 |
| Đường cơ sở đánh giá | **ĐÃ CÓ** | xem [bảng M3](#duong-co-so-danh-gia-m3) | 22/09/2026 |
| API tương thích OpenAI tại `llm.bdsg.vn` | **ĐÃ SỐNG** | `/` → 200 · `/v1/models` → 200 · `/api/suc-khoe` → 200 | 25/09/2026 |
| **Trọng số do BDSG huấn luyện** | **CHƯA CÓ** | API tự khai `bdsg_la_trong_so_bdsg = false` cho **mọi** mã mô hình | 25/09/2026 |
| Từ vựng (tokenizer) tiếng Việt — bản **thử nghiệm** | **ĐÃ ĐO** | giảm 66,1% token tiếng Việt so với từ vựng MiniMind, cùng cỡ 6.400 | 25/09/2026 |
| Từ vựng (tokenizer) — bản **phát hành** | **CHƯA CÓ** | chưa trộn tiếng Anh và tiếng Trung | chưa đo |
| Bộ dữ liệu tiền huấn luyện đóng gói `.jsonl` | **CHƯA CÓ** | — | chưa đo |
| Ngữ liệu tiếng Trung của BDSG | **CHƯA CÓ** | chưa chọn nguồn, chưa đo dung lượng | chưa đo |
| Chi phí GPU thật đã trả | **CHƯA CÓ** | chưa thuê GPU lần nào | chưa đo |

### Phải nói rõ ba điều

1. **Bản phát hành này chưa có trọng số do BDSG huấn luyện.** Không có tệp `.safetensors`
   nào trong kho, và không có liên kết tải trọng số nào ở phần dưới. Mục nào cần trọng số
   thì trong [MODEL-CARD.md](MODEL-CARD.md) đều ghi "chưa huấn luyện — mục này trống cho tới M7".

2. **Thứ đang chạy tại `llm.bdsg.vn` là TRUY HỒI đặt trước một mô hình của bên thứ ba,
   không phải trọng số của BDSG.** Lớp truy hồi dùng `pg_trgm` + `tsvector` của PostgreSQL —
   tức là **khớp chữ, không phải khớp vector**: cổng LiteLLM của BDSG không có mô hình nhúng
   (embedding) nào, nên không có lựa chọn nào khác. Mã mô hình `/v1/models` trả về là
   `openbiz-vn-chat` và `openbiz-vn-reasoner`; cả hai đều trả
   `bdsg_la_trong_so_bdsg = false` (gọi lại và đọc tận nơi ngày 25/09/2026).

3. **Vì thế kho này KHÔNG được gọi là "mô hình ngôn ngữ của BDSG" cho tới mốc M7.** Cho tới
   lúc đó nó là một bộ dữ liệu mở, một bộ đánh giá đóng băng, và một dây chuyền huấn luyện
   sẽ dùng để tạo ra trọng số ấy.

---

<a id="vi-sao-phat-hanh-du-lieu-truoc-trong-so-sau"></a>

## Vì sao phát hành dữ liệu trước, trọng số sau

Phát hành **ngữ liệu + mã + bộ đánh giá trước, trọng số sau** không phải là cách lách để
gắn chữ "LLM" lên một hệ truy hồi. Đó là trình tự đã có tiền lệ trong chính giới mô hình mở:

| Bộ dữ liệu phát hành trước | Trọng số phát hành sau |
|---|---|
| **Dolma** (Allen Institute for AI) | **OLMo** |
| **The Pile** (EleutherAI) | **GPT-NeoX-20B** |
| **RedPajama-Data** (Together) | **RedPajama-INCITE** |

Điểm chung: ngữ liệu và quy trình lọc được công bố để người ngoài kiểm tra được **trước**
khi có bất kỳ trọng số nào; trọng số ra sau và có thể tái lập từ thứ đã công bố. Đó chính
là điều kho này đang làm.

Ranh giới cần giữ, và kho này giữ nó ở [bảng trạng thái](#bang-trang-thai-thang-than):
một hệ truy hồi **không** trở thành mô hình ngôn ngữ vì được đặt sau một tên miền tên là
`llm.bdsg.vn`. Tên miền là tên miền. Trọng số là trọng số. Khi nào BDSG có trọng số, bảng
trạng thái sẽ đổi và trường `bdsg_la_trong_so_bdsg` sẽ trả `true` — không sớm hơn.

---

<a id="thu-tu-ngon-ngu-viet--anh--trung"></a>

## Thứ tự ngôn ngữ: Việt → Anh → Trung

Đây là quyết định của chủ dự án, không phải mặc định kỹ thuật kế thừa từ thượng nguồn.

| Thứ tự | Ngôn ngữ | Nguồn ngữ liệu | Dung lượng đã đo |
|---|---|---|---|
| 1 | **Tiếng Việt** | toàn bộ ngữ liệu doanh nghiệp trong kho này | 7.509.969 ký tự (25/09/2026) |
| 2 | **Tiếng Anh** | cột `name_en` trong `business.capabilities`, tóm tắt song ngữ | **chưa tách đo riêng** — 346.704 ký tự là tổng của `name` + `name_en` |
| 3 | **Tiếng Trung** | **chưa chọn nguồn** | **chưa đo** |

Ba điều phải nói rõ về thứ tự này:

- **MiniMind gốc là tiếng Trung + tiếng Anh.** `requirements.txt` của họ có `jieba` —
  thư viện tách từ tiếng Trung. Ngữ liệu tiền huấn luyện và SFT mà họ phát hành
  (`pretrain_t2t` ~10 GB, `sft_t2t` ~14 GB) là ngữ liệu Trung–Anh. Nếu BDSG dùng
  nguyên dây chuyền ấy mà không đổi gì, thứ tự ngôn ngữ sẽ là Trung → Anh → Việt,
  tức là ngược với quyết định của dự án.
- **Vì thế BDSG bắt buộc phải huấn luyện từ vựng (tokenizer) riêng.** Xem mục kế tiếp.
- **Tiếng Trung vẫn ở lại, nhưng ở vị trí thứ ba.** Tiếng Trung không bị loại: nó là ngôn
  ngữ thứ ba trong thứ tự ưu tiên. Nhưng tại 25/09/2026 BDSG **chưa chọn được nguồn ngữ
  liệu tiếng Trung có giấy phép cho phép tái phát hành**, nên phần tiếng Trung hiện **chưa
  có số đo nào**. Không hứa dung lượng, không hứa chất lượng, không hứa mốc.

### Vì sao phải huấn luyện lại tokenizer, dù chính MiniMind khuyên đừng

Ngay dòng đầu tệp `trainer/train_tokenizer.py` của MiniMind có cảnh báo: **không khuyến nghị
huấn luyện lại tokenizer**, vì mô hình huấn luyện trên từ điển khác sẽ cho đầu ra không
thống nhất và làm giảm khả năng dùng lại trong cộng đồng.

Cảnh báo ấy đúng — **cho người dùng lại trọng số đã phát hành của MiniMind**. Đổi từ điển
mà giữ trọng số cũ thì trọng số trở thành vô nghĩa.

BDSG **huấn luyện từ đầu**, không nạp trọng số MiniMind nào. Trong tình huống đó cảnh báo
không áp dụng, và điều ngược lại mới đúng: từ vựng 6.400 token của MiniMind được dựng trên
ngữ liệu Trung–Anh, nên chữ tiếng Việt có dấu sẽ bị băm thành nhiều byte-token hơn mức cần
thiết, làm phí cả độ dài ngữ cảnh lẫn thời gian GPU. Muốn tiếng Việt đứng thứ nhất thì từ
vựng phải được dựng trên ngữ liệu tiếng Việt.

**Hệ quả phải chấp nhận và nói trước:** trọng số của kho này sẽ **không** tương thích với
tokenizer của MiniMind, và ngược lại. Đây là cái giá của quyết định đặt tiếng Việt lên đầu.

### Phép đo chứng minh điều đó, và phép đo chứng minh vì sao tiếng Trung vẫn phải ở lại

Nhóm từ vựng đã chạy thử và đo ngày **25/09/2026**, giữ nguyên cỡ từ vựng **6.400 — đúng
bằng MiniMind**, để so sánh công bằng (tăng cỡ từ vựng rồi khoe số token giảm là so sánh
gian: từ vựng lớn hơn luôn nén tốt hơn). Đo trên phần giữ lại chưa từng thấy lúc huấn
luyện: 1.199 đoạn · 1.037.113 ký tự.

| Từ vựng | Token (tiếng Việt) | ký tự/token | Token (tiếng Anh) | ký tự/token |
|---|---:|---:|---:|---:|
| MiniMind gốc (Trung–Anh) | 852.285 | 1,22 | 2.001 | 3,18 |
| BDSG, học trên tiếng Việt | **289.266** | **3,59** | 2.441 | 2,61 |

- Tiếng Việt: **giảm 66,1% số token**, tức chứa được gấp **2,95 lần** chữ trên cùng ngân
  sách ngữ cảnh. Đây là bằng chứng cho lập luận ở trên, không phải lời khẳng định suông.
- Tiếng Anh: **tệ đi 22,0%**. Con số này phải công bố cùng, không được giấu.

Chính con số −22,0% ấy là lý do **tiếng Trung ở lại chứ không bị cắt**. Một bản thử nghiệm
chỉ học tiếng Việt đã làm hỏng tiếng Anh; nên bản phát hành phải **trộn ba thứ tiếng theo
trọng số** (Việt nhiều nhất, rồi Anh, rồi Trung) chứ không phải đổi hẳn sang tiếng Việt.
Thứ tự Việt → Anh → Trung là thứ tự **trọng số trong hỗn hợp**, không phải danh sách ngôn
ngữ được phép có mặt.

Lưu ý về số: nhóm từ vựng làm việc trên **11.699 đoạn sau lọc**, chênh 34 đoạn so với
11.733 đoạn thô ghi ở bảng dữ liệu bên dưới. Chênh lệch là do bước lọc đã chạy ở phía họ.
Ghi lại ở đây để không ai tưởng hai con số là một.

Ba điều phép đo này **chưa** chứng minh, theo đúng ghi nhận của nhóm từ vựng: nó chưa phải
tokenizer phát hành; nó chưa trộn tiếng Anh và tiếng Trung; và **nén tốt hơn không đồng
nghĩa trả lời tốt hơn** — chất lượng trả lời phải đo bằng bộ đánh giá ở `danh-gia/`.

---

<a id="bo-du-lieu-so-do-ngay-25092026"></a>

## Bộ dữ liệu: số đo ngày 25/09/2026

Mọi con số dưới đây được đo trực tiếp trên cơ sở dữ liệu ngày 25/09/2026. Không con số nào
là ước lượng.

### Lớp văn bản (CSDL `bdsg_chat`, bảng `doan_tri_thuc`)

Sau khi loại hai nguồn máy sinh (xem [mục loại trừ](#nhung-gi-co-y-khong-co-trong-bo-nay-va-vi-sao)):

| Nguồn | Số đoạn | Dung lượng |
|---|---:|---:|
| `ho-so-niem-yet` | 5.192 | 4,20 MB |
| `ho-so-dn` | 6.434 | 2,83 MB |
| `wiki-crm` | 107 | 0,13 MB |
| **Tổng phát hành được** | **11.733** | **7,16 MB** (7.509.969 ký tự) |

Chia tập (tính trên toàn bộ 17.788 đoạn của bảng gốc, trước khi loại nguồn máy sinh):
**huấn luyện 16.151 · kiểm tra 835 · thẩm định 802**.

### Lớp có cấu trúc (CSDL `postgres`)

| Bảng | Số đo |
|---|---|
| `business.company_profiles` | 6.672 tổng · 5.645 đã xuất bản · 6.439 có sản phẩm · 5.952 có mã tỉnh · 6.608 có tóm tắt |
| Ký tự (trên 5.645 đã xuất bản) | tóm tắt 1.941.353 + sản phẩm 322.477 |
| `business.company_sector_links` | 6.666 công ty có ngành |
| `business.capabilities` | 11.927 dòng · 346.704 ký tự tên (`name` + `name_en`) |

**Con số được phép dùng cho câu "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ" là
5.424** — số doanh nghiệp đủ **cả ba** điều kiện (đã xuất bản ∧ có ngành ∧ có sản phẩm).
Không được dùng 6.672, không được dùng 6.439: đó là các con số đếm theo **một** điều kiện.

### Kiểm tra dữ liệu cá nhân (tự chạy, không tin lời khai)

| Phép quét | Kết quả |
|---|---|
| Email | **0** |
| Số điện thoại | **0** |
| URL nội bộ | **0** |
| "mã số thuế" | 29 khớp — phần lớn là mã số thuế / số ĐKKD doanh nghiệp (**thông tin đăng ký công khai** ở Việt Nam), lẫn vài dương tính giả (tên lớp CSS, trường `rev` trong JSON) |
| "địa chỉ IP" | 5 khớp — **tất cả là dương tính giả**: số tiền viết kiểu Việt Nam, ví dụ `120.086.720.000 đồng` |

Trong văn bản còn nhãn `[EMAIL]` và `[SĐT]`. Đây là bằng chứng bước gỡ dữ liệu cá nhân
**đã chạy thật**, chứ không phải bước được khai là đã chạy.

### Rác cào web còn sót

**110 đoạn** còn dính rác cào web (menu web, CSS, JS, URL ngoài) — **0,17 MB trên 7,16 MB
= 2,3%**. Rác tập trung ở `ho-so-niem-yet`: 110/5.192 = 2,1% số đoạn của nguồn đó.

Đây là mức **lọc được**, không phải mức phải bỏ nguồn. Con số 110 đoạn là số đo trên bản
thô; bộ lọc của bản phát hành thuộc mốc M4 và trạng thái của nó do nhóm bộ dữ liệu ghi
trong `bo-du-lieu/`.

---

<a id="nhung-gi-co-y-khong-co-trong-bo-nay-va-vi-sao"></a>

## Những gì CỐ Ý không có trong bộ này và vì sao

Một bản phát hành nghiêm túc được đánh giá bằng chỗ nó nói **không**. Dưới đây là từng
nguồn đã bị loại, kèm lý do đo được, chứ không phải lý do cảm tính.

| Nguồn bị loại | Quy mô | Vì sao loại |
|---|---|---|
| `map5d.khach_dn` | 1.079.991 bản ghi | **100% có `nguon = 'crm_geocode_dot2'` ⇒ đây là dữ liệu khách hàng lấy từ CRM.** Ngoài ra bảng chỉ có các cột `id`, `ten`, `do_chinh_xac`, `ma_xa`, `ma_tinh`, `geom`, `nguon`, `ngay_cap_nhat`: **không có cột ngành nghề, không có cột sản phẩm**. Nó không những không được phát hành, nó còn không chứa thứ mà người ta tưởng nó chứa. |
| `kho-tri-thuc` | 118 tệp | **118/118 tệp mang dòng cấp phép bên thứ ba** ("Licensed to RAI Holdings"). Tỷ lệ là 118/118, không phải "phần lớn". |
| `ocop` | 1.727 sản phẩm | Văn quảng cáo do người bán viết; `url` trỏ về `buudien.vn`. Không phải văn bản tri thức, và không phải của BDSG. |
| `tin-tuc` | — | Bản quyền thuộc các toà soạn. |
| `bai-dang` | — | Nội dung do người dùng đăng trên nền tảng; BDSG không có quyền tái phát hành thay họ. |
| `nao-agent` | 116 đoạn | **Máy sinh qua cổng LiteLLM** ⇒ là đầu ra của mô hình bên thứ ba; điều khoản nhà cung cấp thường cấm dùng đầu ra để huấn luyện mô hình cạnh tranh. Thêm nữa, 3.601 "não agent" là **cấu hình thương mại của BDSG**. |
| `bai-dang-bds` | 5.939 đoạn | **Máy sinh qua cổng LiteLLM** — cùng lý do trên. |
| `business.capabilities.description` | 696.890 ký tự | Trông như 696.890 ký tự mô tả, thực tế **chỉ có 58 giá trị khác nhau trên 11.927 dòng** ⇒ là chuỗi xuất xứ do ETL lặp lại, không phải mô tả. Phát hành nó là làm phồng số liệu bằng văn bản trùng lặp. Cột `name` + `name_en` (346.704 ký tự) thì giữ. |

Hai nguồn máy sinh cộng lại là **6.055 đoạn** (116 + 5.939). Đó là khoảng cách giữa 17.788
đoạn trong bảng gốc và 11.733 đoạn phát hành được.

---

<a id="duong-co-so-danh-gia-m3"></a>

## Đường cơ sở đánh giá M3

Bộ 227 câu, **đóng băng** ngày 22/09/2026. "Đóng băng" nghĩa là bộ câu hỏi không được sửa
sau khi đã đo, để lần đo sau còn so được với lần đo này.

| Nhóm | Số câu | Điểm |
|---|---:|---:|
| Nghiệp vụ **trong** kho tri thức | 111 | **0,636** |
| Nghiệp vụ **ngoài** kho tri thức | 31 | **0,539** |
| Câu bẫy chống bịa | 60 | **0,953** |
| Tiếng Việt tổng quát | 25 | **0,908** |
| **Lợi ích của truy hồi** (trong kho − ngoài kho) | — | **+0,097** |

Cách đọc đúng bảng này:

- **+0,097 là toàn bộ giá trị mà lớp truy hồi mang lại**, đo trên hệ hiện tại. Không phải
  một con số lớn. Nói thẳng ra như vậy tốt hơn là trưng 0,636 rồi để người đọc tự tưởng
  đó là công của BDSG.
- **0,636 và 0,539 là điểm của một mô hình bên thứ ba**, có/không có truy hồi của BDSG
  đứng trước. Không phải điểm của trọng số BDSG — chưa có trọng số nào để đo.
- **0,953 ở câu bẫy chống bịa** là điểm cao, và nó cũng là điểm dễ gây hiểu nhầm nhất:
  đường cơ sở cao nghĩa là khoảng cải thiện còn lại rất hẹp, chứ không nghĩa là hệ đã an toàn.

Chỗ dành cho bộ câu hỏi và mã chấm là thư mục `danh-gia/` (mốc M3 của kho này). **Cảnh báo
cho người clone:** năm con số ở bảng trên là kết quả đo trên hệ đang chạy, **không** phải
thứ bạn nhận được cùng bản clone — lúc 22:00 ngày 25/09/2026 thư mục `danh-gia/` còn **rỗng**.
Hãy mở thư mục đó trong bản bạn tải về để biết trạng thái thật tại thời điểm của bạn, đừng
suy từ dòng này.

---

<a id="lo-trinh-m1--m7"></a>

## Lộ trình M1 → M7

Đánh số M1…M7 là đánh số **của kho này**.

| Mốc | Nội dung | Trạng thái |
|---|---|---|
| **M1** | Xác định và đo ngữ liệu phát hành được; quét dữ liệu cá nhân; chốt danh sách nguồn bị loại | **XONG** — đo 25/09/2026 |
| **M2** | Huấn luyện từ vựng (tokenizer) byte-level BPE trên ngữ liệu tiếng Việt | **ĐANG LÀM** — bản thử nghiệm đã đo 25/09/2026 (−66,1% token tiếng Việt, −22,0% tiếng Anh); bản phát hành còn phải trộn Anh và Trung |
| **M3** | Bộ đánh giá 227 câu đóng băng + đường cơ sở | **XONG** — đo 22/09/2026 |
| **M4** | Lọc 110 đoạn rác cào web; đóng gói `.jsonl` tiền huấn luyện + SFT | **ĐANG LÀM ở thư mục khác** — mã nằm trong `bo-du-lieu/` và `huan-luyen/du-lieu/`; trạng thái do nhóm ấy ghi tại đó |
| **M5** | Chạy thử toàn dây chuyền ở quy mô nhỏ để chứng minh nó chạy hết được | **chưa thấy bằng chứng đã chạy** tại 25/09/2026 |
| **M6** | Sổ mô hình + cổng nghiệm thu: không có bản nào được gọi là phát hành nếu chưa qua bộ 227 câu | **ĐANG LÀM ở thư mục khác** — cổng nằm trong `cong/`; đọc trạng thái tại đó |
| **M7** | **Huấn luyện trọng số gốc trên GPU thuê** — mốc duy nhất làm bảng trạng thái đổi | **CHƯA LÀM** — chưa thuê GPU lần nào (25/09/2026) |

Vì sao ba dòng giữa không ghi "XONG" hay "CHƯA LÀM" dứt khoát: tài liệu ở gốc kho **không
được khẳng định trạng thái thư mục của nhóm khác**. Bản đầu của README này từng viết mấy
thư mục ấy còn rỗng, và câu đó sai sau chín phút. Trạng thái đúng chỉ có ở tệp trong chính
thư mục đó.

Về M7, những gì biết được từ số liệu MiniMind công bố (đây là số của **họ**, đo trên phần
cứng và ngữ liệu của **họ**, không phải số của BDSG):

- 1 GPU RTX 3090, khoảng **2,31 giờ** cho 1 epoch, chi phí khoảng **3 nhân dân tệ**
  (giá thuê 3090 họ ghi khoảng 1,3 ¥/giờ). Con số ấy là cho bản `minimind-3` cỡ 64M chạy
  trên **bộ dữ liệu rút gọn** `pretrain_t2t_mini` + `sft_t2t_mini`, không phải cho bộ đầy
  đủ — ghi rõ ra vì trích "2,31 giờ" trần trụi sẽ thành lời hứa rẻ hơn thực tế.
- Trên cụm 8× H100, thời gian rút xuống cỡ phút.
- Chi phí GPU thật của BDSG: **chưa đo** — chưa thuê lần nào.

---

<a id="kien-truc-du-kien"></a>

## Kiến trúc dự kiến

Đọc trực tiếp từ mã MiniMind (`model/model_minimind.py`, nhánh `f659b55`, 23/09/2026),
không phải chép từ tài liệu:

```python
# MiniMindConfig — giá trị mặc định
hidden_size              = 768
num_hidden_layers        = 8
num_attention_heads      = 8
num_key_value_heads      = 4      # GQA: 8 đầu truy vấn dùng chung 4 đầu khoá/giá trị
vocab_size               = 6400
hidden_act               = 'silu'
max_position_embeddings  = 32768
rope_theta               = 1e6
tie_word_embeddings      = True   # dùng chung trọng số nhúng và lớp đầu ra
use_moe                  = False
intermediate_size        = ceil(hidden_size * pi / 64) * 64   # = 2432 khi hidden_size=768
```

Từ vựng (`trainer/train_tokenizer.py`): byte-level BPE, `VOCAB_SIZE = 6400`,
`SPECIAL_TOKENS_NUM = 36`, `pre_tokenizer = ByteLevel(add_prefix_space=False)`,
dùng thư viện `tokenizers` của Hugging Face.

Cỡ mô hình trong họ MiniMind: từ **26M** (`minimind2-small`) tới **198M-A64M**
(`minimind-3-moe`). BDSG **chưa chốt cỡ** sẽ huấn luyện — đó là quyết định của M7, và
quyết định ấy phụ thuộc vào 7,16 MB ngữ liệu hiện có, một con số nhỏ so với ngữ liệu
tiền huấn luyện của MiniMind (~10 GB).

Các tệp của dây chuyền sẽ dùng (đã mở từng tệp để kiểm là có thật trong bản MiniMind
thượng nguồn ở nhánh `f659b55`, không phải chép từ tài liệu của họ):

```
trainer/train_tokenizer.py      trainer/train_pretrain.py     trainer/train_full_sft.py
trainer/train_dpo.py            trainer/train_lora.py         trainer/train_ppo.py
trainer/train_grpo.py           trainer/train_distillation.py trainer/train_agent.py
model/model_minimind.py         model/model_lora.py           dataset/lm_dataset.py
scripts/serve_openai_api.py     scripts/convert_model.py      scripts/web_demo.py
eval_llm.py
```

---

<a id="cach-chay-cuc-bo"></a>

## Cách chạy cục bộ

### Chạy được ngay hôm nay

```bash
# Kho công khai: github.com/BDSG-VN/open-llm-business-vietnam
# Chỗ này còn là chỗ trống vì tên tổ chức chưa được chốt tại 25/09/2026.
git clone https://github.com/BDSG-VN/open-llm-business-vietnam.git
cd open-llm-business-vietnam

python3 -m venv .venv
source .venv/bin/activate
```

**Chưa có `requirements.txt`.** Đừng gõ `pip install -r requirements.txt`: tệp ấy thuộc mốc
M4 và chưa tồn tại trong kho, lệnh sẽ báo lỗi. Bước cài phụ thuộc chỉ có nghĩa khi đã có
tệp đó; chừng nào chưa có thì mỗi script tự khai thư viện nó cần ở đầu tệp.

Các thư mục `huan-luyen/`, `bo-du-lieu/`, `danh-gia/`, `cong/`, `tai-lieu/` được các nhóm
của dự án đổ nội dung vào theo từng mốc M2–M6, và chúng có README hoặc ghi chú đo lường
riêng — đọc tệp trong chính thư mục đó, đừng suy từ README này. Bản phát hành đầu tiên ở
gốc kho là **mặt tiền**: README, thẻ mô hình, giấy phép và quy tắc đóng góp.

### Chưa chạy được, và vì sao

```bash
# CHƯA CHẠY ĐƯỢC: không có trọng số nào để tải.
python scripts/serve_openai_api.py --load_from ./trong-so/...
```

Không có trọng số ⇒ không có lệnh chạy cục bộ nào cho ra chữ. Mục tiêu của dự án là người
dùng tải mô hình về **máy cá nhân** chạy được, và cỡ mô hình MiniMind (26M–198M) khiến mục
tiêu ấy khả thi trên CPU — nhưng đó là mục tiêu ở M7, không phải trạng thái hôm nay.

---

<a id="cach-goi-api-llmbdsgvn"></a>

## Cách gọi API llm.bdsg.vn

`llm.bdsg.vn` **đã sống** (đo 25/09/2026). Chứng chỉ Let's Encrypt cấp lúc **21:27 ngày
25/09/2026**; hai lần xin đầu hỏng với 520/522 vì Cloudflare còn đang khởi tạo tên miền mới,
lần thứ ba đạt. Tên miền cũ `ai.bdsg.vn` đã **NXDOMAIN** — bản ghi DNS bị gỡ cùng ngày.

API tương thích OpenAI:

```bash
# Kiểm tra sức khoẻ — đo 25/09/2026: trả 200, không cần khoá
curl -s https://llm.bdsg.vn/api/suc-khoe

# Liệt kê mã mô hình — đo 25/09/2026: trả 200 ngay cả KHI KHÔNG gửi khoá
curl -s https://llm.bdsg.vn/v1/models

# Hỏi đáp — đường này CÓ cần khoá; chưa tự thử được vì chưa có khoá trong tay
curl -s https://llm.bdsg.vn/v1/chat/completions \
  -H "Authorization: Bearer $KHOA_BDSG" \
  -H "Content-Type: application/json" \
  -d '{
        "model": "openbiz-vn-chat",
        "messages": [{"role": "user", "content": "BDSG có bao nhiêu hồ sơ doanh nghiệp đã xuất bản?"}]
      }'
```

Mã mô hình để điền vào trường `model`, đọc thẳng từ `/v1/models` ngày 25/09/2026:
**`openbiz-vn-chat`** và **`openbiz-vn-reasoner`**.

`bdsg-ai-v1` và `bdsg-ai-v1-suy-luan` là **tên cũ trước ngày 25/09/2026**. Chúng vẫn được
chấp nhận ở trường `model` như **bí danh vĩnh viễn** — không có ngày hết hạn — nên mã tích
hợp cũ không hỏng. Nhưng `/v1/models` chỉ liệt kê hai tên mới, và tài liệu này chỉ dùng tên
mới; hãy dùng tên mới cho mọi tích hợp mới.

Một chỗ dễ nhầm: `bdsg-ai-v1` **cũng** là khoá trong **sổ mô hình nội bộ**, xuất hiện ở
`/api/suc-khoe` tại `dangPhucVu[].ma` để chỉ *bản* nào đang phục vụ. Khoá sổ giữ nguyên tên
cũ có chủ ý — bảng `lan_danh_gia` tham chiếu tới nó, nên viết lại khoá ấy là cắt đứt lịch sử
đánh giá khỏi chính mô hình đã được đánh giá. Tên công khai và tên sổ sách được phép khác
nhau; ánh xạ giữa hai tên nằm ở đúng một chỗ trong mã.

Bốn điều phải biết trước khi gọi:

1. **Cả hai mã mô hình đều trả `bdsg_la_trong_so_bdsg = false`** — đọc trực tiếp trong
   `/v1/models` ngày 25/09/2026. Đằng sau là mô hình của bên thứ ba, có lớp truy hồi của
   BDSG đứng trước.
2. **Lớp truy hồi khớp chữ, không khớp nghĩa** (`pg_trgm` + `tsvector`). Câu hỏi diễn đạt
   khác hẳn từ ngữ trong tài liệu sẽ không truy hồi được.
3. **`/api/suc-khoe` và `/v1/models` trả 200 mà không cần khoá** (đo 25/09/2026). Đừng suy
   ra rằng cả API là công khai: `/v1/chat/completions` cần khoá, và điều đó **chưa được đo
   ở đây** vì người soát không có khoá để thử.
4. **Khoá do BDSG cấp.** Tại 25/09/2026 **chưa có cổng tự đăng ký khoá công khai**.

---

<a id="cau-truc-kho"></a>

## Cấu trúc kho

```
open-llm-business-vietnam/
├── README.md              ← tệp này
├── MODEL-CARD.md          ← thẻ mô hình; phần lớn mục còn trống cho tới M7
├── LICENSE-CODE           ← Apache License 2.0 (toàn văn), cho MÃ
├── LICENSE-DATA           ← CC BY 4.0, chỉ cho bo-du-lieu/
├── CONTRIBUTING.md
├── .gitignore
├── huan-luyen/
│   ├── tu-vung/           ← M2: huấn luyện tokenizer
│   ├── du-lieu/           ← M4: dựng .jsonl tiền huấn luyện + SFT
│   └── cau-hinh/          ← M5/M7: cấu hình chạy
├── bo-du-lieu/            ← ngữ liệu phát hành (CC BY 4.0)
├── danh-gia/              ← M3: bộ 227 câu + mã chấm
├── cong/                  ← cổng nghiệm thu (M6)
└── tai-lieu/
```

Các thư mục ngoài gốc kho có tài liệu riêng và trạng thái riêng theo mốc M2–M6. README này
chỉ chịu trách nhiệm về các tệp **ở gốc**; đừng suy trạng thái của một thư mục từ tài liệu
này mà hãy đọc tệp trong chính thư mục đó.

---

<a id="giay-phep"></a>

## Giấy phép

| Phạm vi | Giấy phép | Tệp |
|---|---|---|
| **Mã nguồn** | Apache License 2.0 | [LICENSE-CODE](LICENSE-CODE) |
| **Dữ liệu trong `bo-du-lieu/`** | CC BY 4.0 | [LICENSE-DATA](LICENSE-DATA) |

Mã dùng Apache-2.0 để **khớp với giấy phép của MiniMind** (thượng nguồn cũng là Apache-2.0),
nhờ đó phần dẫn xuất từ dây chuyền của họ không vướng xung đột giấy phép.

Giấy phép của kho này **không** áp cho các nguồn đã bị loại ở
[mục loại trừ](#nhung-gi-co-y-khong-co-trong-bo-nay-va-vi-sao) — chúng không nằm trong kho,
nên không có gì để cấp phép.

---

<a id="trich-dan"></a>

## Trích dẫn

```bibtex
@misc{openllmbusinessvietnam2026,
  title        = {Open LLM Business Việt Nam: bộ dữ liệu và bộ đánh giá mở
                  cho tri thức doanh nghiệp Việt Nam},
  author       = {BDSG},
  year         = {2026},
  note         = {Chưa có trọng số; phát hành dữ liệu, mã và bộ đánh giá trước.
                  Dây chuyền huấn luyện dựa trên MiniMind (Apache-2.0).},
  howpublished = {\url{https://llm.bdsg.vn}}
}
```

Khi trích dẫn, xin trích cả dòng `note`. Bỏ dòng đó đi thì trích dẫn thành lời khẳng định
rằng đã có trọng số — điều không đúng tại 25/09/2026.

Thượng nguồn: [MiniMind](https://github.com/jingyaogong/minimind) của Jingyao Gong, Apache-2.0.

---

*Cập nhật lần cuối: 25/09/2026. Mọi số trong tài liệu này đều kèm ngày đo. Số nào chưa đo
được ghi thẳng là chưa đo.*
