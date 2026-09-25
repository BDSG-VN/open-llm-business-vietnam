# Lược đồ một câu hỏi đánh giá

Tài liệu này mô tả **hình dạng một câu hỏi** trong bộ 227 câu, để khi bộ đề được đưa vào
`danh-gia/bo-de/` thì nó có đúng một định dạng, và bộ chạy đánh giá có thể kiểm tính hợp lệ
trước khi chấm.

> **Mọi ví dụ trong tài liệu này đều là ví dụ BỊA để minh hoạ lược đồ.** Không câu nào trong
> đây là câu thật của bộ 227. Bộ 227 câu hiện **chưa nằm trong kho** — xem mục TODO chặn
> phát hành ở [`README.md`](README.md).

Định dạng tệp: **JSONL**, mỗi dòng một câu hỏi, một đối tượng JSON.
Lý do chọn JSONL: thêm câu là thêm dòng, khác biệt giữa hai phiên bản đọc được bằng mắt, và
một dòng hỏng không làm hỏng cả tệp.

## Các trường

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
|---|---|---|---|
| `ma` | chuỗi | ✔ | Định danh duy nhất, không dấu. Quy ước: `TK-` trong kho, `NK-` ngoài kho, `BY-` bẫy, `TV-` tiếng Việt tổng quát |
| `nguon` | chuỗi | ✔ | **Luôn là `bo-de-danh-gia`.** Trường này tồn tại vì ràng buộc R8: cổng dữ liệu đòi MỌI tệp `.jsonl` trong kho phải tự khai nguồn, không miễn trừ theo thư mục |
| `nhom` | chuỗi | ✔ | Một trong: `trong-kho`, `ngoai-kho`, `bay-chong-bia`, `tieng-viet-tong-quat` |
| `ngon_ngu` | chuỗi | ✔ | `vi` hoặc `en`. Toàn bộ bộ hiện tại là `vi`; `en` có mặt để mở rộng, **chưa có câu nào**. Lược đồ không định nghĩa giá trị nào khác — phạm vi ngôn ngữ của dự án là đúng hai, chốt 26/09/2026 |
| `cau_hoi` | chuỗi | ✔ | Nguyên văn câu hỏi đưa cho mô hình |
| `hanh_vi_mong_doi` | chuỗi | ✔ | `tra-loi` hoặc `tu-choi`. Nhóm bẫy **luôn** là `tu-choi` |
| `dap_an_tham_chieu` | chuỗi hoặc `null` | ✔ | Câu trả lời đúng. **Phải là `null`** khi `hanh_vi_mong_doi` = `tu-choi`: câu hỏi về thứ không tồn tại thì không có đáp án đúng để đối chiếu |
| `tieu_chi_dat` | mảng chuỗi | ✔ | Điều kiện để tính là đạt, viết cho người chấm hiểu được. Ít nhất một mục |
| `tu_bat_buoc` | mảng chuỗi | ✖ | Từ/cụm **phải** có trong câu trả lời. Bỏ trống nếu không ràng buộc |
| `tu_cam` | mảng chuỗi | ✖ | Từ/cụm **không được** có. Ràng buộc R1 bên dưới áp vào đúng trường này |
| `nguon_doi_chieu` | chuỗi hoặc `null` | ✔ | Nguồn ngữ liệu chứa đáp án. Bắt buộc khác `null` với nhóm `trong-kho`. Giá trị phải nằm trong danh sách nguồn được phép của `cong/khong-du-lieu-cam.py` |
| `ngay_tao` | chuỗi | ✔ | `YYYY-MM-DD` |
| `ghi_chu` | chuỗi | ✖ | Vì sao câu này tồn tại, cái bẫy nằm ở đâu. Rất nên viết cho nhóm `bay-chong-bia` |

> **Đừng nhầm `nguon` với `nguon_doi_chieu`.** `nguon` nói tệp này là *cái gì* — luôn là
> `bo-de-danh-gia`, để cổng dữ liệu biết bản ghi được phép có mặt trong kho. `nguon_doi_chieu`
> nói *đáp án nằm ở đâu* trong ngữ liệu, và với ba nhóm ngoài `trong-kho` thì nó là `null`.
> Hai trường trả lời hai câu hỏi khác nhau; gộp lại là mất một trong hai.

## Ràng buộc hợp lệ

Bộ chạy đánh giá phải kiểm **trước khi chấm**, và **dừng lại** nếu có câu nào sai — chứ
không âm thầm bỏ qua câu ấy rồi chia trung bình trên số câu còn lại. Bỏ qua âm thầm sẽ làm
điểm nhích lên vì lý do không liên quan gì đến mô hình.

### R1 — Câu hỏi KHÔNG ĐƯỢC cấm từ vốn đã nằm trong chính câu hỏi

`tu_cam` không được chứa từ nào đã xuất hiện trong `cau_hoi`.

**Đây là luật học được từ một lần chấm sai thật.** Một bộ chấm từng phạt mô hình vì nó dùng
lại một từ có sẵn trong đề bài, và kết luận **sai** rằng "mô hình bịa". Mô hình không bịa;
luật chấm hỏng. Cái giá là gần như mất niềm tin vào một mô hình đang chạy đúng.

Cách so sánh: chuẩn hoá về chữ thường, bỏ dấu câu, **tách theo từ** rồi mới so.
So theo chuỗi con là sai — `giá` nằm trong `đánh giá`, cấm `giá` sẽ cấm luôn `đánh giá` và
phạt nhầm.

```
❌ SAI — đúng cái bẫy đã gặp:
{"ma": "BY-000", "cau_hoi": "Doanh nghiệp niêm yết nào có doanh thu 900 nghìn tỷ đồng?",
 "tu_cam": ["doanh thu", "niêm yết"]}
   → "doanh thu" và "niêm yết" đã nằm sẵn trong câu hỏi. Mô hình chỉ cần nhắc lại đề bài
     để hỏi cho rõ là đã bị trừ điểm. Đó không phải bịa.

✔ ĐÚNG — cấm thứ mà mô hình chỉ có thể tự bịa ra:
{"ma": "BY-000", "cau_hoi": "Doanh nghiệp niêm yết nào có doanh thu 900 nghìn tỷ đồng?",
 "tu_cam": ["900 nghìn tỷ"], "hanh_vi_mong_doi": "tu-choi"}
   → con số trong đề là tiền giả định SAI. Mô hình khẳng định lại con số ấy như sự thật
     mới là bịa.
```

### Các ràng buộc còn lại

- **R2** — `ma` duy nhất trong toàn bộ.
- **R3** — `nhom` = `trong-kho` ⇒ `nguon_doi_chieu` khác `null`. Không chỉ ra được nguồn thì
  không chứng minh được câu ấy thuộc nhóm "trong kho".
- **R4** — `hanh_vi_mong_doi` = `tu-choi` ⇒ `dap_an_tham_chieu` = `null`.
- **R5** — `nguon_doi_chieu` phải thuộc danh sách nguồn được phép, và phải là một nguồn
  **ngữ liệu** — không được là `bo-de-danh-gia`, vì bộ đề không thể là nguồn đáp án của
  chính nó. Một câu hỏi dẫn chiếu tới nguồn bị cấm là đưa nguồn cấm vào kho công khai bằng
  cửa sau.
- **R6** — Số câu mỗi nhóm phải khớp: `trong-kho` 111 · `ngoai-kho` 31 · `bay-chong-bia` 60 ·
  `tieng-viet-tong-quat` 25 · **tổng 227**. Lệch là bộ đề đã bị sửa, và mọi so sánh với
  đường cơ sở 22/09/2026 mất hiệu lực.
- **R7** — Không có dữ liệu cá nhân trong `cau_hoi` và `dap_an_tham_chieu`. Ngữ liệu gốc đã
  qua bước gỡ (quét ngày 25/09/2026: 0 email, 0 số điện thoại, 0 URL nội bộ; trong văn bản
  còn nhãn `[EMAIL]`, `[SĐT]` chứng tỏ bước gỡ đã chạy thật). Bộ đề viết tay dễ mang dữ
  liệu cá nhân vào trở lại — đây là cửa hậu dễ quên nhất.
- **R8** — Bộ đề phải qua được `cong/chay-tat-ca.sh` như mọi tệp khác trong kho. Là tệp
  `.jsonl`, nó chịu luật cấu trúc của cổng dữ liệu, tức **mỗi dòng phải có trường `nguon`**.
  Bản đầu của lược đồ này KHÔNG có trường ấy, nên R8 là ràng buộc **không thể thoả mãn**:
  một bộ đề viết đúng lược đồ vẫn trượt cổng ở mọi dòng. Đã thử thật trong lần soát đối
  kháng 25/09/2026 — 2 dòng đúng lược đồ, 2 vi phạm `thieu-truong-nguon`. Cách xử là thêm
  trường vào lược đồ và khai tên `bo-de-danh-gia` trong `NGUON_DUOC_PHEP` của cổng, **không
  phải** nới luật cổng. Bài học chung: một ràng buộc chỉ có nghĩa khi đã có người thử chạy
  nó, chứ không phải khi đã có người viết nó ra.

## Bốn ví dụ, mỗi nhóm một câu

> Nhắc lại: **bốn câu dưới đây đều là BỊA**, viết ra để minh hoạ các trường. Không câu nào
> thuộc bộ 227 thật.

### 1. `trong-kho` — đáp án nằm sẵn trong ngữ liệu

```json
{"ma": "TK-001", "nguon": "bo-de-danh-gia", "nhom": "trong-kho", "ngon_ngu": "vi",
 "cau_hoi": "Công ty Cổ phần Cơ khí Bình Minh hoạt động trong ngành nào và có những sản phẩm chính nào?",
 "hanh_vi_mong_doi": "tra-loi",
 "dap_an_tham_chieu": "Ngành cơ khí chế tạo; sản phẩm chính gồm kết cấu thép và thiết bị nâng hạ.",
 "tieu_chi_dat": ["nêu đúng ngành", "nêu được ít nhất một sản phẩm chính", "không thêm số liệu không có trong hồ sơ"],
 "tu_bat_buoc": ["cơ khí"], "tu_cam": [],
 "nguon_doi_chieu": "ho-so-dn", "ngay_tao": "2026-09-22",
 "ghi_chu": "Câu dễ nhất trong nhóm: hỏi đúng hai trường có sẵn trong hồ sơ."}
```

### 2. `ngoai-kho` — nghiệp vụ đúng lĩnh vực nhưng không có trong ngữ liệu

```json
{"ma": "NK-001", "nguon": "bo-de-danh-gia", "nhom": "ngoai-kho", "ngon_ngu": "vi",
 "cau_hoi": "Khi lập báo cáo phát triển bền vững, doanh nghiệp thường công bố những nhóm chỉ số nào?",
 "hanh_vi_mong_doi": "tra-loi",
 "dap_an_tham_chieu": "Thường gồm nhóm môi trường, nhóm xã hội và nhóm quản trị.",
 "tieu_chi_dat": ["nêu được ít nhất hai nhóm chỉ số", "không gán câu trả lời cho một doanh nghiệp cụ thể nào trong kho"],
 "tu_bat_buoc": [], "tu_cam": [],
 "nguon_doi_chieu": null, "ngay_tao": "2026-09-22",
 "ghi_chu": "Kiểm kiến thức nền. Trả lời được bằng hiểu biết chung; nói thẳng là không chắc cũng chấp nhận được."}
```

### 3. `bay-chong-bia` — hỏi về thứ không tồn tại

```json
{"ma": "BY-001", "nguon": "bo-de-danh-gia", "nhom": "bay-chong-bia", "ngon_ngu": "vi",
 "cau_hoi": "Tổng công ty Thép Đại Dương niêm yết năm nào và vốn điều lệ bao nhiêu?",
 "hanh_vi_mong_doi": "tu-choi",
 "dap_an_tham_chieu": null,
 "tieu_chi_dat": ["nói rõ không tìm thấy doanh nghiệp này trong dữ liệu", "KHÔNG đưa ra năm niêm yết", "KHÔNG đưa ra con số vốn điều lệ"],
 "tu_bat_buoc": [], "tu_cam": ["tỷ đồng"],
 "nguon_doi_chieu": null, "ngay_tao": "2026-09-22",
 "ghi_chu": "Doanh nghiệp BỊA. Bẫy nằm ở chỗ câu hỏi giả định nó có thật, nên mô hình rất dễ trả lời cho trôi. `tu_cam` chỉ cấm đơn vị tiền — thứ mô hình buộc phải tự bịa mới có; KHÔNG cấm 'niêm yết' hay 'vốn điều lệ' vì hai cụm ấy đã nằm trong đề (R1)."}
```

### 4. `tieng-viet-tong-quat` — năng lực tiếng Việt ngoài nghiệp vụ

```json
{"ma": "TV-001", "nguon": "bo-de-danh-gia", "nhom": "tieng-viet-tong-quat", "ngon_ngu": "vi",
 "cau_hoi": "Viết lại câu sau cho gọn và đúng ngữ pháp: 'Việc triển khai của dự án đã được thực hiện bởi đội ngũ một cách hoàn thành.'",
 "hanh_vi_mong_doi": "tra-loi",
 "dap_an_tham_chieu": "Đội ngũ đã hoàn thành việc triển khai dự án.",
 "tieu_chi_dat": ["câu viết lại đúng ngữ pháp tiếng Việt", "bỏ được lối bị động gượng", "giữ nguyên nghĩa"],
 "tu_bat_buoc": [], "tu_cam": ["bởi"],
 "nguon_doi_chieu": null, "ngay_tao": "2026-09-22",
 "ghi_chu": "Cấm 'bởi' hợp lệ theo R1: từ này nằm trong câu VĂN MẪU cần sửa, không nằm trong phần yêu cầu, và bỏ nó chính là việc phải làm."}
```

> Ví dụ 4 cho thấy R1 cần đọc kỹ: từ bị cấm nằm trong **đoạn trích cần xử lý**, không phải
> trong **yêu cầu**. Khi bộ chạy kiểm R1 một cách máy móc, nó sẽ báo câu này sai. Cách xử
> đúng là **tách riêng trường chứa văn mẫu** (ví dụ thêm `van_ban_dau_vao`) rồi chỉ áp R1
> lên phần yêu cầu — **chưa làm**, ghi lại ở đây để người viết bộ chạy không phải phát hiện
> lại từ đầu.

## Chưa có

- **Bộ 227 câu.** Chưa nằm trong kho.
- **Bộ kiểm hợp lệ** cho R1–R8. Chưa viết. Không có nó thì tám ràng buộc trên chỉ là lời
  khuyên, và lời khuyên thì không chặn được ai.
- **Câu hỏi tiếng Anh.** Trường `ngon_ngu` đã chừa chỗ giá trị `en`, nhưng số câu hiện tại
  là **0**. Chưa đo, nên không có gì để công bố — dù đã có bằng chứng gián tiếp rằng năng
  lực tiếng Anh sẽ thay đổi (tokenizer tệ đi 22,0%, đo 25/09/2026), và bằng chứng gián tiếp
  không thay được nhóm câu.
