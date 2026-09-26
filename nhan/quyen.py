#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/quyen.py — AI ĐƯỢC GỌI CÔNG CỤ NÀO.

Mô hình: **vai → tập công cụ**, theo DANH SÁCH TRẮNG.

VÌ SAO DANH SÁCH TRẮNG CHỨ KHÔNG PHẢI DANH SÁCH ĐEN
---------------------------------------------------
Với danh sách đen, mỗi công cụ MỚI thêm vào là một lỗ hổng mở sẵn cho tới khi có
người nhớ ra phải khai nó. Mà thứ hay quên nhất chính là công cụ vừa viết xong
lúc 11 giờ đêm. Với danh sách trắng, công cụ mới mặc định KHÔNG ai gọi được: hỏng
kiểu "chưa ai dùng được" thì có người báo trong mười phút, còn hỏng kiểu "ai cũng
dùng được" thì im lặng cho tới lúc đọc nhật ký sự cố.

Hệ quả có chủ ý: kho này KHÔNG hỗ trợ ký tự đại diện (`*`, `crm.*`). Một dòng
`crm.*` trong tệp cấu hình có nghĩa là "cả những công cụ chưa ai viết", tức là
danh sách đen đội lốt danh sách trắng. Khai từng cái. Dài hơn, và đọc xong thì
biết đúng cái gì đang mở.

BA CỔNG CHO MỘT LỜI GỌI GHI
---------------------------
Quyết định kiến trúc số 3 của dự án: mặc định chỉ đọc. Ở đây nó thành ba phép
kiểm ĐỘC LẬP, phải qua cả ba:

  1. Trình điều khiển phải KHAI công cụ ấy là công cụ ghi (`ghi=True`). Người
     viết trình điều khiển là người duy nhất biết lời gọi của mình có ghi hay
     không.
  2. Vai phải được cấp công cụ ấy trong danh sách `ghi=`. Được cấp `doc=` KHÔNG
     tự động có `ghi=` — đây là câu chữ nguyên văn trong yêu cầu, và nó quan
     trọng vì mô hình quyền hay trượt theo hướng "đã đọc được thì cho sửa luôn".
  3. `CongGhi` của cả nhân phải MỞ. Đây là một công tắc toàn cục, ngoài chính
     sách vai. Vai trò của nó: chạy nhân ở chế độ quan sát (điều tra sự cố, thử
     nghiệm, môi trường sao chép dữ liệu thật) mà không phải sửa chính sách — và
     sửa chính sách "tạm một lát" là cách người ta quên bật lại.

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .danh_tinh import DanhTinh

# Loại công cụ
DOC = "doc"
GHI = "ghi"

# Tên công cụ đầy đủ: <trinh_dieu_khien>.<cong_cu>. Xem `nhan/dinh_tuyen.py` để
# biết vì sao có dấu chấm thay vì một không gian tên phẳng.
# NEO CUỐI LÀ \Z, KHÔNG PHẢI $. Sửa 26/09/2026.
#
#   Trong Python, `$` khớp ở cuối chuỗi VÀ ngay trước một ký tự xuống dòng ở
#   cuối chuỗi. Nên `re.compile(r"^[a-z]+$").match("quan-tri\n")` KHỚP. Hệ quả đo
#   được: một tên vai / tên công cụ / mã danh tính kết thúc bằng xuống dòng đi
#   lọt qua mọi phép kiểm hợp lệ, rồi bẻ gãy nhật ký một-dòng-một-bản-ghi ở tầng
#   dưới — bản ghi bị cắt làm đôi và câu "ai đã làm gì" mất nửa sau.
#
#   `\Z` chỉ khớp ở cuối chuỗi thật. Mọi mẫu KIỂM HỢP LỆ trong nhân dùng \Z.
#   Các mẫu DÒ TÌM trong nhat_ky.py giữ `$`: ở đó khớp rộng hơn là làm mờ nhiều
#   hơn, tức nghiêng về phía an toàn.
#
#   Hai vế đều mở đầu bằng CHỮ CÁI, khớp với `MAU_TEN_TRINH`/`MAU_TEN_NGAN`
#   trong `dinh_tuyen.py` (sửa 26/09/2026, lý do đầy đủ ghi ở đó: một tên như
#   `123.45` đọc thành SỐ trong mọi tệp cấu hình). Hai lớp phải cùng một luật —
#   lớp quyền nhận một tên mà lớp định tuyến từ chối thì chính sách có những
#   dòng không bao giờ dùng tới, và không ai được báo.
MAU_TEN_DAY_DU = re.compile(r"^[a-z][a-z0-9_]{0,31}\.[a-z][a-z0-9_]{0,63}\Z")
MAU_TEN_VAI = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}\Z")


class LoiChinhSach(ValueError):
    """Chính sách khai sai.

    Ném lúc KHAI BÁO, không phải lúc gọi. Một dòng cấp quyền gõ nhầm tên công cụ
    mà chỉ im lặng không có tác dụng thì người quản trị tin rằng mình đã cấp
    quyền, người dùng thì bị từ chối, và cả hai mất nửa ngày. Nổ ngay lúc nạp
    cấu hình rẻ hơn nhiều.
    """


@dataclass(frozen=True)
class MoTaCongCu:
    """Một công cụ đã được khai với nhân."""

    ten: str          # đầy đủ: <trinh_dieu_khien>.<cong_cu>
    loai: str         # DOC hoặc GHI
    mo_ta: str = ""

    @property
    def la_ghi(self) -> bool:
        return self.loai == GHI


class CongGhi:
    """Công tắc GHI toàn nhân. Mặc định ĐÓNG.

    Cố ý là một đối tượng chứ không phải một biến bool: nó mang theo lý do mở và
    ai mở, và nhật ký ghi lại được. Một biến bool thì không trả lời được câu
    "vì sao hôm ấy nhân đang mở ghi".
    """

    def __init__(self, mo: bool = False, ly_do: str = "", nguoi_mo: str = "") -> None:
        # ĐƯỜNG VÒNG ĐÃ BỊT, 26/09/2026.
        #
        #   `mo()` đòi ly_do và nguoi_mo — nhưng hàm khởi tạo thì không, nên
        #   `CongGhi(mo=True)` mở được cổng ghi toàn nhân mà không để lại dấu vết
        #   nào về vì sao và do ai. Một phép kiểm chỉ đứng ở MỘT cửa thì cửa kia
        #   là đường vòng, và đường vòng ấy ngắn hơn cửa chính.
        if mo and (not ly_do or not nguoi_mo):
            raise LoiChinhSach(
                "CongGhi(mo=True) phải kèm ly_do và nguoi_mo — cùng một luật với "
                "mo(). Mở cổng ghi vô danh là thứ nhật ký không giải thích được."
            )
        self._mo = bool(mo)
        self._ly_do = ly_do
        self._nguoi_mo = nguoi_mo

    @property
    def dang_mo(self) -> bool:
        return self._mo

    def mo(self, ly_do: str, nguoi_mo: str) -> None:
        if not ly_do or not nguoi_mo:
            # Không cho mở cổng ghi một cách vô danh, không lý do. Đây là chỗ
            # duy nhất trong nhân bắt buộc phải nói vì sao.
            raise LoiChinhSach("mở cổng ghi phải kèm ly_do và nguoi_mo")
        self._mo = True
        self._ly_do = ly_do
        self._nguoi_mo = nguoi_mo

    def dong(self) -> None:
        self._mo = False

    def tom_tat(self) -> Dict[str, object]:
        return {"dang_mo": self._mo, "ly_do": self._ly_do, "nguoi_mo": self._nguoi_mo}


class ChinhSach:
    """Sổ công cụ + bảng vai→công cụ, và hàm quyết định `duoc_goi`."""

    def __init__(self, cong_ghi: Optional[CongGhi] = None) -> None:
        self._cong_cu: Dict[str, MoTaCongCu] = {}
        self._vai_doc: Dict[str, Set[str]] = {}
        self._vai_ghi: Dict[str, Set[str]] = {}
        self.cong_ghi = cong_ghi if cong_ghi is not None else CongGhi(mo=False)

    # -- khai báo -------------------------------------------------------------

    def khai_cong_cu(self, ten: str, ghi: bool = False, mo_ta: str = "") -> MoTaCongCu:
        """Khai sự TỒN TẠI của một công cụ và nó có ghi hay không.

        Khai ở đây KHÔNG cấp quyền cho ai cả. Tồn tại và được phép là hai chuyện
        khác nhau, và tách chúng ra là cách duy nhất để `tools/list` có thể trả
        lời "công cụ này có thật, nhưng vai của bạn không được gọi" thay vì giả
        vờ nó không tồn tại.
        """
        if not isinstance(ten, str) or not MAU_TEN_DAY_DU.match(ten):
            raise LoiChinhSach(
                "tên công cụ %r không hợp lệ; cần dạng <trinh_dieu_khien>.<cong_cu> "
                "khớp %s" % (ten, MAU_TEN_DAY_DU.pattern)
            )
        if ten in self._cong_cu:
            # Khai lại với cùng thuộc tính thì bỏ qua; khác thuộc tính thì nổ.
            cu = self._cong_cu[ten]
            moi_loai = GHI if ghi else DOC
            if cu.loai != moi_loai:
                raise LoiChinhSach(
                    "công cụ %r đã khai là %r, nay khai lại là %r — một công cụ "
                    "đổi từ đọc sang ghi giữa chừng thì mọi lần cấp quyền trước "
                    "đó thành sai" % (ten, cu.loai, moi_loai)
                )
            return cu
        mt = MoTaCongCu(ten=ten, loai=GHI if ghi else DOC, mo_ta=mo_ta)
        self._cong_cu[ten] = mt
        return mt

    def hoan_nguyen_khai_cong_cu(self, ten: str) -> bool:
        """Gỡ một công cụ VỪA khai, để hoàn nguyên một lần đăng ký hỏng nửa chừng.

        Thêm 26/09/2026 cho `dinh_tuyen.Nhan.dang_ky`: khi một trình điều khiển
        khai năm công cụ và cái thứ ba méo, ba cái đầu đã kịp vào sổ. Không có
        đường gỡ thì chúng ở lại làm công cụ MỒ CÔI — `tools/list` quảng cáo
        chúng, mọi lời gọi đều bị từ chối, và đăng ký lại sau khi sửa thì nổ
        vĩnh viễn vì "khai hai lần".

        HAI GIỚI HẠN CỐ Ý, để hàm này không thành đường hạ quyền âm thầm:

          1. TỪ CHỐI gỡ một công cụ đang được vai nào đó cấp. Gỡ nó sẽ làm dòng
             cấp quyền ấy trỏ vào hư không, và lần `khai_vai` sau mới nổ — xa
             nguyên nhân. Một lần đăng ký hỏng nửa chừng thì chưa vai nào kịp
             được cấp, nên giới hạn này không cản đúng việc nó sinh ra để làm.
          2. Trả về True/False chứ không nổ khi không có gì để gỡ: chỗ gọi là
             một khối dọn dẹp, và một khối dọn dẹp tự ném lỗi sẽ che mất lỗi
             gốc — thứ người sửa thật sự cần đọc.
        """
        if ten not in self._cong_cu:
            return False
        for bang in (self._vai_doc, self._vai_ghi):
            for ten_vai, tap in bang.items():
                if ten in tap:
                    raise LoiChinhSach(
                        "không gỡ được công cụ %r: vai %r đang được cấp nó. "
                        "Thu hồi quyền trước (khai_vai với danh sách không có "
                        "nó), rồi mới gỡ." % (ten, ten_vai)
                    )
        del self._cong_cu[ten]
        return True

    def khai_vai(
        self,
        ten_vai: str,
        doc: Sequence[str] = (),
        ghi: Sequence[str] = (),
    ) -> None:
        """Cấp cho một vai tập công cụ ĐỌC và tập công cụ GHI.

        Mọi tên nêu ra phải đã được khai bằng `khai_cong_cu` — tức là trình điều
        khiển phải đăng ký TRƯỚC khi nạp chính sách. Thứ tự ấy là cố ý: nó biến
        một tên gõ nhầm thành lỗi nạp cấu hình chứ không phải một quyền âm thầm
        không tồn tại.
        """
        if not isinstance(ten_vai, str) or not MAU_TEN_VAI.match(ten_vai):
            raise LoiChinhSach("tên vai %r không hợp lệ" % (ten_vai,))

        doc = tuple(doc)
        ghi = tuple(ghi)
        for ten in doc + ghi:
            if ten == "*" or ten.endswith(".*") or "*" in ten:
                raise LoiChinhSach(
                    "ký tự đại diện %r không được hỗ trợ — xem phần đầu tệp về "
                    "vì sao danh sách trắng không có dấu sao" % (ten,)
                )
            if ten not in self._cong_cu:
                raise LoiChinhSach(
                    "vai %r được cấp công cụ %r nhưng công cụ ấy chưa khai. "
                    "Đăng ký trình điều khiển trước, nạp chính sách sau. "
                    "Công cụ đã khai: %s" % (ten_vai, ten, ", ".join(sorted(self._cong_cu)) or "(chưa có cái nào)")
                )
        for ten in ghi:
            if not self._cong_cu[ten].la_ghi:
                raise LoiChinhSach(
                    "công cụ %r là công cụ ĐỌC, không được cấp qua danh sách ghi= "
                    "của vai %r. Cấp nó ở doc=." % (ten, ten_vai)
                )
        for ten in doc:
            if self._cong_cu[ten].la_ghi:
                raise LoiChinhSach(
                    "công cụ %r là công cụ GHI, không được cấp qua danh sách doc= "
                    "của vai %r. Quyền ghi phải khai tường minh ở ghi=." % (ten, ten_vai)
                )

        # THAY THẾ, KHÔNG CỘNG DỒN. Sửa 26/09/2026.
        #
        #   Bản trước dùng `setdefault(...).update(...)` — tức HỢP TẬP. Hệ quả đo
        #   được: khai lại một vai với danh sách NGẮN HƠN không rút được gì. Sau
        #   khai_vai("v", doc=["crm.a","crm.b"]) rồi khai_vai("v", doc=["crm.a"]),
        #   duoc_goi(dt, "crm.b") VẪN trả (True, "vai 'v' có quyền ĐỌC 'crm.b'").
        #   Trong một nhân phân quyền, không thu hồi được quyền là lỗi nặng hơn
        #   cấp nhầm: cấp nhầm còn sửa được, còn cái này thì không có đường sửa.
        #
        #   Nay khai_vai KHAI BÁO trạng thái cuối của vai. Một tệp chính sách đọc
        #   lên là thấy đúng quyền hiện có, không phải quyền cộng dồn qua các lần
        #   nạp trước đó mà không ai còn nhớ.
        #
        #   Nếu về sau thật sự cần cộng dồn (nạp chính sách từ nhiều tệp), hãy
        #   thêm một hàm RIÊNG tên rõ nghĩa — đừng đổi hàm này lại thành update().
        self._vai_doc[ten_vai] = set(doc)
        self._vai_ghi[ten_vai] = set(ghi)

    # -- tra cứu --------------------------------------------------------------

    def cong_cu_da_khai(self) -> List[str]:
        return sorted(self._cong_cu)

    def mo_ta(self, ten: str) -> Optional[MoTaCongCu]:
        return self._cong_cu.get(ten)

    def la_cong_cu_ghi(self, ten: str) -> bool:
        mt = self._cong_cu.get(ten)
        return bool(mt and mt.la_ghi)

    def cac_vai_da_khai(self) -> List[str]:
        return sorted(set(self._vai_doc) | set(self._vai_ghi))

    # -- quyết định -----------------------------------------------------------

    def duoc_goi(
        self, danh_tinh: Optional[DanhTinh], ten_cong_cu: str
    ) -> Tuple[bool, str]:
        """(được hay không, LÝ DO).

        LUÔN trả lý do, kể cả khi cho phép. Nhật ký cần nó: một dòng nhật ký chỉ
        ghi "thành công" không trả lời được câu "vì sao người này gọi được công
        cụ đó" — mà đó chính là câu hỏi đầu tiên sau một sự cố.
        """
        if danh_tinh is None:
            # Chốt chặn thứ hai cho luật "không có khách mặc định". Nhân đã kiểm
            # ở `dinh_tuyen`, nhưng lớp quyền không được TIN rằng lớp trên đã
            # kiểm — một hàm quyết định mà cho `None` đi qua thì bất kỳ đường gọi
            # nào bỏ sót một phép kiểm đều thành đường mở toang.
            return False, "từ chối: không có danh tính"

        mt = self._cong_cu.get(ten_cong_cu)
        if mt is None:
            return False, (
                "từ chối: công cụ %r không có trong danh sách trắng "
                "(chưa trình điều khiển nào khai nó)" % (ten_cong_cu,)
            )

        if not danh_tinh.vai:
            return False, "từ chối: danh tính %r không có vai nào" % (danh_tinh.ma,)

        vai_chua_khai = [v for v in danh_tinh.vai if v not in self._vai_doc and v not in self._vai_ghi]

        if mt.la_ghi:
            # Cổng 3 kiểm TRƯỚC khi xét vai. Cố ý: khi cả nhân đang ở chế độ chỉ
            # đọc thì lý do đúng là "nhân đang chỉ đọc", chứ không phải "vai của
            # bạn thiếu quyền" — nói sai lý do thì người quản trị đi sửa nhầm chỗ.
            if not self.cong_ghi.dang_mo:
                return False, (
                    "từ chối: %r là công cụ GHI và cổng ghi của nhân đang ĐÓNG "
                    "(mặc định chỉ đọc)" % (ten_cong_cu,)
                )
            for v in danh_tinh.vai:
                if ten_cong_cu in self._vai_ghi.get(v, ()):
                    return True, "cho phép: vai %r có quyền GHI %r, cổng ghi đang mở" % (
                        v,
                        ten_cong_cu,
                    )
            # Nói rõ ca "có đọc mà không có ghi": đây là ca hay bị hiểu nhầm nhất.
            co_doc = [v for v in danh_tinh.vai if ten_cong_cu in self._vai_doc.get(v, ())]
            if co_doc:
                return False, (
                    "từ chối: vai %s chỉ có quyền ĐỌC, không có quyền GHI %r"
                    % (", ".join(co_doc), ten_cong_cu)
                )
            return False, (
                "từ chối: không vai nào trong %s được cấp quyền GHI %r%s"
                % (
                    ", ".join(danh_tinh.vai),
                    ten_cong_cu,
                    " (các vai %s chưa khai trong chính sách)" % ", ".join(vai_chua_khai)
                    if vai_chua_khai
                    else "",
                )
            )

        for v in danh_tinh.vai:
            if ten_cong_cu in self._vai_doc.get(v, ()):
                return True, "cho phép: vai %r có quyền ĐỌC %r" % (v, ten_cong_cu)
        return False, (
            "từ chối: không vai nào trong %s được cấp %r%s"
            % (
                ", ".join(danh_tinh.vai),
                ten_cong_cu,
                " (các vai %s chưa khai trong chính sách)" % ", ".join(vai_chua_khai)
                if vai_chua_khai
                else "",
            )
        )

    def cong_cu_duoc_phep(self, danh_tinh: Optional[DanhTinh]) -> List[str]:
        """Danh sách công cụ mà danh tính này gọi được NGAY BÂY GIỜ.

        "Ngay bây giờ" gồm cả trạng thái cổng ghi — nên khi cổng ghi đóng, công
        cụ ghi biến mất khỏi danh sách. `nhan/mcp.py` dùng hàm này cho
        `tools/list`, và đó là lý do nó phải tính đúng theo thời điểm hỏi chứ
        không phải theo cấu hình tĩnh.
        """
        if danh_tinh is None:
            return []
        return [t for t in sorted(self._cong_cu) if self.duoc_goi(danh_tinh, t)[0]]
