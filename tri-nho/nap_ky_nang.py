#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nap_ky_nang.py — nạp KỸ NĂNG của agent từ 200 tin tuyển dụng.

=============================================================================
NGUỒN: /expert — VÀ TRANG ẤY Ở LẠI
=============================================================================
200 tin tuyển dụng trên bdsg.vn/expert mô tả đúng thứ một agent cần biết làm:
`trach_nhiem` (làm những việc gì) và `yeu_cau` (phải biết những gì). Cả hai là
DANH SÁCH, không phải một khối văn xuôi — nên tách được thành từng kỹ năng rời.

Trang /expert KHÔNG bị gỡ. Đo 26/09/2026: nó có 202 URL đang nằm trong
sitemap-chinh.xml và 200 tin tuyển dụng đang chạy. Đây là một phép SAO CHÉP
tri thức sang agent, không phải một cuộc di dời.

=============================================================================
MỖI KỸ NĂNG LÀ MỘT MẨU RIÊNG
=============================================================================
Không gộp cả danh sách vào một mẩu. Truy hồi ở đây là BM25 trên chữ: một mẩu
dài 15 gạch đầu dòng thì mọi câu hỏi đều khớp nó lờ mờ, còn một mẩu đúng một
việc thì khớp sắc. Đổi lại kho to hơn — 200 agent × ~12 mẩu thay vì × 2. Ở quy
mô này (đã đo 4,3 triệu mẩu chạy 55 ms) cái giá ấy không đáng kể.

Nối agent qua KHOÁ NGOẠI `DichVuChuDe.agent`, không đoán theo tên: đo được
200/200 tin khớp bằng khoá ngoại, trong khi đoán theo tên dịch vụ chỉ trúng
252/359 agent — và một lần đoán sai nghĩa là gán kỹ năng của người này cho
người khác.
"""
import csv
import os
import sys
from typing import Any, Dict, Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tri_nho import KhoTriNho, kiem_ma_agent  # noqa: E402

TIEN_TO = "ag."
TRAN_MOT_MAU = 600      # ký tự; một "kỹ năng" dài hơn thế là một đoạn văn bị dán nhầm


def ma_agent_cua(ma: str) -> str:
    sach = "".join(c if c.isalnum() else "-" for c in str(ma).strip().lower())
    return kiem_ma_agent(TIEN_TO + (sach or "0"))


def _tach(o: str) -> Iterable[str]:
    """Tách danh sách đã nối bằng ' | ' lúc kết xuất, bỏ mẩu rỗng và mẩu quá dài."""
    for x in (o or "").split(" | "):
        x = x.strip(" -•\t")
        if 8 <= len(x) <= TRAN_MOT_MAU:
            yield x


def mau_cua(h: Dict[str, str]) -> Iterable:
    dv = (h.get("dich_vu") or "").strip()
    ten = (h.get("ten") or "").strip()
    if ten:
        yield ("vai-tro", "Vai trò: %s." % ten)
    if dv:
        yield ("dich-vu", "Dịch vụ phụ trách: %s." % dv)
    kn = (h.get("nam_kn") or "").strip()
    if kn:
        yield ("kinh-nghiem", "Yêu cầu tối thiểu %s năm kinh nghiệm trong %s." % (kn, dv or ten))
    for x in _tach(h.get("trach_nhiem", "")):
        yield ("trach-nhiem", "Làm được: %s" % x)
    for x in _tach(h.get("yeu_cau", "")):
        yield ("ky-nang", "Biết làm: %s" % x)


def nap(kho: KhoTriNho, dong: Iterable[Dict[str, str]],
        gioi_han: Optional[int] = None) -> Dict[str, Any]:
    tk = {"vi_tri": 0, "khong_co_agent": 0, "agent_moi": 0,
          "mau_moi": 0, "mau_bo_qua": 0, "hang_hong": 0}
    for h in dong:
        if gioi_han is not None and tk["vi_tri"] >= gioi_han:
            break
        ma_ag = (h.get("agent_ma") or "").strip()
        if not ma_ag:
            # KHÔNG đoán một agent nào đó. Một kỹ năng gán nhầm người thì im
            # lặng sai mãi — tra cứu vẫn ra kết quả, chỉ là kết quả của người khác.
            tk["khong_co_agent"] += 1
            continue
        try:
            ma = ma_agent_cua(ma_ag)
        except Exception:
            tk["hang_hong"] += 1
            continue
        a = kho.mo_agent(ma, persona=(h.get("ten") or "").strip()[:200])
        if a["moi"]:
            tk["agent_moi"] += 1
        for nhan, noi in mau_cua(h):
            if kho.nho_mot_lan(ma, noi, nhan) is None:
                tk["mau_bo_qua"] += 1
            else:
                tk["mau_moi"] += 1
        tk["vi_tri"] += 1
    kho.db.commit()
    return tk


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--csdl", required=True)
    p.add_argument("--gioi-han", type=int, default=None)
    a = p.parse_args()
    kho = KhoTriNho(a.csdl)
    tk = nap(kho, csv.DictReader(sys.stdin), gioi_han=a.gioi_han)
    print("")
    print("  ── KẾT QUẢ ──")
    for k, v in tk.items():
        print("    %-18s %s" % (k, format(v, ",") if isinstance(v, int) else v))
    print("    %-18s %s" % ("tổng agent trong kho", format(kho.so_agent(), ",")))
