# Đối chiếu tokenizer với một chuẩn công khai

Đo ngày 26/09/2026. Tệp này tồn tại để **phép đo trung tâm của kho tự chứng minh
được**, không phụ thuộc vào việc người đọc có trong tay đúng một tệp nào đó.

## Vì sao phải đo lại

Phép đo đầu tiên (25/09/2026) lấy đối chứng là tokenizer của một dự án khác.
Con số đúng, nhưng có hai chỗ yếu:

1. Người đọc muốn tự kiểm phải đi tìm đúng tệp ấy.
2. Kết luận bị buộc vào một dự án cụ thể thay vì vào **tính chất của bài toán**.

Nên lần này dùng **tokenizer của GPT-2** — công khai, vĩnh viễn, ai cũng tải được
một dòng lệnh, và là chuẩn byte-level BPE được trích dẫn nhiều nhất.

## Cách đo

| | |
|---|---|
| Văn bản đo | **1.037.113 ký tự tiếng Việt** — phần giữ lại, chưa từng dùng lúc huấn luyện |
| Tokenizer BDSG | byte-level BPE, từ vựng **6.400**, huấn luyện 1,0 giây trên Apple M1 |
| Đối chứng | tokenizer GPT-2, từ vựng **50.257** |

Chú ý phép so này **bất lợi cho BDSG**: đối chứng có từ vựng lớn hơn **7,9 lần**,
mà từ vựng lớn hơn thì gần như luôn nén tốt hơn.

## Kết quả

| tokenizer | từ vựng | token | ký tự/token |
|---|---:|---:|---:|
| GPT-2 | 50.257 | 850.141 | 1,22 |
| **BDSG tiếng Việt** | **6.400** | **289.266** | **3,59** |

**BDSG dùng ít hơn 66,0% số token, với từ vựng nhỏ hơn 7,9 lần.** Cùng một ngân
sách ngữ cảnh, mô hình dùng tokenizer BDSG đọc được nhiều hơn **2,94 lần** chữ
tiếng Việt.

Phép đo trước cho 66,1% với một đối chứng khác. Đổi đối chứng **không đổi kết
luận** — đó là dấu hiệu con số này nói về tiếng Việt, không phải về một dự án nào.

## Cơ chế, nhìn thấy được

Câu thử: `Công ty Cổ phần Tập đoàn BDSG hoạt động trong lĩnh vực bất động sản tại Thanh Hoá.`

| | token | mười hai token đầu |
|---|---:|---|
| GPT-2 | **74** | `C ǀ Ã´ ǀ ng ǀ Ġty ǀ ĠC ǀ á ǀ » ǀ ķ ǀ Ġph ǀ á ǀ º ǀ §` |
| BDSG | **21** | `CÃ´ng ǀ Ġty ǀ ĠCá»ķ ǀ Ġpháº§n ǀ ĠTáºŃp ǀ ĠÄĳoÃłn ǀ ĠB ǀ D ǀ SG ǀ Ġhoáº¡t ǀ ĠÄĳá»Ļng ǀ Ġtrong` |

Chữ **Cổ** ở GPT-2 tốn bốn token `á ǀ » ǀ ķ` cộng phần đầu — dấu tiếng Việt không
có trong từ vựng nên bị đẩy xuống từng byte UTF-8 thô. Tokenizer học tiếng Việt
gộp cả chữ thành **một** token.

Chi phí thật không phải tốc độ mà là **trí nhớ**: cùng cửa sổ ngữ cảnh, mô hình
dùng tokenizer không học tiếng Việt chỉ đọc được **một phần ba** lượng chữ.

## Tự kiểm lại

```bash
.venv/bin/python huan-luyen/tu-vung/do_tokenizer.py \
  --tokenizer huan-luyen/tu-vung/ket-qua/tokenizer-vi-6400-thu-nghiem.json \
  --doi-chieu gpt2 \
  --van-ban <đường dẫn tệp tiếng Việt của bạn>
```

## Điều phép đo này KHÔNG chứng minh

- **Nén tốt hơn không có nghĩa trả lời tốt hơn.** Nó chỉ nói cùng ngân sách token
  thì mô hình đọc được nhiều chữ tiếng Việt hơn. Chất lượng trả lời phải đo bằng
  bộ đánh giá ở `danh-gia/`.
- **Tokenizer này chưa phải bản phát hành.** Nó học trên 7,13 MB văn xuôi nghiệp
  vụ — hẹp về chủ đề. Bản phát hành cần ngữ liệu tiếng Việt rộng hơn nhiều, và
  cần trộn thêm tiếng Anh.
- **Chưa đo phần tiếng Anh của tokenizer BDSG.** Đo ngày 25/09/2026 trên một bản
  chỉ học tiếng Việt cho thấy tiếng Anh **tệ đi 22,0%**. Đó chính là lý do bản
  phát hành phải trộn hai thứ tiếng theo trọng số, chứ không phải chuyển hẳn sang
  tiếng Việt. Con số sau khi trộn **chưa đo**.
