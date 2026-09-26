# Cùng huấn luyện: các doanh nghiệp chạy máy BDSG OS góp vào mô hình chung

**Trạng thái: ĐỀ XUẤT KIẾN TRÚC, chưa có dòng mã nào.** Tài liệu này ghi lại một ý
tưởng sản phẩm và phần thẩm định kỹ thuật của nó, để lần sau không ai phải nghĩ lại
từ đầu — và để không ai hứa phần chưa làm được.

## Ý tưởng

Mỗi doanh nghiệp mua máy trạm BDSG OS đều có sẵn ba thứ mà một dự án mô hình mở
thường thiếu: **phần cứng nhàn rỗi ban đêm**, **dữ liệu ngành thật**, và **động cơ để
mô hình chung giỏi hơn**. Nếu các máy ấy cùng góp vào một mô hình, thì càng bán được
nhiều máy, mô hình càng mạnh — và mô hình càng mạnh thì máy càng đáng mua.

## Làm được tới đâu

| Việc | Chia ra nhiều máy được không | Vì sao |
|---|---|---|
| Tiền huấn luyện 30 tỷ tham số từ đầu | **Không** | Cần liên kết băng thông rất cao giữa các GPU; máy để bàn nối qua Internet chậm hơn hàng nghìn lần. Đây là giới hạn vật lý, không phải giới hạn kỹ thuật lập trình. |
| Tinh chỉnh (LoRA/QLoRA) trên dữ liệu riêng | **Được** | Mỗi máy huấn luyện độc lập; chỉ gửi về **bộ điều hợp**, không gửi dữ liệu. |
| Bộ đánh giá, bộ câu hỏi, sửa lỗi nhãn | **Được, và dễ nhất** | Đây là đóng góp bằng dữ liệu đã ẩn danh, không cần GPU. |

Nói gọn: **mô hình nền do BDSG huấn luyện tập trung; phần tri thức ngành thì cộng đồng
góp.** Đó là ranh giới thật, và nó nên được nói trước khi bán máy chứ không phải sau.

## Kiến trúc đề xuất

1. Máy trạm huấn luyện LoRA trên tài liệu của chính công ty, ngoài giờ làm.
2. Công ty chọn **góp** hoặc **giữ riêng** — mặc định là GIỮ RIÊNG, phải bật mới góp.
3. Khi góp, máy gửi lên **bộ điều hợp** (vài chục–vài trăm MB) kèm mô tả ngành và một
   bộ câu hỏi kiểm chứng. **Không gửi dữ liệu huấn luyện.**
4. BDSG chạy bộ đánh giá chung, so bản có và không có bộ điều hợp ấy.
5. Bộ điều hợp đạt thì vào **thư viện điều hợp mở**, có ghi công người góp.

## Ba giới hạn phải nói thẳng

**1 · "Chỉ gửi bộ điều hợp" KHÔNG đồng nghĩa "không lộ dữ liệu".**
Trọng số đã tinh chỉnh ghi nhớ được câu chữ trong tập huấn luyện, và có những phép tấn
công đã công bố khôi phục lại được một phần tập ấy từ trọng số. Một hợp đồng, một danh
sách khách hàng, một mức giá — đều có thể rò theo đường này. Muốn góp an toàn thì cần
thêm lớp nhiễu khi huấn luyện, hoặc một bước rà trước khi nhận, hoặc cả hai. **Chưa có
lớp nào trong kho này.**

**2 · Trộn trung bình các bộ điều hợp thường làm GIẢM chất lượng.**
Bộ điều hợp của một công ty xây dựng và của một công ty dược kéo mô hình về hai hướng
khác nhau; gộp trung bình cho ra một bản kém hơn cả hai. Lối an toàn là **giữ nhiều bộ
điều hợp riêng và định tuyến theo câu hỏi**, chứ không gộp thành một. Định tuyến thì
lại cần biết câu hỏi thuộc ngành nào — thêm một bài toán nữa, chưa giải.

**3 · Góp vào một mô hình MỞ là một quyết định pháp lý, không chỉ kỹ thuật.**
Tri thức rút từ tài liệu nội bộ, đi vào một mô hình ai cũng tải được. Điều đó phải nằm
trong hợp đồng bán máy, bằng chữ, với quyền rút lại — chứ không phải một ô đánh dấu
trong phần cài đặt.

## Bước nhỏ nhất đáng làm trước

Đừng dựng hệ liên kết trước. Làm theo thứ tự này, mỗi bước đều tự nó có ích:

1. **Một bộ điều hợp, một công ty, đo được.** Chứng minh LoRA trên dữ liệu một công ty
   thật sự làm mô hình trả lời tốt hơn cho công ty ấy. Chưa chứng minh được điều này
   thì mọi thứ phía sau là vô nghĩa.
2. **Thư viện điều hợp + định tuyến.** Hai bộ điều hợp, chọn đúng bộ theo câu hỏi.
3. **Quy trình nhận đóng góp.** Đánh giá tự động + rà rò rỉ, chạy tay trước.
4. **Tự động hoá.** Chỉ khi ba bước trên đã chạy với người thật.

## Liên quan

- [`MAY-BDSG-OS.md`](MAY-BDSG-OS.md) — cỗ máy làm việc huấn luyện này
- [`LO-TRINH-LORA.md`](LO-TRINH-LORA.md) — lộ trình tinh chỉnh
