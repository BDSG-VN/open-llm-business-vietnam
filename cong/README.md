# cong/ — cổng kiểm tự động trước khi đẩy lên kho công khai

Thư mục này có **bảy cổng** và một kịch bản chạy tất cả. Chúng chạy **trước** khi đẩy,
không phải sau.

Bảy cổng ấy chặn **ba họ lỗi khác hẳn nhau**, và vì khác nhau nên chúng cần luật khác nhau:

| | Chặn gì | Thiệt hại nếu lọt |
|---|---|---|
| **Cổng 1–5** | thứ **lọt RA** khỏi kho: bí mật, hạ tầng, dữ liệu người khác, đường khai thác, danh tính | không thu hồi được — xem bảng ngay dưới |
| **Cổng 6** | một **lời khai sai Ở LẠI** trong kho: tài liệu nói sai về nguồn gốc mô hình và phạm vi ngôn ngữ | không rò gì cả, nhưng người đọc bị dẫn sai |
| **Cổng 7** | một **cửa hậu Ở LẠI** trong kho: mã chạy lệnh tuỳ ý trên máy khác, khoá ghi cứng, thực thi động | không rò gì lúc đẩy, nhưng ai chạy mã ấy thì mất toàn quyền máy chủ |

Ba họ này hỏng theo ba cách, và đừng gộp chúng: cổng 1–5 hỏng lúc **đẩy**, cổng 6 hỏng lúc
**đọc**, cổng 7 hỏng lúc **chạy**.

## Vì sao phải chặn trước, không phải dọn sau

Đẩy lên kho công khai là việc **một chiều**. GitHub giữ lịch sử, các bản fork giữ bản sao,
bộ nhớ đệm máy tìm kiếm giữ nội dung. `git push --force` xoá được nhánh, nhưng không xoá
được thứ người khác đã lấy về.

Hệ quả thực tế, theo đúng thứ tự phải làm:

| Lỡ đẩy thứ gì | Xoá commit có cứu được không | Việc thật phải làm |
|---|---|---|
| Khoá API, token | **Không** | Thu hồi khoá, cấp khoá mới |
| Địa chỉ máy chủ, đường dẫn nội bộ | **Không** | Không có cách thu hồi. Chỉ còn cách đổi hạ tầng |
| Dữ liệu khách hàng | **Không** | Đây là lý do cổng 3 là cổng tuyệt đối |
| Đường khai thác lỗ hổng chưa vá | **Không** | Chạy đua vá trong khi người khác đã có bản sao |

Không cột nào trong bảng trên có chữ "có". Đó là toàn bộ lý do tồn tại của thư mục này.

## Chạy

```bash
cong/chay-tat-ca.sh                 # tự kiểm + quét toàn kho  ← chạy cái này trước khi đẩy
cong/chay-tat-ca.sh --goc <thư mục> # quét một thư mục khác
cong/chay-tat-ca.sh --chi-tu-kiem   # chỉ bắt các cổng chứng minh chúng cắn

python3 cong/khong-bi-mat.py            # chạy riêng một cổng
python3 cong/khong-bi-mat.py --tu-kiem  # bài thử ngược của riêng cổng đó
```

Mã thoát của mọi cổng và của kịch bản: `0` đạt · `1` có vi phạm · `2` cổng tự vỡ.
**Mã 2 cũng là hỏng.** Cổng không chạy được thì kết luận duy nhất được phép rút ra là
"chưa biết", không phải "sạch".

`chay-tat-ca.sh` **luôn chạy bài tự kiểm trước khi quét**. Một cổng luôn trả "sạch" trông
y hệt một cổng hỏng; phải bắt nó cắn được chuỗi cố tình cài vào rồi mới tin lời nó nói về
kho. Cổng nào trượt tự kiểm thì bước quét của nó bị **bỏ hẳn** và tính là hỏng — chứ không
phải chạy rồi lấy kết quả.

## Bảy cổng

| Cổng | Chặn gì | Vì sao | Miễn trừ nội dòng |
|---|---|---|---|
| `khong-bi-mat.py` | khoá API (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, Slack, Google), khoá riêng PEM, JWT, chuỗi kết nối có mật khẩu, tệp `.env`, tệp khoá `.pem/.key/.p12` | Lộ khoá là mất quyền kiểm soát tài khoản. Xoá commit vô ích, phải thu hồi khoá | **Không** |
| `khong-ha-tang.py` | IPv4 công cộng, đường dẫn vận hành, tên container, tên miền quản trị, số cổng nội bộ | Hạ tầng **không có nút thu hồi**. Lộ là lộ vĩnh viễn, và là bản đồ cho người dò | Có |
| `khong-du-lieu-cam.py` | bản ghi không chứng minh được nguồn; nguồn bị cấm (dữ liệu CRM khách hàng, tài liệu có cấp phép bên thứ ba, nội dung người khác, đầu ra máy sinh) | Dữ liệu của người khác thì không có lý do kỹ thuật nào biến thành của mình | **Không** |
| `khong-lo-hong.py` | cookie phiên kèm giá trị, cờ bảo mật bị tắt, đường dẫn và số dòng của hệ đang chạy, mô tả khai thác gắn với vật thể cụ thể | Viết đường khai thác mất 10 giây, vá hệ mất nhiều ngày. Khoảng chênh ấy là cửa sổ tấn công | Có |
| `khong-danh-tinh.py` | danh tính cá nhân do người vận hành khai trong `cong/danh-tinh.local` (tệp bị `.gitignore` chặn) | Bốn cổng trên ĐẠT toàn kho, rồi một lượt soát TAY vẫn tìm ra họ tên thật của chủ dự án. Thứ soát tay tìm được phải trở thành cổng | Có |
| `khong-tham-chieu-ngoai.py` | tên một **dự án ngoài** (mọi cách viết hoa), và tên một **ngôn ngữ đã bị đưa ra khỏi phạm vi** dự án ngày 26/09/2026 — gồm ba cách viết tên ngôn ngữ ấy, ký tự chữ Hán, mã ngôn ngữ dạng `zh` + gạch nối + mã vùng, và tên một thư viện tách từ chỉ dùng cho ngôn ngữ ấy | Xoá tên dự án ngoài mà giữ phần dẫn xuất thì vừa phạm Apache-2.0 điều 4 (giữ ghi công, nêu rõ chỗ đã sửa) vừa là **lời khai sai về nguồn gốc mô hình** — đúng thứ kho này đặt ra để chống | Có |
| `khong-cua-hau.py` | ba họ khuôn mã: gọi lệnh hệ thống bằng **chuỗi ghép từ tham số** (hàm luôn đi qua trình bao, cờ trình bao bật, chuỗi f, nối chuỗi, và **SSH làm phương tiện gọi công cụ**); **đường dẫn khoá riêng SSH ghi cứng**; **thực thi động** | Kho này đang thành một hệ điều hành cho doanh nghiệp. Một trình điều khiển mở tiến trình con chạy lệnh trên máy khác thì vòng qua nhân: mất cả quyền, hạn mức, nhật ký lẫn ranh giới đọc/ghi. Số đo làm cổng này ra đời nằm ở mục riêng bên dưới | Có |

Chi tiết đầy đủ nằm trong phần đầu mỗi tệp `.py`, kèm số đo và ngày đo.

### Cổng 6 nói gì, và vì sao tài liệu này KHÔNG viết thẳng chuỗi nó chặn

`khong-tham-chieu-ngoai.py` chặn hai thứ, và cả hai đều là **lời khai sai ở lại trong kho**
chứ không phải rò rỉ ra ngoài:

1. **Tên một dự án ngoài.** Kiến trúc và bộ huấn luyện của kho này do BDSG viết độc lập,
   dựng từ kỹ thuật đã công bố trong bài báo (RMSNorm arXiv:1910.07467, RoPE
   arXiv:2104.09864, GQA arXiv:2305.13245, SwiGLU arXiv:2002.05202, pre-norm
   arXiv:2002.04745). Một cái tên thượng nguồn còn sót lại trong tài liệu là một lời khai
   sai về nguồn gốc mô hình.
2. **Tên một ngôn ngữ đã bị đưa ra khỏi phạm vi** ngày 26/09/2026. Phạm vi còn đúng hai:
   tiếng Việt chính, tiếng Anh phụ.

**Tài liệu này cố ý không viết thẳng các chuỗi ấy ra**, cùng lý do với ô ví dụ miễn trừ ở
trên: `cong/README.md` nằm trong phạm vi quét, nên một chuỗi viết nguyên vẹn ở đây sẽ bị
chính cổng bắt, và tài liệu mô tả cổng lại trở thành vi phạm đầu tiên của cổng. Muốn biết
chính xác cổng chặn chữ gì thì **đọc phần khai biến ở đầu tệp `.py`** — nó đọc được dù
không viết chuỗi ra.

Chính tệp cổng cũng chơi đúng thủ thuật đó: mọi chuỗi cấm trong đó được **ghép lúc chạy**
từ hai mảnh, nên trên đĩa chuỗi không bao giờ xuất hiện nguyên vẹn. Và cổng **tự quét chính
nó** — không có dòng loại trừ nào cho `__file__`. Bài tự kiểm còn chép nguyên mã nguồn của
chính nó vào thư mục tạm rồi quét, đòi kết quả **0 vi phạm, 0 miễn trừ**.

Phép thử ấy không phải trang trí: **nó bắt lỗi ngay ở lần chạy đầu tiên, 26/09/2026.** Bản
đầu viết biên giới khối chữ Hán bằng dãy thoát `\u…` trong chuỗi nguồn; công cụ ghi tệp đã
**diễn giải** dãy thoát ấy trước khi ghi, nên trên đĩa nó thành bốn ký tự chữ Hán thật —
đúng thứ cổng sinh ra để chặn, nằm ngay trong tệp cổng. Bản sửa dựng biên giới bằng `chr()`
để trên đĩa chỉ còn chữ số hex.

Đó là lý do luật "cổng phải tự quét chính nó" tồn tại, và nó đến từ một lỗi thật khác:
**bản đầu của `khong-danh-tinh.py` viết bốn danh tính thật vào phần tự kiểm làm mẫu thử.**
Nó ĐẠT — vì tự loại mình khỏi phạm vi quét — rồi được đẩy lên kho công khai, mang theo đúng
bốn thứ nó sinh ra để chặn. Một bộ dò mang theo danh sách thứ nó dò thì chính nó là chỗ rò.

### Ca miễn trừ hợp pháp của cổng 6: mục lịch sử thay đổi

Cổng 6 **có** miễn trừ nội dòng, và ca hợp pháp của nó rất cụ thể: muốn ghi trung thực rằng
ngày 26/09/2026 dự án đã **bỏ** một ngôn ngữ khỏi phạm vi thì phải gọi tên ngôn ngữ ấy.
Không có đường thoát hợp pháp thì người viết chỉ còn hai lựa chọn — nói dối lịch sử, hoặc
tắt cổng. Cả hai đều tệ hơn một miễn trừ có ghi lý do.

Đối xứng với điều đó, cổng 6 **cố ý không chặn** mã ngôn ngữ `zh` trần (không có gạch nối
và mã vùng). Lý do đo được: chuỗi `zh` nằm trong **"Zhang"** — họ của một trong hai tác giả
bài báo RMSNorm mà chính kho này bắt buộc phải trích dẫn. Một cổng cắt oan tên tác giả bài
báo sẽ bị tắt, và **một cổng bị tắt là một cổng không tồn tại**. Hệ quả phải chấp nhận và
đã khai trong mục PHẠM VI TỰ KHAI: một giá trị enum `zh` trần sẽ lọt qua.

Cùng họ với ca ấy: cổng chỉ bắt tên ngôn ngữ khi nó đi **sau chữ "tiếng"**. Bắt chữ đó đứng
một mình sẽ cắt oan `trung bình`, `tập trung`, `Trung tâm`, `muc_tin_cay = "trung-binh"` —
cả bốn đều là tiếng Việt thường ngày và **đều có thật trong kho này**. Bài tự kiểm có dòng
đối chứng cho từng ca.

### Tên trường cấu hình chuẩn transformers ĐƯỢC GIỮ

`hidden_size`, `num_hidden_layers`, `num_attention_heads`, `num_key_value_heads`,
`intermediate_size`, `vocab_size`, `rms_norm_eps`, `rope_theta`, `tie_word_embeddings` là
quy ước chung của cả hệ sinh thái mô hình mở, không phải tên riêng của ai. Giữ nguyên bộ
tên ấy là điều kiện để trọng số BDSG nạp được ở nơi khác.

Bài tự kiểm của cổng 6 có một **dòng sạch gồm đúng các tên ấy**, để bất kỳ ai siết cổng về
sau cũng lập tức thấy chúng phải lọt. Đây là ví dụ cho luật *"ngoại lệ không có bài thử là
lỗ thủng"* áp theo chiều ngược: thứ **phải lọt** cũng cần một bài thử, nếu không lần siết
luật sau sẽ vô tình cắt mất nó mà không ai biết.

### Cổng 7 nói gì, và SỐ ĐO nào làm nó ra đời

Cổng 7 là cổng duy nhất sinh ra từ việc đọc **mã đang chạy thật của chính BDSG**, chứ không
từ một lượt soát kho.

Ngày 26/09/2026, BDSG đã có **một máy chủ MCP chạy thật**. Nó nằm **ngoài** kho này, nên ở
đây chỉ ghi số đo, không ghi đường dẫn: **221 dòng, 7 công cụ**, nói JSON-RPC qua stdio,
phục vụ Unomi CDP + OpenMetadata (OpenMetadata đang quản trị **3 nguồn**: một MariaDB, một
Postgres, một MySQL). Ba giới hạn đã đo:

| # | Đo được gì | Vì sao nó là vấn đề |
|---|---|---|
| a | **Vận chuyển là SSH vào máy chủ sản phẩm**, bằng một khoá root ghi cứng trong mã | Mỗi công cụ là **một lệnh tuỳ ý trên production**. Đó không phải trình điều khiển, đó là **cửa hậu có giao diện đẹp** |
| b | 7 công cụ, một lĩnh vực, một tệp phẳng | Thêm một nền tảng thì phải sửa tệp — không mở rộng được ra 18 nền tảng |
| c | **Không có lớp quyền, không có nhật ký** — tìm ba chữ `quyen`, `auth`, `nhat_ky` trong mã ấy trả về **rỗng** | Không trả lời được câu **"ai đã làm gì"** |

Giới hạn (a) là toàn bộ lý do cổng này tồn tại. Bốn quyết định kiến trúc đã chốt cùng ngày
nói rằng: **MCP là ranh giới lời gọi hệ thống**; **nhân** giữ danh tính, quyền, hạn mức,
nhật ký; **trình điều khiển** chỉ đổi một lời gọi công cụ thành một lời gọi API của nền
tảng nó phụ trách; **mặc định chỉ đọc**.

Một trình điều khiển mở tiến trình con để chạy lệnh trên máy khác thì **phá cả bốn điều
cùng lúc** — nó vòng qua nhân, nên không có quyền, không có hạn mức, không có nhật ký, và
không có ranh giới đọc/ghi nào cả.

**Cổng 7 không làm gì với máy chủ MCP cũ.** Nó chỉ chặn khuôn ấy **tái xuất hiện trong kho
này**. Ranh giới ấy phải nói thẳng, vì một cổng được tin quá mức còn nguy hơn không có cổng.

#### Cổng 7 đã được chứng minh là CẮN trên vật thật

Ngoài bài `--tu-kiem`, cổng 7 còn được chạy thử trên **một bản sao của chính tệp máy chủ
MCP ấy**, đặt trong thư mục tạm ngoài kho. Kết quả ngày 26/09/2026: **HỎNG, 3 vị trí, đều
ở dòng 12** — `ssh-lam-van-chuyen`, `khoa-ssh-ghi-cung`, `khoa-ssh-co-i`. Đó là phép thử
đáng tin hơn mọi mẫu tự cài: cổng bắt đúng dòng mã đã có thật.

Trong báo cáo ấy, ba dòng thuộc họ khoá **chỉ in vị trí, không in giá trị** — đúng như luật
ở mục cuối tài liệu này.

#### Chỗ mù của cổng 7 — đọc trước khi tin nó

Ba chỗ mù lớn nhất, khai thẳng vì một cổng không nói rõ chỗ mù của mình sẽ được hiểu là bảo
vệ toàn diện:

- **Cổng đọc từng dòng một.** Chuỗi lệnh ghép ở dòng trên rồi dòng dưới chỉ gọi một biến
  thì cổng **không thấy gì**. Đây là chỗ mù lớn nhất và không vá được bằng biểu thức chính
  quy — muốn vá thật phải phân tích cây cú pháp, và đó là một cổng khác, **chưa viết**.
- **Hai lời gọi thực thi động có dấu cách trước ngoặc thì lọt.** Đánh đổi có chủ ý: cho
  phép dấu cách thì mọi câu tiếng Việt kiểu *"bộ eval (đánh giá) 227 câu"* bị cắt oan.
- **Cổng không biết dữ liệu đến từ đâu.** Nó không phân biệt được thực thi động trên hằng
  số với thực thi động trên thân yêu cầu, nên nó **coi mọi lời gọi động là vi phạm**
  (fail-closed) và để đường thoát ở miễn trừ có lý do.

#### Bốn dòng đối chứng của cổng 7 lấy NGUYÊN VĂN từ kho này

Phần "dòng sạch" của bài tự kiểm quan trọng ngang phần "mẫu phải bắt", vì bốn ca dưới đây
**có thật** và cắt oan bất kỳ ca nào cũng đủ làm cổng bị tắt:

| Dòng đối chứng | Ở đâu trong kho | Vì sao phải lọt |
|---|---|---|
| `mo_hinh.eval()` | 15 chỗ trong `mo-hinh/` và `huan-luyen/` | chế độ suy luận của PyTorch, không liên quan gì tới thực thi động |
| `mau.exec(van)` | `chat/chat.js` | `RegExp.exec` của JavaScript |
| bảng liệt kê tên khoá riêng dạng khoá từ điển | `cong/khong-bi-mat.py` | đó là **bảng dò của cổng 1**. Cắt oan nó là cổng 7 vô hiệu hoá cổng 1 |
| `ast.literal_eval(...)` | khuôn phổ biến | bộ phân tích **an toàn**, không phải lời gọi động |

Chính vì ca thứ ba mà luật khoá của cổng 7 **bắt buộc phải có dấu gạch chéo đứng trước tên
khoá**: một luật bắt tên trần sẽ cắt oan đúng cổng bí mật của kho này.

#### Cổng 7 cũng tự quét chính nó — và lần đầu nó bắt được chính nó

Giống cổng 6, cổng 7 **không có dòng loại trừ nào cho `__file__`**, mọi khuôn cấm trong tệp
đều được **ghép lúc chạy** từ hai mảnh trở lên, và bài tự kiểm chép nguyên mã nguồn của
chính nó vào thư mục tạm rồi đòi **0 vi phạm, 0 miễn trừ**.

Phép thử ấy **bắt lỗi ngay lần chạy đầu tiên, 26/09/2026**, ở đúng hai chỗ, và cả hai đều
là **dòng chú thích đang giải thích luật**: một dòng viết liền tên chỉ thị trỏ tệp khoá,
một dòng nêu ví dụ đầy đủ về cách gọi kèm cờ chỉ định khoá. Nói cách khác: **câu văn mô tả
luật lại chính là câu vi phạm luật.** Bản sửa mô tả hai khuôn ấy bằng lời, và chỉ vào phần
ghép chuỗi trong `tu_kiem()` — nơi khuôn đầy đủ được dựng **lúc chạy** chứ không nằm trên
đĩa.

Đây là lần thứ hai cùng một lỗi xảy ra trong thư mục này (lần trước là biên giới khối chữ
Hán trong cổng 6), và là lý do luật *"cổng phải tự quét chính nó"* không được bỏ.

## Hai nguyên tắc mà cổng nào cũng phải giữ

### 1. Cổng phải TỰ KHAI PHẠM VI

Mỗi cổng mở đầu bằng mục **PHẠM VI TỰ KHAI**: nó quét cái gì, và **nó không quét cái gì**.
Phần thứ hai quan trọng hơn. Một cổng không nói rõ chỗ mù của mình sẽ được người ta hiểu
là bảo vệ toàn diện, và đó là lúc nó nguy hiểm hơn cả không có cổng.

Những chỗ mù đã biết, tính đến 25/09/2026:

- **Ảnh chụp màn hình**: không cổng nào đọc. Một ảnh terminal lộ nhiều hơn mọi thứ các cổng
  bắt được. Phải soi bằng mắt.
- **IPv6**: chưa có luật. Chưa đo, đừng tưởng đã chặn.
- **Tệp nhị phân và trọng số mô hình**: không mở ra đọc. Bí mật nằm trong trọng số là thứ
  **chưa đo**. Riêng cổng bí mật thì báo hỏng nếu gặp tệp nhị phân có đuôi chưa khai —
  thà bắt khai còn hơn im lặng bỏ qua.
- **Lịch sử git**: các cổng quét cây thư mục hiện tại, không quét commit cũ.

Vì vậy, dòng cuối của bảng tổng kết viết đúng như nó là: *"không tìm thấy thứ đã biết cách
tìm"*, chứ không phải *"kho đã an toàn"*.

### 2. Cổng phải được THỬ NGƯỢC — phải chứng minh nó CẮN

Mọi cổng đều có `--tu-kiem`: dựng một thư mục tạm, **cố tình cài vào đó thứ phải bị bắt**,
chạy chính hàm quét ấy, rồi đòi hai điều — bắt đủ mọi mẫu đã cài, và **không** bắt nhầm các
dòng sạch làm đối chứng.

Nguyên tắc này không phải lý thuyết. Nó sinh ra từ một phép đo sai suýt cho kết luận ngược:

> Câu lệnh dò địa chỉ IP viết cho `git grep` có dùng `\b`. `git grep` chạy biểu thức chính
> quy POSIX ERE, **không hiểu `\b`**, nên trả về 0 kết quả — trong khi dữ liệu có IP thật.
> Suýt kết luận "kho sạch".

Cho nên: mọi cổng ở đây viết bằng `re` của Python, **không** dựa vào `git grep`; và
`khong-ha-tang.py --tu-kiem` cài sẵn một chuỗi IP công cộng để chứng minh cổng cắn được nó.

Cùng họ với bẫy ấy, hai thứ nữa đã gặp thật và đã được xử trong mã:

- **Một byte NUL** làm `grep` im lặng coi cả tệp là nhị phân rồi bỏ qua; `file` chỉ báo
  `data`. Ở đây tệp nhị phân đuôi lạ bị **báo hỏng**, không được bỏ qua im lặng.
- **Số tiền kiểu Việt Nam trông y hệt địa chỉ IP.** Lần quét ngữ liệu 25/09/2026 có 5 khớp
  "địa chỉ IP" thì cả 5 đều là số tiền. Cách xử **không phải** nới luật, mà là siết đúng
  chỗ: octet có số 0 đứng đầu thì không phải IP (`086`, `000`), hai bên khớp không được
  dính chữ số hay dấu chấm, và ngay sau khớp là "đồng"/"VND" thì là tiền.

## Thêm ngoại lệ cho đúng cách

### Cổng nào cho miễn trừ, cổng nào không — và vì sao lệch nhau

- `khong-ha-tang`, `khong-lo-hong`, `khong-danh-tinh`, `khong-tham-chieu-ngoai` và
  `khong-cua-hau` **có** miễn trừ nội dòng. Năm cổng này là heuristic, chắc chắn có dương
  tính giả thật, và một cổng không có đường thoát hợp pháp sẽ bị người ta tắt hẳn — mất cả
  cổng. Mỗi cổng có một ca hợp pháp cụ thể, và ca của `khong-cua-hau` là: **tài liệu kiến
  trúc phải trưng được khuôn bị từ chối**. Muốn giải thích vì sao SSH-vào-production là sai
  thì phải cho người đọc thấy nó trông như thế nào.
- `khong-bi-mat` và `khong-du-lieu-cam` **không** có. Hai cổng này tuyệt đối: không có lý do
  nào đủ tốt để giữ một khoá thật hay dữ liệu khách hàng trong kho công khai. Nếu bị bắt
  oan thì phải sửa **luật**, không phải mở **lỗ**.

### Cú pháp miễn trừ

Ghi ngay trên chính dòng bị bắt, theo dạng:

```
<dấu miễn trừ> <tên-cổng> ly-do=<lý do cụ thể>
```

- `<dấu miễn trừ>` là chuỗi `cong` nối với `:bo-qua`.
- `<tên-cổng>` là một trong năm cổng có miễn trừ: `khong-ha-tang`, `khong-lo-hong`,
  `khong-danh-tinh`, `khong-tham-chieu-ngoai`, `khong-cua-hau`.
- Phần `ly-do=` là **bắt buộc**. Miễn trừ thiếu lý do thì chính nó bị tính là vi phạm, mã
  `mien-tru-khong-ly-do`. Một ngoại lệ không lý do là một lỗ thủng mà vài tháng sau không
  ai nhớ vì sao đã mở — và vì không ai nhớ, không ai dám đóng.

> Tài liệu này **cố ý không viết ví dụ đầy đủ đã ghép sẵn**. Một ví dụ đầy đủ sẽ bị chính
> cổng đếm là "một miễn trừ đang dùng", và con số trên bảng tổng kết sẽ sai ngay từ dòng
> đầu tiên. Hiện tại số ấy là **0**, và nó đáng được giữ đúng.

Mọi miễn trừ đang dùng đều được **đếm và in ra** ở đầu báo cáo mỗi cổng. Đó là chủ ý: ngoại
lệ phải nhìn thấy được, không được trở thành thứ vô hình.

### Ba việc phải làm khi thêm ngoại lệ

1. **Ưu tiên sửa nội dung trước.** Cần một địa chỉ IP làm ví dụ? Dùng dải RFC5737 —
   `192.0.2.x`, `198.51.100.x`, `203.0.113.x` — vốn sinh ra để làm ví dụ và không trỏ tới
   máy nào.
2. **Viết lý do cụ thể.** "dương tính giả" không phải lý do. "số tiền trong báo cáo tài
   chính, không phải địa chỉ máy chủ" mới là lý do.
3. **Thêm một ca vào `tu_kiem()`.** Nếu ngoại lệ mở rộng tới mức làm thủng một trường hợp
   khác, bài thử ngược phải phát hiện được. **Ngoại lệ không có bài thử là lỗ thủng.**

### Nới luật thì phải khai số đo

Muốn thêm một nguồn vào `NGUON_DUOC_PHEP` của `khong-du-lieu-cam.py`, phải kèm **số đo và
ngày đo**, như các nguồn đang có. Nguồn chưa khai thì mặc định là **chưa được phát hành** —
cổng không đoán hộ. Đây là ý nghĩa của chữ *fail-closed*: bản ghi thiếu trường `nguon` bị
tính là hỏng không phải vì nó chắc chắn bẩn, mà vì **nó không chứng minh được là sạch**.

Ngoại lệ tốt nhất là ngoại lệ không phải tồn tại. `NGOAI_LE_TEP` trong
`khong-du-lieu-cam.py` hiện **rỗng**, và đó là kết quả của một lần sửa thật: bản đầu bắt
dấu hiệu nguồn cấm trên mọi tệp văn bản, chạy ngày 25/09/2026 thì bắt 15 chỗ trong
`MODEL-CARD.md`, `README.md` và `bo-du-lieu/README.md` — toàn bộ là bảng liệt kê *"đã loại
nguồn nào và vì sao"*. Cổng đang phạt người viết vì họ ghi rõ mình đã loại cái gì. Thay vì
mở ngoại lệ cho từng tệp, ranh giới được sửa lại: xét **hình dạng** chứ không xét **chuỗi**.
Nhắc tên nguồn trong câu văn là tài liệu; một bản ghi của nguồn ấy dán vào giữa tài liệu mới
là rò rỉ. Sau khi sửa, không tệp nào cần ngoại lệ nữa.

## Khi thêm một cổng mới

Khai tên tệp vào mảng `CONG_MONG_DOI` trong `chay-tat-ca.sh`. Kịch bản **cố ý không dùng**
`*.py`: glob im lặng bỏ qua cổng bị xoá, và bảng tổng kết vẫn "toàn ĐẠT" trong khi kho đã
mất một cổng. Ngược lại, tệp `.py` nằm trong `cong/` mà không có trong danh sách sẽ bị báo
hỏng — vì một cổng không bao giờ được gọi thì không bảo vệ gì cả, nó chỉ tạo cảm giác an
toàn. Đó là kiểu hỏng tệ nhất: hỏng mà không báo.

Cổng mới phải có đủ: mục **PHẠM VI TỰ KHAI** (gồm phần *không* quét), `--tu-kiem` với cả
mẫu-phải-bắt lẫn dòng-sạch-đối-chứng, mã thoát `0/1/2`, và **không bao giờ in ra giá trị bí
mật** — chỉ in vị trí. In giá trị ra là làm lộ lần thứ hai, lần này vào log CI, mà log CI
thường dễ đọc hơn cả kho.
