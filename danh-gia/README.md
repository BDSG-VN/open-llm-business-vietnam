# danh-gia/ — bộ đánh giá 227 câu

Mọi con số chất lượng mà dự án công bố đều đến từ bộ đề này. Vì vậy tài liệu này bắt đầu
bằng điều quan trọng nhất, không phải bằng bảng kết quả.

---

## ⚠ TODO CHẶN PHÁT HÀNH — BỘ ĐỀ 227 CÂU HIỆN KHÔNG NẰM TRONG KHO

**Trạng thái ngày 25/09/2026: thư mục này chưa có tệp bộ đề nào.**

Hệ quả phải nói thẳng: **mọi con số dưới đây hiện KHÔNG kiểm chứng lại được.** Người đọc
không có cách nào chạy lại, không có cách nào biết 111 câu "trong kho" hỏi cái gì, cũng
không có cách nào phản bác. Một con số không kiểm chứng được thì về mặt khoa học không khác
gì một con số bịa — dù nó được đo thật, và các số này *đã* được đo thật.

Việc phải làm trước khi phát hành, theo thứ tự:

1. **Đưa bộ 227 câu vào `danh-gia/bo-de/`**, đúng lược đồ trong
   [`luoc-do-bo-de.md`](luoc-do-bo-de.md).
2. **Ghi lại cách chấm** cho tới mức chạy lại ra đúng số (xem mục "Cách chấm" bên dưới —
   phần còn thiếu đã được đánh dấu).
3. **Viết bộ chạy đánh giá.** Hiện **chưa có** trong kho.
4. **Chạy lại đường cơ sở** bằng chính bộ đề và bộ chạy đã công bố, rồi đối chiếu với bảng
   22/09/2026. Lệch thì sửa **tài liệu**, không sửa số đo.

Cho tới khi làm xong bốn việc ấy, bảng số dưới đây phải được đọc kèm đúng một chữ:
**chưa kiểm chứng lại được.**

Bộ đề khi đưa vào phải **giữ nguyên, không sửa theo kết quả**. Bộ đề sửa được sau khi nhìn
điểm thì không còn là thước đo, nó thành cái gương.

---

## Bốn nhóm câu hỏi

| Nhóm | Số câu | Hỏi cái gì | Trả lời đúng nghĩa là gì |
|---|---:|---|---|
| Nghiệp vụ **trong kho** | 111 | Nội dung có thật trong ngữ liệu đã nạp | Lấy đúng thông tin có sẵn |
| Nghiệp vụ **ngoài kho** | 31 | Nghiệp vụ cùng lĩnh vực nhưng **không** có trong ngữ liệu | Trả lời được bằng kiến thức nền, hoặc nói thẳng là không biết |
| **Câu bẫy chống bịa** | 60 | Hỏi về thứ **không tồn tại**, hoặc cài tiền giả định sai | **Từ chối bịa.** Điểm cao ở đây nghĩa là mô hình nói "không có" đúng lúc |
| **Tiếng Việt tổng quát** | 25 | Năng lực tiếng Việt ngoài nghiệp vụ | Viết tiếng Việt đúng và tự nhiên |
| **Tổng** | **227** | | |

Nhóm câu bẫy chiếm 60/227 — hơn một phần tư. Đó là chủ ý: với một mô hình tư vấn doanh
nghiệp, **bịa một con số nguy hiểm hơn là không trả lời được.** Người dùng bỏ qua một câu
"tôi không biết"; họ không bỏ qua được một con số sai đã đưa vào báo cáo.

## Đường cơ sở — đo ngày 22/09/2026

| Nhóm | Số câu | Điểm |
|---|---:|---:|
| Nghiệp vụ trong kho | 111 | **0,636** |
| Nghiệp vụ ngoài kho | 31 | **0,539** |
| Lợi ích truy hồi | — | **+0,097** |
| Câu bẫy chống bịa | 60 | **0,953** |
| Tiếng Việt tổng quát | 25 | **0,908** |

Đọc bảng này cho đúng:

- **0,636 là điểm thấp.** Nghiệp vụ trong kho là phần *dễ nhất*: câu trả lời nằm sẵn trong
  ngữ liệu, chỉ cần lấy ra. Được 0,636 ở phần dễ nhất là chỗ còn nhiều việc nhất, không
  phải chỗ để khoe.
- **0,953 ở câu bẫy là con số tốt nhất trong bảng**, và cũng là con số đáng giữ nhất. Mọi
  thay đổi về sau phải kiểm lại số này trước tiên. Hai lý do đã biết trước: mô hình ngôn
  ngữ **nhỏ** bịa kiến thức (không đủ chỗ nhớ sự kiện, nên khi bị hỏi thứ nó không biết,
  đầu ra trôi chảy vẫn là đầu ra bịa), và **độ ổn định sự thật thường giảm sau các giai
  đoạn tinh chỉnh theo sở thích** (RLHF/DPO) — mô hình học cách trả lời *dễ nghe* hơn, và
  dễ nghe đôi khi trái với đúng. Nghĩa là con số này được **dự báo** sẽ tụt ở các mốc sau.
  Đây là dự báo theo hiểu biết chung về mô hình nhỏ, **không phải số đo của BDSG** — nhưng
  biết trước thì phải canh, và phải canh sau **mỗi** giai đoạn tinh chỉnh chứ không chỉ
  một lần ở cuối.
- **0,908 tiếng Việt tổng quát** đến từ mô hình bên thứ ba đang chạy, **không** phải từ
  trọng số của BDSG (xem mục ngay dưới).

### ⚠ Con số "+0,097" cần được làm rõ trước khi công bố

Về số học, `0,636 − 0,539 = 0,097` — đúng bằng con số đang được gọi là "lợi ích truy hồi".
Nhưng **hai cách hiểu sau đây khác hẳn nhau**, và hồ sơ hiện có **không ghi lại** đó là cách
nào:

1. **Chênh lệch giữa hai nhóm câu hỏi khác nhau** (trong kho so với ngoài kho). Nếu là cách
   này thì nó **không phải** lợi ích của truy hồi, vì hai nhóm câu có độ khó khác nhau ngay
   từ đầu; số đo đang trộn "truy hồi giúp được bao nhiêu" với "câu nào khó hơn".
2. **Cùng một bộ câu hỏi, đo hai lần: có truy hồi và không truy hồi.** Chỉ cách này mới
   đúng là lợi ích của truy hồi.

**Việc phải làm:** đo lại theo cách 2 và ghi rõ, hoặc đổi tên con số cho đúng bản chất.
Cho tới lúc đó, không được phát hành câu "truy hồi giúp tăng 0,097". **Chưa đo đúng thứ
đang được gọi tên.**

## ⚠ Đường cơ sở này đo hệ NÀO

Đây là chỗ dễ hiểu nhầm nhất của cả tài liệu, nên viết thẳng:

**BDSG chưa huấn luyện trọng số nào.** Tính đến 25/09/2026, API tự khai
`bdsg_la_trong_so_bdsg = false` cho **mọi** mô hình. Thứ đang chạy tại `llm.bdsg.vn` là một
lớp **truy hồi** (`pg_trgm` + `tsvector` — **không phải** vector, vì cổng LLM hiện không có
mô hình nhúng nào) đặt trước **một mô hình của bên thứ ba**.

Vậy nên:

- Năm con số trên đo **hệ truy hồi + mô hình bên thứ ba**.
- Chúng **không** đo mô hình mà dự án sắp huấn luyện.
- Khi mô hình tự huấn luyện đầu tiên chạy được, điểm của nó **gần như chắc chắn thấp hơn
  nhiều** — một mô hình đủ nhỏ để chạy trên máy cá nhân không so được với mô hình thương mại
  lớn. Điều đó **không phải thất bại**; nó là cái giá của việc người dùng tải mô hình về
  chạy trên máy mình. Nhưng phải công bố hai cột số riêng, **không được để lẫn**, và mọi con
  số phải ghi rõ đo trên hệ nào.

Nói gọn: bảng 22/09/2026 là **điểm xuất phát để so sánh**, không phải thành tích của mô
hình sắp có.

## Cách chấm

**Phần đã biết:** mỗi nhóm cho một điểm trong khoảng `[0; 1]`, càng cao càng tốt; điểm của
nhóm là trung bình điểm các câu trong nhóm.

**Phần CHƯA GHI LẠI — phải bổ sung trước khi phát hành** (mỗi mục dưới đây đều làm số đo
thay đổi, nên thiếu mục nào là không chạy lại được):

- Chấm bằng gì: đối chiếu chuỗi, hay dùng một mô hình làm giám khảo? Nếu là mô hình giám
  khảo thì **mô hình nào, lời nhắc ra sao** — đổi giám khảo là đổi thước đo.
- Câu bẫy tính điểm thế nào: từ chối đúng được 1, trả lời bịa được 0, còn trả lời nửa vời
  thì sao?
- Lời nhắc hệ thống lúc đo, và các tham số sinh (nhiệt độ, số token tối đa).
- Đo một lần hay nhiều lần rồi lấy trung bình. Nếu một lần, **chưa đo được độ dao động** —
  và khi chưa biết độ dao động thì một chênh lệch nhỏ như 0,097 chưa chắc có nghĩa.

### Luật đã học được bằng một lần chấm sai

> **Câu hỏi KHÔNG ĐƯỢC cấm những từ vốn đã nằm trong chính câu hỏi.**

Một bộ chấm từng phạt mô hình vì nó dùng lại một từ có sẵn trong đề bài, rồi kết luận
**sai** rằng "mô hình bịa". Mô hình không bịa; luật chấm hỏng. Bài học rộng hơn: khi bộ lọc
từ chối hàng loạt, **hãy nghi đầu vào và luật chấm trước**, đừng vội kết luận về mô hình —
và tuyệt đối đừng "sửa" bằng cách nới lỏng bộ lọc.

Luật này được ghi thành ràng buộc kiểm tra trong [`luoc-do-bo-de.md`](luoc-do-bo-de.md).

## Ngôn ngữ

Phạm vi ngôn ngữ của dự án, chốt ngày 26/09/2026, là **đúng hai**: tiếng Việt là chính,
tiếng Anh là phụ.

Bộ 227 câu hiện tại phục vụ **tiếng Việt**, cả 227 câu. Về tiếng Anh: **chưa đo** — hiện
không có nhóm câu nào, và không có con số nào để công bố.

Vì sao tiếng Anh vẫn phải có nhóm câu riêng, dù là ngôn ngữ phụ: BDSG huấn luyện từ vựng
**ưu tiên tiếng Việt**, và phép đo ngày 25/09/2026 cho thấy điều đó **làm tiếng Anh tệ đi
22,0%** ở mức nén token. Đó là bằng chứng rằng năng lực tiếng Anh **thay đổi** chứ không
đứng yên — theo hướng nào ở mức *trả lời*, chứ không phải ở mức *nén token*, thì **chưa
biết, vì chưa đo**. Nén tốt hơn không đồng nghĩa trả lời tốt hơn, và chiều ngược lại cũng
vậy. Không được lấy kết quả tiếng Việt để suy ra tiếng Anh.

Khi bổ sung, thêm nhóm mới kèm số câu, **đừng sửa 227 câu đang có** — sửa bộ đề cũ là mất
luôn khả năng so với đường cơ sở 22/09/2026.

## Chạy đánh giá

**Chưa có bộ chạy trong kho.** Khi viết, nó phải: đọc bộ đề theo lược đồ đã công bố, ghi lại
đủ thông tin để chạy lại ra đúng số (mô hình, ngày, tham số, phiên bản bộ đề), và in điểm
theo **từng nhóm** — không gộp thành một con số duy nhất. Một con số gộp sẽ giấu mất đúng
thứ đáng lo: điểm câu bẫy tụt trong khi điểm nghiệp vụ tăng, gộp lại trông vẫn "tốt lên".
