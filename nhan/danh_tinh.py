#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/danh_tinh.py — AI ĐANG GỌI.

Lớp này trả lời đúng một câu hỏi, và không trả lời câu nào khác: *ai* đang đứng
sau lời gọi công cụ này. Nó KHÔNG quyết định người đó được làm gì (xem
`nhan/quyen.py`), KHÔNG đếm số lần gọi (xem `nhan/han_muc.py`), KHÔNG ghi chép
(xem `nhan/nhat_ky.py`).

HAI LUẬT CỨNG CỦA TỆP NÀY
-------------------------
1. KHÔNG CÓ DANH TÍNH "KHÁCH" MẶC ĐỊNH.
   Không xác định được thì `xac_thuc()` trả `None`. Tuyệt đối không trả về một
   danh tính vô danh có sẵn một vài nào đó. Một hệ thống mở toang mà *trông như*
   có xác thực thì nguy hiểm hơn một hệ thống không có xác thực, vì không ai đi
   kiểm lại nó. Trong kho này còn một bài học thật về họ lỗi ấy: một cơ chế đăng
   nhập một lần từng so khớp email rồi cấp quyền theo chuỗi khớp được, và thế là
   chiếm được tài khoản quản trị. Danh tính phải do NGUỒN xác thực khẳng định,
   không phải do một giá trị mặc định nào đó điền hộ.

2. KHÔNG TỰ CÀI ĐẶT MẬT MÃ.
   Tệp này không băm mật khẩu, không ký JWT, không so khoá. Nó nhận một HÀM XÁC
   THỰC tiêm vào từ bên ngoài (`dang_ky_nguon`). Lý do: mật mã tự viết là một
   trong những cách hỏng âm thầm chắc chắn nhất — nó vẫn chạy, vẫn trả True/False,
   và sai ở chỗ không ai nhìn thấy. Doanh nghiệp triển khai nhân này sẽ cắm vào
   đây thứ họ đã có sẵn (LDAP, một bảng khoá API, phiên của ứng dụng web…).

   Ngoại lệ duy nhất: `so_sanh_hang_dinh()` bọc `hmac.compare_digest` của thư
   viện chuẩn. Đó là một phép SO SÁNH, không phải một thuật toán mật mã; để nó ở
   đây vì người viết hàm xác thực rất hay dùng `==` và rò rỉ thời gian.

VÌ SAO `DanhTinh` BẤT BIẾN (frozen)
-----------------------------------
Sau khi nhân xác thực xong, đối tượng danh tính đi qua tay trình điều khiển.
Nếu nó sửa được thì một trình điều khiển (do bên thứ ba viết, cắm vào nhân) chỉ
cần `danh_tinh.vai = ("quan-tri",)` là leo thang quyền, và lần kiểm quyền kế tiếp
trong cùng một tiến trình sẽ tin theo. Đóng băng nó lại thì đường đó không tồn tại.

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import hmac
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Sequence, Tuple, Union

# ── Tên nguồn đã biết ────────────────────────────────────────────────────────
# Đây chỉ là HẰNG SỐ TIỆN TAY, không phải danh sách đóng: `dang_ky_nguon` nhận
# tên tuỳ ý. Yêu cầu tối thiểu của dự án là hai nguồn dưới đây phải chạy được.
NGUON_KHOA_API = "khoa-api"
NGUON_PHIEN = "phien-nguoi-dung"

# Mã danh tính và tên vai dùng làm khoá trong nhật ký, trong bảng hạn mức và
# trong tệp cấu hình quyền. Cho phép ký tự lạ vào đây là mở đường cho chuyện
# nhỏ mà bẩn: một mã chứa dấu chấm sẽ trộn lẫn với cú pháp
# `<trinh_dieu_khien>.<cong_cu>`, một mã chứa xuống dòng sẽ bẻ gãy nhật ký
# một-dòng-một-bản-ghi. Chặn ngay từ lúc dựng đối tượng.
MAU_MA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-@]{0,127}$")
MAU_VAI = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")
MAU_NGUON = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")


class LoiDanhTinh(ValueError):
    """Danh tính dựng sai. Ném lúc DỰNG, không phải lúc dùng.

    Cố ý ném sớm: một danh tính méo mó lọt được vào hệ thống thì chỗ nó gây hại
    (nhật ký lệch, khoá hạn mức trùng nhau) cách chỗ nó sinh ra rất xa.
    """


@dataclass(frozen=True)
class DanhTinh:
    """Ai đang gọi.

    ma     : định danh bền, duy nhất trong phạm vi một nguồn. Đây là thứ đi vào
             nhật ký và làm khoá hạn mức. KHÔNG dùng tên người làm mã.
    ten    : tên hiển thị cho người đọc. Có thể rỗng. CỐ Ý không đưa vào nhật ký
             (xem `tom_tat()`), vì nhật ký giữ lâu và tên là dữ liệu cá nhân.
    vai    : bộ vai, luôn là tuple. Nhận vào một chuỗi thì tự gói thành tuple một
             phần tử — một người thật hay có nhiều vai, ép mỗi người một vai chỉ
             đẻ ra những tài khoản-vai dùng chung, tức là mất dấu vết ai làm gì.
    nguon  : tên nguồn đã xác thực ra danh tính này.
    het_han: mốc thời gian epoch (giây) mà danh tính hết hiệu lực; None = nguồn
             không khai hạn. None KHÔNG có nghĩa là "vĩnh viễn hợp lệ" — nghĩa là
             "nguồn không nói", và nhân sẽ không tự bịa ra một hạn.
    """

    ma: str
    ten: str = ""
    vai: Tuple[str, ...] = field(default=())
    nguon: str = ""
    het_han: Optional[float] = None

    def __post_init__(self) -> None:
        # frozen=True chặn gán thường, nên chuẩn hoá phải đi qua object.__setattr__.
        if isinstance(self.vai, str):
            object.__setattr__(self, "vai", (self.vai,))
        else:
            object.__setattr__(self, "vai", tuple(self.vai))

        if not isinstance(self.ma, str) or not MAU_MA.match(self.ma):
            raise LoiDanhTinh(
                "mã danh tính không hợp lệ: %r (cần khớp %s)" % (self.ma, MAU_MA.pattern)
            )
        if not isinstance(self.nguon, str) or not MAU_NGUON.match(self.nguon):
            raise LoiDanhTinh("nguồn không hợp lệ: %r" % (self.nguon,))
        if not self.vai:
            # Danh tính KHÔNG VAI là hợp lệ về mặt dữ liệu, nhưng đây gần như luôn
            # là lỗi cấu hình, và hậu quả của nó im lặng: `quyen.duoc_goi` sẽ từ
            # chối mọi thứ và người dùng chỉ thấy "không có quyền" mà không hiểu
            # vì sao. Cho phép dựng, nhưng phải cố ý — xem `khong_vai()`.
            raise LoiDanhTinh(
                "danh tính %r không có vai nào. Nếu CỐ Ý muốn một danh tính "
                "không quyền gì, gọi DanhTinh.khong_vai(...)" % (self.ma,)
            )
        for v in self.vai:
            if not isinstance(v, str) or not MAU_VAI.match(v):
                raise LoiDanhTinh("tên vai không hợp lệ: %r" % (v,))
        if len(set(self.vai)) != len(self.vai):
            raise LoiDanhTinh("vai bị lặp trong %r" % (self.vai,))
        if self.het_han is not None and not isinstance(self.het_han, (int, float)):
            raise LoiDanhTinh("het_han phải là số epoch giây hoặc None")

    # -- tiện ích -------------------------------------------------------------

    @classmethod
    def khong_vai(cls, ma: str, ten: str = "", nguon: str = "", **kw) -> "DanhTinh":
        """Dựng một danh tính KHÔNG có vai nào — tức là không được gọi gì cả.

        Có mặt để phép thử và những lối vào "đã nhận ra người nhưng chưa cấp
        quyền" không phải lách bằng cách bịa một vai giả. Nó đi qua
        `__post_init__` bằng một vai đặc biệt rồi rút vai ấy ra.
        """
        dt = cls(ma=ma, ten=ten, vai=("tam",), nguon=nguon, **kw)
        object.__setattr__(dt, "vai", ())
        return dt

    def con_hieu_luc(self, bay_gio: Optional[float] = None) -> bool:
        """het_han=None ⇒ còn hiệu lực (nguồn không khai hạn thì nhân không bịa)."""
        if self.het_han is None:
            return True
        if bay_gio is None:
            bay_gio = time.time()
        return bay_gio < self.het_han

    def co_vai(self, ten_vai: str) -> bool:
        return ten_vai in self.vai

    def tom_tat(self) -> Dict[str, object]:
        """Dạng rút gọn để ĐƯA VÀO NHẬT KÝ.

        CỐ Ý KHÔNG có `ten`. Nhật ký sống lâu hơn phiên làm việc rất nhiều và
        thường được đẩy sang nơi khác để phân tích; tên người là dữ liệu cá nhân,
        còn `ma` đã đủ để truy ra ai. Cần tên thì tra ngược từ `ma` trong hệ quản
        lý người dùng — chỗ có kiểm soát truy cập, khác hẳn một tệp nhật ký.
        """
        return {"ma": self.ma, "vai": list(self.vai), "nguon": self.nguon}


# Kiểu của một hàm xác thực tiêm vào: nhận chứng thư thô, trả DanhTinh hoặc None.
HamXacThuc = Callable[[str], Optional[DanhTinh]]


def so_sanh_hang_dinh(a: Union[str, bytes], b: Union[str, bytes]) -> bool:
    """So sánh hai bí mật trong thời gian không phụ thuộc nội dung.

    Bọc `hmac.compare_digest` của thư viện chuẩn. KHÔNG phải mật mã tự viết —
    chỉ là phép so sánh. Để ở đây vì hàm xác thực do người dùng tiêm vào rất hay
    viết `if khoa == khoa_that`, và `==` thoát ra ở byte khác đầu tiên, đủ để dò
    dần từng ký tự qua đo thời gian.
    """
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hmac.compare_digest(a, b)


class BoXacThuc:
    """Sổ đăng ký các nguồn xác thực, và cửa vào duy nhất để đổi chứng thư lấy danh tính.

    Nhân giữ đúng MỘT bộ này. Trình điều khiển KHÔNG được cầm nó — nếu mỗi trình
    điều khiển tự xác thực thì 18 nền tảng cho ra 18 mô hình danh tính khác nhau,
    và câu hỏi "ai đã làm gì" không còn câu trả lời duy nhất nào.
    """

    def __init__(self, dong_ho: Callable[[], float] = time.time) -> None:
        # dong_ho tiêm vào để bài tự kiểm kiểm được chuyện hết hạn mà không phải
        # chờ thật. Mọi chỗ trong nhân đều theo quy ước này.
        self._nguon: Dict[str, HamXacThuc] = {}
        self._dong_ho = dong_ho

    def dang_ky_nguon(self, nguon: str, ham: HamXacThuc) -> None:
        if not MAU_NGUON.match(nguon or ""):
            raise LoiDanhTinh("tên nguồn không hợp lệ: %r" % (nguon,))
        if not callable(ham):
            raise LoiDanhTinh("hàm xác thực của nguồn %r không gọi được" % (nguon,))
        if nguon in self._nguon:
            # Ghi đè im lặng là cách một mô-đun nạp sau chiếm quyền xác thực của
            # mô-đun nạp trước. Muốn thay thì gỡ tường minh.
            raise LoiDanhTinh("nguồn %r đã đăng ký rồi; gỡ trước nếu muốn thay" % (nguon,))
        self._nguon[nguon] = ham

    def go_nguon(self, nguon: str) -> None:
        self._nguon.pop(nguon, None)

    def cac_nguon(self):
        return sorted(self._nguon)

    def xac_thuc(self, nguon: str, chung_thu: Optional[str]) -> Optional[DanhTinh]:
        """Trả DanhTinh, hoặc None. KHÔNG BAO GIỜ trả một danh tính mặc định."""
        return self.xac_thuc_ky(nguon, chung_thu)[0]

    def xac_thuc_ky(
        self, nguon: str, chung_thu: Optional[str]
    ) -> Tuple[Optional[DanhTinh], str]:
        """Như `xac_thuc` nhưng kèm LÝ DO — nhân cần lý do để ghi nhật ký.

        Lý do trả về CỐ Ý thô sơ và giống nhau giữa các ca hỏng ("không xác định
        được danh tính"), vì chuỗi này có thể đi ngược ra phía người gọi. Phân
        biệt "không có nguồn ấy" với "khoá sai" là chỉ cho người dò biết họ đang
        đi đúng hướng. Chi tiết nằm ở phần sau dấu hai chấm và chỉ dùng cho nhật
        ký nội bộ.
        """
        if not nguon or nguon not in self._nguon:
            return None, "không xác định được danh tính: nguồn %r chưa đăng ký" % (nguon,)
        if not isinstance(chung_thu, str) or not chung_thu:
            return None, "không xác định được danh tính: chứng thư rỗng"

        try:
            dt = self._nguon[nguon](chung_thu)
        except Exception as loi:  # hàm tiêm vào là mã của người khác
            # Hàm xác thực nổ KHÔNG được làm sập nhân, và KHÔNG được biến thành
            # "cho qua". Nổ ⇒ từ chối.
            return None, "không xác định được danh tính: nguồn %r nổ: %s" % (
                nguon,
                type(loi).__name__,
            )

        if dt is None:
            return None, "không xác định được danh tính: nguồn %r từ chối" % (nguon,)
        if not isinstance(dt, DanhTinh):
            # Một hàm trả về dict hay chuỗi mà nhân cứ thế tin là đường vào kinh
            # điển: phía sau chỉ cần `danh_tinh.vai` là nổ, hoặc tệ hơn, một dict
            # có khoá "vai" lại chạy được y như thật mà bỏ qua mọi phép kiểm
            # trong __post_init__.
            return None, "nguồn %r trả về %s chứ không phải DanhTinh" % (
                nguon,
                type(dt).__name__,
            )
        if dt.nguon != nguon:
            # Nguồn A không được phép phát hành danh tính mang nhãn nguồn B. Nếu
            # cho phép, chính sách quyền viết theo nguồn sẽ bị lách bằng cách cắm
            # thêm một nguồn dễ dãi.
            return None, "nguồn %r phát hành danh tính mang nhãn nguồn %r" % (
                nguon,
                dt.nguon,
            )
        if not dt.con_hieu_luc(self._dong_ho()):
            return None, "danh tính %r đã hết hạn" % (dt.ma,)
        if not dt.vai:
            # Hợp lệ về dữ liệu, nhưng nói thẳng ra để nhật ký không chỉ ghi
            # "không có quyền" ở bước sau mà không ai hiểu vì sao.
            return dt, "danh tính %r hợp lệ nhưng KHÔNG có vai nào" % (dt.ma,)
        return dt, "danh tính %r hợp lệ qua nguồn %r" % (dt.ma, nguon)


# ── Một nguồn mẫu: bảng khoá API trong bộ nhớ ────────────────────────────────
def nguon_bang_khoa(
    bang: Dict[str, DanhTinh], nguon: str = NGUON_KHOA_API
) -> HamXacThuc:
    """Dựng một hàm xác thực từ bảng {khoa_thô: DanhTinh}.

    ⚠ CHỈ DÙNG ĐỂ THỬ VÀ ĐỂ CHẠY CỤC BỘ. Bảng này giữ khoá ở dạng THÔ trong bộ
    nhớ. Bản triển khai thật phải giữ BĂM của khoá, không giữ khoá — nhưng việc
    băm là mật mã, và mật mã thì tệp này không tự cài (xem đầu tệp). Doanh nghiệp
    cắm hàm của mình vào đây.

    So khớp đi qua `so_sanh_hang_dinh` và duyệt HẾT bảng kể cả khi đã khớp, để
    thời gian chạy không phụ thuộc vị trí khoá trong bảng. Với bảng lớn thì đây
    là cách sai về hiệu năng — lại thêm một lý do nữa để đừng dùng nó thật.
    """

    def xac_thuc(chung_thu: str) -> Optional[DanhTinh]:
        tim_thay = None
        for khoa, dt in bang.items():
            if so_sanh_hang_dinh(khoa, chung_thu) and tim_thay is None:
                tim_thay = dt
        return tim_thay

    xac_thuc.__doc__ = "Nguồn khoá API trong bộ nhớ (%s)." % nguon
    return xac_thuc
