#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/nhat_ky.py — AI ĐÃ LÀM GÌ.

Mỗi lời gọi công cụ đi qua nhân để lại ĐÚNG MỘT DÒNG JSON. Một dòng một bản ghi
(JSON Lines) chứ không phải một mảng JSON lớn: mảng chỉ đọc được khi đã đóng
ngoặc, nên tiến trình bị giết giữa chừng là mất sạch tệp; còn từng dòng thì cắt
ở đâu cũng đọc được tới đó, `tail -f` xem trực tiếp được, `grep` được.

⚠ LÀM MỜ THAM SỐ — PHẦN QUAN TRỌNG NHẤT CỦA TỆP NÀY
---------------------------------------------------
Tham số công cụ ĐI QUA nhân, và chúng chứa thứ người ta gửi kèm: email khách,
số điện thoại, mật khẩu tạm, khoá API của nền tảng đích. Một hệ thống ghi nhật
ký đầy đủ mà chép nguyên các thứ ấy thì chính tệp nhật ký trở thành chỗ rò lớn
nhất trong hệ — và là chỗ rò tệ nhất, vì nhật ký được sao chép đi khắp nơi để
phân tích, được đưa cho người ngoài xem khi gỡ lỗi, và giữ lâu hơn dữ liệu gốc.

Cho nên `lam_mo()` chạy TRƯỚC khi ghi, và nó làm mờ theo HAI hướng độc lập:
  1. theo TÊN TRƯỜNG (mat_khau, token, khoa_api, cookie…)
  2. theo HÌNH DẠNG GIÁ TRỊ (chuỗi kiểu JWT, chuỗi hex dài, "Bearer …", email,
     số điện thoại) — kể cả khi tên trường trông vô hại.
Hai hướng vì mỗi hướng đều có lỗ: một khoá nằm trong trường tên `ghi_chu` thì
hướng 1 bỏ sót, còn một mật khẩu là "1234" thì hướng 2 bỏ sót.

CĂNG THẲNG PHẢI NÓI RA: LÀM MỜ QUÁ TAY CŨNG LÀ HỎNG.
Nếu nhật ký làm mờ cả `tu_khoa` của một lệnh tìm kiếm thì nó hết dùng được để
gỡ lỗi, và thứ hết dùng được thì người ta TẮT. Một nhật ký bị tắt bảo vệ được 0
byte. Vì vậy có `MIEN_TRU_TRUONG`: một danh sách ngắn, khai tường minh, những
tên trường CHỨA chữ nhạy cảm nhưng thật ra vô hại.

KHÔNG GHI GIÁ TRỊ TRẢ VỀ
------------------------
Bản ghi chỉ có KIỂU và KÍCH THƯỚC của kết quả, không có nội dung. Kết quả là
chỗ dữ liệu khách đi ra: một lệnh tìm hồ sơ trả về 50 hồ sơ đầy đủ, ghi vào
nhật ký là chép nguyên 50 hồ sơ ấy sang một nơi ít được bảo vệ hơn. Cần xem nội
dung thì bật `ghi_ket_qua=True` một cách tường minh, và tự chịu.

ĐỘ DÀI BÍ MẬT CŨNG LÀ THÔNG TIN
-------------------------------
Chỗ làm mờ KHÔNG ghi số ký tự chính xác, chỉ ghi một BẬC (rỗng / ngắn / vừa /
dài). Biết mật khẩu dài đúng 8 ký tự là đã thu hẹp việc dò rất nhiều. Bậc thì đủ
để trả lời câu hỏi gỡ lỗi hay gặp nhất — "tham số ấy có rỗng không".

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import json
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

# ── Kết quả chuẩn hoá của một lời gọi ────────────────────────────────────────
THANH_CONG = "thanh-cong"
TU_CHOI = "tu-choi"
LOI = "loi"

DAU_LAM_MO = "\u00ab" + "da-lam-mo"  # «da-lam-mo:...»


class LoiNhatKy(RuntimeError):
    """Không ghi được nhật ký.

    Ném ra chứ không nuốt. Nhân bắt lỗi này và TỪ CHỐI lời gọi (xem
    `dinh_tuyen.Nhan`): một hệ thống vẫn chạy tiếp khi sổ sách hỏng là một hệ
    thống không có sổ sách, và ta chỉ biết điều đó sau sự cố.
    """


# ── Hướng 1: tên trường ──────────────────────────────────────────────────────
# So khớp theo TỪ sau khi tách tên trường bằng ký tự không phải chữ/số, cộng
# thêm một ít so khớp theo chuỗi con cho các tên viết liền (apikey, matkhau).
TU_NHAY_CAM = frozenset(
    {
        "mat_khau", "matkhau", "password", "passwd", "pwd", "pass",
        "token", "secret", "bi_mat", "bimat",
        "key", "apikey", "api_key",
        "authorization", "auth", "bearer",
        "cookie", "session", "sid",
        "chung_thu", "chungthu", "credential", "credentials",
        "private", "riengtu", "rieng_tu",
        "otp", "pin", "cvv", "cvc", "salt",
        "chu_ky", "chuky", "signature", "sig",
        "cccd", "cmnd", "passport", "ho_chieu",
        "so_the", "sothe", "card", "iban",
    }
)
CHUOI_CON_NHAY_CAM = ("password", "matkhau", "apikey", "secret", "token", "bimat")

# ── Từ MƠ HỒ: nhạy cảm hay không tuỳ CẢ TÊN TRƯỜNG ───────────────────────────
# Sửa 26/09/2026. "khoa" và "phien" trước đây nằm thẳng trong TU_NHAY_CAM, mà
# `_ten_truong_nhay_cam` so khớp theo TỪ. Trong một kho viết bằng tiếng Việt
# KHÔNG DẤU, hai từ ấy mang nhiều nghĩa vô hại hơn là nghĩa nhạy cảm:
#
#     phien_ban, so_phien_ban   → phiên bản phần mềm
#     ma_khoa_hoc, ten_khoa     → khoá học, khoa phòng
#
# Đo được: cả bốn trường trên bị che thành vô nghĩa. Đầu tệp này đã tự cảnh báo
# đúng nguy cơ ấy — nhật ký hết dùng được thì người ta TẮT, và nhật ký bị tắt
# bảo vệ được 0 byte.
#
# CÁCH SỬA KHÔNG CHỌN: nhét bốn tên ấy vào MIEN_TRU_TRUONG. Đó là đập chuột
# chũi: lần sau sẽ tới `khoa_dao_tao`, `phien_hop`, `truong_khoa`… và danh sách
# miễn trừ dài ra mãi trong khi luật sinh ra lỗi thì vẫn nguyên.
#
# LUẬT THAY THẾ: một từ mơ hồ làm cả tên trường thành nhạy cảm, TRỪ KHI trong
# tên có một từ VÔ HẠI khai bên dưới. `khoa`, `khoa_api`, `khoa_truy_cap`,
# `ma_phien` → nhạy cảm. `ma_khoa_hoc`, `ten_khoa`, `phien_ban`, `tu_khoa` →
# không.
#
# CHIỀU MẶC ĐỊNH LÀ CHE, KHÔNG PHẢI HIỆN. Sửa lại 26/09/2026, cùng ngày.
#
#   Bản đầu của luật này viết ngược: nhạy cảm chỉ khi MỌI từ trong tên đều là
#   từ mơ hồ hoặc từ BỔ TRỢ. Nghe thì chặt, nhưng nó biến danh sách bổ trợ
#   thành thứ phải KỂ ĐỦ mới che được, và một danh sách kể-đủ thì luôn thiếu.
#   Đo được ngay trên chính kho này — sáu tên trường sau đi thẳng vào nhật ký
#   NGUYÊN VĂN sau bản vá, trong khi trước bản vá chúng được che:
#
#       khoa_truy_cap   khoa_ma_hoa   ma_phien
#       khoa_ky         khoa_cu       khoa_moi
#
#   `khoa_truy_cap` đúng là "access key" viết bằng tiếng Việt không dấu —
#   danh sách bổ trợ có "access" mà không có "truy"/"cap", nên nó lọt. Đây là
#   cùng một họ lỗi với thứ bản vá định chữa, chỉ đổi chiều: lần trước là che
#   quá tay, lần này là hở. Hở thì im lặng, nên tệ hơn.
#
#   Nay mặc định của một từ mơ hồ là CHE. Muốn hiện thì phải nói ra bằng một từ
#   VÔ HẠI, và danh sách vô hại có thiếu thì hậu quả là một trường vô hại bị
#   che — thấy ngay, sửa được, không mất gì.
TU_MO_HO = frozenset({"khoa", "phien"})

# Từ BỔ TRỢ: đi kèm một từ mơ hồ thì XÁC NHẬN nghĩa nhạy cảm, và thắng cả từ vô
# hại (`ten_khoa_api` là khoá, không phải tên khoa). Nay chỉ còn để phá hoà —
# mặc định đã là che — nên thêm vào đây không nới quyền che của ai.
TU_BO_TRO = frozenset(
    {
        "api", "llm", "secret", "private", "rieng", "bi", "mat",
        "access", "refresh", "token", "bearer", "auth", "id",
        "xac", "thuc", "truy", "cap", "ky",
    }
)

# Từ VÔ HẠI: đi kèm một từ mơ hồ thì GỠ nghĩa nhạy cảm. Đây mới là danh sách
# phải cân nhắc từng dòng — mỗi từ thêm vào là một lần NỚI CHỖ HỞ. Đổi lại,
# thiếu một từ ở đây chỉ gây che quá tay, tức là hỏng mà KÊU.
TU_VO_HAI = frozenset(
    {
        "ban",      # phien_ban — phiên bản
        "hoc",      # khoa_hoc, ma_khoa_hoc — khoá học
        "ten",      # ten_khoa — tên khoa
        "truong",   # truong_khoa — trưởng khoa
        "tu",       # tu_khoa — từ khoá
        "dao", "tao",   # khoa_dao_tao
        "hop",      # phien_hop — phiên họp
        "mon", "lop", "vien", "sinh", "nganh", "phong",
    }
)

# Những tên trường CHỨA chữ nhạy cảm nhưng vô hại. Danh sách này phải NGẮN và
# phải khai từng cái — xem phần "làm mờ quá tay" ở đầu tệp.
MIEN_TRU_TRUONG = frozenset(
    {
        "tu_khoa",        # từ khoá tìm kiếm
        "khoa_chinh",     # khoá chính của bảng
        "khoa_ngoai",     # khoá ngoại
        "khoa_sap_xep",   # cột sắp xếp
        "so_khoa",        # số lượng khoá
        "loai_khoa",
        "key_type",
        "sort_key",
        "primary_key",
    }
)

MAU_TACH_TU = re.compile(r"[^a-z0-9]+")

# ── Hướng 2: hình dạng giá trị ───────────────────────────────────────────────
# Các mẫu dưới đây CỐ Ý không cố nhận diện nhà cung cấp cụ thể nào. Nhận diện
# theo hình dạng chung thì bắt được cả khoá của nhà cung cấp chưa ai nghĩ tới.
#
# KHÔNG NEO BẰNG ^…$ NỮA. Sửa 26/09/2026.
#
#   Bản trước neo 5/6 mẫu bằng `^…$` trong khi chỗ dùng gọi `mau.search()`. Hệ
#   quả: mẫu chỉ khớp khi bí mật là TOÀN BỘ giá trị chuỗi. Mà hình dạng hay gặp
#   nhất ngoài đời lại là bí mật nằm GIỮA một câu — người dùng dán nguyên câu
#   báo lỗi, nguyên lệnh curl, nguyên chuỗi kết nối vào tham số. Đo được: thẻ
#   JWT, chuỗi kết nối có mật khẩu, khoá kiểu GitHub và chuỗi hex dài đều đi
#   thẳng vào nhật ký NGUYÊN VĂN, và `so_truong_da_lam_mo` báo 0 nên không có
#   dấu hiệu nào cho thấy vừa rò.
#
#   Nay mỗi mẫu dùng ranh giới nhìn-trước/nhìn-sau thay cho neo đầu-cuối: khớp
#   được ở giữa câu, nhưng không cắt nửa chừng một chuỗi dài hơn. Chỗ dùng
#   (`che_chuoi_theo_hinh_dang`) che ĐÚNG đoạn khớp và giữ lại phần còn lại của
#   câu — che cả câu thì lại rơi vào lỗi "làm mờ quá tay" ở đầu tệp.
_KY_TU_KHOA = r"A-Za-z0-9+/_\-"   # tập ký tự một chuỗi khoá/thẻ hay dùng

MAU_GIA_TRI_NHAY_CAM: Tuple[Tuple[str, "re.Pattern"], ...] = (
    ("kieu-bearer", re.compile(r"(?i)\b(?:bearer|basic|digest)\s+[A-Za-z0-9+/=_.\-]{8,}")),
    ("khoi-khoa-pem", re.compile(r"-----BEGIN [A-Z ]*(?:PRIVATE KEY|CERTIFICATE)-----")),
    # Ba đoạn ngăn bằng dấu chấm, đoạn đầu mở bằng 'eyJ' — hình dạng thẻ JWT.
    (
        "kieu-jwt",
        re.compile(
            r"(?<![%s])ey[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{4,}"
            r"(?![%s])" % (_KY_TU_KHOA, _KY_TU_KHOA)
        ),
    ),
    # Chuỗi hex dài: băm, khoá đối xứng, mã phiên.
    (
        "hex-dai",
        re.compile(r"(?<![%s])[0-9a-fA-F]{32,}(?![%s])" % (_KY_TU_KHOA, _KY_TU_KHOA)),
    ),
    # Chuỗi base64url dài, không khoảng trắng: khoá hoặc thẻ.
    (
        "chuoi-ngau-nhien-dai",
        re.compile(
            r"(?<![%s=])[%s]{40,}={0,2}(?![%s])" % (_KY_TU_KHOA, _KY_TU_KHOA, _KY_TU_KHOA)
        ),
    ),
    # Chuỗi kết nối có mật khẩu nhúng.
    (
        "chuoi-ket-noi",
        re.compile(r"(?i)(?<![a-z0-9+.\-])[a-z][a-z0-9+.\-]*://[^\s:/@]+:[^\s@/]+@"),
    ),
)

MAU_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
# Số điện thoại: 8–15 chữ số, cho phép dấu cách/gạch/ngoặc/dấu cộng ở giữa.
MAU_DIEN_THOAI = re.compile(r"^\+?[\d][\d\s().\-]{6,18}\d$")

# Trần chống "bom nhật ký": một tham số lồng sâu hoặc một danh sách triệu phần
# tử sẽ biến mỗi lời gọi thành một dòng nhật ký khổng lồ, và đó vừa là cách làm
# đầy đĩa vừa là cách làm chậm cả nhân.
DO_SAU_TOI_DA = 6
SO_PHAN_TU_TOI_DA = 50
SO_TRUONG_TOI_DA = 50
DO_DAI_CHUOI_TOI_DA = 200


def _bac_do_dai(n: int) -> str:
    """Bậc độ dài thay cho số chính xác — xem phần đầu tệp.

    Bậc cuối nói thêm "đã cắt". Lý do: một chuỗi 5.000 ký tự khớp mẫu bí mật
    được thay bằng một nhãn ngắn, tức là trần chống bom nhật ký ĐÃ cắt nó —
    nhưng nếu nhãn không nói gì thì người vận hành đọc nhật ký không phân biệt
    được chuỗi 33 ký tự với chuỗi 5.000 ký tự, và một lần cắt IM LẶNG đúng là
    họ lỗi mà kho này đặt tên riêng. Vẫn KHÔNG ghi số ký tự chính xác: độ dài
    của một bí mật cũng là thông tin.
    """
    if n == 0:
        return "rỗng"
    if n <= 8:
        return "ngắn"
    if n <= 32:
        return "vừa"
    if n <= DO_DAI_CHUOI_TOI_DA:
        return "dài"
    return "dài, đã cắt"


def _lam_mo_chuoi(gt: str, loai: str) -> str:
    return "%s:%s:%s%s" % (DAU_LAM_MO, loai, _bac_do_dai(len(gt)), "\u00bb")


def _ten_truong_nhay_cam(ten: str) -> bool:
    t = str(ten).strip().lower()
    if t in MIEN_TRU_TRUONG:
        return False
    lien = MAU_TACH_TU.sub("", t)
    for con in CHUOI_CON_NHAY_CAM:
        if con in lien:
            return True
    cac_tu = [x for x in MAU_TACH_TU.split(t) if x]
    if t in TU_NHAY_CAM:
        return True
    if any(tu in TU_NHAY_CAM for tu in cac_tu):
        return True
    # Từ MƠ HỒ ("khoa", "phien"): mặc định là CHE. Một từ BỔ TRỢ xác nhận nghĩa
    # nhạy cảm; một từ VÔ HẠI gỡ nó. Bổ trợ thắng vô hại. Xem chú thích ở
    # TU_MO_HO về vì sao chiều mặc định phải là che.
    if any(tu in TU_MO_HO for tu in cac_tu):
        if any(tu in TU_BO_TRO for tu in cac_tu):
            return True
        return not any(tu in TU_VO_HAI for tu in cac_tu)
    return False


def _lam_mo_email(gt: str) -> str:
    ten, _, mien = gt.partition("@")
    dau = ten[:1] if ten else ""
    return "%s%s@%s" % (dau, "*" * max(len(ten) - 1, 1), mien)


def _lam_mo_dien_thoai(gt: str) -> str:
    so = [c for c in gt if c.isdigit()]
    duoi = "".join(so[-3:])
    return "*" * max(len(so) - 3, 0) + duoi


def che_chuoi_theo_hinh_dang(gt: str) -> Tuple[str, int]:
    """Che TỪNG ĐOẠN giống bí mật nằm bên trong một chuỗi. Trả (chuỗi, số đoạn).

    Dùng khi bí mật NHÚNG giữa một câu — câu báo lỗi của nền tảng đích, lệnh
    curl người dùng dán vào, vết ngăn xếp. Che đúng đoạn khớp chứ không che cả
    câu: che cả câu thì nhật ký mất phần giải thích và rơi vào lỗi "làm mờ quá
    tay" mà đầu tệp đã cảnh báo.

    Công khai (không có gạch dưới) vì `nhan/dinh_tuyen.py` cần đúng phép này
    cho thông điệp lỗi và vết ngăn xếp của trình điều khiển.
    """
    if not isinstance(gt, str) or not gt:
        return gt, 0
    dem = [0]

    def _thay(m, nhan=""):
        dem[0] += 1
        return _lam_mo_chuoi(m.group(0), nhan)

    ra = gt
    for nhan, mau in MAU_GIA_TRI_NHAY_CAM:
        ra = mau.sub(lambda m, n=nhan: _thay(m, n), ra)
    return ra, dem[0]


class _DemLamMo:
    """Đếm số trường đã làm mờ, để bản ghi nói được là nó ĐÃ làm mờ thật.

    Không có con số này thì một hàm làm mờ hỏng (trả nguyên đầu vào) nhìn y hệt
    một tham số vốn không có gì nhạy cảm. Đây đúng họ lỗi "hỏng mà không báo".
    """

    def __init__(self) -> None:
        self.so = 0


def _lam_mo_gia_tri(gt: Any, ten_truong: str, dem: _DemLamMo, do_sau: int) -> Any:
    if do_sau > DO_SAU_TOI_DA:
        return "%s:qua-sau:%d\u00bb" % (DAU_LAM_MO, do_sau)

    if isinstance(gt, (bytes, bytearray, memoryview)):
        # Không bao giờ ghi byte thô: không JSON hoá được, và nội dung nhị phân
        # thường chính là khoá hoặc tệp người dùng tải lên.
        dem.so += 1
        return "%s:nhi-phan:%s\u00bb" % (DAU_LAM_MO, _bac_do_dai(len(bytes(gt))))

    if isinstance(gt, dict):
        ra: Dict[str, Any] = {}
        for i, (k, v) in enumerate(gt.items()):
            if i >= SO_TRUONG_TOI_DA:
                ra["\u2026"] = "còn %d trường nữa, đã cắt" % (len(gt) - SO_TRUONG_TOI_DA)
                break
            ra[str(k)] = _lam_mo_gia_tri(v, str(k), dem, do_sau + 1)
        return ra

    if isinstance(gt, (list, tuple, set, frozenset)):
        ds = list(gt)
        ra_ds: List[Any] = []
        for v in ds[:SO_PHAN_TU_TOI_DA]:
            ra_ds.append(_lam_mo_gia_tri(v, ten_truong, dem, do_sau + 1))
        if len(ds) > SO_PHAN_TU_TOI_DA:
            ra_ds.append("… còn %d phần tử nữa, đã cắt" % (len(ds) - SO_PHAN_TU_TOI_DA))
        return ra_ds

    if isinstance(gt, str):
        if _ten_truong_nhay_cam(ten_truong):
            dem.so += 1
            return _lam_mo_chuoi(gt, "truong-nhay-cam")
        for nhan, mau in MAU_GIA_TRI_NHAY_CAM:
            khop = mau.search(gt)
            if khop:
                if khop.group(0) == gt.strip():
                    # Bí mật là TOÀN BỘ giá trị: thay cả trường bằng một nhãn,
                    # kèm bậc độ dài — không có gì khác để giữ lại.
                    dem.so += 1
                    return _lam_mo_chuoi(gt, nhan)
                # Bí mật NHÚNG giữa một câu: che đúng đoạn ấy, giữ phần còn lại
                # để dòng nhật ký vẫn giải thích được chuyện gì đã xảy ra.
                ra_che, so_che = che_chuoi_theo_hinh_dang(gt)
                dem.so += so_che
                if len(ra_che) > DO_DAI_CHUOI_TOI_DA:
                    ra_che = ra_che[:DO_DAI_CHUOI_TOI_DA] + "… (cắt %d ký tự)" % (
                        len(ra_che) - DO_DAI_CHUOI_TOI_DA
                    )
                return ra_che
        if MAU_EMAIL.match(gt):
            dem.so += 1
            return _lam_mo_email(gt)
        if MAU_DIEN_THOAI.match(gt) and sum(c.isdigit() for c in gt) >= 8:
            dem.so += 1
            return _lam_mo_dien_thoai(gt)
        if len(gt) > DO_DAI_CHUOI_TOI_DA:
            return gt[:DO_DAI_CHUOI_TOI_DA] + "… (cắt %d ký tự)" % (
                len(gt) - DO_DAI_CHUOI_TOI_DA
            )
        return gt

    if isinstance(gt, bool) or gt is None:
        return gt

    if isinstance(gt, (int, float)):
        if _ten_truong_nhay_cam(ten_truong):
            # Một mã OTP hay mã PIN rất hay đi vào dưới dạng SỐ.
            dem.so += 1
            return "%s:so-nhay-cam\u00bb" % DAU_LAM_MO
        return gt

    # Kiểu lạ: CHỈ ghi tên kiểu. Gọi str() lên một đối tượng bất kỳ là cách một
    # bản ghi khách hàng đầy đủ lọt vào nhật ký qua __repr__ của nó.
    return "%s:kieu-la:%s\u00bb" % (DAU_LAM_MO, type(gt).__name__)


def lam_mo(tham_so: Any) -> Tuple[Any, int]:
    """Làm mờ tham số trước khi ghi. Trả (bản đã làm mờ, số trường đã làm mờ)."""
    dem = _DemLamMo()
    ra = _lam_mo_gia_tri(tham_so, "", dem, 0)
    return ra, dem.so


def ma_theo_doi_moi() -> str:
    """Mã nối một lời gọi với dòng nhật ký của nó và với thứ trả về cho người gọi.

    Người dùng báo lỗi thì đọc được mã này trong câu trả lời; người vận hành
    `grep` đúng mã ấy là ra dòng nhật ký. Không có nó thì việc ghép hai đầu phải
    đoán theo thời điểm, và đoán sai khi hệ chạy nhiều lời gọi song song.
    """
    return uuid.uuid4().hex[:16]


def _co_gang_do_kich_thuoc(gt: Any) -> Dict[str, Any]:
    """Kiểu + kích thước của kết quả, KHÔNG có nội dung."""
    ra: Dict[str, Any] = {"kieu": type(gt).__name__}
    try:
        if isinstance(gt, (list, tuple, set, frozenset, dict, str, bytes)):
            ra["so_phan_tu"] = len(gt)
    except Exception:
        pass
    return ra


class NhatKy:
    """Ghi một dòng JSON cho mỗi lời gọi."""

    def __init__(
        self,
        dong_ra=None,
        dong_ho: Callable[[], float] = time.time,
        ham_lam_mo: Callable[[Any], Tuple[Any, int]] = lam_mo,
        ghi_ket_qua: bool = False,
    ) -> None:
        # Mặc định ra stderr, KHÔNG phải stdout: khi nhân chạy như một máy chủ
        # MCP thì stdout là kênh giao thức JSON-RPC. In một dòng nhật ký vào đó
        # là bẻ gãy giao thức, và triệu chứng sẽ là "máy khách không hiểu gì" —
        # rất xa nguyên nhân.
        self._dong_ra = dong_ra if dong_ra is not None else sys.stderr
        self._dong_ho = dong_ho
        self._ham_lam_mo = ham_lam_mo
        self.ghi_ket_qua = bool(ghi_ket_qua)

    def _thoi_diem(self) -> str:
        return datetime.fromtimestamp(self._dong_ho(), tz=timezone.utc).isoformat()

    def ghi(
        self,
        danh_tinh,
        cong_cu: str,
        tham_so: Any,
        ket_qua: str,
        ly_do: str = "",
        mili_giay: float = 0.0,
        ma_theo_doi: str = "",
        gia_tri_tra_ve: Any = None,
        them: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dựng bản ghi, làm mờ, ghi MỘT dòng. Trả lại bản ghi (để kiểm thử)."""
        if ket_qua not in (THANH_CONG, TU_CHOI, LOI):
            raise LoiNhatKy("kết quả %r không hợp lệ" % (ket_qua,))

        tham_so_mo, so_lam_mo = self._ham_lam_mo(tham_so)

        ban_ghi: Dict[str, Any] = {
            "thoi_diem": self._thoi_diem(),
            "ma_theo_doi": ma_theo_doi or ma_theo_doi_moi(),
            "danh_tinh": danh_tinh.tom_tat() if danh_tinh is not None else None,
            "cong_cu": cong_cu,
            "tham_so": tham_so_mo,
            "so_truong_da_lam_mo": so_lam_mo,
            "ket_qua": ket_qua,
            "ly_do": ly_do,
            "mili_giay": round(float(mili_giay), 3),
        }
        if them:
            ban_ghi["them"] = them
        if gia_tri_tra_ve is not None:
            if self.ghi_ket_qua:
                mo, _ = self._ham_lam_mo(gia_tri_tra_ve)
                ban_ghi["ket_qua_noi_dung"] = mo
            else:
                ban_ghi["ket_qua_do"] = _co_gang_do_kich_thuoc(gia_tri_tra_ve)

        try:
            dong = json.dumps(ban_ghi, ensure_ascii=False, sort_keys=True, default=str)
        except Exception as loi:
            raise LoiNhatKy("không dựng được JSON cho bản ghi: %s" % (loi,))

        if "\n" in dong:
            # json.dumps đã thoát mọi xuống dòng bên trong chuỗi; nếu vẫn còn
            # thì có gì đó rất sai, và một dòng bị tách đôi làm hỏng cả tệp
            # JSON Lines từ đó trở đi.
            raise LoiNhatKy("bản ghi chứa ký tự xuống dòng chưa thoát")

        try:
            self._dong_ra.write(dong + "\n")
            # flush ngay: nhật ký chưa xuống đĩa lúc tiến trình bị giết là nhật
            # ký không tồn tại, và tiến trình hay bị giết đúng lúc đang có sự cố.
            if hasattr(self._dong_ra, "flush"):
                self._dong_ra.flush()
        except Exception as loi:
            raise LoiNhatKy("không ghi được nhật ký: %s: %s" % (type(loi).__name__, loi))

        return ban_ghi
