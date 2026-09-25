# Chạy mô hình trên máy của bạn

Cập nhật 25/09/2026.

## Điều phải nói trước

**Hôm nay chưa có trọng số nào để tải về.** BDSG chưa huấn luyện mô hình nào —
API tại `llm.bdsg.vn` tự khai `bdsg_la_trong_so_bdsg=false` cho **mọi** mô hình.
Thứ đang chạy ở đó là **truy hồi** (pg_trgm + tsvector — không phải vector, vì
cổng LiteLLM không có mô hình nhúng nào) đặt trước một mô hình của bên thứ ba.

Vậy tài liệu này để làm gì: nó là **hợp đồng kỹ thuật viết trước**. Nó nói rõ
máy cần gì, lệnh chạy ra sao, và **đã biết trước những chỗ nào sẽ vướng** — để
khi có trọng số thật thì không phải dò lại từ đầu. Mọi con số bộ nhớ dưới đây
là **tính ra** (`huan-luyen/cau-hinh/tinh_tham_so.py`), **chưa đo trên máy thật**.
Chỗ nào chưa đo đều được ghi là chưa đo.

---

## 1. Máy cần gì

Ba cấu hình trong `huan-luyen/cau-hinh/`. Số tham số và bộ nhớ trọng số tính từ
kiến trúc; xem cách tính trong `tinh_tham_so.py`.

| | `nho.json` | `vua.json` | `moe.json` |
|---|---|---|---|
| Tham số | 39,33 M | 136,87 M | 212,38 M (kích hoạt 77,90 M) |
| hidden / lớp | 512 / 8 | 768 / 16 | 768 / 8, 4 chuyên gia top-1 |
| Trọng số fp16 | **75,0 MB** | **261,1 MB** | **405,1 MB** |
| Trọng số fp32 | 150,0 MB | 522,1 MB | 810,1 MB |
| Bộ đệm KV mỗi token (fp16) | 8 KB | 24 KB | 12 KB |
| Bộ đệm KV cho 2.048 token | 16 MB | 48 MB | 24 MB |
| Bộ đệm RoPE lúc khởi tạo | ~16,8 MB | ~25,2 MB | ~25,2 MB |
| **RAM tối thiểu ước tính** | **~1 GB** | **~1,5 GB** | **~2 GB** |

Cách tính bộ đệm KV: `2 (K và V) × số_lớp × num_key_value_heads × head_dim ×
2 byte`. Với `nho`: `2 × 8 × 4 × 64 × 2 = 8.192` byte mỗi token.

Cách tính bộ đệm RoPE: `MiniMindModel.__init__` gọi `precompute_freqs_cis(dim=head_dim,
end=max_position_embeddings)` với `max_position_embeddings = 32768`, tạo hai
tensor float32 cỡ `(32768, head_dim)`. Với `nho` đó là `32768 × 64 × 4 × 2 =
16,8 MB` — **nhiều hơn 1/5 kích thước trọng số**, trên một mô hình 39M. Bộ đệm
này là `persistent=False` nên không nằm trong tệp `.pth`, chỉ chiếm RAM lúc chạy.
Con số này hay làm người ta bất ngờ nên ghi ra đây.

Cột "RAM tối thiểu" đã cộng thêm phần dôi cho PyTorch và activation, nhưng
**chưa đo** — activation phụ thuộc độ dài đầu vào. Coi nó là mức sàn để loại
trừ, không phải mức đảm bảo.

### GPU có cần không

Không, với `nho`. 75 MB trọng số chạy được trên CPU của máy tính xách tay thông
thường. **Tốc độ sinh chữ thì chưa đo** — không hứa số token/giây nào cho đến
khi có mô hình thật để bấm giờ.

Kinh nghiệm hạ tầng BDSG có liên quan: trên VPS, mô hình 7B chạy được **0,3
token/giây** vì nghẽn băng thông RAM (~1,4 GB/s). Mô hình ở đây nhỏ hơn 7B
khoảng 180 lần, nên tình huống đó không lặp lại — nhưng con số cụ thể vẫn phải
đo, không suy ra.

---

## 2. Cài đặt

```bash
git clone https://github.com/jingyaogong/minimind.git
cd minimind
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Bẫy 1 — `requirements.txt` KHÔNG cài torch.** Bốn dòng cuối tệp đó bị chú
thích lại:

```
# torch==2.6.0
# torchvision==0.21.0
# peft==0.7.1
# matplotlib==3.10.0
```

Cài riêng, chọn đúng bản cho máy mình (CPU hay CUDA) theo hướng dẫn trên
pytorch.org:

```bash
pip install torch          # bản CPU cho máy cá nhân
```

---

## 3. Đặt trọng số và từ vựng vào đúng chỗ

```
minimind/
├── model/
│   ├── tokenizer.json           <-- THAY bằng từ vựng BDSG
│   ├── tokenizer_config.json    <-- THAY bằng từ vựng BDSG
│   └── model_minimind.py
├── out/
│   └── full_sft_512.pth         <-- trọng số BDSG tải về
└── scripts/
    └── serve_openai_api.py
```

**Bẫy 2 — từ vựng bắt buộc nằm ở `model/`.** `trainer_utils.init_model` (dòng
121-122) có tham số `tokenizer_path='../model'` **cố định trong chữ ký hàm**, và
`train_pretrain.py` dòng 126 gọi nó mà không truyền đường dẫn khác. Để từ vựng
BDSG ở chỗ khác thì mô hình sẽ lặng lẽ dùng từ vựng tiếng Trung của MiniMind.

**Bẫy 3 — tên tệp trọng số được ghép theo `hidden_size`, không theo tên cấu
hình.** `train_pretrain.py` đặt tên là
`{save_dir}/{save_weight}_{hidden_size}{'_moe' nếu MoE}.pth`. Nghĩa là:

| Cấu hình | Tên tệp |
|---|---|
| `nho` (512) | `full_sft_512.pth` |
| `vua` (768, 16 lớp) | `full_sft_768.pth` |
| `moe` (768, 8 lớp, MoE) | `full_sft_768_moe.pth` |

Hai mô hình **khác số lớp nhưng cùng `hidden_size`** sẽ ghi đè lên nhau. Ở ba
cấu hình BDSG thì không đụng, nhưng ai thêm cấu hình thứ tư phải nhớ điều này.

---

## 4. Chạy máy chủ tương thích OpenAI

```bash
cd scripts
python serve_openai_api.py \
    --load_from ../model \
    --save_dir out \
    --weight full_sft \
    --hidden_size 512 \
    --num_hidden_layers 8 \
    --device cpu
```

Máy chủ lắng nghe ở **cổng 8998**.

**Bẫy 4 — phải chạy từ trong thư mục `scripts/`.** Bên trong, đường dẫn trọng số
được ghép cứng là `f'../{args.save_dir}/…'` (dòng 32). Chạy từ thư mục gốc dự án
sẽ tìm trọng số ở `../out` — tức là **bên ngoài** cả kho mã.

**Bẫy 5 — `--load_from` được xét bằng phép tìm chuỗi con.** Dòng 30:

```python
if 'model' in args.load_from:
```

Nếu bạn để mô hình định dạng transformers ở thư mục tên `bdsg-model-v1`, chuỗi
`'model'` nằm trong đó, nên nó nhảy vào nhánh "trọng số torch thuần" và đi tìm
tệp `.pth` không tồn tại. Đổi tên thư mục là xong, nhưng lỗi báo ra sẽ chẳng nói
gì về nguyên nhân thật.

**Bẫy 6 — trên CPU, `.half()` là sai.** Dòng 47:

```python
return model.half().eval().to(device)
```

fp16 được ép **không điều kiện**, kể cả khi `--device cpu`. PyTorch trên CPU
chạy fp16 rất chậm và một số phép còn chưa hỗ trợ. Với máy cá nhân, sửa dòng đó
thành:

```python
return (model.eval().to(device) if device == 'cpu'
        else model.half().eval().to(device))
```

Đổi lại là trọng số chiếm gấp đôi RAM (`nho`: 150 MB thay vì 75 MB) — vẫn thoải
mái trên máy cá nhân. **Chưa đo** chênh lệch tốc độ cụ thể trên máy thật.

**Bẫy 7 — `host="0.0.0.0"` (dòng 252) mở ra toàn bộ card mạng.** Ở quán cà phê
hay mạng công ty, ai trong cùng mạng cũng gọi được mô hình của bạn. Muốn chỉ máy
mình dùng thì sửa thành `host="127.0.0.1"`.

---

## 5. Gọi thử

```bash
curl http://127.0.0.1:8998/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bdsg",
    "messages": [{"role": "user", "content": "Ngành nghề kinh doanh chính là gì?"}],
    "stream": false
  }'
```

Vì đây là API tương thích OpenAI, mọi thư viện khách nói chuyện được với OpenAI
đều dùng được — chỉ cần đổi `base_url` sang `http://127.0.0.1:8998/v1`.

**Bẫy 8 — `scripts/chat_api.py` đi kèm KHÔNG trỏ vào máy chủ này.** Tệp đó đặt
`base_url="http://localhost:11434/v1"` (cổng của Ollama) và `model=
"minimind-local:latest"`. Nó được viết cho một cách triển khai khác. Muốn dùng
với `serve_openai_api.py` thì sửa hai dòng đó thành cổng `8998`.

Bật chế độ suy luận (mô hình sinh phần `<think>…</think>` trước khi trả lời):

```json
{"chat_template_kwargs": {"open_thinking": true}}
```

hoặc `{"open_thinking": true}` — máy chủ chấp nhận cả hai (xem
`ChatRequest.get_open_thinking`).

---

## 6. Trò chuyện thẳng trong terminal, không cần máy chủ

```bash
python eval_llm.py --load_from model --weight full_sft --hidden_size 512 --device cpu
```

Chạy từ **thư mục gốc** của MiniMind (khác với `serve_openai_api.py` — cái đó
phải chạy từ `scripts/`). `eval_llm.py` dòng 14 có **đúng cái bẫy chuỗi con**
như bẫy 5, và dòng 30 có **đúng cái `.half()`** như bẫy 6.

---

## 7. Đặt kỳ vọng cho đúng

Mô hình cỡ 39M–212M **không phải** trợ lý đa năng. MiniMind tự ghi trong tài
liệu của họ hai hạn chế, và chúng áp nguyên cho mô hình BDSG vì cùng kiến trúc,
cùng quy mô:

- **mô hình bịa ra kiến thức nó không có**;
- **độ ổn định về sự thật giảm sau khi học tăng cường**.

Đường cơ sở BDSG đo được (bộ M3, 227 câu, 22/09/2026) — đây là số của **hệ truy
hồi + mô hình bên thứ ba** đang chạy, **không phải** của mô hình sẽ huấn luyện:

| Nhóm câu | Điểm | Số câu |
|---|---:|---:|
| Nghiệp vụ trong kho | 0,636 | 111 |
| Nghiệp vụ ngoài kho | 0,539 | 31 |
| Lợi ích của truy hồi | +0,097 | — |
| Câu bẫy chống bịa | 0,953 | 60 |
| Tiếng Việt tổng quát | 0,908 | 25 |

Mô hình 39M huấn luyện từ đầu **gần như chắc chắn sẽ thấp hơn các số này** ở
giai đoạn đầu. Đó không phải thất bại — đó là điều đã biết trước khi bắt đầu.
Giá trị của mô hình nhỏ chạy cục bộ nằm ở chỗ **dữ liệu không rời khỏi máy** và
**không tốn tiền gọi API**, không nằm ở chỗ nó khôn hơn.

Khi có trọng số thật, mọi con số ở trang này phải được **đo lại và thay**, kèm
ngày đo.
