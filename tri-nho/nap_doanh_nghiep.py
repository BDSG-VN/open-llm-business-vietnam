#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nap_doanh_nghiep.py — nạp mỗi doanh nghiệp thành MỘT agent có trí nhớ.

=============================================================================
ĐỌC TSV TỪ ĐẦU VÀO CHUẨN, KHÔNG TỰ NỐI CSDL
=============================================================================
Cố ý tách khỏi CSDL. Ba cái lợi, và cái thứ ba mới là lý do chính:
  · kiểm được bằng vài dòng TSV viết tay, không cần dựng Postgres;
  · `psql` bơm thẳng vào được, nhanh hơn mọi trình điều khiển Python;
  · bộ nạp KHÔNG cần khoá CSDL, nên không có khoá nào để lỡ ghi vào mã.

Cột mong đợi (có tiêu đề):  id, ten, ten_tinh, ten_xa, ma_tinh, ma_xa, nguon

=============================================================================
HAI TÍNH CHẤT PHẢI CÓ, vì 1,08 triệu bản ghi là việc hàng chục phút
=============================================================================
1. CHẠY LẠI ĐƯỢC MÀ KHÔNG NHÂN ĐÔI. Dùng `nho_mot_lan()`. Không có nó thì chạy
   lại lần hai là mỗi agent có hai mẩu y hệt; truy hồi trả kết quả trùng, mà
   tra cứu vẫn "có kết quả" nên không ai thấy lúc nó bắt đầu sai.
2. BÁO TIẾN ĐỘ VÀ GHI CHỖ DỪNG. Việc đứt giữa chừng là chuyện bình thường;
   không biết nó dừng ở đâu mới là vấn đề.

=============================================================================
MỘT AGENT NHỚ GÌ LÚC MỚI SINH
=============================================================================
Bốn mẩu, mỗi mẩu một loại sự kiện, tách rời để truy hồi bắt trúng:
  ten      — tên doanh nghiệp (thứ người ta gõ khi tìm)
  dia-ban  — tỉnh và xã bằng CHỮ, không bằng mã (mã không ai gõ)
  hanh-chinh — mã tỉnh/xã, để khớp chính xác khi cần
  nguon    — dữ liệu này ở đâu ra (bất biến 6)

KHÔNG có mẩu nào chứa tên người. Dữ liệu nguồn không có, và kể cả có thì một
agent mang tên người thật là mạo danh — xem phần cuối README của kho.
"""
import csv
import os
import sys
import time
from typing import Any, Dict, Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tri_nho import KhoTriNho, kiem_ma_agent  # noqa: E402

TIEN_TO = "dn."   # mặc định; đổi bằng --tien-to cho loại thực thể khác


def ma_agent_cua(ma_dn: str, tien_to: str = TIEN_TO) -> str:
    """Mã agent từ id thực thể. Chữ thường, chỉ số và dấu — hợp mẫu của kho.

    Tiền tố tách các HỌ thực thể ra khỏi nhau: `dn.` cho doanh nghiệp, `da.`
    cho dự án. Không có nó thì doanh nghiệp id 89 và dự án id 89 thành CÙNG
    một agent, và trí nhớ của hai thứ khác hẳn nhau trộn vào nhau — một kiểu
    rò rỉ không ai nghĩ tới vì nó không đi qua phép kiểm quyền nào.
    """
    sach = "".join(c if c.isalnum() else "-" for c in str(ma_dn).strip().lower())
    return kiem_ma_agent(tien_to + (sach or "0"))


def mau_cua(hang: Dict[str, str]) -> Iterable:
    ten = (hang.get("ten") or "").strip()
    if ten:
        yield ("ten", ten)
    tinh = (hang.get("ten_tinh") or "").strip()
    xa = (hang.get("ten_xa") or "").strip()
    if tinh or xa:
        # Viết thành CÂU, không thành cặp khoá-giá trị: truy hồi ở đây là BM25
        # trên chữ, nên "Trụ sở tại xã X, tỉnh Y" khớp được câu hỏi tự nhiên,
        # còn "ten_tinh=Y" thì không khớp gì cả.
        yield ("dia-ban", "Trụ sở tại %s%s%s." % (
            ("xã " + xa) if xa else "",
            ", " if (xa and tinh) else "",
            ("tỉnh/thành phố " + tinh) if tinh else ""))
    mt, mx = (hang.get("ma_tinh") or "").strip(), (hang.get("ma_xa") or "").strip()
    if mt or mx:
        yield ("hanh-chinh", "Mã hành chính: tỉnh %s, xã %s." % (mt or "—", mx or "—"))
    # Địa chỉ dạng văn xuôi — dùng cho thực thể không có mã hành chính, ví dụ
    # 5.683 dự án bất động sản: cột `province_id` của chúng RỖNG HOÀN TOÀN
    # (đo 0/5.683), nhưng chuỗi địa chỉ thì có ở 89,5 % bản ghi. Không bịa mã
    # tỉnh từ chuỗi ấy — để nguyên văn cho BM25 khớp.
    dc = (hang.get("dia_chi") or "").strip()
    if dc:
        yield ("dia-chi", "Địa chỉ: %s" % dc)
    tt = (hang.get("trang_thai") or "").strip()
    if tt:
        yield ("trang-thai", "Trạng thái: %s." % tt)
    ng = (hang.get("nguon") or "").strip()
    if ng:
        yield ("nguon", "Nguồn dữ liệu: %s." % ng)


def nap(kho: KhoTriNho, dong: Iterable[Dict[str, str]],
        in_moi: int = 20_000, gioi_han: Optional[int] = None,
        tien_to: str = TIEN_TO) -> Dict[str, Any]:
    tk = {"dn": 0, "agent_moi": 0, "mau_moi": 0, "mau_bo_qua": 0, "hang_hong": 0}
    t0 = time.time()
    kho.db.execute("PRAGMA synchronous=OFF")
    for hang in dong:
        if gioi_han is not None and tk["dn"] >= gioi_han:
            break
        try:
            ma_dn = (hang.get("id") or "").strip()
            if not ma_dn:
                tk["hang_hong"] += 1
                continue
            ma = ma_agent_cua(ma_dn, tien_to)
        except Exception:
            tk["hang_hong"] += 1
            continue
        a = kho.mo_agent(ma, persona=(hang.get("ten") or "").strip()[:200])
        if a["moi"]:
            tk["agent_moi"] += 1
        for nhan, noi in mau_cua(hang):
            if kho.nho_mot_lan(ma, noi, nhan) is None:
                tk["mau_bo_qua"] += 1
            else:
                tk["mau_moi"] += 1
        tk["dn"] += 1
        if tk["dn"] % in_moi == 0:
            g = time.time() - t0
            print("    …%s doanh nghiệp · %.0fs · %.0f/giây" % (
                format(tk["dn"], ","), g, tk["dn"] / max(g, 1e-9)), flush=True)
    kho.db.commit()
    tk["giay"] = time.time() - t0
    tk["moi_giay"] = tk["dn"] / max(tk["giay"], 1e-9)
    return tk


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--csdl", required=True, help="tệp SQLite chứa kho trí nhớ")
    p.add_argument("--gioi-han", type=int, default=None)
    p.add_argument("--phan-cach", default=",", help="mặc định ',' (psql --csv)")
    p.add_argument("--tien-to", default=TIEN_TO, help="dn. cho doanh nghiệp, da. cho dự án")
    a = p.parse_args()
    kho = KhoTriNho(a.csdl)
    # Mặc định CSV, KHÔNG phải TSV. Lý do đã trả giá: truyền `-F$"\t"` cho psql
    # qua nhiều lớp nháy của ssh thì nó thành hai ký tự `\` và `t` viết thẳng,
    # không phải một tab. Cả 50.000 hàng vào bộ nạp thành MỘT trường, và bộ nạp
    # báo "50.000 hàng hỏng" — đúng, nhưng lý do thật nằm ở lớp vỏ shell.
    # `psql --csv` thì tự lo trích dẫn, không có gì để gõ nhầm.
    doc = csv.DictReader(sys.stdin, delimiter=a.phan_cach)
    tk = nap(kho, doc, gioi_han=a.gioi_han, tien_to=a.tien_to)
    print("")
    print("  ── KẾT QUẢ ──")
    for k, v in tk.items():
        print("    %-14s %s" % (k, format(v, ",") if isinstance(v, int) else round(v, 2)))
    print("    %-14s %s" % ("tổng agent", format(kho.so_agent(), ",")))
    if os.path.exists(a.csdl):
        print("    %-14s %.1f MB" % ("dung lượng", os.path.getsize(a.csdl) / 1e6))
