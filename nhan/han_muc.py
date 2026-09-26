#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/han_muc.py — GỌI BAO NHIÊU THÌ ĐỦ.

CỬA SỔ TRƯỢT, KHÔNG PHẢI "TỪ NỬA ĐÊM"
-------------------------------------
Cửa sổ theo lịch (mỗi ngày reset lúc 00:00, mỗi giờ reset lúc phút 0) có một lỗ
ai cũng biết mà vẫn hay dùng: dồn HAI ngày hạn mức vào một giờ quanh mốc reset.
Hạn mức 1.000 lượt/ngày thì 23:59 gọi 1.000 lượt, 00:01 gọi tiếp 1.000 lượt —
2.000 lượt trong hai phút, mà không dòng nhật ký nào báo vượt. Với một nhân điều
phối 18 nền tảng thì đó không phải chuyện lý thuyết: đúng cái giờ ấy là lúc các
việc theo lịch cùng chạy.

Ở đây mỗi lần gọi ghi lại MỘT MỐC THỜI GIAN. Khi kiểm, đếm số mốc nằm trong
`(bây_giờ − cửa_sổ, bây_giờ]`. Không có mốc reset nào để canh.

Giá phải trả, nói thẳng: bộ nhớ tỉ lệ với SỐ LƯỢT trong cửa sổ, không phải với
số người dùng. Hạn mức 10.000 lượt/giờ cho 100 danh tính là tối đa một triệu mốc
thời gian trong RAM. Với quy mô hiện tại của dự án (đo 26/09/2026: chưa có lượt
gọi thật nào qua nhân này) thì không thành vấn đề; với quy mô lớn thì thay
`KhoTrongBoNho` bằng kho ngoài — đó là lý do lớp `KhoHanMuc` tồn tại.

HAI VAI THÌ LẤY HẠN MỨC NÀO
---------------------------
Chọn: lấy hạn mức RỘNG NHẤT trong các vai, rồi VẪN phải qua hạn mức riêng của
công cụ (nếu có khai) — hai phép kiểm nối bằng VÀ.
Lý do chọn rộng nhất giữa các vai: vai là thứ được CẤP. Cấp thêm cho ai đó một
vai mà lại làm họ gọi được ÍT đi là hành vi bất ngờ, và người quản trị sẽ đi tìm
lỗi ở chỗ khác. Còn hạn mức theo công cụ thì đúng là trần tuyệt đối do người vận
hành đặt cho một nền tảng yếu — nó phải thắng.
Lựa chọn ngược lại (lấy chặt nhất) cũng bảo vệ được, nhưng đánh đổi sự bất ngờ
ấy; ghi ra đây để người sau đổi ý thì đổi có hiểu biết.

CÁI HẠN MỨC NÀY KHÔNG LÀM
-------------------------
Nó đếm LƯỢT GỌI. Nó không biết gì về token, về tiền, về dung lượng trả về. Một
lượt gọi kéo về 2 triệu bản ghi cũng chỉ là một lượt. Trần theo khối lượng là
việc của trình điều khiển và chưa được viết tính đến 26/09/2026.

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, Optional, Tuple

from .danh_tinh import DanhTinh


class LoiHanMuc(ValueError):
    pass


@dataclass(frozen=True)
class HanMuc:
    """so_lan lượt trong cua_so_giay giây."""

    so_lan: int
    cua_so_giay: float

    def __post_init__(self) -> None:
        if not isinstance(self.so_lan, int) or self.so_lan < 0:
            raise LoiHanMuc("so_lan phải là số nguyên không âm, nhận %r" % (self.so_lan,))
        if not isinstance(self.cua_so_giay, (int, float)) or self.cua_so_giay <= 0:
            raise LoiHanMuc("cua_so_giay phải > 0, nhận %r" % (self.cua_so_giay,))

    def mo_ta(self) -> str:
        return "%d lượt / %g giây" % (self.so_lan, self.cua_so_giay)


class KhoHanMuc:
    """Giao diện kho mốc thời gian.

    Tách ra thành lớp riêng để đổi sang kho ngoài (một CSDL khoá-giá trị chẳng
    hạn) mà không đụng vào `BoHanMuc`. Đây cũng là chỗ duy nhất trong nhân có
    trạng thái ghi được, nên khi nào cần chạy NHIỀU tiến trình nhân song song
    thì đúng một lớp này phải thay — nói trước để người sau không phải đi dò.

    ⚠ Bản trong bộ nhớ KHÔNG chia sẻ giữa các tiến trình. Chạy hai tiến trình
    nhân thì hạn mức thực tế gấp đôi. Đây là giới hạn ĐÃ BIẾT, không phải lỗi
    ẩn.
    """

    def ghi_nhan(self, khoa: str, thoi_diem: float) -> None:
        raise NotImplementedError

    def dem_tu(self, khoa: str, tu_thoi_diem: float) -> int:
        """Số mốc > tu_thoi_diem."""
        raise NotImplementedError

    def moc_cu_nhat_tu(self, khoa: str, tu_thoi_diem: float) -> Optional[float]:
        """Mốc cũ nhất còn nằm trong cửa sổ, để tính 'còn bao lâu nữa'."""
        raise NotImplementedError

    def don(self, khoa: str, truoc_thoi_diem: float) -> None:
        raise NotImplementedError


class KhoTrongBoNho(KhoHanMuc):
    """Kho mặc định: một deque mốc thời gian cho mỗi khoá.

    deque vì phép dọn luôn là bỏ từ ĐẦU (mốc cũ nhất): `popleft` là O(1), còn
    `list.pop(0)` là O(n) và với cửa sổ vài nghìn lượt thì nó biến phép dọn
    thành phép tốn kém nhất trong cả đường gọi.
    """

    def __init__(self) -> None:
        self._moc: Dict[str, Deque[float]] = {}

    def ghi_nhan(self, khoa: str, thoi_diem: float) -> None:
        self._moc.setdefault(khoa, deque()).append(thoi_diem)

    def _don_noi_bo(self, khoa: str, truoc_thoi_diem: float) -> Deque[float]:
        hang = self._moc.get(khoa)
        if hang is None:
            return deque()
        while hang and hang[0] <= truoc_thoi_diem:
            hang.popleft()
        if not hang:
            # Xoá hẳn khoá rỗng. Không làm thì bảng phình theo TỔNG SỐ danh tính
            # từng gọi, mãi mãi — một rò rỉ bộ nhớ chậm, đúng kiểu chỉ lộ ra sau
            # vài tháng chạy liên tục.
            self._moc.pop(khoa, None)
        return hang

    def don(self, khoa: str, truoc_thoi_diem: float) -> None:
        self._don_noi_bo(khoa, truoc_thoi_diem)

    def dem_tu(self, khoa: str, tu_thoi_diem: float) -> int:
        return len(self._don_noi_bo(khoa, tu_thoi_diem))

    def moc_cu_nhat_tu(self, khoa: str, tu_thoi_diem: float) -> Optional[float]:
        hang = self._don_noi_bo(khoa, tu_thoi_diem)
        return hang[0] if hang else None

    def so_khoa(self) -> int:
        return len(self._moc)


class BoHanMuc:
    """Hạn mức theo vai và theo công cụ, cửa sổ trượt."""

    def __init__(
        self,
        mac_dinh: HanMuc,
        kho: Optional[KhoHanMuc] = None,
        dong_ho: Callable[[], float] = time.monotonic,
    ) -> None:
        # dong_ho mặc định là monotonic, KHÔNG phải time.time(). Lý do: hạn mức
        # đo KHOẢNG CÁCH thời gian. `time.time()` nhảy khi máy đồng bộ NTP hoặc
        # đổi giờ; nhảy lùi một giây thì cửa sổ trượt tính sai, nhảy lùi một giờ
        # thì mọi hạn mức mở toang. monotonic không nhảy.
        # Nhật ký thì ngược lại, cần giờ thật — nên nó có đồng hồ riêng.
        self.mac_dinh = mac_dinh
        self._kho = kho if kho is not None else KhoTrongBoNho()
        self._dong_ho = dong_ho
        self._theo_vai: Dict[str, HanMuc] = {}
        self._theo_cong_cu: Dict[str, HanMuc] = {}

    def dat_han_muc_vai(self, ten_vai: str, han_muc: HanMuc) -> None:
        self._theo_vai[ten_vai] = han_muc

    def dat_han_muc_cong_cu(self, ten_cong_cu: str, han_muc: HanMuc) -> None:
        self._theo_cong_cu[ten_cong_cu] = han_muc

    # -- nội bộ ---------------------------------------------------------------

    def _han_muc_vai(self, danh_tinh: DanhTinh) -> Tuple[HanMuc, str]:
        """Rộng nhất trong các vai; không vai nào khai thì lấy mặc định."""
        tot_nhat: Optional[HanMuc] = None
        vai_tot_nhat = ""
        for v in danh_tinh.vai:
            hm = self._theo_vai.get(v)
            if hm is None:
                continue
            # "Rộng hơn" so theo TỐC ĐỘ cho phép (lượt trên giây), không so theo
            # so_lan. 100 lượt/giờ hẹp hơn 10 lượt/phút, mà so_lan thì ngược lại.
            if tot_nhat is None or (
                hm.so_lan / hm.cua_so_giay > tot_nhat.so_lan / tot_nhat.cua_so_giay
            ):
                tot_nhat = hm
                vai_tot_nhat = v
        if tot_nhat is None:
            return self.mac_dinh, "mặc định"
        return tot_nhat, "vai %r" % vai_tot_nhat

    def _kiem_mot_o(
        self, khoa: str, han_muc: HanMuc, nhan_o: str, bay_gio: float
    ) -> Tuple[bool, str]:
        if han_muc.so_lan == 0:
            return False, "vượt hạn mức (%s): hạn mức là 0 lượt" % nhan_o
        bien = bay_gio - han_muc.cua_so_giay
        da_dung = self._kho.dem_tu(khoa, bien)
        if da_dung < han_muc.so_lan:
            return True, "trong hạn mức (%s): %d/%d trong %g giây" % (
                nhan_o,
                da_dung + 1,
                han_muc.so_lan,
                han_muc.cua_so_giay,
            )
        cu_nhat = self._kho.moc_cu_nhat_tu(khoa, bien)
        cho = (cu_nhat + han_muc.cua_so_giay - bay_gio) if cu_nhat is not None else han_muc.cua_so_giay
        return False, (
            "vượt hạn mức (%s): đã dùng %d/%d trong %g giây; còn %.1f giây nữa "
            "mới gọi được" % (nhan_o, da_dung, han_muc.so_lan, han_muc.cua_so_giay, max(cho, 0.0))
        )

    # -- API ------------------------------------------------------------------

    def kiem(self, danh_tinh: DanhTinh, ten_cong_cu: str) -> Tuple[bool, str]:
        """Kiểm mà KHÔNG ghi nhận. Dùng để xem trước, không dùng trong đường gọi."""
        return self._kiem(danh_tinh, ten_cong_cu, ghi_nhan=False)

    def kiem_va_ghi(self, danh_tinh: DanhTinh, ten_cong_cu: str) -> Tuple[bool, str]:
        """Kiểm, và nếu qua thì ghi nhận lượt này.

        CHỈ ghi nhận khi QUA. Lượt bị từ chối không tính vào hạn mức — nếu tính,
        một người dùng đã vượt hạn mức sẽ tự kéo dài thời gian bị khoá của mình
        mỗi lần thử lại, và tệ hơn: một bên thứ ba biết mã danh tính có thể bắn
        lời gọi hỏng để khoá người khác. Từ chối vì hạn mức vẫn ĐƯỢC GHI NHẬT KÝ
        — đó mới là chỗ phát hiện ai đang đập cửa.
        """
        return self._kiem(danh_tinh, ten_cong_cu, ghi_nhan=True)

    def _kiem(
        self, danh_tinh: DanhTinh, ten_cong_cu: str, ghi_nhan: bool
    ) -> Tuple[bool, str]:
        if danh_tinh is None:
            return False, "từ chối: không có danh tính"
        bay_gio = self._dong_ho()

        han_muc_vai, nhan_vai = self._han_muc_vai(danh_tinh)
        khoa_vai = "dt:%s" % danh_tinh.ma
        qua, ly_do_vai = self._kiem_mot_o(khoa_vai, han_muc_vai, nhan_vai, bay_gio)
        if not qua:
            return False, ly_do_vai

        han_muc_cc = self._theo_cong_cu.get(ten_cong_cu)
        ly_do_cc = ""
        khoa_cc = "dt:%s|cc:%s" % (danh_tinh.ma, ten_cong_cu)
        if han_muc_cc is not None:
            qua, ly_do_cc = self._kiem_mot_o(
                khoa_cc, han_muc_cc, "công cụ %r" % ten_cong_cu, bay_gio
            )
            if not qua:
                # KHÔNG ghi nhận vào ô vai khi ô công cụ chặn. Ghi vào một ô rồi
                # từ chối ở ô sau là tính phí một lượt chưa hề chạy.
                return False, ly_do_cc

        if ghi_nhan:
            self._kho.ghi_nhan(khoa_vai, bay_gio)
            if han_muc_cc is not None:
                self._kho.ghi_nhan(khoa_cc, bay_gio)

        return True, ly_do_vai + ("; " + ly_do_cc if ly_do_cc else "")
