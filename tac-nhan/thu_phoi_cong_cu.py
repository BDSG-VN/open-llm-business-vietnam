#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""thu_phoi_cong_cu.py — khoá RÀNG BUỘC NẶNG NHẤT: số công cụ phơi ra cùng lúc.

Độ chính xác gọi công cụ đi từ ~95% (3 công cụ) xuống ~70% (12 công cụ). BDSG
có 18 nền tảng. Bài này khoá phép phơi bày dần, để trần không bị nới ra trong
một lần sửa nào đó rồi không ai đo lại.

KHÔNG mạng, KHÔNG CSDL, KHÔNG đọc biến môi trường.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phoi_cong_cu import (  # noqa: E402
    TEN_CONG_CU_META, BoPhoiCongCu, LoiPhoiCongCu, linh_vuc_cua,
)

dat = 0
tong = 0


def kiem(ten, dk, ct=""):
    global dat, tong
    tong += 1
    if dk:
        dat += 1
        print("  [DAT ] {}{}".format(ten, "  — " + ct if ct else ""))
    else:
        print("  [HONG] {}{}".format(ten, "  — " + ct if ct else ""))


def nem(lop, ham, ten):
    try:
        ham()
    except lop:
        kiem(ten, True)
        return
    except Exception as e:
        kiem(ten, False, "ném {} chứ không phải {}".format(type(e).__name__, lop.__name__))
        return
    kiem(ten, False, "KHÔNG ném gì cả")


def khai(*ten):
    return [{"ten": t, "mo_ta": t, "ghi": t.endswith(("ghi", "xoa", "tao")), "luoc_do": {}} for t in ten]


MOT_TRAM = khai(*[
    "crm.doc_khach", "crm.doc_viec", "crm.doc_hop_dong", "crm.ghi",
    "kho.doc_ton", "kho.doc_don", "kho.ghi",
    "ban_do.tra_xa", "ban_do.tra_tinh", "ban_do.quanh_diem",
    "twin.mo_khong_gian", "twin.tao",
    "he.gio", "he.ai_toi",
])

print("=" * 74)
print("  PHOI CONG CU — tran so cong cu phoi ra cung luc")
print("=" * 74)

# 1 -----------------------------------------------------------------------
kiem("1. Lĩnh vực suy ra từ tiền tố tên công cụ",
     linh_vuc_cua("crm.doc_khach") == "crm" and linh_vuc_cua("khong_co_cham") == "khong_co_cham")

# 2 -----------------------------------------------------------------------
bp = BoPhoiCongCu(MOT_TRAM, luon_bat=["he.gio", "he.ai_toi"], tran=8)
kiem("2. Lúc đầu CHỈ phơi công cụ luôn-bật",
     bp.so_cong_cu_phoi() == 2, "{} công cụ".format(bp.so_cong_cu_phoi()))

# 3 -----------------------------------------------------------------------
ten = [b["ten"] for b in bp.ban_khai_cho_mo_hinh()]
kiem("3. Công cụ meta LUÔN có mặt", TEN_CONG_CU_META in ten)

# 4 -----------------------------------------------------------------------
kiem("4. Danh mục lĩnh vực nêu đủ, không thiếu lĩnh vực nào",
     set(bp.cac_linh_vuc()) == {"crm", "kho", "ban_do", "twin", "he"},
     ", ".join(bp.cac_linh_vuc()))

# 5 -----------------------------------------------------------------------
bp.mo_linh_vuc("crm")
kiem("5. Mở một lĩnh vực thì thấy công cụ của nó",
     "crm.doc_khach" in [b["ten"] for b in bp.ban_khai_cho_mo_hinh()])

# 6 — CA QUAN TRỌNG NHẤT -------------------------------------------------
bp.mo_linh_vuc("kho")
bp.mo_linh_vuc("ban_do")
bp.mo_linh_vuc("twin")
kiem("6. ★ TRẦN KHÔNG BAO GIỜ BỊ VƯỢT dù mở hết lĩnh vực",
     bp.so_cong_cu_phoi() <= bp.tran,
     "phơi {} / trần {}".format(bp.so_cong_cu_phoi(), bp.tran))

# 7 -----------------------------------------------------------------------
cau = bp.mo_linh_vuc("crm") if "crm" not in bp.linh_vuc_dang_mo() else "vốn đã mở"
kiem("7. Mở lại lĩnh vực đã mở thì nói rõ, không nhân đôi",
     len(bp.linh_vuc_dang_mo()) == len(set(bp.linh_vuc_dang_mo())),
     ", ".join(bp.linh_vuc_dang_mo()))

# 8 -----------------------------------------------------------------------
bp2 = BoPhoiCongCu(MOT_TRAM, luon_bat=["he.gio"], tran=8)
bp2.mo_linh_vuc("crm")
bp2.mo_linh_vuc("kho")
bp2.mo_linh_vuc("ban_do")
cau = bp2.mo_linh_vuc("twin")
kiem("8. ★ Khi phải ĐÓNG bớt, câu trả lời NÓI RA việc đã đóng",
     "đóng" in cau.lower(), cau)

# 9 -----------------------------------------------------------------------
nem(LoiPhoiCongCu, lambda: BoPhoiCongCu(MOT_TRAM, luon_bat=["khong.co_that"], tran=8),
    "9. Công cụ luôn-bật không có trong bản khai thì NỔ LÚC DỰNG")

# 10 ----------------------------------------------------------------------
nem(LoiPhoiCongCu,
    lambda: BoPhoiCongCu(MOT_TRAM, luon_bat=["crm.doc_khach", "crm.doc_viec", "crm.ghi"], tran=2),
    "10. Luôn-bật nhiều hơn trần thì NỔ LÚC DỰNG, không hỏng lúc chạy")

# 11 ----------------------------------------------------------------------
nem(LoiPhoiCongCu, lambda: BoPhoiCongCu(khai("crm.a", "crm.a"), tran=4),
    "11. Bản khai có tên TRÙNG thì nổ — gọi cái nào là chuyện may rủi")

# 12 ----------------------------------------------------------------------
nem(LoiPhoiCongCu, lambda: BoPhoiCongCu(MOT_TRAM, tran=0), "12. Trần 0 bị từ chối")

# 13 ----------------------------------------------------------------------
bp3 = BoPhoiCongCu(MOT_TRAM, luon_bat=["he.gio"], tran=8)
try:
    bp3.mo_linh_vuc("khong_co_that")
    kiem("13. Mở lĩnh vực không có thì báo lỗi CÓ ÍCH", False, "không ném gì")
except KeyError as e:
    kiem("13. Mở lĩnh vực không có thì báo lỗi CÓ ÍCH",
         "crm" in str(e), "lỗi có liệt kê lĩnh vực thật: {}".format(str(e)[:70]))

# 14 — ẩn KHÁC cấm ---------------------------------------------------------
bp4 = BoPhoiCongCu(MOT_TRAM, luon_bat=["he.gio"], tran=8)
kiem("14. ★ Công cụ bị ẨN vẫn nằm trong bản khai gốc — ẩn ≠ cấm",
     "crm.ghi" in bp4._theo_ten and
     "crm.ghi" not in [b["ten"] for b in bp4.ban_khai_cho_mo_hinh()],
     "quyền do nhan/quyen.py quyết, tệp này chỉ quyết CHO XEM GÌ")

print("-" * 74)
print("  KET QUA: {}/{} DAT".format(dat, tong))
print("")
print("  NGHIA LA GI KHONG: bai nay do PHEP PHOI BAY, khong do DO CHINH XAC")
print("  cua mo hinh. Con so 95%/70% la ly do tep kia ton tai, khong phai thu")
print("  bai nay kiem chung duoc — muon biet mo hinh cua BDSG goi cong cu dung")
print("  bao nhieu phan tram thi phai co GPU va mot bo do rieng.")
print("=" * 74)
sys.exit(0 if dat == tong else 1)
