# Lộ trình tinh chỉnh LoRA/QLoRA cho Gemma 4 31B

Viết ngày **26/09/2026**. Đi kèm [`GEMMA4-31B.md`](GEMMA4-31B.md).

> **CHƯA CHẠY LẦN HUẤN LUYỆN NÀO.** Tài liệu này là lộ trình, không phải báo cáo. Mọi con
> số bộ nhớ ở đây là **TÍNH RA**; không có số nào đo trên GPU thật, vì dự án chưa có GPU
> (xem bảng "chi phí GPU: chưa đo" trong [`../README.md`](../README.md)).

---

## Mục lục

- [0 · Ba điều kiện BẮT BUỘC](#0-ba-dieu-kien-bat-buoc)
- [1 · ⚠ Cảnh báo lớn nhất: "làm giàu tiếng Việt" có thể giết năng lực gọi công cụ](#1-canh-bao-lon-nhat)
- [2 · Ước tính VRAM cho QLoRA trên 31B](#2-uoc-tinh-vram-cho-qlora-tren-31b)
- [3 · Bộ đánh giá trước/sau](#3-bo-danh-gia-truoc-sau)
- [4 · Trình tự một lần tinh chỉnh](#4-trinh-tu-mot-lan-tinh-chinh)
- [5 · Luật đặt tên và khai báo quyền sở hữu](#5-luat-dat-ten-va-khai-bao-quyen-so-huu)
- [6 · CHƯA ĐO](#6-chua-do)

---

<a id="0-ba-dieu-kien-bat-buoc"></a>

## 0 · Ba điều kiện BẮT BUỘC

**Thiếu MỘT trong ba là KHÔNG CHẠY.** Không có phiên bản rút gọn, không có "chạy thử cho
biết".

| # | Điều kiện | Thế nào là đủ | Trạng thái 26/09/2026 |
|---|---|---|---|
| 1 | **Có GPU** | GPU NVIDIA đã thuê hoặc đã có, đủ VRAM theo [§2](#2-uoc-tinh-vram-cho-qlora-tren-31b), truy cập được | **CHƯA CÓ** — dự án chưa thuê GPU lần nào |
| 2 | **Dữ liệu ĐƯỢC PHÉP dùng** | Từng nguồn có cơ sở pháp lý ghi ra được: tự sản xuất, được cấp phép, hoặc khách hàng đồng ý bằng văn bản | **CHƯA RÀ** cho mục đích tinh chỉnh |
| 3 | **Ngân sách ĐÃ XÁC NHẬN** | Chủ dự án duyệt một con số cụ thể, bằng chữ, trước khi bấm chạy | **CHƯA CÓ** |

Vì sao ba điều này là điều kiện chặn chứ không phải lời khuyên:

- **Điều kiện 2 là chỗ nguy hiểm nhất, và nó không tự báo lỗi.** Một lần huấn luyện bằng
  tài liệu khách hàng không được phép sẽ **không hỏng gì cả** — nó chạy xong, ra trọng số
  tốt, và cái sai chỉ lộ ra khi đã quá muộn để gỡ. Trọng số **không gỡ được** một tài liệu
  ra khỏi mình; cách duy nhất là bỏ trọng số và huấn luyện lại. Cho nên phép rà phải làm
  **trước**, không phải "để sau rồi kiểm".
  - Kho này đã có sẵn ranh giới ấy ở `bo-du-lieu/GIAY-PHEP-NGUON.md` và ở bảy cổng trong
    `cong/`. Dữ liệu tinh chỉnh phải qua **cùng** phép rà đó, không phải một phép rà lỏng
    hơn vì "chỉ để huấn luyện nội bộ".
  - **Tài liệu khách hàng không được đưa vào bộ dữ liệu mở.** Một lần tinh chỉnh nội bộ
    không mở ra quyền công bố dữ liệu ấy.
- **Điều kiện 3 tồn tại vì chi phí ở đây không tuyến tính với kỳ vọng.** Một lần QLoRA
  trên 31B không phải một lần thử — nó là giờ GPU thật, và một lần chạy hỏng vì cấu hình
  sai vẫn tính đủ tiền.

---

<a id="1-canh-bao-lon-nhat"></a>

## 1 · ⚠ Cảnh báo lớn nhất: "làm giàu tiếng Việt" có thể giết năng lực gọi công cụ

**Đọc mục này trước khi viết dòng cấu hình huấn luyện đầu tiên.**

Ý định tự nhiên nhất khi có trong tay một mô hình đa ngữ là: *tinh chỉnh bằng dữ liệu
tiếng Việt thuần để nó giỏi tiếng Việt hơn*. Phiên tra cứu **26/09/2026** cho thấy ý định
ấy có một cái giá mà phép đo tiếng Việt **không nhìn thấy**.

Số đo làm cơ sở — của **Gemma-3 12B ở Q4_K_M**, tức lượng tử hoá chứ không phải tinh chỉnh:

> **91,3% → 69,0% trên BFCL (gọi công cụ), giảm 22,3 điểm**, trong khi chất lượng trả lời
> chữ thường gần như không đổi. Tỉ lệ nhạy: **~70 lần**.

Điều số đo ấy chứng minh — và điều nó **không** chứng minh:

- **Chứng minh:** năng lực gọi công cụ là một năng lực **mỏng và dễ vỡ**, nằm ở chỗ khác
  với năng lực ngôn ngữ, và một phép đo ngôn ngữ **không phát hiện được** khi nó vỡ.
- **KHÔNG chứng minh:** rằng tinh chỉnh tiếng Việt sẽ làm rớt đúng 22,3 điểm. Con số ấy là
  của một mô hình khác, một họ khác, và một tác nhân khác (lượng tử hoá, không phải tinh
  chỉnh). **Chép nó sang đây như một dự báo là bịa số.**

Lập luận nối hai chuyện lại: tinh chỉnh bằng dữ liệu **một lĩnh vực, một ngôn ngữ, không
có ví dụ gọi công cụ** là một sức ép đẩy phân bố đi khỏi chỗ năng lực mỏng ấy đang nằm.
Cơ chế khác lượng tử hoá, nhưng **chỗ vỡ thì cùng một chỗ**.

**Quy tắc bắt buộc, không có ngoại lệ:**

1. **Đo gọi công cụ TRƯỚC và SAU mỗi lần tinh chỉnh.** Không chỉ đo tiếng Việt. Một lần
   tinh chỉnh làm tiếng Việt tăng 5 điểm và gọi công cụ rớt 20 điểm là một lần **thất
   bại** — dù bảng tiếng Việt trông rất đẹp.
2. **Bộ đề gọi công cụ phải đóng băng trước khi chạy**, cùng nguyên tắc với bộ 227 câu:
   bộ đề sửa được sau khi nhìn điểm thì không còn là thước đo, nó thành cái gương.
3. **Trộn ví dụ gọi công cụ vào dữ liệu tinh chỉnh**, đừng chỉ đưa văn bản tiếng Việt
   thuần. Đây là cách giữ, không phải cách chữa — chữa thì phải huấn luyện lại.
4. **Chưa đo thì không được nói bản tinh chỉnh "vẫn dùng được như cũ".**

---

<a id="2-uoc-tinh-vram-cho-qlora-tren-31b"></a>

## 2 · Ước tính VRAM cho QLoRA trên 31B

**TÍNH RA, chưa đo.** Số tham số LoRA dưới đây tính thật bằng máy ngày 26/09/2026 từ cấu
hình ở [`GEMMA4-31B.md` §2](GEMMA4-31B.md#2-thong-so-mo-hinh), giả định bộ đặt gắn vào bốn
phép chiếu chú ý (`q`, `k`, `v`, `o`) ở **cả 60 lớp**.

Nhắc lại hai chi tiết làm phép tính này khác một mô hình thường: 50 lớp dùng `head_dim`
256, còn 10 lớp chú ý toàn cục dùng `global_head_dim` **512** — nên các lớp toàn cục tốn
gần gấp đôi.

| Hạng `r` | Tham số LoRA | % của 31,27 tỷ | Bộ đặt (BF16) | Gradient | Trạng thái Adam (fp32) | Cộng |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 24.084.480 | 0,077% | 45,9 MiB | 45,9 MiB | 183,8 MiB | **275,6 MiB** |
| **16** | **48.168.960** | **0,154%** | 91,9 MiB | 91,9 MiB | 367,5 MiB | **551,2 MiB** |
| 32 | 96.337.920 | 0,308% | 183,8 MiB | 183,8 MiB | 735,0 MiB | **1.102,5 MiB** |
| 64 | 192.675.840 | 0,616% | 367,5 MiB | 367,5 MiB | 1.470,0 MiB | **2.205,0 MiB** |

Cộng với mô hình nền nén 4-bit (0,60 byte/tham số — cùng ước tính với
[`GEMMA4-31B.md` §3.1](GEMMA4-31B.md#3-bo-nho-bang-tinh-ra-chua-do)): **17.895 MiB ≈ 17,5 GiB**.

| Cấu hình | Nền + bộ đặt + gradient + Adam | **CHƯA** gồm |
|---|---|---|
| QLoRA `r=16` | **18.446 MiB ≈ 18,0 GiB** | kích hoạt |
| QLoRA `r=64` | **20.100 MiB ≈ 19,6 GiB** | kích hoạt |

> **Phần thiếu của bảng này là phần lớn nhất, và phải nói thẳng: KÍCH HOẠT CHƯA TÍNH.**
> Bộ nhớ kích hoạt phụ thuộc độ dài chuỗi, cỡ lô, và có bật tái tính kích hoạt (gradient
> checkpointing) hay không — ba thứ chưa chốt. Với chuỗi dài, phần này **có thể lớn hơn cả
> phần đã tính ở trên**.
>
> Cho nên: **đừng đọc "18 GiB" rồi đi mua card 24 GB.** Con số dùng để lập kế hoạch là
> **48 GB trở lên**, và con số thật phải đo ở lần chạy đầu tiên.

Ba núm vặn khi thiếu VRAM, theo thứ tự nên thử:

1. **Bật tái tính kích hoạt.** Đổi bộ nhớ lấy thời gian — thường là đổi đáng giá nhất.
2. **Giảm độ dài chuỗi huấn luyện**, rồi mới giảm cỡ lô (bù bằng tích luỹ gradient).
3. **Giảm hạng `r`.** Để sau cùng: đây là núm duy nhất làm giảm sức học của bộ đặt.

---

<a id="3-bo-danh-gia-truoc-sau"></a>

## 3 · Bộ đánh giá trước/sau

### 3.1 Tiếng Việt — dùng bộ 227 câu đã có

Bộ đề nằm ở [`../danh-gia/`](../danh-gia/), gồm **227 câu, 4 nhóm**, đóng băng từ
22/09/2026 (`danh-gia/README.md` khai "Bốn nhóm câu hỏi"; bảng dưới cộng đúng 227):

| Nhóm | Số câu | Đo cái gì |
|---|---:|---|
| Nghiệp vụ **trong kho** | 111 | lấy đúng thông tin có sẵn |
| Nghiệp vụ **ngoài kho** | 31 | trả lời bằng kiến thức nền, hoặc nói thẳng là không biết |
| **Câu bẫy chống bịa** | 60 | **từ chối bịa** — điểm cao nghĩa là nói "không có" đúng lúc |
| Tiếng Việt tổng quát | 25 | viết tiếng Việt đúng và tự nhiên |

> ⚠ **`danh-gia/README.md` ghi rõ một TODO chặn phát hành: bộ đề CHƯA nằm trong kho, và
> bộ chạy đánh giá CHƯA có.** Đọc tệp ấy trước, đừng tin tài liệu này về trạng thái của
> thư mục khác. Chừng nào chưa có bộ đề và bộ chạy thì **không có phép đo trước/sau nào
> thực hiện được** — tức điều kiện để tinh chỉnh chưa đủ, ngay cả khi đã có GPU.

Nhóm **câu bẫy chống bịa** (60/227) là nhóm phải theo dõi sát nhất qua một lần tinh chỉnh.
Tinh chỉnh trên dữ liệu một lĩnh vực thường làm mô hình **tự tin hơn** trong lĩnh vực ấy,
và tự tin hơn đúng là cách điểm nhóm này rớt. Với một trợ lý tư vấn doanh nghiệp thì bịa
một con số nguy hiểm hơn không trả lời được.

### 3.2 Gọi công cụ — bộ đề CHƯA CÓ, phải dựng trước

Chưa có bộ đề gọi công cụ nào trong kho tại 26/09/2026. Phải dựng trước khi tinh chỉnh,
nếu không thì [§1](#1-canh-bao-lon-nhat) chỉ là một lời cảnh báo không kiểm chứng được.
Tối thiểu cần: gọi đúng tên công cụ · điền đúng tham số · **không gọi khi không nên gọi**
(ca này hay bị bỏ và là ca rớt nhiều nhất) · gọi nhiều bước nối tiếp.

### 3.3 Bảng phải điền đủ mới được kết luận

| Phép đo | Trước | Sau | Kết luận |
|---|---|---|---|
| 227 câu — tổng | chưa đo | chưa đo | |
| 227 câu — nhóm bẫy chống bịa | chưa đo | chưa đo | |
| Gọi công cụ | chưa đo | chưa đo | |
| Độ trễ token đầu | chưa đo | chưa đo | |

**Thiếu một ô là chưa có kết luận.** Điền ba ô rồi kết luận "tốt hơn" là đúng thứ tài liệu
này tồn tại để chặn.

---

<a id="4-trinh-tu-mot-lan-tinh-chinh"></a>

## 4 · Trình tự một lần tinh chỉnh

Mỗi bước có một điều kiện ra, và **không bước nào được bỏ vì "lần này vội"**.

| # | Bước | Điều kiện ra |
|---|---|---|
| 0 | Kiểm ba điều kiện ở [§0](#0-ba-dieu-kien-bat-buoc) | cả ba ĐẠT, ghi ra thành văn |
| 1 | Rà giấy phép từng nguồn dữ liệu tinh chỉnh | mỗi nguồn có một dòng cơ sở pháp lý |
| 2 | Đóng băng bộ đề tiếng Việt **và** bộ đề gọi công cụ | hai bộ đề có mã băm, không sửa nữa |
| 3 | **Đo ĐƯỜNG CƠ SỞ trên trọng số Google nguyên bản** | bảng [§3.3](#3-bo-danh-gia-truoc-sau) điền xong cột "Trước" |
| 4 | Chạy QLoRA | có bộ đặt, có nhật ký, có cấu hình lưu lại |
| 5 | **Đo lại cả hai bộ đề** | cột "Sau" điền xong |
| 6 | So sánh và quyết | rớt gọi công cụ ⇒ **BỎ bản này**, không phát hành |
| 7 | Ghi thẻ mô hình | nói rõ nền là trọng số Google, bộ đặt là của BDSG |

**Bước 3 không được bỏ.** Không có đường cơ sở thì không có phép so, và khi ấy mọi con số
"sau" đều vô nghĩa — kể cả khi chúng đẹp.

---

<a id="5-luat-dat-ten-va-khai-bao-quyen-so-huu"></a>

## 5 · Luật đặt tên và khai báo quyền sở hữu

**KHÔNG BAO GIỜ đặt `bdsg_la_trong_so_bdsg = true` cho trọng số Google nguyên bản.**

Ba trạng thái, ba cách khai, không được trộn:

| Thứ đang phục vụ | `bdsg_la_trong_so_bdsg` | Nói thế nào cho đúng |
|---|---|---|
| Trọng số Google Gemma 4 31B nguyên bản | **`false`** | "BDSG **phục vụ** trọng số của Google" |
| Trọng số Google + **bộ đặt LoRA do BDSG huấn luyện** | **`false`** cho nền, và khai bộ đặt **tách riêng** | "mô hình nền của Google, **bộ đặt** của BDSG" |
| Trọng số BDSG huấn luyện từ đầu (mốc M7) | **`true`** | "trọng số do BDSG huấn luyện" |

Dòng giữa là dòng dễ khai sai nhất, nên nói cho rõ: **một bộ đặt LoRA không biến trọng số
nền thành của BDSG.** Phần lớn năng lực của mô hình vẫn đến từ 31,27 tỷ tham số do Google
huấn luyện; phần của BDSG là 48 triệu tham số bộ đặt (0,154% ở `r=16` — xem
[§2](#2-uoc-tinh-vram-cho-qlora-tren-31b)). Khai `true` ở dòng ấy là nhận công của người
khác, và nó cũng làm hỏng đúng thứ kho này dựng lên để giữ.

Phép chặn này đã được cài trong mã: `trien-khai/chay-vllm.sh` từ chối
`--served-model-name` có chữ "bdsg" khi `BDSG_DA_TINH_CHINH` khác `co`, và phép chặn ấy có
bài thử ngược trong `--tu-kiem`.

Giấy phép: trọng số nền Apache-2.0 của Google. Bộ đặt do BDSG huấn luyện là tác phẩm của
BDSG, nhưng **phát hành nó vẫn phải kèm ghi công mô hình nền** — vừa là nghĩa vụ
Apache-2.0 điều 4, vừa là điều kiện để người dùng biết họ đang nạp bộ đặt lên cái gì.

---

<a id="6-chua-do"></a>

## 6 · CHƯA ĐO

| Hạng mục | Vì sao |
|---|---|
| VRAM thật của một lần QLoRA | chưa chạy lần nào; [§2](#2-uoc-tinh-vram-cho-qlora-tren-31b) là tính ra, và còn thiếu phần kích hoạt |
| Thời gian một epoch | chưa có GPU |
| Chi phí một lần chạy | chưa thuê GPU, không có đơn giá để trích |
| Điểm 227 câu của Gemma 4 31B nguyên bản | chưa chạy; bộ chạy đánh giá cũng chưa có |
| Điểm gọi công cụ trước/sau | bộ đề chưa dựng |
| Cỡ dữ liệu tinh chỉnh cần thiết | chưa rà giấy phép nên chưa biết dùng được bao nhiêu |

---

*Viết 26/09/2026. Số tham số LoRA ở [§2](#2-uoc-tinh-vram-cho-qlora-tren-31b) tính thật
bằng máy từ cấu hình đã công bố; mọi con số VRAM là TÍNH RA, chưa đo. Trọng số nền là của
Google DeepMind, Apache-2.0.*
