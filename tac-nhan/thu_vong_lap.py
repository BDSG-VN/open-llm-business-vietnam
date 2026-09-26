#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""thu_vong_lap.py — khoá BẢY LUẬT của vòng lặp tác nhân.

Bài này dùng NHÂN THẬT (nhan/) với trình điều khiển GIẢ và mô hình GIẢ có kịch
bản. Dùng nhân thật là cố ý: một vòng lặp kiểm bằng nhân giả chỉ chứng minh nó
khớp với cái giả ấy.

PHÉP ĐO TRUNG TÂM là BỘ ĐẾM CHẠY THẬT của công cụ, KHÔNG phải giá trị trả về.
Lý do: một lời gọi có thể trả về lỗi TRONG KHI công cụ đã chạy rồi và đã gây
tác dụng phụ. Bài kiểm nào chỉ xem giá trị trả về sẽ không bao giờ bắt được ca
ấy — và ca ấy đúng là ca nguy hiểm nhất.

KHÔNG mạng, KHÔNG CSDL, KHÔNG đọc biến môi trường thật.
"""
import importlib.util
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.dirname(GOC)
sys.path.insert(0, GOC)
sys.path.insert(0, KHO)

_s = importlib.util.spec_from_file_location(
    "nhan", os.path.join(KHO, "nhan", "__init__.py"),
    submodule_search_locations=[os.path.join(KHO, "nhan")])
_n = importlib.util.module_from_spec(_s)
sys.modules["nhan"] = _n
_s.loader.exec_module(_n)

from nhan import dinh_tuyen as DT           # noqa: E402
from nhan.danh_tinh import DanhTinh         # noqa: E402
from nhan.quyen import ChinhSach            # noqa: E402
from phoi_cong_cu import TEN_CONG_CU_META, BoPhoiCongCu   # noqa: E402
from vong_lap import CanXacNhan, VongLapTacNhan           # noqa: E402

dat = 0
tong = 0


def kiem(ten, dk, ct=""):
    global dat, tong
    tong += 1
    print("  [{}] {}{}".format("DAT " if dk else "HONG", ten, "  — " + ct if ct else ""))
    if dk:
        dat += 1


# ── Trình điều khiển GIẢ: mỗi công cụ ĐẾM số lần nó THẬT SỰ chạy ──────────
class TrinhGia:
    def __init__(self):
        self.dem = {}

    def _lam(self, ten, ket_qua=None, nem=None):
        # Nhân gọi `ban_khai.ham(tham_so)` — MỘT đối số vị trí là cả dict tham
        # số, KHÔNG phải **kwargs. Viết sai chữ ký thì mọi công cụ ném TypeError
        # và bài kiểm đo nhầm một thứ khác hẳn.
        def f(tham_so):
            self.dem[ten] = self.dem.get(ten, 0) + 1
            if nem is not None:
                raise nem
            return ket_qua if ket_qua is not None else {"ok": ten, "tham_so": tham_so}
        return f

    # `BanKhaiCongCu.ten` là tên NGẮN — nhân tự ghép `<trình>.<công cụ>` lúc
    # đăng ký. Khai tên đầy đủ ở đây sẽ bị LoiDangKy từ chối, và đó là hành vi
    # đúng: một chỗ duy nhất quyết định tên đầy đủ thì không có hai cách gọi.
    def cong_cu_crm(self):
        return [
            DT.BanKhaiCongCu(ten="doc_khach", ham=self._lam("crm.doc_khach"),
                             ghi=False, mo_ta="đọc khách", luoc_do={}),
            DT.BanKhaiCongCu(ten="ghi_khach", ham=self._lam("crm.ghi_khach"),
                             ghi=True, mo_ta="GHI khách", luoc_do={}),
            DT.BanKhaiCongCu(ten="hay_hong",
                             ham=self._lam("crm.hay_hong", nem=RuntimeError("CSDL sập")),
                             ghi=False, mo_ta="luôn hỏng", luoc_do={}),
        ]

    def cong_cu_kho(self):
        return [
            DT.BanKhaiCongCu(ten="doc_ton", ham=self._lam("kho.doc_ton"),
                             ghi=False, mo_ta="đọc tồn", luoc_do={}),
        ]

    def khai_day_du(self):
        """Bản khai cho BoPhoiCongCu — dùng TÊN ĐẦY ĐỦ, như mô hình nhìn thấy."""
        ra = []
        for tien_to, ds in (("crm", self.cong_cu_crm()), ("kho", self.cong_cu_kho())):
            for b in ds:
                ra.append({"ten": tien_to + "." + b.ten, "mo_ta": b.mo_ta,
                           "ghi": b.ghi, "luoc_do": {}})
        return ra


def dung(cho_phep_ghi=False, tran_luot=12, tran_lap_loi=3, vai=("nhan_vien",)):
    trinh = TrinhGia()
    cs = ChinhSach()
    for b in trinh.khai_day_du():
        cs.khai_cong_cu(b["ten"], ghi=b["ghi"], mo_ta=b["mo_ta"])
    cs.khai_vai("nhan_vien", doc=["crm.doc_khach", "crm.hay_hong", "kho.doc_ton"],
                ghi=["crm.ghi_khach"])
    cs.khai_vai("khach_le", doc=["crm.doc_khach"])
    if cho_phep_ghi:
        cs.cong_ghi.mo("bài tự kiểm", "thu_vong_lap")
    # Nhật ký mặc định in ra stdout. Trong bài kiểm nó làm ngập kết quả, nên
    # hứng vào một dòng giả — và nhờ vậy ĐẾM ĐƯỢC số bản ghi.
    #
    # `dong_ra` cần một ĐỐI TƯỢNG CÓ .write(), không phải một hàm. Truyền
    # `list.append` vào đây thì NhatKy ném AttributeError, và nhân — rất đúng —
    # TỪ CHỐI chạy mọi công cụ GHI vì không ghi được nhật ký ý định trước.
    # Triệu chứng khi ấy là "công cụ ghi chạy 0 lần", trông hệt như một lỗi
    # phân quyền. Ghi lại vì đã mất một lượt truy tìm vì chỗ này.
    from nhan.nhat_ky import NhatKy

    class _DongGia:
        def __init__(self):
            self.dong = []

        def write(self, s):
            if s.strip():
                self.dong.append(s)

        def flush(self):
            pass

    dong_nhat_ky = _DongGia()
    nhan = DT.Nhan(chinh_sach=cs, nhat_ky=NhatKy(dong_ra=dong_nhat_ky))
    nhan._thu_dong_nhat_ky = dong_nhat_ky   # để bài kiểm đếm được
    # `dang_ky` nhận một ĐỐI TƯỢNG có `.cong_cu()`, không nhận một danh sách —
    # đó là giao thức TrinhDieuKhien. Bọc lại cho đúng.
    class _Boc:
        def __init__(self, ds):
            self._ds = ds

        def cong_cu(self):
            return self._ds

    nhan.dang_ky("crm", _Boc(trinh.cong_cu_crm()))
    nhan.dang_ky("kho", _Boc(trinh.cong_cu_kho()))
    bp = BoPhoiCongCu(trinh.khai_day_du(), luon_bat=["crm.doc_khach"], tran=6)
    dt = DanhTinh(ma="nv-01", vai=tuple(vai), nguon="thu")
    return trinh, nhan, bp, dt


def mo_hinh_kich_ban(*buoc):
    """Mô hình giả chạy theo kịch bản; hết kịch bản thì trả lời bằng chữ."""
    hop = {"i": 0}

    def f(tin_nhan, cong_cu):
        i = hop["i"]
        hop["i"] += 1
        if i < len(buoc):
            b = buoc[i]
            return b(tin_nhan, cong_cu) if callable(b) else b
        return {"loai": "chu", "noi_dung": "xong"}
    return f


def goi(_ten_cong_cu, **ts):
    # Tham số đầu có gạch dưới để không đụng khoá `ten` mà người gọi truyền vào
    # tham số công cụ — đã dính đúng lỗi ấy một lần.
    return {"loai": "goi_cong_cu", "ten": _ten_cong_cu, "tham_so": ts}


print("=" * 74)
print("  VONG LAP TAC NHAN — bay luat")
print("=" * 74)

# ── LUẬT 1 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
khach = DanhTinh(ma="kh-01", vai=("khach_le",), nguon="thu")
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi("kho.doc_ton")), bp)
bg = vl.chay(khach, "xem tồn kho")
kiem("1. ★ LUẬT 1 — bị TỪ CHỐI quyền thì công cụ KHÔNG chạy lần nào",
     trinh.dem.get("kho.doc_ton", 0) == 0,
     "bộ đếm chạy thật = {} (đo bằng bộ đếm, KHÔNG bằng giá trị trả về)"
     .format(trinh.dem.get("kho.doc_ton", 0)))

kiem("2. Lần TỪ CHỐI vẫn sinh sự kiện cho giao diện",
     bg.dem("ket_qua_cong_cu") >= 1 or bg.dem("goi_cong_cu") >= 1,
     ", ".join(bg.cac_loai()))

# ── LUẬT 2 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung(tran_luot=3)
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(*[goi("crm.doc_khach")] * 20), bp, tran_luot=3)
bg = vl.chay(dt, "lặp mãi")
cuoi = bg.su_kien[-1]
kiem("3. ★ LUẬT 2 — hết trần thì DỪNG và NÓI RÕ, không cắt ngang im lặng",
     cuoi["loai"] == "xong" and "trần" in cuoi["ly_do"] and "CHƯA xong" in cuoi["ly_do"],
     cuoi.get("ly_do", "")[:70])
kiem("4. Hết trần thì chạy ĐÚNG số lượt, không hơn",
     trinh.dem.get("crm.doc_khach", 0) == 3,
     "{} lần".format(trinh.dem.get("crm.doc_khach", 0)))

# ── LUẬT 3 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi("khong.co_that"), {"loai": "chu", "noi_dung": "thôi"}), bp)
bg = vl.chay(dt, "gọi công cụ ma")
sk = [s for s in bg.su_kien if s["loai"] == "ket_qua_cong_cu" and not s.get("ok")]
kiem("5. ★ LUẬT 3 — công cụ không tồn tại thì báo lại CÓ ÍCH, không sập",
     len(sk) >= 1 and "crm.doc_khach" in (sk[0].get("ly_do") or ""),
     (sk[0].get("ly_do") if sk else "không có sự kiện lỗi")[:80])

# ── LUẬT 4 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(*[goi("crm.hay_hong")] * 20), bp,
                    tran_luot=12, tran_lap_loi=3)
bg = vl.chay(dt, "gọi cái luôn hỏng")
cuoi = bg.su_kien[-1]
kiem("6. ★ LUẬT 4 — lặp cùng một lỗi thì DỪNG SỚM, không chạy hết trần",
     cuoi["loai"] == "xong" and "lặp lại" in cuoi["ly_do"] and cuoi["so_luot"] < 12,
     "dừng ở lượt {}".format(cuoi.get("so_luot")))
kiem("7. Dừng sớm tiết kiệm THẬT: công cụ chỉ chạy đúng số lần đã đếm",
     trinh.dem.get("crm.hay_hong", 0) == 3,
     "{} lần (trần lặp lỗi = 3)".format(trinh.dem.get("crm.hay_hong", 0)))

# ── LUẬT 5 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung(cho_phep_ghi=False)
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi("crm.ghi_khach", ten="X")), bp,
                    cho_phep_ghi=False)
try:
    vl.chay(dt, "ghi một khách mới")
    kiem("8. ★ LUẬT 5 — hành động GHI phải dừng chờ xác nhận", False, "KHÔNG dừng")
except CanXacNhan as e:
    kiem("8. ★ LUẬT 5 — hành động GHI phải dừng chờ xác nhận",
         e.ten_cong_cu == "crm.ghi_khach")
kiem("9. ★ Khi chờ xác nhận, công cụ GHI chưa chạy lần nào",
     trinh.dem.get("crm.ghi_khach", 0) == 0,
     "bộ đếm = {}".format(trinh.dem.get("crm.ghi_khach", 0)))

# ── Đã duyệt thì chạy được ───────────────────────────────────────────────
trinh, nhan, bp, dt = dung(cho_phep_ghi=True)
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi("crm.ghi_khach", ten="X")), bp,
                    cho_phep_ghi=True)
bg = vl.chay(dt, "ghi một khách mới")
kiem("10. Sau khi được duyệt thì hành động GHI chạy ĐÚNG MỘT lần",
     trinh.dem.get("crm.ghi_khach", 0) == 1,
     "{} lần".format(trinh.dem.get("crm.ghi_khach", 0)))

# ── LUẬT 6 ───────────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi("crm.doc_khach"),
                                           {"loai": "chu", "noi_dung": "đây"}), bp)
bg = vl.chay(dt, "đọc khách")
kiem("11. ★ LUẬT 6 — dòng sự kiện đủ để dựng lại cả phiên",
     bg.cac_loai()[0] == "bat_dau" and bg.cac_loai()[-1] == "xong"
     and "goi_cong_cu" in bg.cac_loai() and "tra_loi" in bg.cac_loai(),
     " → ".join(bg.cac_loai()))

# ── Mô hình trả về rác ───────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban("một chuỗi, không phải dict", 12345,
                                           {"loai": "chu", "noi_dung": "ok"}), bp)
bg = vl.chay(dt, "thử rác")
kiem("12. Mô hình trả về RÁC thì vòng lặp dạy lại khuôn, không sập",
     bg.dem("phan_hoi_hong") == 2 and bg.cac_loai()[-1] == "xong",
     "{} lần nhận rác".format(bg.dem("phan_hoi_hong")))

# ── Mô hình NÉM ─────────────────────────────────────────────────────────
def mo_hinh_no(tin_nhan, cong_cu):
    raise ConnectionError("máy nội bộ không nối được")


trinh, nhan, bp, dt = dung()
bg = VongLapTacNhan(nhan, mo_hinh_no, bp).chay(dt, "hỏi gì đó")
kiem("13. Mô hình NÉM thì ghi lại rồi dừng, không để ngoại lệ vọt ra",
     bg.cac_loai()[-1] == "loi_mo_hinh")
kiem("14. Lỗi mô hình KHÔNG bị nuốt thành câu trả lời rỗng",
     "ConnectionError" in bg.su_kien[-1].get("loai_loi", ""),
     bg.su_kien[-1].get("ly_do", "")[:60])

# ── Công cụ meta ────────────────────────────────────────────────────────
trinh, nhan, bp, dt = dung()
truoc = bp.so_cong_cu_phoi()
vl = VongLapTacNhan(nhan, mo_hinh_kich_ban(goi(TEN_CONG_CU_META, linh_vuc="kho"),
                                           goi("kho.doc_ton"),
                                           {"loai": "chu", "noi_dung": "xong"}), bp)
bg = vl.chay(dt, "xem tồn kho")
kiem("15. ★ Mô hình tự MỞ lĩnh vực rồi gọi được công cụ vừa hiện ra",
     trinh.dem.get("kho.doc_ton", 0) == 1 and bp.so_cong_cu_phoi() > truoc,
     "phơi {} → {}".format(truoc, bp.so_cong_cu_phoi()))

# ── LUẬT 7 ───────────────────────────────────────────────────────────────
nguon = open(os.path.join(GOC, "vong_lap.py"), encoding="utf-8").read()
than = "\n".join(d for d in nguon.split("\n") if not d.strip().startswith("#"))
kiem("16. ★ LUẬT 7 — vòng lặp KHÔNG tự kiểm quyền / đếm hạn mức / ghi nhật ký",
     "duoc_goi(" not in than and "kiem_va_ghi(" not in than
     and ".nhat_ky.ghi(" not in than,
     "làm lại việc của nhân là tạo ra mô hình quyền thứ hai")
kiem("17. ★ LUẬT 1 (cấu trúc) — vòng lặp chỉ chạm nhân qua .goi(",
     than.count(".goi(") >= 1 and "ban_khai.ham" not in than and ".ham(" not in than,
     "không có đường gọi thẳng hàm công cụ")

print("-" * 74)
print("  KET QUA: {}/{} DAT".format(dat, tong))
print("")
print("  NGHIA LA GI KHONG: bai nay do VONG LAP, khong do MO HINH. Mo hinh o")
print("  day la kich ban viet san. No KHONG noi gi ve viec mot mo hinh that co")
print("  chon dung cong cu hay khong — do do can GPU va mot bo do rieng.")
print("=" * 74)
sys.exit(0 if dat == tong else 1)
