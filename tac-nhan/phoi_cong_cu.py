#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phoi_cong_cu.py — PHƠI BÀY DẦN công cụ cho mô hình.

=============================================================================
VÌ SAO TỆP NÀY TỒN TẠI — RÀNG BUỘC NẶNG NHẤT CỦA CẢ KIẾN TRÚC
=============================================================================
Độ chính xác gọi công cụ TỤT THEO SỐ CÔNG CỤ ĐƯỢC PHƠI RA CÙNG LÚC: khoảng
95% với 3 công cụ, còn khoảng 70% với 12. Đó không phải chi tiết kỹ thuật phụ
— một hệ điều hành sống bằng gọi công cụ, nên đây là ràng buộc quyết định.

BDSG có MƯỜI TÁM nền tảng. Phơi hết công cụ của mười tám nền tảng ra một lúc
là tự đẩy mô hình xuống vùng 70%, và 30% còn lại không phải "trả lời hơi sai"
mà là GỌI NHẦM CÔNG CỤ — tức làm nhầm việc trên hệ thống thật.

Cách giải ở đây: mô hình KHÔNG bao giờ nhìn thấy quá `tran` công cụ. Nó thấy
một nhúm công cụ luôn-bật, cộng với DANH MỤC LĨNH VỰC và một công cụ meta để
MỞ một lĩnh vực khi cần. Mở lĩnh vực mới thì lĩnh vực cũ đóng lại nếu vượt trần.

=============================================================================
BA ĐIỀU ĐÃ CHỐT, ghi ra để người sau không "sửa" nhầm
=============================================================================
1. LĨNH VỰC SUY RA TỪ TIỀN TỐ TÊN CÔNG CỤ, không phải một bảng cấu hình riêng.
   `nhan/quyen.py` đã buộc tên công cụ có dạng `<trình_điều_khiển>.<công_cụ>`,
   nên tiền tố ấy LÀ lĩnh vực. Một bảng riêng sẽ trôi khỏi thực tế và không ai
   biết, vì không có gì bắt hai bên khớp nhau.

2. TRẦN ÁP LÊN THỨ MÔ HÌNH NHÌN THẤY, KHÔNG PHẢI THỨ NÓ ĐƯỢC PHÉP GỌI.
   Quyền vẫn do `nhan/quyen.py` quyết. Tệp này chỉ quyết CHO XEM GÌ. Trộn hai
   việc là biến một ràng buộc về độ chính xác thành một lỗ bảo mật: một công cụ
   bị ẩn KHÔNG có nghĩa là nó bị cấm.

3. CÔNG CỤ META LUÔN CÓ MẶT và KHÔNG tính vào trần. Nếu nó bị đẩy ra ngoài trần
   thì mô hình mất đường mở lĩnh vực và kẹt vĩnh viễn — hỏng theo kiểu im lặng.
"""
from typing import Any, Dict, List, Optional, Sequence

TEN_CONG_CU_META = "he.mo_linh_vuc"
TRAN_MAC_DINH = 8


class LoiPhoiCongCu(RuntimeError):
    """Cấu hình phơi bày sai — nổ lúc dựng, không nổ giữa một phiên đang chạy."""


def linh_vuc_cua(ten_cong_cu: str) -> str:
    """Lĩnh vực = phần trước dấu chấm đầu tiên.

    `nhan/quyen.py` đã ép mọi tên công cụ về dạng `<trình>.<công cụ>`, nên phép
    tách này luôn có kết quả. Tên không có dấu chấm thì lĩnh vực là chính nó —
    không nổ, vì tệp này không phải chỗ kiểm tính hợp lệ của tên.
    """
    if "." not in ten_cong_cu:
        return ten_cong_cu
    return ten_cong_cu.split(".", 1)[0]


class BoPhoiCongCu:
    """Quyết định mô hình NHÌN THẤY công cụ nào ở lượt này."""

    def __init__(
        self,
        ban_khai: Sequence[Dict[str, Any]],
        luon_bat: Sequence[str] = (),
        tran: int = TRAN_MAC_DINH,
    ) -> None:
        if tran < 1:
            raise LoiPhoiCongCu("trần phải ≥ 1, nhận %r" % (tran,))
        self._theo_ten = {b["ten"]: b for b in ban_khai}
        if len(self._theo_ten) != len(list(ban_khai)):
            raise LoiPhoiCongCu(
                "bản khai có tên trùng — hai công cụ cùng tên thì mô hình gọi "
                "cái nào là chuyện may rủi"
            )
        for t in luon_bat:
            if t not in self._theo_ten:
                raise LoiPhoiCongCu(
                    "công cụ luôn-bật %r không có trong bản khai. Công cụ đã khai: %s"
                    % (t, ", ".join(sorted(self._theo_ten)) or "(không có cái nào)")
                )
        if len(luon_bat) > tran:
            raise LoiPhoiCongCu(
                "có %d công cụ luôn-bật nhưng trần là %d — trần sẽ không bao giờ "
                "đủ chỗ cho một lĩnh vực nào" % (len(luon_bat), tran)
            )
        self._luon_bat = list(luon_bat)
        self._tran = tran
        self._dang_mo: List[str] = []   # lĩnh vực đang mở, cũ nhất đứng trước

    # -- tra cứu -------------------------------------------------------------

    @property
    def tran(self) -> int:
        return self._tran

    def cac_linh_vuc(self) -> List[str]:
        return sorted({linh_vuc_cua(t) for t in self._theo_ten})

    def linh_vuc_dang_mo(self) -> List[str]:
        return list(self._dang_mo)

    def ban_khai_goc(self, ten: str) -> Optional[Dict[str, Any]]:
        """Tra bản khai ĐẦY ĐỦ, kể cả công cụ đang bị ẩn.

        Cần có lối này vì ẨN ≠ CẤM. Một công cụ GHI đang bị ẩn vẫn là công cụ
        GHI, và mọi phép kiểm về tính chất của nó phải hỏi bản khai gốc chứ
        không hỏi danh sách đang phơi — hỏi nhầm chỗ thì cổng xác nhận hành
        động không-lùi-được sẽ im lặng bị đi vòng.
        """
        b = self._theo_ten.get(ten)
        return dict(b) if b else None

    def cong_cu_cua_linh_vuc(self, lv: str) -> List[str]:
        return sorted(t for t in self._theo_ten if linh_vuc_cua(t) == lv)

    # -- mở / đóng -----------------------------------------------------------

    def mo_linh_vuc(self, lv: str) -> str:
        """Mở một lĩnh vực. Trả về câu mô tả việc đã làm, để đưa lại cho mô hình.

        Vượt trần thì ĐÓNG lĩnh vực mở lâu nhất. Nói ra việc đóng ấy là bắt buộc:
        mô hình vừa thấy một công cụ biến mất mà không hiểu vì sao thì nó sẽ gọi
        lại đúng cái vừa mất.
        """
        co = self.cac_linh_vuc()
        if lv not in co:
            raise KeyError(
                "không có lĩnh vực %r. Các lĩnh vực có thật: %s" % (lv, ", ".join(co))
            )
        if lv in self._dang_mo:
            return "lĩnh vực %r vốn đã mở" % (lv,)
        self._dang_mo.append(lv)
        da_dong = []
        while self._dem_phoi() > self._tran and len(self._dang_mo) > 1:
            da_dong.append(self._dang_mo.pop(0))
        if da_dong:
            return "đã mở %r; đóng %s để giữ trần %d công cụ" % (
                lv, ", ".join(repr(x) for x in da_dong), self._tran)
        return "đã mở %r" % (lv,)

    def dong_tat(self) -> None:
        self._dang_mo = []

    # -- thứ mô hình nhìn thấy ------------------------------------------------

    def _ten_dang_phoi(self) -> List[str]:
        ten = list(self._luon_bat)
        for lv in self._dang_mo:
            for t in self.cong_cu_cua_linh_vuc(lv):
                if t not in ten:
                    ten.append(t)
        return ten

    def _dem_phoi(self) -> int:
        return len(self._ten_dang_phoi())

    def so_cong_cu_phoi(self) -> int:
        """Số công cụ THẬT đang phơi — KHÔNG tính công cụ meta.

        Meta không tính vào trần (quyết định 3 ở đầu tệp), nên phép đo trần phải
        loại nó ra, nếu không phép kiểm trần sẽ đo nhầm một con số khác.
        """
        return self._dem_phoi()

    def ban_khai_cho_mo_hinh(self) -> List[Dict[str, Any]]:
        """Danh sách công cụ đưa cho mô hình ở lượt này, kèm công cụ meta."""
        ra = [dict(self._theo_ten[t]) for t in self._ten_dang_phoi()]
        con_lai = [lv for lv in self.cac_linh_vuc() if lv not in self._dang_mo]
        ra.append({
            "ten": TEN_CONG_CU_META,
            "mo_ta": (
                "Mở một lĩnh vực để thấy công cụ của nó. Dùng khi việc cần làm "
                "không nằm trong danh sách công cụ hiện có. Lĩnh vực chưa mở: "
                + (", ".join(con_lai) if con_lai else "(đã mở hết)")
            ),
            "luoc_do": {
                "loai": "object",
                "thuoc_tinh": {"linh_vuc": {"loai": "string", "chon": con_lai}},
                "bat_buoc": ["linh_vuc"],
            },
            "ghi": False,
        })
        return ra
