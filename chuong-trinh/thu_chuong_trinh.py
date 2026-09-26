#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""thu_chuong_trinh.py — khoá KHUNG CHƯƠNG TRÌNH và HỒ SƠ HỌC VẤN.

Hai thứ tệp này bảo vệ:
  1. Khung đúng Chương trình GDPT 2018 ở những chỗ DỄ CHÉP NHẦM theo tài liệu
     cũ — nhất là Lịch sử ở THPT, môn từng đổi từ lựa chọn sang bắt buộc.
  2. Hồ sơ học vấn TẤT ĐỊNH: cùng một mã agent luôn ra cùng một hồ sơ, trên mọi
     máy, mọi lần chạy. Mất tính ấy thì học vấn của một người đổi sau mỗi lần
     khởi động lại, và không ai thấy lúc nó bắt đầu đổi.

KHÔNG mạng, KHÔNG CSDL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from khung import (  # noqa: E402
    BAC_SAU_PT, CAP_HOC, MON, cap_theo_ma, mon_chuan_vn, mon_cua_cap, tong_ti_le_bac,
)
from ho_so import (  # noqa: E402
    LINH_VUC, ho_so_hoc_van, phan_bo, so_nganh_dai_dien,
)

dat = 0
tong = 0


def kiem(ten, dk, ct=""):
    global dat, tong
    tong += 1
    print("  [{}] {}{}".format("DAT " if dk else "HONG", ten, "  — " + str(ct) if ct else ""))
    if dk:
        dat += 1


print("=" * 74)
print("  KHUNG CHUONG TRINH GDPT 2018 + HO SO HOC VAN")
print("=" * 74)

# ── Khung ────────────────────────────────────────────────────────────────
kiem("1. Bốn cấp: mầm non → tiểu học → THCS → THPT",
     [c["ma"] for c in CAP_HOC] == ["mam-non", "tieu-hoc", "thcs", "thpt"])

kiem("2. Lớp phủ kín 1–12, không trùng không hụt",
     sorted(l for c in CAP_HOC for l in c["lop"]) == list(range(1, 13)))

# Ca này bảo vệ đúng chỗ dễ sai nhất của khung.
ls = [m for m in MON if m["ma"] == "pt-lich-su"]
kiem("3. ★ LỊCH SỬ là môn BẮT BUỘC ở THPT",
     len(ls) == 1 and ls[0]["bat_buoc"] is True,
     "điểm từng thay đổi; tài liệu cũ ghi là môn lựa chọn")

kiem("4. THPT có cả môn bắt buộc lẫn lựa chọn",
     len(mon_cua_cap("thpt", True)) < len(mon_cua_cap("thpt")),
     "{} bắt buộc / {} tổng".format(len(mon_cua_cap("thpt", True)), len(mon_cua_cap("thpt"))))

kiem("5. Ba cấp dưới THPT thì MỌI môn đều bắt buộc",
     all(len(mon_cua_cap(c, True)) == len(mon_cua_cap(c))
         for c in ("mam-non", "tieu-hoc", "thcs")))

kiem("6. Mã môn không trùng", len({m["ma"] for m in MON}) == len(MON), "{} môn".format(len(MON)))

kiem("7. Mọi môn đều thuộc một cấp CÓ THẬT",
     all(cap_theo_ma(m["cap"]) is not None for m in MON))

# ── Chuẩn Việt Nam — lý do tồn tại của mô hình ──────────────────────────
cvn = {m["ma"] for m in mon_chuan_vn()}
kiem("8. ★ Lịch sử, Địa lí, Toán đều nằm trong nhóm 'chuẩn Việt Nam'",
     {"pt-lich-su", "pt-dia-li", "pt-toan", "cs-lsdl", "th-lsdl", "th-toan", "cs-toan"} <= cvn,
     "đây là chỗ mô hình nước ngoài sai và người Việt nhận ra ngay")

kiem("9. Nhóm chuẩn-VN không phải là TẤT CẢ các môn",
     0 < len(cvn) < len(MON),
     "{} / {} môn — gắn cờ cho tất cả thì cờ ấy vô nghĩa".format(len(cvn), len(MON)))

# ── Bậc sau phổ thông ───────────────────────────────────────────────────
kiem("10. Tỉ lệ các bậc cộng lại đúng 1,0",
     abs(tong_ti_le_bac() - 1.0) < 1e-9, tong_ti_le_bac())

kiem("11. Có đủ cả thạc sĩ và tiến sĩ, và tiến sĩ hiếm hơn thạc sĩ",
     next(b for b in BAC_SAU_PT if b["ma"] == "tien-si")["ti_le"]
     < next(b for b in BAC_SAU_PT if b["ma"] == "thac-si")["ti_le"])

# ── Hồ sơ: TẤT ĐỊNH ─────────────────────────────────────────────────────
a = ho_so_hoc_van("nd.00000007")
b = ho_so_hoc_van("nd.00000007")
kiem("12. ★ Cùng mã agent → cùng hồ sơ, không đổi giữa hai lần gọi", a == b)

import subprocess  # noqa: E402
_ma = "nd.00000007"
_out = subprocess.run(
    [sys.executable, "-c",
     "import sys;sys.path.insert(0,%r);from ho_so import ho_so_hoc_van;"
     "print(ho_so_hoc_van(%r)['bac_sau_pho_thong']['ma'])"
     % (os.path.dirname(os.path.abspath(__file__)), _ma)],
    capture_output=True, text=True).stdout.strip()
kiem("13. ★ Tất định qua TIẾN TRÌNH KHÁC — không dùng hash() của Python",
     _out == a["bac_sau_pho_thong"]["ma"],
     "hash() đổi mỗi lần chạy; blake2b thì không. Tiến trình mới ra: {!r}".format(_out))

kiem("14. Hai agent khác nhau thì hồ sơ khác nhau",
     len({str(ho_so_hoc_van("nd.%08d" % i)) for i in range(200)}) > 100)

# ── Hồ sơ: mang nhãn SUY RA ─────────────────────────────────────────────
kiem("15. ★ Mọi hồ sơ mang nhãn suy_ra=True — bất biến số 3 của dự án",
     all(ho_so_hoc_van("nd.%08d" % i)["suy_ra"] is True for i in range(50)),
     "dữ liệu suy luận không được trích dẫn như đã xác minh")

# ── Hồ sơ: phân bố ──────────────────────────────────────────────────────
N = 20_000
pb = phan_bo(N)
lech = max(abs(pb["theo_bac"].get(x["ma"], 0) / N - x["ti_le"]) for x in BAC_SAU_PT)
kiem("16. ★ Phân bố bậc học khớp tỉ lệ đã đặt (lệch < 1%)",
     lech < 0.01, "lệch lớn nhất {:.3%} trên {:,} agent".format(lech, N))

kiem("17. Mọi lĩnh vực đều có người theo học, không lĩnh vực nào chết",
     len(pb["theo_linh_vuc"]) == len(LINH_VUC),
     "{} / {} lĩnh vực".format(len(pb["theo_linh_vuc"]), len(LINH_VUC)))

kiem("18. Ai 'hết phổ thông' thì KHÔNG có chuyên môn đại học",
     all("chuyen_mon" not in h for h in
         (ho_so_hoc_van("nd.%08d" % i) for i in range(500))
         if h["bac_sau_pho_thong"]["ma"] == "khong"))

kiem("19. Ai có bậc sau phổ thông thì PHẢI có ngành",
     all(h.get("chuyen_mon", {}).get("nganh") for h in
         (ho_so_hoc_van("nd.%08d" % i) for i in range(500))
         if h["bac_sau_pho_thong"]["ma"] != "khong"))

kiem("20. Tốt nghiệp đại học không thể sau năm mốc",
     all(h["chuyen_mon"]["nam_tot_nghiep"] <= 2026 for h in
         (ho_so_hoc_van("nd.%08d" % i) for i in range(500)) if "chuyen_mon" in h))

# ── Hồ sơ: KHÔNG TỐN BYTE NÀO ───────────────────────────────────────────
_ng = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ho_so.py"),
           encoding="utf-8").read()
kiem("21. ★ Sinh hồ sơ KHÔNG chạm CSDL và KHÔNG ghi tệp — nên 100 triệu = 0 byte",
     "sqlite" not in _ng and "open(" not in _ng.split('"""', 2)[2]
     and "INSERT" not in _ng.upper(),
     "hồ sơ chỉ ghi xuống khi NGƯỜI DÙNG tự sửa, và khi ấy nó thôi là suy luận")

# ── Ranh giới bản quyền phải được VIẾT RA ───────────────────────────────
_kh = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "khung.py"),
           encoding="utf-8").read()
kiem("22. ★ Tệp khung NÓI RÕ nó là cấu trúc công khai, không phải nội dung sách",
     "32/2018" in _kh and "bản quyền" in _kh and "viết mới" in _kh,
     "sách giáo khoa có bản quyền; chép vào ngữ liệu rồi phát hành mở là vi phạm")

print("-" * 74)
print("  KET QUA: {}/{} DAT".format(dat, tong))
print("")
print("  NGHIA LA GI KHONG: bai nay do CAU TRUC khung va tinh TAT DINH cua ho")
print("  so. No KHONG kiem duoc noi dung mon hoc co dung khong — cai do can")
print("  chuyen gia tung mon doc, khong phai mot phep kiem. Va no KHONG tao ra")
print("  mot chu nao cua ngu lieu: khung chi noi CAN VIET GI, chua viet.")
print("=" * 74)
sys.exit(0 if dat == tong else 1)
