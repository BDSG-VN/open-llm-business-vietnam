# Dây chuyền huấn luyện

Mô hình ngôn ngữ mở tiếng Việt cho dữ liệu doanh nghiệp.
Nền: [MiniMind](https://github.com/jingyaogong/minimind) (Apache-2.0).
Thứ tự ngôn ngữ: **tiếng Việt → tiếng Anh → tiếng Trung**.

Cập nhật 25/09/2026.

---

## 0. Trạng thái thật, nói trước khi nói gì khác

**BDSG chưa huấn luyện trọng số nào.** Không có mô hình để tải, không có điểm
đánh giá của mô hình BDSG, không có tốc độ sinh chữ đã đo.

API đang chạy tại `llm.bdsg.vn` tự khai `bdsg_la_trong_so_bdsg=false` cho **mọi**
mô hình. Thứ chạy ở đó là **truy hồi** (pg_trgm + tsvector — *không phải* vector,
vì cổng LiteLLM không có mô hình nhúng nào) đặt trước một mô hình của bên thứ ba.
Hai mã mô hình công khai hiện có: `openbiz-vn-chat` và `openbiz-vn-reasoner`.
`bdsg-ai-v1` và `bdsg-ai-v1-suy-luan` là **tên cũ**, vẫn nhận được vĩnh viễn
như bí danh, nhưng `/v1/models` chỉ liệt kê hai tên mới.

Thư mục này là **dây chuyền**, không phải sản phẩm. Nó biến ngữ liệu thành mô
hình. Hôm nay nó chưa chạy lần nào trên dữ liệu thật.

Tất cả các con số trong tài liệu này thuộc đúng một trong ba loại, và loại nào
cũng được ghi rõ:

| Nhãn | Nghĩa |
|---|---|
| **đo được** | có lệnh chạy ra con số đó, kèm ngày |
| **tính ra** | suy từ kiến trúc bằng công thức có sẵn trong repo, kiểm chứng lại được |
| **chưa đo** | nói thẳng là chưa đo |

---

## 1. Dây chuyền gồm những gì

```
huan-luyen/
├── README.md                     ← bạn đang đọc
├── chay-cuc-bo.md                ← hướng dẫn cho người dùng cuối tải mô hình về chạy
├── tu-vung/
│   ├── huan_luyen_tu_vung.py     ← huấn luyện BPE ba thứ tiếng, có trọng số ngôn ngữ
│   └── do_tokenizer.py           ← ĐO chất lượng từ vựng (bằng chứng cho mục 2)
├── du-lieu/
│   ├── lam_sach.py               ← lọc rác cào web khỏi JSONL
│   ├── tron.py                   ← trộn ba thứ tiếng, xuất định dạng MiniMind đọc được
│   └── nguon-mo.md               ← bảng nguồn ngữ liệu mở + giấy phép từng nguồn
└── cau-hinh/
    ├── nho.json                  ← 39,33 M — chạy trên máy cá nhân, CPU
    ├── vua.json                  ← 136,87 M — một GPU 24GB
    ├── moe.json                  ← 212,38 M (kích hoạt 77,90 M) — thử nghiệm
    └── tinh_tham_so.py           ← tính lại số tham số, không cần cài torch
```

Thứ tự chạy:

```
  (1) lam_sach.py     ngữ liệu BDSG thô  →  ngữ liệu sạch
  (2) huan_luyen_tu_vung.py   ngữ liệu vi+en+zh  →  từ vựng BDSG
  (3) do_tokenizer.py         kiểm từ vựng trước khi tiêu tiền GPU
  (4) tron.py --dinh-dang pretrain   →  ngữ liệu tiền-huấn-luyện
  (5) MiniMind train_pretrain.py     →  trọng số nền     (cần GPU thuê, mốc M7)
  (6) tron.py --dinh-dang sft        →  ngữ liệu tinh chỉnh
  (7) MiniMind train_full_sft.py     →  mô hình trả lời được
```

Bước 5 và 7 là mã của MiniMind, không viết lại. Thư mục này chuẩn bị đầu vào cho
chúng, và ghi lại những chỗ mã của họ sẽ cắn.

Mọi script đều chạy bằng **Python thuần + thư viện `tokenizers`**. Không cần
torch, không cần transformers, để bước chuẩn bị dữ liệu làm được trên máy tính
xách tay trong khi GPU để dành cho việc huấn luyện. Đã chạy thử trên Python
3.9.6 + tokenizers 0.22.2, 25/09/2026.

---

## 2. Vì sao phải huấn luyện từ vựng riêng, dù chính MiniMind khuyên đừng

### Cảnh báo của họ nói gì

Dòng đầu tiên của `trainer/train_tokenizer.py` trong MiniMind:

> *không khuyến nghị huấn luyện lại tokenizer — MiniMind đã có sẵn, script này
> chỉ để học và tham khảo. Mô hình huấn luyện trên từ điển khác nhau sẽ cho đầu
> ra hoàn toàn không thống nhất, làm giảm khả năng dùng lại mô hình trong cộng
> đồng.*

Cảnh báo này **đúng**, và nó nhắm vào **người dùng lại trọng số đã phát hành của
MiniMind**. Nếu bạn tải `minimind2-small` về rồi đổi từ vựng, bạn đã phá vỡ ánh
xạ giữa id token và hàng embedding — mô hình vẫn chạy, chỉ là nói bậy.

**BDSG huấn luyện từ đầu, không nạp một byte trọng số nào của họ.** Không có ánh
xạ nào để phá. Điều "không thống nhất" ở đây không tồn tại.

### Giữ từ vựng của họ mới là cái sai — và đây là số đo

Từ vựng 6.400 của MiniMind được huấn luyện trên ngữ liệu **tiếng Trung + tiếng
Anh**, không có tiếng Việt. Byte-level BPE **không bao giờ báo lỗi** khi gặp chữ
lạ — nó lặng lẽ tụt xuống mức byte. Một chữ tiếng Việt có dấu chiếm 2–3 byte
UTF-8, nên nó thành 2–3 token.

Đo bằng `do_tokenizer.py` trên từ vựng gốc của MiniMind (thư mục `model/` của bản
MiniMind đã tải về; trên máy đo hôm đó là `/tmp/minimind-ref/model`),
văn bản mẫu là văn phong hồ sơ doanh nghiệp, **25/09/2026**:

| Văn bản | Ký tự | Token | token/ký tự | Token là mảnh byte |
|---|---:|---:|---:|---:|
| Tiếng Anh | 356 | 104 | **0,292** | 0,0% |
| Tiếng Việt **không dấu** | 546 | 276 | **0,505** | 0,0% |
| Tiếng Việt **có dấu** | 546 | 472 | **0,864** | **22,2%** |
| Tiếng Trung | 77 | 61 | 0,792 | 0,0% |

Và phép so trong **cùng một văn bản, cùng một từ vựng** — chỉ khác nhau đúng một
biến là dấu thanh:

| | Token trung bình / từ | Tỉ lệ từ bị băm nhỏ |
|---|---:|---:|
| Từ **có dấu** | **4,08** | **100,0%** |
| Từ **không dấu** | 2,39 | — |

Ba con số rút ra:

1. **Mỗi ký tự tiếng Việt có dấu tốn gấp 2,96 lần một ký tự tiếng Anh.**
2. **Dấu thanh làm một từ tốn gấp 1,71 lần** — và **100%** từ có dấu bị băm
   thành nhiều token. Không có ngoại lệ nào.
3. **22,2% số token không phủ thêm được ký tự nào** — chúng là mảnh byte giữa
   chừng một chữ cái. Hơn một phần năm ngân sách ngữ cảnh đốt vào việc ráp lại
   dấu thanh.

Hệ quả cụ thể: với cửa sổ 512 token, từ vựng MiniMind chứa được **592 ký tự**
tiếng Việt có dấu. Cùng ngân sách đó ở tiếng Anh là 1.753 ký tự. Một hồ sơ doanh
nghiệp trung bình trong ngữ liệu BDSG dài 640 ký tự (7.509.969 ÷ 11.733) — tức
là **một hồ sơ đã không vừa một cửa sổ**.

### Đọc lại số này thế nào cho đúng

Các con số trên đo trên **văn bản mẫu tự viết, vài trăm ký tự**. Chúng đủ để
chứng minh **hướng** của vấn đề, không đủ để chốt một con số cho toàn bộ ngữ
liệu. Muốn con số thật thì chạy trên ngữ liệu thật:

```bash
python3 do_tokenizer.py --bo minimind=<thư-mục-model-của-MiniMind> \
                        --van-ban vi=../../bo-du-lieu/bdsg.sach.jsonl
```

### Phép đo trên dữ liệu thật — mạnh hơn, xem ở `tu-vung/ket-qua/`

Cùng ngày 25/09/2026, phép đo trên **ngữ liệu BDSG thật** đã được thực hiện và
ghi tại **`tu-vung/ket-qua/do-luong-25-09-2026.md`** *(tệp đó không do tài liệu
này sinh ra — nó là kết quả của một lượt đo riêng, kèm tokenizer thử nghiệm
`tokenizer-vi-6400-thu-nghiem.json`)*. Cách làm ở đó chặt hơn: huấn luyện trên
10.500 đoạn, **giữ lại 1.199 đoạn / 1.037.113 ký tự chưa từng thấy** để đo, và
**giữ nguyên vocab 6.400** đúng bằng MiniMind — không tăng từ vựng rồi khoe số
token giảm, vì từ vựng lớn hơn thì bao giờ cũng nén tốt hơn.

| tokenizer (đều 6.400 từ) | tiếng Việt: ký tự/token | tiếng Anh: ký tự/token |
|---|---:|---:|
| MiniMind gốc (Trung–Anh) | 1,22 | 3,18 |
| Thử nghiệm học tiếng Việt | **3,59** | 2,61 |

Hai kết luận, và **cái thứ hai quan trọng hơn**:

1. Tiếng Việt **giảm 66,1% số token**, chứa được gấp **2,95 lần** chữ trên cùng
   ngân sách ngữ cảnh. (Khớp hướng với bảng mẫu ở trên: 1,22 ký tự/token ở đó
   tương ứng 0,820 token/ký tự, cạnh 0,864 tôi đo trên văn bản mẫu.)
2. Tiếng Anh **tệ đi 22,0%**. Bản thử nghiệm đó chỉ học tiếng Việt, và cái giá
   hiện ra ngay. **Đây chính là bằng chứng rằng bước trộn ba thứ tiếng ở mục 4
   là bắt buộc, không phải trang trí.** Nếu chỉ đổi sang tiếng Việt thuần thì
   BDSG chỉ đổi nạn nhân chứ không giải quyết gì.

Cơ chế nhìn thấy được, không phải suy đoán: chữ **Công** ở từ vựng gốc tốn **bốn**
token (`C ǀ Ã ǀ ´ ǀ ng`) vì `ô` không có trong từ vựng Trung–Anh nên bị đẩy xuống
từng byte UTF-8. Từ vựng học tiếng Việt gộp cả chữ thành **một** token.

### Cái giá phải trả, nói luôn

Từ vựng riêng nghĩa là **mô hình BDSG không dùng lại được trọng số MiniMind, và
ngược lại**. Cộng đồng MiniMind không tải thẳng trọng số BDSG về dùng được. Đó
đúng là cái mà cảnh báo của họ nói tới. BDSG chấp nhận, vì lựa chọn kia là phát
hành một mô hình tiếng Việt đốt 22% ngân sách ngữ cảnh vào dấu thanh.

### Cái gì bắt buộc giữ nguyên

Đổi từ vựng, nhưng **không** đổi giao thức. `huan_luyen_tu_vung.py` giữ nguyên:

- `models.BPE` + `pre_tokenizers.ByteLevel(add_prefix_space=False)` + `decoders.ByteLevel`;
- **đúng 36 vị trí token đặc biệt, đúng thứ tự đó**, nên `<|endoftext|>`=0,
  `<|im_start|>`=1, `<|im_end|>`=2 — khớp với `bos_token_id=1`, `eos_token_id=2`
  trong `MiniMindConfig`. Script **dừng lại và báo lỗi** nếu ba id này sai, trước
  khi ghi bất cứ tệp nào ra đĩa;
- **mẫu hội thoại (chat template) sao chép nguyên văn**, 3.895 ký tự, đã đối
  chiếu bằng `difflib` là giống hệt bản trong `model/tokenizer_config.json` của
  họ. Lý do không được sửa: `SFTDataset.generate_labels` (`dataset/lm_dataset.py`
  dòng 91-107) tìm chuỗi `"<bos>assistant\n"` … `"<eos>\n"` để biết đoạn nào là
  câu trả lời cần gán nhãn. Sửa mẫu mà quên sửa hàm đó thì **nhãn sai hết mà
  không có một dòng lỗi nào** — mất mát vẫn giảm, mô hình vẫn "học", chỉ là học
  sai chỗ.

### Từ vựng bao nhiêu chữ

Mặc định **24.576**. Đây là **giả định ban đầu, chưa được đo**. Lý lẽ:

- MiniMind dùng 6.400 cho **hai** thứ tiếng. BDSG có **ba**, một trong đó cần
  dấu thanh.
- Chia thô: ~8k cho tiếng Việt, ~6k cho tiếng Anh, ~10k để tiếng Trung đủ phủ
  chữ Hán cơ bản → ~24k. Là bội số của 64.
- Cái giá: với `nho` (hidden 512), embedding chiếm **32,0%** tổng tham số. Từ
  vựng to làm mô hình nhỏ phình ra ở chỗ không sinh lợi.

Cách chốt con số thật: huấn luyện vài từ vựng ở các cỡ khác nhau rồi chạy
`do_tokenizer.py` so sánh, **trước** khi thuê GPU.

**Cả ba cấu hình dùng CHUNG một từ vựng.** Đây không phải chi tiết nhỏ: mỗi từ
vựng khác nhau là một họ mô hình khác nhau, không dùng chung trọng số, không
dùng chung bộ đánh giá. Chính là bài học rút ra từ cảnh báo của MiniMind — chỉ
là áp cho họ mô hình của BDSG.

---

## 3. Vì sao 7,16 MB ngữ liệu BDSG là dữ liệu TINH CHỈNH, không phải TIỀN-HUẤN-LUYỆN

### Số đo

Ngữ liệu BDSG phát hành được, đo 25/09/2026 (CSDL `bdsg_chat`, bảng
`doan_tri_thuc`), sau khi loại hai nguồn máy sinh:

| Nguồn | Đoạn | Dung lượng |
|---|---:|---:|
| `ho-so-niem-yet` | 5.192 | 4,20 MB |
| `ho-so-dn` | 6.434 | 2,83 MB |
| `wiki-crm` | 107 | 0,13 MB |
| **Cộng** | **11.733** | **7,16 MB** (7.509.969 ký tự) |

### So với cái cần có

| | Dung lượng | BDSG bằng bao nhiêu |
|---|---:|---:|
| Ngữ liệu BDSG | 7,16 MB | — |
| `pretrain_t2t` **bản mini** của MiniMind | 1,2 GB | **0,58%** |
| `pretrain_t2t` bản đầy đủ của MiniMind | ~10 GB | **0,07%** |

**BDSG có 0,6% của bộ tiền-huấn-luyện nhỏ nhất mà chính MiniMind dùng.**

Tính theo token thì còn rõ hơn. Với từ vựng MiniMind (0,864 token/ký tự **đo
được** ở mục 2), 7.509.969 ký tự ≈ **6,5 triệu token**. Theo tỉ lệ kinh nghiệm
~20 token cho mỗi tham số (Chinchilla — quy tắc kinh nghiệm, **không phải định
luật**), cấu hình `nho` 39,33 M tham số cần khoảng **787 triệu token**. BDSG có
**0,8%** con số đó.

### Điều đó nghĩa là gì

Một mô hình chỉ học trên 7,16 MB sẽ không học được **tiếng Việt**. Nó sẽ học
thuộc 11.733 hồ sơ doanh nghiệp. Nó không biết ngữ pháp, không biết từ ngoài
lĩnh vực, và sẽ trả lời mọi câu hỏi bằng cách ghép lại các mảnh hồ sơ — đúng cái
hành vi mà bộ câu bẫy chống bịa (60 câu, điểm 0,953 ở đường cơ sở M3) được lập
ra để bắt.

Nên dây chuyền tách làm hai tầng, đúng như MiniMind tách:

| Tầng | Học cái gì | Lấy ở đâu | Quy mô cần |
|---|---|---|---|
| **Tiền-huấn-luyện** | tiếng Việt: ngữ pháp, từ vựng, cách nói | **ngữ liệu tiếng Việt mở** (mục 4 của `du-lieu/nguon-mo.md`) | GB |
| **Tinh chỉnh** | nghiệp vụ: hồ sơ doanh nghiệp, ngành nghề, sản phẩm | **7,16 MB của BDSG** | MB là đủ |

7,16 MB là **quá ít cho tầng một và vừa đủ cho tầng hai**. Đây không phải khiếm
khuyết của dữ liệu BDSG — đó là dữ liệu chuyên ngành, và dữ liệu chuyên ngành
vốn dĩ phải ít. Sai lầm duy nhất có thể mắc ở đây là **tưởng nó thay được tầng
một**.

### Lấy tầng nền ở đâu

Ngữ liệu tiếng Việt mở: phần tiếng Việt của **CulturaX**, **Wikipedia tiếng
Việt**, phần `vie_Latn` của **FineWeb-2**. Giấy phép từng nguồn ở
`du-lieu/nguon-mo.md` — **và ở đó có ghi rõ là tôi chưa kiểm được giấy phép nào
trong phiên này**, phải tự kiểm trước khi tải.

Về việc các dự án khác làm thế nào: **VinaLLaMA** và **Vi-Mistral-X** đều xây mô
hình tiếng Việt bằng cách lấy ngữ liệu tiếng Việt quy mô lớn. Nhưng phải nói cho
đúng: cả hai làm **tiếp tục huấn luyện** trên một mô hình nền đã có (LLaMA-2,
Mistral), còn BDSG huấn luyện **từ đầu**. Đường từ đầu cần **nhiều** ngữ liệu
hơn, không phải ít hơn. Điểm chung đáng lấy: **không ai làm được mô hình tiếng
Việt bằng ngữ liệu nội bộ vài MB.** (Đây là kiến thức tôi nhớ được, **chưa tra
lại nguồn trong phiên này**.)

### Lớp dữ liệu có cấu trúc

Ngoài 7,16 MB văn bản, còn lớp có cấu trúc trong CSDL `postgres`:

- `business.company_profiles`: **5.424** bản ghi đủ cả ba điều kiện (đã xuất bản
  ∧ có ngành ∧ có sản phẩm). **5.424 là con số duy nhất được phép dùng** cho
  câu "doanh nghiệp theo ngành nghề, tỉnh, sản phẩm dịch vụ". Không phải 6.672,
  không phải 5.645.
- `business.capabilities`: 11.927 dòng, 346.704 ký tự tên. Cột `description` có
  696.890 ký tự nhưng **chỉ 58 giá trị khác nhau** trên 11.927 dòng ⇒ là chuỗi
  xuất xứ ETL lặp lại, **không phát hành**.

Lớp này thành dữ liệu tinh chỉnh **chỉ khi** biến được thành đối thoại thật —
xem mục "điều tron.py từ chối làm" ở đầu `du-lieu/tron.py`.

---

## 4. Thứ tự vi → en → zh nghĩa là gì, cụ thể

Không phải khẩu hiệu. Nó là hai con số ở hai chỗ, và hai con số đó **cố ý khác
nhau**.

### Ở khâu từ vựng: 60 / 25 / 15

```bash
python3 huan_luyen_tu_vung.py --ti-le vi=0.60,en=0.25,zh=0.15 …
```

Tỉ lệ tính theo **ký tự**, không theo số dòng hay số tệp. BPE học merge từ **tần
suất**; một dòng tiếng Trung 50 ký tự không cân được một đoạn tiếng Việt 5.000
ký tự. Đếm dòng sẽ cho tỉ lệ sai hoàn toàn.

Vì sao **không** để vi cao hơn nữa, ví dụ 85/10/5: từ vựng là **tài sản cố
định**. Sau khi huấn luyện xong, không thêm chữ vào được nếu không huấn luyện
lại từ đầu cả mô hình. Cho tiếng Trung quá ít ký tự thì chữ Hán không có merge
nào, và mọi chữ Hán về sau đều tụt xuống 3 token byte — đúng cái bệnh mà mục 2
vừa chỉ ra ở tiếng Việt, chỉ đổi nạn nhân. 15% là mức tối thiểu để tiếng Trung
**dùng được**, không phải để nó **dùng tốt**.

**Điều này đã được đo, không phải lo xa.** Bản thử nghiệm chỉ học tiếng Việt
(`tu-vung/ket-qua/do-luong-25-09-2026.md`) làm tiếng Anh **tệ đi 22,0%** —
3,18 xuống 2,61 ký tự/token. Đó là cái xảy ra khi một ngôn ngữ bị bỏ đói trong
ngân sách ký tự. Con số 25% cho tiếng Anh và 15% cho tiếng Trung tồn tại để
tránh đúng chuyện đó, và **phải kiểm lại bằng `do_tokenizer.py` sau khi huấn
luyện từ vựng thật** — nếu tiếng Anh vẫn tụt sâu thì tỉ lệ này còn sai.

### Ở khâu trộn dữ liệu: 70 / 20 / 10

```bash
python3 tron.py --ti-le vi=0.70,en=0.20,zh=0.10 …
```

Ở đây vi được đẩy cao hơn, vì đích của mô hình là tiếng Việt và ngữ liệu huấn
luyện **thêm vào được** bất cứ lúc nào — khác hẳn từ vựng.

### Vì sao tiếng Anh đứng thứ hai

Không phải vì sang. Vì nó có thật trong dữ liệu BDSG: cột `name_en` của
`business.capabilities` đóng góp trong số 346.704 ký tự tên đã đo được. Thuật
ngữ ngành, tên sản phẩm, tên tổ chức trong hồ sơ doanh nghiệp Việt Nam vốn lẫn
tiếng Anh. Mô hình không đọc được tiếng Anh sẽ vấp ngay trong dữ liệu của chính
mình.

### Vì sao vẫn giữ tiếng Trung, và vì sao nó đứng thứ ba

Giữ, vì toàn bộ hệ sinh thái MiniMind là tiếng Trung: ngữ liệu mẫu của họ, bộ
đánh giá của họ, `jieba` trong `requirements.txt`. Giữ tiếng Trung nghĩa là khi
cần **đối chứng** — "mô hình của tôi lỗi, hay là tôi dùng sai mã của họ?" — thì
còn chạy được ngữ liệu của họ để so.

Thứ ba, vì đó là thứ tự ưu tiên thật. Hệ quả **đã biết trước và chấp nhận**: nén
ngữ cảnh tiếng Trung của từ vựng BDSG sẽ **kém hơn** từ vựng gốc MiniMind (đo
được hôm nay: 0,792 token/ký tự). Đó là cái giá của việc dồn chỗ cho tiếng Việt.
Khi đo lại bằng `do_tokenizer.py` mà thấy tiếng Trung kém đi, **đó không phải
lỗi** — đó là thiết kế, và nó được ghi ở đây để sáu tháng nữa không ai tưởng là
lỗi rồi đi "sửa".

---

## 5. Ba cấu hình mô hình

Số tham số **tính ra** bằng `cau-hinh/tinh_tham_so.py`, chạy được không cần torch.

| | `nho` | `vua` | `moe` |
|---|---:|---:|---:|
| hidden_size | 512 | 768 | 768 |
| số lớp | 8 | 16 | 8 |
| q / kv heads | 8 / 4 | 8 / 4 | 8 / 4 |
| chuyên gia | — | — | 4, top-1 |
| **Tổng tham số** | **39.331.328** | **136.867.584** | **212.375.808** |
| Kích hoạt mỗi token | 39,33 M | 136,87 M | 77,90 M |
| Embedding chiếm | 32,0% | 13,8% | 8,9% |
| Trọng số fp16 | 75,0 MB | 261,1 MB | 405,1 MB |
| Chạy ở đâu | máy cá nhân, CPU | một GPU 24GB | thử nghiệm |

Công thức đã **đối chiếu với bảng MiniMind công bố** (`README_en.md` dòng 576-580):

```
$ python3 cau-hinh/tinh_tham_so.py --doi-chieu

cau hinh                            ho ghi      cong thuc nay
minimind-3 (dense)                     64M             63.91M     ← khớp
minimind-3-moe                   198M-A64M    198.42M-A63.94M     ← khớp
minimind2-small (ban lich su)          26M             28.98M     ← lệch 11%
minimind2 (ban lich su)               104M            118.19M     ← lệch 14%
```

Hai dòng đầu khớp dưới 0,2%. Hai dòng "bản lịch sử" **lệch, và tôi không biết vì
sao** — có thể chúng dùng cấu hình khác với bảng, hoặc đếm theo cách khác. Chỗ
lệch này được ghi ra thay vì giấu đi, và là lý do BDSG không lấy số của các bản
lịch sử làm căn cứ.

---

## 6. Bốn chỗ mã MiniMind sẽ cắn

Đọc từ mã thật, không đoán. Cả bốn đều thuộc họ **hỏng mà không báo**.

### 6.1. `vocab_size` không bao giờ được truyền vào — mô hình lặng lẽ lấy 6400

`trainer/train_pretrain.py` dòng 108 và `trainer/train_full_sft.py` dòng 109:

```python
lm_config = MiniMindConfig(hidden_size=args.hidden_size,
                           num_hidden_layers=args.num_hidden_layers,
                           use_moe=bool(args.use_moe))
```

Không có `vocab_size`. `MiniMindConfig` lấy mặc định `kwargs.get("vocab_size", 6400)`.
Không có tham số dòng lệnh `--vocab_size` nào cả — đã `grep` toàn bộ `trainer/`,
`scripts/` và `eval_llm.py`: chuỗi `vocab_size` chỉ xuất hiện ở bốn chỗ, và
không chỗ nào là tham số dòng lệnh — `train_tokenizer.py` (tham số của chính nó),
`convert_model.py` dòng 44 (ghi ra khi chuyển định dạng), `train_distillation.py`
dòng 63-64 (biến cục bộ `vocab_size_student`), và một dòng chú thích trong
`train_dpo.py`.

Với từ vựng 24.576 của BDSG: embedding chỉ có 6.400 hàng, còn tokenizer sinh ra
id tới 24.575 → lỗi chỉ số ngay batch đầu. Đó là trường hợp **may**. Trường hợp
xấu là ai đó đặt từ vựng nhỏ hơn 6.400: khi ấy không có lỗi nào, chỉ là hàng
nghìn hàng embedding chết nằm đó ăn bộ nhớ và ăn gradient.

**Vá — ba dòng, ở cả hai tệp:**

```python
from transformers import AutoTokenizer                      # thêm vào phần import
_tok = AutoTokenizer.from_pretrained('../model')            # ngay trước dòng lm_config
lm_config = MiniMindConfig(hidden_size=args.hidden_size,
                           num_hidden_layers=args.num_hidden_layers,
                           use_moe=bool(args.use_moe),
                           vocab_size=len(_tok))            # ← lấy từ chính tokenizer
```

Lấy từ chính tokenizer chứ không thêm `--vocab_size` vào dòng lệnh: một tham số
gõ tay là một tham số có ngày gõ sai, và gõ sai kiểu này không báo lỗi.

### 6.2. Từ vựng bắt buộc nằm ở `../model`

`trainer/trainer_utils.py` dòng 121-122:

```python
def init_model(lm_config, from_weight='pretrain', tokenizer_path='../model', …):
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
```

`train_pretrain.py` dòng 126 gọi `init_model(lm_config, args.from_weight, device=…)`
— **không truyền `tokenizer_path`**. Nên từ vựng luôn được nạp từ `../model`.
Để từ vựng BDSG ở chỗ khác thì huấn luyện vẫn chạy, chỉ là chạy bằng từ vựng
tiếng Trung. Phải chép đè `tokenizer.json` và `tokenizer_config.json` vào
`model/` của MiniMind.

### 6.3. `PretrainDataset` cắt cụt, không ghép gói

`dataset/lm_dataset.py` dòng 52:

```python
tokens = self.tokenizer(str(sample['text']), add_special_tokens=False,
                        max_length=self.max_length - 2, truncation=True).input_ids
```

Đoạn dài hơn `max_seq_len` bị **vứt phần đuôi**, không đẩy sang mẫu sau.
`train_pretrain.py` để mặc định `max_seq_len=340`, kèm chú thích của họ: *"tiếng
Trung 1 token ≈ 1,5–1,7 ký tự"*.

Hai việc phải làm:

1. **Con số 340 là của tiếng Trung, không dùng lại được.** Phải suy ra từ chính
   phép đo của mình: chạy `do_tokenizer.py` trên từ vựng BDSG, lấy ký tự/token,
   rồi tính ngược ra độ dài mong muốn.
2. **Cắt đoạn trước khi ghi**: `tron.py --cat-doan N` cắt theo ranh giới câu.
   Mặc định là `0` = không cắt, **cố ý**: bật nó lên mà chưa đo ký tự/token thì
   chỉ là đổi một con số đoán này lấy một con số đoán khác.

### 6.4. `SFTDataset` tìm nhãn bằng chuỗi

`generate_labels` (dòng 91-107) dò chuỗi `"<bos>assistant\n"` … `"<eos>\n"` để
biết phần nào là câu trả lời cần tính mất mát. Vai trò ghi sai — `"bot"`, `"ai"`
thay vì `"assistant"` — **không sinh lỗi nào**, chỉ làm không đoạn nào được gán
nhãn. `tron.py` từ chối ghi ra và nói rõ lý do khi gặp vai trò lạ, vì lỗi này
không thể bắt được ở bất kỳ chỗ nào phía sau.

---

## 7. Chi phí, theo số của MiniMind

MiniMind công bố: **RTX 3090, ~2,31 giờ, ~3 nhân dân tệ** cho bản `minimind2-small`.
Với 8× H100 rút xuống cỡ phút.

Đây là số của **họ**, cho **cấu hình của họ**, trên **ngữ liệu của họ**. Nó chưa
nói gì về chi phí của BDSG, vì cả ba đều khác:

- Từ vựng 24.576 thay vì 6.400 → embedding to hơn, lớp cuối tính nhiều hơn.
- `nho` là 39,33 M, không phải 26 M.
- Ngữ liệu tiếng Việt chưa tải về nên **chưa biết là bao nhiêu GB**.

Chi phí thật chỉ biết sau khi chạy một lần. Đó là việc của **mốc M7 (thuê GPU)**.

---

## 8. Dây chuyền này KHÔNG làm gì

- **Không huấn luyện.** Bước 5 và 7 là mã MiniMind, cần GPU, chưa chạy lần nào.
- **Không tải dữ liệu.** `du-lieu/nguon-mo.md` liệt kê nguồn; tải là việc thủ
  công, có chủ ý, sau khi đã đọc giấy phép.
- **Không kiểm giấy phép.** Phiên làm việc 25/09/2026 không truy cập mạng. Mọi
  dòng giấy phép trong `nguon-mo.md` là kiến thức nhớ được, phải kiểm lại.
- **Không đánh giá mô hình.** Bộ M3 (227 câu) nằm ở `danh-gia/`, không ở đây.
- **Không hứa điểm số.** Đường cơ sở M3 — nghiệp vụ trong kho 0,636 (111 câu),
  ngoài kho 0,539 (31 câu), lợi ích truy hồi +0,097, câu bẫy chống bịa 0,953
  (60 câu), tiếng Việt tổng quát 0,908 (25 câu) — là điểm của **hệ truy hồi +
  mô hình bên thứ ba** đang chạy, đo 22/09/2026. **Không phải** điểm của mô hình
  sẽ huấn luyện. Một mô hình 39M huấn luyện từ đầu gần như chắc chắn sẽ thấp hơn
  ở giai đoạn đầu.
- **Không hứa tốc độ.** Chưa đo token/giây trên bất cứ máy nào.

MiniMind tự ghi hai hạn chế của họ, và chúng áp nguyên cho mô hình BDSG vì cùng
kiến trúc, cùng quy mô: **mô hình bịa ra kiến thức nó không có**, và **độ ổn định
về sự thật giảm sau khi học tăng cường**.

---

## 9. Giấy phép và ghi công

MiniMind là **Apache-2.0**. Mọi tệp trong thư mục này đọc mã của họ và có chỗ đi
theo sát (danh sách 36 token đặc biệt, mẫu hội thoại 3.895 ký tự chép nguyên
văn). Giữ nguyên thông báo giấy phép và ghi công trong bản phát hành.

**Giấy phép mã nguồn không phải giấy phép dữ liệu.** Bộ dữ liệu của MiniMind
(`jingyaogong/minimind_dataset`) được tổng hợp từ nguồn bên thứ ba và **không**
nằm dưới Apache-2.0. Muốn dùng phải lần lại xuất xứ từng phần.
