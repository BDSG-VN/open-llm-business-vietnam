#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cong/khong-du-lieu-cam.py — CỔNG 3/4: chặn dữ liệu KHÔNG được phát hành.

VÌ SAO CỔNG NÀY TỒN TẠI
  Không phải dữ liệu nào chạy được cũng phát hành được. Bốn loại bị cấm vì bốn lý do khác
  nhau, và trộn chúng lại là cách nhanh nhất để quên mất lý do:
    a) Dữ liệu KHÁCH HÀNG (lớp CRM đã định vị): là dữ liệu cá nhân/kinh doanh của người
       khác, không phải của dự án. Đo 25/09/2026: 1.079.991 bản ghi, 100% mang một giá trị
       nguồn duy nhất là dấu vết ETL từ CRM. Bảng ấy còn KHÔNG có cột ngành nghề, KHÔNG có
       cột sản phẩm — nghĩa là kể cả muốn dùng cho mục đích "danh bạ ngành nghề" cũng
       không dùng được. Cấm vì quyền riêng tư, và cấm luôn vì vô dụng cho việc này.
    b) Tài liệu có CẤP PHÉP BÊN THỨ BA: đo 25/09/2026, 118/118 tệp kho tri thức đều mang
       một dòng cấp phép của pháp nhân khác. Ta không có quyền phát hành lại.
    c) Nội dung của NGƯỜI KHÁC: văn quảng cáo người bán (OCOP, 1.727 sản phẩm), bài toà
       soạn (tin tức), bài người dùng đăng trên nền tảng. Bản quyền không thuộc dự án.
    d) Đầu ra MÁY SINH qua cổng LLM bên thứ ba: 116 đoạn não agent + 5.939 đoạn bài đăng
       bất động sản. Điều khoản nhà cung cấp thường cấm dùng đầu ra để huấn luyện mô hình
       cạnh tranh. Thêm nữa, 3.601 não agent là cấu hình thương mại của BDSG.

  Ngữ liệu ĐƯỢC phát hành, sau khi loại 2 nguồn máy sinh, đo 25/09/2026:
    11.733 đoạn · 7.509.969 ký tự · 7,16 MB, gồm đúng ba nguồn NGỮ LIỆU (ba mục đầu của
    NGUON_DUOC_PHEP; các mục sau là lớp có cấu trúc và bộ đề, không tính vào con số này).

PHẠM VI TỰ KHAI
  1. LUẬT CẤU TRÚC (fail-closed): mọi tệp .jsonl/.ndjson/.csv/.tsv, và .json nằm trong thư
     mục dữ liệu đã khai, phải chứng minh từng bản ghi có trường 'nguon' thuộc danh sách
     cho phép. Thiếu trường 'nguon' cũng là HỎNG — không phải vì nó chắc chắn bẩn, mà vì
     nó KHÔNG CHỨNG MINH ĐƯỢC là sạch. Cổng này không đoán hộ.
  2. LUẬT DẤU HIỆU: quét chuỗi đặc trưng của nguồn bị cấm.
     - Trong tệp DỮ LIỆU: mọi dấu hiệu (mạnh và yếu) đều là HỎNG.
     - Trong tài liệu và mã: chỉ HỎNG khi dòng vừa mang dấu hiệu mạnh VỪA CÓ HÌNH DẠNG
       BẢN GHI (mảnh JSON đối tượng, toạ độ WKT, hàng phân cách bằng tab).

     ĐÂY LÀ LUẬT QUAN TRỌNG NHẤT CỦA CỔNG NÀY, VÀ NÓ ĐƯỢC SỬA SAU MỘT PHÉP ĐO THẬT:
     bản đầu quét dấu hiệu mạnh trên MỌI tệp văn bản, chạy ngày 25/09/2026 thì bắt 15 chỗ
     trong MODEL-CARD.md, README.md và bo-du-lieu/README.md — toàn bộ đều là bảng liệt kê
     "những nguồn KHÔNG phát hành và vì sao". Tức là cổng đang cắn đúng vào phần tử tế nhất
     của bản phát hành: phần nói KHÔNG. Một cổng phạt người viết vì họ ghi rõ mình đã loại
     cái gì là cổng dạy người ta viết tài liệu mập mờ.
     Ranh giới đúng không nằm ở CHUỖI mà ở HÌNH DẠNG: "đã loại nguồn X vì Y" là tài liệu;
     một bản ghi của nguồn X dán vào giữa tài liệu mới là rò rỉ.
  KHÔNG có miễn trừ nội dòng. Đây là cổng tuyệt đối, như cổng bí mật: dữ liệu của người
  khác thì không có lý do kỹ thuật nào biến nó thành của mình.

MÃ THOÁT: 0 sạch · 1 có vi phạm · 2 cổng tự vỡ (fail-closed).
Đo lần đầu: 25/09/2026.
"""

import argparse
import csv
import json
import os
import re
import sys
import tempfile

BO_QUA_THU_MUC = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"}

DUOI_DU_LIEU_DONG = {".jsonl", ".ndjson"}
DUOI_DU_LIEU_BANG = {".csv", ".tsv"}
DUOI_VAN_BAN_KHAC = {".json", ".txt", ".md", ".py", ".sh", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sql"}

# Thư mục dữ liệu đã khai: .json nằm trong đây phải theo luật cấu trúc.
# .json ngoài đây được coi là CẤU HÌNH (ví dụ huan-luyen/cau-hinh) — vẫn bị quét dấu hiệu
# mạnh, chỉ không bị đòi trường 'nguon', vì cấu hình không phải bản ghi ngữ liệu.
THU_MUC_DU_LIEU = ("bo-du-lieu", os.path.join("huan-luyen", "du-lieu"), os.path.join("danh-gia", "bo-de"))

# ── Nguồn được phép, kèm số đo ngày 25/09/2026 ────────────────────────────────
NGUON_DUOC_PHEP = {
    "ho-so-niem-yet": "5.192 đoạn · 4,20 MB. Lưu ý: 110/5.192 đoạn (2,1%) dính rác cào web "
                      "(menu/CSS/JS/URL ngoài) — lọc được, không phải bỏ nguồn.",
    "ho-so-dn": "6.434 đoạn · 2,83 MB.",
    "wiki-crm": "107 đoạn · 0,13 MB.",
    # Bộ đề đánh giá KHÔNG phải ngữ liệu, nhưng luật cấu trúc fail-closed không miễn trừ
    # theo thư mục: mọi tệp .jsonl đều phải tự khai nguồn. Phát hiện trong lần soát đối
    # kháng 25/09/2026 — lược đồ ở danh-gia/luoc-do-bo-de.md KHÔNG có trường 'nguon', nên
    # một bộ đề viết ĐÚNG lược đồ vẫn trượt cổng ở MỌI dòng, khiến ràng buộc R8 của chính
    # tài liệu ấy thành không thể thoả mãn. Đã thử thật: 2 dòng đúng lược đồ ⇒ 2 vi phạm.
    # Cách xử là bổ sung trường vào lược đồ và khai tên nguồn ở đây, KHÔNG phải nới luật.
    "bo-de-danh-gia": "câu hỏi viết tay của bộ đánh giá, không phải ngữ liệu huấn luyện. "
                      "CHƯA CÓ tệp nào trong kho (đo 25/09/2026) ⇒ số bản ghi hiện là 0.",
    # Lớp có cấu trúc: tên nguồn do dự án tự đặt. CHƯA CÓ tệp nào dùng các tên này
    # ⇒ chưa đo trên thực tế, ghi ra đây là để khai trước phạm vi cho phép.
    "business.company_profiles": "5.424 doanh nghiệp đủ cả ba điều kiện (đã xuất bản ∧ có "
                                 "ngành ∧ có sản phẩm). Đây là con số duy nhất được phép dùng.",
    "business.capabilities": "11.927 dòng, CHỈ phát hành cột name và name_en (346.704 ký tự). "
                             "Cột description có 696.890 ký tự nhưng chỉ 58 giá trị khác nhau "
                             "trên 11.927 dòng ⇒ là chuỗi xuất xứ ETL lặp lại, KHÔNG phát hành.",
    "business.company_sector_links": "6.666 công ty có ngành.",
}

# ── Nguồn bị cấm (đối chiếu chính xác giá trị trường 'nguon') ──────────────────
# Khoá đầu được GHÉP lúc chạy vì nó trùng một dấu hiệu mạnh: viết thẳng thì chính tệp cổng
# này bị cổng bắt (đã đo thật ngày 25/09/2026, đúng một dòng), và người sửa sẽ bị dụ đi
# mở ngoại lệ cho cổng thay vì giữ cổng sạch.
NGUON_BI_CAM = {
    "crm_geocode" + "_dot2": "dữ liệu CRM khách hàng đã định vị — 1.079.991 bản ghi, dữ liệu của người khác",
    "khach_dn": "cùng nguồn CRM khách hàng",
    "bai-dang-bds": "5.939 đoạn MÁY SINH qua cổng LLM bên thứ ba",
    "nao-agent": "116 đoạn MÁY SINH + là cấu hình thương mại của BDSG",
    "ocop": "1.727 sản phẩm, văn quảng cáo của người bán",
    "tin-tuc": "bản quyền toà soạn",
    "bai-dang": "nội dung người dùng đăng trên nền tảng",
    "kho-tri-thuc": "118/118 tệp mang cấp phép bên thứ ba",
}

# ── Dấu hiệu MẠNH: quét mọi tệp văn bản ───────────────────────────────────────
# Ghép lúc chạy để chính tệp .py này không chứa chuỗi cấm và không phải xin ngoại lệ
# cho bản thân nó. Ngoại lệ dành cho cổng là thứ dễ bị lạm dụng nhất.
DAU_HIEU_MANH = [
    ("crm_geocode" + "_dot2", "giá trị cột nguồn của lớp dữ liệu CRM khách hàng"),
    ("Licensed to " + "RAI Holdings", "dòng cấp phép bên thứ ba, có ở 118/118 tệp kho tri thức"),
    ("buu" + "dien.vn", "URL người bán trong dữ liệu OCOP"),
    ("map5d." + "khach_dn", "tên bảng CRM khách hàng, 1.079.991 bản ghi"),
]
# ── Dấu hiệu YẾU: chỉ quét tệp dữ liệu (xem giải thích ở phần PHẠM VI) ─────────
DAU_HIEU_YEU = ["bai-dang-bds", "nao-agent", "kho-tri-thuc", "ocop", "tin-tuc", "bai-dang"]

# ── Hình dạng BẢN GHI: thứ phân biệt "nhắc tên nguồn" với "dán dữ liệu của nguồn" ──
MAU_MANH_JSON = re.compile(r"\{\s*\"[A-Za-z_][A-Za-z0-9_]*\"\s*:")   # {"ten": ...
MAU_TOA_DO_WKT = re.compile(r"(?i)\b(?:POINT|MULTIPOLYGON|POLYGON)\s*\(")
SO_TAB_TOI_THIEU = 3  # một hàng TSV thật; văn xuôi hầu như không bao giờ có 3 tab trên một dòng


def la_dong_dang_ban_ghi(dong):
    """Dòng này trông giống MỘT BẢN GHI hay chỉ là câu văn nhắc tới nguồn?

    Cố ý KHÔNG dựa vào tên cột (id, ten, ma_xa, geom…): tài liệu tử tế phải được phép
    liệt kê đúng những cột ấy để nói rõ "bảng này chỉ có chừng đó cột, nên kể cả muốn
    dùng cũng không dùng được". Dựa vào tên cột là cấm luôn lời giải thích.
    """
    return bool(MAU_MANH_JSON.search(dong) or MAU_TOA_DO_WKT.search(dong)
                or dong.count("\t") >= SO_TAB_TOI_THIEU)


# ── Ngoại lệ tệp ──────────────────────────────────────────────────────────────
# CỐ Ý ĐỂ RỖNG. Bản đầu của cổng phải mở một ngoại lệ cho cong/README.md; sau khi ranh
# giới được sửa lại theo HÌNH DẠNG thay vì theo CHUỖI (xem docstring), ngoại lệ ấy hết
# cần thiết và đã bị xoá. Ngoại lệ tốt nhất là ngoại lệ không phải tồn tại.
# Nếu buộc phải thêm: mỗi khoá một lý do cụ thể, và phải thêm một ca vào tu_kiem() chứng
# minh ngoại lệ ấy KHÔNG làm thủng luật ở tệp khác.
NGOAI_LE_TEP = {}

MAX_IN_MOI_TEP = 15  # in quá dài thì không ai đọc, mà đọc mới sửa được


def la_nhi_phan(duong_dan):
    with open(duong_dan, "rb") as f:
        return b"\x00" in f.read(8192)


def duyet_tep(goc):
    ket_qua = []
    for thu_muc, cac_con, cac_tep in os.walk(goc):
        cac_con[:] = [c for c in cac_con if c not in BO_QUA_THU_MUC]
        for ten in cac_tep:
            ket_qua.append(os.path.join(thu_muc, ten))
    return sorted(ket_qua)


def la_trong_thu_muc_du_lieu(tuong_doi):
    return any(tuong_doi == t or tuong_doi.startswith(t + os.sep) for t in THU_MUC_DU_LIEU)


def kiem_ban_ghi(ban_ghi, so_dong, tuong_doi, vi_pham):
    """Một bản ghi phải TỰ CHỨNG MINH nguồn của nó. Im lặng không phải là trong sạch."""
    if not isinstance(ban_ghi, dict):
        vi_pham.append((tuong_doi, so_dong, "ban-ghi-khong-phai-doi-tuong",
                        "không chứng minh được nguồn vì bản ghi không có trường nào"))
        return
    if "nguon" not in ban_ghi:
        vi_pham.append((tuong_doi, so_dong, "thieu-truong-nguon",
                        "thiếu trường 'nguon' ⇒ KHÔNG chứng minh được là hợp lệ (fail-closed)"))
        return
    gia_tri = ban_ghi["nguon"]
    if not isinstance(gia_tri, str) or not gia_tri.strip():
        vi_pham.append((tuong_doi, so_dong, "truong-nguon-rong", "trường 'nguon' rỗng hoặc sai kiểu"))
        return
    gia_tri = gia_tri.strip()
    if gia_tri in NGUON_BI_CAM:
        vi_pham.append((tuong_doi, so_dong, "nguon-bi-cam",
                        "nguồn '%s' — %s" % (gia_tri, NGUON_BI_CAM[gia_tri])))
        return
    if gia_tri not in NGUON_DUOC_PHEP:
        vi_pham.append((tuong_doi, so_dong, "nguon-chua-khai",
                        "nguồn '%s' không nằm trong danh sách cho phép. Chưa khai = chưa được "
                        "phát hành; muốn thêm thì thêm vào NGUON_DUOC_PHEP kèm số đo." % gia_tri))


def kiem_jsonl(duong_dan, tuong_doi, vi_pham):
    so_ban_ghi = 0
    with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
        for so_dong, dong in enumerate(f, start=1):
            if not dong.strip():
                vi_pham.append((tuong_doi, so_dong, "dong-rong",
                                "dòng rỗng trong JSONL — bộ nạp huấn luyện thường nuốt im lặng, "
                                "nên ở đây tính là hỏng"))
                continue
            try:
                ban_ghi = json.loads(dong)
            except ValueError as loi:
                vi_pham.append((tuong_doi, so_dong, "dong-khong-doc-duoc", "JSON hỏng: %s" % loi))
                continue
            so_ban_ghi += 1
            kiem_ban_ghi(ban_ghi, so_dong, tuong_doi, vi_pham)
    return so_ban_ghi


def kiem_json(duong_dan, tuong_doi, vi_pham):
    with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
        try:
            noi_dung = json.load(f)
        except ValueError as loi:
            vi_pham.append((tuong_doi, 0, "json-hong", "không đọc được: %s" % loi))
            return 0
    if isinstance(noi_dung, list):
        cac_ban_ghi = noi_dung
    elif isinstance(noi_dung, dict) and isinstance(noi_dung.get("du_lieu"), list):
        cac_ban_ghi = noi_dung["du_lieu"]
    elif isinstance(noi_dung, dict) and isinstance(noi_dung.get("ban_ghi"), list):
        cac_ban_ghi = noi_dung["ban_ghi"]
    else:
        vi_pham.append((tuong_doi, 0, "hinh-dang-la",
                        "tệp .json trong thư mục dữ liệu nhưng không phải danh sách bản ghi "
                        "(cũng không có khoá 'du_lieu'/'ban_ghi') ⇒ không kiểm được nguồn"))
        return 0
    for chi_so, ban_ghi in enumerate(cac_ban_ghi):
        kiem_ban_ghi(ban_ghi, chi_so + 1, tuong_doi, vi_pham)
    return len(cac_ban_ghi)


def kiem_bang(duong_dan, tuong_doi, duoi, vi_pham):
    dau_phan_cach = "\t" if duoi == ".tsv" else ","
    with open(duong_dan, "r", encoding="utf-8", errors="replace", newline="") as f:
        bo_doc = csv.DictReader(f, delimiter=dau_phan_cach)
        if bo_doc.fieldnames is None:
            vi_pham.append((tuong_doi, 0, "bang-rong", "không có dòng tiêu đề ⇒ không kiểm được nguồn"))
            return 0
        if "nguon" not in bo_doc.fieldnames:
            vi_pham.append((tuong_doi, 1, "thieu-cot-nguon",
                            "bảng không có cột 'nguon' ⇒ KHÔNG chứng minh được là hợp lệ"))
            return 0
        so_dong = 0
        for chi_so, hang in enumerate(bo_doc, start=2):
            so_dong += 1
            kiem_ban_ghi(dict(hang), chi_so, tuong_doi, vi_pham)
    return so_dong


def quet_dau_hieu(duong_dan, tuong_doi, la_du_lieu, vi_pham):
    if tuong_doi in NGOAI_LE_TEP:
        return
    with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
        for so_dong, dong in enumerate(f, start=1):
            dang_ban_ghi = la_dong_dang_ban_ghi(dong)
            for chuoi, ly_do in DAU_HIEU_MANH:
                if chuoi not in dong:
                    continue
                if la_du_lieu:
                    vi_pham.append((tuong_doi, so_dong, "dau-hieu-manh", "%s — %s" % (chuoi, ly_do)))
                elif dang_ban_ghi:
                    vi_pham.append((tuong_doi, so_dong, "ban-ghi-cam-trong-tai-lieu",
                                    "%s — %s. Dòng này có hình dạng BẢN GHI, không phải câu văn "
                                    "nhắc tên nguồn." % (chuoi, ly_do)))
            if la_du_lieu:
                for chuoi in DAU_HIEU_YEU:
                    if chuoi in dong:
                        vi_pham.append((tuong_doi, so_dong, "dau-hieu-yeu",
                                        "%s — %s" % (chuoi, NGUON_BI_CAM.get(chuoi, "nguồn bị cấm"))))


def quet_kho(goc):
    vi_pham = []
    loi_cong = []
    thong_ke = {"tep_du_lieu": 0, "ban_ghi": 0}

    for duong_dan in duyet_tep(goc):
        tuong_doi = os.path.relpath(duong_dan, goc)
        _, duoi = os.path.splitext(duong_dan.lower())
        la_du_lieu = (duoi in DUOI_DU_LIEU_DONG or duoi in DUOI_DU_LIEU_BANG
                      or (duoi == ".json" and la_trong_thu_muc_du_lieu(tuong_doi)))
        if duoi not in DUOI_DU_LIEU_DONG and duoi not in DUOI_DU_LIEU_BANG and duoi not in DUOI_VAN_BAN_KHAC:
            continue
        try:
            if la_nhi_phan(duong_dan):
                loi_cong.append((tuong_doi, "đuôi văn bản nhưng nội dung nhị phân — không kiểm được"))
                continue
            if la_du_lieu:
                thong_ke["tep_du_lieu"] += 1
                if duoi in DUOI_DU_LIEU_DONG:
                    thong_ke["ban_ghi"] += kiem_jsonl(duong_dan, tuong_doi, vi_pham)
                elif duoi in DUOI_DU_LIEU_BANG:
                    thong_ke["ban_ghi"] += kiem_bang(duong_dan, tuong_doi, duoi, vi_pham)
                else:
                    thong_ke["ban_ghi"] += kiem_json(duong_dan, tuong_doi, vi_pham)
            quet_dau_hieu(duong_dan, tuong_doi, la_du_lieu, vi_pham)
        except OSError as loi:
            loi_cong.append((tuong_doi, "không đọc được: %s" % loi.strerror))

    return vi_pham, loi_cong, thong_ke


def in_bao_cao(goc, vi_pham, loi_cong, thong_ke):
    print("CỔNG khong-du-lieu-cam — gốc quét: %s" % goc)
    print("  Đã kiểm %d tệp dữ liệu, %d bản ghi. Nguồn được phép: %d tên đã khai."
          % (thong_ke["tep_du_lieu"], thong_ke["ban_ghi"], len(NGUON_DUOC_PHEP)))
    if thong_ke["tep_du_lieu"] == 0:
        print("  LƯU Ý: chưa có tệp dữ liệu nào trong kho. 'Không tìm thấy vi phạm' ở đây nghĩa là")
        print("  CHƯA CÓ GÌ ĐỂ KIỂM, không phải 'dữ liệu đã được thẩm định'. Đừng đọc nhầm.")
    if not vi_pham and not loi_cong:
        print("  ĐẠT.")
        return
    if vi_pham:
        theo_tep = {}
        for v in vi_pham:
            theo_tep.setdefault(v[0], []).append(v)
        print("  HỎNG: %d vi phạm trong %d tệp." % (len(vi_pham), len(theo_tep)))
        for tep in sorted(theo_tep):
            danh_sach = theo_tep[tep]
            print("    %s — %d vi phạm:" % (tep, len(danh_sach)))
            for _, so_dong, ma, chi_tiet in danh_sach[:MAX_IN_MOI_TEP]:
                print("      dòng %-6s [%s] %s" % (so_dong or "-", ma, chi_tiet))
            if len(danh_sach) > MAX_IN_MOI_TEP:
                print("      … và %d vi phạm nữa trong tệp này (in gọn cho dễ đọc)."
                      % (len(danh_sach) - MAX_IN_MOI_TEP))
    if loi_cong:
        print("  HỎNG (fail-closed): %d tệp không kiểm được." % len(loi_cong))
        for tep, ghi_chu in loi_cong:
            print("    %-52s %s" % (tep, ghi_chu))


def tu_kiem():
    """Bài thử ngược: chứng minh cổng CẮN từng luật, và KHÔNG cắn văn xuôi giải thích."""
    hong = []
    with tempfile.TemporaryDirectory() as tam:
        thu_muc_du_lieu = os.path.join(tam, "bo-du-lieu")
        os.makedirs(thu_muc_du_lieu)

        def ghi(duong_dan_tuong_doi, noi_dung):
            day_du = os.path.join(tam, duong_dan_tuong_doi)
            os.makedirs(os.path.dirname(day_du), exist_ok=True)
            with open(day_du, "w", encoding="utf-8") as f:
                f.write(noi_dung)

        ghi("bo-du-lieu/tot.jsonl",
            json.dumps({"nguon": "ho-so-dn", "van_ban": "Doanh nghiệp sản xuất."}, ensure_ascii=False) + "\n")
        ghi("bo-du-lieu/thieu-nguon.jsonl",
            json.dumps({"van_ban": "Không khai nguồn."}, ensure_ascii=False) + "\n")
        ghi("bo-du-lieu/nguon-cam.jsonl",
            json.dumps({"nguon": "bai-dang-bds", "van_ban": "x"}, ensure_ascii=False) + "\n")
        ghi("bo-du-lieu/nguon-la.jsonl",
            json.dumps({"nguon": "nguon-chua-ai-khai", "van_ban": "x"}, ensure_ascii=False) + "\n")
        ghi("bo-du-lieu/hong.jsonl", "{khong phai json}\n")
        ghi("bo-du-lieu/co-dong-rong.jsonl",
            json.dumps({"nguon": "wiki-crm", "van_ban": "x"}, ensure_ascii=False) + "\n\n")
        ghi("bo-du-lieu/thieu-cot.csv", "ten,van_ban\nA,B\n")
        # Tệp dữ liệu mang dấu hiệu mạnh: bắt ngay, không cần hình dạng bản ghi.
        ghi("bo-du-lieu/lo-dau-hieu-manh.csv",
            "nguon,van_ban\nho-so-dn,\"trích từ " + "crm_geocode" + "_dot2\"\n")
        # Tài liệu DÁN một bản ghi thật vào: phải bắt (có hình dạng JSON đối tượng).
        ghi("tai-lieu/dan-ban-ghi.md",
            "Ví dụ một bản ghi:\n\n    " +
            json.dumps({"id": 7, "ten": "Công ty X", "nguon": "crm_geocode" + "_dot2"}, ensure_ascii=False) +
            "\n")
        # Tài liệu NHẮC TÊN nguồn để nói rõ đã loại: phải KHÔNG bắt.
        # Ba dòng dưới đây mô phỏng đúng thứ đã bị bắt oan trong phép đo 25/09/2026.
        ghi("tai-lieu/van-xuoi-sach.md",
            "Các nguồn KHÔNG phát hành: ocop, tin-tuc, bai-dang, nao-agent, kho-tri-thuc.\n"
            "| `map5d." + "khach_dn` | 1.079.991 bản ghi | 100% `nguon = '" + "crm_geocode" + "_dot2'` "
            "⇒ dữ liệu khách hàng CRM; cột chỉ có id, ten, ma_xa, geom |\n"
            "118/118 tệp mang dòng cấp phép bên thứ ba (\"Licensed to " + "RAI Holdings\"), "
            "còn ocop thì url trỏ " + "buudien.vn" + ".\n")

        vi_pham, loi_cong, thong_ke = quet_kho(tam)
        theo_ma = {}
        for tep, _, ma, _ in vi_pham:
            theo_ma.setdefault(ma, set()).add(tep)

        can_bat = {
            "thieu-truong-nguon": "bo-du-lieu/thieu-nguon.jsonl",
            "nguon-bi-cam": "bo-du-lieu/nguon-cam.jsonl",
            "nguon-chua-khai": "bo-du-lieu/nguon-la.jsonl",
            "dong-khong-doc-duoc": "bo-du-lieu/hong.jsonl",
            "dong-rong": "bo-du-lieu/co-dong-rong.jsonl",
            "thieu-cot-nguon": "bo-du-lieu/thieu-cot.csv",
            "dau-hieu-manh": "bo-du-lieu/lo-dau-hieu-manh.csv",
            "ban-ghi-cam-trong-tai-lieu": "tai-lieu/dan-ban-ghi.md",
        }
        for ma, tep in can_bat.items():
            if tep not in theo_ma.get(ma, set()):
                hong.append("KHÔNG bắt được '%s' ở %s — cổng thủng ở luật này." % (ma, tep))
        for tep, so_dong, ma, chi_tiet in vi_pham:
            if tep in ("bo-du-lieu/tot.jsonl", "tai-lieu/van-xuoi-sach.md"):
                hong.append("Bắt nhầm tệp sạch %s dòng %s [%s] %s" % (tep, so_dong, ma, chi_tiet))
        if loi_cong:
            hong.append("Lỗi cổng ngoài dự kiến: %s" % loi_cong)

    print("TỰ KIỂM khong-du-lieu-cam: %d luật cài bẫy, 2 tệp sạch làm đối chứng." % len(can_bat))
    if hong:
        for d in hong:
            print("  HỎNG: %s" % d)
        return 1
    print("  ĐẠT: bắt đủ %d luật, gồm bản ghi THIẾU trường 'nguon' (fail-closed) và một bản ghi" % len(can_bat))
    print("       cấm bị DÁN vào tài liệu; đồng thời KHÔNG bắt nhầm bảng văn xuôi liệt kê")
    print("       'đã loại nguồn nào và vì sao' — đúng thứ đã bị bắt oan trong phép đo 25/09/2026.")
    return 0


def main():
    bo_phan_tich = argparse.ArgumentParser(description="Cổng 3/4: chặn dữ liệu không được phát hành.")
    bo_phan_tich.add_argument("--goc", default=None, help="thư mục gốc cần quét (mặc định: thư mục cha của cong/)")
    bo_phan_tich.add_argument("--tu-kiem", action="store_true", help="chạy bài thử ngược, chứng minh cổng cắn")
    tham_so = bo_phan_tich.parse_args()

    if tham_so.tu_kiem:
        return tu_kiem()

    goc = tham_so.goc or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir(goc):
        print("HỎNG: không thấy thư mục gốc '%s'." % goc)
        return 2
    try:
        vi_pham, loi_cong, thong_ke = quet_kho(goc)
    except Exception as loi:
        print("HỎNG: cổng tự vỡ khi quét (%s: %s). Coi như KHÔNG đạt." % (type(loi).__name__, loi))
        return 2

    in_bao_cao(goc, vi_pham, loi_cong, thong_ke)
    if vi_pham:
        return 1
    if loi_cong:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
