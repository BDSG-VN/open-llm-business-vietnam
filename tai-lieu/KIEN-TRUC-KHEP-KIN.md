# Chuỗi khép kín: mô hình BDSG → BDSG Open Chat, không khoá bên thứ ba

Đo và viết ngày 26/09/2026.

Mục tiêu do chủ dự án đặt ra, nguyên văn ý: *người dùng tải mô hình LLM mở của
BDSG về, chạy BDSG Open Chat, và mọi tính năng hoạt động mà **không cần khoá API
LLM từ bên thứ ba**.*

Tài liệu này ghi lại **con đường đã đo được là khả thi**, và **ràng buộc thiết kế
mà nếu bỏ qua thì cả chuỗi đứt ở mắt xích cuối**.

---

## 1 · Bốn mắt xích

```
  ┌────────────────────┐
  │ 1. Kiến trúc BDSG  │  mo-hinh/kien_truc.py — PyTorch thuần
  │    (kho này)       │  RMSNorm · RoPE · GQA · SwiGLU · pre-norm
  └─────────┬──────────┘
            │  huấn luyện (cần GPU thuê — mốc M7)
            ▼
  ┌────────────────────┐
  │ 2. Trọng số .safetensors                           │
  └─────────┬──────────┘
            │  chuyển đổi
            ▼
  ┌────────────────────┐
  │ 3. Tệp GGUF        │  định dạng llama.cpp đọc được
  └─────────┬──────────┘
            │  llama-server phục vụ, giao thức tương thích OpenAI
            ▼
  ┌────────────────────┐
  │ 4. BDSG Open Chat  │  nền OpenClaw (MIT), trỏ vào điểm cuối cục bộ
  └────────────────────┘
```

Mắt xích 1 đang được viết trong kho này. Mắt xích 2 chờ GPU. Mắt xích 3 và 4 đã
**đo là có đường**, chưa chạy thật.

---

## 2 · RÀNG BUỘC QUYẾT ĐỊNH — đọc trước khi sửa kiến trúc

**Kiến trúc của BDSG phải chuyển được sang GGUF mà KHÔNG phải vá `llama.cpp`.**

`llama.cpp` không đọc một kiến trúc tuỳ ý. Bộ chuyển đổi của nó nhận diện các
kiến trúc đã biết qua trường `architectures` trong `config.json` và qua tên các
tham số. Một kiến trúc lạ sẽ cần viết thêm mã C++ trong chính `llama.cpp` — tức
mắt xích 3 và 4 đứt, và người dùng cuối không chạy được gì.

Điều may: bốn kỹ thuật BDSG chọn — **RMSNorm, RoPE, GQA, SwiGLU, pre-norm** —
chính là bộ kỹ thuật mà họ kiến trúc Llama dùng. Nếu viết đúng chuẩn ấy và đặt
tên tham số theo chuẩn thư viện `transformers`, mô hình chuyển đổi được như một
kiến trúc đã biết, **không cần sửa `llama.cpp` một dòng nào**.

Đây không phải may mắn tình cờ mà là lý do chọn đúng bốn kỹ thuật đó. Nên:

> ⚠ Mỗi lần ai đó định thêm một khối "sáng tạo" vào kiến trúc — một kiểu chuẩn
> hoá khác, một cách mã hoá vị trí khác, một cổng phi tuyến khác — hãy hỏi trước:
> **`llama.cpp` có đọc được không?** Nếu không, cái giá không phải là một hàm
> phải viết thêm, mà là **người dùng cuối không chạy được mô hình trên máy họ**.

Phép kiểm cho ràng buộc này chưa viết. Nó phải là: xuất một mô hình tí hon ra
`.safetensors` + `config.json`, chạy bộ chuyển đổi của `llama.cpp`, và khẳng định
nó ra được tệp GGUF. Chưa có GPU vẫn chạy được phép kiểm này vì mô hình tí hon
huấn luyện trên CPU trong vài giây.

---

## 3 · Mắt xích 4: vì sao là OpenClaw

Đo ngày 26/09/2026 trên `openclaw/openclaw` bản `2026.9.6`:

| | |
|---|---|
| Giấy phép | **MIT** — cho dùng, sửa, phát hành, bán, đổi thương hiệu; chỉ buộc giữ dòng bản quyền |
| Quy mô | 49.795 tệp, 40.976 tệp TypeScript |
| Nhà cung cấp cục bộ | có sẵn `openai-completions`, `ollama`, `custom`, `local`, cấu hình `baseUrl` |
| Plugin quan trọng nhất | `@openclaw/llama-cpp-provider` — **tự cài và quản `llama-server`**, chạy GGUF, kèm nhúng cục bộ cho tìm kiếm trí nhớ |

GitHub khai giấy phép là "Other" chỉ vì tệp `LICENSE` có thêm một dòng trỏ sang
`THIRD_PARTY_NOTICES.md`; thân văn bản là MIT nguyên vẹn.

**Đây là khác biệt so với lần trước.** Dự án từng cân nhắc Open WebUI và phải bỏ:
giấy phép của nó cấm cả việc *che* thương hiệu, kể cả "giao diện xung quanh", nên
hai mục tiêu "mở cho khách" và "mang thương hiệu BDSG" loại trừ nhau. MIT không
có điều khoản ấy.

---

## 4 · Điều tài liệu này KHÔNG khẳng định

- **Chưa chạy thật mắt xích nào sau mắt xích 1.** Chưa có trọng số, nên chưa có
  GGUF, nên chưa chứng minh được BDSG Open Chat chạy trên mô hình BDSG.
- **Chưa đo chất lượng.** Một mô hình nhỏ đủ để *chạy* không có nghĩa nó đủ để
  *dùng*. Cỡ mô hình chạy được trên máy cá nhân sẽ bịa nhiều; đó là lý do lớp
  truy hồi vẫn đứng trước và vẫn là phần trả lời sự thật.
- **Chưa đo tính năng nào của OpenClaw thật sự hoạt động với mô hình nhỏ.** Gọi
  công cụ và làm việc nhiều bước đòi hỏi mô hình bám đúng định dạng; mô hình nhỏ
  thường không bám nổi. Phải đo từng tính năng, không được suy ra.

Ba điều trên là ba phép đo phải làm, không phải ba điều cần tin.
