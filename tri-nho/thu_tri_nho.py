#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""thu_tri_nho.py — khoá CÁCH LY GIỮA CÁC AGENT, và vài luật quy mô.

Điều quan trọng nhất tệp này đo: trí nhớ của người này KHÔNG lọt sang người
kia, ở MỌI đường đọc và MỌI đường xoá. Một nền tảng một-agent-một-người mà rò
chỗ ấy thì hỏng ở mức không sửa được bằng xin lỗi.

KHÔNG mạng, KHÔNG GPU, CSDL nằm trong bộ nhớ.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tri_nho import (  # noqa: E402
    TRAN_MAU_MOI_AGENT, KhoTriNho, LoiTriNho, kiem_ma_agent,
)

dat = 0
tong = 0


def kiem(ten, dk, ct=""):
    global dat, tong
    tong += 1
    # `ct` có thể là list/dict khi ca kiểm muốn in ra thứ nó vừa đo — ép về chuỗi
    # ở đây chứ không bắt từng ca tự nhớ, vì quên một chỗ là bài kiểm NỔ giữa
    # chừng và các ca sau không chạy, trông hệt như chúng đã đạt.
    print("  [{}] {}{}".format("DAT " if dk else "HONG", ten,
                               "  — " + str(ct) if ct else ""))
    if dk:
        dat += 1


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


print("=" * 74)
print("  TRI NHO RIENG TUNG AGENT — cach ly la dieu kien so mot")
print("=" * 74)

k = KhoTriNho()

# ── Tạo theo nhu cầu ─────────────────────────────────────────────────────
kiem("1. Kho mới thì KHÔNG có agent nào — không tạo sẵn 100 triệu bản rỗng",
     k.so_agent() == 0, "{} agent".format(k.so_agent()))

a = k.mo_agent("nguoi.an", persona="chủ doanh nghiệp xây dựng")
kiem("2. Agent ra đời đúng lúc người thật tới", a["moi"] is True and k.so_agent() == 1)

a2 = k.mo_agent("nguoi.an")
kiem("3. Mở lại KHÔNG tạo trùng", a2["moi"] is False and k.so_agent() == 1)

k.mo_agent("nguoi.binh", persona="kế toán")
kiem("4. Người thứ hai là agent thứ hai", k.so_agent() == 2)

# ── Ghi nhớ ──────────────────────────────────────────────────────────────
k.nho("nguoi.an", "Anh An đang tìm nhà thầu xây dựng ở Hà Nội", nhan="nhu-cau")
k.nho("nguoi.an", "Ngân sách khoảng 8 tỷ đồng cho dự án kho bãi", nhan="ngan-sach")
k.nho("nguoi.binh", "Chị Bình phụ trách quyết toán thuế quý 3", nhan="cong-viec")
k.nho("nguoi.binh", "Ngân sách phòng kế toán 200 triệu mỗi năm", nhan="ngan-sach")
kiem("5. Mỗi agent đếm đúng mẩu của mình",
     k.dem_mau("nguoi.an") == 2 and k.dem_mau("nguoi.binh") == 2)

# ── ★ CÁCH LY — nhóm ca quan trọng nhất ─────────────────────────────────
r = k.nho_lai("nguoi.an", "ngân sách")
kiem("6. ★ Nhớ lại CHỈ ra mẩu của chính mình",
     len(r) == 1 and "8 tỷ" in r[0]["noi_dung"],
     "{} kết quả: {}".format(len(r), [x["noi_dung"][:36] for x in r]))

r2 = k.nho_lai("nguoi.binh", "ngân sách")
kiem("7. ★ Cùng một từ khoá, người khác ra kết quả KHÁC HẲN",
     len(r2) == 1 and "kế toán" in r2[0]["noi_dung"],
     [x["noi_dung"][:36] for x in r2])

kiem("8. ★ Tìm bằng chính NỘI DUNG của người khác vẫn KHÔNG ra gì",
     k.nho_lai("nguoi.an", "quyết toán thuế quý 3") == [],
     "chuỗi ấy có thật trong kho, nhưng thuộc agent khác")

kiem("9. ★ Gõ trúng MÃ của người khác cũng không ra gì",
     k.nho_lai("nguoi.an", "nguoi.binh") == [],
     "ma_agent là cột UNINDEXED nên không lọt vào chỉ mục chữ")

kiem("10. ★ Danh sách gần đây cũng cách ly",
     all("Bình" not in x["noi_dung"] and "kế toán" not in x["noi_dung"]
         for x in k.gan_day("nguoi.an", 50)))

kiem("11. Agent chưa tồn tại thì nhớ lại ra rỗng, không nổ, không lộ",
     k.nho_lai("nguoi.chua.co", "ngân sách") == [])

# ── ★ CÁCH LY KHI XOÁ ───────────────────────────────────────────────────
id_binh = k.gan_day("nguoi.binh", 1)[0]["id"]
kiem("12. ★ KHÔNG xoá được mẩu của người khác dù biết đúng id",
     k.quen_mau("nguoi.an", id_binh) is False and k.dem_mau("nguoi.binh") == 2,
     "quyền sở hữu nằm TRONG câu lệnh xoá")

kiem("13. Xoá mẩu của chính mình thì được",
     k.quen_mau("nguoi.binh", id_binh) is True and k.dem_mau("nguoi.binh") == 1)

# ── Quyền rút lại ───────────────────────────────────────────────────────
n = k.quen_het("nguoi.an")
kiem("14. ★ Quên HẾT — quyền xoá dữ liệu theo NĐ 13/2023",
     n == 2 and k.dem_mau("nguoi.an") == 0 and k.nho_lai("nguoi.an", "ngân sách") == [])

kiem("15. Quên hết của người này KHÔNG chạm người kia", k.dem_mau("nguoi.binh") == 1)

k.xoa_agent("nguoi.an")
kiem("16. Xoá hẳn agent thì nó biến khỏi danh sách", k.so_agent() == 1)

# ── Đầu vào dị dạng ─────────────────────────────────────────────────────
for xau in ("", "Nguoi.HOA", "nguoi binh", "nguoi.an\n", None, 12345):
    nem(LoiTriNho, lambda x=xau: kiem_ma_agent(x),
        "17. Mã agent dị dạng bị từ chối: {!r}".format(xau))

k.mo_agent("nguoi.cuc")
nem(LoiTriNho, lambda: k.nho("nguoi.cuc", "   "), "18. Không ghi mẩu rỗng")
nem(LoiTriNho, lambda: k.nho("khong.ton.tai", "x"),
    "19. Ghi cho agent chưa tồn tại thì nổ, không âm thầm tạo")

# ── Cú pháp FTS5 trong câu hỏi của người dùng ───────────────────────────
k.nho("nguoi.cuc", 'Báo giá "trọn gói" cho nhà xưởng', nhan="bao-gia")
try:
    r = k.nho_lai("nguoi.cuc", 'giá "trọn gói" OR NEAR(')
    kiem("20. ★ Câu hỏi chứa cú pháp FTS5 KHÔNG làm nổ truy vấn",
         isinstance(r, list), "{} kết quả".format(len(r)))
except Exception as e:
    kiem("20. ★ Câu hỏi chứa cú pháp FTS5 KHÔNG làm nổ truy vấn", False,
         "{}: {}".format(type(e).__name__, e))

# ── Trần ─────────────────────────────────────────────────────────────────
kiem("21. Nội dung quá dài bị CẮT, không bị từ chối",
     len(k.gan_day("nguoi.cuc", 1) and
         k.nho("nguoi.cuc", "x" * 99_999) and
         k.gan_day("nguoi.cuc", 1)[0]["noi_dung"]) == 4_000)

# ── Quy mô: nhiều agent, tra vẫn đúng phạm vi ───────────────────────────
k2 = KhoTriNho()
for i in range(500):
    ma = "d.%04d" % i
    k2.mo_agent(ma)
    k2.nho(ma, "Doanh nghiệp số %d ở tỉnh Thái Nguyên cần vốn lưu động" % i)
r = k2.nho_lai("d.0042", "vốn lưu động Thái Nguyên", so_luong=50)
kiem("22. ★ 500 agent cùng một câu chữ — tra vẫn CHỈ ra của mình",
     len(r) == 1 and "số 42 " in r[0]["noi_dung"],
     "{} kết quả trong kho có 500 bản ghi gần như giống hệt".format(len(r)))

# ── ★ KHOÁ PHẠM VI KHÔNG ĐƯỢC THÀNH MỘT CỬA VÀO ────────────────────────
from tri_nho import TIEN_TO_PHAM_VI, khoa_pham_vi  # noqa: E402

k3 = KhoTriNho()
k3.mo_agent("nguoi.x"); k3.mo_agent("nguoi.y")
k3.nho("nguoi.x", "Hop dong xay dung 12 ty voi doi tac Nhat Ban")
k3.nho("nguoi.y", "Hop dong xay dung 12 ty voi doi tac Nhat Ban")

kb_x = khoa_pham_vi("nguoi.x")
r = k3.nho_lai("nguoi.y", kb_x + " hop dong xay dung")
kiem("23. ★ Gõ đúng KHOÁ PHẠM VI của người khác vẫn không đọc được của họ",
     len(r) == 1 and all(x["id"] not in
                         [m["id"] for m in k3.gan_day("nguoi.x", 50)] for x in r),
     "khoá phạm vi bị LỌC khỏi câu hỏi trước khi truy vấn")

kiem("24. ★ Khoá phạm vi có thật trong chỉ mục (nếu không, phép kiểm 23 vô nghĩa)",
     kb_x.startswith(TIEN_TO_PHAM_VI) and kb_x != khoa_pham_vi("nguoi.y"),
     "{} ≠ {}".format(kb_x, khoa_pham_vi("nguoi.y")))

kiem("25. Câu hỏi CHỈ gồm khoá phạm vi thì ra rỗng, không ra tất cả",
     k3.nho_lai("nguoi.y", kb_x) == [] and k3.nho_lai("nguoi.y", khoa_pham_vi("nguoi.y")) == [])

# Cấu trúc: khoá phạm vi phải nằm TRONG biểu thức MATCH, không chỉ ở WHERE.
import os as _os  # noqa: E402
_ng = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "tri_nho.py"),
           encoding="utf-8").read()
kiem("26. ★ Khoá phạm vi nằm TRONG biểu thức MATCH — đo được: 1.933 ms → 19,7 ms",
     "khoa_pham_vi(ma_agent)," in _ng and "mau_tim MATCH ? AND ma_agent = ?" in _ng,
     "và mệnh đề WHERE VẪN GIỮ: khoá để NHANH, WHERE để ĐÚNG")

# ── ★ PHÉP ĐO CÁCH LY PHẢI SO BẰNG ID, KHÔNG BẰNG CHỮ ──────────────────
#
#   Lỗi đã dính thật ngày 26/09/2026 khi đo trên 50.000 doanh nghiệp: phép
#   kiểm rò rỉ so NỘI DUNG của kết quả với nội dung mẩu của agent khác, và báo
#   "RÒ RỈ". Đo lại bằng ID thì 399/399 cặp sạch.
#   Lý do: hai doanh nghiệp cùng một xã có mẩu địa bàn TRÙNG CHỮ một cách hợp
#   lệ ("Trụ sở tại xã X, tỉnh Y"), và cùng nguồn thì mẩu nguồn cũng trùng.
#   Trùng chữ KHÔNG phải rò rỉ; rò rỉ là nhận được BẢN GHI của người khác.
#   Một phép đo không phân biệt được hai điều ấy sẽ báo động giả mãi, rồi tới
#   lúc người ta tắt nó đi — và khi ấy mới là lúc rò rỉ thật đi qua.
k4 = KhoTriNho()
for m in ("dn.a", "dn.b"):
    k4.mo_agent(m)
    k4.nho(m, "Trụ sở tại xã Phường Hoàn Kiếm, tỉnh/thành phố Hà Nội.", "dia-ban")

ma_b = k4.gan_day("dn.b", 9)
id_b = {x["id"] for x in ma_b}
kq = k4.nho_lai("dn.a", ma_b[0]["noi_dung"][:50], so_luong=9)

kiem("27. ★ Hai agent TRÙNG CHỮ vẫn không thấy bản ghi của nhau",
     len(kq) == 1 and not any(z["id"] in id_b for z in kq),
     "nhận {} kết quả, {} thuộc agent kia — so bằng ID, không bằng chữ"
     .format(len(kq), sum(1 for z in kq if z["id"] in id_b)))

kiem("28. Phép đo SO BẰNG CHỮ sẽ báo động giả ở đúng ca trên",
     any(z["noi_dung"] == ma_b[0]["noi_dung"] for z in kq),
     "chính vì vậy mà ca 27 phải so bằng ID")

# ── ★ GHI MỘT LẦN: chạy lại không nhân đôi ────────────────────────────
k5 = KhoTriNho()
k5.mo_agent("dn.c")
x1 = k5.nho_mot_lan("dn.c", "Công ty TNHH Xây dựng Thái Nguyên", "ten")
x2 = k5.nho_mot_lan("dn.c", "Công ty TNHH Xây dựng Thái Nguyên", "ten")
x3 = k5.nho_mot_lan("dn.c", "Trụ sở tại xã Phú Lương.", "dia-ban")
kiem("29. ★ nho_mot_lan: ghi lần đầu, BỎ QUA lần hai, vẫn ghi mẩu khác",
     x1 and x2 is None and x3 and k5.dem_mau("dn.c") == 2,
     "nạp 1,08 triệu bản ghi là việc hàng chục phút — nó SẼ phải chạy lại")

kiem("30. Ghi một lần vẫn CÁCH LY: agent khác ghi cùng nội dung thì vẫn ghi được",
     k5.mo_agent("dn.d") is not None
     and k5.nho_mot_lan("dn.d", "Công ty TNHH Xây dựng Thái Nguyên", "ten") is not None
     and k5.dem_mau("dn.d") == 1,
     "trùng nội dung với người khác không phải lý do từ chối")

print("-" * 74)
print("  KET QUA: {}/{} DAT".format(dat, tong))
print("")
print("  NGHIA LA GI KHONG: bai nay do CACH LY va VONG DOI tren SQLite trong bo")
print("  nho. No KHONG do hieu nang o 100 trieu agent, KHONG do Postgres, va")
print("  KHONG chung minh duoc chat luong truy hoi tieng Viet — BM25 tren")
print("  unicode61 khong tach tu tieng Viet, nen cum tu ghep se kem. Do cai do")
print("  can mot bo cau hoi that, chua co.")
print("=" * 74)
sys.exit(0 if dat == tong else 1)
