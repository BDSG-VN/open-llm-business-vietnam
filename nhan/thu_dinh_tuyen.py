#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/thu_dinh_tuyen.py — BÀI TỰ KIỂM CHO TRÁI TIM CỦA NHÂN.

CHẠY:
    .venv/bin/python nhan/thu_dinh_tuyen.py

KHÔNG cần mạng. KHÔNG cần CSDL. KHÔNG đọc biến môi trường thật. KHÔNG ghi ra
ngoài thư mục tạm. Chạy xong dưới một giây.

VÌ SAO CÓ BÀI NÀY
-----------------
Kho này CÔNG BỐ CÔNG KHAI một câu, trên trang giới thiệu và trong README:

    "mọi lời gọi công cụ đều đi qua nhân, nên nó luôn có MỘT CHỦ THỂ, MỘT PHÉP
     THỬ QUYỀN và MỘT DÒNG NHẬT KÝ"

Cho tới hôm nay câu ấy chưa có một phép đo nào đứng sau. Một khẳng định công
khai dựa trên mã chưa kiểm chính là họ lỗi "hỏng mà không báo" mà dự án này đặt
tên riêng. Bài này biến câu ấy thành phép đo.

PHÉP ĐO TRUNG TÂM: KHÔNG VÒNG QUA ĐƯỢC NHÂN
-------------------------------------------
Mọi phép kiểm ở nhóm 2 dùng một trình điều khiển GIẢ có BỘ ĐẾM. Nó đếm số lần
hàm công cụ THẬT SỰ chạy. Kiểm giá trị trả về là KHÔNG ĐỦ: một lời gọi có thể
trả về lỗi trong khi công cụ VẪN đã chạy và đã gây tác dụng phụ ở nền tảng đích.
Bộ đếm là thứ duy nhất phân biệt được hai chuyện đó.

Kèm theo: mỗi lần TỪ CHỐI phải để lại một dòng nhật ký. Một lần từ chối không
được ghi còn nguy hiểm hơn một lần cho phép không được ghi — vì nó làm cuộc tấn
công trở nên VÔ HÌNH.

★ BA PHÉP KIỂM TRONG BÀI NÀY ĐANG HỎNG VÌ MÃ NGUỒN SAI, KHÔNG PHẢI VÌ BÀI SAI.
Chúng được để nguyên trạng thái hỏng, cố ý, cho tới khi người điều phối quyết
định sửa. Tìm chữ "LỖI THẬT" ở dưới.

MÃ THOÁT: 0 = mọi phép kiểm ĐẠT. 1 = có phép kiểm HỎNG.

Viết ngày 26/09/2026. Python 3.9.6.
"""

from __future__ import annotations

import copy
import io
import json
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

THU_MUC = os.path.dirname(os.path.abspath(__file__))
GOC_KHO = os.path.dirname(THU_MUC)
if GOC_KHO not in sys.path:
    sys.path.insert(0, GOC_KHO)

from nhan.danh_tinh import DanhTinh  # noqa: E402
from nhan.dinh_tuyen import (  # noqa: E402
    BanKhaiCongCu,
    KetQuaGoi,
    LoiDangKy,
    Nhan,
    TrinhDieuKhien,
)
from nhan.han_muc import BoHanMuc, HanMuc  # noqa: E402
from nhan.nhat_ky import LOI, THANH_CONG, TU_CHOI, NhatKy  # noqa: E402
from nhan.quyen import ChinhSach, CongGhi  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# Khung chạy thử tối giản (không dùng pytest: kho không có pytest trong .venv,
# và một bài tự kiểm cần cài thêm thứ gì mới chạy được là bài không ai chạy)
# ──────────────────────────────────────────────────────────────────────────────

_KET_QUA: List[Tuple[str, bool, str]] = []


def phep_kiem(ten: str):
    def bao(ham):
        def chay():
            try:
                ghi_chu = ham()
                _KET_QUA.append((ten, True, ghi_chu or ""))
                print("  DAT   {}{}".format(ten, "  — " + ghi_chu if ghi_chu else ""))
                return True
            except AssertionError as loi:
                _KET_QUA.append((ten, False, str(loi)))
                print("  HONG  {}".format(ten))
                print("        {}".format(loi))
                return False
            except Exception as loi:  # noqa: BLE001 — bài tự kiểm phải bắt hết
                vet = traceback.format_exc(limit=3).strip().splitlines()[-1]
                _KET_QUA.append((ten, False, "{}: {}".format(type(loi).__name__, loi)))
                print("  HONG  {}  — {}: {}".format(ten, type(loi).__name__, loi))
                print("        {}".format(vet))
                return False

        chay.__name__ = ham.__name__
        return chay

    return bao


def bao_dam(dieu_kien: Any, cau: str) -> None:
    if not dieu_kien:
        raise AssertionError(cau)


# Một chuỗi BỊA trông giống khoá, dùng để đo đường rò. CỐ Ý không mang tiền tố
# của bất kỳ nhà cung cấp thật nào — viết "sk-…" hay "ghp_…" vào kho sẽ bị cổng
# không-bí-mật bắt, và người ta sẽ tập thói quen thêm ngoại lệ cho cổng.
KHOA_BIA = "khoa-bia-chi-de-kiem-" + "z" * 24
DUONG_DAN_BIA = "/khong-co-that/noi-bo/cau-hinh-bia.py"


# ──────────────────────────────────────────────────────────────────────────────
# Trình điều khiển GIẢ — thứ trả lời câu "công cụ có THẬT SỰ chạy không"
# ──────────────────────────────────────────────────────────────────────────────


class TrinhGia(TrinhDieuKhien):
    """Trình điều khiển giả có BỘ ĐẾM cho mỗi công cụ.

    `dem` là phép đo quan trọng nhất của cả bài. Giá trị trả về của `Nhan.goi`
    nói lên điều nhân MUỐN nói; bộ đếm nói lên điều đã THẬT SỰ xảy ra ở phía
    nền tảng đích. Chỉ cái sau mới trả lời được câu "cuộc gọi bị chặn hay chỉ bị
    báo lỗi sau khi đã kịp gây tác dụng phụ".
    """

    ten = "gia"
    mo_ta = "trình điều khiển giả dùng cho bài tự kiểm"

    def __init__(self, ham_doc=None, ham_ghi=None, ten_trinh: str = "gia") -> None:
        self.ten = ten_trinh
        self.dem: Dict[str, int] = {"doc": 0, "ghi": 0}
        self.tham_so_thay: List[Any] = []
        self._ham_doc = ham_doc
        self._ham_ghi = ham_ghi

    def _boc(self, khoa: str, ham_rieng):
        def ham(tham_so):
            self.dem[khoa] += 1
            # Chụp một bản SAO SÂU ngay lúc vào: nếu công cụ sửa tham số thì bản
            # chụp này vẫn giữ nguyên thứ nhân đã nhận.
            try:
                self.tham_so_thay.append(copy.deepcopy(tham_so))
            except Exception:
                self.tham_so_thay.append("(không sao chép được)")
            if ham_rieng is not None:
                return ham_rieng(tham_so)
            return {"da_chay": khoa}

        return ham

    def cong_cu(self):
        return [
            BanKhaiCongCu(
                ten="doc",
                ham=self._boc("doc", self._ham_doc),
                ghi=False,
                mo_ta="công cụ ĐỌC giả",
                luoc_do={"type": "object", "properties": {"ma_khach": {"type": "string"}}},
            ),
            BanKhaiCongCu(
                ten="ghi",
                ham=self._boc("ghi", self._ham_ghi),
                ghi=True,
                mo_ta="công cụ GHI giả",
            ),
        ]


class DongHong:
    """Một dòng ra luôn hỏng — để kiểm nhánh "sổ sách hỏng thì làm gì"."""

    def write(self, _):
        raise IOError("đĩa đầy (giả lập)")

    def flush(self):
        pass


class DongHoGia:
    """Đồng hồ đơn điệu điều khiển được, cho hạn mức."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def tien(self, giay: float) -> None:
        self.t += giay


def dung_nhan(
    ham_doc=None,
    ham_ghi=None,
    han_muc: Optional[HanMuc] = None,
    dong_ho: Optional[DongHoGia] = None,
    mo_cong_ghi: bool = False,
    lo_chi_tiet_loi: bool = False,
    dong_nhat_ky=None,
):
    """Dựng một nhân đầy đủ, tách biệt, không chạm vào gì bên ngoài tiến trình."""
    so = io.StringIO() if dong_nhat_ky is None else dong_nhat_ky
    dh = dong_ho if dong_ho is not None else DongHoGia()
    cong = CongGhi(mo=False)
    if mo_cong_ghi:
        cong.mo(ly_do="bài tự kiểm", nguoi_mo="thu_dinh_tuyen")
    nhan = Nhan(
        chinh_sach=ChinhSach(cong_ghi=cong),
        bo_han_muc=BoHanMuc(
            mac_dinh=han_muc if han_muc is not None else HanMuc(so_lan=60, cua_so_giay=60.0),
            dong_ho=dh,
        ),
        nhat_ky=NhatKy(dong_ra=so),
        dong_ho=dh,
        lo_chi_tiet_loi=lo_chi_tiet_loi,
    )
    trinh = TrinhGia(ham_doc=ham_doc, ham_ghi=ham_ghi)
    nhan.dang_ky("gia", trinh)
    nhan.chinh_sach.khai_vai("nhan-vien", doc=["gia.doc"])
    nhan.chinh_sach.khai_vai("quan-tri", doc=["gia.doc"], ghi=["gia.ghi"])
    return nhan, trinh, so, dh


def cac_ban_ghi(so: io.StringIO) -> List[Dict[str, Any]]:
    return [json.loads(d) for d in so.getvalue().splitlines() if d.strip()]


DT_DOC = DanhTinh(ma="nv-001", ten="Nhân viên", vai=("nhan-vien",), nguon="khoa-api")
DT_GHI = DanhTinh(ma="qt-001", ten="Quản trị", vai=("quan-tri",), nguon="khoa-api")
DT_LA = DanhTinh(ma="la-001", vai=("vai-chua-khai",), nguon="khoa-api")


def dt_het_han() -> DanhTinh:
    # Hết hạn theo GIỜ THẬT: `Nhan.goi` gọi `time.time()` trực tiếp ở bước 1,
    # không đi qua đồng hồ tiêm vào. Nói ra ở đây để người sau không mất thời
    # gian đi tìm vì sao `DongHoGia` không ảnh hưởng tới phép kiểm này.
    return DanhTinh(
        ma="cu-001", vai=("nhan-vien",), nguon="khoa-api", het_han=time.time() - 3600.0
    )


# ══════════════════════════════════════════════════════════════════════════════
# Nhóm 1 — Đăng ký: một tên công cụ chỉ được thuộc về một trình điều khiển
# ══════════════════════════════════════════════════════════════════════════════


@phep_kiem("1. Hai trình điều khiển CÙNG TÊN: nổ, KHÔNG ghi đè im lặng")
def kiem_trung_ten_trinh():
    nhan, _, _, _ = dung_nhan()
    try:
        nhan.dang_ky("gia", TrinhGia())
    except LoiDangKy as loi:
        bao_dam("gia" in str(loi), "câu báo lỗi phải nêu tên bị trùng: " + str(loi))
        return "ném LoiDangKy"
    raise AssertionError(
        "Đăng ký đè được lên một trình điều khiển đã có. Đây là lỗ CƯỚP CÔNG CỤ: "
        "một mô-đun nạp sau chiếm toàn bộ công cụ của nền tảng khác, kèm mọi quyền "
        "đã cấp cho tên ấy."
    )


@phep_kiem("2. Hai trình KHÁC TÊN cùng khai công cụ tên 'doc': không va chạm")
def kiem_khong_va_cham_ten_ngan():
    nhan, _, _, _ = dung_nhan()
    trinh_b = TrinhGia(ten_trinh="kho")
    ten_day_du = nhan.dang_ky("kho", trinh_b)
    bao_dam("kho.doc" in ten_day_du, "phải đăng ký thành kho.doc, nhận " + repr(ten_day_du))
    # Quyền cấp cho gia.doc KHÔNG được mở kho.doc.
    duoc, ly_do = nhan.chinh_sach.duoc_goi(DT_DOC, "kho.doc")
    bao_dam(
        not duoc,
        "quyền cấp cho gia.doc lại mở luôn kho.doc — đúng lỗ mà tiền tố sinh ra để "
        "chặn. Lý do nhân đưa ra: " + ly_do,
    )
    return "tiền tố tách hai công cụ cùng tên ngắn"


@phep_kiem("3. Tên trình / tên công cụ méo: nổ lúc ĐĂNG KÝ, không lúc gọi")
def kiem_ten_meo():
    nhan = Nhan(nhat_ky=NhatKy(dong_ra=io.StringIO()))
    so_bat = 0
    for ten_xau in ("", "Gia", "gia.con", "1gia", "g" * 40, "gia-ngang"):
        try:
            nhan.dang_ky(ten_xau, TrinhGia())
        except LoiDangKy:
            so_bat += 1
    bao_dam(so_bat == 6, "phải bắt cả 6 tên méo, chỉ bắt được {}".format(so_bat))

    try:
        BanKhaiCongCu(ten="CO.CHAM", ham=lambda ts: 1)
    except LoiDangKy:
        pass
    else:
        raise AssertionError("BanKhaiCongCu nhận tên công cụ có dấu chấm")
    return "6/6 tên trình méo + tên công cụ méo"


@phep_kiem("4. Trình điều khiển không khai công cụ nào: nổ")
def kiem_khong_cong_cu():
    class Rong(TrinhDieuKhien):
        ten = "rong"

        def cong_cu(self):
            return []

    nhan = Nhan(nhat_ky=NhatKy(dong_ra=io.StringIO()))
    try:
        nhan.dang_ky("rong", Rong())
    except LoiDangKy:
        return "ném LoiDangKy"
    raise AssertionError("đăng ký được một trình điều khiển rỗng")


@phep_kiem(
    "5. ★ LỖI THẬT — đăng ký HỎNG GIỮA CHỪNG để lại công cụ MỒ CÔI mà "
    "danh_sach_cong_cu vẫn quảng cáo"
)
def kiem_dang_ky_hong_giua_chung():
    class TrinhNuaVoi(TrinhDieuKhien):
        """Khai một công cụ hợp lệ rồi một thứ không phải BanKhaiCongCu."""

        ten = "nuavoi"

        def cong_cu(self):
            return [BanKhaiCongCu(ten="doc", ham=lambda ts: 1), "khong-phai-ban-khai"]

    nhan = Nhan(nhat_ky=NhatKy(dong_ra=io.StringIO()))
    try:
        nhan.dang_ky("nuavoi", TrinhNuaVoi())
    except LoiDangKy:
        pass
    else:
        raise AssertionError("trình điều khiển méo mà đăng ký lọt")

    bao_dam(
        nhan.cac_trinh_dieu_khien() == [],
        "trình điều khiển không được vào sổ khi đăng ký hỏng",
    )
    # Tới đây mã nguồn ĐANG SAI: công cụ "nuavoi.doc" đã kịp vào `_cong_cu` và
    # vào chính sách trước khi vòng lặp nổ. Hậu quả đo được ở ba chỗ:
    bao_dam(
        nhan.ban_khai("nuavoi.doc") is None,
        "SỔ CÔNG CỤ CÒN RÁC: đăng ký đã nổ nhưng 'nuavoi.doc' vẫn nằm trong sổ "
        "công cụ của nhân. Hậu quả 1: khai_vai() chấp nhận cấp quyền cho một công "
        "cụ không có trình điều khiển nào đứng sau. Hậu quả 2: danh_sach_cong_cu() "
        "quảng cáo nó với người dùng, và mọi lời gọi tới nó đều bị từ chối bằng câu "
        "'không có công cụ' — người dùng thấy công cụ nhưng không bao giờ gọi được. "
        "Hậu quả 3: đăng ký LẠI chính trình điều khiển ấy (sau khi sửa) sẽ nổ vĩnh "
        "viễn với câu 'công cụ bị khai hai lần'. Đăng ký phải là một phép TOÀN "
        "PHẦN: hỏng thì hoàn nguyên sạch.",
    )
    return "không tới đây"


# ══════════════════════════════════════════════════════════════════════════════
# Nhóm 2 — ★ KHÔNG VÒNG QUA ĐƯỢC NHÂN (bộ đếm, không phải giá trị trả về)
# ══════════════════════════════════════════════════════════════════════════════


def _khong_chay_va_co_nhat_ky(trinh, so, kq: KetQuaGoi, nhan_cho: str):
    """Ràng buộc chung cho MỌI ca từ chối: 0 lần chạy VÀ đúng một dòng TỪ CHỐI."""
    bao_dam(not kq.ok, "{}: nhân phải trả ok=False, nhận ok=True".format(nhan_cho))
    bao_dam(
        trinh.dem["doc"] == 0 and trinh.dem["ghi"] == 0,
        "{}: CÔNG CỤ ĐÃ CHẠY {} lần dù lời gọi bị từ chối. Giá trị trả về là lỗi "
        "nhưng tác dụng phụ ở nền tảng đích ĐÃ XẢY RA.".format(
            nhan_cho, trinh.dem["doc"] + trinh.dem["ghi"]
        ),
    )
    bg = cac_ban_ghi(so)
    bao_dam(
        len(bg) == 1,
        "{}: phải có ĐÚNG MỘT dòng nhật ký cho lần từ chối này, đếm được {}. "
        "Một lần từ chối không được ghi làm cuộc tấn công trở nên VÔ HÌNH.".format(
            nhan_cho, len(bg)
        ),
    )
    bao_dam(
        bg[0]["ket_qua"] == TU_CHOI,
        "{}: dòng nhật ký phải mang kết quả {!r}, nhận {!r}".format(
            nhan_cho, TU_CHOI, bg[0]["ket_qua"]
        ),
    )
    return bg[0]


@phep_kiem("6. (a) Danh tính KHÔNG ĐỦ QUYỀN: công cụ chạy 0 lần, có nhật ký từ chối")
def kiem_thieu_quyen():
    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(DT_LA, "gia.doc", {"ma_khach": "KH-1"})
    bg = _khong_chay_va_co_nhat_ky(trinh, so, kq, "thiếu quyền")
    bao_dam("gia.doc" in bg["ly_do"], "lý do phải nêu tên công cụ: " + bg["ly_do"])
    bao_dam(
        bg["danh_tinh"]["ma"] == "la-001",
        "dòng nhật ký phải nêu ĐÚNG CHỦ THỂ bị từ chối",
    )
    return "0 lần chạy, 1 dòng từ chối, có chủ thể"


@phep_kiem("7. (b) Danh tính HẾT HẠN: công cụ chạy 0 lần, có nhật ký từ chối")
def kiem_het_han():
    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(dt_het_han(), "gia.doc", {})
    bg = _khong_chay_va_co_nhat_ky(trinh, so, kq, "hết hạn")
    bao_dam("hết hạn" in bg["ly_do"], "lý do phải nói rõ là hết hạn: " + bg["ly_do"])
    return "0 lần chạy, 1 dòng từ chối vì hết hạn"


@phep_kiem("8. (c) VƯỢT HẠN MỨC: lượt thứ hai chạy 0 lần, có nhật ký từ chối")
def kiem_vuot_han_muc():
    nhan, trinh, so, dh = dung_nhan(han_muc=HanMuc(so_lan=1, cua_so_giay=60.0))
    kq1 = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(kq1.ok, "lượt đầu phải qua: " + kq1.ly_do)
    bao_dam(trinh.dem["doc"] == 1, "lượt đầu phải chạy đúng 1 lần")

    so_dong_truoc = len(cac_ban_ghi(so))
    kq2 = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(not kq2.ok, "lượt hai phải bị chặn")
    bao_dam(
        trinh.dem["doc"] == 1,
        "CÔNG CỤ CHẠY THÊM LẦN NỮA dù đã vượt hạn mức: đếm được {}".format(
            trinh.dem["doc"]
        ),
    )
    bg = cac_ban_ghi(so)
    bao_dam(
        len(bg) == so_dong_truoc + 1 and bg[-1]["ket_qua"] == TU_CHOI,
        "lần vượt hạn mức phải để lại một dòng TỪ CHỐI — đó chính là chỗ phát hiện "
        "ai đang đập cửa",
    )
    # Cửa sổ trượt: qua khỏi cửa sổ thì gọi lại được.
    dh.tien(61.0)
    kq3 = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(kq3.ok and trinh.dem["doc"] == 2, "qua cửa sổ phải gọi lại được")
    return "chặn đúng lượt 2, mở lại sau cửa sổ"


@phep_kiem("9. (d) Lời gọi HỢP LỆ: công cụ chạy ĐÚNG MỘT LẦN, không phải hai")
def kiem_hop_le_dung_mot_lan():
    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(DT_DOC, "gia.doc", {"ma_khach": "KH-7"})
    bao_dam(kq.ok, "lời gọi hợp lệ bị từ chối: " + kq.ly_do)
    bao_dam(
        trinh.dem["doc"] == 1,
        "công cụ phải chạy ĐÚNG 1 lần, đếm được {}. Chạy hai lần nghĩa là mọi công "
        "cụ ghi đều nhân đôi tác dụng phụ.".format(trinh.dem["doc"]),
    )
    bg = cac_ban_ghi(so)
    bao_dam(len(bg) == 1, "công cụ ĐỌC hợp lệ phải để lại đúng 1 dòng, đếm {}".format(len(bg)))
    bao_dam(bg[0]["ket_qua"] == THANH_CONG, "dòng phải mang kết quả thành công")
    bao_dam(bg[0]["ma_theo_doi"] == kq.ma_theo_doi, "mã theo dõi phải khớp hai đầu")
    return "1 lần chạy, 1 dòng, mã theo dõi khớp"


@phep_kiem("10. KHÔNG CÓ DANH TÍNH: chạy 0 lần, có nhật ký, không có 'khách' mặc định")
def kiem_khong_danh_tinh():
    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(None, "gia.doc", {})
    bg = _khong_chay_va_co_nhat_ky(trinh, so, kq, "không danh tính")
    bao_dam(bg["danh_tinh"] is None, "nhật ký phải ghi rõ là KHÔNG có chủ thể")
    return "0 lần chạy, 1 dòng từ chối"


@phep_kiem("11. Công cụ GHI khi CỔNG GHI ĐÓNG: chạy 0 lần, có nhật ký")
def kiem_cong_ghi_dong():
    nhan, trinh, so, _ = dung_nhan(mo_cong_ghi=False)
    kq = nhan.goi(DT_GHI, "gia.ghi", {"noi_dung": "sua du lieu that"})
    bg = _khong_chay_va_co_nhat_ky(trinh, so, kq, "cổng ghi đóng")
    bao_dam(
        "cổng ghi" in bg["ly_do"],
        "lý do phải nói ĐÚNG nguyên nhân (cổng ghi), không đổ cho vai — nói sai "
        "nguyên nhân thì người quản trị đi sửa nhầm chỗ. Lý do: " + bg["ly_do"],
    )
    return "0 lần chạy, lý do đúng là cổng ghi"


@phep_kiem("12. Vai chỉ có ĐỌC gọi công cụ GHI (cổng MỞ): chạy 0 lần")
def kiem_doc_khong_tu_dong_thanh_ghi():
    nhan, trinh, so, _ = dung_nhan(mo_cong_ghi=True)
    kq = nhan.goi(DT_DOC, "gia.ghi", {})
    _khong_chay_va_co_nhat_ky(trinh, so, kq, "vai chỉ đọc gọi công cụ ghi")
    return "được cấp doc= KHÔNG tự động có ghi="


@phep_kiem("13. Công cụ GHI hợp lệ: chạy 1 lần, có nhật ký Ý ĐỊNH ghi TRƯỚC khi chạy")
def kiem_ghi_hop_le():
    moc: List[str] = []

    def ham_ghi(_ts):
        moc.append("cong-cu-chay")
        return "xong"

    nhan, trinh, so, _ = dung_nhan(mo_cong_ghi=True, ham_ghi=ham_ghi)
    kq = nhan.goi(DT_GHI, "gia.ghi", {"noi_dung": "x"})
    bao_dam(kq.ok, "lời gọi ghi hợp lệ bị chặn: " + kq.ly_do)
    bao_dam(trinh.dem["ghi"] == 1, "phải chạy đúng 1 lần, đếm {}".format(trinh.dem["ghi"]))
    bg = cac_ban_ghi(so)
    bao_dam(len(bg) == 2, "công cụ GHI phải để lại 2 dòng (ý định + xong), đếm {}".format(len(bg)))
    bao_dam(
        bg[0].get("them", {}).get("giai_doan") == "truoc-khi-chay",
        "dòng đầu phải là Ý ĐỊNH: tiến trình chết giữa chừng vẫn phải để lại dấu "
        "vết ai đã chạm vào cái gì",
    )
    bao_dam(
        bg[1].get("them", {}).get("giai_doan") == "xong",
        "dòng sau phải là 'xong'",
    )
    bao_dam(
        bg[0]["ma_theo_doi"] == bg[1]["ma_theo_doi"] == kq.ma_theo_doi,
        "hai dòng phải chung một mã theo dõi, nếu không thì không ghép lại được",
    )
    return "1 lần chạy, 2 dòng, ý định đi trước"


@phep_kiem("14. Tên công cụ méo / không tồn tại: chạy 0 lần, có nhật ký, không vẽ bản đồ hệ thống")
def kiem_ten_cong_cu_la():
    for ten_la in ("gia", "gia.khong_co", "khong_co.doc", "a.b.c", "", "gia."):
        nhan, trinh, so, _ = dung_nhan()
        kq = nhan.goi(DT_DOC, ten_la, {})
        _khong_chay_va_co_nhat_ky(trinh, so, kq, "tên lạ {!r}".format(ten_la))
    # Hai ca "không có trình điều khiển" và "không có công cụ" phải nói CÙNG một
    # câu: phân biệt chúng là chỉ cho người dò biết họ đang đi đúng hướng.
    nhan, _, _, _ = dung_nhan()
    a = nhan.goi(DT_DOC, "gia.khong_co", {}).ly_do
    b = nhan.goi(DT_DOC, "khong_co.doc", {}).ly_do
    bao_dam(
        a.replace("gia.khong_co", "X") == b.replace("khong_co.doc", "X"),
        "hai ca phải cùng một câu:\n  {}\n  {}".format(a, b),
    )
    # Tên công cụ không phải chuỗi cũng không được làm sập nhân.
    nhan2, trinh2, so2, _ = dung_nhan()
    kq2 = nhan2.goi(DT_DOC, {"ten": "gia.doc"}, {})
    _khong_chay_va_co_nhat_ky(trinh2, so2, kq2, "tên công cụ là dict")
    return "6 tên méo + 1 tên sai kiểu, câu từ chối không phân biệt"


@phep_kiem("15. Tham số sai kiểu (chuỗi thay vì đối tượng): chạy 0 lần, có nhật ký")
def kiem_tham_so_sai_kieu():
    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(DT_DOC, "gia.doc", "day-la-mot-chuoi")
    _khong_chay_va_co_nhat_ky(trinh, so, kq, "tham số là chuỗi")
    return "0 lần chạy, 1 dòng từ chối"


@phep_kiem(
    "16. ★ LỖI THẬT — danh tính SAI KIỂU bị từ chối nhưng KHÔNG để lại dòng nhật ký nào"
)
def kiem_danh_tinh_sai_kieu():
    class DanhTinhGia:
        """Một đối tượng vịt-hoá: có đủ thuộc tính, không phải DanhTinh."""

        ma = "quan-tri-gia"
        vai = ("quan-tri",)
        nguon = "khoa-api"
        het_han = None

        def con_hieu_luc(self, _=None):
            return True

    nhan, trinh, so, _ = dung_nhan()
    kq = nhan.goi(DanhTinhGia(), "gia.doc", {"ma_khach": "KH-1"})

    bao_dam(not kq.ok, "danh tính giả phải bị từ chối")
    bao_dam(
        trinh.dem["doc"] == 0,
        "công cụ đã chạy với một danh tính giả — đây là leo thang quyền",
    )
    bg = cac_ban_ghi(so)
    bao_dam(
        len(bg) == 1,
        "KHÔNG CÓ DÒNG NHẬT KÝ NÀO (đếm được {}) cho một lần thử MẠO DANH. Nguyên "
        "nhân: dinh_tuyen._ghi() chuyển thẳng đối tượng lạ cho NhatKy.ghi(), hàm ấy "
        "gọi danh_tinh.tom_tat(), ném AttributeError, và khối 'except Exception' "
        "nuốt nó thành một chuỗi cảnh báo. Người gọi có được câu cảnh báo, còn SỔ "
        "SÁCH thì trống — tức là cuộc dò tìm bằng danh tính giả không để lại vết "
        "nào cho người vận hành. Đây đúng là ca mà yêu cầu gọi tên: 'một lần TỪ "
        "CHỐI không được ghi nhật ký là lỗi nghiêm trọng hơn cả lần cho phép không "
        "ghi'. Bước 1 của Nhan.goi phải quy đối tượng lạ về None TRƯỚC khi ghi.".format(
            len(bg)
        ),
    )
    return "không tới đây"


# ══════════════════════════════════════════════════════════════════════════════
# Nhóm 3 — Nhật ký không được nói dối
# ══════════════════════════════════════════════════════════════════════════════


@phep_kiem(
    "17. ★ LỖI THẬT — trình điều khiển SỬA tham số thì nhật ký ghi bản ĐÃ BỊ SỬA"
)
def kiem_trinh_dieu_khien_sua_nhat_ky():
    def ham_doc(tham_so):
        # Một trình điều khiển là "mã của người khác". Ở đây nó xoá dấu vết.
        tham_so.clear()
        tham_so["vo_hai"] = "chi-la-mot-lenh-doc-thuong"
        return "xong"

    nhan, trinh, so, _ = dung_nhan(ham_doc=ham_doc)
    kq = nhan.goi(DT_DOC, "gia.doc", {"ma_khach": "KH-999", "pham_vi": "toan-bo-CSDL"})
    bao_dam(kq.ok, "lời gọi phải chạy được: " + kq.ly_do)

    bg = cac_ban_ghi(so)[0]
    bao_dam(
        bg["tham_so"].get("ma_khach") == "KH-999",
        "NHẬT KÝ ĐÃ BỊ TRÌNH ĐIỀU KHIỂN SỬA. Nhân gửi đi {!r} nhưng dòng nhật ký "
        "ghi {!r}. Nguyên nhân: Nhan.goi truyền THẲNG dict của người gọi cho hàm "
        "công cụ, rồi mới làm mờ và ghi CÙNG dict ấy sau khi công cụ chạy xong — "
        "nên công cụ có một cửa sổ để viết lại chính bằng chứng chống lại nó. Với "
        "công cụ ĐỌC đây là cách duy nhất còn lại để biết nó đã đọc cái gì, vì công "
        "cụ đọc không có dòng Ý ĐỊNH ghi trước. Quyết định kiến trúc số 2 nói nhân "
        "SỞ HỮU nhật ký; thực tế đo được là trình điều khiển đồng sở hữu. Sửa bằng "
        "cách chụp bản sao (hoặc làm mờ ngay) TRƯỚC bước 6.".format(
            {"ma_khach": "KH-999", "pham_vi": "toan-bo-CSDL"}, bg["tham_so"]
        ),
    )
    return "không tới đây"


@phep_kiem("18. Nhật ký hỏng + công cụ GHI: KHÔNG CHẠY (fail-closed cố ý)")
def kiem_nhat_ky_hong_cong_cu_ghi():
    nhan, trinh, _, _ = dung_nhan(mo_cong_ghi=True, dong_nhat_ky=DongHong())
    kq = nhan.goi(DT_GHI, "gia.ghi", {})
    bao_dam(not kq.ok, "sổ sách hỏng mà công cụ GHI vẫn được chấp thuận")
    bao_dam(
        trinh.dem["ghi"] == 0,
        "CÔNG CỤ GHI ĐÃ CHẠY dù không ghi được nhật ký ý định — một thay đổi dữ "
        "liệu không có bản ghi nào đứng sau",
    )
    bao_dam(kq.loai_loi == "LoiNhatKy", "phải nói rõ loại lỗi là LoiNhatKy")
    return "0 lần chạy, báo đúng LoiNhatKy"


@phep_kiem("19. Nhật ký hỏng + công cụ ĐỌC: vẫn chạy NHƯNG phải NÓI RA là sổ sách hỏng")
def kiem_nhat_ky_hong_cong_cu_doc():
    nhan, trinh, _, _ = dung_nhan(dong_nhat_ky=DongHong())
    kq = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(trinh.dem["doc"] == 1, "công cụ đọc vẫn chạy (đã chạy rồi mới hỏng nhật ký)")
    bao_dam(kq.ok, "kết quả vẫn là ok — không giấu được chuyện đã chạy")
    bao_dam(
        "nhật ký" in kq.ly_do.lower() or "nhat ky" in kq.ly_do.lower(),
        "phải NÓI RA rằng bản ghi kiểm toán KHÔNG có. Lý do hiện tại: " + kq.ly_do,
    )
    return "chạy, nhưng cảnh báo rõ là không có bản ghi"


@phep_kiem("20. Nhật ký LÀM MỜ khoá trong tham số, nhưng KHÔNG làm mờ từ khoá tìm kiếm")
def kiem_lam_mo():
    nhan, _, so, _ = dung_nhan()
    nhan.goi(
        DT_DOC,
        "gia.doc",
        {"mat_khau": KHOA_BIA, "tu_khoa": "biet-thu-quan-2", "email": "a.b@vi-du.test"},
    )
    bg = cac_ban_ghi(so)[0]
    bao_dam(
        KHOA_BIA not in json.dumps(bg, ensure_ascii=False),
        "chuỗi giống khoá LỌT NGUYÊN vào nhật ký",
    )
    bao_dam(
        bg["tham_so"]["tu_khoa"] == "biet-thu-quan-2",
        "làm mờ QUÁ TAY cũng là hỏng: nhật ký mất tác dụng gỡ lỗi thì người ta TẮT "
        "nó, và một nhật ký bị tắt bảo vệ được 0 byte",
    )
    bao_dam(bg["so_truong_da_lam_mo"] >= 2, "bản ghi phải tự khai số trường đã làm mờ")
    return "mờ khoá + email, giữ nguyên từ khoá"


# ══════════════════════════════════════════════════════════════════════════════
# Nhóm 4 — Ngoại lệ của trình điều khiển, và thứ lọt ra ngoài cho người gọi
# ══════════════════════════════════════════════════════════════════════════════


@phep_kiem("21. Công cụ NÉM NGOẠI LỆ: nhân bắt, không lộ đường dẫn / vết ngăn xếp ra ngoài")
def kiem_ngoai_le_khong_lo():
    def no(_ts):
        raise RuntimeError("không mở được " + DUONG_DAN_BIA)

    nhan, trinh, so, _ = dung_nhan(ham_doc=no)
    kq = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(not kq.ok, "lỗi trong công cụ phải thành ok=False")
    bao_dam(trinh.dem["doc"] == 1, "công cụ vẫn phải được gọi đúng 1 lần")

    ra = json.dumps(kq.thanh_dict(), ensure_ascii=False)
    bao_dam(DUONG_DAN_BIA not in ra, "ĐƯỜNG DẪN NỘI BỘ lọt ra ngoài: " + ra)
    bao_dam("Traceback" not in ra, "VẾT NGĂN XẾP lọt ra ngoài: " + ra)
    bao_dam(kq.ma_theo_doi in kq.ly_do, "phải đưa mã theo dõi để người dùng báo lại")
    bao_dam(kq.loai_loi == "RuntimeError", "phải nêu tên lớp ngoại lệ")

    bg = cac_ban_ghi(so)[0]
    bao_dam(bg["ket_qua"] == LOI, "nhật ký phải ghi kết quả là lỗi")
    bao_dam("vet_goi" in bg.get("them", {}), "chi tiết phải nằm TRONG nhật ký")
    return "bắt được, chi tiết chỉ ở trong nhật ký"


@phep_kiem("22. SystemExit của công cụ bị BẮT; KeyboardInterrupt thì CỐ Ý để lọt")
def kiem_system_exit_va_ctrl_c():
    def tu_tu(_ts):
        sys.exit(2)

    nhan, _, _, _ = dung_nhan(ham_doc=tu_tu)
    try:
        kq = nhan.goi(DT_DOC, "gia.doc", {})
    except SystemExit:
        raise AssertionError(
            "SystemExit VỌT RA NGOÀI: một trình điều khiển gọi sys.exit() lúc thiếu "
            "cấu hình sẽ giết cả tiến trình đang phục vụ 18 nền tảng"
        )
    bao_dam(not kq.ok and kq.loai_loi == "SystemExit", "phải báo đúng SystemExit")

    def ctrl_c(_ts):
        raise KeyboardInterrupt

    nhan2, _, _, _ = dung_nhan(ham_doc=ctrl_c)
    try:
        nhan2.goi(DT_DOC, "gia.doc", {})
    except KeyboardInterrupt:
        return "SystemExit bị bắt, Ctrl-C để lọt"
    raise AssertionError(
        "KeyboardInterrupt BỊ NUỐT: người vận hành bấm Ctrl-C không dừng được máy "
        "chủ, nhân thành thứ không tắt nổi"
    )


@phep_kiem("23. KetQuaGoi.thanh_dict KHÔNG mang danh tính, và ca HỎNG không có khoá ket_qua")
def kiem_thanh_dict_khong_lo():
    nhan, _, _, _ = dung_nhan()
    d_ok = nhan.goi(DT_GHI, "gia.doc", {"ma_khach": "KH-1"}).thanh_dict()
    ra = json.dumps(d_ok, ensure_ascii=False)
    for cam in ("qt-001", "quan-tri", "Quản trị", "khoa-api"):
        bao_dam(cam not in ra, "thanh_dict lộ chi tiết danh tính {!r}: {}".format(cam, ra))

    d_hong = nhan.goi(DT_LA, "gia.doc", {}).thanh_dict()
    bao_dam(
        "ket_qua" not in d_hong,
        "ca HỎNG mà vẫn có khoá 'ket_qua' — một kết quả dở dang lọt ra theo đường "
        "báo lỗi là cách rò dữ liệu khó thấy nhất",
    )
    bao_dam(set(d_hong) <= {"ok", "ma_theo_doi", "ly_do", "cong_cu", "loai_loi"},
            "thanh_dict có khoá ngoài dự kiến: " + repr(sorted(d_hong)))
    return "chỉ 4-5 khoá, không có chủ thể"


@phep_kiem(
    "24. ★ LỖI THẬT — lo_chi_tiet_loi=True: chuỗi giống khoá nằm GIỮA thông điệp "
    "KHÔNG bị làm mờ"
)
def kiem_lo_chi_tiet_loi():
    def no(_ts):
        raise RuntimeError("nền tảng đích từ chối, chứng thư đã dùng: " + KHOA_BIA)

    nhan, _, so, _ = dung_nhan(ham_doc=no, lo_chi_tiet_loi=True)
    kq = nhan.goi(DT_DOC, "gia.doc", {})
    bao_dam(
        KHOA_BIA not in kq.ly_do,
        "CHUỖI GIỐNG KHOÁ ĐI THẲNG RA NGƯỜI GỌI. dinh_tuyen.py dòng 361-363 nói "
        "'Thông điệp lỗi ĐI QUA hàm làm mờ … và tham số ấy có thể là khoá của "
        "khách', nhưng nhat_ky.lam_mo() neo mọi mẫu hình dạng bằng ^…$, nên nó chỉ "
        "bắt được chuỗi bí mật ĐỨNG MỘT MÌNH. Một bí mật nối vào giữa câu văn thì "
        "lọt nguyên. Cùng lỗ ấy làm trường 'them.thong_diep' trong nhật ký cũng "
        "không được làm mờ như tên biến thong_diep_mo hứa, và 'them.vet_goi' thì "
        "chép nguyên cả vết ngăn xếp, không qua làm mờ lần nào. Lý do trả về: "
        + kq.ly_do,
    )
    return "không tới đây"


# ══════════════════════════════════════════════════════════════════════════════
# Nhóm 5 — Liệt kê công cụ: không được vẽ bản đồ hệ thống cho người chưa có quyền
# ══════════════════════════════════════════════════════════════════════════════


@phep_kiem("25. danh_sach_cong_cu chỉ liệt kê công cụ NGƯỜI ĐÓ ĐƯỢC PHÉP")
def kiem_danh_sach_loc_theo_quyen():
    nhan, _, _, _ = dung_nhan(mo_cong_ghi=True)
    ten_cua_nv = [c["ten"] for c in nhan.danh_sach_cong_cu(DT_DOC)]
    bao_dam(
        ten_cua_nv == ["gia.doc"],
        "danh sách của vai chỉ-đọc phải đúng ['gia.doc'], nhận {!r}. Liệt kê cả "
        "công cụ không được phép là RÒ RỈ THÔNG TIN: kẻ tấn công biết được hệ có "
        "những công cụ gì.".format(ten_cua_nv),
    )
    ten_cua_qt = [c["ten"] for c in nhan.danh_sach_cong_cu(DT_GHI)]
    bao_dam(sorted(ten_cua_qt) == ["gia.doc", "gia.ghi"], "quản trị phải thấy cả hai")

    bao_dam(nhan.danh_sach_cong_cu(DT_LA) == [], "vai chưa khai phải thấy danh sách RỖNG")
    bao_dam(nhan.danh_sach_cong_cu(None) == [], "không danh tính phải thấy danh sách RỖNG")
    bao_dam(
        nhan.danh_sach_cong_cu(DanhTinh.khong_vai(ma="x-1", nguon="khoa-api")) == [],
        "danh tính KHÔNG VAI phải thấy danh sách RỖNG",
    )
    return "lọc đúng theo vai, 3 ca rỗng"


@phep_kiem("26. Công cụ GHI BIẾN MẤT khỏi danh sách khi cổng ghi ĐÓNG")
def kiem_danh_sach_theo_cong_ghi():
    nhan, _, _, _ = dung_nhan(mo_cong_ghi=False)
    ten = [c["ten"] for c in nhan.danh_sach_cong_cu(DT_GHI)]
    bao_dam(
        ten == ["gia.doc"],
        "cổng ghi ĐÓNG mà công cụ ghi vẫn hiện: {!r}. Danh sách phải tính theo "
        "thời điểm hỏi, không theo cấu hình tĩnh.".format(ten),
    )
    nhan.chinh_sach.cong_ghi.mo(ly_do="bài tự kiểm", nguoi_mo="thu_dinh_tuyen")
    ten2 = sorted(c["ten"] for c in nhan.danh_sach_cong_cu(DT_GHI))
    bao_dam(ten2 == ["gia.doc", "gia.ghi"], "mở cổng thì công cụ ghi phải hiện lại")
    nhan.chinh_sach.cong_ghi.dong()
    ten3 = [c["ten"] for c in nhan.danh_sach_cong_cu(DT_GHI)]
    bao_dam(ten3 == ["gia.doc"], "đóng lại thì phải biến mất lần nữa")
    return "hiện/ẩn theo trạng thái cổng ngay lúc hỏi"


# ══════════════════════════════════════════════════════════════════════════════

CAC_PHEP_KIEM = [
    kiem_trung_ten_trinh,
    kiem_khong_va_cham_ten_ngan,
    kiem_ten_meo,
    kiem_khong_cong_cu,
    kiem_dang_ky_hong_giua_chung,
    kiem_thieu_quyen,
    kiem_het_han,
    kiem_vuot_han_muc,
    kiem_hop_le_dung_mot_lan,
    kiem_khong_danh_tinh,
    kiem_cong_ghi_dong,
    kiem_doc_khong_tu_dong_thanh_ghi,
    kiem_ghi_hop_le,
    kiem_ten_cong_cu_la,
    kiem_tham_so_sai_kieu,
    kiem_danh_tinh_sai_kieu,
    kiem_trinh_dieu_khien_sua_nhat_ky,
    kiem_nhat_ky_hong_cong_cu_ghi,
    kiem_nhat_ky_hong_cong_cu_doc,
    kiem_lam_mo,
    kiem_ngoai_le_khong_lo,
    kiem_system_exit_va_ctrl_c,
    kiem_thanh_dict_khong_lo,
    kiem_lo_chi_tiet_loi,
    kiem_danh_sach_loc_theo_quyen,
    kiem_danh_sach_theo_cong_ghi,
]


def main() -> int:
    print("=" * 78)
    print("BAI TU KIEM — nhan/dinh_tuyen.py (trai tim cua nhan)")
    print("Python {}.{}.{}".format(*sys.version_info[:3]))
    print("KHONG mang, KHONG CSDL, KHONG doc bien moi truong that.")
    print("=" * 78)
    print()

    tat_ca_dat = True
    for phep in CAC_PHEP_KIEM:
        if not phep():
            tat_ca_dat = False

    print()
    print("=" * 78)
    so_dat = sum(1 for _, dat, _ in _KET_QUA if dat)
    so_hong = len(_KET_QUA) - so_dat
    if tat_ca_dat:
        print("KET QUA: {}/{} DAT.".format(so_dat, len(_KET_QUA)))
        print()
        print("Nghia la gi: mot loi goi cong cu KHONG vong qua duoc nhan. Thieu quyen,")
        print("het han, vuot han muc, cong ghi dong — trong ca bon ca, ham cong cu chay")
        print("DUNG 0 LAN (do bang bo dem, khong doc gia tri tra ve), va moi lan tu choi")
        print("de lai dung MOT dong nhat ky co chu the.")
        print()
        print("Nghia la gi KHONG: bai nay khong do hieu nang, khong do chay song song,")
        print("khong kiem KhoTrongBoNho qua nhieu tien trinh, va khong kiem mot trinh")
        print("dieu khien THAT nao — moi trinh dieu khien o day deu la gia.")
    else:
        print("KET QUA: {}/{} DAT, {} HONG.".format(so_dat, len(_KET_QUA), so_hong))
        print()
        print("Cac phep kiem HONG:")
        for ten, dat, ghi_chu in _KET_QUA:
            if not dat:
                print("  - {}".format(ten))
                print("    {}".format(ghi_chu))
        print()
        print("Phep kiem co dau ★ LOI THAT hong vi MA NGUON sai, khong phai vi bai sai.")
        print("Khong duoc lam chung xanh bang cach noi long phep kiem.")
    print("=" * 78)
    return 0 if tat_ca_dat else 1


if __name__ == "__main__":
    sys.exit(main())
