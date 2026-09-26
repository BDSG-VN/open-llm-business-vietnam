#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/dinh_tuyen.py — TRÁI TIM CỦA NHÂN.

Một lời gọi công cụ đi qua đúng bảy bước, luôn theo thứ tự này:

    1. danh tính   — không có thì DỪNG (không có "khách" mặc định)
    2. phân giải   — tách <trinh_dieu_khien>.<cong_cu>, tìm trình điều khiển
    3. quyền       — danh sách trắng + phân biệt đọc/ghi + cổng ghi toàn nhân
    4. hạn mức     — cửa sổ trượt
    5. (nếu là công cụ GHI) ghi nhật ký Ý ĐỊNH trước khi chạy
    6. chạy        — gọi trình điều khiển, bắt mọi lỗi
    7. nhật ký     — một dòng JSON, tham số đã làm mờ

QUYẾT ĐỊNH KIẾN TRÚC SỐ 2, VIẾT THÀNH MÃ
----------------------------------------
Nhân sở hữu danh tính, quyền, hạn mức, nhật ký. Trình điều khiển thì KHÔNG.
Trình điều khiển biết đúng một việc: đổi một lời gọi công cụ thành một lời gọi
API của nền tảng nó phụ trách, rồi trả kết quả về. Nó không nhận `danh_tinh`,
không đọc chính sách, không đụng vào nhật ký. Đó không phải phép lịch sự — đó là
điều kiện để câu "ai đã làm gì" có MỘT câu trả lời. Mười tám nền tảng mà mỗi
nền tảng tự xác thực thì có mười tám mô hình quyền, và không mô hình nào trả lời
được câu ấy cho cả hệ.

Hệ quả cụ thể trong chữ ký hàm: `ham(tham_so) -> ket_qua`. Không có tham số
`danh_tinh`. Muốn một trình điều khiển hành động "thay mặt" người dùng ở nền
tảng đích thì đó là chuyện danh tính LIÊN NỀN TẢNG, và tính đến 26/09/2026 việc
ấy CHƯA LÀM — nói thẳng ra đây thay vì để một tham số lấp lửng gợi ý là đã có.

VÌ SAO TÊN CÔNG CỤ CÓ DẠNG `<trinh_dieu_khien>.<cong_cu>`, KHÔNG PHẲNG
----------------------------------------------------------------------
Ba lý do, lý do thứ nhất là đủ:
  1. VA CHẠM TÊN. Hệ sinh thái này có nhiều nền tảng cùng loại nghiệp vụ; sớm
     muộn hai nền tảng cùng muốn một công cụ tên `tim_kiem`. Với tên phẳng, cái
     đăng ký sau ghi đè cái trước — im lặng — và một quyền cấp cho `tim_kiem`
     của nền tảng A bỗng mở `tim_kiem` của nền tảng B.
  2. ĐỌC CHÍNH SÁCH RA NGHĨA. Một dòng `crm.doc_khach` nói luôn nó chạm vào
     đâu. Một dòng `doc_khach` thì phải đi tra.
  3. NHẬT KÝ TRUY VẤN ĐƯỢC THEO NỀN TẢNG. "Tuần này ai đụng vào nền tảng bản
     đồ" là một phép lọc tiền tố, không phải một bảng tra cứu phải bảo trì.

MỘT LỖI TRONG TRÌNH ĐIỀU KHIỂN KHÔNG ĐƯỢC LÀM SẬP NHÂN
------------------------------------------------------
Trình điều khiển là mã của người khác (kể cả của chính ta, viết lúc vội). Nhân
bắt `Exception` VÀ `SystemExit` — `SystemExit` vì một trình điều khiển gọi
`sys.exit()` lúc thiếu cấu hình sẽ giết cả tiến trình phục vụ 18 nền tảng.
`KeyboardInterrupt` thì CỐ Ý để lọt: người vận hành bấm Ctrl-C phải dừng được
máy chủ, không thì nhân biến thành thứ không tắt nổi.

GIỚI HẠN ĐÃ BIẾT, CHƯA LÀM (26/09/2026)
---------------------------------------
  · KHÔNG CÓ HẠN GIỜ CHẠY. Một trình điều khiển treo thì treo luôn nhân. Làm
    đúng việc này cần tiến trình con hoặc luồng có thể huỷ, và cả hai đều đổi
    kiến trúc; chưa làm, và KHÔNG giả vờ là đã có.
  · KHÔNG CÓ HÀNG ĐỢI / CHẠY SONG SONG. Mỗi lần một lời gọi.
  · `KhoTrongBoNho` của hạn mức không chia sẻ giữa các tiến trình (xem
    `han_muc.py`).

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import copy
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from .danh_tinh import BoXacThuc, DanhTinh
from .han_muc import BoHanMuc, HanMuc
from .nhat_ky import LOI, THANH_CONG, TU_CHOI, LoiNhatKy, NhatKy, lam_mo, ma_theo_doi_moi
from .quyen import ChinhSach, CongGhi

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
MAU_TEN_TRINH = re.compile(r"^[a-z0-9][a-z0-9_]{0,31}\Z")
MAU_TEN_NGAN = re.compile(r"^[a-z0-9][a-z0-9_]{0,63}\Z")


class LoiDangKy(ValueError):
    pass


@dataclass(frozen=True)
class BanKhaiCongCu:
    """Một công cụ do trình điều khiển cung cấp.

    `ghi` do NGƯỜI VIẾT TRÌNH ĐIỀU KHIỂN khai, vì chỉ người ấy biết lời gọi phía
    sau có thay đổi gì ở nền tảng đích hay không. Nhân không đoán hộ: đoán theo
    tên (`tao_`, `xoa_`, `sua_`) thì một công cụ tên `dong_bo` sẽ được xếp nhầm
    vào loại đọc, và mặc định chỉ đọc mất hiệu lực đúng ở chỗ nguy hiểm nhất.
    """

    ten: str
    ham: Callable[[Dict[str, Any]], Any]
    ghi: bool = False
    mo_ta: str = ""
    luoc_do: Optional[Dict[str, Any]] = None  # JSON Schema cho MCP tools/list

    def __post_init__(self) -> None:
        if not MAU_TEN_NGAN.match(self.ten or ""):
            raise LoiDangKy("tên công cụ %r không hợp lệ" % (self.ten,))
        if not callable(self.ham):
            raise LoiDangKy("công cụ %r không có hàm gọi được" % (self.ten,))


class TrinhDieuKhien:
    """Lớp cơ sở. Kế thừa và khai `ten` + `cong_cu()`.

    Cố ý rất mỏng: mỏng thì viết một trình điều khiển mới cho nền tảng thứ 19 là
    một tệp nhỏ, không phải một cuộc đàm phán với nhân.
    """

    ten: str = ""
    mo_ta: str = ""

    def cong_cu(self) -> Sequence[BanKhaiCongCu]:
        raise NotImplementedError


@dataclass
class KetQuaGoi:
    """Thứ `Nhan.goi` trả về. Luôn có cấu trúc, kể cả khi hỏng."""

    ok: bool
    ma_theo_doi: str
    ly_do: str
    ten_cong_cu: str = ""
    ket_qua: Any = None
    loai_loi: str = ""

    def thanh_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "ok": self.ok,
            "ma_theo_doi": self.ma_theo_doi,
            "ly_do": self.ly_do,
            "cong_cu": self.ten_cong_cu,
        }
        if self.ok:
            d["ket_qua"] = self.ket_qua
        if self.loai_loi:
            d["loai_loi"] = self.loai_loi
        return d


class Nhan:
    """Nhân: danh tính + quyền + hạn mức + nhật ký + định tuyến."""

    def __init__(
        self,
        chinh_sach: Optional[ChinhSach] = None,
        bo_han_muc: Optional[BoHanMuc] = None,
        nhat_ky: Optional[NhatKy] = None,
        bo_xac_thuc: Optional[BoXacThuc] = None,
        dong_ho: Callable[[], float] = time.monotonic,
        lo_chi_tiet_loi: bool = False,
    ) -> None:
        self.chinh_sach = chinh_sach if chinh_sach is not None else ChinhSach()
        self.bo_han_muc = (
            bo_han_muc
            if bo_han_muc is not None
            else BoHanMuc(mac_dinh=HanMuc(so_lan=60, cua_so_giay=60.0), dong_ho=dong_ho)
        )
        self.nhat_ky = nhat_ky if nhat_ky is not None else NhatKy()
        self.bo_xac_thuc = bo_xac_thuc if bo_xac_thuc is not None else BoXacThuc()
        self._dong_ho = dong_ho
        # lo_chi_tiet_loi=False: người gọi nhận tên lớp ngoại lệ và mã theo dõi,
        # KHÔNG nhận thông điệp lỗi gốc. Thông điệp lỗi của một thư viện CSDL hay
        # kèm câu truy vấn, tên bảng, đôi khi cả giá trị tham số — tức là đường
        # rò dữ liệu ra phía người gọi, và là bản đồ cho người dò. Chi tiết vẫn
        # nằm trong nhật ký, chỗ có kiểm soát truy cập.
        self.lo_chi_tiet_loi = bool(lo_chi_tiet_loi)
        self._trinh: Dict[str, TrinhDieuKhien] = {}
        self._cong_cu: Dict[str, BanKhaiCongCu] = {}

    # -- đăng ký --------------------------------------------------------------

    def dang_ky(self, ten: str, trinh_dieu_khien: TrinhDieuKhien) -> List[str]:
        """Đăng ký một trình điều khiển dưới tên `ten`. Trả danh sách tên công cụ đầy đủ.

        Đăng ký KHÔNG cấp quyền cho ai. Nó chỉ khai với chính sách rằng các công
        cụ này TỒN TẠI và cái nào ghi. Việc cấp quyền là `ChinhSach.khai_vai`, và
        phải chạy SAU — thứ tự ấy biến một tên gõ nhầm trong cấu hình quyền thành
        lỗi nạp thay vì một quyền âm thầm không tồn tại.
        """
        if not MAU_TEN_TRINH.match(ten or ""):
            raise LoiDangKy(
                "tên trình điều khiển %r không hợp lệ (cần %s)" % (ten, MAU_TEN_TRINH.pattern)
            )
        if ten in self._trinh:
            # Ghi đè im lặng = một mô-đun nạp sau chiếm toàn bộ công cụ của một
            # nền tảng khác, kể cả các quyền đã cấp cho tên ấy.
            raise LoiDangKy("đã có trình điều khiển tên %r" % (ten,))

        cac_ban_khai = list(trinh_dieu_khien.cong_cu())
        if not cac_ban_khai:
            raise LoiDangKy("trình điều khiển %r không khai công cụ nào" % (ten,))

        ten_day_du: List[str] = []
        for bk in cac_ban_khai:
            if not isinstance(bk, BanKhaiCongCu):
                raise LoiDangKy(
                    "trình điều khiển %r trả về %s chứ không phải BanKhaiCongCu"
                    % (ten, type(bk).__name__)
                )
            day_du = "%s.%s" % (ten, bk.ten)
            if day_du in self._cong_cu:
                raise LoiDangKy("công cụ %r bị khai hai lần" % (day_du,))
            self.chinh_sach.khai_cong_cu(day_du, ghi=bk.ghi, mo_ta=bk.mo_ta)
            self._cong_cu[day_du] = bk
            ten_day_du.append(day_du)

        self._trinh[ten] = trinh_dieu_khien
        return ten_day_du

    def cac_trinh_dieu_khien(self) -> List[str]:
        return sorted(self._trinh)

    def ban_khai(self, ten_day_du: str) -> Optional[BanKhaiCongCu]:
        return self._cong_cu.get(ten_day_du)

    # -- liệt kê --------------------------------------------------------------

    def danh_sach_cong_cu(self, danh_tinh: Optional[DanhTinh]) -> List[Dict[str, Any]]:
        """Chỉ những công cụ danh tính này gọi được NGAY BÂY GIỜ.

        Liệt kê hết rồi từ chối lúc gọi là bày cho người dùng đi một vòng vô ích,
        và với một mô hình ngôn ngữ ở đầu kia thì còn tệ hơn: nó sẽ thử, bị từ
        chối, rồi thử lại bằng cách khác — đốt lượt gọi và làm bẩn nhật ký.
        """
        ra: List[Dict[str, Any]] = []
        for ten in self.chinh_sach.cong_cu_duoc_phep(danh_tinh):
            bk = self._cong_cu.get(ten)
            if bk is None:
                continue
            ra.append(
                {
                    "ten": ten,
                    "mo_ta": bk.mo_ta,
                    "ghi": bk.ghi,
                    "luoc_do": bk.luoc_do or {"type": "object", "properties": {}},
                }
            )
        return ra

    # -- đường gọi ------------------------------------------------------------

    def goi(
        self,
        danh_tinh: Optional[DanhTinh],
        ten_cong_cu: str,
        tham_so: Optional[Dict[str, Any]] = None,
    ) -> KetQuaGoi:
        ma = ma_theo_doi_moi()
        tham_so = {} if tham_so is None else tham_so
        bat_dau = self._dong_ho()

        # ── QUY DANH TÍNH LẠ VỀ None TRƯỚC KHI GHI BẤT CỨ THỨ GÌ ───────────
        #   Sửa 26/09/2026. Trước bản vá: một đối tượng KHÔNG PHẢI DanhTinh
        #   được chuyển thẳng xuống NhatKy.ghi(), hàm ấy gọi .tom_tat(), ném
        #   AttributeError, và khối `except Exception` bên dưới biến nó thành
        #   một chuỗi cảnh báo trả về cho NGƯỜI GỌI. Kết quả đo được: một lần
        #   thử MẠO DANH để lại ĐÚNG 0 dòng nhật ký. Người gọi biết, còn người
        #   vận hành thì không — tức kẻ dò tìm bằng danh tính giả đi qua không
        #   để lại vết.
        #
        #   Một lần TỪ CHỐI không được ghi còn nặng hơn một lần cho phép không
        #   được ghi: lần cho phép ít ra còn có hậu quả nhìn thấy được ở nơi
        #   khác, còn lần từ chối thì không để lại gì hết.
        sai_kieu = danh_tinh is not None and not isinstance(danh_tinh, DanhTinh)
        if sai_kieu:
            kieu_la = type(danh_tinh).__name__
            danh_tinh = None      # từ đây trở xuống, nhật ký ghi được

        # ── CHỤP THAM SỐ TRƯỚC KHI TRÌNH ĐIỀU KHIỂN CHẠM VÀO ───────────────
        #   Sửa 26/09/2026. Trước bản vá, nhân truyền THẲNG dict của người gọi
        #   cho hàm công cụ rồi mới ghi CÙNG dict ấy sau khi công cụ chạy xong.
        #   Nên trình điều khiển có một cửa sổ để viết lại chính bằng chứng
        #   chống lại nó: đo được cảnh nhân gửi {'pham_vi': 'toan-bo-CSDL'} mà
        #   nhật ký ghi {'vo_hai': '...'}.
        #
        #   Quyết định kiến trúc số 2 nói NHÂN sở hữu nhật ký. Muốn điều đó
        #   đúng thì nhân phải giữ bản chụp của riêng mình.
        try:
            tham_so_ghi = copy.deepcopy(tham_so)
        except Exception:
            # Không sao chép sâu được (đối tượng lạ, vòng tham chiếu) thì ghi
            # dạng chữ. Thà một bản ghi kém chi tiết còn hơn một bản ghi mà
            # trình điều khiển sửa được.
            tham_so_ghi = {"khong_sao_chep_duoc": repr(tham_so)[:500]}

        def _ghi(ket_qua: str, ly_do: str, gia_tri=None, them=None) -> Optional[str]:
            """Ghi nhật ký. Trả None nếu ổn, hoặc chuỗi lý do nếu KHÔNG ghi được."""
            try:
                self.nhat_ky.ghi(
                    danh_tinh=danh_tinh,
                    cong_cu=ten_cong_cu,
                    tham_so=tham_so_ghi,   # BẢN CHỤP, không phải dict người gọi
                    ket_qua=ket_qua,
                    ly_do=ly_do,
                    mili_giay=(self._dong_ho() - bat_dau) * 1000.0,
                    ma_theo_doi=ma,
                    gia_tri_tra_ve=gia_tri,
                    them=them,
                )
                return None
            except LoiNhatKy as loi:
                return str(loi)
            except Exception as loi:  # nhật ký hỏng kiểu khác cũng không được nuốt
                return "%s: %s" % (type(loi).__name__, loi)

        def _tu_choi(ly_do: str) -> KetQuaGoi:
            loi_ghi = _ghi(TU_CHOI, ly_do)
            if loi_ghi:
                # Không ghi được cả dòng TỪ CHỐI thì vẫn phải từ chối; chỉ nói
                # thêm cho người gọi biết sổ sách đang hỏng.
                return KetQuaGoi(
                    ok=False,
                    ma_theo_doi=ma,
                    ten_cong_cu=ten_cong_cu,
                    ly_do=ly_do + " | ⚠ nhật ký hỏng: " + loi_ghi,
                    loai_loi="LoiNhatKy",
                )
            return KetQuaGoi(ok=False, ma_theo_doi=ma, ten_cong_cu=ten_cong_cu, ly_do=ly_do)

        # 1. Danh tính ------------------------------------------------------
        if sai_kieu:
            return _tu_choi(
                "từ chối: danh tính sai kiểu (%s, cần DanhTinh) — coi như MẠO DANH"
                % (kieu_la,)
            )
        if danh_tinh is None:
            return _tu_choi("từ chối: không có danh tính (nhân không có khách mặc định)")
        if not isinstance(danh_tinh, DanhTinh):
            return _tu_choi(
                "từ chối: đối tượng danh tính sai kiểu (%s)" % type(danh_tinh).__name__
            )
        if not danh_tinh.con_hieu_luc(time.time()):
            return _tu_choi("từ chối: danh tính %r đã hết hạn" % (danh_tinh.ma,))

        # Tham số phải là ánh xạ — mọi lớp phía sau (làm mờ, lược đồ MCP) đều
        # giả định thế, và một chuỗi lọt vào đây sẽ lỗi ở chỗ rất xa.
        if not isinstance(tham_so, dict):
            return _tu_choi(
                "từ chối: tham số phải là đối tượng, nhận %s" % type(tham_so).__name__
            )

        # 2. Phân giải tên ---------------------------------------------------
        if not isinstance(ten_cong_cu, str) or ten_cong_cu.count(".") != 1:
            return _tu_choi(
                "từ chối: tên công cụ %r phải có dạng <trinh_dieu_khien>.<cong_cu>"
                % (ten_cong_cu,)
            )
        ten_trinh = ten_cong_cu.split(".", 1)[0]
        trinh = self._trinh.get(ten_trinh)
        ban_khai = self._cong_cu.get(ten_cong_cu)
        if trinh is None or ban_khai is None:
            # Cùng một câu cho "không có trình điều khiển" và "không có công cụ":
            # phân biệt hai ca là vẽ bản đồ hệ thống cho người chưa có quyền.
            return _tu_choi("từ chối: không có công cụ %r" % (ten_cong_cu,))

        # 3. Quyền -----------------------------------------------------------
        duoc, ly_do_quyen = self.chinh_sach.duoc_goi(danh_tinh, ten_cong_cu)
        if not duoc:
            return _tu_choi(ly_do_quyen)

        # 4. Hạn mức ---------------------------------------------------------
        trong_han, ly_do_han = self.bo_han_muc.kiem_va_ghi(danh_tinh, ten_cong_cu)
        if not trong_han:
            return _tu_choi(ly_do_han)

        # 5. Nhật ký Ý ĐỊNH cho công cụ GHI ----------------------------------
        # Ghi TRƯỚC khi chạy, vì với một lời gọi làm thay đổi dữ liệu thì bản ghi
        # "đã định làm" quan trọng hơn bản ghi "đã làm xong": tiến trình chết
        # giữa chừng vẫn để lại dấu vết là ai đã chạm vào cái gì. Không ghi được
        # thì KHÔNG CHẠY — đây là chỗ nhân chọn fail-closed một cách cố ý.
        if ban_khai.ghi:
            loi_ghi = _ghi(
                THANH_CONG,
                "ý định: sắp chạy công cụ GHI %r (%s)" % (ten_cong_cu, ly_do_quyen),
                them={"giai_doan": "truoc-khi-chay"},
            )
            if loi_ghi:
                return KetQuaGoi(
                    ok=False,
                    ma_theo_doi=ma,
                    ten_cong_cu=ten_cong_cu,
                    ly_do="từ chối: không ghi được nhật ký ý định cho công cụ GHI "
                    "⇒ không chạy. " + loi_ghi,
                    loai_loi="LoiNhatKy",
                )

        # 6. Chạy ------------------------------------------------------------
        try:
            gia_tri = ban_khai.ham(tham_so)
        except KeyboardInterrupt:
            # Cố ý để lọt: Ctrl-C phải dừng được máy chủ.
            raise
        except (Exception, SystemExit) as loi:
            loai = type(loi).__name__
            # Thông điệp lỗi ĐI QUA hàm làm mờ: một ngoại lệ rất hay nhắc lại
            # chính tham số gây ra nó, và tham số ấy có thể là khoá của khách.
            thong_diep_mo, _ = lam_mo(str(loi))
            vet = traceback.format_exc()
            if len(vet) > 4000:
                vet = vet[:4000] + "… (cắt)"
            _ghi(
                LOI,
                "lỗi trong trình điều khiển %r: %s" % (ten_trinh, loai),
                them={
                    "giai_doan": "khi-chay",
                    "loai_loi": loai,
                    "thong_diep": thong_diep_mo,
                    "vet_goi": vet,
                },
            )
            ly_do_ra = "lỗi khi chạy công cụ %r (%s). Mã theo dõi: %s" % (
                ten_cong_cu,
                loai,
                ma,
            )
            if self.lo_chi_tiet_loi:
                ly_do_ra += " — %s" % (thong_diep_mo,)
            return KetQuaGoi(
                ok=False,
                ma_theo_doi=ma,
                ten_cong_cu=ten_cong_cu,
                ly_do=ly_do_ra,
                loai_loi=loai,
            )

        # 7. Nhật ký kết quả --------------------------------------------------
        loi_ghi = _ghi(
            THANH_CONG,
            ly_do_quyen + "; " + ly_do_han,
            gia_tri=gia_tri,
            them={"giai_doan": "xong"} if ban_khai.ghi else None,
        )
        if loi_ghi:
            # Đã chạy rồi mới hỏng nhật ký: không giấu được chuyện đã chạy, nhưng
            # phải nói ra rằng bản ghi kiểm toán KHÔNG có.
            return KetQuaGoi(
                ok=True,
                ma_theo_doi=ma,
                ten_cong_cu=ten_cong_cu,
                ket_qua=gia_tri,
                ly_do="đã chạy xong nhưng ⚠ KHÔNG ghi được nhật ký: " + loi_ghi,
            )
        return KetQuaGoi(
            ok=True,
            ma_theo_doi=ma,
            ten_cong_cu=ten_cong_cu,
            ket_qua=gia_tri,
            ly_do=ly_do_quyen,
        )
