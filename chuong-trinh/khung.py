#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""khung.py — KHUNG CHƯƠNG TRÌNH GIÁO DỤC PHỔ THÔNG VIỆT NAM.

=============================================================================
TỆP NÀY LÀ GÌ, VÀ QUAN TRỌNG HƠN: KHÔNG PHẢI GÌ
=============================================================================
Đây là **cấu trúc** chương trình: có những cấp nào, mỗi cấp những môn nào, môn
nào bắt buộc. Cấu trúc ấy lấy từ **Chương trình giáo dục phổ thông 2018**
(Thông tư 32/2018/TT-BGDĐT) — một VĂN BẢN PHÁP QUY CÔNG KHAI.

Đây KHÔNG phải nội dung sách giáo khoa. Sách giáo khoa có bản quyền của các nhà
xuất bản được phê duyệt. Chép nội dung sách vào ngữ liệu rồi phát hành mô hình
mở là vi phạm, và không có cách nào lách. Ngữ liệu phải được **viết mới**, bám
theo khung này — đúng cách mà phi-1 đã làm (sinh nội dung dạng sách giáo khoa,
không chép sách có sẵn).

=============================================================================
VÌ SAO KHUNG NÀY LÀ THỨ ĐÁNG GIÁ NHẤT
=============================================================================
Ba môn trong khung này là chỗ mô hình nước ngoài sai nặng nhất, và sai theo
cách người Việt nhận ra ngay:

  · LỊCH SỬ — trình bày theo góc nhìn nước khác.
  · ĐỊA LÍ  — cấu trúc hành chính cũ (63 tỉnh), và quan trọng hơn: chủ quyền
              biển đảo. Hoàng Sa thuộc Đà Nẵng, Trường Sa thuộc Khánh Hoà.
  · TOÁN    — ký hiệu, cách trình bày, thứ tự kiến thức theo lớp khác nhau.

BDSG đã có sẵn hai thứ để chặn hai lỗi đầu: cổng chủ quyền
(`scripts/kiem-tra/chu-quyen.mjs` ở kho landing) và dữ liệu 34 tỉnh / 3.321
phường xã theo NQ 202/2025/QH15. Khung này nối chúng vào ngữ liệu huấn luyện.

=============================================================================
MỘT AGENT KHÁC AGENT KHÁC BẰNG CON TRỎ, KHÔNG BẰNG BẢN SAO
=============================================================================
100 triệu người Việt học CÙNG một chương trình phổ thông. Viết nó 100 triệu
lần thì 99,99% ngữ liệu là bản sao, và dữ liệu trùng lặp không dạy thêm gì.

Nên: ngữ liệu phổ thông viết MỘT lần (~16 triệu token). Mỗi agent mang một
**hồ sơ học vấn** ~200 byte trỏ vào đó, cộng phần chuyên môn riêng. 100 triệu
hồ sơ = 20 GB, thay vì 9.760 TB nếu chép ngữ liệu cho từng agent.
"""
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------
# Cấp học. `tuoi` là tuổi bắt đầu theo quy định phổ biến; không phải luật cứng.
# --------------------------------------------------------------------------
CAP_HOC = (
    {"ma": "mam-non",  "ten": "Mầm non / Mẫu giáo", "lop": (),                 "tuoi": 3},
    {"ma": "tieu-hoc", "ten": "Tiểu học",           "lop": (1, 2, 3, 4, 5),    "tuoi": 6},
    {"ma": "thcs",     "ten": "Trung học cơ sở",    "lop": (6, 7, 8, 9),       "tuoi": 11},
    {"ma": "thpt",     "ten": "Trung học phổ thông","lop": (10, 11, 12),       "tuoi": 15},
)

# --------------------------------------------------------------------------
# Môn học theo Chương trình GDPT 2018.
#   `bat_buoc`  — môn bắt buộc ở cấp đó
#   `chuan_vn`  — môn mà "đúng chuẩn Việt Nam" là điều KHÁC BIỆT thật sự, tức
#                 chỗ một mô hình nước ngoài sẽ sai. Cờ này dẫn tới phép kiểm.
# --------------------------------------------------------------------------
MON = (
    # --- Mầm non ---
    {"ma": "mn-ngon-ngu", "ten": "Phát triển ngôn ngữ", "cap": "mam-non", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "mn-nhan-thuc","ten": "Phát triển nhận thức","cap": "mam-non", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "mn-tinh-cam", "ten": "Phát triển tình cảm và kỹ năng xã hội", "cap": "mam-non", "bat_buoc": True, "chuan_vn": False},

    # --- Tiểu học ---
    {"ma": "th-tieng-viet","ten": "Tiếng Việt",        "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "th-toan",      "ten": "Toán",              "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "th-dao-duc",   "ten": "Đạo đức",           "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "th-tnxh",      "ten": "Tự nhiên và Xã hội","cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "th-khoa-hoc",  "ten": "Khoa học",          "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "th-lsdl",      "ten": "Lịch sử và Địa lí", "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "th-tin-cn",    "ten": "Tin học và Công nghệ","cap": "tieu-hoc","bat_buoc": True,  "chuan_vn": False},
    {"ma": "th-the-chat",  "ten": "Giáo dục thể chất", "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "th-nghe-thuat","ten": "Nghệ thuật (Âm nhạc, Mĩ thuật)", "cap": "tieu-hoc", "bat_buoc": True, "chuan_vn": True},
    {"ma": "th-ngoai-ngu", "ten": "Ngoại ngữ 1",       "cap": "tieu-hoc", "bat_buoc": True,  "chuan_vn": False},

    # --- THCS ---
    {"ma": "cs-ngu-van",   "ten": "Ngữ văn",           "cap": "thcs", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "cs-toan",      "ten": "Toán",              "cap": "thcs", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "cs-ngoai-ngu", "ten": "Ngoại ngữ 1",       "cap": "thcs", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "cs-gdcd",      "ten": "Giáo dục công dân", "cap": "thcs", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "cs-lsdl",      "ten": "Lịch sử và Địa lí", "cap": "thcs", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "cs-khtn",      "ten": "Khoa học tự nhiên", "cap": "thcs", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "cs-cong-nghe", "ten": "Công nghệ",         "cap": "thcs", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "cs-tin-hoc",   "ten": "Tin học",           "cap": "thcs", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "cs-the-chat",  "ten": "Giáo dục thể chất", "cap": "thcs", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "cs-nghe-thuat","ten": "Nghệ thuật",        "cap": "thcs", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "cs-dia-phuong","ten": "Nội dung giáo dục địa phương", "cap": "thcs", "bat_buoc": True, "chuan_vn": True},

    # --- THPT: bắt buộc ---
    # Lịch sử là môn BẮT BUỘC ở THPT. Ghi rõ vì đây là điểm từng thay đổi và là
    # chỗ dễ chép nhầm theo tài liệu cũ.
    {"ma": "pt-ngu-van",   "ten": "Ngữ văn",           "cap": "thpt", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "pt-toan",      "ten": "Toán",              "cap": "thpt", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "pt-ngoai-ngu", "ten": "Ngoại ngữ 1",       "cap": "thpt", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "pt-lich-su",   "ten": "Lịch sử",           "cap": "thpt", "bat_buoc": True,  "chuan_vn": True},
    {"ma": "pt-the-chat",  "ten": "Giáo dục thể chất", "cap": "thpt", "bat_buoc": True,  "chuan_vn": False},
    {"ma": "pt-qpan",      "ten": "Giáo dục quốc phòng và an ninh", "cap": "thpt", "bat_buoc": True, "chuan_vn": True},
    # --- THPT: lựa chọn ---
    {"ma": "pt-dia-li",    "ten": "Địa lí",            "cap": "thpt", "bat_buoc": False, "chuan_vn": True},
    {"ma": "pt-ktpl",      "ten": "Giáo dục kinh tế và pháp luật", "cap": "thpt", "bat_buoc": False, "chuan_vn": True},
    {"ma": "pt-vat-li",    "ten": "Vật lí",            "cap": "thpt", "bat_buoc": False, "chuan_vn": False},
    {"ma": "pt-hoa-hoc",   "ten": "Hoá học",           "cap": "thpt", "bat_buoc": False, "chuan_vn": False},
    {"ma": "pt-sinh-hoc",  "ten": "Sinh học",          "cap": "thpt", "bat_buoc": False, "chuan_vn": False},
    {"ma": "pt-cong-nghe", "ten": "Công nghệ",         "cap": "thpt", "bat_buoc": False, "chuan_vn": False},
    {"ma": "pt-tin-hoc",   "ten": "Tin học",           "cap": "thpt", "bat_buoc": False, "chuan_vn": False},
    {"ma": "pt-am-nhac",   "ten": "Âm nhạc",           "cap": "thpt", "bat_buoc": False, "chuan_vn": True},
    {"ma": "pt-mi-thuat",  "ten": "Mĩ thuật",          "cap": "thpt", "bat_buoc": False, "chuan_vn": True},
)

# --------------------------------------------------------------------------
# BẬC SAU PHỔ THÔNG. Tỉ lệ là để SINH HỒ SƠ có phân bố hợp lý, KHÔNG phải số
# thống kê chính thức — tệp này không được dùng làm nguồn trích dẫn dân số.
# --------------------------------------------------------------------------
BAC_SAU_PT = (
    {"ma": "khong",     "ten": "Hết phổ thông",  "ti_le": 0.62},
    {"ma": "cao-dang",  "ten": "Cao đẳng",       "ti_le": 0.10},
    {"ma": "dai-hoc",   "ten": "Đại học",        "ti_le": 0.24},
    {"ma": "thac-si",   "ten": "Thạc sĩ",        "ti_le": 0.035},
    {"ma": "tien-si",   "ten": "Tiến sĩ",        "ti_le": 0.005},
)


def cap_theo_ma(ma: str) -> Optional[Dict[str, Any]]:
    for c in CAP_HOC:
        if c["ma"] == ma:
            return c
    return None


def mon_cua_cap(ma_cap: str, chi_bat_buoc: bool = False) -> List[Dict[str, Any]]:
    return [m for m in MON if m["cap"] == ma_cap and (m["bat_buoc"] or not chi_bat_buoc)]


def mon_chuan_vn() -> List[Dict[str, Any]]:
    """Các môn mà 'đúng chuẩn Việt Nam' là khác biệt thật sự.

    Đây là danh sách dẫn tới phép kiểm: ngữ liệu cho những môn này phải đi qua
    cổng chủ quyền và cổng dữ liệu hành chính trước khi vào bộ huấn luyện.
    """
    return [m for m in MON if m["chuan_vn"]]


def tong_ti_le_bac() -> float:
    return sum(b["ti_le"] for b in BAC_SAU_PT)
