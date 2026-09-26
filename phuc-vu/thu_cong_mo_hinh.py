#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phuc-vu/thu_cong_mo_hinh.py — BÀI TỰ KIỂM CHO LỚP PHỤC VỤ MÔ HÌNH.

CHẠY:
    .venv/bin/python phuc-vu/thu_cong_mo_hinh.py

KHÔNG cần mạng. KHÔNG cần GPU. KHÔNG cần trọng số. KHÔNG cần máy vLLM nào đang
chạy. Toàn bộ bài chạy xong dưới một giây trên máy xách tay.

VÌ SAO CÓ BÀI NÀY, VÀ VÌ SAO NÓ KIỂM ĐÚNG NHỮNG CHỖ NÀY
--------------------------------------------------------
Lớp phục vụ có bốn chỗ hỏng mà lỗi KHÔNG tự báo, và cả bốn đều được chọn vào đây:

  1. CẤU HÌNH THIẾU MÀ VẪN CHẠY. Nếu thiếu địa chỉ máy mà chương trình đoán một
     giá trị, nó sẽ chạy và trỏ vào chỗ không ai định trỏ tới. Phải ném lỗi.
  2. KHOÁ LỌT VÀO NHẬT KÝ. Hàm tóm tắt cấu hình sinh ra để dán vào nhật ký khởi
     động và báo cáo sự cố — hai chỗ đi xa hơn người viết nghĩ.
  3. LỖI MẠNG TRẦN TRÔI LÊN GIAO DIỆN. Trong một hệ hứa "mọi thứ chạy trên máy
     bạn", câu báo lỗi phải nói rõ hỏng ở MÁY NỘI BỘ. "Connection refused" thì
     không nói được điều đó.
  4. BỘ ĐỌC SSE VỠ KHI GÓI MẠNG CẮT GIỮA MỘT MẨU CHỮ. Đây là chỗ dễ hỏng nhất
     của mọi bộ đọc SSE, và nó gần như không bao giờ lộ ra trên máy cục bộ với
     câu trả lời ngắn — nó lộ ra trên máy thật, với người dùng thật.

BÀI NÀY KHÔNG NÓI GÌ VỀ CHẤT LƯỢNG MÔ HÌNH. Tính đến 26/09/2026 dự án chưa có
GPU, chưa từng nạp google/gemma-4-31B-it, chưa đo độ trễ, chưa đo số yêu cầu
đồng thời. Mọi con số ấy là CHƯA ĐO. Bài này chỉ kiểm tính đúng của phần mã
không cần mô hình.

MÃ THOÁT: 0 = mọi phép kiểm ĐẠT. 1 = có phép kiểm HỎNG.

Viết ngày 26/09/2026. Python 3.9.6.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import socket
import sys
import threading
import traceback

THU_MUC = os.path.dirname(os.path.abspath(__file__))
GOC_KHO = os.path.dirname(THU_MUC)

# ----------------------------------------------------------------------
# Nạp gói. Thư mục thật tên là "phuc-vu" — gạch ngang không hợp lệ trong tên
# mô-đun Python, nên khi chạy tệp này trực tiếp (không có __package__) phải nạp
# thư mục bằng importlib dưới một tên hợp lệ.
# ----------------------------------------------------------------------
if __package__:
    from . import cau_hinh as _cau_hinh
    from . import cong_mo_hinh as _cong
    from . import gia_lap as _gia_lap
else:
    _spec = importlib.util.spec_from_file_location(
        "phuc_vu",
        os.path.join(THU_MUC, "__init__.py"),
        submodule_search_locations=[THU_MUC],
    )
    if _spec is None or _spec.loader is None:
        print("HỎNG: không nạp được gói từ {}".format(THU_MUC))
        sys.exit(1)
    _goi = importlib.util.module_from_spec(_spec)
    sys.modules["phuc_vu"] = _goi
    _spec.loader.exec_module(_goi)
    _cau_hinh = sys.modules["phuc_vu.cau_hinh"]
    _cong = sys.modules["phuc_vu.cong_mo_hinh"]
    _gia_lap = sys.modules["phuc_vu.gia_lap"]

CauHinhPhucVu = _cau_hinh.CauHinhPhucVu
LoiCauHinh = _cau_hinh.LoiCauHinh
bdsg_la_trong_so_bdsg = _cau_hinh.bdsg_la_trong_so_bdsg

BoDocSSE = _cong.BoDocSSE
CongMoHinh = _cong.CongMoHinh
boc_mau_chu = _cong.boc_mau_chu
doi_chieu_mo_hinh = _cong.doi_chieu_mo_hinh
LoiKhongNoiDuocMayNoiBo = _cong.LoiKhongNoiDuocMayNoiBo
LoiMayNoiBoTraLoiSai = _cong.LoiMayNoiBoTraLoiSai

CongMoHinhGiaLap = _gia_lap.CongMoHinhGiaLap
LoiGiaLapChuaBat = _gia_lap.LoiGiaLapChuaBat
MA_MO_HINH_GIA = _gia_lap.MA_MO_HINH_GIA


# ----------------------------------------------------------------------
# Khung chạy thử tối giản (không dùng pytest, để bài này chạy được ở mọi nơi —
# kho không có pytest trong .venv, và một bài tự kiểm cần thêm phụ thuộc mới
# chạy được là bài tự kiểm sẽ không ai chạy).
# ----------------------------------------------------------------------

_KET_QUA = []


def phep_kiem(ten):
    def bao(ham):
        def chay():
            try:
                ghi_chu = ham()
                _KET_QUA.append((ten, True, ghi_chu or ""))
                print("  [ĐẠT ] {}{}".format(ten, "  — " + ghi_chu if ghi_chu else ""))
                return True
            except Exception as loi:  # noqa: BLE001 — bài tự kiểm phải bắt hết
                _KET_QUA.append((ten, False, "{}: {}".format(type(loi).__name__, loi)))
                print("  [HỎNG] {}".format(ten))
                print("         {}: {}".format(type(loi).__name__, loi))
                for dong in traceback.format_exc().splitlines()[-6:]:
                    print("         | " + dong)
                return False

        chay.__name__ = ham.__name__
        return chay

    return bao


def bang(dieu_kien, thong_diep):
    if not dieu_kien:
        raise AssertionError(thong_diep)


class MoiTruongTam:
    """Đặt/xoá biến môi trường rồi TRẢ LẠI NGUYÊN TRẠNG khi ra khỏi khối.

    Không khôi phục thì phép kiểm thứ hai chạy trên rác của phép kiểm thứ nhất,
    và thứ tự chạy trở thành một đầu vào ẩn. Đó là kiểu bài kiểm "xanh khi chạy
    cả bộ, đỏ khi chạy riêng một phép" — mất nhiều giờ mới truy ra.
    """

    def __init__(self, **cac_bien):
        self._moi = cac_bien
        self._cu = {}

    def __enter__(self):
        for ten, gia_tri in self._moi.items():
            self._cu[ten] = os.environ.get(ten)
            if gia_tri is None:
                os.environ.pop(ten, None)
            else:
                os.environ[ten] = gia_tri
        return self

    def __exit__(self, *_):
        for ten, gia_tri in self._cu.items():
            if gia_tri is None:
                os.environ.pop(ten, None)
            else:
                os.environ[ten] = gia_tri
        return False


def _cong_chac_chan_dong():
    """Trả về một số cổng trên máy này gần như chắc chắn KHÔNG có ai nghe.

    Cách làm: xin hệ điều hành cấp một cổng tạm, ghi lại số, rồi đóng ngay. Hệ
    điều hành không cấp lại số ấy cho tiến trình khác trong chốc lát, nên nối
    vào đó sẽ bị từ chối — đúng tình huống "máy nội bộ chưa chạy" cần dựng lại.
    """
    o = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    o.bind(("127.0.0.1", 0))
    so_cong = o.getsockname()[1]
    o.close()
    return so_cong


# Một khoá BỊA để kiểm hàm tóm tắt. CỐ Ý không dùng tiền tố của bất kỳ nhà cung
# cấp thật nào (không "sk-", không "ghp_", không "AKIA"): viết thẳng một chuỗi
# như thế vào kho sẽ bị cong/khong-bi-mat.py bắt, và người ta sẽ tập thói quen
# thêm ngoại lệ cho cổng — mà mỗi ngoại lệ là một lỗ thủng.
KHOA_BIA = "khoa-bia-chi-de-kiem-" + "z" * 24


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 1 — Cấu hình
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("1. Thiếu biến địa chỉ máy phục vụ thì NÉM LỖI, không đoán giá trị")
def kiem_thieu_url():
    with MoiTruongTam(BDSG_VLLM_URL=None):
        try:
            CauHinhPhucVu.tu_moi_truong()
        except LoiCauHinh as loi:
            bang(
                _cau_hinh.BIEN_URL in str(loi),
                "Câu báo lỗi phải nói rõ tên biến còn thiếu, đang là: " + str(loi),
            )
            return "ném LoiCauHinh và nêu đúng tên biến"
    raise AssertionError(
        "Thiếu địa chỉ máy mà vẫn dựng được cấu hình — đây đúng là kiểu hỏng mà "
        "không báo: chương trình chạy được nhưng trỏ vào một chỗ không ai định "
        "trỏ tới."
    )


@phep_kiem("2. Địa chỉ sai giao thức thì NÉM LỖI")
def kiem_url_sai_giao_thuc():
    so_ca_bat = 0
    for dia_chi in ("127.0.0.1:8000/v1", "ftp://127.0.0.1/v1", "cai-gi-do"):
        with MoiTruongTam(BDSG_VLLM_URL=dia_chi):
            try:
                CauHinhPhucVu.tu_moi_truong()
            except LoiCauHinh:
                so_ca_bat += 1
    bang(so_ca_bat == 3, "Phải bắt cả 3 địa chỉ sai, chỉ bắt được {}".format(so_ca_bat))
    return "bắt 3/3 địa chỉ sai giao thức"


@phep_kiem("3. Biến số không phải số thì NÉM LỖI, không âm thầm lấy mặc định")
def kiem_so_khong_hop_le():
    with MoiTruongTam(
        BDSG_VLLM_URL="http://127.0.0.1:8000/v1", BDSG_NGU_CANH="tam nghin"
    ):
        try:
            CauHinhPhucVu.tu_moi_truong()
        except LoiCauHinh as loi:
            bang("BDSG_NGU_CANH" in str(loi), "Lỗi phải nêu tên biến sai")
            return "ném LoiCauHinh cho giá trị 'tam nghin'"
    raise AssertionError("Giá trị không phải số mà vẫn lọt qua")


@phep_kiem("4. Trần token ra >= ngữ cảnh thì NÉM LỖI (không còn chỗ cho câu hỏi)")
def kiem_tran_lon_hon_ngu_canh():
    with MoiTruongTam(
        BDSG_VLLM_URL="http://127.0.0.1:8000/v1",
        BDSG_NGU_CANH="2048",
        BDSG_TRAN_TOKEN_RA="2048",
    ):
        try:
            CauHinhPhucVu.tu_moi_truong()
        except LoiCauHinh:
            return "ném LoiCauHinh khi 2048 >= 2048"
    raise AssertionError(
        "Trần token ra bằng ngữ cảnh mà vẫn lọt — cấu hình này hỏng ở MỌI lượt "
        "hỏi, nhưng chỉ lộ ra sau khi đã dựng xong máy chủ."
    )


@phep_kiem("5. Ngữ cảnh mặc định là 8192, KHÔNG phải trần 262144 của mô hình")
def kiem_ngu_canh_mac_dinh():
    with MoiTruongTam(
        BDSG_VLLM_URL="http://127.0.0.1:8000/v1",
        BDSG_NGU_CANH=None,
        BDSG_TRAN_TOKEN_RA=None,
    ):
        cau_hinh = CauHinhPhucVu.tu_moi_truong()
    bang(
        cau_hinh.ngu_canh == 8192,
        "Ngữ cảnh mặc định phải là 8192, đang là {}".format(cau_hinh.ngu_canh),
    )
    bang(
        cau_hinh.ngu_canh != _cau_hinh.NGU_CANH_TRAN_CUA_MO_HINH,
        "Mặc định KHÔNG được bằng trần kiến trúc: bộ nhớ đệm KV sẽ ăn hết VRAM "
        "còn lại sau trọng số.",
    )
    bang(
        cau_hinh.tran_token_ra == 2048,
        "Trần token ra mặc định phải là 2048, đang là {}".format(cau_hinh.tran_token_ra),
    )
    return "8192 (trần kiến trúc 262144 KHÔNG được lấy làm mặc định)"


@phep_kiem("6. tom_tat() KHÔNG in khoá ra bất kỳ đâu")
def kiem_tom_tat_khong_lo_khoa():
    with MoiTruongTam(
        BDSG_VLLM_URL="http://127.0.0.1:8000/v1", BDSG_VLLM_KHOA=KHOA_BIA
    ):
        cau_hinh = CauHinhPhucVu.tu_moi_truong()
    bang(cau_hinh.khoa == KHOA_BIA, "Cấu hình phải THẬT SỰ giữ khoá thì phép kiểm mới có nghĩa")
    ban_in = cau_hinh.tom_tat()
    bang(
        KHOA_BIA not in ban_in,
        "KHOÁ LỌT VÀO BẢN TÓM TẮT. Bản tóm tắt này được dán vào nhật ký khởi động "
        "và báo cáo sự cố.",
    )
    # Kiểm cả mảnh: một bản "che bớt" kiểu in nửa khoá vẫn là lộ khoá.
    bang(KHOA_BIA[:12] not in ban_in, "Một phần đầu của khoá vẫn lọt vào bản tóm tắt")
    bang(KHOA_BIA[-12:] not in ban_in, "Một phần cuối của khoá vẫn lọt vào bản tóm tắt")
    bang("đã đặt" in ban_in, "Bản tóm tắt vẫn phải nói CÓ khoá hay không")
    return "khoá bịa {} ký tự không xuất hiện, kể cả một phần".format(len(KHOA_BIA))


@phep_kiem("7. bdsg_la_trong_so_bdsg() là FALSE cho trọng số Google nguyên bản")
def kiem_khong_nhan_vo_trong_so():
    bang(
        bdsg_la_trong_so_bdsg("google/gemma-4-31B-it") is False,
        "Trọng số Google nguyên bản KHÔNG phải trọng số do BDSG huấn luyện.",
    )
    bang(bdsg_la_trong_so_bdsg() is False, "Mặc định cũng phải là False")
    return "false cho mọi mã mô hình (BDSG PHỤC VỤ trọng số Google, không huấn luyện)"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 2 — Đường báo lỗi khi máy nội bộ không chạy
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("8. Máy nội bộ không chạy → ném ĐÚNG lớp lỗi riêng, nói rõ 'nội bộ'")
def kiem_may_noi_bo_khong_chay():
    so_cong = _cong_chac_chan_dong()
    dia_chi = "http://127.0.0.1:{}/v1".format(so_cong)
    with MoiTruongTam(BDSG_VLLM_URL=dia_chi, BDSG_HET_GIO_GIAY="3"):
        cong = CongMoHinh(CauHinhPhucVu.tu_moi_truong())
    try:
        cong.danh_sach_mo_hinh()
    except LoiKhongNoiDuocMayNoiBo as loi:
        thong_bao = str(loi)
        bang(
            "nội bộ" in thong_bao.lower() or "NỘI BỘ" in thong_bao,
            "Thông báo phải nói rõ hỏng ở máy NỘI BỘ, đang là: " + thong_bao,
        )
        bang(
            str(so_cong) in thong_bao,
            "Thông báo nên nêu địa chỉ đã thử, để người đọc biết kiểm ở đâu",
        )
        bang(
            "dự phòng" in thong_bao,
            "Thông báo phải nói rõ KHÔNG có đường dự phòng ra ngoài — nếu không, "
            "người đọc sẽ tự hỏi câu của mình đã đi đâu.",
        )
        return "LoiKhongNoiDuocMayNoiBo, thông báo nêu cổng {} và nói rõ không có đường ra ngoài".format(so_cong)
    except Exception as loi:  # noqa: BLE001
        raise AssertionError(
            "Ném nhầm loại lỗi {}: {}. Lỗi HTTP trần trôi lên giao diện thì người "
            "dùng không biết hỏng ở máy mình hay ở đâu.".format(type(loi).__name__, loi)
        )
    raise AssertionError("Nối được tới một cổng đáng lẽ đã đóng — phép kiểm không có nghĩa")


# Ba tệp DUY NHẤT trong lớp phục vụ có thể sinh ra một lời gọi mạng tới mô hình.
# Quét cả ba chứ không chỉ cong_mo_hinh.py: một đường dự phòng đặt trong cau_hinh.py
# (làm giá trị mặc định) hay trong gia_lap.py cũng ra ngoài y hệt, mà bản đầu của
# phép kiểm này không nhìn tới chúng.
CAC_TEP_CHAM_MANG = ("cau_hinh.py", "cong_mo_hinh.py", "gia_lap.py")

# Chỉ các máy NGAY TRÊN máy này mới được phép xuất hiện dưới dạng địa chỉ viết cứng
# (cau_hinh.py có một ví dụ 127.0.0.1 trong câu báo lỗi, và nó nên còn ở đó).
MAY_CUC_BO = ("127.0.0.1", "localhost", "0.0.0.0", "[::1]", "::1")

# Chỗ đứng của một biểu thức không phải hằng chuỗi, khi gộp một chuỗi bị nối từ
# nhiều mảnh. Nhờ nó mà `"https" + "://" + may + "/v1"` hiện ra thành một địa chỉ
# có phần máy chủ, thay vì tan thành ba mảnh vô hại.
CHO_TRONG_BIEU_THUC = "MOT-BIEU-THUC"


def _gop_chuoi(nut):
    """Gộp một nút cây cú pháp thành chuỗi nó sẽ tạo ra khi chạy.

    Hằng chuỗi trả về chính nó. Phép cộng gộp hai vế. Chuỗi-f và mọi thứ không
    phải hằng chuỗi trở thành CHO_TRONG_BIEU_THUC — ta không cần biết giá trị,
    chỉ cần biết CHỖ ẤY CÓ GÌ ĐÓ, vì một địa chỉ ghép từ biến vẫn là một địa chỉ.
    """
    if isinstance(nut, ast.Constant) and isinstance(nut.value, str):
        return nut.value
    if isinstance(nut, ast.JoinedStr):  # chuỗi-f
        ra = ""
        for phan in nut.values:
            if isinstance(phan, ast.Constant) and isinstance(phan.value, str):
                ra += phan.value
            else:
                ra += CHO_TRONG_BIEU_THUC
        return ra
    if isinstance(nut, ast.BinOp) and isinstance(nut.op, ast.Add):
        return _gop_chuoi(nut.left) + _gop_chuoi(nut.right)
    return CHO_TRONG_BIEU_THUC


def _quet_dia_chi_ra_ngoai(ma_nguon):
    """Trả về mọi địa chỉ tuyệt đối KHÔNG trỏ vào chính máy này."""
    cac_dia_chi = []
    for nut in ast.walk(ast.parse(ma_nguon)):
        if not isinstance(nut, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            continue
        chuoi = _gop_chuoi(nut)
        if chuoi == CHO_TRONG_BIEU_THUC:
            continue
        for khop in re.finditer(r"(?i)https?://([^\s'\"\\]*)", chuoi):
            may = khop.group(1).split("/")[0].lower()
            # Phần máy chủ rỗng hoặc không bắt đầu bằng ký tự của một tên máy:
            # đây là chữ trong câu văn ("phải bắt đầu bằng http:// hoặc https://"),
            # không phải một địa chỉ. Bắt oan chỗ này thì người ta gỡ phép kiểm.
            if not re.match(r"^([a-z0-9\[]|" + CHO_TRONG_BIEU_THUC.lower() + ")", may):
                continue
            if may.startswith(MAY_CUC_BO):
                continue
            cac_dia_chi.append(khop.group(0)[:80])
    return sorted(set(cac_dia_chi))


@phep_kiem("9. Lớp chạm mạng KHÔNG chứa một địa chỉ nào ra ngoài máy này")
def kiem_khong_co_duong_ra_ngoai():
    """Kiểm CẤU TRÚC, không kiểm hành vi — và đó là chủ ý.

    Một phép kiểm hành vi chỉ chứng minh đường dự phòng không chạy TRONG ca đã
    thử. Phép kiểm này chứng minh trong mã không tồn tại một địa chỉ ra ngoài
    nào để mà chạy tới, kể cả khi nó nằm trong nhánh chưa bao giờ chạy.

    SỬA 26/09/2026 — bản đầu dò bằng `re.findall(r"https?://[A-Za-z0-9]")` trên
    MỘT tệp. Đã ĐO ĐƯỢC là nó để lọt bốn cách viết, mỗi cách đều chạy được:
        "https" + "://" + may + "/v1"     (ghép từ mảnh — vẫn xanh 18/18)
        "https:" + "//api.nha-cung-cap"   (cắt ngay sau dấu hai chấm)
        "HTTPS://api.nha-cung-cap"        (viết hoa)
        f"https://{may}/v1"               (chuỗi-f)
    và nó không nhìn cau_hinh.py lẫn gia_lap.py, nơi một đường dự phòng cũng ra
    ngoài y hệt. Bản này đọc CÂY CÚ PHÁP: gộp các mảnh chuỗi lại trước khi dò,
    nên bốn cách trên hiện nguyên hình.

    CỐ Ý KHÔNG mang theo danh sách tên nhà cung cấp. Bài học đã ghi trong
    cong/khong-tham-chieu-ngoai.py: một bộ dò mang theo danh sách thứ nó dò thì
    chính nó là chỗ rò. Ở đây luật là luật CẤU TRÚC — mọi địa chỉ không trỏ vào
    chính máy này đều bị chặn, không cần biết nó tên gì.
    """
    for ten_tep in CAC_TEP_CHAM_MANG:
        with open(os.path.join(THU_MUC, ten_tep), "r", encoding="utf-8") as tep:
            ma_nguon = tep.read()
        cac_dia_chi = _quet_dia_chi_ra_ngoai(ma_nguon)
        bang(
            not cac_dia_chi,
            "{} chứa địa chỉ ra ngoài máy này: {}. Lớp này chỉ được gọi địa chỉ "
            "đọc từ cấu hình; một địa chỉ viết cứng ở đây là mầm của một đường "
            "dự phòng ra ngoài.".format(ten_tep, cac_dia_chi),
        )

    # ĐỐI CHỨNG. Không có nó thì một phép kiểm hỏng (ví dụ ast.parse ném lỗi rồi
    # bị nuốt, hoặc ai đó sửa hàm dò thành `return []`) vẫn báo ĐẠT — cổng xanh
    # mà không đo gì. Bốn mẫu dưới đây PHẢI bị bắt, và hai mẫu cục bộ PHẢI lọt.
    cac_mau_phai_bat = (
        'x = "https://mot-nha-cung-cap-nao-do.example/v1"',
        'x = "https" + "://" + may + "/v1"',
        'x = "HTTPS://mot-nha-cung-cap-nao-do.example/v1"',
        'x = f"https://{may}/v1"',
    )
    for mau in cac_mau_phai_bat:
        bang(
            _quet_dia_chi_ra_ngoai(mau),
            "Bộ dò KHÔNG bắt được {!r} — phép kiểm 9 đang xanh mà không đo gì.".format(mau),
        )
    for mau in ('x = "http://127.0.0.1:8000/v1"', 'x = "http://localhost:8765"'):
        bang(
            not _quet_dia_chi_ra_ngoai(mau),
            "Bộ dò bắt OAN địa chỉ cục bộ {!r}. Một cổng bắt oan là một cổng sẽ "
            "bị gỡ.".format(mau),
        )

    return "sạch ở {} tệp chạm mạng; đối chứng 4 mẫu trốn bị bắt, 2 mẫu cục bộ lọt".format(
        len(CAC_TEP_CHAM_MANG)
    )


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 3 — Bộ đọc SSE
# ══════════════════════════════════════════════════════════════════════════


def _goi_sse(chu, mo_hinh="google/gemma-4-31B-it"):
    """Dựng một dòng SSE giả đúng dạng vLLM trả về."""
    return (
        'data: {"id":"x","object":"chat.completion.chunk","model":"%s",'
        '"choices":[{"index":0,"delta":{"content":"%s"},"finish_reason":null}]}\n\n'
        % (mo_hinh, chu)
    ).encode("utf-8")


@phep_kiem("10. Bộ đọc SSE bóc đúng từng mẩu chữ từ một dòng chảy nguyên vẹn")
def kiem_sse_nguyen_ven():
    dong_chay = (
        b'data: {"model":"google/gemma-4-31B-it","choices":[{"delta":{"role":"assistant"}}]}\n\n'
        + _goi_sse("Xin")
        + _goi_sse(" chao")
        + _goi_sse(" ban")
        + b"data: [DONE]\n\n"
    )
    bo_doc = BoDocSSE()
    cac_chu = []
    xong = False
    for goi_json in bo_doc.nap(dong_chay):
        boc = boc_mau_chu(goi_json)
        if boc["chu"] is not None:
            cac_chu.append(boc["chu"])
        if boc["xong"] == "[DONE]":
            xong = True
    bang(cac_chu == ["Xin", " chao", " ban"], "Bóc sai mẩu chữ: {!r}".format(cac_chu))
    bang(xong, "Không nhận ra dấu kết thúc [DONE]")
    bang(bo_doc.con_du() == b"", "Bộ đệm phải rỗng sau một dòng chảy trọn vẹn")
    return "3 mẩu chữ đúng thứ tự + nhận [DONE], bộ đệm rỗng"


@phep_kiem("11. Bộ đọc SSE KHÔNG mất chữ khi một mẩu bị cắt đôi giữa hai gói mạng")
def kiem_sse_cat_doi():
    """Đây là chỗ dễ hỏng nhất của mọi bộ đọc SSE — xem đầu tệp cong_mo_hinh.py.

    Cắt ở BA vị trí khác nhau, vì một bộ đọc có thể đúng ở chỗ này mà sai ở chỗ
    kia: cắt giữa JSON, cắt ngay trước ký tự xuống dòng, cắt giữa hai ký tự
    xuống dòng của ranh giới sự kiện.
    """
    nguyen = _goi_sse("Xin") + _goi_sse(" chao") + b"data: [DONE]\n\n"
    ket_qua_mong_doi = ["Xin", " chao"]

    cac_vi_tri_cat = [
        len(_goi_sse("Xin")) // 2,          # giữa thân JSON của gói đầu
        len(_goi_sse("Xin")) - 2,           # ngay trước ký tự xuống dòng
        len(_goi_sse("Xin")) - 1,           # giữa hai ký tự xuống dòng
        len(nguyen) - 3,                    # sát cuối dòng chảy
    ]
    for vi_tri in cac_vi_tri_cat:
        bo_doc = BoDocSSE()
        cac_chu = []
        for goi in (nguyen[:vi_tri], nguyen[vi_tri:]):
            for goi_json in bo_doc.nap(goi):
                boc = boc_mau_chu(goi_json)
                if boc["chu"] is not None:
                    cac_chu.append(boc["chu"])
        bang(
            cac_chu == ket_qua_mong_doi,
            "Cắt ở byte {} làm mất chữ: được {!r}, cần {!r}".format(
                vi_tri, cac_chu, ket_qua_mong_doi
            ),
        )

    # Cắt từng byte một: trường hợp cực đoan, đúng cảnh mạng rất chậm.
    bo_doc = BoDocSSE()
    cac_chu = []
    for chi_so in range(len(nguyen)):
        for goi_json in bo_doc.nap(nguyen[chi_so:chi_so + 1]):
            boc = boc_mau_chu(goi_json)
            if boc["chu"] is not None:
                cac_chu.append(boc["chu"])
    bang(
        cac_chu == ket_qua_mong_doi,
        "Nạp từng byte một làm mất chữ: {!r}".format(cac_chu),
    )
    return "đúng ở 4 vị trí cắt + khi nạp từng byte một"


@phep_kiem("12. Bộ đọc SSE bỏ qua nhịp giữ kết nối và dòng rỗng, phát hiện gói dở")
def kiem_sse_nhip_va_goi_do():
    bo_doc = BoDocSSE()
    cac_chu = []
    dong_chay = b": nhip giu ket noi\n\n" + _goi_sse("A") + b"\n" + _goi_sse("B")
    for goi_json in bo_doc.nap(dong_chay):
        boc = boc_mau_chu(goi_json)
        if boc["chu"] is not None:
            cac_chu.append(boc["chu"])
    bang(cac_chu == ["A", "B"], "Nhịp giữ kết nối làm hỏng bộ đọc: {!r}".format(cac_chu))

    # Dòng chảy đứt giữa một gói: bộ đệm phải còn dư, để lớp trên biết mà báo.
    bo_doc_do = BoDocSSE()
    list(bo_doc_do.nap(b'data: {"choices":[{"delta":{"cont'))
    bang(
        bo_doc_do.con_du() != b"",
        "Gói dở dang phải nằm lại trong bộ đệm — đó là dấu hiệu duy nhất để biết "
        "câu trả lời bị cắt chứ không phải đã xong.",
    )
    return "bỏ qua nhịp/dòng rỗng, giữ lại gói dở trong bộ đệm"


@phep_kiem("13. Máy chủ báo lỗi giữa dòng chảy thì KHÔNG bị nuốt thành câu rỗng")
def kiem_sse_loi_giua_dong():
    try:
        boc_mau_chu('{"error":{"message":"het bo nho GPU"}}')
    except LoiMayNoiBoTraLoiSai as loi:
        bang("het bo nho GPU" in str(loi), "Phải chuyển nguyên lời máy chủ cho người đọc")
        return "gói error thành LoiMayNoiBoTraLoiSai, giữ nguyên lời máy chủ"
    raise AssertionError(
        "Gói error bị bỏ qua — lỗi im lặng biến thành 'câu trả lời rỗng', và người "
        "dùng tưởng mô hình không biết trả lời."
    )


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 4 — Đối chiếu tên mô hình
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("14. doi_chieu_mo_hinh trả tên THẬT khi máy chủ báo khác tên gửi đi")
def kiem_doi_chieu_mo_hinh():
    that = doi_chieu_mo_hinh("google/gemma-4-31B-it", "google/gemma-4-31B-it-AWQ")
    bang(
        that == "google/gemma-4-31B-it-AWQ",
        "Tên máy chủ khai phải THẮNG tên gửi đi, đang trả {!r}".format(that),
    )
    bang(
        doi_chieu_mo_hinh("a", None) == "a",
        "Máy chủ không khai gì thì mới lấy tên gửi đi",
    )
    bang(doi_chieu_mo_hinh("a", "  ") == "a", "Tên rỗng/toàn khoảng trắng không được thắng")
    bang(doi_chieu_mo_hinh("a", " b ") == "b", "Phải cắt khoảng trắng hai đầu")
    return "tên máy chủ khai thắng tên gửi đi; chỉ lùi về tên gửi khi máy chủ im lặng"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 5 — Backend giả
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("15. Backend giả TỪ CHỐI chạy khi chưa được bật tường minh")
def kiem_gia_lap_chua_bat():
    with MoiTruongTam(BDSG_DUNG_GIA_LAP=None):
        try:
            CongMoHinhGiaLap()
        except LoiGiaLapChuaBat:
            pass
        else:
            raise AssertionError("Backend giả chạy được khi chưa bật — chữ bịa có thể ra ngoài")

    # Các giá trị "gần giống bật" phải bị coi là TẮT.
    for gia_tri in ("0", "true", "yes", "", " "):
        with MoiTruongTam(BDSG_DUNG_GIA_LAP=gia_tri):
            try:
                CongMoHinhGiaLap()
            except LoiGiaLapChuaBat:
                continue
            raise AssertionError(
                "Giá trị {!r} bật được backend giả. Chỉ đúng chuỗi '1' mới được "
                "tính là bật.".format(gia_tri)
            )
    return "chỉ đúng chuỗi '1' mới bật; '0'/'true'/'yes'/rỗng đều bị từ chối"


@phep_kiem("16a. Tên tự khai của backend giả KHÔNG được giống tên một mô hình thật")
def kiem_ten_gia_lap_tu_to_cao():
    """Khoá LỚP 3 của backend giả bằng tính chất của chính CÁI TÊN.

    SỬA 26/09/2026 — phép kiểm 16 bản đầu so `thu_thap["mo_hinh_that"]` với hằng
    `MA_MO_HINH_GIA` đọc từ chính mô-đun ấy. Đó là so một thứ với chính nó. ĐÃ ĐO:
    đổi hằng thành "google/gemma-4-31B-it" rồi chạy lại — vẫn 18/18 ĐẠT. Nghĩa là
    backend giả có thể mạo danh mô hình thật trên nhãn "câu trả lời đến từ …" của
    giao diện mà không cổng nào kêu, đúng thứ lớp 3 sinh ra để chặn.

    Phép kiểm này không so với hằng nữa; nó ĐÒI cái tên phải tự tố cáo:
    có chữ "gia-lap", và không mang tên của một họ mô hình thật nào.
    """
    ten = MA_MO_HINH_GIA
    bang(
        "gia-lap" in ten.lower(),
        "Tên backend giả phải chứa 'gia-lap' để người đọc nhận ra ngay trên nhãn "
        "giao diện, đang là {!r}".format(ten),
    )
    bang(
        "khong-phai-mo-hinh-that" in ten.lower(),
        "Tên phải nói thẳng nó KHÔNG phải mô hình thật, đang là {!r}".format(ten),
    )
    # Không mang theo danh sách nhà cung cấp (xem bài học trong
    # cong/khong-tham-chieu-ngoai.py). Chỉ đối chiếu với mã mô hình mà chính kho
    # này cấu hình để phục vụ — nếu tên giả trùng hay chứa nó thì là mạo danh.
    that = _cau_hinh.MO_HINH_MAC_DINH
    bang(
        ten != that and that.lower() not in ten.lower(),
        "Tên backend giả {!r} mang tên mô hình thật {!r} — nó sẽ mạo danh mô hình "
        "thật trên nhãn 'câu trả lời đến từ …'.".format(ten, that),
    )
    bang(
        "/" not in ten,
        "Tên backend giả không được viết theo dạng <chủ>/<mô hình> của Hugging "
        "Face, vì dạng ấy khiến người đọc tưởng là trọng số thật: {!r}".format(ten),
    )
    return "tên {!r} tự tố cáo và không trùng/chứa {!r}".format(ten, that)


@phep_kiem("16. Backend giả sinh đủ chữ và tự khai mình là GIẢ")
def kiem_gia_lap_chay():
    with MoiTruongTam(
        BDSG_DUNG_GIA_LAP="1", BDSG_GIA_LAP_LOI=None, BDSG_GIA_LAP_TRE_GIAY="0"
    ):
        cong = CongMoHinhGiaLap()
        thu_thap = {}
        cac_mau = list(cong.hoi_dong_chay([{"role": "user", "content": "chao"}], thu_thap=thu_thap))
        danh_sach = cong.danh_sach_mo_hinh()

    bang(len(cac_mau) > 5, "Phải sinh nhiều mẩu chữ, đang có {}".format(len(cac_mau)))
    bang(int(thu_thap["so_mau"]) == len(cac_mau), "so_mau đếm sai")
    bang(thu_thap["ly_do_dung"] == "stop", "Phải khai lý do dừng khi xong sạch")
    bang(
        thu_thap["mo_hinh_that"] == MA_MO_HINH_GIA,
        "moHinhThat phải là tên tự tố cáo, đang là {!r}".format(thu_thap["mo_hinh_that"]),
    )
    ca_cau = "".join(cac_mau)
    bang(
        MA_MO_HINH_GIA in ca_cau,
        "Chính câu trả lời cũng phải tự khai là giả — đây là lớp khoá cuối cùng, "
        "lớp duy nhất không phụ thuộc vào ai nhớ điều gì.",
    )
    bang(danh_sach[0]["ma"] == MA_MO_HINH_GIA, "danh_sach_mo_hinh phải khai tên giả")
    return "{} mẩu chữ, moHinhThat = {}".format(len(cac_mau), MA_MO_HINH_GIA)


@phep_kiem("17. Backend giả diễn được 3 đường hỏng, ném ĐÚNG lớp lỗi của mã thật")
def kiem_gia_lap_cac_duong_loi():
    # (a) máy nội bộ chết trước khi sinh chữ nào
    with MoiTruongTam(
        BDSG_DUNG_GIA_LAP="1", BDSG_GIA_LAP_LOI="khong-noi-duoc", BDSG_GIA_LAP_TRE_GIAY="0"
    ):
        cong = CongMoHinhGiaLap()
        try:
            list(cong.hoi_dong_chay([{"role": "user", "content": "chao"}]))
        except LoiKhongNoiDuocMayNoiBo as loi:
            bang("NỘI BỘ" in str(loi) or "nội bộ" in str(loi), "Phải nói rõ máy nội bộ")
        else:
            raise AssertionError("Chế độ 'khong-noi-duoc' không ném lỗi")

    # (b) đứt giữa dòng, SAU khi người dùng đã nhận được một phần chữ
    with MoiTruongTam(
        BDSG_DUNG_GIA_LAP="1", BDSG_GIA_LAP_LOI="giua-dong", BDSG_GIA_LAP_TRE_GIAY="0"
    ):
        cong = CongMoHinhGiaLap()
        da_nhan = []
        try:
            for mau in cong.hoi_dong_chay([{"role": "user", "content": "chao"}]):
                da_nhan.append(mau)
        except LoiKhongNoiDuocMayNoiBo:
            pass
        else:
            raise AssertionError("Chế độ 'giua-dong' không ném lỗi")
        bang(
            len(da_nhan) > 0,
            "Phải đứt SAU khi đã trả một phần chữ — đúng cảnh khó nhất cho giao "
            "diện: phải giữ phần đã nhận VÀ báo lỗi.",
        )

    # (c) máy sống nhưng từ chối yêu cầu
    with MoiTruongTam(
        BDSG_DUNG_GIA_LAP="1", BDSG_GIA_LAP_LOI="may-tra-loi-sai", BDSG_GIA_LAP_TRE_GIAY="0"
    ):
        cong = CongMoHinhGiaLap()
        try:
            list(cong.hoi_dong_chay([{"role": "user", "content": "chao"}]))
        except LoiMayNoiBoTraLoiSai:
            pass
        else:
            raise AssertionError("Chế độ 'may-tra-loi-sai' không ném LoiMayNoiBoTraLoiSai")

    return "3/3 đường hỏng ném đúng lớp lỗi; đường (b) giữ được phần chữ đã nhận"


@phep_kiem("18. Bộ cắt mẩu chữ của backend giả không làm rơi ký tự nào")
def kiem_gia_lap_khong_roi_ky_tu():
    with MoiTruongTam(
        BDSG_DUNG_GIA_LAP="1", BDSG_GIA_LAP_LOI=None, BDSG_GIA_LAP_TRE_GIAY="0"
    ):
        cong = CongMoHinhGiaLap()
        ca_cau = "".join(cong.hoi_dong_chay([{"role": "user", "content": "chao"}]))
    bang(
        ca_cau == _gia_lap._CAU_TRA_LOI_BIA,
        "Ghép các mẩu lại KHÔNG ra câu gốc. Một bộ cắt làm rơi khoảng trắng sẽ "
        "cho mọi phép so chuỗi về sau một sai số không ai truy ra được.",
    )
    return "ghép {} ký tự khớp tuyệt đối câu gốc".format(len(ca_cau))


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 6 — CongMoHinh THẬT, chạy qua HTTP thật trên máy này
#
# Vì sao cần nhóm này: các phép kiểm 10–13 chỉ chạm BoDocSSE và boc_mau_chu, còn
# phép kiểm 8 chỉ chạm danh_sach_mo_hinh. Đường sinh chữ của CongMoHinh —
# hoi_dong_chay, tức đúng đường mà mọi câu hỏi của người dùng sẽ đi qua — trước
# 26/09/2026 KHÔNG có phép kiểm nào trong kho. Nó từng được thử bằng một tệp
# ngoài kho; một phép thử không nằm trong kho thì không phải là cổng.
# ══════════════════════════════════════════════════════════════════════════


def _may_chu_sse_mot_lan(than_tra_loi, cat_lam_hai=True):
    """Dựng một máy chủ HTTP thật trên 127.0.0.1, phục vụ đúng MỘT yêu cầu.

    Trả về (số cổng, luồng). Máy chủ luôn kết thúc bằng đóng SẠCH nửa phía ghi
    (shutdown WR) — cố ý, vì đó là cách một máy chủ hoặc một proxy lịch sự kết
    thúc, và chính là ca mà phép kiểm truncation cũ để lọt.

    `cat_lam_hai`: ghi thân trả lời làm HAI lần ghi, cắt vào giữa. Ép đường chạy
    thật phải ghép bộ đệm, chứ không chỉ ghép trong phép kiểm đơn vị.
    """
    o = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    o.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    o.bind(("127.0.0.1", 0))
    o.listen(1)
    so_cong = o.getsockname()[1]

    def phuc_vu():
        try:
            noi, _ = o.accept()
            noi.recv(65536)
            dau = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/event-stream\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8")
            than = than_tra_loi.encode("utf-8")
            if cat_lam_hai and len(than) > 4:
                giua = len(than) // 2
                noi.sendall(dau + than[:giua])
                noi.sendall(than[giua:])
            else:
                noi.sendall(dau + than)
            noi.shutdown(socket.SHUT_WR)
            try:
                noi.recv(65536)
            except OSError:
                pass
            noi.close()
        finally:
            o.close()

    luong = threading.Thread(target=phuc_vu, daemon=True)
    luong.start()
    return so_cong, luong


def _goi_chu(chu, mo_hinh="google/gemma-4-31B-it"):
    return "data: " + json.dumps(
        {
            "model": mo_hinh,
            "choices": [{"index": 0, "delta": {"content": chu}, "finish_reason": None}],
        },
        ensure_ascii=False,
    ) + "\n\n"


def _cong_toi(so_cong):
    with MoiTruongTam(
        BDSG_VLLM_URL="http://127.0.0.1:{}/v1".format(so_cong),
        BDSG_HET_GIO_GIAY="5",
        BDSG_VLLM_KHOA=None,
    ):
        return CongMoHinh(CauHinhPhucVu.tu_moi_truong())


@phep_kiem("19. CongMoHinh THẬT sinh đủ chữ qua HTTP và lấy đúng tên máy chủ khai")
def kiem_cong_that_dong_chay_tron():
    than = (
        _goi_chu("Xin", mo_hinh="google/gemma-4-31B-it-AWQ")
        + _goi_chu(" chao", mo_hinh="google/gemma-4-31B-it-AWQ")
        + _goi_chu(" ban", mo_hinh="google/gemma-4-31B-it-AWQ")
        + 'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
        + "data: [DONE]\n\n"
    )
    so_cong, luong = _may_chu_sse_mot_lan(than, cat_lam_hai=True)
    cong = _cong_toi(so_cong)
    thu_thap = {}
    cac_chu = list(cong.hoi_dong_chay([{"role": "user", "content": "chao"}], thu_thap=thu_thap))
    luong.join(5)

    bang(cac_chu == ["Xin", " chao", " ban"], "Mất chữ trên đường thật: {!r}".format(cac_chu))
    bang(int(thu_thap["so_mau"]) == 3, "so_mau sai: {!r}".format(thu_thap["so_mau"]))
    bang(
        thu_thap["mo_hinh_that"] == "google/gemma-4-31B-it-AWQ",
        "moHinhThat phải là tên MÁY CHỦ khai (…-AWQ), không phải tên ta gửi đi; "
        "đang là {!r}".format(thu_thap["mo_hinh_that"]),
    )
    return "3 mẩu chữ qua 2 lần ghi mạng, moHinhThat = tên máy chủ khai"


@phep_kiem("20. Dòng chảy đứt mà KHÔNG có dấu kết thúc thì PHẢI báo lỗi, không im")
def kiem_cong_that_dut_giua_chung():
    """Họ lỗi "hỏng mà không báo" ở dạng khó thấy nhất của nó.

    ĐÃ ĐO 26/09/2026: bản đầu chỉ báo lỗi khi bộ đệm CÒN DƯ. Máy chủ đóng sạch
    ngay tại ranh giới một dòng SSE trọn vẹn thì bộ đệm rỗng, và hàm trả về êm
    như thể câu trả lời đã xong — giao diện hiện một câu cụt, không có lỗi nào.
    Ba ca dưới đây khoá cả hai đường về, và ca (c) giữ cho phép kiểm không siết
    quá tay với máy chủ chỉ gửi finish_reason mà không gửi [DONE].
    """
    # (a) đứt GIỮA một gói dở dang — bộ đệm còn dư
    so_cong, luong = _may_chu_sse_mot_lan(
        _goi_chu("Xin") + 'data: {"choices":[{"delta":{"cont', cat_lam_hai=False
    )
    try:
        list(_cong_toi(so_cong).hoi_dong_chay([{"role": "user", "content": "chao"}]))
        raise AssertionError("Gói dở dang mà không báo lỗi")
    except LoiKhongNoiDuocMayNoiBo as loi:
        bang("cắt" in str(loi), "Thông báo phải nói câu trả lời bị cắt")
    luong.join(5)

    # (b) đứt SẠCH ngay tại ranh giới dòng — bộ đệm RỖNG. Đây là ca đã lọt.
    so_cong, luong = _may_chu_sse_mot_lan(
        _goi_chu("Xin") + _goi_chu(" chao"), cat_lam_hai=False
    )
    da_nhan = []
    try:
        for mau in _cong_toi(so_cong).hoi_dong_chay([{"role": "user", "content": "chao"}]):
            da_nhan.append(mau)
        raise AssertionError(
            "Dòng chảy kết thúc không có [DONE] lẫn finish_reason mà KHÔNG báo "
            "lỗi. Giao diện sẽ hiện {!r} như một câu trả lời đã xong.".format(
                "".join(da_nhan)
            )
        )
    except LoiKhongNoiDuocMayNoiBo as loi:
        bang("nội bộ" in str(loi).lower(), "Thông báo phải nói rõ máy NỘI BỘ")
        bang(len(da_nhan) == 2, "Phải trả hết phần chữ đã nhận rồi mới báo lỗi")
    luong.join(5)

    # (c) ĐỐI CHỨNG: có finish_reason nhưng KHÔNG có [DONE] → KHÔNG được báo lỗi.
    # Không phải máy chủ tương thích OpenAI nào cũng gửi nhãn [DONE]; siết quá
    # tay ở đây thì mọi câu trả lời hợp lệ của những máy ấy đều thành lỗi giả.
    so_cong, luong = _may_chu_sse_mot_lan(
        _goi_chu("Xin")
        + 'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
        cat_lam_hai=False,
    )
    thu_thap = {}
    cac_chu = list(
        _cong_toi(so_cong).hoi_dong_chay(
            [{"role": "user", "content": "chao"}], thu_thap=thu_thap
        )
    )
    luong.join(5)
    bang(cac_chu == ["Xin"], "Đối chứng (c) mất chữ: {!r}".format(cac_chu))
    bang(thu_thap["ly_do_dung"] == "stop", "Phải đọc được finish_reason")

    return "(a) gói dở → lỗi · (b) đứt sạch không dấu kết thúc → lỗi · (c) chỉ có finish_reason → KHÔNG lỗi"


# ══════════════════════════════════════════════════════════════════════════

CAC_PHEP_KIEM = [
    kiem_thieu_url,
    kiem_url_sai_giao_thuc,
    kiem_so_khong_hop_le,
    kiem_tran_lon_hon_ngu_canh,
    kiem_ngu_canh_mac_dinh,
    kiem_tom_tat_khong_lo_khoa,
    kiem_khong_nhan_vo_trong_so,
    kiem_may_noi_bo_khong_chay,
    kiem_khong_co_duong_ra_ngoai,
    kiem_sse_nguyen_ven,
    kiem_sse_cat_doi,
    kiem_sse_nhip_va_goi_do,
    kiem_sse_loi_giua_dong,
    kiem_doi_chieu_mo_hinh,
    kiem_gia_lap_chua_bat,
    kiem_ten_gia_lap_tu_to_cao,
    kiem_gia_lap_chay,
    kiem_gia_lap_cac_duong_loi,
    kiem_gia_lap_khong_roi_ky_tu,
    kiem_cong_that_dong_chay_tron,
    kiem_cong_that_dut_giua_chung,
]


def main():
    print("=" * 78)
    print("BÀI TỰ KIỂM — phuc-vu/ (lớp phục vụ mô hình)")
    print("Python {}.{}.{}".format(*sys.version_info[:3]))
    print("KHÔNG cần mạng, KHÔNG cần GPU, KHÔNG cần máy vLLM nào đang chạy.")
    print("=" * 78)
    print()

    tat_ca_dat = True
    for phep in CAC_PHEP_KIEM:
        if not phep():
            tat_ca_dat = False

    print()
    print("=" * 78)
    so_dat = sum(1 for _, dat, _ in _KET_QUA if dat)
    so_hong = len(_KET_QUA) - so_dat
    if tat_ca_dat:
        print("KẾT QUẢ: {}/{} ĐẠT.".format(so_dat, len(_KET_QUA)))
        print()
        print("Nghĩa là gì: cấu hình từ chối chạy khi thiếu biến bắt buộc; khoá không lọt")
        print("vào bản tóm tắt; máy nội bộ không chạy thì báo đúng là lỗi NỘI BỘ; bộ đọc SSE")
        print("không mất chữ kể cả khi gói mạng cắt vào giữa một mẩu; tên mô hình hiện ra là")
        print("tên máy chủ THẬT khai, không phải tên ta gửi đi.")
        print()
        print("Nghĩa là gì KHÔNG: bài này KHÔNG nói gì về mô hình. Tính đến 26/09/2026 dự án")
        print("chưa có GPU, CHƯA từng nạp google/gemma-4-31B-it, CHƯA đo độ trễ, CHƯA đo số")
        print("yêu cầu đồng thời, CHƯA đo bộ nhớ đệm KV. Toàn bộ các số ấy là CHƯA ĐO.")
        print("Và trọng số là của Google (Apache-2.0), không phải của BDSG.")
    else:
        print("KẾT QUẢ: {}/{} ĐẠT, {} HỎNG.".format(so_dat, len(_KET_QUA), so_hong))
        print()
        print("Các phép kiểm hỏng:")
        for ten, dat, ghi_chu in _KET_QUA:
            if not dat:
                print("  - {}: {}".format(ten, ghi_chu))
    print("=" * 78)
    return 0 if tat_ca_dat else 1


if __name__ == "__main__":
    sys.exit(main())
