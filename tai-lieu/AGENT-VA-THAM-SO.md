# Mỗi agent là một bộ não — cần bao nhiêu agent để thành 30 tỷ tham số?

**Câu trả lời ngắn: không cần bao nhiêu cả, vì tham số KHÔNG CỘNG DỒN giữa các
agent.** Nhưng trực giác đằng sau câu hỏi thì đúng, và nó dẫn tới hai kiến trúc
có thật. Tài liệu này tách hai điều ấy ra.

---

## 1 · Phép tính không chạy: tham số không cộng được

Nếu có **N** agent, mỗi agent **P** tham số, ta KHÔNG có một mô hình `N × P`
tham số. Ta có **N mô hình riêng, mỗi cái P tham số**.

30.000 agent mỗi cái 1 triệu tham số **không phải** một mô hình 30 tỷ. Nó là
30.000 mô hình 1 triệu.

Lý do nằm ở chỗ sức mạnh của một mô hình 30 tỷ đến từ đâu: **cả 30 tỷ tham số
cùng tham gia MỘT lượt suy luận**, và mối liên hệ giữa chúng là thứ được học.
Hai mô hình chạy riêng không có mối liên hệ ấy — chúng không thấy trạng thái
bên trong của nhau, không có gradient chung, không có gì để học cách phối hợp.
Ghép đầu ra của chúng lại là ghép **kết luận**, không phải ghép **năng lực**.

## 2 · Phép so với bộ não người chạy NGƯỢC hướng trực giác

| | |
|---|---|
| Nơ-ron trong một bộ não người | ~86.000.000.000 |
| Khớp thần kinh (thứ tương ứng với "tham số") | ~100.000.000.000.000 |
| Đích của BDSG | 30.000.000.000 |

Chia ra: **30 tỷ tham số ≈ 1/3.333 của MỘT bộ não người**, tức khoảng **0,03 %**.

Nên câu hỏi "cần bao nhiêu người để đạt 30 tỷ" có câu trả lời là **0,0003
người**. Không phải nhiều người — là một phần rất nhỏ của một người. Nói cách
khác: một bộ não người tương đương khoảng **3.333 mô hình 30 tỷ cộng lại**.

*(Con số khớp thần kinh thường được nêu trong khoảng 1e14–1e15, nên tỉ lệ trên
có thể xê dịch tới mười lần. Kết luận không đổi: 30 tỷ nhỏ hơn một bộ não rất
nhiều lần, chứ không lớn hơn.)*

Điều này quan trọng vì nó đổi câu hỏi. Không phải *"gom bao nhiêu bộ não cho
đủ"*, mà *"làm sao để một mô hình nhỏ hơn bộ não 3.000 lần vẫn làm được việc
của doanh nghiệp"*. Câu sau có lời giải; câu trước thì không.

---

## 3 · Nhưng trực giác thì đúng — và đây là hai kiến trúc thật

### 3.1 · Hỗn hợp chuyên gia (Mixture of Experts)

Đây **chính là** "nhiều bộ não trong một cái đầu", và nó có thật.

Mô hình chứa nhiều mạng con gọi là **chuyên gia**. Một **bộ định tuyến** chọn
vài chuyên gia cho mỗi token. Tổng tham số lớn, nhưng số tham số **hoạt động**
mỗi lượt thì nhỏ — nên chạy được trên phần cứng vừa phải.

Ví dụ đã công bố: Mixtral 8×7B có 8 chuyên gia, ~47 tỷ tham số tổng, nhưng chỉ
~13 tỷ hoạt động mỗi token.

Quy về BDSG ở mức 30 tỷ: đại khái **8 chuyên gia × ~4 tỷ**, hoặc **16 × ~2 tỷ**,
với 2 chuyên gia hoạt động mỗi token.

**Điều kiện then chốt, và là chỗ khác với ý tưởng ban đầu:** các chuyên gia được
huấn luyện **CÙNG NHAU BÊN TRONG MỘT MÔ HÌNH**, không phải huấn luyện rời rồi
ghép lại. Bộ định tuyến chỉ học được cách chọn khi nó thấy cả hệ cùng lúc.

### 3.2 · Chưng cất (distillation) — phần ý tưởng của anh ĐÚNG

Ý *"huấn luyện agent trước, sau đó tạo ra mô hình trung tâm"* là **đúng**, và
nó có tên: chưng cất. Nhiều **mô hình thầy** sinh ra dữ liệu; một **mô hình
trò** học từ đó.

Với BDSG đây là con đường thực tế nhất, vì nó giải đúng thứ BDSG đang thiếu:
**ngữ liệu**. Đích 30 tỷ cần khoảng 600 tỷ token theo Chinchilla; BDSG có 4,37
triệu. Không có cách nào gom đủ bằng tài liệu. Nhưng **mỗi cuộc trò chuyện với
agent là một bộ ba** (câu hỏi, câu trả lời, có hữu ích không) — và đó là thứ
không mua được ở đâu, chỉ sinh ra được bằng cách vận hành.

Lưu ý: cỡ của mô hình trò do **phần cứng** quyết định, không do đếm số agent.

---

## 4 · Vậy BDSG nên có bao nhiêu agent?

**Đếm theo LĨNH VỰC, không đếm theo tham số.**

Con số đúng là số **miền tri thức phân biệt được** mà BDSG thật sự phục vụ. Hôm
nay BDSG có ~359 agent (200 tư vấn + 221 persona CRM + 3.321 xã/phường), nhưng
số MIỀN thì ít hơn nhiều — khoảng 12–20 nếu gộp theo ngành.

Từ đó ra con số kiến trúc:
- **12–20 chuyên gia** trong một mô hình MoE, hoặc
- **12–20 bộ điều hợp LoRA** định tuyến lúc suy luận (rẻ hơn, làm được sớm hơn).

359 agent vẫn giữ nguyên ở tầng sản phẩm — mỗi agent là một **persona + phạm vi
tri thức + danh sách công cụ**, tức một BẢN GHI DỮ LIỆU. Nhiều persona có thể
dùng chung một chuyên gia bên dưới. Đó là lý do "thay thế 359 agent" là một
cuộc **di chuyển dữ liệu**, không phải viết lại 359 lần.

---

## 5 · Thứ tự làm, và cái nào bắt đầu được ngay

| Bước | Làm được khi nào | Điều kiện |
|---|---|---|
| 1. Agent sinh dữ liệu: mọi cuộc trò chuyện thành bộ ba có nhãn | **Ngay** | Chat đã mở công khai 26/09/2026 |
| 2. Một bộ điều hợp LoRA cho MỘT miền, ĐO được nó làm tốt hơn | Khi có GPU | Chưa có GPU |
| 3. Thư viện điều hợp + định tuyến theo miền | Sau bước 2 | — |
| 4. MoE 30 tỷ tinh chỉnh từ một mô hình nền mở | Sau bước 3 | Nhiều GPU |
| 5. Tiền huấn luyện 30 tỷ từ đầu | **Không khuyến nghị** | ~600 tỷ token — BDSG sẽ không có |

Bước 1 là bước duy nhất chạy được hôm nay, và nó là bước không ai làm hộ được:
ngữ liệu hội thoại của doanh nghiệp Việt Nam thì chỉ BDSG vận hành mới có.

---

## 6 · Những gì tài liệu này CHƯA chứng minh

- Chưa đo bộ điều hợp LoRA nào trên dữ liệu BDSG — **chưa có GPU**.
- Chưa biết 12–20 miền có phải con số đúng không; đó là ước lượng từ danh mục
  hiện tại, chưa phải kết quả phân cụm trên dữ liệu thật.
- Con số Mixtral 8×7B là **của Mistral công bố**, không phải số BDSG đo.
- Phép so bộ não là một **phép loại suy có giới hạn**: khớp thần kinh không
  tương đương tham số về mặt chức năng. Nó dùng để chỉnh lại bậc độ lớn, không
  dùng để kết luận về năng lực.

## Liên quan

- [`CUNG-HUAN-LUYEN.md`](CUNG-HUAN-LUYEN.md) — các máy cùng góp bộ điều hợp
- [`LO-TRINH-LORA.md`](LO-TRINH-LORA.md) — lộ trình tinh chỉnh
- [`MAY-BDSG-OS.md`](MAY-BDSG-OS.md) — vì sao 30 tỷ chứ không lớn hơn
