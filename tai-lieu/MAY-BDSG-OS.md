# Máy trạm BDSG OS

![Bản vẽ minh hoạ máy trạm BDSG OS](anh/may-bdsg-os.svg)

> **Bản vẽ dựng tạm.** Hình trên là bản vẽ kỹ thuật minh hoạ cấu hình, **không phải ảnh
> chụp một cỗ máy đã xuất xưởng**. Tính đến 26/09/2026 chưa có máy nào được dựng, và
> **chưa có một phép đo hiệu năng nào** trên phần cứng thật.

---

## Bài toán

Một doanh nghiệp khoảng 30 nhân sự muốn dùng AI nội bộ mà dữ liệu không rời khỏi toà nhà.
Câu hỏi không phải "máy nào mạnh nhất" mà là: **cấu hình nhỏ nhất đủ để vừa phục vụ vừa
huấn luyện, trên một thùng máy đặt được trong phòng máy bình thường.**

## Tải thật nhỏ hơn trực giác

Trực giác nói "30 người thì phải chịu được 30 lượt cùng lúc". Định luật Little nói khác.

Với giả định (đây là **giả định**, không phải số đo tại một khách hàng):

- 30 nhân sự, mỗi người ~20 lượt hỏi mỗi ngày → 600 lượt / 8 giờ ≈ **0,021 lượt/giây**
- mỗi lượt sinh chữ trung bình ~40 giây

thì số phiên chạy đồng thời trung bình `L = λ × W ≈ 0,021 × 40 ≈ **0,83**`.

Kể cả nhân hệ số đỉnh 5 lần cho giờ cao điểm, con số vẫn dưới 5. Thiết kế **8–12 khe phục
vụ** là đã rộng rãi. **Một card đồ hoạ là đủ** — và đó là kết luận quan trọng nhất của cả
tài liệu này, vì nó là thứ quyết định máy này giá của một cỗ máy trạm chứ không phải giá
của một tủ rack.

## Vì sao 30 tỷ tham số, và vì sao không lớn hơn

| Cỡ mô hình | Trọng số ở 4-bit | Vừa card nào |
|---|---|---|
| 8 tỷ | ~4,5 GB | 16 GB — thừa |
| 14 tỷ | ~8 GB | 24 GB — thoải mái |
| 30 tỷ | ~16–17 GB | 24 GB chật, **48 GB thoải mái** |
| 70 tỷ | ~38 GB | 48 GB chật, thực tế cần 2 card |

Ở 30 tỷ, trọng số + bộ nhớ đệm KV cho 8–12 khe vừa **một** card 48 GB. Lên 70 tỷ là phải
hai card, và hai card đổi luôn cả khung máy, nguồn, tản nhiệt và giá thành. Ranh giới
"một thùng máy" nằm ở đây.

Có một điểm gãy đã đo được trong tài liệu công khai và nó nói ngược lại xu hướng "càng to
càng tốt": trên bộ đánh giá gọi công cụ BFCL v3, họ Qwen3 đi **1,7B = 56,6 → 4B = 65,9 →
8B = 68,1 → 14B = 70,4 → 32B = 70,3 → 235B = 70,8**. Tức là từ khoảng 8–14 tỷ trở lên,
thêm tham số gần như không thêm được năng lực gọi công cụ. Một hệ điều hành sống bằng gọi
công cụ thì mua tham số quá điểm gãy ấy là mua thứ không dùng tới.

Vậy 30 tỷ để làm gì? Không phải để gọi công cụ giỏi hơn, mà để **hiểu tài liệu và ngữ
cảnh nghiệp vụ tiếng Việt** tốt hơn — phần mà tham số vẫn còn giúp được.

## Cấu hình đề xuất

Cấu hình dưới đây là **đặc tả**, không phải số đo. Cột cuối nói rõ vì sao chọn.

| Bộ phận | Đặc tả | Lý do |
|---|---|---|
| Card đồ hoạ | 1 × 48 GB VRAM | Vừa trọng số 30B ở 4-bit + đệm KV cho 8–12 khe; một card giữ máy ở khung để bàn |
| CPU | 16–24 nhân | Tiền xử lý, nhúng văn bản, MCP; không phải nút thắt |
| RAM | 256 GB ECC | Tinh chỉnh LoRA cần nạp dữ liệu ngoài GPU; ECC vì máy chạy qua đêm |
| Ổ cứng | 2 × 4 TB NVMe | Trọng số, điểm kiểm, ngữ liệu, kho tri thức; NVMe vì nạp trọng số là I/O tuần tự lớn |
| Nguồn | 1600 W | Đủ đầu cho một card công suất cao + dư tải khi huấn luyện liên tục |
| Tản nhiệt | Khí, luồng trước-sau | Máy đặt trong phòng làm việc, không phải phòng máy có điều áp |

**Giá không nằm trong tài liệu này.** Cấu hình và báo giá theo yêu cầu.

## Ban ngày phục vụ, ban đêm huấn luyện

Đây là lý do máy cần RAM và ổ lớn hơn một máy chỉ để chạy mô hình:

- **Giờ làm**: mô hình phục vụ 8–12 khe. GPU dùng phần lớn VRAM cho trọng số và đệm KV.
- **Ngoài giờ**: chạy tinh chỉnh LoRA/QLoRA trên tài liệu mới của công ty trong ngày. Dữ
  liệu huấn luyện đọc từ NVMe, dựng lô trên RAM, chỉ đẩy phần cần thiết lên GPU.

Kết quả là **mô hình của doanh nghiệp nào thì hợp với doanh nghiệp ấy**, và quá trình làm
cho nó hợp không đi qua máy chủ của bất kỳ ai khác.

## Những gì CHƯA đo — không được trích dẫn như số đo

Danh sách này quan trọng ngang phần đặc tả:

- Chưa có GPU, **chưa nạp mô hình 30 tỷ tham số lần nào**.
- Chưa đo độ trễ lượt đầu, chưa đo số token/giây, chưa đo số lượt đồng thời thực tế.
- Chưa đo mức tụt độ chính xác gọi công cụ khi lượng tử hoá xuống 4-bit **ở họ mô hình sẽ
  dùng**. Số 91,3 % → 69,0 % trích ở trên là của **Gemma-3 12B**, không phải của mô hình
  này, và nó là lý do phải đo chứ không phải kết luận về máy này.
- Chưa đo điện năng, nhiệt độ, tiếng ồn khi chạy huấn luyện liên tục qua đêm.

Mọi con số hiệu năng chỉ được đưa vào tài liệu **sau khi đo trên máy thật**, kèm cấu hình
và cách đo.

## Liên quan

- [`GEMMA4-31B.md`](GEMMA4-31B.md) — backend phục vụ trọng số Gemma 4 31B của Google
- [`LO-TRINH-LORA.md`](LO-TRINH-LORA.md) — lộ trình tinh chỉnh
- [`KIEN-TRUC-HE-DIEU-HANH.md`](KIEN-TRUC-HE-DIEU-HANH.md) — nhân, MCP, phân quyền
