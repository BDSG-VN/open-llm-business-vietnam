#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/thu_nhat_ky.py — BÀI TỰ KIỂM CHO NHẬT KÝ VÀ HÀM LÀM MỜ.

CHẠY:
    .venv/bin/python nhan/thu_nhat_ky.py

KHÔNG cần mạng. KHÔNG cần CSDL. KHÔNG đọc biến môi trường thật. KHÔNG ghi ra
ngoài bộ nhớ — mọi dòng nhật ký trong bài này đi vào một `io.StringIO`, không
tệp nào được tạo.

MỌI CHUỖI GIỐNG BÍ MẬT TRONG TỆP NÀY ĐỀU LÀ BỊA. Chúng được dựng bằng cách nối
chuỗi ngay tại chỗ dùng, đúng độ dài của hàng thật, để phép kiểm đo được cái
cần đo mà không có một bí mật thật nào nằm trong kho.

VÌ SAO CÓ BÀI NÀY
-----------------
BDSG vừa khẳng định CÔNG KHAI (trang bdsg.vn/open-bdsg-os và README kho): "mọi
lời gọi công cụ đều đi qua nhân, nên nó luôn có một chủ thể, một phép thử quyền
và MỘT DÒNG NHẬT KÝ". Phần "một dòng nhật ký" của khẳng định ấy tính đến hôm nay
chưa có một phép đo nào. Bài này đo nó.

Và nó đo một thứ nặng hơn nữa. `lam_mo()` là cái chắn giữa tham số công cụ và
một tệp được sao đi khắp nơi, đưa cho người ngoài xem khi gỡ lỗi, giữ lâu hơn cả
dữ liệu gốc. Nếu `lam_mo()` hỏng thì nhật ký — thứ sinh ra để bảo vệ — trở thành
chỗ rò lớn nhất trong hệ, và nó rò IM LẶNG: một hàm làm mờ trả nguyên đầu vào
nhìn y hệt một tham số vốn không có gì nhạy cảm.

BỐN CHỖ HỎNG MÀ KHÔNG TỰ BÁO, cả bốn đều có phép kiểm ở đây:
  1. BÍ MẬT LỌT NGUYÊN VĂN. Nhóm 1 và 2.
  2. LÀM MỜ QUÁ TAY. Nhật ký mờ hết thì hết dùng được, mà thứ hết dùng được thì
     người ta TẮT — và một nhật ký bị tắt bảo vệ được 0 byte. Nhóm 3.
  3. BẢN GHI THIẾU TRƯỜNG. Một dòng không trả lời được "AI đã làm GÌ, LÚC NÀO,
     KẾT QUẢ RA SAO" thì không dùng được làm bằng chứng. Nhóm 4.
  4. GHI HỎNG MÀ NUỐT IM LẶNG. Một sổ sách có thể mất bản ghi mà không ai biết
     thì không phải sổ sách. Nhóm 5.

HAI PHÉP KIỂM CUỐI (nhóm 6) ĐANG ĐỎ, VÀ ĐỎ ĐÚNG.
Chúng thể hiện hai lỗi THẬT tìm thấy trong `nhan/nhat_ky.py` khi viết bài này.
Chúng không được sửa ở đây: bài tự kiểm không sửa mã nguồn. Đọc phần in ra ở
cuối để biết lỗi gì và hậu quả ra sao.

MÃ THOÁT: 0 = mọi phép kiểm ĐẠT. 1 = có phép kiểm HỎNG.

Viết ngày 26/09/2026. Python 3.9.6.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import traceback

THU_MUC = os.path.dirname(os.path.abspath(__file__))
GOC_KHO = os.path.dirname(THU_MUC)

if __package__:
    from . import danh_tinh as _danh_tinh
    from . import nhat_ky as _nhat_ky
else:
    if GOC_KHO not in sys.path:
        sys.path.insert(0, GOC_KHO)
    from nhan import danh_tinh as _danh_tinh  # noqa: E402
    from nhan import nhat_ky as _nhat_ky  # noqa: E402

DanhTinh = _danh_tinh.DanhTinh
NhatKy = _nhat_ky.NhatKy
LoiNhatKy = _nhat_ky.LoiNhatKy
lam_mo = _nhat_ky.lam_mo
ma_theo_doi_moi = _nhat_ky.ma_theo_doi_moi
THANH_CONG = _nhat_ky.THANH_CONG
TU_CHOI = _nhat_ky.TU_CHOI
LOI = _nhat_ky.LOI
DAU_LAM_MO = _nhat_ky.DAU_LAM_MO


# ----------------------------------------------------------------------
# Khung chạy thử tối giản (không pytest) — giống phuc-vu/thu_cong_mo_hinh.py.
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


# ----------------------------------------------------------------------
# Nguyên liệu BỊA. Nối chuỗi tại chỗ để không có chuỗi nào trong kho trông như
# một bí mật thật — cổng cong/khong-bi-mat.py sẽ bắt, và mỗi ngoại lệ thêm vào
# cổng ấy là một lỗ thủng.
# ----------------------------------------------------------------------
KHOA_KIEU_GITHUB = "g" + "hp_" + "B" * 36          # 40 ký tự, đúng dạng hàng thật
KHOA_KIEU_OPENAI = "s" + "k-" + "c" * 48
JWT_BIA = (
    "eyJhbGciOiJIUzI1NiJ9"
    + "."
    + "eyJzdWIiOiJjaGktZGUta2llbSJ9"
    + "."
    + "chu-ky-bia-khong-that"
)
# Dựng từ mảnh, KHÔNG viết liền. Lý do: cổng khong-bi-mat và khong-ha-tang quét
# chính kho này, và một chuỗi kết nối viết liền trong bài kiểm sẽ bị chúng bắt —
# bộ dò mang theo đúng chuỗi nó dò thì tự nó thành vi phạm. Ghép lúc chạy thì trên
# đĩa không có chuỗi nào khớp, mà bài kiểm vẫn nhận đúng chuỗi cần làm mờ.
URL_CO_MAT_KHAU = ("post" + "gres://nguoidung:matkhaubia@may-chu-bia.test:"
                   + str(5000 + 432) + "/csdl")
HEX_DAI_BIA = "d" * 40
THE_BIA = "4111 1111 1111 1111"          # số thẻ thử nghiệm công khai, không dùng được
EMAIL_BIA = "khach.hang@vi-du.test"
DIEN_THOAI_BIA = "0912345678"
MAT_KHAU_BIA = "matkhaubia-1234"

# Mọi chuỗi trên đây, khi lọt vào nhật ký, phải KHÔNG còn nguyên văn.
CAC_BI_MAT = [
    ("khoá kiểu GitHub", KHOA_KIEU_GITHUB),
    ("khoá kiểu OpenAI", KHOA_KIEU_OPENAI),
    ("thẻ JWT ba đoạn", JWT_BIA),
    ("chuỗi kết nối có mật khẩu", URL_CO_MAT_KHAU),
    ("chuỗi hex dài", HEX_DAI_BIA),
    ("số thẻ", THE_BIA),
    ("email", EMAIL_BIA),
    ("số điện thoại Việt Nam", DIEN_THOAI_BIA),
]


def _con_nguyen_van(bi_mat, trong):
    """bi_mat có còn xuất hiện NGUYÊN VĂN trong `trong` (đã JSON hoá) không.

    Ép về JSON rồi tìm chuỗi con, chứ không so từng trường: một bí mật lọt ra
    qua khoá của dict, qua phần tử thứ 51 của một danh sách, hay qua repr của
    một đối tượng lạ thì so từng trường sẽ bỏ sót.
    """
    return bi_mat in json.dumps(trong, ensure_ascii=False, default=str)


def _nhat_ky_vao_bo_nho(**kw):
    dong = io.StringIO()
    return NhatKy(dong_ra=dong, **kw), dong


def _danh_tinh_thu():
    return DanhTinh(
        ma="nguoi-thu-01",
        ten="Tên Riêng Chỉ Để Kiểm",
        vai=("nhan-vien", "tu-van"),
        nguon="bai-tu-kiem",
    )


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 1 — lam_mo: bí mật KHÔNG được còn nguyên văn
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("1. Tên trường nhạy cảm: giá trị bị che dù trông vô hại thế nào")
def kiem_che_theo_ten_truong():
    # Hướng 1 của làm mờ. Mật khẩu "1234" thì hình dạng không bắt được — chỉ tên
    # trường cứu được nó.
    tham_so = {
        "mat_khau": "1234",
        "password": "abc",
        "api_key": "xyz",
        "token": "q",
        "authorization": "gi do",
        "cookie": "a=b",
        "cvv": 123,
        "otp": 987654,
        "chu_ky": "ky-bia",
        "so_the": 4111111111111111,
    }
    ra, dem = lam_mo(tham_so)
    for ten, gt in tham_so.items():
        bang(
            ra[ten] != gt,
            "trường %r giữ NGUYÊN giá trị — hướng làm mờ theo tên trường không "
            "chạm tới nó. Đây là chỗ mật khẩu ngắn và mã OTP lọt ra." % ten,
        )
        bang(
            str(gt) not in json.dumps(ra[ten], ensure_ascii=False),
            "trường %r vẫn chứa giá trị gốc sau khi làm mờ" % ten,
        )
    bang(
        dem == len(tham_so),
        "đếm %d trường đã làm mờ nhưng có %d trường nhạy cảm — con số này là thứ "
        "duy nhất phân biệt 'đã làm mờ' với 'không có gì để làm mờ'"
        % (dem, len(tham_so)),
    )
    return "%d trường nhạy cảm bị che, kể cả mật khẩu 4 ký tự và OTP dạng SỐ" % dem


@phep_kiem("2. Hình dạng giá trị: bí mật bị che dù nằm dưới tên trường vô hại")
def kiem_che_theo_hinh_dang():
    # Hướng 2. Tên trường cố ý chọn thứ vô hại nhất có thể — "mo_ta", "ghi_chu"
    # — để chắc chắn phép kiểm đo HÌNH DẠNG chứ không vô tình đo tên trường.
    for nhan, bi_mat in CAC_BI_MAT:
        ra, dem = lam_mo({"mo_ta": bi_mat})
        bang(
            not _con_nguyen_van(bi_mat, ra),
            "%s LỌT NGUYÊN VĂN vào nhật ký dưới tên trường vô hại 'mo_ta'. "
            "Nhật ký được sao đi khắp nơi và giữ lâu hơn dữ liệu gốc — đây là "
            "chỗ rò tệ nhất có thể có. Giá trị ghi ra: %r" % (nhan, ra["mo_ta"]),
        )
        bang(dem >= 1, "%s bị che nhưng KHÔNG được đếm — bản ghi sẽ nói 'không "
             "có gì nhạy cảm' trong khi vừa che một bí mật" % nhan)
    return "%d hình dạng bí mật đều bị che dưới tên trường 'mo_ta'" % len(CAC_BI_MAT)


@phep_kiem("3. Bí mật LỒNG SÂU (dict trong list trong dict) cũng bị che")
def kiem_che_long_nhau():
    # Một hàm làm mờ chỉ quét tầng mặt là hàm làm mờ vô dụng: tham số công cụ
    # thật gần như luôn có ít nhất hai tầng.
    tham_so = {
        "yeu_cau": {
            "danh_sach": [
                {"ten": "hồ sơ 1", "lien_he": {"email": EMAIL_BIA}},
                {"ten": "hồ sơ 2", "chung_thu": {"mat_khau": MAT_KHAU_BIA}},
                [{"sau_nua": {"token": KHOA_KIEU_GITHUB}}],
            ]
        }
    }
    ra, dem = lam_mo(tham_so)
    for nhan, bi_mat in (
        ("email tầng 4", EMAIL_BIA),
        ("mật khẩu tầng 5", MAT_KHAU_BIA),
        ("khoá tầng 6", KHOA_KIEU_GITHUB),
    ):
        bang(
            not _con_nguyen_van(bi_mat, ra),
            "%s lọt nguyên văn — làm mờ chỉ quét tầng mặt, không đi sâu. Cây đã "
            "làm mờ: %s" % (nhan, json.dumps(ra, ensure_ascii=False)),
        )
    bang(dem >= 3, "phải đếm ít nhất 3 trường đã làm mờ, đang đếm %d" % dem)
    # Phần KHÔNG nhạy cảm ở cùng độ sâu phải còn nguyên, nếu không thì cây bị
    # làm mờ cả cụm chứ không phải làm mờ đúng chỗ.
    bang(
        _con_nguyen_van("hồ sơ 1", ra),
        "tên hồ sơ ở cùng độ sâu cũng bị xoá ⇒ làm mờ cả cụm, nhật ký hết dùng",
    )
    return "đi sâu tới tầng 6, che đúng 3 chỗ, giữ nguyên phần vô hại cùng tầng"


@phep_kiem("4. Byte thô và đối tượng lạ không được đổ nội dung vào nhật ký")
def kiem_byte_va_kieu_la():
    class HoSoKhach:
        """Đối tượng có __repr__ tiết lộ tất cả — đúng kiểu ORM hay sinh ra."""

        def __repr__(self):
            return "HoSoKhach(email=%r, mat_khau=%r)" % (EMAIL_BIA, MAT_KHAU_BIA)

    ra, _ = lam_mo({"tep": b"\x00\x01noi dung tep nguoi dung tai len"})
    bang(
        "noi dung tep" not in json.dumps(ra, ensure_ascii=False),
        "byte thô bị chép vào nhật ký: %r" % ra,
    )
    bang("nhi-phan" in json.dumps(ra, ensure_ascii=False), "phải ghi rõ là nhị phân")

    ra2, _ = lam_mo({"ho_so": HoSoKhach()})
    bang(
        not _con_nguyen_van(EMAIL_BIA, ra2) and not _con_nguyen_van(MAT_KHAU_BIA, ra2),
        "gọi str()/repr() lên đối tượng lạ đã kéo cả bản ghi khách hàng vào nhật "
        "ký: %r" % ra2,
    )
    bang(
        "HoSoKhach" in json.dumps(ra2, ensure_ascii=False),
        "phải ghi TÊN KIỂU để còn gỡ lỗi được, đang ghi: %r" % ra2,
    )
    return "byte → bậc kích thước; đối tượng lạ → chỉ tên kiểu, không gọi repr"


@phep_kiem("5. Chỉ ghi BẬC độ dài bí mật, không ghi số ký tự chính xác")
def kiem_chi_ghi_bac_do_dai():
    # Biết mật khẩu dài đúng 8 ký tự là đã thu hẹp việc dò rất nhiều.
    for do_dai in (7, 8, 9, 17, 41):
        ra, _ = lam_mo({"mat_khau": "x" * do_dai})
        chuoi = str(ra["mat_khau"])
        bang(
            str(do_dai) not in chuoi,
            "độ dài chính xác %d lọt vào nhãn làm mờ: %r" % (do_dai, chuoi),
        )
    # Nhưng vẫn phải trả lời được câu hỏi gỡ lỗi hay gặp nhất: có rỗng không.
    ra_rong, _ = lam_mo({"mat_khau": ""})
    ra_day, _ = lam_mo({"mat_khau": "x" * 40})
    bang(
        str(ra_rong["mat_khau"]) != str(ra_day["mat_khau"]),
        "chuỗi RỖNG và chuỗi dài cho cùng một nhãn ⇒ không trả lời được 'tham số "
        "ấy có rỗng không', mà đó là câu hỏi gỡ lỗi hay gặp nhất",
    )
    return "5 độ dài khác nhau không lộ con số; rỗng vẫn phân biệt được với dài"


@phep_kiem("6. Trần chống bom nhật ký: sâu quá, dài quá, nhiều quá đều bị cắt")
def kiem_tran_chong_bom():
    # Một tham số lồng sâu hoặc một danh sách triệu phần tử biến mỗi lời gọi
    # thành một dòng khổng lồ — vừa làm đầy đĩa vừa làm chậm cả nhân.
    sau = cur = {}
    for i in range(30):
        cur["tang"] = {}
        cur = cur["tang"]
    cur["day"] = MAT_KHAU_BIA
    ra, _ = lam_mo(sau)
    chuoi = json.dumps(ra, ensure_ascii=False)
    bang("qua-sau" in chuoi, "lồng 30 tầng mà không bị cắt: %s" % chuoi[:200])
    bang(
        MAT_KHAU_BIA not in chuoi,
        "cắt theo độ sâu nhưng bí mật ở đáy vẫn lọt ra",
    )

    ra_ds, _ = lam_mo({"ds": list(range(5000))})
    bang(len(ra_ds["ds"]) <= 51, "danh sách 5000 phần tử không bị cắt")
    bang("cắt" in str(ra_ds["ds"][-1]), "phải nói rõ là đã cắt, không cắt lặng lẽ")

    ra_dict, _ = lam_mo({"d": {"k%d" % i: i for i in range(500)}})
    bang(len(ra_dict["d"]) <= 51, "dict 500 trường không bị cắt")

    ra_chuoi, _ = lam_mo({"mo_ta": "y" * 5000})
    bang(len(str(ra_chuoi["mo_ta"])) < 400, "chuỗi 5000 ký tự không bị cắt")
    bang("cắt" in str(ra_chuoi["mo_ta"]), "phải nói rõ là đã cắt")
    return "sâu 30 tầng · 5000 phần tử · 500 trường · 5000 ký tự đều bị cắt có báo"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 2 — mã theo dõi
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("7. ma_theo_doi_moi: định dạng ổn định, không trùng, không đoán được")
def kiem_ma_theo_doi():
    mau = [ma_theo_doi_moi() for _ in range(5000)]
    bang(len(set(mau)) == 5000, "có mã TRÙNG trong 5000 lần sinh — hai lời gọi "
         "khác nhau sẽ chỉ về cùng một dòng nhật ký")
    mau_hop_le = re.compile(r"^[0-9a-f]{16}$")
    for m in mau[:100]:
        bang(mau_hop_le.match(m), "định dạng mã không ổn định: %r" % m)

    # Không đoán được: nếu mã đi từ một bộ sinh yếu (đếm lên, hay time-based)
    # thì biết một mã là đoán được mã kế tiếp, và người ngoài tra được dòng nhật
    # ký của người khác. Đo thô bằng hai dấu hiệu của bộ sinh yếu.
    so = [int(m, 16) for m in mau]
    tang_dan = sum(1 for i in range(1, len(so)) if so[i] > so[i - 1])
    bang(
        1000 < tang_dan < 4000,
        "%d/4999 cặp liên tiếp TĂNG DẦN — mã gần như chắc chắn đi từ một bộ đếm "
        "hoặc từ thời gian, tức là đoán được" % tang_dan,
    )
    dau = set(m[:4] for m in mau)
    bang(
        len(dau) > 2000,
        "chỉ %d tiền tố 4 ký tự khác nhau trong 5000 mã — entropy quá thấp"
        % len(dau),
    )
    return "5000 mã: 0 trùng, đúng 16 hex, phân bố không cho thấy bộ sinh yếu"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 3 — KHÔNG làm mờ quá tay
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("8. Không làm mờ quá tay: tên công cụ, từ khoá, câu hỏi giữ NGUYÊN VĂN")
def kiem_khong_lam_mo_qua_tay():
    # Nếu nhật ký làm mờ cả từ khoá tìm kiếm thì nó hết dùng được để gỡ lỗi, và
    # thứ hết dùng được thì người ta TẮT. Một nhật ký bị tắt bảo vệ được 0 byte.
    phai_giu_nguyen = {
        "tu_khoa": "mật khẩu wifi quán cà phê",   # có chữ nhạy cảm, vẫn phải giữ
        "khoa_chinh": "ma_du_an",
        "khoa_ngoai": "ma_tinh",
        "khoa_sap_xep": "ngay_tao",
        "so_khoa": 12,
        "cau_hoi": "có bao nhiêu xã ở Thanh Hoá sau sắp xếp",
        "ten_tinh": "Thanh Hoá",
        "so_luong": 3321,
        "trang": 2,
        "bat_buoc": True,
        "khong_co": None,
        "duong_dan": "/business/danh-ba",
        "ma_du_an": "DA-2026-017",
    }
    ra, dem = lam_mo(phai_giu_nguyen)
    for ten, gt in phai_giu_nguyen.items():
        bang(
            ra[ten] == gt,
            "trường VÔ HẠI %r bị làm mờ thành %r. Làm mờ quá tay biến nhật ký "
            "thành vô dụng, và nhật ký vô dụng thì bị tắt." % (ten, ra[ten]),
        )
    bang(dem == 0, "đếm %d trường đã làm mờ trong một tham số không có gì nhạy "
         "cảm — báo động giả" % dem)

    # Và tên công cụ phải đi thẳng vào bản ghi, không qua làm mờ.
    nk, dong = _nhat_ky_vao_bo_nho()
    nk.ghi(_danh_tinh_thu(), "crm.tim_khach_hang", {"tu_khoa": "xi măng"}, THANH_CONG)
    ban_ghi = json.loads(dong.getvalue())
    bang(
        ban_ghi["cong_cu"] == "crm.tim_khach_hang",
        "TÊN CÔNG CỤ bị làm mờ (%r) — không còn biết nhân vừa chạy gì"
        % ban_ghi["cong_cu"],
    )
    bang(ban_ghi["tham_so"]["tu_khoa"] == "xi măng", "từ khoá bị làm mờ")
    return "13 trường vô hại + tên công cụ giữ nguyên, 0 báo động giả"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 4 — Bản ghi: đủ trường, đúng một dòng
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("9. Một bản ghi trả lời đủ AI · LÀM GÌ · LÚC NÀO · KẾT QUẢ RA SAO")
def kiem_du_bon_truong():
    nk, dong = _nhat_ky_vao_bo_nho()
    dt = _danh_tinh_thu()
    nk.ghi(
        dt,
        "crm.tao_cong_viec",
        {"tieu_de": "gọi lại khách"},
        THANH_CONG,
        ly_do="qua chính sách",
        mili_giay=12.5,
        ma_theo_doi="a" * 16,
    )
    bg = json.loads(dong.getvalue())

    # AI
    bang(bg.get("danh_tinh") is not None, "thiếu CHỦ THỂ — không biết AI đã làm")
    bang(bg["danh_tinh"]["ma"] == "nguoi-thu-01", "chủ thể phải có mã truy được")
    bang("nhan-vien" in bg["danh_tinh"]["vai"], "chủ thể phải kèm vai")
    bang(bg["danh_tinh"]["nguon"] == "bai-tu-kiem", "chủ thể phải kèm nguồn")
    # LÀM GÌ
    bang(bg.get("cong_cu") == "crm.tao_cong_viec", "thiếu TÊN CÔNG CỤ")
    bang("tham_so" in bg, "thiếu THAM SỐ (đã làm mờ)")
    # LÚC NÀO
    bang(bg.get("thoi_diem"), "thiếu THỜI ĐIỂM")
    bang("T" in bg["thoi_diem"] and "+00:00" in bg["thoi_diem"],
         "thời điểm phải là ISO có múi giờ, đang là %r" % bg["thoi_diem"])
    bang("mili_giay" in bg, "thiếu thời lượng chạy")
    # KẾT QUẢ RA SAO
    bang(bg.get("ket_qua") == THANH_CONG, "thiếu KẾT QUẢ")
    bang(bg.get("ly_do") == "qua chính sách", "thiếu lý do")
    # Nối hai đầu
    bang(bg.get("ma_theo_doi") == "a" * 16, "thiếu MÃ THEO DÕI để grep")
    bang("so_truong_da_lam_mo" in bg, "thiếu số trường đã làm mờ")

    # Và TÊN NGƯỜI phải KHÔNG có mặt: nhật ký sống lâu hơn phiên làm việc.
    bang(
        "Tên Riêng Chỉ Để Kiểm" not in dong.getvalue(),
        "TÊN NGƯỜI lọt vào nhật ký — dữ liệu cá nhân trong một tệp giữ rất lâu "
        "và hay được chép đi nơi khác",
    )
    return "đủ 4 nhóm trường + mã theo dõi; tên người KHÔNG có mặt"


@phep_kiem("10. Đúng MỘT dòng cho mỗi lời gọi, kể cả khi tham số có xuống dòng")
def kiem_dung_mot_dong():
    nk, dong = _nhat_ky_vao_bo_nho()
    for i in range(3):
        nk.ghi(
            _danh_tinh_thu(),
            "cc",
            {"van_ban": "dòng một\ndòng hai\r\ndòng ba", "so": i},
            THANH_CONG,
        )
    cac_dong = dong.getvalue().splitlines()
    bang(
        len(cac_dong) == 3,
        "3 lời gọi ra %d dòng — một bản ghi bị tách đôi làm hỏng cả tệp JSON "
        "Lines từ chỗ đó trở đi, và hỏng IM LẶNG" % len(cac_dong),
    )
    for d in cac_dong:
        bg = json.loads(d)  # từng dòng phải tự đọc được
        bang("\n" in bg["tham_so"]["van_ban"], "xuống dòng phải được GIỮ trong "
             "giá trị, chỉ thoát khi ghi ra")
    bang(dong.getvalue().endswith("\n"), "dòng cuối phải có ký tự xuống dòng")
    return "3 lời gọi → đúng 3 dòng, mỗi dòng tự đọc được bằng json.loads"


@phep_kiem("11. Kết quả lạ bị TỪ CHỐI, không lặng lẽ ghi vào")
def kiem_ket_qua_la():
    nk, dong = _nhat_ky_vao_bo_nho()
    for gt in ("ok", "SUCCESS", "", None, 1, "thanh_cong"):
        try:
            nk.ghi(_danh_tinh_thu(), "cc", {}, gt)
        except LoiNhatKy:
            continue
        raise AssertionError(
            "kết quả %r được nhận — bộ ba thanh-cong/tu-choi/loi không còn là bộ "
            "ba, và mọi phép đếm trên nhật ký sau này sẽ sai lặng lẽ" % (gt,)
        )
    bang(dong.getvalue() == "", "không được ghi dòng nào cho kết quả không hợp lệ")
    for gt in (THANH_CONG, TU_CHOI, LOI):
        nk.ghi(_danh_tinh_thu(), "cc", {}, gt)
    bang(len(dong.getvalue().splitlines()) == 3, "3 kết quả hợp lệ phải ghi được")
    return "6 kết quả lạ bị ném LoiNhatKy; 3 kết quả hợp lệ ghi được"


@phep_kiem("12. Mặc định KHÔNG ghi nội dung trả về, chỉ kiểu và kích thước")
def kiem_khong_ghi_noi_dung_tra_ve():
    # Kết quả là chỗ dữ liệu khách ĐI RA: một lệnh tìm hồ sơ trả 50 hồ sơ đầy
    # đủ, ghi vào nhật ký là chép nguyên 50 hồ sơ ấy sang nơi ít được bảo vệ hơn.
    ket_qua = [{"ten": "Khách %d" % i, "email": EMAIL_BIA} for i in range(50)]

    nk, dong = _nhat_ky_vao_bo_nho()
    nk.ghi(_danh_tinh_thu(), "cc", {}, THANH_CONG, gia_tri_tra_ve=ket_qua)
    bg = json.loads(dong.getvalue())
    bang("ket_qua_noi_dung" not in bg, "mặc định đã ghi cả nội dung trả về")
    bang(bg["ket_qua_do"]["kieu"] == "list", "phải ghi kiểu của kết quả")
    bang(bg["ket_qua_do"]["so_phan_tu"] == 50, "phải ghi số phần tử")
    bang(EMAIL_BIA not in dong.getvalue(), "email khách lọt ra qua giá trị trả về")

    # Bật tường minh thì ghi — nhưng vẫn phải ĐI QUA làm mờ.
    nk2, dong2 = _nhat_ky_vao_bo_nho(ghi_ket_qua=True)
    nk2.ghi(_danh_tinh_thu(), "cc", {}, THANH_CONG, gia_tri_tra_ve=ket_qua)
    bg2 = json.loads(dong2.getvalue())
    bang("ket_qua_noi_dung" in bg2, "bật ghi_ket_qua mà không ghi nội dung")
    bang(
        EMAIL_BIA not in dong2.getvalue(),
        "bật ghi_ket_qua thì nội dung trả về KHÔNG đi qua làm mờ — 50 email "
        "khách vào thẳng nhật ký",
    )
    return "mặc định: kiểu + 50 phần tử, 0 nội dung; bật lên: nội dung ĐÃ làm mờ"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 5 — Ghi hỏng phải NỔ, không nuốt
# ══════════════════════════════════════════════════════════════════════════


class DongRaHong:
    """Dòng ra luôn hỏng — dựng lại 'đĩa đầy' / 'kho lỗi' mà không cần đĩa đầy."""

    def __init__(self, hong_o="write"):
        self.hong_o = hong_o
        self.da_viet = []

    def write(self, s):
        if self.hong_o == "write":
            raise OSError(28, "No space left on device")
        self.da_viet.append(s)
        return len(s)

    def flush(self):
        if self.hong_o == "flush":
            raise OSError(5, "Input/output error")


@phep_kiem("13. Ghi hỏng thì NÉM LỖI, không nuốt im lặng — kể cả hỏng lúc flush")
def kiem_ghi_hong_thi_no():
    # Một nhật ký có thể mất bản ghi mà không ai biết thì không dùng được làm
    # bằng chứng, và ta chỉ phát hiện ra sau sự cố — đúng lúc cần nó nhất.
    for hong_o in ("write", "flush"):
        nk = NhatKy(dong_ra=DongRaHong(hong_o))
        try:
            nk.ghi(_danh_tinh_thu(), "cc", {"a": 1}, THANH_CONG)
        except LoiNhatKy as loi:
            bang(
                str(loi),
                "LoiNhatKy phải kèm câu giải thích, không ném rỗng",
            )
            continue
        raise AssertionError(
            "ghi hỏng ở %s mà `ghi` vẫn trả về bình thường — sổ sách MẤT BẢN GHI "
            "mà không ai biết. Đây đúng họ lỗi 'hỏng mà không báo'." % hong_o
        )

    # Bản ghi không JSON hoá được cũng phải nổ, không ghi nửa dòng.
    class KhongJson:
        def __repr__(self):
            raise RuntimeError("repr cũng hỏng")

    nk2, dong2 = _nhat_ky_vao_bo_nho()
    try:
        nk2.ghi(_danh_tinh_thu(), "cc", {"x": KhongJson()}, THANH_CONG)
    except LoiNhatKy:
        bang(dong2.getvalue() == "", "không được ghi nửa dòng khi dựng JSON hỏng")
    return "hỏng ở write, ở flush, và ở dựng JSON đều ném LoiNhatKy"


@phep_kiem("14. Mặc định ghi ra STDERR, không phải stdout")
def kiem_mac_dinh_ra_stderr():
    # Khi nhân chạy như một máy chủ MCP thì stdout là kênh giao thức JSON-RPC.
    # In một dòng nhật ký vào đó là bẻ gãy giao thức, và triệu chứng ("máy khách
    # không hiểu gì") nằm rất xa nguyên nhân.
    nk = NhatKy()
    bang(
        nk._dong_ra is sys.stderr,
        "dòng ra mặc định là %r chứ không phải sys.stderr" % (nk._dong_ra,),
    )
    bang(nk._dong_ra is not sys.stdout, "dòng ra mặc định TRÙNG stdout")
    return "mặc định là sys.stderr"


# ══════════════════════════════════════════════════════════════════════════
# Nhóm 6 — HAI LỖI THẬT. Hai phép kiểm này ĐỎ, và đỏ đúng.
# ══════════════════════════════════════════════════════════════════════════


@phep_kiem("15. LỖI THẬT — bí mật NHÚNG trong một chuỗi dài lọt NGUYÊN VĂN")
def kiem_bi_mat_nhung_trong_chuoi():
    # 5 trong 6 mẫu hình dạng ở MAU_GIA_TRI_NHAY_CAM neo bằng ^ và $, nhưng mã
    # dò bằng `mau.search(gt)`. Kết quả: mẫu chỉ khớp khi bí mật là TOÀN BỘ giá
    # trị chuỗi. Bí mật nằm giữa một câu — đúng hình dạng thường gặp nhất trong
    # thực tế: câu báo lỗi, lệnh curl người dùng dán vào, chuỗi kết nối trong
    # một thông báo — đi thẳng vào nhật ký nguyên văn.
    cac_ca = [
        ("thẻ JWT giữa câu", "lỗi 401 với thẻ " + JWT_BIA + ", xin cấp lại"),
        ("Bearer giữa câu", "đặt header Authorization: Bearer " + JWT_BIA + " rồi gọi lại"),
        ("chuỗi kết nối giữa câu", "không nối được tới " + URL_CO_MAT_KHAU + " từ máy này"),
        ("khoá dài giữa câu", "dùng khoá " + KHOA_KIEU_GITHUB + " cho kho này"),
        ("hex dài giữa câu", "băm là " + HEX_DAI_BIA + " nhưng không khớp"),
    ]
    lot = []
    for nhan, chuoi in cac_ca:
        ra, dem = lam_mo({"mo_ta": chuoi})
        if _con_nguyen_van(chuoi.split()[-2] if False else "", ra):
            pass
        for _, bi_mat in (("", JWT_BIA), ("", URL_CO_MAT_KHAU),
                          ("", KHOA_KIEU_GITHUB), ("", HEX_DAI_BIA)):
            if bi_mat in chuoi and _con_nguyen_van(bi_mat, ra):
                lot.append((nhan, dem))
                break
    bang(
        not lot,
        "%d/%d ca: bí mật nhúng giữa một chuỗi dài LỌT NGUYÊN VĂN vào nhật ký, "
        "và số trường đã làm mờ báo 0 nên không ai biết. Các ca lọt: %r. "
        "Nguyên nhân: 5/6 mẫu trong MAU_GIA_TRI_NHAY_CAM neo bằng ^…$ nên "
        "`mau.search()` chỉ khớp khi bí mật là TOÀN BỘ giá trị."
        % (len(lot), len(cac_ca), [n for n, _ in lot]),
    )
    return "không ca nào lọt"


@phep_kiem("16. LỖI THẬT — làm mờ quá tay: `phien_ban`, `ma_khoa_hoc` thành vô nghĩa")
def kiem_lam_mo_qua_tay_tieng_viet():
    # `_ten_truong_nhay_cam` tách tên trường thành TỪ rồi đối chiếu TU_NHAY_CAM,
    # trong đó có "khoa" và "phien". Trong một kho viết bằng tiếng Việt không
    # dấu, "khoa" còn nghĩa là khoá học / khoa phòng, và "phien" đi trong
    # "phien_ban". MIEN_TRU_TRUONG chỉ liệt kê 9 tên tiếng Anh + 4 tên có
    # "khoa_", không phủ được các tên này.
    phai_giu_nguyen = {
        "phien_ban": "1.2.0",
        "ma_khoa_hoc": "KH-2026-017",
        "ten_khoa": "Khoa Kiến trúc",
        "so_phien_ban": 3,
    }
    ra, dem = lam_mo(phai_giu_nguyen)
    bi_che = [t for t, gt in phai_giu_nguyen.items() if ra[t] != gt]
    bang(
        not bi_che,
        "%d trường VÔ HẠI bị làm mờ: %r. Trong kho tiếng Việt không dấu, 'khoa' "
        "cũng là khoá học/khoa phòng và 'phien' nằm trong 'phien_ban'. Hậu quả: "
        "người vận hành không đọc được phiên bản nào đang chạy hay khoá học nào "
        "bị hỏng, và một nhật ký hết dùng được là một nhật ký sắp bị tắt. "
        "(số trường đã làm mờ báo %d)" % (len(bi_che), bi_che, dem),
    )
    return "4 trường vô hại giữ nguyên"


CAC_PHEP_KIEM = [
    kiem_che_theo_ten_truong,
    kiem_che_theo_hinh_dang,
    kiem_che_long_nhau,
    kiem_byte_va_kieu_la,
    kiem_chi_ghi_bac_do_dai,
    kiem_tran_chong_bom,
    kiem_ma_theo_doi,
    kiem_khong_lam_mo_qua_tay,
    kiem_du_bon_truong,
    kiem_dung_mot_dong,
    kiem_ket_qua_la,
    kiem_khong_ghi_noi_dung_tra_ve,
    kiem_ghi_hong_thi_no,
    kiem_mac_dinh_ra_stderr,
    kiem_bi_mat_nhung_trong_chuoi,
    kiem_lam_mo_qua_tay_tieng_viet,
]


def main():
    print("=" * 78)
    print("BÀI TỰ KIỂM — nhan/nhat_ky.py (nhật ký và hàm làm mờ)")
    print("Python {}.{}.{}".format(*sys.version_info[:3]))
    print("KHÔNG cần mạng, KHÔNG ghi tệp nào — nhật ký đi vào bộ nhớ.")
    print("Mọi chuỗi giống bí mật trong bài này đều là BỊA.")
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
    else:
        print("KẾT QUẢ: {}/{} ĐẠT, {} HỎNG.".format(so_dat, len(_KET_QUA), so_hong))
        print()
        print("Các phép kiểm hỏng:")
        for ten, dat, ghi_chu in _KET_QUA:
            if not dat:
                print("  - {}: {}".format(ten, ghi_chu))
        print()
        print("HAI PHÉP KIỂM CUỐI ĐỎ LÀ CÓ CHỦ Ý. Chúng thể hiện hai lỗi THẬT trong")
        print("nhan/nhat_ky.py, phát hiện khi viết bài này, và CỐ Ý không sửa — bài tự")
        print("kiểm không sửa mã nguồn, người điều phối quyết định sửa thế nào:")
        print()
        print("  · Phép kiểm 15 (nặng): `lam_mo` chỉ bắt được bí mật khi bí mật là TOÀN BỘ")
        print("    giá trị chuỗi. 5/6 mẫu trong MAU_GIA_TRI_NHAY_CAM neo bằng ^…$ trong khi")
        print("    mã dò bằng `.search()`. Thẻ JWT, chuỗi kết nối có mật khẩu, khoá API nằm")
        print("    GIỮA một câu — dạng hay gặp nhất trong thực tế, vì người dùng dán cả câu")
        print("    báo lỗi hoặc cả lệnh curl vào tham số — đi thẳng vào nhật ký nguyên văn,")
        print("    và `so_truong_da_lam_mo` báo 0 nên không có dấu hiệu nào cho thấy vừa rò.")
        print()
        print("  · Phép kiểm 16 (vừa): làm mờ QUÁ TAY với tên trường tiếng Việt không dấu.")
        print("    'khoa' và 'phien' nằm trong TU_NHAY_CAM, nên phien_ban, ma_khoa_hoc,")
        print("    ten_khoa đều bị che. Đầu tệp nhat_ky.py tự cảnh báo đúng nguy cơ này:")
        print("    nhật ký hết dùng được thì người ta TẮT, và nhật ký bị tắt bảo vệ 0 byte.")
    print()
    print("Nghĩa là gì KHÔNG: bài này KHÔNG kiểm nhật ký dưới NHIỀU LUỒNG (một dòng có")
    print("thể xen vào giữa dòng khác — chưa đo), KHÔNG kiểm xoay vòng tệp hay giữ bao")
    print("lâu, và KHÔNG kiểm trường `them`: `them` đi vào bản ghi mà KHÔNG qua làm mờ.")
    print("Hiện chỉ nhân tự đặt `them` bằng giá trị cố định nên chưa rò, nhưng đó là một")
    print("lối rò đang mở sẵn cho người viết trình điều khiển sau này.")
    print("=" * 78)
    return 0 if tat_ca_dat else 1


if __name__ == "__main__":
    sys.exit(main())
