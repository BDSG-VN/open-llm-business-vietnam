# Backend Gemma 4 31B — trợ lý AI nội bộ chạy trên máy của BDSG

Viết ngày **26/09/2026**. Tài liệu gốc cho phần `trien-khai/`.

Tài liệu này nói về **một backend phục vụ trọng số của Google**. Nó **không** nói về mô
hình nhỏ do BDSG tự huấn luyện — hai thứ ấy là hai nhánh riêng, và mục
[§5 Ai sở hữu cái gì](#5-ai-so-huu-cai-gi) giữ ranh giới đó. Ai chỉ đọc được một mục thì
đọc mục ấy.

---

## Mục lục

- [0 · Trạng thái đo được hôm nay](#0-trang-thai-do-duoc-hom-nay)
- [1 · Ghi công Google](#1-ghi-cong-google)
- [2 · Thông số mô hình](#2-thong-so-mo-hinh)
- [3 · Bộ nhớ: bảng TÍNH RA, chưa đo](#3-bo-nho-bang-tinh-ra-chua-do)
- [4 · ⚠ Cảnh báo lượng tử hoá và gọi công cụ](#4-canh-bao-luong-tu-hoa-va-goi-cong-cu)
- [5 · Ai sở hữu cái gì](#5-ai-so-huu-cai-gi)
- [6 · Khởi động nội bộ](#6-khoi-dong-noi-bo)
- [7 · Điểm nối với giao diện chat](#7-diem-noi-voi-giao-dien-chat)
- [8 · Điểm nối RAG theo quyền truy cập — THIẾT KẾ, chưa cài](#8-diem-noi-rag-theo-quyen-truy-cap-thiet-ke-chua-cai)
- [9 · Đề xuất cấu hình máy](#9-de-xuat-cau-hinh-may)
- [10 · CHƯA ĐO — danh sách đầy đủ](#10-chua-do-danh-sach-day-du)

---

<a id="0-trang-thai-do-duoc-hom-nay"></a>

## 0 · Trạng thái đo được hôm nay

Bảng này đứng đầu **có chủ ý**. Phần sau mô tả một backend; bảng này nói backend ấy hiện
đứng ở đâu. Đọc ngược thứ tự thì rất dễ tưởng mọi thứ đã chạy.

| Hạng mục | Trạng thái | Số đo | Đo ngày |
|---|---|---|---|
| Thông số mô hình tra từ nguồn Google | **ĐÃ TRA** | xem [§2](#2-thong-so-mo-hinh) | 26/09/2026 |
| Kịch bản khởi động `trien-khai/chay-vllm.sh` | **ĐÃ CÓ** | 45 phép tự kiểm, chạy thật, ĐẠT 45/45 | 26/09/2026 |
| Phần kiểm trước khi chạy | **ĐÃ CHẠY THẬT** | lần chạy mặc định trên máy không GPU chặn **4 vấn đề**, mã thoát 1 | 26/09/2026 |
| Cài `vllm` | **CHƯA LÀM ĐƯỢC** | máy soạn là macOS arm64, không CUDA | 26/09/2026 |
| Nạp trọng số Gemma 4 31B | **CHƯA LÀM** | chưa tải, chưa nạp lần nào | chưa đo |
| Độ trễ, thông lượng, số yêu cầu đồng thời | **CHƯA ĐO** | không có GPU để đo | chưa đo |
| Ước tính VRAM | **TÍNH RA, KHÔNG PHẢI ĐO** | [§3](#3-bo-nho-bang-tinh-ra-chua-do) | 26/09/2026 |
| Đăng nhập / phân quyền người dùng | **CHƯA CÓ** | chỉ demo MỘT NGƯỜI trên localhost | 26/09/2026 |
| RAG tài liệu doanh nghiệp — **phía tài liệu này** | **MỚI LÀ THIẾT KẾ** | bốn ràng buộc ở [§8](#8-diem-noi-rag-theo-quyen-truy-cap-thiet-ke-chua-cai); phần cài nằm ở `phuc-vu/`, **đọc trạng thái tại đó** | 26/09/2026 |

> **Bản này CHƯA CÓ ĐĂNG NHẬP.** Mặc định nghe `127.0.0.1`, và đó là mặc định có chủ ý.
> Chừng nào chưa có lớp xác thực thì đây là **bản demo một người chạy trên máy của chính
> mình** — **chưa dùng được cho nhiều nhân viên**. Không có "ai đã hỏi gì", không có hạn
> mức theo người, không có cách tách hội thoại của người này khỏi người kia.

---

<a id="1-ghi-cong-google"></a>

## 1 · Ghi công Google

**Trọng số là của Google DeepMind. BDSG không huấn luyện chúng, không sở hữu chúng, và
không được nói khác đi.**

| Thứ | Nguồn |
|---|---|
| Trọng số bản chat (instruction-tuned) | `https://huggingface.co/google/gemma-4-31B-it` |
| Trọng số bản nền | `https://huggingface.co/google/gemma-4-31B` |
| Mã triển khai của Google | `https://github.com/google-deepmind/gemma` |
| Định nghĩa kiến trúc 31B | `https://github.com/google-deepmind/gemma/blob/main/gemma/gm/nn/gemma4/_gemma4.py` |
| Bài báo | arXiv:2607.02770 |
| **Giấy phép trọng số** | **Apache-2.0** — tra ngày 26/09/2026, và `gated = false` |

**Apache-2.0 là điểm khác hẳn so với Gemma 1–3.** Ba thế hệ trước phát hành theo *giấy
phép riêng của Gemma* kèm điều khoản sử dụng riêng. Gemma 4 dùng Apache-2.0 — cùng giấy
phép với mã trong kho này. Hệ quả thực tế: dùng thương mại được, không phải xin phép, và
nghĩa vụ chính còn lại là **giữ ghi công và nêu rõ chỗ đã sửa** (Apache-2.0 điều 4).

Tài liệu này và `trien-khai/` là chỗ giữ ghi công ấy. Đừng gỡ.

Họ Gemma 4 gồm bốn bản: **E2B · E4B · 26B MoE · 31B Dense**. Kho này phục vụ bản **31B
Dense**.

---

<a id="2-thong-so-mo-hinh"></a>

## 2 · Thông số mô hình

Tra ngày **26/09/2026** từ cấu hình Google công bố. **Không thêm con số nào ngoài bảng
này**; thứ không có ở đây thì chưa tra, và phải ghi là chưa tra.

| Trường | Giá trị |
|---|---|
| Số tham số | **31.273.088.876** (31,27 tỷ), BF16 |
| Lớp kiến trúc | `Gemma4ForConditionalGeneration` · `model_type = "gemma4"` |
| Số lớp | 60 |
| Số đầu chú ý | 32 |
| Số đầu khoá/giá trị (KV) | 16 |
| Bề rộng ẩn | 5.376 |
| Bề rộng lớp trung gian | 21.504 |
| `head_dim` | 256 |
| `global_head_dim` | 512 |
| `attention_k_eq_v` | `true` |
| Kiểu lớp | **50 lớp cửa sổ trượt** (cửa sổ 1.024) **+ 10 lớp chú ý toàn cục** |
| Cỡ từ vựng | 262.144 |
| `max_position_embeddings` | 262.144 (ngữ cảnh 256K) |
| `final_logit_softcapping` | 30,0 |
| `hidden_activation` | `gelu_pytorch_tanh` |
| Đa phương thức | **có `vision_config`** (ảnh + chữ → chữ) · `audio_config = null` ở bản 31B |
| Giấy phép | Apache-2.0 · `gated = false` |

Về phía máy phục vụ: **vLLM hỗ trợ kiến trúc `gemma4` từ bản 0.19.0**, phát hành
**02/04/2026** — cùng ngày Google công bố Gemma 4. Bản mới nhất khi soạn tài liệu này là
**0.24.0** (30/06/2026). Bản cũ hơn 0.19.0 báo "kiến trúc không được hỗ trợ", và câu báo
ấy **không nhắc gì tới phiên bản** — nên `chay-vllm.sh` kiểm số này trước khi chạy.

---

<a id="3-bo-nho-bang-tinh-ra-chua-do"></a>

## 3 · Bộ nhớ: bảng TÍNH RA, chưa đo

**Mọi con số trong mục này là SỐ TÍNH RA từ số tham số và cấu hình ở §2. Không có số nào
được đo trên GPU thật**, vì dự án chưa có GPU. Tự chạy lại:
`trien-khai/chay-vllm.sh --tu-kiem`.

> **Mỗi con số in trong ba bảng dưới đây đều có một dòng khoá trong `--tu-kiem`** (nhóm
> `3a` và `4a`), thêm ngày **26/09/2026**. Vì sao phải khoá đúng giá trị chứ không chỉ khoá
> khoảng: bản đầu của bài tự kiểm chỉ kiểm thứ tự và khoảng, và phép thử ngược cho thấy khi
> ấy đảo `SO_LOP_TRUOT`/`SO_LOP_TOAN` làm KV ở 8K nhảy từ 3.360 lên 12.960 MiB mà bài tự
> kiểm **vẫn ĐẠT toàn bộ, mã thoát 0** — cổng xanh trong khi bảng dưới đây đã sai. Sửa hằng
> số mô hình mà quên sửa bảng thì bây giờ hỏng ở cổng, không hỏng lặng lẽ trong đầu người
> đọc.

### 3.1 Trọng số

| Mức | Byte/tham số (ước tính) | TÍNH RA | Vừa card nào |
|---|---|---|---|
| BF16 (không lượng tử hoá) | 2,00 | **59.648 MiB** ≈ 58,3 GiB ≈ 62,5 GB | **không** vừa card 32 GB hay 48 GB |
| FP8 | 1,05 (1 byte + ~5% hệ số tỉ lệ) | **31.315 MiB** ≈ 30,6 GiB ≈ 32,8 GB | vừa sát card 32 GB, **không còn chỗ cho KV cache** |
| INT4 (AWQ/GPTQ) | 0,60 (0,5 byte + hệ số và điểm không theo nhóm) | **17.894 MiB** ≈ 17,5 GiB ≈ 18,8 GB | vừa card 24 GB, thoải mái trên 32 GB |

### 3.2 KV cache — chỗ ngữ cảnh 256K giết máy

Công thức, viết ra để ai cũng kiểm lại được:

- **50 lớp cửa sổ trượt**: KV bị **chặn ở 1.024 token**. Ngữ cảnh dài hơn cũng không tốn
  thêm ở các lớp này.
- **10 lớp chú ý toàn cục**: KV lớn **tuyến tính** theo độ dài ngữ cảnh. Đây là toàn bộ
  nguyên nhân của bảng dưới.
- Mỗi token, mỗi lớp = 2 (K và V) × 16 đầu KV × `head_dim` × 2 byte (BF16).

Cho **một** chuỗi, KV cache BF16:

| Ngữ cảnh | TÍNH RA |
|---|---|
| 4.096 | 2.080 MiB (2,0 GiB) |
| **8.192** (mặc định của kho này) | **3.360 MiB (3,3 GiB)** |
| 16.384 | 5.920 MiB (5,8 GiB) |
| 32.768 | 11.040 MiB (10,8 GiB) |
| 65.536 | 21.280 MiB (20,8 GiB) |
| 131.072 | 41.760 MiB (40,8 GiB) |
| **262.144 (256K)** | **82.720 MiB (80,8 GiB)** — **nhiều hơn cả trọng số BF16** |

Nhân tiếp với số chuỗi đồng thời. **Ngữ cảnh 256K với 4 chuỗi cần ~323 GiB riêng cho KV
cache** — đó là lý do `chay-vllm.sh` **không** lấy 262144 làm mặc định cho
`--max-model-len`, và là lý do mặc định là 8.192.

**Hai chỗ bảng này có thể cao hơn thực tế — nói ra đúng hơn giấu:**

1. Cấu hình khai `attention_k_eq_v = true`. Nếu điều đó nghĩa là K và V dùng chung một
   tensor thì phần KV **chỉ bằng một nửa** bảng trên. Chưa kiểm chứng được cách vLLM cài,
   nên ở đây tính K và V tách rời — tức tính về phía **an toàn**: thừa bộ nhớ thì vẫn
   chạy, thiếu thì chết giữa chừng.
2. vLLM cấp KV cache theo khối và cấp trước theo phần VRAM còn trống, chứ không cấp đúng
   bằng nhu cầu. Bảng trên là **nhu cầu**, không phải mức cấp.

### 3.3 Tổng cần, chạy thật bằng `--chi-kiem` ngày 26/09/2026

BF16, ngữ cảnh 8.192, đã cộng 2.048 MiB dự phòng (khoản chừa theo kinh nghiệm, **chưa đo**):

| Số chuỗi đồng thời | Tổng cần | Một card 80 GB ở mức 0,90 cho dùng 73.403 MiB |
|---|---|---|
| 1 | 65.056 MiB | vừa |
| **2 (mặc định)** | **68.416 MiB** | **vừa, dư ~5 GiB** |
| 3 | 71.776 MiB | vừa, sát |
| 4 | 75.136 MiB | **KHÔNG vừa** — thiếu ~1.700 MiB |
| 8 | 88.576 MiB | không vừa |

> Dòng "4 chuỗi" là **một con số đã bị sửa**, ghi lại để người sau đừng đặt lại như cũ.
> Bản đầu của `cau-hinh.mau.env` ghi mặc định 4 kèm câu "vừa một card 80 GB". Chạy phép
> tính ra thì sai: thiếu ~1.700 MiB. Kiểu thiếu ấy không hỏng lúc khởi động mà hỏng lúc
> tải đỉnh — tức hỏng vào đúng lúc khó chẩn đoán nhất.

---

<a id="4-canh-bao-luong-tu-hoa-va-goi-cong-cu"></a>

## 4 · ⚠ Cảnh báo lượng tử hoá và gọi công cụ

**Đọc mục này trước khi đặt `LUONG_TU_HOA`.**

Bảng §3.1 làm INT4 trông như một món hời: 18,8 GB thay vì 62,5 GB, vừa một card 24 GB.
Cái giá thì không nằm ở chỗ người ta hay nhìn.

Phiên tra cứu **26/09/2026** đo được rằng **năng lực GỌI CÔNG CỤ nhạy với lượng tử hoá
gấp khoảng 70 lần so với trả lời chữ thường**:

> **Gemma-3 12B ở Q4_K_M rớt từ 91,3% xuống 69,0% trên BFCL — giảm 22,3 điểm.**

Ba điều phải nói cho đủ, vì một cảnh báo bị tin quá mức cũng hại như không có cảnh báo:

1. **Số đó là của Gemma-3 12B, không phải Gemma 4 31B.** Độ nhạy này **phụ thuộc họ mô
   hình**. Không được chép con số 22,3 điểm sang Gemma 4 như thể đã đo.
2. **Chưa ai đo Gemma 4 ở INT4 cho gọi công cụ.** Tại 26/09/2026 không có số để trích.
3. Vì hai điều trên, **chạy 31B ở INT4 là một RỦI RO ĐÃ BIẾT, không phải một ẩn số**. Khác
   nhau ở chỗ: ẩn số thì có thể bỏ qua, rủi ro đã biết thì phải đo trước khi hứa.

**Quy tắc cho dự án này:** trợ lý nội bộ mà mất năng lực gọi công cụ thì mất luôn phần
đáng giá nhất — nó không truy hồi được tài liệu, không gọi được API nội bộ, chỉ còn tán
gẫu. Nên:

- Mặc định **không lượng tử hoá**. Thiếu VRAM thì giảm ngữ cảnh và số chuỗi đồng thời
  **trước**, lượng tử hoá **sau cùng**.
- Bật lượng tử hoá thì **phải đo gọi công cụ trước và sau**, trên cùng bộ đề. Đo tiếng
  Việt thôi là không đủ: phần rớt nằm ở chỗ khác.
- Chưa đo thì **không được nói với người dùng rằng bản lượng tử hoá "vẫn tốt"**.

---

<a id="5-ai-so-huu-cai-gi"></a>

## 5 · Ai sở hữu cái gì

Đây là mục quan trọng nhất của tài liệu, và nó tồn tại vì ranh giới này rất dễ bị xoá
bằng một cái tên đặt cho tiện.

| Thứ | Của ai | Giấy phép |
|---|---|---|
| **Trọng số Gemma 4 31B** | **Google DeepMind** | Apache-2.0 |
| Tokenizer và chat template của Gemma 4 | **Google DeepMind** | Apache-2.0, đi kèm kho trọng số |
| Mã trong `trien-khai/` (kịch bản, cấu hình, tài liệu này) | BDSG | Apache-2.0 |
| Kiến trúc mô hình nhỏ trong `mo-hinh/`, bộ huấn luyện `huan-luyen/` | BDSG, viết độc lập từ bài báo | Apache-2.0 |
| Bộ từ vựng 6.400 token, ngữ liệu trong `bo-du-lieu/` | BDSG | CC BY 4.0 cho dữ liệu |

**BDSG PHỤC VỤ trọng số của Google. BDSG KHÔNG huấn luyện chúng.** Câu ấy có ba hệ quả
bắt buộc:

1. **`bdsg_la_trong_so_bdsg` phải là `false`** ở mọi chỗ khai ra ngoài, cho trọng số
   Google nguyên bản. Chỉ đặt `true` khi **chính BDSG** huấn luyện ra tệp trọng số đang
   nạp. Không có ngoại lệ, và cái tên "đã tinh chỉnh một ít" không phải ngoại lệ.
2. **Không đặt tên phục vụ có chữ "bdsg" cho trọng số Google nguyên bản.** Tên ở
   `--served-model-name` hiện ra tại `/v1/models` và tại nhãn "câu trả lời đến từ …" trên
   giao diện. `chay-vllm.sh` **chặn** việc này bằng hàm `kiem_ten_phuc_vu()`, và phép chặn
   ấy có bài thử ngược.
3. **Hai nhánh không được trộn.** Mô hình nhỏ của BDSG (26.878.464 tham số, từ vựng 6.400
   token) là **một nhánh nghiên cứu riêng**. Cụ thể là hai điều cấm, cả hai đều làm hỏng
   mô hình một cách lặng lẽ:
   - **Không nạp trọng số Gemma 4 vào kiến trúc của `mo-hinh/`.** Hai kiến trúc khác nhau
     ở gần như mọi chiều (60 lớp vs. cấu hình nhỏ; `head_dim` 256/512; 50+10 lớp trượt và
     toàn cục; `final_logit_softcapping`). Trọng số nạp vào sai kiến trúc thì hoặc báo lỗi
     hình dạng, hoặc — tệ hơn — nạp được một phần rồi sinh ra chữ vô nghĩa.
   - **Không thay tokenizer/chat template gốc của Gemma bằng bộ từ vựng 6.400 của BDSG.**
     Gemma 4 có từ vựng 262.144. Đổi tokenizer là đổi ý nghĩa của từng mã token mà mô hình
     đã học — kết quả là chữ vô nghĩa, và không có thông báo lỗi nào.

---

<a id="6-khoi-dong-noi-bo"></a>

## 6 · Khởi động nội bộ

```bash
# 1. Chép cấu hình mẫu ra rồi sửa. Bản mẫu KHÔNG chứa bí mật nào.
cp trien-khai/cau-hinh.mau.env cau-hinh.env
$EDITOR cau-hinh.env

# 2. Kiểm trước. Bước này KHÔNG khởi động gì, chỉ trả lời "chạy được hay không, vì sao".
set -a; . ./cau-hinh.env; set +a
trien-khai/chay-vllm.sh --chi-kiem

# 3. Đạt hết thì chạy thật.
trien-khai/chay-vllm.sh
```

Hai lệnh nữa, dùng khi cần:

```bash
trien-khai/chay-vllm.sh --tu-kiem   # thử ngược các hàm tính, CHẠY ĐƯỢC KHÔNG CẦN GPU
trien-khai/chay-vllm.sh --in-lenh   # kiểm xong thì in lệnh vllm ra, không khởi động
```

**Kịch bản dừng — chứ không chạy rồi hỏng giữa chừng — khi:** không biết lấy trọng số ở
đâu · tên phục vụ khai sai quyền sở hữu · không nạp được vLLM hoặc vLLM cũ hơn 0.19.0 ·
không thấy `nvidia-smi` · VRAM tính ra không đủ · `--max-model-len` vượt 262.144.

> **Phép kiểm VRAM đếm đúng số card ĐƯỢC DÙNG, không đếm cả máy.** vLLM chỉ trải mô hình
> lên `SO_GPU_SONG_SONG` card; VRAM của các card còn lại không được cộng vào. Bản đầu của
> kịch bản cộng tổng mọi card, nên một máy 4 × 24 GB chạy `SO_GPU_SONG_SONG=1` đi qua cổng
> (88.473 MiB "dùng được" > 68.416 MiB cần) rồi hết bộ nhớ lúc nạp — trái hẳn dòng
> "1 × 24 GB: chỉ INT4" ở [§9](#9-de-xuat-cau-hinh-may). Sửa **26/09/2026**; nhóm `4b` của
> `--tu-kiem` khoá lại đúng ca ấy. Máy trộn nhiều cỡ card thì lấy **card nhỏ nhất** trong
> nhóm, vì tensor parallel chia đều nên card nhỏ nhất là chỗ thắt.

**Ba điều kịch bản không làm, và đừng thêm vào:**

- **Không tải trọng số.** Mặc định đòi trọng số có sẵn trên đĩa. Muốn vLLM tự kéo thì phải
  bật tường minh `CHO_PHEP_TAI_TRONG_SO=co` — vì lỡ tay tải 62,5 GB là một tai nạn.
- **Không ghi token vào đâu cả.** Token đọc từ biến môi trường, không in ra, không có giá
  trị mặc định.
- **Không có đường dự phòng ra nhà cung cấp bên ngoài.** Máy nội bộ hỏng thì **báo lỗi rõ
  ràng và dừng**. Một chuỗi "cục bộ trước, đám mây sau" phá đúng thứ hệ này hứa: người
  dùng tưởng đang chạy cục bộ, còn câu hỏi thì âm thầm đi ra ngoài. Đó không phải tính
  năng dự phòng, đó là rò rỉ dữ liệu có hẹn giờ.

---

<a id="7-diem-noi-voi-giao-dien-chat"></a>

## 7 · Điểm nối với giao diện chat

Giao diện trong `chat/` gọi **năm** đường, và hợp đồng đầy đủ nằm ở
[`../chat/README.md`](../chat/README.md) — **đọc tệp đó trước khi viết máy chủ**, đừng
viết theo trí nhớ.

| Đường | Việc |
|---|---|
| `GET /api/mo-hinh` | trả `moHinh`, `mucNoLuc`, `mucNoLucMacDinh`, và **`danhSach` (bắt buộc)** |
| `POST /api/hoi` | `text/event-stream`, bốn sự kiện: `batdau` · `chu` · `loi` · `xong` |
| `GET /api/hoi-thoai` | liệt kê hội thoại |
| `GET /api/hoi-thoai/:id` | đọc một hội thoại |
| `DELETE /api/hoi-thoai/:id` | `{"daXoa": true}` hoặc **404** |

Bốn chỗ dễ làm sai, ghi ra vì mỗi chỗ đều hỏng theo kiểu khó thấy:

1. **`danhSach` không được bỏ.** Giao diện dùng nó để đổi mã mô hình thành tên người đọc
   được. Bỏ đi thì nhãn "câu trả lời đến từ …" hiện ra mã trần — hỏng đúng tại chỗ có
   nhiệm vụ chống khai sai tên mô hình.
2. **`moHinhThat` trong sự kiện `xong` phải là tên THẬT đã sinh ra câu trả lời**, không
   phải tên người dùng đã chọn. Hai thứ ấy khác nhau khi máy chủ đổi mô hình giữa chừng,
   và đúng lúc ấy người đọc cần biết sự thật nhất.
3. **`trichDan` phải trỏ tới tài liệu đã thật sự được đưa vào lời nhắc.** Nhãn trích dẫn
   sống sót sau khi đoạn chữ bị cắt là một lỗi đã gặp ở dự án này: người đọc thấy nguồn,
   mô hình thì chưa từng đọc nguồn ấy.
4. **`DELETE` trả 404 cho cả "không có" lẫn "của người khác".** Trả 403 là nói "có thứ đó,
   bạn không được đụng" — tức cho người lạ một cách dò xem một mã hội thoại có tồn tại hay
   không.

**Phần máy chủ nối vLLM vào năm đường này KHÔNG thuộc đợt làm của tài liệu này.** Đợt này
chỉ có `trien-khai/` và tài liệu.

Một thư mục `phuc-vu/` đã xuất hiện trong kho ngày 26/09/2026, cùng
[`RAG-PHAN-QUYEN.md`](RAG-PHAN-QUYEN.md). **Tài liệu này không khẳng định thay trạng thái
của chúng** — theo đúng luật chung của kho: trạng thái của một thư mục chỉ có ở tệp trong
chính thư mục đó, vì tài liệu ở nơi khác lạc hậu ngay lần sửa sau. Đừng đọc tài liệu này
rồi kết luận rằng đường chạy từ giao diện tới Gemma đã thông; hãy chạy bài tự kiểm trong
thư mục ấy và đọc kết quả.

---

<a id="8-diem-noi-rag-theo-quyen-truy-cap-thiet-ke-chua-cai"></a>

## 8 · Điểm nối RAG theo quyền truy cập — THIẾT KẾ, chưa cài

> **Chưa có kiểm thử đầu cuối ⇒ KHÔNG được nói là "đã chạy RAG".** Mục này là **thiết kế**
> đứng từ phía backend, và nó nằm ở đây để phần cài không phải nghĩ lại từ đầu.
>
> Ngày 26/09/2026 kho có thêm `phuc-vu/rag.py`, `phuc-vu/thu_rag.py` và
> [`RAG-PHAN-QUYEN.md`](RAG-PHAN-QUYEN.md). **Mục này không khẳng định thay trạng thái của
> chúng** — chạy bài tự kiểm ở đó rồi đọc kết quả tại chỗ. Bốn ràng buộc dưới đây là thứ
> phần cài phải thoả, bất kể ai cài.

Bốn ràng buộc, theo thứ tự quan trọng:

1. **Quyền lọc TRƯỚC khi truy hồi, không phải sau.** Truy hồi trước rồi lọc sau thì đoạn
   tài liệu ngoài quyền đã nằm trong bộ nhớ tiến trình, và chỉ cần một lần ghi nhật ký
   hoặc một thông báo lỗi là nó lộ ra. Điều kiện quyền phải nằm **trong chính câu truy
   vấn** — cùng lập luận với luật "đặt điều kiện sở hữu trong chính câu lệnh xoá" ở
   `chat/README.md`.
2. **Quyền theo từng người và từng tài liệu**, không phải theo từng thư mục. Một tài liệu
   đổi chỗ không được làm đổi quyền của nó.
3. **Từ chối tài liệu ngoài quyền phải giống hệt "không tìm thấy".** Câu trả lời "có tài
   liệu ấy nhưng bạn không được đọc" là một kênh dò: hỏi đủ nhiều thì dựng lại được danh
   mục tài liệu mật.
4. **Dữ liệu ở lại máy nội bộ.** Không có bước nào gửi đoạn tài liệu ra ngoài — kể cả để
   tính vector nhúng. Mô hình nhúng cũng phải chạy nội bộ, nếu không thì toàn bộ điểm của
   việc tự phục vụ mô hình đã mất.

Ba điều **không** được làm:

- Không đưa tài liệu khách hàng vào bộ dữ liệu mở `bo-du-lieu/`. Ranh giới ấy đã được
  `.gitignore` và bảy cổng trong `cong/` giữ; đừng mở ra vì tiện.
- Không công bố số đo chất lượng RAG trước khi có kiểm thử đầu cuối chạy thật.
- Không dùng `trichDan` như đồ trang trí. Xem điểm 3 ở [§7](#7-diem-noi-voi-giao-dien-chat).

---

<a id="9-de-xuat-cau-hinh-may"></a>

## 9 · Đề xuất cấu hình máy

**Dựa trên phép TÍNH ở §3, không dựa trên phép đo.** Chưa có GPU nào được chạy thử, nên
mọi dòng dưới đây phải đọc kèm chữ "tính ra".

| Cấu hình | Chạy được gì (tính ra) | Nhận xét |
|---|---|---|
| 1 × 80 GB (A100/H100) | BF16 · ngữ cảnh 8K · **2 chuỗi** đồng thời | Cấu hình **tối thiểu** để chạy BF16. Không còn chỗ cho ngữ cảnh dài. |
| 2 × 80 GB (`SO_GPU_SONG_SONG=2`) | BF16 · ngữ cảnh 32K · nhiều chuỗi hơn | **Khuyến nghị** cho một trợ lý nội bộ thật. |
| 1 × 141 GB (H200) | BF16 · ngữ cảnh 32K–64K | Một card, ít phức tạp hơn chia hai card. |
| 1 × 48 GB (L40S) | **không** chạy được BF16 (cần 58,3 GiB trọng số) | Buộc phải lượng tử hoá ⇒ đọc [§4](#4-canh-bao-luong-tu-hoa-va-goi-cong-cu) trước. |
| 1 × 24 GB | chỉ INT4, ngữ cảnh ngắn | Rủi ro gọi công cụ chưa đo. Không dùng cho bản phục vụ thật. |
| Máy không có GPU NVIDIA | **không chạy được** | Kể cả Apple Silicon. `chay-vllm.sh` dừng ở bước 4. |

Hai lời khuyên rút ra từ chính bảng §3.3:

- **Đừng mua theo con số "62,5 GB" rồi lấy card 64 GB.** Trọng số chỉ là một phần; KV
  cache và dự phòng đẩy tổng lên 65–75 GB ngay ở ngữ cảnh 8K.
- **Ngữ cảnh là thứ đắt hơn người ta tưởng.** Tăng 8K → 32K tốn thêm **7.680 MiB ≈ 7,5
  GiB** mỗi chuỗi (11.040 − 3.360, theo bảng §3.2).
  Đó thường là lý do đáng mua thêm VRAM hơn là để chạy nhiều chuỗi song song.

---

<a id="10-chua-do-danh-sach-day-du"></a>

## 10 · CHƯA ĐO — danh sách đầy đủ

Liệt kê ở đây để không ai phải đoán chỗ nào có số thật, chỗ nào không.

| Hạng mục | Vì sao chưa đo |
|---|---|
| Độ trễ token đầu tiên | chưa có GPU |
| Số token/giây khi sinh | chưa có GPU |
| Số yêu cầu đồng thời chịu được | chưa có GPU |
| VRAM thật vLLM chiếm khi nạp | chưa nạp lần nào |
| Thời gian nạp trọng số | chưa tải trọng số |
| Chất lượng tiếng Việt của Gemma 4 31B trên bộ 227 câu | chưa chạy |
| Năng lực gọi công cụ, BF16 và INT4 | chưa chạy — xem [§4](#4-canh-bao-luong-tu-hoa-va-goi-cong-cu) |
| `vllm` cài được hay không theo `yeu-cau.txt` | máy soạn là macOS arm64, không CUDA |
| Chất lượng và độ trễ RAG | mới là thiết kế, chưa cài |

Ô nào ở bảng này được điền thì **điền bằng số đo, kèm ngày và kèm cấu hình máy**. Một con
số không kèm ngày và không kèm máy thì không kiểm chứng lại được, và một con số không
kiểm chứng lại được thì về mặt khoa học không khác gì một con số bịa.

---

*Viết 26/09/2026. Trọng số Gemma 4 là của Google DeepMind, Apache-2.0 — xem
[§1](#1-ghi-cong-google). Mã trong `trien-khai/` là của BDSG, Apache-2.0. Mọi số VRAM
trong tài liệu này là số TÍNH RA; số nào chưa đo được ghi thẳng là chưa đo.*
