#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vi_du_bo_nho.py — mot trinh dieu khien THAT, chay hoan toan trong bo nho.

=============================================================================
VI SAO CO TEP NAY
=============================================================================
Mot hop dong khong co ban mau chay duoc thi chi la mot bai van. Tep nay lam hai
viec, va chi hai viec:

  1. Cho NGUOI MOI mot thu chay duoc trong ba giay, khong can mang, khong can
     bien moi truong, khong can mot nen tang nao dang song:
         .venv/bin/python trinh-dieu-khien/vi_du_bo_nho.py
  2. Cho BAI TU KIEM mot doi tuong that de thu luat phan quyen: no co ca cong cu
     DOC lan cong cu GHI, nen thu duoc ca hai nhanh cua quyet dinh "mac dinh chi
     doc" ma khong cham vao he that.

DAY LA MOT TRINH DIEU KHIEN THAT, KHONG PHAI MOT BAN GIA. No di qua dung
`kiem_hop_dong()` nhu moi trinh dieu khien khac, dung dung `bat_dau_goi()` nhu
moi trinh dieu khien khac. Cai duy nhat khac la "nen tang" ma no phu trach nam
trong RAM cua chinh tien trinh nay.

GIOI HAN, KHAI THANG:
  - Du lieu SONG TRONG BO NHO va MAT khi tien trinh thoat. Khong ghi dia, khong
    ghi CSDL. Do la co y: mot vi du ma tu ghi ra dia se de lai rac tren may
    nguoi thu, va con mo ra mot cau hoi ghi vao dau — dung cau hoi khong nen co
    trong mot vi du.
  - KHONG khoa (lock). Neu nhan chay da luong va goi cung mot trinh dieu khien
    tu nhieu luong, cac loi goi ghi o day co the dam nhau. Voi mot vi du thi
    chap nhan duoc, VOI MOT TRINH DIEU KHIEN THAT THI KHONG — chuyen nay ghi ra
    day de khong ai chep nguyen mau nay roi tuong da xong.

=============================================================================
PHU THUOC
=============================================================================
Chi phu thuoc `hop_dong.py` nam cung thu muc. KHONG phu thuoc nhan (nhan chua
ton tai 26/09/2026), KHONG phu thuoc mang, KHONG phu thuoc thu vien ngoai.
"""

from __future__ import annotations

import importlib.util
import os
import sys

# =============================================================================
# NAP hop_dong.py
# =============================================================================
# Thu muc that ten la "trinh-dieu-khien" — gach ngang khong hop le trong ten
# mo-dun Python, nen khong `import` thang duoc khi chay tep nay truc tiep.
#
# BAY QUAN TRONG, DOC KY: phai nap duoi DUNG MOT ten trong sys.modules. Neu
# hop_dong.py bi nap hai lan duoi hai ten khac nhau thi trong tien trinh se co
# HAI lop TrinhDieuKhien khac nhau, va `isinstance(td, TrinhDieuKhien)` trong
# kiem_hop_dong() se tra ve False cho mot doi tuong hoan toan hop le. Loi ay rat
# kho doc, vi thong diep se noi "khong ke thua TrinhDieuKhien" trong khi ma
# nguon ro rang co ke thua. Khoa sys.modules o duoi la thu chan chuyen do.
_TEN_MODUN_HOP_DONG = "bdsg_trinh_dieu_khien_hop_dong"
_THU_MUC = os.path.dirname(os.path.abspath(__file__))


def _nap_hop_dong():
    if _TEN_MODUN_HOP_DONG in sys.modules:
        return sys.modules[_TEN_MODUN_HOP_DONG]
    duong_dan = os.path.join(_THU_MUC, "hop_dong.py")
    spec = importlib.util.spec_from_file_location(_TEN_MODUN_HOP_DONG, duong_dan)
    if spec is None or spec.loader is None:
        raise ImportError("khong nap duoc {}".format(duong_dan))
    mo_dun = importlib.util.module_from_spec(spec)
    # Dat vao sys.modules TRUOC khi exec_module, de mot lan nap long nhau khong
    # tao ra ban thu hai.
    sys.modules[_TEN_MODUN_HOP_DONG] = mo_dun
    spec.loader.exec_module(mo_dun)
    return mo_dun


hop_dong = _nap_hop_dong()

KhaiBaoCongCu = hop_dong.KhaiBaoCongCu
TrinhDieuKhien = hop_dong.TrinhDieuKhien
LoiCongCu = hop_dong.LoiCongCu


# =============================================================================
# TRINH DIEU KHIEN
# =============================================================================


class SoTayBoNho(TrinhDieuKhien):
    """Mot so tay ghi chu nam trong bo nho.

    "Nen tang" ma trinh dieu khien nay phu trach la mot tu dien Python. Chon mot
    linh vuc nham chan nhu vay la co y: nguoi doc phai thay duoc HINH DANG cua
    mot trinh dieu khien ma khong bi phan tam boi nghiep vu.

    Nam cong cu, chia dung theo quyet dinh 3:
        so-tay__liet_ke   DOC  (co y KHONG khai `ghi` — xem ghi chu ben duoi)
        so-tay__doc       DOC
        so-tay__tim       DOC
        so-tay__luu       GHI
        so-tay__xoa       GHI
    """

    ten = "so-tay"

    CONG_CU = (
        # ── CONG CU DOC ───────────────────────────────────────────────────
        # CO Y KHONG TRUYEN `ghi=False` o cong cu dau tien nay. Do la ca thu cho
        # luat "quen khai ghi thi duoc coi la CHI DOC", va bai tu kiem kiem dung
        # cong cu nay. Neu mac dinh bi doi thanh True thi phep kiem ay do.
        KhaiBaoCongCu(
            ten="so-tay__liet_ke",
            mo_ta="Liet ke khoa cua moi ghi chu dang co trong so tay.",
            tham_so={},
        ),
        KhaiBaoCongCu(
            ten="so-tay__doc",
            mo_ta="Doc noi dung mot ghi chu theo khoa.",
            tham_so={
                "khoa": {"kieu": "chuoi", "mo_ta": "Khoa cua ghi chu.",
                         "bat_buoc": True, "toi_da_ky_tu": 64},
            },
            ghi=False,
        ),
        KhaiBaoCongCu(
            ten="so-tay__tim",
            mo_ta="Tim cac ghi chu co chua mot chuoi con (khong phan biet hoa thuong).",
            tham_so={
                "chuoi": {"kieu": "chuoi", "mo_ta": "Chuoi can tim.",
                          "bat_buoc": True, "toi_da_ky_tu": 200},
                "toi_da": {"kieu": "so_nguyen", "mo_ta": "So ket qua toi da tra ve.",
                           "mac_dinh": 10},
            },
            ghi=False,
        ),
        # ── CONG CU GHI ───────────────────────────────────────────────────
        # Hai cong cu duoi day khai `ghi=True` TUONG MINH. Nhan se dinh tuyen
        # chung qua cong ghi rieng; trinh dieu khien khong biet va khong can biet
        # cong ay lam gi.
        KhaiBaoCongCu(
            ten="so-tay__luu",
            mo_ta="Luu (tao moi hoac ghi de) mot ghi chu.",
            tham_so={
                "khoa": {"kieu": "chuoi", "mo_ta": "Khoa cua ghi chu.",
                         "bat_buoc": True, "toi_da_ky_tu": 64},
                "noi_dung": {"kieu": "chuoi", "mo_ta": "Noi dung ghi chu.",
                             "bat_buoc": True, "toi_da_ky_tu": 2000},
            },
            ghi=True,
        ),
        KhaiBaoCongCu(
            ten="so-tay__xoa",
            mo_ta="Xoa mot ghi chu theo khoa.",
            tham_so={
                "khoa": {"kieu": "chuoi", "mo_ta": "Khoa cua ghi chu can xoa.",
                         "bat_buoc": True, "toi_da_ky_tu": 64},
            },
            ghi=True,
        ),
    )

    def __init__(self, chi_doc=hop_dong.MAC_DINH_CHI_DOC, ghi_chu_ban_dau=None):
        super(SoTayBoNho, self).__init__(chi_doc=chi_doc)
        # Sao chep tu dien dua vao, khong giu tham chieu: nguoi goi doi tu dien
        # cua ho sau nay thi khong duoc doi trang thai ben trong trinh dieu khien.
        self._ghi_chu = dict(ghi_chu_ban_dau or _GHI_CHU_MAU)

    # -- thuc thi ----------------------------------------------------------
    def goi(self, ten, tham_so):
        """Doi mot loi goi cong cu thanh mot thao tac tren tu dien trong bo nho.

        Ba dong duoi day la khuon chung cua MOI trinh dieu khien:
          1. bat_dau_goi()  -> kiem ton tai, kiem che do chi doc, kiem tham so
          2. dinh tuyen theo ten
          3. tra ve du lieu; that bai thi NEM LoiCongCu, khong tra ve dict gia
             vo thanh cong

        KHONG co dong nao xac thuc. KHONG co dong nao ghi nhat ky. KHONG co dong
        nao hoi "nguoi nay co duoc phep khong". Ba thu do o nhan (quyet dinh 2).
        """
        ts = self.bat_dau_goi(ten, tham_so)

        if ten == "so-tay__liet_ke":
            return {"khoa": sorted(self._ghi_chu), "so_luong": len(self._ghi_chu)}

        if ten == "so-tay__doc":
            khoa = ts["khoa"]
            if khoa not in self._ghi_chu:
                raise LoiCongCu(
                    "khong co ghi chu voi khoa '{}'".format(khoa), ma="khong_tim_thay")
            return {"khoa": khoa, "noi_dung": self._ghi_chu[khoa]}

        if ten == "so-tay__tim":
            can_tim = ts["chuoi"].lower()
            toi_da = ts["toi_da"]
            if toi_da <= 0:
                raise hop_dong.LoiThamSo("toi_da phai lon hon 0, nhan duoc {}".format(toi_da))
            khop = [k for k in sorted(self._ghi_chu)
                    if can_tim in k.lower() or can_tim in self._ghi_chu[k].lower()]
            # Tra ve ca tong so truoc khi cat, de nguoi goi biet minh dang nhin
            # mot phan chu khong phai toan bo. Cat ma khong noi la mot kieu
            # "hong ma khong bao".
            return {"tong_khop": len(khop), "tra_ve": khop[:toi_da], "bi_cat": len(khop) > toi_da}

        if ten == "so-tay__luu":
            khoa = ts["khoa"]
            da_co = khoa in self._ghi_chu
            self._ghi_chu[khoa] = ts["noi_dung"]
            return {"khoa": khoa, "viec": "ghi_de" if da_co else "tao_moi"}

        if ten == "so-tay__xoa":
            khoa = ts["khoa"]
            if khoa not in self._ghi_chu:
                raise LoiCongCu(
                    "khong co ghi chu voi khoa '{}'".format(khoa), ma="khong_tim_thay")
            del self._ghi_chu[khoa]
            return {"khoa": khoa, "viec": "da_xoa", "con_lai": len(self._ghi_chu)}

        # Khong bao gio toi day: bat_dau_goi() da nem LoiKhongCoCongCu cho ten la.
        # Van giu nhanh nay, vi neu mot nguoi them cong cu vao CONG_CU ma quen
        # them nhanh xu ly thi phai no ra o day — chu khong phai tra ve None va
        # de nhan tuong la "thanh cong, khong co du lieu".
        raise LoiCongCu(
            "cong cu '{}' co trong khai bao nhung chua co nhanh xu ly trong goi()"
            .format(ten), ma="thieu_nhanh_xu_ly")


# Du lieu mau. Khong chua du lieu that cua ai, khong chua bi mat.
_GHI_CHU_MAU = {
    "doc-truoc": "Trinh dieu khien khong tu xac thuc, khong tu ghi nhat ky, "
                 "khong tu quyet dinh quyen. Ba viec do o nhan.",
    "mac-dinh": "Cong cu quen khai `ghi` thi duoc coi la chi doc.",
}


# =============================================================================
# CHAY TRUC TIEP: ban trinh dien ngan
# =============================================================================


def _in(nhan_dong, gia_tri):
    print("  {:<38} {}".format(nhan_dong, gia_tri))


def main():
    print("=" * 78)
    print("VI DU TRINH DIEU KHIEN TRONG BO NHO — so-tay")
    print("=" * 78)

    # 1. Hop dong phai duyet truoc. Neu khong duyet thi khong co gi de trinh dien.
    tom_tat = hop_dong.kiem_hop_dong(SoTayBoNho())
    print()
    print("HOP DONG: DAT")
    _in("ten trinh dieu khien", tom_tat["ten"])
    _in("so cong cu", tom_tat["so_cong_cu"])
    _in("cong cu CHI DOC", ", ".join(tom_tat["cong_cu_doc"]))
    _in("cong cu GHI", ", ".join(tom_tat["cong_cu_ghi"]))

    # 2. Ban gan MAC DINH: chi doc.
    print()
    print("BAN GAN MAC DINH (chi_doc=True)")
    td = SoTayBoNho()
    _in("liet_ke", td.goi("so-tay__liet_ke", {}))
    _in("doc 'mac-dinh'", td.goi("so-tay__doc", {"khoa": "mac-dinh"})["noi_dung"][:48] + "...")
    _in("tim 'quyen'", td.goi("so-tay__tim", {"chuoi": "quyen"}))
    try:
        td.goi("so-tay__luu", {"khoa": "thu", "noi_dung": "x"})
        _in("luu (cong cu GHI)", "!! KHONG BI CHAN — day la loi")
        return 1
    except hop_dong.LoiChiDoc as e:
        _in("luu (cong cu GHI)", "bi chan dung nhu mong doi")
        print("      -> {}".format(e))

    # 3. Ban gan cho ghi TUONG MINH.
    print()
    print("BAN GAN CHO GHI (chi_doc=False) — phai khai tuong minh")
    td_ghi = SoTayBoNho(chi_doc=False)
    _in("luu 'nhac-viec'", td_ghi.goi("so-tay__luu",
                                      {"khoa": "nhac-viec", "noi_dung": "Viet trinh dieu khien thu ba."}))
    _in("liet_ke", td_ghi.goi("so-tay__liet_ke", {}))
    _in("xoa 'nhac-viec'", td_ghi.goi("so-tay__xoa", {"khoa": "nhac-viec"}))

    # 4. Tham so sai bi TU CHOI, khong duoc doan mo.
    print()
    print("THAM SO SAI BI TU CHOI (khong ep kieu, khong bo qua khoa la)")
    for mo_ta_ca, ten_cc, ts in (
        ("thieu tham so bat buoc", "so-tay__doc", {}),
        ("sai kieu (chuoi cho so nguyen)", "so-tay__tim", {"chuoi": "a", "toi_da": "10"}),
        ("khoa la (go nham ten tham so)", "so-tay__doc", {"khoaa": "mac-dinh"}),
        ("cong cu khong ton tai", "so-tay__nuot-chung", {}),
    ):
        try:
            td.goi(ten_cc, ts)
            _in(mo_ta_ca, "!! KHONG BI CHAN — day la loi")
            return 1
        except hop_dong.LoiCongCu as e:
            _in(mo_ta_ca, "{} ({})".format(type(e).__name__, e.ma))

    # 5. Danh sach dang MCP — thu ma nhan se dua ra cho mo hinh.
    print()
    print("DANH SACH DANG MCP (nhan se dua ra cho mo hinh)")
    for muc in td.danh_sach_mcp():
        print("  {:<20} ghi={:<5} tham so: {}".format(
            muc["name"], str(muc["ghi"]),
            ", ".join(sorted(muc["inputSchema"]["properties"])) or "(khong co)"))

    print()
    print("=" * 78)
    print("XONG. Moi thu tren day chay trong bo nho, khong cham mang, khong cham dia.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
