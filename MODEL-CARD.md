# Thẻ mô hình — Open LLM Business Việt Nam

Viết theo khuôn thẻ mô hình (model card) của Hugging Face.

> ## Cảnh báo đặt ở đầu, không giấu xuống cuối
>
> **Tại 25/09/2026, BDSG chưa huấn luyện trọng số nào.** Không có tệp trọng số nào để tải,
> không có liên kết tải nào trong tài liệu này.
>
> Thứ đang chạy tại `llm.bdsg.vn` là **lớp truy hồi của BDSG đặt trước một mô hình của bên
> thứ ba**. API tự khai trường `bdsg_la_trong_so_bdsg = false` cho **mọi** mã mô hình.
>
> Mọi mục dưới đây cần trọng số để trả lời đều ghi **"chưa huấn luyện — mục này trống cho
> tới M7"**. Không mục nào được điền bằng số ước lượng, số của mô hình khác, hay số của
> thượng nguồn.

---

## 1. Chi tiết mô hình

### 1.1 Mô tả

| Trường | Giá trị |
|---|---|
| Tên | Open LLM Business Việt Nam |
| Đơn vị phát triển | BDSG |
| Loại mô hình | mô hình ngôn ngữ nhân quả (decoder-only), kiến trúc MiniMind |
| Ngôn ngữ | **1. Tiếng Việt · 2. Tiếng Anh · 3. Tiếng Trung** |
| Giấy phép mã | Apache License 2.0 — xem [LICENSE-CODE](LICENSE-CODE) |
| Giấy phép dữ liệu | CC BY 4.0, chỉ cho `bo-du-lieu/` — xem [LICENSE-DATA](LICENSE-DATA) |
| Mô hình gốc được tinh chỉnh từ | **không có** — dự kiến huấn luyện từ đầu, không nạp trọng số MiniMind |
| Trọng số phát hành | **chưa có** (25/09/2026) |
| Kho mã | thư mục này |
| Điểm cuối API đang sống | `https://llm.bdsg.vn` — **không phục vụ trọng số của BDSG** |

### 1.2 Kiến trúc dự kiến

Đọc trực tiếp từ `model/model_minimind.py` của MiniMind (nhánh `f659b55`, 23/09/2026):

| Tham số | Giá trị mặc định |
|---|---|
| `hidden_size` | 768 |
| `num_hidden_layers` | 8 |
| `num_attention_heads` | 8 |
| `num_key_value_heads` | 4 (GQA) |
| `vocab_size` | 6400 |
| `hidden_act` | `silu` |
| `max_position_embeddings` | 32768 |
| `rope_theta` | 1e6 |
| `tie_word_embeddings` | `True` |
| `use_moe` | `False` |
| `intermediate_size` | `ceil(hidden_size * pi / 64) * 64` = 2432 khi `hidden_size = 768` |

Dải cỡ trong họ MiniMind: **26M** (`minimind2-small`) đến **198M-A64M** (`minimind-3-moe`).

**Cỡ mà BDSG sẽ huấn luyện: chưa chốt.** Đây là quyết định của M7 và phụ thuộc vào lượng
ngữ liệu thật đang có (7,16 MB), một con số nhỏ so với ngữ liệu tiền huấn luyện của
MiniMind (~10 GB). Không ghi con số nào ở đây cho tới khi chốt.

### 1.3 Từ vựng (tokenizer)

Byte-level BPE, `SPECIAL_TOKENS_NUM = 36`, `pre_tokenizer = ByteLevel(add_prefix_space=False)`,
thư viện `tokenizers` (Hugging Face).

**Trạng thái: bản THỬ NGHIỆM đã huấn luyện và đã đo (25/09/2026); bản PHÁT HÀNH chưa có.**

Bản thử nghiệm giữ nguyên cỡ từ vựng **6.400 — đúng bằng MiniMind**, để so sánh công bằng.
Đo trên phần giữ lại chưa từng thấy lúc huấn luyện (1.199 đoạn · 1.037.113 ký tự):

| Từ vựng | Token (tiếng Việt) | ký tự/token | Token (tiếng Anh) | ký tự/token |
|---|---:|---:|---:|---:|
| MiniMind gốc (Trung–Anh) | 852.285 | 1,22 | 2.001 | 3,18 |
| BDSG, học trên tiếng Việt | 289.266 | 3,59 | 2.441 | 2,61 |

Tiếng Việt **giảm 66,1% số token** (gấp 2,95 lần chữ trên cùng ngân sách ngữ cảnh); tiếng
Anh **tệ đi 22,0%**. Con số thứ hai là lý do bản phát hành phải **trộn ba thứ tiếng theo
trọng số** chứ không phải đổi hẳn sang tiếng Việt.

**Cỡ từ vựng của bản phát hành: chưa chốt.** Cấu hình trong `huan-luyen/cau-hinh/` do nhóm
cấu hình giữ — đọc tại đó, đừng suy từ thẻ này.

**Vì sao vẫn huấn luyện lại dù MiniMind khuyên đừng.** Dòng đầu tệp
`trainer/train_tokenizer.py` của MiniMind ghi rõ là không khuyến nghị huấn luyện lại
tokenizer. Cảnh báo ấy nhắm vào người **dùng lại trọng số đã phát hành của MiniMind**:
đổi từ điển mà giữ trọng số cũ thì trọng số mất nghĩa. BDSG huấn luyện **từ đầu**, không
nạp trọng số nào của họ, nên tình huống ấy không xảy ra — và ngược lại, từ vựng 6.400 token
dựng trên ngữ liệu Trung–Anh sẽ băm chữ tiếng Việt có dấu thành nhiều byte-token hơn mức
cần, phí cả ngữ cảnh lẫn thời gian GPU.

**Hệ quả phải chấp nhận:** trọng số của dự án này sẽ **không tương thích** với tokenizer
của MiniMind, và ngược lại.

---

## 2. Công dụng dự kiến

### 2.1 Dùng trực tiếp

**Chưa huấn luyện — mục này trống cho tới M7.** Không có trọng số thì không có công dụng
trực tiếp nào để mô tả.

Mục tiêu của dự án (là mục tiêu, không phải trạng thái): mô hình đủ nhỏ để **người dùng
tải về máy cá nhân chạy được**, kể cả khi không có GPU rời.

### 2.2 Dùng làm nền cho việc khác

**Chưa huấn luyện — mục này trống cho tới M7.**

### 2.3 Thứ dùng được ngay hôm nay

Không phải trọng số, nhưng có thật — **có thật trong cơ sở dữ liệu nguồn**, đo ngày
25/09/2026:

| Tài nguyên | Dùng để làm gì |
|---|---|
| Ngữ liệu doanh nghiệp Việt Nam (11.733 đoạn · 7.509.969 ký tự · 7,16 MB) | huấn luyện hoặc đánh giá mô hình khác |
| Lớp có cấu trúc: 5.424 doanh nghiệp đủ ngành + tỉnh + sản phẩm | dựng bộ hỏi–đáp có đáp án kiểm chứng được |
| Bộ đánh giá 227 câu đóng băng (22/09/2026) | đo mô hình tiếng Việt lĩnh vực doanh nghiệp |

> **Phải đọc kèm bảng trên, nếu không nó thành lời hứa.** "Có thật" ở đây nghĩa là *đã đo
> được ở nguồn*, **chưa** nghĩa là *đã nằm sẵn trong bản clone của bạn*. Việc kết xuất ba
> tài nguyên ấy thành tệp thuộc các mốc sau và do nhóm khác làm trong `bo-du-lieu/`,
> `danh-gia/`, `huan-luyen/`. Lúc 22:00 ngày 25/09/2026, `danh-gia/` còn rỗng và
> `bo-du-lieu/` mới có tài liệu cùng script kết xuất, chưa có tệp ngữ liệu. Trạng thái ấy
> đổi theo giờ — hãy liệt kê chính các thư mục đó thay vì tin dòng này.

---

## 3. Ngoài phạm vi và không được dùng

Những việc sau **không** nằm trong phạm vi, kể cả sau khi có trọng số ở M7:

- **Tư vấn đầu tư, định giá doanh nghiệp, khuyến nghị mua bán chứng khoán.** Ngữ liệu có
  `ho-so-niem-yet` (5.192 đoạn) — hồ sơ doanh nghiệp niêm yết. Có dữ liệu về doanh nghiệp
  niêm yết **không** làm mô hình thành công cụ tư vấn đầu tư.
- **Tư vấn pháp lý, kế toán, thuế.** Trong ngữ liệu có mã số thuế và số ĐKKD (thông tin
  đăng ký công khai); đó là dữ liệu định danh doanh nghiệp, không phải cơ sở để tư vấn thuế.
- **Tra cứu thông tin liên hệ của cá nhân.** Email và số điện thoại đã bị gỡ khỏi ngữ liệu
  (đo 25/09/2026: 0 email, 0 số điện thoại). Mô hình không được dựng để trả về thông tin
  liên hệ, và nếu nó trả về thì đó là bịa.
- **Ra quyết định tự động có hệ quả với con người hoặc doanh nghiệp** (cho vay, tuyển dụng,
  chấm tín nhiệm, sàng lọc đối tác).
- **Nguồn dữ kiện chính thức.** Ngữ liệu chụp trạng thái tại thời điểm cào; doanh nghiệp
  thay đổi liên tục.

---

## 4. Dữ liệu huấn luyện

Toàn bộ số đo dưới đây đo ngày **25/09/2026**, trực tiếp trên CSDL.

### 4.1 Lớp văn bản (`bdsg_chat.doan_tri_thuc`)

| Nguồn | Số đoạn | Dung lượng |
|---|---:|---:|
| `ho-so-niem-yet` | 5.192 | 4,20 MB |
| `ho-so-dn` | 6.434 | 2,83 MB |
| `wiki-crm` | 107 | 0,13 MB |
| **Tổng phát hành được** | **11.733** | **7,16 MB** (7.509.969 ký tự) |

Chia tập (trên toàn bộ 17.788 đoạn của bảng gốc, trước khi loại nguồn máy sinh):
huấn luyện **16.151** · kiểm tra **835** · thẩm định **802**.

### 4.2 Lớp có cấu trúc (`postgres`)

| Bảng | Số đo |
|---|---|
| `business.company_profiles` | 6.672 tổng · 5.645 đã xuất bản · 6.439 có sản phẩm · 5.952 có mã tỉnh · 6.608 có tóm tắt |
| Ký tự (trên 5.645 đã xuất bản) | tóm tắt 1.941.353 + sản phẩm 322.477 |
| `business.company_sector_links` | 6.666 công ty có ngành |
| `business.capabilities` | 11.927 dòng · 346.704 ký tự tên (`name` + `name_en`) |

**Con số chính thức cho "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ" là 5.424** —
đủ **cả ba** điều kiện (đã xuất bản ∧ có ngành ∧ có sản phẩm). Các con số 6.672 / 6.439 /
5.952 chỉ đếm theo **một** điều kiện và không được dùng thay.

### 4.3 Phân bố ngôn ngữ

| Thứ tự | Ngôn ngữ | Dung lượng đã đo |
|---|---|---|
| 1 | Tiếng Việt | 7.509.969 ký tự |
| 2 | Tiếng Anh | **chưa tách đo riêng** (346.704 ký tự là tổng `name` + `name_en`) |
| 3 | Tiếng Trung | **chưa đo** — chưa chọn được nguồn có giấy phép cho phép tái phát hành |

### 4.4 Tiền xử lý và kiểm tra dữ liệu cá nhân

Quét tự chạy, không tin lời khai của bước trước:

| Phép quét | Kết quả |
|---|---|
| Email | 0 |
| Số điện thoại | 0 |
| URL nội bộ | 0 |
| "mã số thuế" | 29 khớp — phần lớn là mã số thuế / số ĐKKD doanh nghiệp (**thông tin đăng ký công khai** ở Việt Nam), lẫn vài dương tính giả (tên lớp CSS, trường `rev` trong JSON) |
| "địa chỉ IP" | 5 khớp — **tất cả dương tính giả**: số tiền kiểu Việt Nam, ví dụ `120.086.720.000 đồng` |

Nhãn `[EMAIL]` và `[SĐT]` còn trong văn bản là bằng chứng bước gỡ **đã chạy thật**.

**Rác cào web còn sót:** 110 đoạn (menu web / CSS / JS / URL ngoài) = **0,17 MB trên
7,16 MB = 2,3%**, tập trung ở `ho-so-niem-yet` (110/5.192 = 2,1%). Đây là số đo trên bản
thô; bộ lọc của bản phát hành thuộc M4 và trạng thái của nó ghi trong `bo-du-lieu/`.

### 4.5 Nguồn bị loại và lý do

| Nguồn | Quy mô | Lý do |
|---|---|---|
| `map5d.khach_dn` | 1.079.991 bản ghi | 100% `nguon = 'crm_geocode_dot2'` ⇒ dữ liệu khách hàng CRM. Cột chỉ có `id`, `ten`, `do_chinh_xac`, `ma_xa`, `ma_tinh`, `geom`, `nguon`, `ngay_cap_nhat` — **không có ngành nghề, không có sản phẩm** |
| `kho-tri-thuc` | 118 tệp | 118/118 mang dòng cấp phép bên thứ ba ("Licensed to RAI Holdings") |
| `ocop` | 1.727 sản phẩm | văn quảng cáo người bán, `url` trỏ `buudien.vn` |
| `tin-tuc` | — | bản quyền toà soạn |
| `bai-dang` | — | nội dung người dùng đăng trên nền tảng |
| `nao-agent` | 116 đoạn | **máy sinh qua LiteLLM** ⇒ đầu ra mô hình bên thứ ba; thêm nữa 3.601 não agent là cấu hình thương mại của BDSG |
| `bai-dang-bds` | 5.939 đoạn | **máy sinh qua LiteLLM** — cùng lý do |
| `business.capabilities.description` | 696.890 ký tự | chỉ **58 giá trị khác nhau** trên 11.927 dòng ⇒ chuỗi xuất xứ ETL lặp lại, không phải mô tả |

Hai nguồn máy sinh cộng lại 6.055 đoạn — đúng bằng khoảng cách 17.788 − 11.733.

---

## 5. Quy trình huấn luyện

**Chưa huấn luyện — mục này trống cho tới M7.**

Các trường sau **không có giá trị** vì chưa có lần chạy nào:

| Trường | Giá trị |
|---|---|
| Số bước / số epoch | chưa đo |
| Tốc độ học, bộ tối ưu, lịch giảm | chưa đo |
| Kích thước lô, độ dài ngữ cảnh khi huấn luyện | chưa đo |
| Độ chính xác số (fp16/bf16) | chưa đo |
| Phần cứng đã dùng | chưa có — chưa thuê GPU lần nào |
| Thời gian huấn luyện | chưa đo |
| Mất mát cuối cùng | chưa đo |

Dây chuyền **dự kiến** dùng (các tệp đã kiểm tra là có thật trong bản MiniMind tham chiếu):
`train_tokenizer.py` → `train_pretrain.py` → `train_full_sft.py`, tuỳ chọn thêm
`train_dpo.py` / `train_lora.py` / `train_ppo.py` / `train_grpo.py` /
`train_distillation.py` / `train_agent.py`.

Số liệu MiniMind tự công bố, để tham khảo mức chi phí — **đây là số của họ, trên phần cứng
và ngữ liệu của họ, không phải số của BDSG**: 1× RTX 3090, ~2,31 giờ cho 1 epoch, ~3 nhân
dân tệ (giá thuê 3090 họ ghi ~1,3 ¥/giờ); trên 8× H100 rút xuống cỡ phút. Con số 2,31 giờ
là cho `minimind-3` cỡ 64M trên **bộ rút gọn** `pretrain_t2t_mini` + `sft_t2t_mini`, không
phải bộ đầy đủ.

---

## 6. Đánh giá

### 6.1 Bộ đánh giá

227 câu, **đóng băng ngày 22/09/2026**. Bộ câu hỏi không được sửa sau khi đã đo, để lần đo
sau còn so được với lần này.

### 6.2 Kết quả đường cơ sở M3

> **Đây KHÔNG phải điểm của trọng số BDSG.** Không có trọng số nào để đo. Đây là điểm của
> hệ đang chạy tại `llm.bdsg.vn`: lớp truy hồi `pg_trgm` + `tsvector` của BDSG đặt trước
> một mô hình của bên thứ ba.

| Nhóm | Số câu | Điểm |
|---|---:|---:|
| Nghiệp vụ **trong** kho tri thức | 111 | 0,636 |
| Nghiệp vụ **ngoài** kho tri thức | 31 | 0,539 |
| Câu bẫy chống bịa | 60 | 0,953 |
| Tiếng Việt tổng quát | 25 | 0,908 |
| **Lợi ích truy hồi** (trong − ngoài) | — | **+0,097** |

### 6.3 Cách đọc

- **+0,097 là toàn bộ đóng góp đo được của lớp truy hồi.** Không lớn. Ghi đúng như đo được
  tốt hơn là trưng 0,636 để người đọc tưởng đó là công của BDSG.
- **0,953 ở nhóm chống bịa là đường cơ sở cao**, nghĩa là khoảng cải thiện còn lại rất hẹp —
  không nghĩa là hệ đã an toàn.
- Lớp truy hồi **khớp chữ, không khớp nghĩa**: cổng LiteLLM của BDSG không có mô hình nhúng
  (embedding) nào, nên không có lựa chọn vector.

### 6.4 Đánh giá trọng số BDSG

**Chưa huấn luyện — mục này trống cho tới M7.** Khi có trọng số, chúng sẽ được đo trên
đúng bộ 227 câu đã đóng băng ở trên và kết quả sẽ đặt cạnh đường cơ sở này.

---

## 7. Giới hạn và thiên lệch

### 7.1 Giới hạn do dữ liệu (đo được)

- **Ngữ liệu nhỏ: 7,16 MB.** Ngữ liệu tiền huấn luyện của MiniMind là ~10 GB. Chênh lệch
  cỡ ba bậc độ lớn. Mô hình huấn luyện trên 7,16 MB sẽ **không** có kiến thức tổng quát;
  tốt nhất nó chỉ thạo miền doanh nghiệp Việt Nam trong ngữ liệu.
- **2,3% ngữ liệu còn dính rác cào web** (110 đoạn, 0,17 MB), chưa lọc.
- **Thiên lệch về doanh nghiệp niêm yết và doanh nghiệp có hồ sơ trên nền tảng BDSG.**
  `ho-so-niem-yet` chiếm 4,20/7,16 MB = 59% dung lượng. Doanh nghiệp nhỏ, hộ kinh doanh,
  doanh nghiệp không có hồ sơ số gần như vắng mặt.
- **Thiên lệch địa lý chưa đo.** Có 5.952 hồ sơ mang mã tỉnh, nhưng **phân bố theo tỉnh
  chưa được đo** — không kết luận gì về độ phủ vùng miền.
- **Tiếng Anh chưa tách đo, tiếng Trung chưa có.** Mọi tuyên bố về năng lực hai ngôn ngữ
  này đều chưa có cơ sở đo lường.

### 7.2 Giới hạn do kiến trúc

Chính MiniMind ghi trong tài liệu của họ: **mô hình bịa kiến thức**, và **độ ổn định sự
thật giảm sau giai đoạn học tăng cường (RL)**. Ở cỡ 26M–198M, đây là giới hạn của cỡ mô
hình chứ không phải lỗi cấu hình, và không có cách điều chỉnh tham số nào làm nó biến mất.

### 7.3 Khuyến nghị

Đừng dùng đầu ra làm dữ kiện mà không đối chiếu nguồn. Trong miền doanh nghiệp, một cái
tên hay một con số bịa ra trông y hệt một cái tên hay con số thật.

---

## 8. Tác động môi trường

**Chưa huấn luyện — mục này trống cho tới M7.**

| Trường | Giá trị |
|---|---|
| Loại phần cứng | chưa có |
| Số giờ GPU | chưa đo |
| Nhà cung cấp hạ tầng / vùng | chưa chọn |
| Lượng carbon phát thải | chưa đo |

Sẽ khai báo theo *Machine Learning Impact calculator* (Lacoste và cộng sự, 2019) khi có lần
chạy thật. Không điền số của thượng nguồn vào ô của mình.

---

## 9. Cân nhắc đạo đức

- **Dữ liệu khách hàng CRM không được đưa vào, và đây là quyết định lớn nhất của bản phát
  hành này.** 1.079.991 bản ghi `map5d.khach_dn` bị loại vì 100% đến từ `crm_geocode_dot2`.
  Đó là con số lớn nhất mà dự án có; không dùng nó là chỗ bản phát hành này **nói không**
  rõ nhất.
- **Đầu ra máy sinh không được đưa vào.** 6.055 đoạn sinh qua cổng LiteLLM bị loại vì điều
  khoản nhà cung cấp thường cấm dùng đầu ra để huấn luyện mô hình cạnh tranh — và vì huấn
  luyện mô hình trên đầu ra của mô hình khác là chép bài, không phải học.
- **Mã số thuế và số ĐKKD được giữ lại có chủ đích.** Ở Việt Nam đây là thông tin đăng ký
  **công khai** của pháp nhân, không phải dữ liệu cá nhân. Email và số điện thoại thì bị gỡ
  (đo lại: 0 và 0).
- **Nội dung bên thứ ba bị loại theo tỷ lệ đo được, không theo cảm tính.** `kho-tri-thuc`
  bị loại vì **118/118** tệp mang dòng cấp phép của bên khác.
- **Tên miền không phải bằng chứng.** `llm.bdsg.vn` là tên miền; nó không chứng minh có
  trọng số. Trường `bdsg_la_trong_so_bdsg` mới là thứ trả lời câu hỏi đó, và nó đang trả
  `false`.

---

## 10. Trích dẫn

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

Thượng nguồn: [MiniMind](https://github.com/jingyaogong/minimind) của Jingyao Gong,
Apache-2.0.

---

## 11. Liên hệ và phiên bản thẻ

| Trường | Giá trị |
|---|---|
| Phiên bản thẻ | 1 |
| Ngày viết | 25/09/2026 |
| Ngày số liệu ngữ liệu được đo | 25/09/2026 |
| Ngày số liệu đánh giá được đo | 22/09/2026 |
| Phiên bản mô hình được mô tả | **chưa có** |

Thẻ này sẽ được viết lại ở M7. Cho tới lúc đó, mọi mục ghi "chưa huấn luyện — mục này
trống cho tới M7" phải giữ nguyên chữ ấy, không được điền bằng số suy đoán.
