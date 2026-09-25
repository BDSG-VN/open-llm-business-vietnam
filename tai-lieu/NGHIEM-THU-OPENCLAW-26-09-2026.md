# Nghiệm thu nền OpenClaw — đo ngày 26/09/2026

Mục tiêu thử: chứng minh nền tảng agent nói chuyện được với mô hình của BDSG.

## Đã đạt

| Bước | Kết quả |
|---|---|
| Giấy phép | **MIT** — cho dùng, sửa, phát hành, đổi thương hiệu. Thân văn bản là MIT nguyên vẹn; GitHub khai "Other" chỉ vì có thêm dòng trỏ `THIRD_PARTY_NOTICES.md` |
| Dựng ảnh Docker | ✅ `bdsg-open-chat:dung-thu`, **3,09 GB** |
| Chạy | ✅ `openclaw --version` → `OpenClaw 2026.9.6` |
| Cấu hình nhà cung cấp BDSG | ✅ `openclaw models list` thấy `bdsg/openbiz-vn-chat` · ngữ cảnh 33k · `Local yes` · `Auth yes` · nhãn `default` |
| Mô hình BDSG trả lời thật | ✅ qua API: *"BDSG là trợ lý tri thức doanh nghiệp Việt Nam… có trích dẫn nguồn [1][2]"* |

## ĐIỂM CHẶN CỨNG — nhân hệ điều hành

Gateway **không khởi động được**:

```
Gateway failed to start: failed to acquire gateway lock
  | openat2 beneath root: Function not implemented (os error 38) | ENOSYS
```

Đo được:

| | |
|---|---|
| Nhân máy chủ | **5.4.0-216-generic** |
| `openat2` cần | **≥ 5.6** |
| Docker | 27.0.1 · libseccomp 2.5.1 |

Đã thử `--security-opt seccomp=unconfined` — **vẫn hỏng y hệt**. Đó là phép đo
quyết định: nếu là seccomp chặn thì bỏ seccomp phải chạy được. Nó không chạy
được, nên nguyên nhân nằm ở **nhân**, không phải ở bộ lọc.

Ba lỗi trước đó đều đã sửa xong và **không phải** nguyên nhân cuối:
`gateway.mode` thiếu · khoá SQLite sót · từ chối mở cổng khi chưa có xác thực.
Ghi lại vì mỗi cái đều tốn một vòng chẩn đoán, và lần sau ai gặp thì đỡ mất.

## Ba đường đi, và giá của từng đường

| Đường | Giá |
|---|---|
| Nâng nhân máy chủ chính | Phải **khởi động lại máy** đang chạy 38 container và 56 tên miền. Không phải việc làm lúc không ai trực |
| Dùng một máy khác có nhân ≥5.6 | Chưa có quyền truy cập bằng khoá hiện tại — đã thử hai địa chỉ, cả hai từ chối |
| Chạy trên máy người dùng cuối | **Đường này không vướng gì**: máy cá nhân đời mới đều có nhân ≥5.6 hoặc macOS/Windows. Và đó chính là mục tiêu của dự án |

Đường thứ ba đáng chú ý: vướng mắc này là của **máy chủ BDSG**, không phải của
sản phẩm. Người dùng tải về chạy trên máy họ sẽ không gặp.

## Điều chưa chứng minh

- **Chưa chạy một lượt agent nào qua Gateway.** Cấu hình đúng và mô hình thấy
  được không đồng nghĩa một lượt có công cụ sẽ chạy trót lọt.
- **Chưa thử với mô hình cục bộ.** BDSG chưa có trọng số nào, nên mắt xích
  "không cần khoá bên thứ ba" vẫn chưa khép.
- **Chưa đo tính năng nào hoạt động với mô hình nhỏ.** Gọi công cụ đòi mô hình
  bám đúng định dạng; mô hình nhỏ thường không bám nổi. Phải đo từng cái.
