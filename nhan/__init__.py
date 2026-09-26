#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan — NHÂN CỦA OPEN BDSG OS.

Nhân sở hữu DANH TÍNH, QUYỀN, HẠN MỨC và NHẬT KÝ. Trình điều khiển thì không:
nó chỉ đổi một lời gọi công cụ thành một lời gọi API của nền tảng nó phụ trách.

    danh_tinh.py   ai đang gọi
    quyen.py       ai được gọi công cụ nào (danh sách trắng, đọc ≠ ghi)
    han_muc.py     gọi bao nhiêu thì đủ (cửa sổ trượt)
    nhat_ky.py     ai đã làm gì (một dòng JSON, tham số đã làm mờ)
    dinh_tuyen.py  trái tim: bảy bước của một lời gọi
    mcp.py         phơi nhân ra ngoài qua JSON-RPC trên stdio
    thu_nhan.py    bài tự kiểm, chạy được, không cần mạng, không cần CSDL

Chỉ dùng thư viện chuẩn của Python. Chạy bài tự kiểm:

    .venv/bin/python nhan/thu_nhan.py

Đọc `nhan/README.md` trước khi sửa: bốn quyết định kiến trúc và một ràng buộc
cứng về mô hình đều nằm ở đó.
"""

from .danh_tinh import (
    NGUON_KHOA_API,
    NGUON_PHIEN,
    BoXacThuc,
    DanhTinh,
    LoiDanhTinh,
    nguon_bang_khoa,
    so_sanh_hang_dinh,
)
from .dinh_tuyen import BanKhaiCongCu, KetQuaGoi, LoiDangKy, Nhan, TrinhDieuKhien
from .han_muc import BoHanMuc, HanMuc, KhoHanMuc, KhoTrongBoNho, LoiHanMuc
from .nhat_ky import LOI, THANH_CONG, TU_CHOI, LoiNhatKy, NhatKy, lam_mo
from .mcp import MayChuMCP, PHIEN_BAN_GIAO_THUC
from .quyen import DOC, GHI, ChinhSach, CongGhi, LoiChinhSach, MoTaCongCu

__all__ = [
    # danh tính
    "DanhTinh", "BoXacThuc", "LoiDanhTinh", "nguon_bang_khoa", "so_sanh_hang_dinh",
    "NGUON_KHOA_API", "NGUON_PHIEN",
    # quyền
    "ChinhSach", "CongGhi", "MoTaCongCu", "LoiChinhSach", "DOC", "GHI",
    # hạn mức
    "HanMuc", "BoHanMuc", "KhoHanMuc", "KhoTrongBoNho", "LoiHanMuc",
    # nhật ký
    "NhatKy", "lam_mo", "LoiNhatKy", "THANH_CONG", "TU_CHOI", "LOI",
    # định tuyến
    "Nhan", "TrinhDieuKhien", "BanKhaiCongCu", "KetQuaGoi", "LoiDangKy",
    # MCP
    "MayChuMCP", "PHIEN_BAN_GIAO_THUC",
]
