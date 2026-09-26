#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Máy chủ HTTP cho giao diện chat BDSG — thư viện chuẩn, không phụ thuộc ngoài.

CHẠY:
    .venv/bin/python3 phuc-vu/may_chu.py
    # rồi mở http://127.0.0.1:8765

BÀI TỰ KIỂM (không cần GPU, không cần mô hình):
    .venv/bin/python3 phuc-vu/thu_may_chu.py

═══ TỆP NÀY CÀI ĐÚNG HỢP ĐỒNG Ở `chat/README.md` ═══

Sáu đường, không hơn:

    GET    /api/mo-hinh
    POST   /api/hoi              → text/event-stream (batdau · chu · loi · xong)
    GET    /api/hoi-thoai
    GET    /api/hoi-thoai/<id>
    DELETE /api/hoi-thoai/<id>
    GET    /api/toi

`POST /api/dang-xuat` mà giao diện gọi khi bấm nút thoát KHÔNG được cài ở bản này:
chưa có đăng nhập thì không có gì để đăng xuất. Giao diện nhận 404 rồi vẫn quay về
trang đầu, nên không có gì hỏng — nhưng phải nói ra chứ không để người sau tự đoán.

═══ PHỤ THUỘC: `phuc-vu/cong_mo_hinh.py` VÀ `phuc-vu/cau_hinh.py` ═══

Hai tệp ấy do nhóm cổng mô hình viết và chúng đã có mặt (26/09/2026). Máy chủ này
vẫn chạy được KHI THIẾU chúng: mọi đường trừ `POST /api/hoi` hoạt động bình thường,
còn `POST /api/hoi` trả `event: loi` nói thẳng là cổng mô hình nội bộ chưa cài. Đó
là lựa chọn có chủ ý — một máy chủ từ chối khởi động vì thiếu một mô-đun thì người
mới không bao giờ thấy được giao diện, còn một máy chủ im lặng trả lời rỗng thì tệ
hơn nữa.

Phần tệp này gọi tới (ghi ra đây vì đây là mặt tiếp giáp giữa hai nhóm):

    cau_hinh.CauHinhPhucVu.tu_moi_truong()
        Dựng cấu hình từ biến môi trường. Ném `LoiCauHinh` khi thiếu `BDSG_VLLM_URL`
        — cố ý không có địa chỉ mặc định, để không bao giờ có chuyện chương trình
        chạy được mà trỏ vào một máy không ai định trỏ tới.

    cau_hinh.bdsg_la_trong_so_bdsg(ma_mo_hinh) -> bool
        Nguồn sự thật DUY NHẤT cho cờ cùng tên ở `GET /api/mo-hinh`. Tệp này KHÔNG
        tự quyết định giá trị ấy.

    cong_mo_hinh.CongMoHinh(cau_hinh).hoi_dong_chay(tin_nhan, ..., thu_thap=dict)
        Bộ sinh, mỗi lần sinh ra MỘT mẩu chữ (`str`). `tin_nhan` theo dạng OpenAI:
        [{"role": "user"|"assistant", "content": "..."}]. Sau khi bộ sinh chạy hết,
        `thu_thap["mo_hinh_that"]` mang tên mô hình đọc được — dùng dict thay cho
        giá trị trả về vì vòng `for` không bao giờ thấy giá trị trả về của hàm sinh.

    cong_mo_hinh.LoiKhongNoiDuocMayNoiBo
        Lớp ngoại lệ khi không nói chuyện được với máy phục vụ nội bộ.

BẪY ĐÃ SUÝT DÍNH, GHI LẠI ĐỂ ĐỪNG AI VIẾT LẠI:
`cong_mo_hinh.doi_chieu_mo_hinh(da_gui, doc_duoc)` KHÔNG trả về bool — nó trả về
TÊN mô hình thật (một chuỗi). Dùng nó làm điều kiện "hai tên có lệch nhau không"
thì mọi câu trả lời đều lệch, vì một chuỗi không rỗng luôn đúng. Tệp này so bằng
`!=` và không gọi hàm ấy. Hàm ấy đã được cổng mô hình gọi rồi, kết quả nằm sẵn
trong `thu_thap["mo_hinh_that"]`.

═══ BỐN LUẬT CỦA BẢN NÀY, VÀ VÌ SAO ═══

1. MẶC ĐỊNH VÀ DUY NHẤT GỌI MÔ HÌNH NỘI BỘ.

   Không có đường dự phòng nào trỏ ra ngoài. Không có chuỗi "thử cục bộ trước, rơi
   sang đám mây sau". Một chuỗi như thế phá đúng thứ hệ này hứa: người dùng tưởng
   mình đang chạy cục bộ, còn câu hỏi thì âm thầm đi ra ngoài. Khi máy nội bộ hỏng,
   câu trả lời đúng là MỘT CÂU BÁO LỖI, không phải một câu trả lời từ nơi khác.

   Đo được chứ không phải lời hứa: tệp này KHÔNG nhập bất kỳ thư viện gọi mạng ra
   nào (`urllib.request`, `http.client`, `requests`, `httpx`, `socket`). Bài tự
   kiểm đọc mã nguồn tệp này và kiểm đúng điều đó. Toàn bộ việc gọi mô hình đi qua
   `cong_mo_hinh` — một chỗ, kiểm được.

2. KHÔNG CÓ XÁC THỰC ⇒ CHỈ NGHE 127.0.0.1.

   Máy chủ này TỪ CHỐI KHỞI ĐỘNG nếu bị bảo nghe ngoài loopback, trừ khi người vận
   hành khai tường minh qua biến môi trường. Lý do: một máy chủ không xác thực mà
   nghe 0.0.0.0 là một kho dữ liệu mở cho cả mạng — mọi hội thoại của "người dùng
   demo" thuộc về bất kỳ ai gọi tới được, vì danh tính ở bản này là một hằng số chứ
   không phải một phiên đăng nhập.

3. BẢN NÀY LÀ DEMO MỘT NGƯỜI. CHƯA DÙNG ĐƯỢC CHO NHIỀU NHÂN VIÊN.

   `GET /api/toi` trả một danh tính cố định và tự khai `xacThuc: false`. Lớp phân
   quyền hội thoại trong `kho_hoi_thoai.py` là thật và đã được kiểm, nhưng nó phân
   quyền theo một danh tính mà HIỆN CHƯA AI PHẢI CHỨNG MINH. Hai việc khác nhau:
   phần khó (điều kiện sở hữu nằm trong câu lệnh SQL) đã xong, phần còn thiếu là
   đăng nhập.

4. TRỌNG SỐ LÀ CỦA GOOGLE, KHÔNG PHẢI CỦA BDSG.

   `GET /api/mo-hinh` trả `bdsg_la_trong_so_bdsg: false` và một khối `nen` nói rõ
   nhà cung cấp, mã trọng số, giấy phép và liên kết. BDSG PHỤC VỤ trọng số Google;
   BDSG chưa tinh chỉnh trọng số nào. Ngày nào có trọng số do BDSG huấn luyện thì
   đổi cờ ấy — và chỉ ngày ấy.

═══ BIẾN MÔI TRƯỜNG ═══

    BDSG_CHAT_DIA_CHI      địa chỉ nghe            (mặc định 127.0.0.1)
    BDSG_CHAT_CONG         cổng nghe               (mặc định 8765)
    BDSG_CHAT_CSDL         tệp CSDL hội thoại      (xem kho_hoi_thoai.py)
    BDSG_CHAT_NGUOI_DEMO   mã người dùng demo      (mặc định "demo")
    BDSG_CHAT_MA_MO_HINH   mã mô hình công khai    (mặc định "bdsg-chat-noi-bo")
    BDSG_CHAT_TEN_MO_HINH  tên hiện ra
    BDSG_CHAT_TRONG_SO_NEN mã trọng số nền         (mặc định "google/gemma-4-31B-it")
    BDSG_CHAT_GIAO_DIEN    thư mục giao diện tĩnh  (mặc định ../chat)
    BDSG_CHAT_CHAP_NHAN_RUI_RO_NGHE_NGOAI = "toi-hieu-rui-ro"
                           mở khoá việc nghe ngoài loopback (xem luật 2)

Không biến nào ở đây chứa bí mật, và tệp này KHÔNG đọc khoá API nào — nó không gọi
ra ngoài nên không cần khoá nào cả.

TRẠNG THÁI SỐ LIỆU (26/09/2026): chưa đo độ trễ, chưa đo số yêu cầu đồng thời, chưa
chạy với mô hình thật. Mọi phép đo trong bài tự kiểm dùng cổng mô hình GIẢ.
"""

from __future__ import annotations

import inspect
import json
import os
import posixpath
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List, Optional

THU_MUC = os.path.dirname(os.path.abspath(__file__))
GOC_KHO = os.path.dirname(THU_MUC)

# Thư mục thật tên là "phuc-vu" — dấu gạch ngang không hợp lệ trong tên mô-đun
# Python, nên không import kiểu gói được. Đưa thư mục này vào đường tìm kiếm để
# `import kho_hoi_thoai` chạy cả khi tệp được nạp từ nơi khác.
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

import kho_hoi_thoai  # noqa: E402  (phải đặt sau khi vá sys.path, xem trên)

# ──────────────────────────────────────────────────────────────────────────────
# Hằng số
# ──────────────────────────────────────────────────────────────────────────────

BIEN_DIA_CHI = "BDSG_CHAT_DIA_CHI"
BIEN_CONG = "BDSG_CHAT_CONG"
BIEN_NGUOI_DEMO = "BDSG_CHAT_NGUOI_DEMO"
BIEN_MA_MO_HINH = "BDSG_CHAT_MA_MO_HINH"
BIEN_TEN_MO_HINH = "BDSG_CHAT_TEN_MO_HINH"
BIEN_TRONG_SO_NEN = "BDSG_CHAT_TRONG_SO_NEN"
BIEN_GIAO_DIEN = "BDSG_CHAT_GIAO_DIEN"
BIEN_NGHE_NGOAI = "BDSG_CHAT_CHAP_NHAN_RUI_RO_NGHE_NGOAI"

# Giá trị phải gõ đúng từng chữ. Cố ý KHÔNG nhận "1", "true", "yes": ba giá trị ấy
# hay bị bật nhầm bởi một kịch bản triển khai dùng lại từ chỗ khác. Một câu tiếng
# Việt gõ tay thì không ai bật nhầm.
GIA_TRI_CHAP_NHAN_RUI_RO = "toi-hieu-rui-ro"

DIA_CHI_CUC_BO = frozenset({"127.0.0.1", "localhost", "::1"})

# Vật đánh dấu "chưa khai gì, tự đi nạp". Cần một vật riêng vì `None` ở đây đã
# mang nghĩa khác: "cố ý KHÔNG có cổng mô hình".
TU_NAP = object()

DIA_CHI_MAC_DINH = "127.0.0.1"
CONG_MAC_DINH = 8765

MA_MO_HINH_MAC_DINH = "bdsg-chat-noi-bo"
TEN_MO_HINH_MAC_DINH = "BDSG Chat (chạy nội bộ)"
TRONG_SO_NEN_MAC_DINH = "google/gemma-4-31B-it"
LIEN_KET_NEN_MAC_DINH = "https://huggingface.co/google/gemma-4-31B-it"

DAI_TOI_DA_CAU_HOI = 12000          # khớp với câu báo lỗi "qua-dai" của giao diện
DAI_TOI_DA_THAN_YEU_CAU = 200000    # chặn thân yêu cầu phình to trước khi đọc

MUC_NO_LUC = (
    {"muc": "nhanh", "ten": "Nhanh", "moTa": "Trả lời ngắn, ít bước suy luận."},
    {"muc": "ky", "ten": "Kỹ", "moTa": "Nghĩ lâu hơn, câu trả lời dài hơn."},
)
MUC_NO_LUC_MAC_DINH = "nhanh"

# Mức "kỹ" chỉ nới TRẦN TOKEN RA lên gấp ngần này. Đây là một NÚM VẶN, không phải
# một phép đo: chưa ai đo xem câu trả lời dài hơn có tốt hơn không (26/09/2026).
# Ghi ra thành hằng số để người đo được sau này biết chỗ mà sửa.
HE_SO_TRAN_TOKEN_MUC_KY = 3

# Giao diện tĩnh: chỉ ba loại tệp, chỉ ở ngay trong thư mục giao diện, không đệ quy.
KIEU_TEP = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


class LoiKhongNoiDuocMayNoiBo(RuntimeError):
    """Không nói chuyện được với máy phục vụ mô hình NỘI BỘ.

    Lớp mặc định, dùng khi `cong_mo_hinh` chưa có hoặc không khai lớp của riêng nó.
    Máy chủ bắt lớp mà CHÍNH cổng mô hình khai ra (xem `_lop_loi_noi_bo`), nên hai
    bên không cần chia sẻ mô-đun nào.
    """


class LoiDiaChiKhongAnToan(RuntimeError):
    """Bị bảo nghe ngoài loopback mà người vận hành chưa khai chấp nhận rủi ro."""


CAU_BAO_LOI_NOI_BO = (
    "Máy phục vụ mô hình NỘI BỘ không trả lời, nên câu hỏi dừng ở đây. "
    "Câu hỏi của bạn KHÔNG được gửi đi đâu khác — máy chủ này không có đường "
    "dự phòng ra ngoài. Cách kiểm: (1) tiến trình vLLM còn chạy không; "
    "(2) địa chỉ máy phục vụ trong cấu hình có đúng không; "
    "(3) xem nhật ký của máy phục vụ mô hình."
)

CAU_BAO_CHUA_CO_CONG = (
    "Chưa cài cổng mô hình NỘI BỘ (phuc-vu/cong_mo_hinh.py), nên chưa hỏi được. "
    "Máy chủ này cố ý không gọi bất kỳ nhà cung cấp nào bên ngoài để thay thế. "
    "Giao diện, lịch sử hội thoại và các đường còn lại vẫn chạy bình thường."
)

CANH_BAO_CHUA_XAC_THUC = (
    "Bản demo MỘT NGƯỜI trên máy nội bộ. Chưa có đăng nhập, nên chưa dùng được "
    "cho nhiều nhân viên: mọi người gọi tới máy chủ này đều là cùng một danh tính."
)


# ──────────────────────────────────────────────────────────────────────────────
# Cấu hình mô hình đem ra giao diện
# ──────────────────────────────────────────────────────────────────────────────


def doc_cau_hinh_mo_hinh(cau_hinh_ngoai: Any = None) -> Dict[str, Any]:
    """Dựng khối cấu hình mà `GET /api/mo-hinh` trả về.

    `cau_hinh_ngoai` là một `cau_hinh.CauHinhPhucVu` (hoặc một dict cùng trường).
    Đọc bằng `getattr`/`get` chứ không ép kiểu: hai nhóm viết song song, và một
    trường thiếu không nên làm cả đường `/api/mo-hinh` chết.

    HAI TÊN KHÁC NHAU, ĐỪNG TRỘN:
      · `ma`           — mã CÔNG KHAI của BDSG, một cái tên hiển thị.
      · `trong_so_nen` — mã trọng số THẬT gửi tới máy vLLM, tức
                         `CauHinhPhucVu.ma_mo_hinh`. Đây là thứ của Google.
    Trộn hai cái làm một thì hoặc là giao diện khoe mã Google như tên sản phẩm
    BDSG, hoặc là phép so "máy chủ có trả lời bằng đúng mô hình đã gọi không"
    luôn báo lệch. Cả hai đều sai theo hai hướng ngược nhau.
    """

    def lay(ten: str, mac_dinh: Any) -> Any:
        if cau_hinh_ngoai is None:
            return mac_dinh
        if isinstance(cau_hinh_ngoai, dict):
            gia_tri = cau_hinh_ngoai.get(ten)
        else:
            gia_tri = getattr(cau_hinh_ngoai, ten, None)
        return mac_dinh if gia_tri in (None, "") else gia_tri

    ma = os.environ.get(BIEN_MA_MO_HINH, "").strip() or MA_MO_HINH_MAC_DINH
    ten = os.environ.get(BIEN_TEN_MO_HINH, "").strip() or TEN_MO_HINH_MAC_DINH
    nen = lay(
        "ma_mo_hinh",
        os.environ.get(BIEN_TRONG_SO_NEN, "").strip() or TRONG_SO_NEN_MAC_DINH,
    )
    # Liên kết mặc định trỏ tới trang trọng số của Google, nên nó CHỈ được dùng
    # làm mặc định khi trọng số đang phục vụ đúng là của Google. Trỏ người đọc
    # tới trang Gemma 4 của Google trong lúc máy chủ đang chạy một trọng số khác
    # là một lời khai sai về xuất xứ — cùng họ với việc đặt cờ
    # `bdsg_la_trong_so_bdsg` sai, chỉ ngược chiều.
    if la_trong_so_google(nen):
        mac_dinh_lien_ket = LIEN_KET_NEN_MAC_DINH
    else:
        mac_dinh_lien_ket = ""
    lien_ket = lay("lien_ket_nen", mac_dinh_lien_ket)
    return {
        "ma": str(ma),
        "ten": str(ten),
        "trong_so_nen": str(nen),
        "lien_ket_nen": str(lien_ket),
    }


def la_trong_so_google(ma_trong_so: Any) -> bool:
    """Mã trọng số này có phải của Google không? So bằng tiền tố kho `google/`.

    Một hàm riêng vì cùng một câu hỏi được hỏi ở ba chỗ (cờ `bdsg_la_trong_so_bdsg`,
    khối khai xuất xứ `nen`, và dòng tóm tắt lúc khởi động). Ba chỗ tự trả lời
    riêng thì sẽ có ngày chúng trả lời khác nhau.
    """
    return (
        isinstance(ma_trong_so, str)
        and ma_trong_so.strip().lower().startswith("google/")
    )


def xuat_xu_trong_so(ma_trong_so: Any) -> Dict[str, str]:
    """Nhà cung cấp và giấy phép của trọng số — SUY RA TỪ MÃ, không viết cứng.

    VÌ SAO KHÔNG VIẾT CỨNG "Google / Apache-2.0": mã trọng số là một BIẾN (đặt
    qua `BDSG_CHAT_TRONG_SO_NEN` hoặc qua `cau_hinh.ma_mo_hinh`), còn khối khai
    xuất xứ thì trước đây là hằng số. Hai thứ ấy lệch nhau ngay khi ai đó trỏ máy
    chủ sang một trọng số khác, và cái lệch ấy đi thẳng ra API dưới dạng một lời
    khai sai: "trọng số bdsg/... do Google cung cấp, giấy phép Apache-2.0".

    Ghi công Google phải đúng sự thật theo CẢ HAI chiều — không nhận vơ trọng số
    của Google là của BDSG, và cũng không gán cho Google một trọng số không phải
    của họ. Chưa biết thì nói "chưa khai", đừng đoán một giấy phép.
    """
    ma = (ma_trong_so or "").strip() if isinstance(ma_trong_so, str) else ""
    if la_trong_so_google(ma):
        # Gemma 4 phát hành theo Apache-2.0 (khác hẳn giấy phép riêng của Gemma
        # 1-3). Xem tai-lieu/GEMMA4-31B.md.
        return {"nhaCungCap": "Google", "giayPhep": "Apache-2.0"}
    to_chuc = ma.split("/")[0].strip() if "/" in ma else ""
    return {"nhaCungCap": to_chuc or "chưa khai", "giayPhep": "chưa khai"}


def la_trong_so_bdsg(ma_trong_so: str) -> bool:
    """Trọng số đang phục vụ có phải do BDSG huấn luyện không?

    Nguồn sự thật là `cau_hinh.bdsg_la_trong_so_bdsg()` của nhóm cổng mô hình —
    tệp này không tự quyết định. Thiếu mô-đun ấy thì trả False, vì "không biết"
    và "là của BDSG" không được phép rơi vào cùng một câu trả lời.

    CÒN MỘT CHỐT CỨNG: mã trọng số bắt đầu bằng "google/" thì LUÔN trả False,
    bất kể hàm kia nói gì. Lý do không phải là nghi ngờ nhóm kia, mà là thứ tự
    nhân quả: trọng số Google NGUYÊN BẢN không thể là trọng số BDSG đã tinh chỉnh
    — một bản đã tinh chỉnh thì mang mã khác. Nên một giá trị `True` ở đây chỉ có
    thể là một lỗi, và một lỗi ở đúng dòng này là một lời khai sai về việc ai đã
    làm ra mô hình. Chốt lại thì lỗi ấy không ra tới người đọc được.
    """
    if la_trong_so_google(ma_trong_so):
        return False
    try:
        import cau_hinh
    except ImportError:
        return False
    ham = getattr(cau_hinh, "bdsg_la_trong_so_bdsg", None)
    if not callable(ham):
        return False
    try:
        return bool(ham(ma_trong_so))
    except Exception:  # noqa: BLE001
        return False


def dung_phan_hoi_mo_hinh(cau_hinh: Dict[str, Any]) -> Dict[str, Any]:
    """Thân của `GET /api/mo-hinh`, đúng hình dạng giao diện đọc.

    `danhSach` BẮT BUỘC có, và ở đây nó có HAI mục chứ không phải một. Lý do:
    giao diện dùng `danhSach` để đổi mã trong `moHinhThat` thành tên người đọc
    được, mà `moHinhThat` là mã máy phục vụ tự khai — với vLLM thì đó là mã trọng
    số của Google, không phải mã công khai của BDSG. Thiếu mục thứ hai thì nhãn
    "câu trả lời đến từ …" hiện ra một mã trần, đúng chỗ có nhiệm vụ chống khai
    sai tên mô hình.
    """
    ma = cau_hinh["ma"]
    ten = cau_hinh["ten"]
    nen = cau_hinh["trong_so_nen"]
    xuat_xu = xuat_xu_trong_so(nen)
    # Câu mô tả cũng nêu tên nhà cung cấp THẬT, không viết cứng "của Google":
    # đây là câu người dùng đọc trong bảng chọn mô hình, tức là chỗ lời khai sai
    # về xuất xứ đi xa nhất.
    mo_ta = "Chạy trên máy nội bộ của BDSG. Nền là trọng số %s (%s)." % (
        nen, xuat_xu["nhaCungCap"],
    )
    danh_sach = [
        {"ma": ma, "ten": ten, "moTa": mo_ta, "suyLuan": False},
    ]
    if nen != ma:
        danh_sach.append(
            {
                "ma": nen,
                "ten": nen,
                "moTa": "Mã trọng số do máy phục vụ tự khai.",
                "suyLuan": False,
            }
        )
    return {
        "moHinh": {"ma": ma, "ten": ten, "moTa": mo_ta},
        "mucNoLuc": [dict(m) for m in MUC_NO_LUC],
        "mucNoLucMacDinh": MUC_NO_LUC_MAC_DINH,
        "danhSach": danh_sach,
        # Khối này là phần khai nguồn gốc. Nó nằm trong phản hồi API chứ không chỉ
        # trong tài liệu, vì tài liệu thì người dùng giao diện không đọc.
        "nen": {
            "nhaCungCap": xuat_xu["nhaCungCap"],
            "maTrongSo": nen,
            "giayPhep": xuat_xu["giayPhep"],
            "lienKet": cau_hinh["lien_ket_nen"],
            "phucVuBoi": "vLLM",
            "chayTai": "máy nội bộ",
        },
        # BDSG PHỤC VỤ trọng số của Google. BDSG chưa tinh chỉnh trọng số nào, nên
        # cờ này là false. Đổi nó chỉ khi thứ đang phục vụ thật sự là trọng số do
        # BDSG huấn luyện — không phải khi BDSG chỉ chạy máy phục vụ.
        "bdsg_la_trong_so_bdsg": la_trong_so_bdsg(nen),
        "xacThuc": False,
        "canhBao": CANH_BAO_CHUA_XAC_THUC,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Bối cảnh: gom mọi phụ thuộc vào một chỗ để bài tự kiểm thay được
# ──────────────────────────────────────────────────────────────────────────────


class BoiCanh:
    """Những thứ bộ xử lý HTTP cần. Tiêm vào chứ không tự đi tìm.

    Tự đi tìm (import toàn cục, đọc biến môi trường ngay trong bộ xử lý) làm bài
    tự kiểm không thay được cổng mô hình bằng bản giả, và khi không thay được thì
    bài kiểm cần GPU — tức là không ai chạy nó.
    """

    def __init__(
        self,
        kho: Any,
        cong_mo_hinh: Any = None,
        cau_hinh_ngoai: Any = None,
        nguoi_demo: Optional[str] = None,
        thu_muc_giao_dien: Optional[str] = None,
    ) -> None:
        self.kho = kho
        self.cong_mo_hinh = cong_mo_hinh
        self.cau_hinh = doc_cau_hinh_mo_hinh(cau_hinh_ngoai)
        self.nguoi_demo = (
            nguoi_demo
            or os.environ.get(BIEN_NGUOI_DEMO, "").strip()
            or "demo"
        )
        if thu_muc_giao_dien is None:
            thu_muc_giao_dien = (
                os.environ.get(BIEN_GIAO_DIEN, "").strip()
                or os.path.join(GOC_KHO, "chat")
            )
        self.thu_muc_giao_dien = os.path.realpath(thu_muc_giao_dien)

    def lop_loi_noi_bo(self) -> type:
        """Lớp ngoại lệ "không nói được với máy nội bộ" mà cổng mô hình khai ra.

        Bắt theo lớp CỦA CỔNG chứ không theo lớp của tệp này: hai mô-đun không
        cần chia sẻ tổ tiên nào, và bài tự kiểm cắm được một cổng giả có lớp lỗi
        của riêng nó.
        """
        # 1. Lớp do CHÍNH đối tượng cổng khai (bài tự kiểm cắm cổng giả bằng đường
        #    này, và một cổng tự viết cũng dùng được).
        lop = getattr(self.cong_mo_hinh, "LoiKhongNoiDuocMayNoiBo", None)
        if isinstance(lop, type) and issubclass(lop, BaseException):
            return lop
        # 2. Lớp của mô-đun cổng mô hình thật. Cần bước này vì `CongMoHinh` là một
        #    LỚP, còn ngoại lệ là thuộc tính của MÔ-ĐUN — không với tới nhau qua
        #    đối tượng. Thiếu bước này thì lỗi "không nối được máy nội bộ" rơi vào
        #    nhánh lỗi chung và người dùng nhận một câu báo kém chính xác hơn.
        try:
            import cong_mo_hinh as _mo_dun
        except ImportError:
            return LoiKhongNoiDuocMayNoiBo
        lop = getattr(_mo_dun, "LoiKhongNoiDuocMayNoiBo", None)
        if isinstance(lop, type) and issubclass(lop, BaseException):
            return lop
        return LoiKhongNoiDuocMayNoiBo

    def lech_mo_hinh(self, ma_yeu_cau: Optional[str], ma_that: Optional[str]) -> bool:
        """Mã đã gửi đi và mã máy phục vụ khai có lệch nhau không?

        So bằng `!=`, KHÔNG gọi `cong_mo_hinh.doi_chieu_mo_hinh`: hàm ấy trả về
        TÊN mô hình thật (một chuỗi), không phải một giá trị đúng/sai. Ép nó thành
        bool thì mọi chuỗi không rỗng đều đúng, tức mọi câu trả lời đều bị dán
        nhãn "lệch" — một cảnh báo kêu ở mọi lượt là một cảnh báo không ai đọc.
        Việc đối chiếu đã được cổng mô hình làm xong; kết quả nằm trong
        `thu_thap["mo_hinh_that"]`.
        """
        if not ma_that:
            return False
        return ma_yeu_cau != ma_that

    # ── gọi cổng mô hình ─────────────────────────────────────────────────────

    def _tran_token_ra(self, muc_no_luc: str) -> Optional[int]:
        """Mức nỗ lực → trần token ra. `None` nghĩa là dùng mặc định của cổng."""
        if muc_no_luc != "ky":
            return None
        goc = getattr(getattr(self.cong_mo_hinh, "cau_hinh", None), "tran_token_ra", None)
        if isinstance(goc, int) and goc > 0:
            return goc * HE_SO_TRAN_TOKEN_MUC_KY
        return None

    def goi_cong(
        self,
        lich_su: List[Dict[str, str]],
        muc_no_luc: str,
        thu_thap: Dict[str, Any],
    ) -> Any:
        """Gọi cổng mô hình. ĐÂY LÀ LỐI RA DUY NHẤT của máy chủ này.

        Một chỗ, một hàm. Mọi câu hỏi của người dùng đi qua đúng dòng này, nên
        câu hỏi "dữ liệu có đi ra ngoài không" chỉ cần đọc một hàm để trả lời —
        thay vì đọc cả tệp và hy vọng không bỏ sót một nhánh nào.

        Đổi hình dạng tin nhắn ở đây: kho lưu `vai_tro` là "nguoi"/"may" (tiếng
        Việt, theo giao diện), còn cổng mô hình nói API tương thích OpenAI nên
        cần "user"/"assistant". Đổi tại BIÊN chứ không đổi tên cột trong CSDL:
        cột trong CSDL là thứ giao diện đọc, còn hình dạng OpenAI là thứ một máy
        phục vụ bên ngoài đòi — hai thứ ấy sẽ tách đường nhau ngày nào đó.
        """
        tin_nhan = [
            {
                "role": "user" if t.get("vai_tro") == "nguoi" else "assistant",
                "content": t.get("noi_dung", ""),
            }
            for t in lich_su
        ]
        tham_so: Dict[str, Any] = {"thu_thap": thu_thap}
        tran = self._tran_token_ra(muc_no_luc)
        if tran is not None:
            tham_so["tran_token_ra"] = tran
        return self.cong_mo_hinh.hoi_dong_chay(tin_nhan, **self._loc_tham_so(tham_so))

    def _loc_tham_so(self, tham_so: Dict[str, Any]) -> Dict[str, Any]:
        """Bỏ những tham số mà `hoi_dong_chay` của cổng này không nhận.

        Hai nhóm viết song song và chữ ký hàm bên kia còn đổi. Gửi một tham số
        lạ thì Python ném `TypeError`, và `TypeError` rơi vào nhánh lỗi chung —
        người dùng nhận câu "cổng mô hình gặp lỗi" thay vì câu trả lời, mà nguyên
        nhân thật chỉ là một tên tham số. Lọc trước thì cổng nào cũng gọi được,
        chỉ mất phần tinh chỉnh mà cổng ấy không hỗ trợ.
        """
        ham = getattr(self.cong_mo_hinh, "hoi_dong_chay", None)
        try:
            chu_ky = inspect.signature(ham)
        except (TypeError, ValueError):
            return tham_so
        # Hàm nhận **kwargs thì nhận tuốt, không cần lọc.
        for tham in chu_ky.parameters.values():
            if tham.kind is inspect.Parameter.VAR_KEYWORD:
                return tham_so
        nhan_duoc = set(chu_ky.parameters)
        return {ten: gia_tri for ten, gia_tri in tham_so.items() if ten in nhan_duoc}


# ──────────────────────────────────────────────────────────────────────────────
# Bộ xử lý HTTP
# ──────────────────────────────────────────────────────────────────────────────


def tao_lop_xu_ly(boi_canh: BoiCanh) -> type:
    """Dựng lớp xử lý mang theo `boi_canh`.

    `BaseHTTPRequestHandler` được khởi tạo lại cho TỪNG yêu cầu, nên không truyền
    phụ thuộc qua `__init__` được. Đóng gói bằng bao đóng là cách sạch nhất; cách
    còn lại là gắn lên lớp máy chủ rồi với qua `self.server`, vốn buộc bài tự kiểm
    phải dựng cả máy chủ mới thử được một đường.
    """

    class XuLy(BaseHTTPRequestHandler):
        server_version = "BDSGChatNoiBo"
        # Giấu phiên bản Python: nó là thông tin miễn phí cho người dò, và không
        # giúp gì người dùng.
        sys_version = ""
        protocol_version = "HTTP/1.1"

        # ── tiện ích ───────────────────────────────────────────────────────────

        def log_message(self, dinh_dang, *tham_so):  # noqa: A002, N802
            """Nhật ký một dòng, KHÔNG ghi thân yêu cầu.

            Câu hỏi của người dùng đi trong thân của POST /api/hoi. Nếu nó lọt vào
            nhật ký thì dữ liệu riêng của doanh nghiệp nằm trong một tệp text mà
            không ai coi là dữ liệu riêng. Bản mặc định chỉ ghi dòng yêu cầu, và
            câu hỏi không nằm ở đó — giữ nguyên hành vi ấy, ghi ra để người sau
            đừng thêm thân vào cho "dễ gỡ lỗi".
            """
            sys.stderr.write(
                "[%s] %s - %s\n"
                % (self.log_date_time_string(), self.address_string(), dinh_dang % tham_so)
            )

        def _tra_json(self, ma_http: int, doi_tuong: Any) -> None:
            than = json.dumps(doi_tuong, ensure_ascii=False).encode("utf-8")
            if ma_http >= 400:
                # Đóng kết nối ở mọi phản hồi lỗi. Lý do là một lỗi lệch khung
                # HTTP/1.1 rất khó truy: khi máy chủ từ chối một yêu cầu TRƯỚC khi
                # đọc hết thân của nó, phần thân chưa đọc còn nằm trong ống và sẽ
                # bị hiểu nhầm là dòng đầu của yêu cầu KẾ TIẾP trên cùng kết nối.
                self.close_connection = True
            self.send_response(ma_http)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(than)))
            self.send_header("Cache-Control", "no-store")
            # Không đặt Access-Control-Allow-Origin. Giao diện và API cùng một gốc
            # (máy chủ này phục vụ cả hai). Mở CORS ở một máy chủ không xác thực là
            # cho mọi trang web trong trình duyệt đọc hội thoại của người dùng.
            self.end_headers()
            self._viet(than)

        def _viet(self, du_lieu: bytes) -> bool:
            """Ghi ra socket. Trả False khi khách đã ngắt.

            Khách bấm "dừng" thì giao diện `abort()` — socket đứt giữa chừng và
            mọi lần ghi sau đó ném ngoại lệ. Bắt ở đây để vòng sinh chữ dừng lại
            thay vì đổ vết lỗi, và quan trọng hơn: để ngừng sinh tiếp phần chữ
            không còn ai đọc.
            """
            try:
                self.wfile.write(du_lieu)
                self.wfile.flush()
                return True
            except (BrokenPipeError, ConnectionResetError, ValueError, OSError):
                return False

        def _mo_sse(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            # Nói với mọi proxy đứng giữa: đừng gom. Một proxy gom đệm biến dòng
            # chảy chữ thành một cục chữ đến sau ba mươi giây — hỏng mà không báo.
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True

        def _su_kien(self, ten: str, du_lieu: Any) -> bool:
            """Đẩy MỘT khung SSE ra ngay lập tức.

            Ghi rồi flush từng khung chứ không gom: gom lại thì khách thấy chữ hiện
            thành từng cục thay vì chảy đều, tức mất đúng thứ SSE sinh ra để làm.
            `json.dumps` thoát mọi ký tự xuống dòng bên trong chuỗi, nên khung luôn
            đúng một dòng `data:` — không cần tự cắt dòng.
            """
            khung = "event: %s\ndata: %s\n\n" % (
                ten,
                json.dumps(du_lieu, ensure_ascii=False),
            )
            return self._viet(khung.encode("utf-8"))

        def _nguoi(self) -> str:
            """Danh tính của yêu cầu này.

            Ở bản demo là một hằng số: CHƯA CÓ ĐĂNG NHẬP. Mọi đường phân quyền gọi
            qua đây, nên ngày nối đăng nhập thật chỉ phải sửa một hàm này.
            """
            return boi_canh.nguoi_demo

        def _doc_than(self) -> Optional[Any]:
            try:
                dai = int(self.headers.get("Content-Length") or 0)
            except (TypeError, ValueError):
                return None
            if dai <= 0 or dai > DAI_TOI_DA_THAN_YEU_CAU:
                return None
            try:
                tho = self.rfile.read(dai)
                return json.loads(tho.decode("utf-8"))
            except (ValueError, UnicodeDecodeError, OSError):
                return None

        # ── định tuyến ─────────────────────────────────────────────────────────

        def do_GET(self):  # noqa: N802
            duong = urllib.parse.urlsplit(self.path).path
            if duong == "/api/mo-hinh":
                return self._get_mo_hinh()
            if duong == "/api/toi":
                return self._get_toi()
            if duong == "/api/hoi-thoai":
                return self._get_danh_sach()
            if duong.startswith("/api/hoi-thoai/"):
                return self._get_mot(duong[len("/api/hoi-thoai/"):])
            if duong.startswith("/api/"):
                return self._tra_json(404, {"loi": "khong-co-duong"})
            return self._tep_tinh(duong)

        def do_POST(self):  # noqa: N802
            duong = urllib.parse.urlsplit(self.path).path
            if duong == "/api/hoi":
                return self._post_hoi()
            return self._tra_json(404, {"loi": "khong-co-duong"})

        def do_DELETE(self):  # noqa: N802
            duong = urllib.parse.urlsplit(self.path).path
            if duong.startswith("/api/hoi-thoai/"):
                return self._xoa(duong[len("/api/hoi-thoai/"):])
            return self._tra_json(404, {"loi": "khong-co-duong"})

        # ── các đường ──────────────────────────────────────────────────────────

        def _get_mo_hinh(self) -> None:
            self._tra_json(200, dung_phan_hoi_mo_hinh(boi_canh.cau_hinh))

        def _get_toi(self) -> None:
            """Danh tính. Bản này KHÔNG có đăng nhập và tự khai điều đó.

            `dangNhap: true` để giao diện hiện tên ở chân thanh bên; `xacThuc:
            false` và `canhBao` là phần nói thật: không ai phải chứng minh mình là
            ai để tới được đây. Hai trường ấy nằm trong API chứ không chỉ trong tài
            liệu, vì một máy chủ đang chạy thì người ta đọc API chứ không đọc README.

            Không có email, không có ảnh: bản demo không có dữ liệu cá nhân nào để
            trả, và trả một địa chỉ bịa ra là tự tạo một dữ liệu cá nhân giả.
            """
            self._tra_json(
                200,
                {
                    "dangNhap": True,
                    "ten": "Người dùng demo",
                    "email": None,
                    "anh": None,
                    "hanMuc": None,
                    "xacThuc": False,
                    "canhBao": CANH_BAO_CHUA_XAC_THUC,
                },
            )

        def _get_danh_sach(self) -> None:
            self._tra_json(200, {"danhSach": boi_canh.kho.liet_ke(self._nguoi())})

        def _get_mot(self, ma: str) -> None:
            ma = urllib.parse.unquote(ma)
            hoi_thoai = boi_canh.kho.doc(ma, self._nguoi())
            if hoi_thoai is None:
                # 404 cho cả "không có" lẫn "của người khác" — xem chat/README.md.
                return self._tra_json(404, {"loi": "khong-co-hoi-thoai"})
            self._tra_json(200, hoi_thoai)

        def _xoa(self, ma: str) -> None:
            ma = urllib.parse.unquote(ma)
            # `kho.xoa` tự kiểm dạng mã và tự kiểm chủ sở hữu TRONG câu lệnh SQL.
            # Ở đây không đọc lên rồi so — cố ý, xem đầu kho_hoi_thoai.py.
            if boi_canh.kho.xoa(ma, self._nguoi()):
                return self._tra_json(200, {"daXoa": True})
            self._tra_json(404, {"loi": "khong-co-hoi-thoai"})

        # ── đường chính: hỏi ───────────────────────────────────────────────────

        def _post_hoi(self) -> None:
            than = self._doc_than()
            if not isinstance(than, dict):
                return self._tra_json(400, {"loi": "than-hong"})

            noi_dung = than.get("noiDung")
            ma_loi = kiem_cau_hoi(noi_dung)
            if ma_loi is not None:
                # Bốn mã này khớp đúng `moTaLoi()` của giao diện: "rong",
                # "qua-dai", "ky-tu-dieu-khien". Đổi tên mã là làm giao diện hiện
                # câu chung chung thay vì câu đúng.
                return self._tra_json(400, {"loi": ma_loi})

            muc_no_luc = than.get("mucNoLuc")
            if muc_no_luc not in [m["muc"] for m in MUC_NO_LUC]:
                muc_no_luc = MUC_NO_LUC_MAC_DINH

            nguoi = self._nguoi()
            ma_hoi_thoai = than.get("hoiThoaiId")
            if ma_hoi_thoai:
                if boi_canh.kho.doc(ma_hoi_thoai, nguoi) is None:
                    # Cùng luật với DELETE: không tiết lộ hội thoại có tồn tại hay
                    # không. Không âm thầm tạo hội thoại mới thay thế, vì như thế
                    # câu hỏi sẽ rơi vào một chỗ khác chỗ người dùng tưởng.
                    return self._tra_json(404, {"loi": "khong-co-hoi-thoai"})
            else:
                ma_hoi_thoai = boi_canh.kho.tao_hoi_thoai(nguoi, noi_dung)

            boi_canh.kho.them_tin_nhan(ma_hoi_thoai, nguoi, "nguoi", noi_dung)

            lich_su = []
            da_doc = boi_canh.kho.doc(ma_hoi_thoai, nguoi)
            if da_doc:
                lich_su = [
                    {"vai_tro": t["vaiTro"], "noi_dung": t["noiDung"]}
                    for t in da_doc["tinNhan"]
                ]

            self._mo_sse()
            if not self._su_kien("batdau", {"hoiThoaiId": ma_hoi_thoai}):
                return

            if boi_canh.cong_mo_hinh is None:
                # Chưa có cổng mô hình. Báo thẳng. KHÔNG có nhánh nào khác ở đây —
                # đây đúng là chỗ một "đường dự phòng ra ngoài" hay được cài vào.
                self._su_kien("loi", {"thongBao": CAU_BAO_CHUA_CO_CONG})
                return

            self._chay_dong(ma_hoi_thoai, nguoi, lich_su, muc_no_luc)

        def _chay_dong(
            self,
            ma_hoi_thoai: str,
            nguoi: str,
            lich_su: List[Dict[str, str]],
            muc_no_luc: str,
        ) -> None:
            """Chảy chữ từ cổng mô hình ra khách, rồi lưu lại."""
            lop_loi = boi_canh.lop_loi_noi_bo()
            # So LỆCH với mã TRỌNG SỐ NỀN, không phải với mã công khai của BDSG.
            # Mã công khai ("bdsg-chat-noi-bo") là một cái tên hiển thị; thứ thật
            # sự gửi tới máy phục vụ là mã trọng số. Nếu so với tên hiển thị thì
            # câu trả lời nào cũng "lệch", và một cảnh báo kêu ở mọi lượt là một
            # cảnh báo không ai còn đọc — đúng lúc nó cần được đọc thì đã muộn.
            ma_yeu_cau = boi_canh.cau_hinh["trong_so_nen"]

            da_nhan = []
            # `thu_thap` là cái hộp cổng mô hình điền vào trong lúc chạy. Phải
            # dùng hộp chứ không dùng giá trị trả về: `hoi_dong_chay` là một HÀM
            # SINH, và vòng `for` không bao giờ nhìn thấy giá trị trả về của nó.
            # Cổng điền `mo_hinh_that` ở khối `finally` của chính nó, nên hộp có
            # dữ liệu kể cả khi dòng chảy đứt giữa chừng.
            thu_thap: Dict[str, Any] = {}
            bo_sinh = None
            khach_con_do = True

            try:
                bo_sinh = boi_canh.goi_cong(lich_su, muc_no_luc, thu_thap)
                for mau in bo_sinh:
                    if mau is None or mau == "":
                        continue
                    chu = mau if isinstance(mau, str) else str(mau)
                    da_nhan.append(chu)
                    if not self._su_kien("chu", {"chu": chu}):
                        khach_con_do = False
                        break
            except lop_loi:
                # Máy nội bộ hỏng. Báo lỗi rõ ràng rồi ĐÓNG DÒNG.
                # Không thử nhà cung cấp nào khác — xem luật 1 ở đầu tệp.
                self._luu_phan_da_nhan(ma_hoi_thoai, nguoi, da_nhan, thu_thap)
                self._su_kien("loi", {"thongBao": CAU_BAO_LOI_NOI_BO})
                return
            except Exception as loi:  # noqa: BLE001
                # Lỗi khác (cổng mô hình có bọ, dữ liệu trả về sai hình dạng...).
                # Vẫn KHÔNG có đường ra ngoài. Ghi loại lỗi vào nhật ký máy chủ,
                # không ném nội dung lỗi cho khách: nó hay chứa đường dẫn nội bộ.
                # Vết lỗi đầy đủ chỉ đi vào nhật ký MÁY CHỦ, không đi ra khách:
                # nó hay chứa đường dẫn nội bộ và tên biến. Người vận hành cần nó
                # để sửa; người dùng cuối thì không, và người lạ càng không.
                self.log_message(
                    "loi cong mo hinh: %s: %s", type(loi).__name__, loi
                )
                self._luu_phan_da_nhan(ma_hoi_thoai, nguoi, da_nhan, thu_thap)
                self._su_kien(
                    "loi",
                    {
                        "thongBao": "Cổng mô hình NỘI BỘ gặp lỗi (%s). Xem nhật ký "
                        "máy chủ để biết chi tiết." % (type(loi).__name__,)
                    },
                )
                return
            finally:
                # Khách ngắt giữa chừng thì đóng bộ sinh để cổng mô hình biết đường
                # ngừng sinh. Không đóng thì máy phục vụ vẫn sinh tiếp phần chữ
                # không ai đọc — tốn GPU cho hư không.
                if bo_sinh is not None and not khach_con_do:
                    dong = getattr(bo_sinh, "close", None)
                    if callable(dong):
                        dong()

            van = "".join(da_nhan)
            ma_that = doc_mo_hinh_that(thu_thap)
            trich_dan = chuan_hoa_trich_dan(thu_thap.get("trich_dan"))
            boi_canh.kho.them_tin_nhan(
                ma_hoi_thoai, nguoi, "may", van, ma_that, trich_dan
            )

            if not khach_con_do:
                return

            # `moHinhThat` ĐỌC TỪ PHẢN HỒI của máy phục vụ, không phải tên đã gửi đi.
            # Khi cổng mô hình không khai tên nào thì trả None chứ KHÔNG vọng lại mã
            # đã yêu cầu: vọng lại chính là lời nói dối mà trường này sinh ra để
            # chống. Giao diện bỏ qua nhãn khi trường này rỗng.
            xong = {
                "trichDan": trich_dan,
                "moHinhThat": ma_that,
            }
            if ma_that and boi_canh.lech_mo_hinh(ma_yeu_cau, ma_that):
                xong["lech"] = True
                xong["moHinhYeuCau"] = ma_yeu_cau
            # CỐ Ý không gửi `thu_thap["so_mau"]` vào `tokenRa`: `so_mau` là số
            # MẨU CHỮ nhận được, không phải số token. Hai con số ấy gần nhau
            # nhưng không bằng nhau, và giao diện hiện nó kèm chữ "token" — dán
            # nhãn sai lên một con số là cách rẻ nhất để làm hỏng mọi phép tính
            # chi phí về sau. Chỉ gửi khi cổng khai đúng số token.
            if thu_thap.get("token_ra"):
                xong["tokenRa"] = thu_thap["token_ra"]
            self._su_kien("xong", xong)

        def _luu_phan_da_nhan(
            self,
            ma_hoi_thoai: str,
            nguoi: str,
            da_nhan: List[str],
            thu_thap: Dict[str, Any],
        ) -> None:
            """Giữ phần chữ đã nhận được trước khi lỗi.

            Vứt đi là phạt người dùng vì một sự cố của máy chủ: họ đã đọc mấy dòng
            ấy trên màn hình, mở lại hội thoại mà không thấy gì thì tưởng mình nhớ
            nhầm.
            """
            van = "".join(da_nhan)
            if not van:
                return
            boi_canh.kho.them_tin_nhan(
                ma_hoi_thoai,
                nguoi,
                "may",
                van,
                doc_mo_hinh_that(thu_thap),
                chuan_hoa_trich_dan(thu_thap.get("trich_dan")),
            )

        # ── giao diện tĩnh ─────────────────────────────────────────────────────

        def _tep_tinh(self, duong: str) -> None:
            """Phục vụ ba tệp giao diện, CÙNG MỘT GỐC với API.

            Vì sao máy chủ này phục vụ luôn giao diện: mở giao diện bằng một máy chủ
            tĩnh riêng ở cổng khác thì trình duyệt coi đó là gốc khác, và mọi lời gọi
            `/api/*` với `credentials: same-origin` sẽ hỏng. Cùng một gốc là cách
            duy nhất để bản demo chạy mà không phải mở CORS.

            CHẶN ĐI XUYÊN THƯ MỤC: chỉ nhận tên tệp TRẦN, không nhận đường dẫn có
            thư mục. So `basename(ten) == ten` sau khi giải mã %-encoding, rồi còn
            kiểm đường dẫn thật có nằm trong thư mục giao diện không. Hai lớp, vì
            lớp thứ nhất là phép so chuỗi và phép so chuỗi hay bị lách.
            """
            ten = urllib.parse.unquote(duong).lstrip("/")
            if ten == "":
                ten = "index.html"
            if ten != posixpath.basename(ten):
                return self._tra_json(404, {"loi": "khong-co-duong"})
            phan_mo_rong = os.path.splitext(ten)[1].lower()
            if phan_mo_rong not in KIEU_TEP:
                return self._tra_json(404, {"loi": "khong-co-duong"})
            duong_that = os.path.realpath(os.path.join(boi_canh.thu_muc_giao_dien, ten))
            goc = boi_canh.thu_muc_giao_dien
            if duong_that != goc and not duong_that.startswith(goc + os.sep):
                return self._tra_json(404, {"loi": "khong-co-duong"})
            try:
                with open(duong_that, "rb") as tep:
                    than = tep.read()
            except OSError:
                return self._tra_json(404, {"loi": "khong-co-tep"})
            self.send_response(200)
            self.send_header("Content-Type", KIEU_TEP[phan_mo_rong])
            self.send_header("Content-Length", str(len(than)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self._viet(than)

    return XuLy


# ──────────────────────────────────────────────────────────────────────────────
# Kiểm đầu vào
# ──────────────────────────────────────────────────────────────────────────────


def kiem_cau_hoi(noi_dung: Any) -> Optional[str]:
    """Trả mã lỗi, hoặc None nếu câu hỏi dùng được.

    Ba mã trả về khớp đúng bảng `moTaLoi()` của giao diện. Giao diện đổi mã thành
    câu tiếng Việt; máy chủ trả mã chứ không trả câu, để hai bên đổi lời văn độc
    lập với nhau.
    """
    if not isinstance(noi_dung, str) or noi_dung.strip() == "":
        return "rong"
    if len(noi_dung) > DAI_TOI_DA_CAU_HOI:
        return "qua-dai"
    # Ký tự điều khiển: chừa \n \r \t vì câu hỏi dán từ tài liệu luôn có chúng.
    # Chặn phần còn lại vì chúng không phải chữ người gõ, và chúng đi thẳng vào
    # lời nhắc của mô hình.
    for ky_tu in noi_dung:
        if ord(ky_tu) < 32 and ky_tu not in "\n\r\t":
            return "ky-tu-dieu-khien"
        if ord(ky_tu) == 127:
            return "ky-tu-dieu-khien"
    return None


def chuan_hoa_trich_dan(tho: Any) -> List[Dict[str, str]]:
    """Ép trích dẫn về đúng ba trường giao diện đọc: nhan, nguon, duongDan.

    Không tin hình dạng cổng mô hình trả về. Giao diện dựng danh sách nguồn bằng
    `textContent` nên không có đường chèn HTML, nhưng một trường thiếu vẫn làm
    dòng nguồn hiện ra chữ "undefined" — và một bảng nguồn nhìn như hỏng thì
    người đọc thôi tin cả phần trích dẫn.

    Rỗng khi chưa có RAG. Đó là câu trả lời ĐÚNG ở bản này: chưa nối kho tài liệu
    thì không có nguồn nào để dẫn, và bịa ra một danh sách rỗng-mà-có-tiêu-đề còn
    tệ hơn.
    """
    if not isinstance(tho, list):
        return []
    ra = []
    for chi_so, muc in enumerate(tho, start=1):
        if not isinstance(muc, dict):
            continue
        ra.append(
            {
                "nhan": str(muc.get("nhan", chi_so)),
                "nguon": str(muc.get("nguon", "")),
                "duongDan": str(muc.get("duongDan", "")),
            }
        )
    return ra


# ──────────────────────────────────────────────────────────────────────────────
# Dựng và chạy
# ──────────────────────────────────────────────────────────────────────────────


def kiem_dia_chi(dia_chi: str, cho_phep: Optional[str] = None) -> None:
    """Ném `LoiDiaChiKhongAnToan` nếu bị bảo nghe ngoài loopback mà chưa khai.

    VÌ SAO CHẶN: bản này KHÔNG CÓ XÁC THỰC. Danh tính là một hằng số, nên mọi hội
    thoại thuộc về bất kỳ ai gọi tới được. Nghe 127.0.0.1 thì "ai gọi tới được"
    nghĩa là "người đang ngồi trước máy". Nghe 0.0.0.0 thì nghĩa là cả mạng — máy
    chủ biến thành một kho dữ liệu mở, và không có một dòng mã nào trong tệp này
    ngăn được điều đó ngoài phép kiểm này.

    Có đường mở khoá, vì có ca dùng thật (chạy trong container, nghe trên giao
    diện nội bộ rồi để một lớp proxy có xác thực đứng trước). Nhưng đường ấy phải
    do người vận hành gõ tay một câu tiếng Việt, chứ không bật được bằng một cờ
    `true` sao chép từ kịch bản khác.
    """
    if dia_chi in DIA_CHI_CUC_BO:
        return
    if cho_phep is None:
        cho_phep = os.environ.get(BIEN_NGHE_NGOAI, "").strip()
    if cho_phep == GIA_TRI_CHAP_NHAN_RUI_RO:
        return
    raise LoiDiaChiKhongAnToan(
        "Từ chối nghe ở '%s': bản này CHƯA CÓ XÁC THỰC, nghe ngoài 127.0.0.1 là mở "
        "toàn bộ hội thoại cho cả mạng. Muốn vẫn làm thì đặt %s=%s và tự chịu trách "
        "nhiệm đặt một lớp xác thực đứng trước."
        % (dia_chi, BIEN_NGHE_NGOAI, GIA_TRI_CHAP_NHAN_RUI_RO)
    )


def tao_may_chu(
    dia_chi: Optional[str] = None,
    cong: Optional[int] = None,
    kho: Any = None,
    cong_mo_hinh: Any = TU_NAP,
    cau_hinh_ngoai: Any = TU_NAP,
    nguoi_demo: Optional[str] = None,
    thu_muc_giao_dien: Optional[str] = None,
    cho_phep_nghe_ngoai: Optional[str] = None,
) -> ThreadingHTTPServer:
    """Dựng máy chủ. KIỂM ĐỊA CHỈ TRƯỚC KHI MỞ SOCKET.

    Thứ tự quan trọng: `kiem_dia_chi` chạy trước `ThreadingHTTPServer(...)`, nên
    khi phép kiểm từ chối thì không có cổng nào từng được mở, dù chỉ một nhịp.

    `cong_mo_hinh=None` nghĩa là CỐ Ý không có cổng mô hình (bài tự kiểm dùng ca
    này), còn bỏ trống thì tự đi nạp. Hai ý ấy phải phân biệt được: nếu `None`
    cũng có nghĩa "tự nạp" thì bài kiểm "chưa cài cổng mô hình" sẽ âm thầm chạy
    với cổng thật và ĐẠT vì một lý do khác hẳn lý do nó được viết ra — đã dính
    đúng lỗi này một lần trong phiên 26/09/2026.
    """
    if dia_chi is None:
        dia_chi = os.environ.get(BIEN_DIA_CHI, "").strip() or DIA_CHI_MAC_DINH
    if cong is None:
        cong = int(os.environ.get(BIEN_CONG, "").strip() or CONG_MAC_DINH)

    kiem_dia_chi(dia_chi, cho_phep_nghe_ngoai)

    if kho is None:
        kho = kho_hoi_thoai.KhoHoiThoai()
    if cau_hinh_ngoai is TU_NAP:
        cau_hinh_ngoai = nap_cau_hinh_ngoai()
    if cong_mo_hinh is TU_NAP:
        cong_mo_hinh = nap_cong_mo_hinh(cau_hinh_ngoai)

    boi_canh = BoiCanh(
        kho=kho,
        cong_mo_hinh=cong_mo_hinh,
        cau_hinh_ngoai=cau_hinh_ngoai,
        nguoi_demo=nguoi_demo,
        thu_muc_giao_dien=thu_muc_giao_dien,
    )
    may_chu = ThreadingHTTPServer((dia_chi, cong), tao_lop_xu_ly(boi_canh))
    # Luồng con không giữ tiến trình sống sau Ctrl-C.
    may_chu.daemon_threads = True
    may_chu.boi_canh = boi_canh  # để kịch bản gọi ngoài đọc được cấu hình đang chạy
    return may_chu


def nap_cau_hinh_ngoai() -> Any:
    """Dựng `cau_hinh.CauHinhPhucVu` từ biến môi trường, hoặc None.

    Thiếu `BDSG_VLLM_URL` thì `tu_moi_truong()` ném `LoiCauHinh` — và đó là hành
    vi ĐÚNG của nó: lớp cấu hình cố ý không có địa chỉ mặc định. Ở đây bắt lại và
    trả None, kèm một dòng ra stderr, vì máy chủ vẫn phải lên được để người mới
    nhìn thấy giao diện và đọc được câu báo lỗi. Nuốt im thì không ai biết vì sao
    hỏi mãi không ra.
    """
    try:
        import cau_hinh
    except ImportError:
        return None
    try:
        return cau_hinh.CauHinhPhucVu.tu_moi_truong()
    except Exception as loi:  # noqa: BLE001
        sys.stderr.write(
            "CHU Y: chua dung duoc cau hinh may phuc vu mo hinh (%s: %s). "
            "May chu van len, nhung POST /api/hoi se bao loi.\n"
            % (type(loi).__name__, loi)
        )
        return None


def nap_cong_mo_hinh(cau_hinh_phuc_vu: Any = None) -> Any:
    """Dựng `cong_mo_hinh.CongMoHinh`, hoặc None khi chưa đủ điều kiện.

    Không dùng `importlib` thủ công: thư mục này đã nằm trong `sys.path` (xem đầu
    tệp), nên một `import` bình thường là đủ. Thiếu mô-đun hoặc thiếu cấu hình
    KHÔNG phải lỗi chết người — xem phần "phụ thuộc" ở đầu tệp.
    """
    try:
        import cong_mo_hinh
    except ImportError:
        return None
    if cau_hinh_phuc_vu is None:
        return None
    try:
        return cong_mo_hinh.CongMoHinh(cau_hinh_phuc_vu)
    except Exception as loi:  # noqa: BLE001
        sys.stderr.write(
            "CHU Y: khong dung duoc cong mo hinh (%s: %s).\n"
            % (type(loi).__name__, loi)
        )
        return None


def doc_mo_hinh_that(thu_thap: Dict[str, Any]) -> Optional[str]:
    """Tên mô hình THẬT lấy từ hộp thu thập của cổng mô hình.

    Trả None khi cổng không khai gì. KHÔNG rơi về mã đã gửi đi ở tầng này: vọng
    lại tên mình vừa gửi chính là lời khai sai mà trường `moHinhThat` sinh ra để
    chống. (Cổng mô hình thật có luật riêng của nó cho ca ấy — nó đứng gần phản
    hồi hơn nên nó biết nhiều hơn; máy chủ chỉ chuyển tiếp thứ cổng khai.)
    """
    gia_tri = thu_thap.get("mo_hinh_that")
    if isinstance(gia_tri, str) and gia_tri.strip():
        return gia_tri.strip()
    return None


def main(tham_so: Optional[Iterable[str]] = None) -> int:
    dia_chi = os.environ.get(BIEN_DIA_CHI, "").strip() or DIA_CHI_MAC_DINH
    cong = int(os.environ.get(BIEN_CONG, "").strip() or CONG_MAC_DINH)
    try:
        may_chu = tao_may_chu(dia_chi, cong)
    except LoiDiaChiKhongAnToan as loi:
        sys.stderr.write("HONG: %s\n" % (loi,))
        return 2
    except OSError as loi:
        sys.stderr.write("HONG: khong mo duoc %s:%s — %s\n" % (dia_chi, cong, loi))
        return 2

    boi_canh = may_chu.boi_canh
    print("=" * 78)
    print("BDSG Chat — may chu NOI BO")
    print("  Nghe tai      : http://%s:%s" % (dia_chi, cong))
    print("  Kho hoi thoai : %s" % (boi_canh.kho.duong_dan,))
    print("  Ma mo hinh    : %s" % (boi_canh.cau_hinh["ma"],))
    xuat_xu = xuat_xu_trong_so(boi_canh.cau_hinh["trong_so_nen"])
    print("  Trong so nen  : %s (%s, %s)" % (
        boi_canh.cau_hinh["trong_so_nen"],
        xuat_xu["nhaCungCap"],
        xuat_xu["giayPhep"],
    ))
    # ĐỌC giá trị thật chứ không in sẵn chữ "False". Dòng này nói về việc AI đã
    # làm ra trọng số đang chạy, nên nó phải là một PHÉP ĐO chứ không phải một
    # câu viết cứng: một hằng số in ra thì vẫn đúng ngày người vận hành trỏ máy
    # chủ sang một trọng số khác, và lúc ấy nó thành một lời khai sai.
    la_bdsg = la_trong_so_bdsg(boi_canh.cau_hinh["trong_so_nen"])
    print("  bdsg_la_trong_so_bdsg = %s" % (la_bdsg,))
    if la_bdsg:
        print("                  (trong so nay khai la DA DUOC BDSG tinh chinh)")
    else:
        print("                  (BDSG PHUC VU trong so cua Google;")
        print("                   BDSG chua tinh chinh trong so nao)")
    if boi_canh.cong_mo_hinh is None:
        print("  Cong mo hinh  : CHUA CO (phuc-vu/cong_mo_hinh.py).")
        print("                  Cac duong khac chay binh thuong; POST /api/hoi bao loi.")
    else:
        print("  Cong mo hinh  : da nap")
    print("-" * 78)
    print("  CANH BAO: ban DEMO MOT NGUOI. Chua co dang nhap ⇒ chua dung duoc cho")
    print("            nhieu nhan vien. Khong dat may chu nay ra Internet.")
    print("=" * 78)
    try:
        may_chu.serve_forever()
    except KeyboardInterrupt:
        print("\nDung theo yeu cau.")
    finally:
        may_chu.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
