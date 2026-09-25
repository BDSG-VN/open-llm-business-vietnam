# Kiến trúc mô hình BDSG

Transformer decoder-only viết từ đầu bằng PyTorch thuần, từ các kỹ thuật đã công bố
trong bài báo. Không phụ thuộc thư viện `transformers`, không phụ thuộc `numpy`.

**Trạng thái 26/09/2026: kiến trúc này chưa từng được huấn luyện.** Không có trọng số nào
tồn tại. Mọi con số trong tài liệu này hoặc là số **tính ra từ công thức** (và được ghi rõ
là vậy), hoặc là số **đo được** từ bài tự kiểm (`thu_kien_truc.py`). Không có con số nào
nói về chất lượng mô hình, vì chất lượng chưa đo được.

---

## 1. Tệp trong thư mục này

| Tệp | Việc |
|---|---|
| `cau_hinh.py` | `CauHinhBDSG` — kích thước và siêu tham số, tự kiểm ràng buộc, đọc/ghi JSON, tính số tham số không cần torch |
| `kien_truc.py` | `BDSGChoNgonNgu` và các khối thành phần: `RMSNorm`, RoPE, `ChuYNhomTruyVan`, `MangSwiGLU`, `KhoiGiaiMa` |
| `__init__.py` | Xuất công khai |
| `thu_kien_truc.py` | Bài tự kiểm, 13 phép kiểm, không cần GPU / dữ liệu / trọng số |
| `README.md` | Tệp này |

Chạy bài tự kiểm:

```bash
.venv/bin/python3 mo-hinh/thu_kien_truc.py     # thoát 0 nếu đạt, 1 nếu hỏng
```

Kết quả chạy thật ngày 26/09/2026 (torch 2.8.0, Python 3.9.6, CPU Apple M1): **13/13 đạt**, thoát mã 0.

---

## 2. Sơ đồ

```
ids (B, T)
  │
  ├─ embed_tokens            (vocab_size × hidden_size)
  │
  ├─ lặp num_hidden_layers lần:
  │     x = x + ChuYNhomTruyVan( RMSNorm(x) )        ← pre-norm, residual
  │     x = x + MangSwiGLU(     RMSNorm(x) )
  │
  ├─ norm                    (RMSNorm cuối)
  └─ lm_head                 (hidden_size × vocab_size, buộc chung với embedding nếu bật)
       │
     logits (B, T, vocab_size)  [+ loss nếu truyền nhãn]
```

Vị trí token đi vào mô hình **chỉ** qua RoPE, áp lên `q` và `k` bên trong mỗi lớp chú ý.
Không có bảng vị trí học được, không có vector vị trí cộng vào embedding.

---

## 3. Bảng kỹ thuật và bài báo gốc

Mỗi khối dưới đây được viết lại từ **mô tả toán học trong bài báo**, không chép từ kho mã nào.

| Kỹ thuật | Bài báo gốc | Mã arXiv | Dùng ở đâu |
|---|---|---|---|
| Transformer, chú ý nhân-tích có tỉ lệ | Vaswani et al. 2017, *Attention Is All You Need* | [1706.03762](https://arxiv.org/abs/1706.03762) | khung chung |
| RMSNorm | Zhang & Sennrich 2019, *Root Mean Square Layer Normalization* | [1910.07467](https://arxiv.org/abs/1910.07467) | `RMSNorm` |
| RoPE | Su et al. 2021, *RoFormer: Enhanced Transformer with Rotary Position Embedding* | [2104.09864](https://arxiv.org/abs/2104.09864) | `_dung_bang_rope`, `ap_rope` |
| Grouped-Query Attention | Ainslie et al. 2023, *GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints* | [2305.13245](https://arxiv.org/abs/2305.13245) | `ChuYNhomTruyVan`, `lap_kv` |
| SwiGLU | Shazeer 2020, *GLU Variants Improve Transformer* | [2002.05202](https://arxiv.org/abs/2002.05202) | `MangSwiGLU` |
| Pre-norm | Xiong et al. 2020, *On Layer Normalization in the Transformer Architecture* | [2002.04745](https://arxiv.org/abs/2002.04745) | `KhoiGiaiMa` |
| Buộc trọng số vào/ra | Press & Wolf 2017, *Using the Output Embedding to Improve Language Models* | [1608.05859](https://arxiv.org/abs/1608.05859) | `tie_word_embeddings` |
| Khởi tạo co giãn theo số lớp | Radford et al. 2019 (GPT-2, báo cáo kỹ thuật, không có mã arXiv); Brown et al. 2020 | [2005.14165](https://arxiv.org/abs/2005.14165) | `_khoi_tao_trong_so` |
| Ngân sách tham số ↔ dữ liệu | Hoffmann et al. 2022, *Training Compute-Optimal Large Language Models* | [2203.15556](https://arxiv.org/abs/2203.15556) | mục 6 dưới đây |

---

## 4. Vì sao chọn từng kỹ thuật

Phần này trả lời **vì sao**, không mô tả lại **là gì** — mô tả "là gì" nằm trong bài báo ở
bảng trên. Lý lẽ đầy đủ nằm trong chú thích của `kien_truc.py`; đây là bản rút gọn.

### RMSNorm thay vì LayerNorm
LayerNorm làm hai việc: dời tâm và đổi tỉ lệ. Bài báo arXiv:1910.07467 cho thấy phần **dời tâm**
gần như không đóng góp vào khả năng hội tụ — cái làm nên tác dụng là phần đổi tỉ lệ. Bỏ dời tâm
thì bớt một lượt rút gọn trên chiều ẩn và bớt một tham số bias mỗi lớp. Ở mô hình nhỏ chạy trên
**máy cá nhân**, mỗi lượt rút gọn đều đắt vì CPU không giàu băng thông bộ nhớ.

Phép tính RMS luôn ép sang float32 rồi mới ép ngược. Lý do: `x²` ở fp16 tràn số rất sớm
(fp16 hết tầm ở ~65504, nên một giá trị kích hoạt 300 là đủ để `300² = 90.000` tràn). Khi tràn,
tổng thành `inf`, `rsqrt(inf)` thành 0, cả vector ra 0, loss thành NaN — **một lớp sau**, không
để lại dấu vết nào chỉ về đây. Phép kiểm số 9 ép đúng tình huống này, và nó đòi **giá trị** chứ
không chỉ đòi `isfinite`: đường đi của lỗi tràn kết thúc ở **số không**, mà số không thì `isfinite`
vẫn trả `True` — bản trước của phép kiểm này hỏng đúng vì thế (xem mục 8).

### RoPE thay vì học vị trí
Ba lý do, theo thứ tự quan trọng với dự án này:

1. **Không tốn tham số.** Bảng vị trí học được tốn `max_position_embeddings × hidden_size`
   tham số. Ở bản `nho` (2048 × 512) đó là 1.048.576 tham số — 2,9% cả mô hình, tiêu vào việc
   đếm chỗ ngồi. RoPE tốn 0 tham số vì nó là phép quay tính ra từ vị trí.
2. **Mã hoá khoảng cách *tương đối*, không phải vị trí tuyệt đối.** Định lý trung tâm của bài
   báo: tích vô hướng `⟨R_m q, R_n k⟩` chỉ phụ thuộc `(m − n)`. Với văn bản hồ sơ doanh nghiệp —
   ngữ liệu của BDSG — quan hệ giữa hai từ cách nhau 3 từ là như nhau dù chúng nằm ở đầu hay
   giữa tài liệu. Vị trí tuyệt đối không mang thông tin đó. Phép kiểm số 10 kiểm chính tính chất này.
3. **Đổi được trần ngữ cảnh mà không phải huấn luyện lại từ đầu.** Bảng học được thì cứng ở
   kích thước đã huấn luyện; RoPE ngoại suy được (kém dần, nhưng có đường đi).

Bảng cos/sin là **buffer `persistent=False`**, không nằm trong `state_dict`. Nó là đại lượng
tính ra từ `(head_dim, rope_theta)`, không phải tham số học. Nếu lưu vào tệp trọng số thì mỗi
lần đổi độ dài ngữ cảnh là một lần tệp không nạp được, mà không vì lý do gì.

### GQA thay vì MHA — lựa chọn quan trọng nhất của kiến trúc này
Lý do **không phải** về chất lượng mà về **bộ nhớ lúc suy luận**.

Khi sinh từng token, mô hình phải giữ K và V của mọi token đã sinh, ở mọi lớp. Kích thước đó là:

```
KV cache = 2 × số_lớp × num_key_value_heads × head_dim × độ_dài × số_byte
```

Nó **không phụ thuộc số tham số**, và nó **lớn lên theo độ dài ngữ cảnh**. Với bản `nho`
(8 lớp, head_dim 64, fp16): GQA `kv=4` tốn 8 KiB mỗi token → **16 MiB** (16,78 MB thập phân)
ở ngữ cảnh 2048. MHA `kv=8` sẽ tốn gấp đôi: 16 KiB mỗi token → **32 MiB** (33,55 MB).
Số tính ra từ công thức trên; `cau_hinh.py::bo_nho_kv_cache_MB` tính lại được và trả về
**MB thập phân** (1 MB = 10⁶ byte), nên nó in ra 16,78 chứ không phải 16 — hai đơn vị, cùng
một lượng bộ nhớ.

Vì sao điều đó quyết định: mục tiêu của dự án là **người dùng tải về máy cá nhân chạy được**.
VPS của BDSG đã đo là không chạy nổi LLM tự host — một mô hình 7B chỉ đạt 0,3 token/giây vì
nghẽn băng thông RAM. Trên máy cá nhân, RAM là thứ khan hiếm hơn FLOP, và ở ngữ cảnh dài thì
KV cache, chứ không phải trọng số, mới là cái chặn.

**Cái giá phải trả:** theo arXiv:2305.13245, GQA mất một phần nhỏ chất lượng so với MHA nhưng
giữ được gần hết, trong khi Multi-Query Attention (`kv=1`) thì mất rõ. GQA là điểm giữa có chủ đích.
**Mất bao nhiêu ở quy mô của BDSG thì CHƯA ĐO**, vì chưa huấn luyện mô hình nào. Không được
trích số của bài báo như thể là số của BDSG.

### SwiGLU thay vì FFN + ReLU/GELU
Bài báo arXiv:2002.05202 đo trên T5 và thấy biến thể có cửa ăn hơn các biến thể không cửa ở
cùng ngân sách tính toán. Đây là kết quả **thực nghiệm**, và bài báo nói thẳng là không giải thích
được vì sao (câu cuối bài quy nó cho "sự quan phòng"). BDSG chọn theo kết quả đó, và ghi lại rằng
đó là chọn theo kết quả người khác đo, chưa phải kết quả BDSG đo.

Hệ quả về kích thước: SwiGLU dùng **ba** ma trận thay vì hai, nên để giữ nguyên ngân sách
`8h²` tham số cho khối FFN, bề rộng trong phải là `8h/3` chứ không phải `4h`. Đó là lý do các
cấu hình trong kho đặt `intermediate_size` quanh 2,7 lần `hidden_size`.

### Pre-norm thay vì post-norm
Bài báo arXiv:2002.04745 phân tích gradient lúc khởi tạo: ở post-norm, gradient tại các lớp gần
đầu ra lớn theo số lớp, nên phải có giai đoạn làm ấm (warmup) dài thì mới không nổ. Ở pre-norm,
đường residual đi thẳng từ đầu vào tới đầu ra không qua lớp chuẩn hoá nào.

Với BDSG đây là lựa chọn về **rủi ro**, không phải về điểm số: dự án **chưa thuê GPU lần nào**
(26/09/2026). Một lần huấn luyện phân kỳ vì đặt sai warmup là một lần trả tiền GPU cho không.

---

## 5. Số tham số: tính ra so với đếm được

`cau_hinh.py::so_tham_so()` tính số tham số bằng công thức, **không cần torch, không cần dựng
mô hình**. Đây là con số mà mọi ước lượng bộ nhớ, thời gian và chi phí thuê GPU của cả dự án
dựa vào. Một công thức sai ở đây làm sai toàn bộ dự toán, và **không ai phát hiện ra cho tới
lúc đã trả tiền GPU**.

Vì vậy phép kiểm số 4 — phép kiểm quan trọng nhất trong bài tự kiểm — đối chiếu
`cfg.so_tham_so()["tong"]` với `sum(p.numel() for p in model.parameters())` trên 6 hình dạng
khác nhau (GQA, MHA `kv=nq`, MQA `kv=1`, buộc/không buộc trọng số, `head_dim` đặt tường minh).
Yêu cầu là **khớp tuyệt đối**, không phải xấp xỉ.

Bài tự kiểm cũng đối chiếu công thức với các tệp cấu hình thật trong `huan-luyen/cau-hinh/`
(mục không bắt buộc, chỉ in ra). Kết quả ngày 26/09/2026:

| Cấu hình | Công thức tính ra | Số tệp tự ghi | |
|---|---:|---:|---|
| `nho.json` | 36.184.576 | 36.184.576 | khớp |
| `vua.json` | 119.563.008 | 119.563.008 | khớp |
| `lon.json` | 295.748.608 | 295.748.608 | khớp |

Hai nguồn số này được viết độc lập với nhau, nên việc chúng khớp là một phép đối chiếu thật.

Cách đếm (khớp từng dòng với `kien_truc.py`, mọi phép chiếu đều `bias=False`):

```
embedding : vocab_size × hidden_size
lm_head   : vocab_size × hidden_size  — CHỈ đếm khi tie_word_embeddings=False
mỗi lớp   : q_proj  hidden × (nq × head_dim)
            k_proj  hidden × (nkv × head_dim)
            v_proj  hidden × (nkv × head_dim)
            o_proj  (nq × head_dim) × hidden
            2 RMSNorm  2 × hidden
            SwiGLU     3 × hidden × intermediate
cuối      : hidden  (RMSNorm trước lm_head)
KHÔNG đếm : bảng cos/sin của RoPE — buffer không học, persistent=False
```

Khi `tie_word_embeddings=True`, `lm_head.weight` **là cùng một đối tượng `Parameter`** với
`embed_tokens.weight`. `nn.Module.parameters()` lọc trùng theo định danh đối tượng nên chỉ đếm
một lần — bài tự kiểm khẳng định cả hai điều: chênh lệch đúng bằng `vocab × hidden`, và
`lm_head.weight is embed_tokens.weight`.

---

## 6. Điều chưa đo, và một tỉ lệ đáng lo

Phải ghi ra đây vì nó ảnh hưởng tới quyết định, không phải để trang trí.

**Ngữ liệu hiện có nhỏ hơn nhiều so với ngân sách dữ liệu mà kích thước mô hình đòi hỏi.**

Số đã đo: ngữ liệu sau khi lọc là 11.699 đoạn / 7.474.485 ký tự (7,13 MB). Tokenizer tiếng Việt
đã đo đạt 3,59 ký tự/token. Suy ra ngữ liệu khoảng **2,08 triệu token** — đây là số **tính ra**
từ hai số đã đo, không phải số đếm trực tiếp trên ngữ liệu đã token hoá.

Hoffmann et al. 2022 (arXiv:2203.15556) đưa ra tỉ lệ tính-toán-tối-ưu khoảng 20 token cho mỗi
tham số. Với bản `nho` 36,18 triệu tham số, tỉ lệ đó ứng với ~724 triệu token. Ngữ liệu hiện có
là **khoảng 0,3% của mức đó** — thiếu cỡ 350 lần.

Đó **không** có nghĩa là phải bỏ. Nó có nghĩa là:
- Con số 36M không nên được biện minh bằng "nhỏ nên dễ", mà phải được hiểu là đã lớn so với dữ liệu.
- Cần hoặc thêm ngữ liệu, hoặc chấp nhận huấn luyện dưới mức tối ưu và nói rõ điều đó, hoặc
  xét lại kích thước.
- Đây là con số nên quyết trước khi thuê GPU, không phải sau.

**Những điều khác chưa đo:**
- Tốc độ (token/giây) trên bất kỳ máy nào — chưa có trọng số nên chưa bấm giờ được.
- Chất lượng mô hình — chưa huấn luyện.
- GQA mất bao nhiêu chất lượng so với MHA **ở quy mô này** — chỉ có số của bài báo gốc ở quy mô khác.
- **Trọng số BDSG có thật sự nạp được bằng công cụ khác hay không.** Kiến trúc này giữ tên trường
  và tên mô-đun theo chuẩn transformers *để* việc đó khả thi, nhưng chưa có trọng số nào để thử,
  nên đó vẫn là **ý định, chưa phải sự kiện đã kiểm chứng**.

Các con số đánh giá M3 (0,636 trong kho / 0,539 ngoài kho / lợi ích truy hồi +0,097 / bẫy chống
bịa 0,953 / tiếng Việt tổng quát 0,908) là của **hệ RAG đang chạy tại `llm.bdsg.vn`**, không phải
của mô hình này. Đừng trích chúng cho mô hình này.

---

## 7. Vì sao không dùng thư viện có sẵn

Câu hỏi thật là: đã có `transformers.LlamaModel` chạy tốt, vì sao viết lại?

**Lý do thứ nhất — và là lý do thật.** Yêu cầu của dự án là một mô hình BDSG *viết độc lập từ đầu*.
Nếu kiến trúc là `LlamaModel` được nhập vào rồi gói lại, thì kiến trúc là mã của người khác, và
câu "viết từ đầu" là một lời khai sai về nguồn gốc. Cách duy nhất để câu đó đúng là thật sự viết
từ mô tả toán học trong bài báo. Đó là việc đã làm ở đây, và bảng ở mục 3 là danh sách nguồn.

**Lý do thứ hai — phụ thuộc.** Mục tiêu là người dùng tải về máy cá nhân chạy được. `transformers`
kéo theo một cây phụ thuộc lớn. Tệp `kien_truc.py` chỉ cần `torch` — thậm chí chạy được trong môi
trường không có cả `numpy` (môi trường của kho này hiện đúng như vậy, và bài tự kiểm chạy qua).

**Lý do thứ ba — đọc được hết.** Cả kiến trúc gói trong một tệp đọc hết được trong một buổi.
Khi mô hình cho kết quả lạ, có thể đọc thẳng đường tính thay vì lần qua nhiều lớp trừu tượng.

### Đổi lại, mất những gì — nói thẳng

Đây không phải lựa chọn miễn phí:

- **Mất nhiều năm sửa lỗi tích luỹ.** `transformers` đã đi qua vô số trường hợp biên mà mã này
  chưa gặp. Bài tự kiểm 13 phép ở đây tốt hơn là không có, nhưng không so được với hàng nghìn
  bài kiểm của một thư viện lớn.
- **Mất các tính năng vận hành.** Không có `device_map`, không có nạp theo mảnh, không có tích hợp
  lượng tử hoá, không có các nhân attention chuyên dụng ngoài `scaled_dot_product_attention` của torch.
- **Mất tốc độ.** Mã này chưa được tối ưu và chưa đo tốc độ trên máy nào.
- **Chưa có mặt na đệm (padding mask).** Sinh theo lô chỉ đúng khi mọi chuỗi trong lô cùng độ dài.
  Huấn luyện của BDSG dùng chuỗi đóng gói độ dài cố định nên chưa cần, nhưng đây là giới hạn thật
  và được ghi trong docstring của `sinh()` để không ai tưởng là đã có.

**Điều KHÔNG đổi và cố tình không đổi:** tên các trường cấu hình (`hidden_size`,
`num_attention_heads`, `num_key_value_heads`, `intermediate_size`, `rms_norm_eps`, `rope_theta`,
`tie_word_embeddings`…) và tên các mô-đun con (`embed_tokens`, `layers`, `norm`, `lm_head`).
Đó là **chuẩn transformers** — quy ước đặt tên chung của cả hệ sinh thái mở, Llama, Mistral, Qwen
đều dùng đúng bộ tên đó. Nó không phải tên riêng của dự án nào, và giữ nó là điều kiện để trọng số
BDSG nạp được ở nơi khác. Đổi tên trường chỉ để trông khác đi là tự cắt đường ra của chính mình.

---

## 8. Bài tự kiểm kiểm những gì

Kiến trúc là phần duy nhất trong cả đường ống mà lỗi của nó **không báo**. Một mặt nạ nhân quả
đặt sai, một phép lệch nhãn sai một ô, một bộ nhớ KV quay RoPE hai lần: mô hình vẫn chạy, loss vẫn
giảm, không ngoại lệ nào được ném ra. Chỉ đến lúc đánh giá mới thấy kết quả kém, và lúc đó không
còn biết kém vì kiến trúc hay vì dữ liệu.

13 phép kiểm, chạy trên mô hình tí hon (hidden 64, 2 lớp, vocab 128), xong trong vài giây trên CPU:

| # | Kiểm gì | Bắt được lỗi gì |
|---|---|---|
| 1 | Cấu hình từ chối 8 trường hợp ràng buộc sai | Cấu hình sai chỉ sập ở giữa vòng huấn luyện |
| 2 | `tu_json`/`ra_json` đi về không mất thông tin | Khoá ghi chú trong tệp cấu hình bị nuốt mất |
| 3 | Hình dạng đầu ra; loss khởi tạo ≈ `ln(vocab)` | Khởi tạo trọng số sai độ lệch chuẩn |
| **4** | **Số tham số tính ra == đếm được, 6 hình dạng** | **Công thức sai ⇒ mọi dự toán GPU sai** |
| 5 | Lan truyền ngược; mọi tham số có gradient; loss giảm | Một khối được dựng nên nhưng không được gọi |
| 6 | `sinh()` trả đúng số token, 6 cách lấy mẫu; eos dừng sớm; sinh có bộ nhớ KV **trùng khít** sinh không bộ nhớ | Lấy mẫu trả sai độ dài; `top_p` ra NaN; `sinh()` dùng bộ nhớ KV sai cách |
| 7 | Bộ nhớ KV cho kết quả trùng đường không bộ nhớ | RoPE áp sai vị trí khi có cache; mặt nạ sai khi `q` ngắn hơn `k` |
| 8 | Đổi token cuối không đổi logits ở vị trí trước — chạy trên **cả hai** đường chú ý | Mặt nạ nhân quả rò rỉ — mô hình nhìn thấy tương lai |
| 9 | RMSNorm khớp công thức; đầu vào 300.0 ở fp16 cho **đúng 1,0** | Tràn số `x²` ở fp16 ⇒ cả vector về 0 rồi NaN một lớp sau |
| 10 | RoPE bảo toàn tích vô hướng theo `(m−n)`; bảo toàn độ dài | Bảng góc quay dựng sai công thức |
| 11 | `lap_kv` nhân bản đúng thứ tự `[1,1,1,2,2,2]` | Đầu query nhìn vào đầu KV sai, im lặng |
| 12 | Đường SDPA và đường viết tay cho cùng kết quả | Sai mặt nạ hoặc sai hệ số `1/√head_dim` ở một trong hai |
| **13** | **Loss ghép logit tại `t` với nhãn tại `t+1`** — đồng nhất thức, và sau khi học thuộc thì đoán token kế tiếp | **Lệch nhãn sai một ô ⇒ mô hình học chép lại đầu vào** |

### Bài kiểm này có thật sự bắt được lỗi không — đo bằng cách gài lỗi

Một bài kiểm luôn in "đạt" thì không nói lên điều gì. Ngày 26/09/2026 đã gài **11 lỗi** vào
`kien_truc.py` và `cau_hinh.py`, mỗi lần một lỗi, rồi chạy lại toàn bộ bài kiểm. Kết quả:
**cả 11 đều bị bắt**, chương trình thoát mã 1.

| Lỗi gài vào | Phép kiểm hỏng |
|---|---|
| `lap_kv` nhân bản xen kẽ thay vì liền khối | 11 |
| Mặt nạ nhân quả nới một ô (nhìn được 1 token tương lai) | 7, 8, 12 |
| Hệ số tỉ lệ `1/√d` thành `1/d` ở đường viết tay | 12 |
| Công thức tham số: FFN đếm 2 ma trận thay vì 3 | 4 |
| Quên buộc trọng số vào/ra | 4 |
| RMSNorm không ép sang float32 | 9 |
| `sinh()` có bộ nhớ KV mà vẫn đưa lại cả chuỗi | 6 |
| Lệch nhãn **ngược** một ô | 13 |
| Lệch nhãn 2 ô | 13 |
| Bỏ lệch nhãn hẳn | 3, 13 |
| Điều kiện dừng `eos` bị lờ | 6 |

**Bốn lỗi trong bảng trên trước đó *không* bị bắt** — bản đầu của bài kiểm (12 phép, 26/09/2026)
vẫn cho 12/12 và thoát mã 0 với chúng. Ghi ra đây vì đó mới là thông tin có ích, và vì mỗi cái
đều là một cách "hỏng mà không báo" điển hình:

- **Lệch nhãn ngược một ô** và **lệch 2 ô**: không phép kiểm nào ghim *hướng* của phép lệch.
  Đây đúng là lỗi mà mục này nói là nguy hiểm nhất. Đã thêm hẳn **phép kiểm 13** cho nó.
- **RMSNorm không ép float32**: phép kiểm 9 cũ chỉ hỏi `isfinite`. Nhưng đường đi của lỗi tràn là
  `x² → inf → rsqrt(inf) → 0`, kết thúc ở **số không**, và số không thì `isfinite` trả `True`.
  Nay phép kiểm đòi giá trị: vector hằng số 300 phải cho ra đúng 1,0.
- **`sinh()` dùng sai bộ nhớ KV**: phép kiểm 6 cũ chỉ so **độ dài** đầu ra. Thêm phép so giá trị
  vẫn chưa đủ — trên mô hình *chưa huấn luyện*, đầu ra suy biến (lấy tham lam rơi vào điểm cố định
  và lặp mãi một token), nên hai đường tính khác nhau vẫn cho cùng một dãy. Phải so trên mô hình
  **đã học thuộc** một chuỗi thì khác biệt mới lộ ra — ở vị trí thứ 13 của chuỗi (đếm từ 0).

Ngoài ra sửa hai chỗ **khẳng định không thể hỏng** (luôn "đạt" bất kể kết quả):

- Phép kiểm 6 khẳng định `ra_du.shape[1] in (T+1, T+2, T+3, T+4)`. Với `so_token_moi=4` thì độ dài
  trả về **chỉ có thể** là một trong bốn giá trị đó — khẳng định phủ trọn miền giá trị.
- Phép kiểm 8 chạy ở cấu hình mặc định (`bdsg_dung_sdpa=True`), mà ở đó khi `S == T` thì
  `kien_truc.py` đi đường `is_causal=True`: mặt nạ do **torch** sinh, còn mặt nạ BDSG tự dựng
  không hề được dùng đến. Phép kiểm 8 cũ vì vậy chứng nhận mặt nạ của torch. Nay nó chạy trên
  **cả hai** đường.

**Điều bài kiểm vẫn chưa ghim** (nói thẳng, chưa sửa): nếu RoPE bị áp nhầm lên cả `v` — chứ không
chỉ `q` và `k` — thì 13 phép kiểm hiện tại vẫn đạt hết. Đây là lỗi làm mất tính chất "vị trí chỉ đi
vào qua điểm số chú ý"; hiện chỉ có chú thích trong `ap_rope()` giữ nó, chưa có phép kiểm.

Kết quả ngày 26/09/2026: **13/13 đạt**, thoát mã 0.

---

## 9. Dùng

```python
from mo_hinh import CauHinhBDSG, BDSGChoNgonNgu

cfg = CauHinhBDSG.tu_json("huan-luyen/cau-hinh/nho.json")   # khoá ghi chú lạ được giữ, không sập
print(cfg.tom_tat())

m = BDSGChoNgonNgu(cfg)
print("tham số đếm được:", m.dem_tham_so())

kq = m(ids, nhan=ids)      # kq.logits, kq.loss
ra = m.sinh(ids, so_token_moi=64, nhiet_do=0.8, top_k=40, top_p=0.9)
```

**Lưu ý về tên thư mục:** thư mục thật tên là `mo-hinh` (có gạch ngang, theo quy ước đặt tên của
kho). Gạch ngang không hợp lệ trong tên mô-đun Python nên `import mo-hinh` không chạy. Tệp
`thu_kien_truc.py` tự nạp gói bằng `importlib` khi chạy trực tiếp. Kho chưa có bản đóng gói
(`pyproject.toml`) tính đến 26/09/2026.
