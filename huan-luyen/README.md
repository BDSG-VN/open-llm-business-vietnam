# Dây chuyền huấn luyện của BDSG

Mô hình ngôn ngữ mở cho dữ liệu doanh nghiệp Việt Nam.
**Tiếng Việt là chính, tiếng Anh là phụ. Không có ngôn ngữ thứ ba.**

Cập nhật 26/09/2026.

---

## 0. Trạng thái thật, nói trước khi nói gì khác

**BDSG chưa huấn luyện trọng số nào.** Không có mô hình để tải, không có điểm
đánh giá của mô hình BDSG, không có tốc độ sinh chữ đã đo.

Dịch vụ tại `llm.bdsg.vn` tự khai `bdsg_la_trong_so_bdsg = false` cho **mọi** mã
mô hình. Thứ chạy ở đó là **truy hồi** (`pg_trgm` + `tsvector` — *không phải*
vector, vì cổng mô hình nội bộ không có mô hình nhúng nào) đặt trước một mô hình
của bên thứ ba. Hai mã công khai: `openbiz-vn-chat`, `openbiz-vn-reasoner`;
`bdsg-ai-v1` và `bdsg-ai-v1-suy-luan` là tên cũ, vẫn nhận vĩnh viễn như bí danh.

Thư mục này là **dây chuyền**, không phải sản phẩm. Nó biến ngữ liệu thành mô
hình. Tính đến hôm nay nó chưa chạy lần nào trên dữ liệu thật ở quy mô thật.

Mọi con số trong tài liệu này thuộc đúng một trong ba loại, và loại nào cũng
được ghi rõ ngay tại chỗ:

| Nhãn | Nghĩa |
|---|---|
| **đo được** | có lệnh chạy ra con số đó, kèm ngày |
| **tính ra** | suy từ kiến trúc bằng công thức có trong kho, kiểm chứng lại được |
| **chưa đo** | nói thẳng là chưa đo |

---

## 1. Mô hình này được viết từ đâu ra

Kiến trúc là **transformer decoder-only, pre-norm**, viết từ đầu bằng PyTorch
thuần từ các kỹ thuật **đã công bố trong bài báo**. Không dẫn lại kho mã nào;
mỗi khối dẫn về bài báo gốc theo mã arXiv:

| Khối | Bài báo |
|---|---|
| RMSNorm | arXiv:1910.07467 — Zhang & Sennrich, 2019 |
| RoPE (mã hoá vị trí quay) | arXiv:2104.09864 — Su và cộng sự, 2021 |
| GQA (chú ý theo nhóm truy vấn) | arXiv:2305.13245 — Ainslie và cộng sự, 2023 |
| SwiGLU | arXiv:2002.05202 — Shazeer, 2020 |
| Đặt chuẩn hoá trước (pre-norm) | arXiv:2002.04745 — Xiong và cộng sự, 2020 |
| Buộc embedding với lớp ra | arXiv:1608.05859 — Press & Wolf, 2016 |
| BPE ở mức byte (từ vựng) | arXiv:1508.07909 và arXiv:1909.03341 |
| Tỉ lệ dữ liệu trên tham số | arXiv:2203.15556 — quy tắc kinh nghiệm, **không phải định luật** |

Bộ huấn luyện cũng là kỹ thuật đã công bố, nên nó phải có bảng dẫn nguồn riêng —
mục 11 nói kiến trúc **và bộ huấn luyện** đều viết từ bài báo, và một lời như thế
chỉ đứng được nếu cả hai nửa đều dẫn được nguồn:

| Kỹ thuật trong `chung.py` / hai vòng huấn luyện | Bài báo |
|---|---|
| AdamW — suy giảm trọng số tách rời khỏi gradient | arXiv:1711.05101 — Loshchilov & Hutter, 2017 |
| Lịch học suất cosine (phần giảm dần) | arXiv:1608.03983 — Loshchilov & Hutter, 2016 |
| Cắt gradient theo chuẩn L2 toàn cục | arXiv:1211.5063 — Pascanu và cộng sự, 2012 |

Ba kỹ thuật còn lại **không có một bài báo gốc duy nhất để dẫn**, và nói thẳng ra
đây còn hơn gán bừa một mã arXiv: **hâm nóng học suất**, **đóng gói chuỗi liên
tục** (mục 7.1), và **che mặt nhãn ở phần câu hỏi khi tinh chỉnh** (mục 7.2) là
thực hành chung của ngành, mỗi cái xuất hiện rải rác ở nhiều báo cáo kỹ thuật
chứ không khởi từ một bài. Lý do BDSG chọn từng cái ghi ngay tại chỗ dùng nó.

**Tên các trường cấu hình theo chuẩn thư viện `transformers`** — `hidden_size`,
`num_hidden_layers`, `num_attention_heads`, `num_key_value_heads`,
`intermediate_size`, `vocab_size`, `rms_norm_eps`, `rope_theta`,
`tie_word_embeddings`. Đây là **quy ước chung của cả hệ sinh thái mô hình mở**,
không phải của riêng dự án nào. Giữ đúng tên không phải để giống ai: đó là điều
kiện để trọng số BDSG nạp được ở máy người khác mà không phải viết lớp chuyển
đổi. Giá trị bên trong thì là lựa chọn của BDSG, và mỗi lựa chọn có lý do ghi
ngay trong tệp cấu hình.

Một hệ quả phải nói thẳng: **giữ bố cục trọng số trùng một bố cục phổ biến là
một ràng buộc thật.** Mỗi lần ai đó định thêm một khối "sáng tạo" vào kiến trúc,
câu hỏi đầu tiên là: bộ chuyển đổi sang định dạng chạy cục bộ có đọc được không?
Nếu không, cái giá không phải một hàm phải viết thêm — mà là người dùng cuối
không chạy được gì.

---

## 2. Dây chuyền gồm những gì

```
huan-luyen/
├── README.md                  ← bạn đang đọc
├── chay-cuc-bo.md             ← hướng dẫn cho NGƯỜI DÙNG CUỐI tải về máy chạy
├── chung.py                   ← phần dùng chung của hai vòng huấn luyện
├── huan_luyen.py              ← ① tiền huấn luyện (pretrain)
├── tinh_chinh.py              ← ② tinh chỉnh theo chỉ dẫn (SFT)
├── tu-vung/                   ← (nhóm khác giữ)
│   ├── huan_luyen_tu_vung.py  ← huấn luyện BPE hai thứ tiếng, có trọng số ngôn ngữ
│   └── do_tokenizer.py        ← ĐO chất lượng từ vựng — bằng chứng cho mục 3
├── du-lieu/                   ← (nhóm khác giữ)
│   ├── lam_sach.py            ← lọc rác cào web khỏi JSONL
│   ├── tron.py                ← trộn hai thứ tiếng theo ngân sách ký tự
│   └── nguon-mo.md            ← bảng nguồn ngữ liệu mở + giấy phép từng nguồn
└── cau-hinh/
    ├── nho.json               ← 36,18 M — máy cá nhân, không GPU
    ├── vua.json               ← 119,56 M — một GPU thuê theo giờ
    ├── lon.json               ← 295,75 M — chỗ dành sẵn, chưa nên chạy
    └── tinh_tham_so.py        ← đếm lại số tham số, không cần cài torch
```

Kiến trúc (`CauHinhBDSG`, `BDSGChoNgonNgu`) nằm ở `mo-hinh/` tại gốc kho, do một
nhóm khác giữ.

Thứ tự chạy:

```
  ①  lam_sach.py            ngữ liệu thô        →  ngữ liệu sạch
  ②  huan_luyen_tu_vung.py  vi + en             →  từ vựng BDSG (24.576)
  ③  do_tokenizer.py        kiểm từ vựng TRƯỚC khi tiêu tiền GPU
  ④  tron.py --dinh-dang pretrain              →  ngữ liệu tiền huấn luyện
  ⑤  huan_luyen.py          ngữ liệu nền        →  trọng số nền
  ⑥  tron.py --dinh-dang sft                   →  ngữ liệu tinh chỉnh
  ⑦  tinh_chinh.py          7,13 MB của BDSG    →  mô hình trả lời được
  ⑧  danh-gia/              chấm điểm
```

Bước ①–④ chạy bằng **Python thuần + `tokenizers`**, không cần torch — để khâu
chuẩn bị làm được trên máy xách tay trong khi GPU để dành cho việc huấn luyện.
Bước ⑤ và ⑦ cần torch.

---

## 3. Vì sao BDSG phải tự huấn luyện từ vựng — đây là số đo, không phải ý kiến

Phép đo 25/09/2026 (biên bản đầy đủ ở `tu-vung/ket-qua/do-luong-25-09-2026.md`).
Trên **1.037.113 ký tự** tiếng Việt chưa từng thấy lúc huấn luyện, hai từ vựng
**cùng kích thước 6.400**, khác nhau đúng một biến — có học tiếng Việt hay không:

| từ vựng | token (tiếng Việt) | ký tự/token | token (tiếng Anh) | ký tự/token |
|---|---:|---:|---:|---:|
| cùng 6.400, **không** học tiếng Việt | 852.285 | 1,22 | 2.001 | 3,18 |
| cùng 6.400, **có** học tiếng Việt | **289.266** | **3,59** | 2.441 | 2,61 |

- Tiếng Việt: **giảm 66,1% số token** — chứa được nhiều hơn **2,95 lần** chữ
  trên cùng một ngân sách ngữ cảnh.
- Tiếng Anh: **tệ đi 22,0%**. Con số này phải công bố cùng, không được giấu. Bản
  thử nghiệm ấy **chỉ** học tiếng Việt, không trộn gì. Nó chính là lý do bản
  phát hành phải trộn **hai** thứ tiếng theo trọng số.

Giữ nguyên 6.400 cho cả hai bản là có chủ ý: từ vựng lớn hơn **luôn** nén tốt
hơn bất kể học tiếng gì, nên tăng từ vựng rồi khoe số token giảm là so sánh
gian.

### Cơ chế — nhìn thấy được, không phải suy đoán

Câu thử: *Công ty Cổ phần Tập đoàn BDSG hoạt động trong lĩnh vực bất động sản
tại Thanh Hoá.* — **72 token** ở bản không học tiếng Việt, **21 token** ở bản có
học.

Chữ **Công** ở bản không học tiếng Việt tốn **bốn** token: `C ǀ Ã ǀ ´ ǀ ng`. Chữ
`ô` không có trong từ vựng nên bị đẩy xuống **từng byte UTF-8 thô**. Bản có học
tiếng Việt gộp cả chữ thành **một** token.

**Không có lỗi nào được báo trong cả hai trường hợp.** BPE ở mức byte không bao
giờ gặp chữ lạ — nó luôn tụt xuống mức byte và chạy tiếp. Chi phí thật không
phải tốc độ mà là **trí nhớ**: cùng cửa sổ ngữ cảnh, bản không học tiếng Việt
chỉ đọc được khoảng một phần ba lượng chữ trước khi hết chỗ. Đây đúng là họ lỗi
**hỏng mà không báo**, và cách phát hiện duy nhất là **đo**.

### Điều phép đo này còn nợ

Bản đo 25/09/2026 lấy một tokenizer có sẵn của bên ngoài làm đối chứng. Kết quả
đúng, nhưng phép đo **không tự chứa**: người đọc muốn dựng lại phải đi tìm đúng
hiện vật ấy. Phép đo sẽ được chạy lại với đối chứng do chính BDSG sinh ra —
cùng 6.400, cùng thuật toán, chỉ học tiếng Anh. **Chưa chạy lại tính đến
26/09/2026**, vì còn thiếu một tệp ngữ liệu tiếng Anh đã kiểm giấy phép.

---

## 4. Thứ tự tiếng Việt → tiếng Anh nghĩa là gì, cụ thể

Không phải khẩu hiệu. Nó là **một con số ở hai chỗ**, và cả hai chỗ đều tính
theo **ngân sách KÝ TỰ**, không theo số dòng hay số tệp:

```bash
# khâu từ vựng
python3 tu-vung/huan_luyen_tu_vung.py --ti-le-viet 0.80 --ti-le-anh 0.20 …

# khâu trộn dữ liệu
python3 du-lieu/tron.py --ti-le-viet 0.80 --ti-le-anh 0.20 …
```

**Vì sao đếm ký tự chứ không đếm dòng:** BPE học merge từ **tần suất**. Một dòng
tiếng Anh 40 ký tự không cân được một đoạn tiếng Việt 4.000 ký tự; đếm dòng sẽ
cho tỉ lệ sai hoàn toàn.

**0,80 / 0,20 là con số ĐẶT, CHƯA ĐO.** Không ai có phép đo nói tỉ lệ nào tốt
nhất. Cách đo nó: chạy lại ở vài tỉ lệ khác nhau rồi đo từng bản bằng
`do_tokenizer.py`, tìm chỗ ký tự/token tiếng Việt thôi cải thiện còn tiếng Anh
bắt đầu tệ đi rõ. **Chưa ai làm phép đo đó (26/09/2026.)**

**Vì sao vẫn phải có tiếng Anh, và vì sao nó đứng thứ hai.** Không phải vì sang.
Vì nó **có thật trong dữ liệu của BDSG**: thuật ngữ ngành, tên sản phẩm, tên tổ
chức trong hồ sơ doanh nghiệp Việt Nam vốn lẫn tiếng Anh. Mô hình không đọc được
tiếng Anh sẽ vấp ngay trong dữ liệu của chính nó. Và con số **tệ đi 22,0%** ở
mục 3 là bằng chứng trực tiếp rằng bỏ đói một ngôn ngữ trong ngân sách ký tự thì
ngôn ngữ ấy hỏng — nên 20% cho tiếng Anh là mức để nó **dùng được**, không phải
để nó **dùng tốt**.

**Không có ngôn ngữ thứ ba.** Từ vựng là **tài sản cố định**: sau khi huấn luyện
xong, không thêm chữ vào được nếu không huấn luyện lại từ đầu cả mô hình. Mỗi ký
tự cấp cho một ngôn ngữ thứ ba là một ký tự lấy khỏi tiếng Việt. BDSG không có
sản phẩm nào cần ngôn ngữ thứ ba, nên không trả cái giá ấy.

---

## 5. Vì sao 7,13 MB ngữ liệu BDSG là dữ liệu TINH CHỈNH, không phải TIỀN-HUẤN-LUYỆN

Đây là điều dễ hiểu sai nhất trong cả dự án, nên nói bằng số.

### Số đo

Ngữ liệu BDSG phát hành được, **đo 26/09/2026** (CSDL `bdsg_chat`, bảng
`doan_tri_thuc`), sau khi loại hai nguồn máy sinh:

| Nguồn | Đoạn | Dung lượng |
|---|---:|---:|
| `ho-so-niem-yet` | 5.192 | 4,20 MB |
| `ho-so-dn` | 6.434 | 2,83 MB |
| `wiki-crm` | 107 | 0,13 MB |
| **Cộng** | **11.733** | **7,16 MB** (7.509.969 ký tự) |

Sau khi lọc rác cào web: **11.699 đoạn · 7.474.485 ký tự · 7,13 MB** (bỏ 34
đoạn). Quét dữ liệu cá nhân: **0 email, 0 số điện thoại, 0 URL nội bộ**.

### So với cái cần có

Với tokenizer tiếng Việt của BDSG (**3,59 ký tự/token**, đo được ở mục 3),
7.474.485 ký tự ≈ **2,08 triệu token** *(số này **tính ra** từ hai số đo trên)*.

Theo tỉ lệ kinh nghiệm ~20 token dữ liệu cho mỗi tham số (arXiv:2203.15556 —
**quy tắc kinh nghiệm, không phải định luật**):

| Cấu hình | Tham số | Token cần (~20×) | BDSG có bằng |
|---|---:|---:|---:|
| `nho` | 36,18 M | ~724 triệu | **0,29 %** |
| `vua` | 119,56 M | ~2,39 tỉ | **0,087 %** |
| `lon` | 295,75 M | ~5,91 tỉ | **0,035 %** |

### Điều đó nghĩa là gì

Một mô hình chỉ học trên 7,13 MB sẽ **không học được tiếng Việt**. Nó sẽ học
thuộc 11.699 đoạn hồ sơ doanh nghiệp. Nó không biết ngữ pháp, không biết từ
ngoài lĩnh vực, và sẽ trả lời mọi câu hỏi bằng cách ghép lại các mảnh hồ sơ —
đúng cái hành vi mà bộ câu bẫy chống bịa (60 câu, 0,953 ở đường cơ sở M3) được
lập ra để bắt.

Nên dây chuyền tách làm hai tầng:

| Tầng | Học cái gì | Lấy ở đâu | Quy mô cần |
|---|---|---|---|
| **① Tiền huấn luyện** | tiếng Việt: ngữ pháp, từ vựng, cách nói | **ngữ liệu tiếng Việt mở + tiếng Anh mở** | **GB** |
| **② Tinh chỉnh** | nghiệp vụ: hồ sơ doanh nghiệp, ngành nghề, sản phẩm | **7,13 MB của BDSG** | **MB là đủ** |

**7,13 MB là quá ít cho tầng ① và vừa đủ cho tầng ②.** Đây không phải khiếm
khuyết của dữ liệu BDSG — dữ liệu chuyên ngành vốn dĩ phải ít. Sai lầm duy nhất
có thể mắc ở đây là **tưởng nó thay được tầng ①**.

### Tầng nền lấy ở đâu

Ngữ liệu tiếng Việt mở và tiếng Anh mở — bảng nguồn và giấy phép từng nguồn ở
`du-lieu/nguon-mo.md`. **Ở đó có ghi rõ là giấy phép chưa được kiểm**; phải tự
kiểm trước khi tải. Tính đến 26/09/2026 **kho chưa có tệp ngữ liệu nền nào trên
đĩa**, nên bước ⑤ chưa chạy được ở quy mô thật.

### Lớp dữ liệu có cấu trúc

Ngoài 7,13 MB văn xuôi, còn lớp có cấu trúc trong CSDL `postgres`:

- `business.company_profiles`: **5.424** bản ghi đủ cả ba điều kiện (đã xuất bản
  ∧ có ngành ∧ có sản phẩm). **5.424 là con số duy nhất được phép dùng** cho câu
  "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ". Không phải 6.672,
  không phải 5.645, không phải 6.439.
- `business.capabilities`: 11.927 dòng. Cột `description` **chỉ có 58 giá trị
  khác nhau** trên 11.927 dòng ⇒ đó là chuỗi xuất xứ ETL lặp lại, **không phát
  hành**.

Lớp này thành dữ liệu tinh chỉnh **chỉ khi** biến được thành đối thoại thật.
`du-lieu/tron.py` cố ý **từ chối** tự bịa hỏi–đáp từ văn xuôi.

---

## 6. Ba cấu hình mô hình

Số tham số **tính ra** bằng `cau-hinh/tinh_tham_so.py`, chạy được không cần
torch.

| | `nho` | `vua` | `lon` |
|---|---:|---:|---:|
| hidden_size | 512 | 768 | 1024 |
| số lớp | 8 | 16 | 24 |
| đầu q / đầu kv | 8 / 4 | 12 / 4 | 16 / 4 |
| head_dim | 64 | 64 | 64 |
| intermediate_size | 1408 | 2048 | 2816 |
| **Tổng tham số** | **36.184.576** | **119.563.008** | **295.748.608** |
| Embedding chiếm | 34,8 % | 15,8 % | 8,5 % |
| Trọng số fp16 | 69,0 MiB | 228,0 MiB | 564,1 MiB |
| Trọng số fp16, đọc theo MB thập phân | 72,4 MB | 239,1 MB | 591,5 MB |
| Trạng thái AdamW fp32 | 0,54 GiB | 1,78 GiB | 4,41 GiB |
| Chạy huấn luyện ở đâu | máy cá nhân, CPU | một GPU ≥12 GB | một GPU 24 GB |

**Đơn vị:** MiB = 1024² byte, GiB = 1024³ — kho tính theo luỹ thừa 2 vì câu hỏi
thật là *có vừa RAM/VRAM không*, mà RAM và VRAM đều đếm theo luỹ thừa 2. Hàng
thập phân có mặt vì kích thước **tệp tải về** thì thế giới quen đọc theo MB
thập phân (1e6 byte). `mo-hinh/cau_hinh.py` có hàm `bo_nho_trong_so_MB()` in
theo MB thập phân, nên số bên đó lớn hơn **4,86 %** — đó là hai đơn vị, không
phải hai kết quả.

Cả ba dùng **chung một từ vựng 24.576** và **chung trần ngữ cảnh 2.048**. Đây
không phải chi tiết nhỏ: mỗi từ vựng khác nhau là một **họ mô hình** khác nhau,
không dùng chung trọng số, không dùng chung bộ đánh giá.

**Không có cấu hình MoE.** Bản trước của thư mục này có một tệp `moe.json`; nó
đã bị bỏ. Lý do bằng số: MoE đổi thêm tham số lấy thêm dữ liệu — nó chỉ có nghĩa
khi có đủ dữ liệu để nuôi các chuyên gia. Ở bảng mục 5, BDSG mới có 0,29 % lượng
token mà cấu hình **nhỏ nhất** cần. Một cấu hình không ai chạy được là một lời
hứa không giữ được, nên nó không được nằm trong kho.

### Kiểm số tham số

```bash
python3 cau-hinh/tinh_tham_so.py --tu-kiem   # phép đếm có đúng số học không
python3 cau-hinh/tinh_tham_so.py nho.json    # in bảng tách từng phần
```

Hai phép đếm độc lập đã cho **đúng cùng một số**: `tinh_tham_so.py` của thư mục
này và `CauHinhBDSG.so_tham_so()` của `mo-hinh/` đều ra **36.184.576** cho
`nho.json`, khớp từng phần (embedding 12.582.912 · một lớp 2.950.144 · norm cuối
512). Hai nhóm viết riêng, không nhìn mã nhau — nên đây là một **đối chiếu chéo
thật**, không phải một phép tính tự khen. *(kiểm 26/09/2026.)*

Khi đã huấn luyện thật, `huan_luyen.py` in cả **số đếm được** lẫn **số tính ra**
cạnh nhau và bắt chúng phải lệch **đúng bằng 0**.

---

## 7. Hai vòng huấn luyện

### 7.1. Tiền huấn luyện — `huan_luyen.py`

Đọc JSONL `{"text": "..."}`, mã hoá, **đóng gói** liên tục thành các khối dài
`max_seq_len`, huấn luyện dự đoán token kế tiếp.

**Đóng gói chứ không cắt cụt.** Cách dễ làm hơn là: mỗi đoạn văn thành một mẫu,
dài quá thì cắt bỏ phần dưới. Làm vậy thì một đoạn 4.000 token với
`max_seq_len` 512 sẽ có **87 % nội dung không bao giờ được học**, và không một
dòng log nào nói ra. Ở đây mọi đoạn được nối thành một luồng token liên tục,
chèn `<|het-van-ban|>` giữa hai đoạn, rồi cắt thành các khối bằng nhau.

Cái giá phải trả, nói luôn: một khối có thể vắt qua ranh giới hai đoạn, nên mô
hình nhìn thấy ngữ cảnh của đoạn trước khi đọc đoạn sau. Token ngăn cách là tín
hiệu để nó học ra chỗ đó là ranh giới. Đây là đánh đổi **đã biết và chấp nhận**.

**Phần kiểm lấy ở CUỐI, không lấy ngẫu nhiên.** Hai khối liền nhau thường đến từ
cùng một văn bản; lấy ngẫu nhiên thì phần kiểm gần như chắc chắn chứa nửa văn
bản mà phần học đã nhìn thấy — mất mát kiểm sẽ đẹp hơn sự thật, và cái đẹp đó
không phát hiện được bằng mắt.

### 7.2. Tinh chỉnh theo chỉ dẫn — `tinh_chinh.py`

Đọc JSONL `{"hoi_thoai": [{"vai": "nguoi", "noi_dung": "…"}, {"vai": "tro-ly",
"noi_dung": "…"}]}`, ráp theo định dạng hội thoại của BDSG, **che mặt nhãn ở
phần câu hỏi**, chỉ tính mất mát trên phần trả lời.

Định dạng hội thoại của BDSG — ba token đặc biệt, do `tu-vung/` đặt ra:

| id | token | việc |
|---:|---|---|
| 0 | `<\|het-van-ban\|>` | ngăn hai văn bản, và làm token đệm |
| 1 | `<\|mo-luot\|>` | mở một lượt nói |
| 2 | `<\|dong-luot\|>` | đóng một lượt nói |

```
<|mo-luot|>nguoi\n{câu hỏi}<|dong-luot|>\n<|mo-luot|>tro-ly\n{trả lời}<|dong-luot|>\n
```

Hai vai hợp lệ **và chỉ hai**: `nguoi`, `tro-ly`. Không có vai hệ thống.

**Vì sao phải che mặt nhãn ở phần câu hỏi** — đây là điều quan trọng nhất của
bước này. Nếu tính mất mát trên cả câu hỏi lẫn câu trả lời thì một phần sức học
của mô hình bị dùng để học **dự đoán câu hỏi của người dùng**, tức là dạy nó
**viết lại câu hỏi**. Ba hậu quả cụ thể:

1. **Chia sai sức học.** Câu hỏi nghiệp vụ thường ngắn và rất có khuôn ("Công ty
   X kinh doanh gì?") — thứ dễ đoán nhất trong cả tệp. Mất mát trên nó giảm rất
   nhanh, kéo mất mát trung bình xuống, làm đồ thị đẹp lên, trong khi phần trả
   lời — thứ duy nhất ta cần — học chậm hơn mà không ai nhìn thấy riêng nó.
2. **Mô hình học thói quen sinh ra câu hỏi.** Trong dữ liệu, sau một lượt trả
   lời luôn là một lượt hỏi mới. Lúc chạy thật, nó trả lời xong rồi tự hỏi tiếp.
3. **Không có lỗi nào báo.** Chỉ có một mô hình kém hơn một cách khó giải thích.

Mặt nạ ở đây được **dựng sẵn theo cấu trúc**, không đi tìm chuỗi dấu hiệu trong
dãy token: chuỗi được ráp từng đoạn một và mỗi đoạn được đánh dấu ngay lúc ráp.
Cách kia — ráp cả hội thoại rồi *tìm* `<|mo-luot|>tro-ly\n` — hỏng im lặng khi
một tin nhắn của người dùng tình cờ chứa đúng chuỗi ấy.

Phần **có giám sát** đúng bằng thứ mô hình phải tự sinh ra lúc chạy thật: nội
dung câu trả lời **và** token `<|dong-luot|>` đóng lượt đó. Dấu xuống dòng sau
`<|dong-luot|>` thì không — lúc chạy thật, sinh chữ dừng ngay ở `<|dong-luot|>`.

**Nhìn mặt nạ bằng mắt trước khi huấn luyện:**

```bash
python3 tinh_chinh.py --du-lieu sft.jsonl --tu-vung tu-vung \
    --cau-hinh cau-hinh/nho.json --xem-mat-na 3
```

### 7.3. Cả hai vòng có chung những gì

`chung.py` giữ phần dùng chung, một bản duy nhất: chọn thiết bị (CUDA → MPS →
CPU, tự động), nạp kiến trúc, nạp từ vựng, **AdamW**, **lịch cosine có hâm
nóng**, **cắt gradient**, **tích luỹ gradient**, **điểm dừng + tiếp tục được**,
và **đồng hồ token/giây kèm ước tính thời gian còn lại**.

Vài lựa chọn có chủ ý:

- **Suy giảm trọng số chỉ áp cho tham số từ 2 chiều trở lên.** Hệ số của RMSNorm
  là một vector nhân quanh giá trị 1; kéo nó về 0 làm lớp chuẩn hoá mất tác dụng
  — âm thầm, không báo lỗi.
- **Điểm dừng ghi tệp tạm rồi đổi tên.** Một điểm dừng 500 MB ghi mất vài giây;
  mất điện giữa chừng thì tệp cũ — cái duy nhất còn dùng được — đã hỏng một nửa.
  `os.replace` là thao tác nguyên tử trên cùng một hệ tệp.
- **Tự động bật AMP chỉ trên CUDA.** bf16 nếu máy có (không cần GradScaler), fp16
  + GradScaler nếu không. Trên MPS và CPU thì **mặc định tắt**: autocast trên MPS
  còn thiếu phép và từng trả kết quả khác CPU.
- **SFT mặc định `--weight-decay 0`** và học suất thấp hơn tiền huấn luyện một
  bậc: đang tinh chỉnh một mô hình đã biết ngôn ngữ, không phải dạy lại từ đầu.

---

## 8. Lề một bước — chỗ lệch thật giữa hai nhóm, và cách nó bị bắt

`mo-hinh/` **tự dịch nhãn bên trong** `forward()`:

```python
nhan_lech = nhan[:, 1:]
loss = cross_entropy(logits[:, :-1], nhan_lech, ignore_index=-100)
```

Bản đặc tả ban đầu của bộ huấn luyện này nói **ngược lại**: bên gọi dịch sẵn.
Hai quy ước đều chạy được, đều không ném lỗi, và nếu áp **cả hai** thì chuỗi bị
dịch **hai lần**: mô hình học dự đoán token cách hai bước, mất mát vẫn giảm đều,
đồ thị vẫn đẹp, chỉ riêng kết quả sinh chữ là hỏng.

**Quyết định: `huan-luyen/` đi theo quy ước của `mo-hinh/`.** Lý do không phải
kỹ thuật mà là **quyền sở hữu** — `mo-hinh/` là thư mục của nhóm khác, bộ huấn
luyện không được sửa vào đó, nên bên phải nhường là bên này. Cụ thể:

```
ids  = chuỗi token đầy đủ                     (B, T)
nhan = CÙNG chuỗi token đó, đặt -100 ở những vị trí không muốn giám sát
```

Có một cổng chặn để đo lại điều này bất cứ lúc nào:

```bash
python3 huan_luyen.py --tu-kiem-dich --cau-hinh cau-hinh/nho.json
```

Nó bắt mô hình học thuộc một lô nhỏ rồi in hai tỉ lệ cạnh nhau: khớp với token
**kế tiếp**, và khớp với token **cách hai**. **Đã chạy thật 26/09/2026**: với
`mo-hinh/` hiện tại ra 100,0 % / 0,0 % — ĐẠT. Cổng này cũng đã được thử ngược
bằng một mô hình cố ý dịch hai lần, và nó **cắn**: 0,0 % / 100,0 %, mã thoát 1.

Một cổng luôn trả "sạch" thì nhìn y hệt một cổng hỏng. Cổng này đã được chứng
minh là cắn được.

---

## 9. Đánh giá

Bộ đánh giá nằm ở `danh-gia/`, không nằm ở đây. Đường cơ sở **đo được**
(22/09/2026, bộ M3, 227 câu) — đây là điểm của **hệ truy hồi + mô hình bên thứ
ba** đang chạy, **không phải** của mô hình sẽ huấn luyện:

| Nhóm câu | Điểm | Số câu |
|---|---:|---:|
| Nghiệp vụ trong kho | 0,636 | 111 |
| Nghiệp vụ ngoài kho | 0,539 | 31 |
| Lợi ích của truy hồi | +0,097 | — |
| Câu bẫy chống bịa | 0,953 | 60 |
| Tiếng Việt tổng quát | 0,908 | 25 |

Một mô hình 36 M huấn luyện từ đầu **gần như chắc chắn sẽ thấp hơn** các số này
ở giai đoạn đầu. Đó không phải thất bại — đó là điều đã biết trước khi bắt đầu.

`danh-gia/README.md` có một **TODO chặn phát hành**: bộ đề 227 câu hiện **không
nằm trong kho**. Chừng nào nó chưa nằm trong kho thì các con số trên chưa dựng
lại được bởi người ngoài.

---

## 10. Dây chuyền này KHÔNG làm gì

- **Không tải dữ liệu.** `du-lieu/nguon-mo.md` liệt kê nguồn; tải là việc thủ
  công, có chủ ý, sau khi đã đọc giấy phép.
- **Không kiểm giấy phép.** Mọi dòng giấy phép trong `nguon-mo.md` phải được
  kiểm lại trước khi dùng.
- **Không hứa điểm số.** Xem mục 9.
- **Không hứa tốc độ.** Chưa đo token/giây của mô hình thật trên máy nào. Con số
  token/giây mà `huan_luyen.py` in ra là tốc độ **của lần chạy đang diễn ra**,
  không phải một lời hứa.
- **Không huấn luyện ở quy mô thật.** Bước ⑤ cần ngữ liệu nền quy mô GB, và kho
  chưa có tệp nào như vậy trên đĩa (26/09/2026).

---

## 11. Giấy phép và ghi công

Mã trong thư mục này do **BDSG viết**. Kiến trúc và bộ huấn luyện được viết từ
**kỹ thuật đã công bố trong bài báo** (hai bảng ở mục 1 — một cho kiến trúc,
một cho bộ huấn luyện), không dẫn xuất từ kho mã
nào — đó là lý do mục 1 trích dẫn **bài báo theo mã arXiv** chứ không trích dẫn
một kho mã.

Thư viện `tokenizers` là **công cụ** hiện thực BPE ở mức byte; PyTorch là công
cụ tính toán. Dùng thư viện là chuyện bình thường và không làm mô hình trở thành
dẫn xuất của thư viện.

**Giấy phép mã nguồn không phải giấy phép dữ liệu.** Ngữ liệu nền lấy từ nguồn
mở bên thứ ba có giấy phép riêng từng nguồn; xem `du-lieu/nguon-mo.md` và kiểm
lại trước khi dùng. Ngữ liệu nghiệp vụ 7,13 MB của BDSG theo `LICENSE-DATA` ở
gốc kho.
