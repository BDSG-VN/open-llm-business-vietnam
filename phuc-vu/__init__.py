#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lớp PHỤC VỤ mô hình của BDSG — nối trợ lý nội bộ tới một máy vLLM chạy cục bộ.

GÓI NÀY LÀM GÌ
--------------
Đúng một việc: đổi "một câu hỏi" thành "một dòng chảy chữ" bằng cách gọi một máy
vLLM NỘI BỘ qua API tương thích OpenAI. Nó không dựng máy chủ HTTP, không giữ
hội thoại, không phân quyền — những phần ấy thuộc về lớp khác.

    phuc-vu/cau_hinh.py         đọc cấu hình từ biến môi trường, tự kiểm, không in khoá
    phuc-vu/cong_mo_hinh.py     gọi vLLM, bóc SSE, dịch lỗi mạng sang lỗi người đọc được
    phuc-vu/gia_lap.py          backend GIẢ để kiểm thử, phải bật tường minh mới chạy
    phuc-vu/thu_cong_mo_hinh.py bài tự kiểm, không cần mạng, không cần GPU

TRỌNG SỐ LÀ CỦA GOOGLE
----------------------
Mô hình phục vụ mặc định là `google/gemma-4-31B-it`, trọng số do Google phát hành
theo giấy phép Apache-2.0 (thẻ mô hình: huggingface.co/google/gemma-4-31B-it;
mã triển khai tham chiếu: github.com/google-deepmind/gemma; bài báo arXiv:2607.02770).

BDSG PHỤC VỤ trọng số ấy. BDSG KHÔNG huấn luyện và KHÔNG tinh chỉnh nó. Trường tự
khai `bdsg_la_trong_so_bdsg` trả `false` cho mọi mã mô hình đi qua gói này — xem
hàm cùng tên trong `cau_hinh.py`.

KHÔNG DÍNH GÌ TỚI MÔ HÌNH NHỎ CỦA BDSG
---------------------------------------
Kiến trúc trong `mo-hinh/` (26.878.464 tham số, tokenizer 6.400 token) là một
NHÁNH NGHIÊN CỨU RIÊNG và gói này không chạm vào nó. Không nạp trọng số Gemma 4
vào kiến trúc ấy, và không thay tokenizer hay chat template gốc của Gemma bằng
tokenizer thử nghiệm của BDSG. Chat template do chính vLLM áp, đọc từ tokenizer
đi kèm trọng số Google.

CHƯA CÓ ĐĂNG NHẬP AN TOÀN
--------------------------
Bản này chỉ dùng cho DEMO MỘT NGƯỜI chạy trên localhost. Nó CHƯA dùng được cho
nhiều nhân viên: chưa có danh tính, chưa có phân quyền hội thoại, chưa có nhật ký
truy cập. Trỏ nó ra mạng là tự mở một cổng vào không ai canh.

TÊN THƯ MỤC: thư mục thật tên là `phuc-vu` (có gạch ngang, theo quy ước đặt tên
của kho). Gạch ngang không hợp lệ trong tên mô-đun Python, nên không `import
phuc-vu` được. Hai cách dùng:
  - chạy tệp trong thư mục ấy trực tiếp:  .venv/bin/python phuc-vu/thu_cong_mo_hinh.py
  - hoặc nạp bằng importlib nếu cần dùng như thư viện từ nơi khác:
        import importlib.util
        spec = importlib.util.spec_from_file_location("phuc_vu", "phuc-vu/__init__.py")

Viết ngày 26/09/2026. Python 3.9.6.
"""

from .cau_hinh import (
    BIEN_HET_GIO,
    BIEN_KHOA,
    BIEN_MO_HINH,
    BIEN_NGU_CANH,
    BIEN_TRAN_TOKEN_RA,
    BIEN_URL,
    MO_HINH_MAC_DINH,
    NGU_CANH_MAC_DINH,
    NGU_CANH_TRAN_CUA_MO_HINH,
    CauHinhPhucVu,
    LoiCauHinh,
    bdsg_la_trong_so_bdsg,
)
from .cong_mo_hinh import (
    BoDocSSE,
    CongMoHinh,
    LoiCongMoHinh,
    LoiKhongNoiDuocMayNoiBo,
    LoiMayNoiBoTraLoiSai,
    boc_mau_chu,
    doi_chieu_mo_hinh,
)
from .gia_lap import (
    BIEN_BAT,
    BIEN_CHE_DO_LOI,
    MA_MO_HINH_GIA,
    CongMoHinhGiaLap,
    LoiGiaLapChuaBat,
    dang_bat,
)

from .may_chu import (  # noqa: E402
    BoiCanh,
    la_trong_so_google,
    tao_lop_xu_ly,
    tao_may_chu,
    xuat_xu_trong_so,
)
from .kho_hoi_thoai import KhoHoiThoai  # noqa: E402
from .rag import Doan, KhoTaiLieu, NguCanh, TaiLieu, duoc_doc  # noqa: E402

__all__ = [
    # Cấu hình
    "CauHinhPhucVu",
    "LoiCauHinh",
    "bdsg_la_trong_so_bdsg",
    "BIEN_URL",
    "BIEN_MO_HINH",
    "BIEN_KHOA",
    "BIEN_TRAN_TOKEN_RA",
    "BIEN_NGU_CANH",
    "BIEN_HET_GIO",
    "MO_HINH_MAC_DINH",
    "NGU_CANH_MAC_DINH",
    "NGU_CANH_TRAN_CUA_MO_HINH",
    # Cổng mô hình
    "CongMoHinh",
    "BoDocSSE",
    "boc_mau_chu",
    "doi_chieu_mo_hinh",
    "LoiCongMoHinh",
    "LoiKhongNoiDuocMayNoiBo",
    "LoiMayNoiBoTraLoiSai",
    # Backend giả (chỉ để kiểm thử)
    "CongMoHinhGiaLap",
    "LoiGiaLapChuaBat",
    "MA_MO_HINH_GIA",
    "BIEN_BAT",
    "BIEN_CHE_DO_LOI",
    "dang_bat",
    # Máy chủ HTTP — 5 đường API của chat/README.md
    "tao_may_chu",
    "tao_lop_xu_ly",
    "BoiCanh",
    "xuat_xu_trong_so",
    "la_trong_so_google",
    # Kho hội thoại
    "KhoHoiThoai",
    # Truy hồi có phân quyền
    "KhoTaiLieu",
    "TaiLieu",
    "Doan",
    "NguCanh",
    "duoc_doc",
]

__version__ = "0.1.0"
