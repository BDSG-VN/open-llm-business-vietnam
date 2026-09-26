#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ho_so.py — HỒ SƠ HỌC VẤN của từng agent, sinh bằng phép tính, không lưu.

=============================================================================
Ý CHÍNH: HỒ SƠ ĐƯỢC TÍNH RA TỪ MÃ AGENT, NÊN KHÔNG TỐN BYTE NÀO
=============================================================================
Mỗi agent cần một học vấn riêng: ngành gì, bậc nào, tốt nghiệp năm nào. Nếu
LƯU, 100 triệu hồ sơ × ~200 byte = 20 GB — chấp nhận được nhưng vẫn là 20 GB
phải sao lưu, di trú, và giữ đồng bộ.

Nếu TÍNH RA từ mã agent bằng một hàm băm tất định thì nó tốn **0 byte**, và
cùng một mã luôn cho ra cùng một hồ sơ trên mọi máy, mọi lần chạy. Hồ sơ chỉ
cần ghi xuống khi người dùng SỬA nó — lúc ấy mới có một bản ghi, và bản ghi ấy
mang ý nghĩa "người này đã tự khai", khác hẳn "hệ thống đoán".

Phân biệt ấy quan trọng hơn chuyện tiết kiệm đĩa: nó làm hệ thống tự phân biệt
được **dữ liệu suy ra** với **dữ liệu người dùng khai**. Bất biến số 3 của dự
án đòi đúng điều đó — suy luận phải mang nhãn suy luận.

=============================================================================
23 LĨNH VỰC LÀ CẤU TRÚC CÔNG KHAI, DANH SÁCH NGÀNH THÌ CHƯA ĐỦ
=============================================================================
`LINH_VUC` dưới đây là 23 lĩnh vực đào tạo theo Danh mục giáo dục đào tạo cấp
IV của Bộ GD&ĐT — cấu trúc công khai. Mỗi lĩnh vực kèm VÀI ngành ĐẠI DIỆN, KHÔNG
phải danh mục đầy đủ (danh mục thật có hàng trăm ngành). Muốn đủ thì nạp từ
chính văn bản của Bộ; tệp này CỐ Ý không bịa cho đủ số.
"""
import hashlib
from typing import Any, Dict, List

try:
    from .khung import BAC_SAU_PT, CAP_HOC, mon_cua_cap
except ImportError:  # chạy thẳng tệp
    from khung import BAC_SAU_PT, CAP_HOC, mon_cua_cap

NAM_MOC = 2026

LINH_VUC = (
    ("khoa-hoc-giao-duc",      "Khoa học giáo dục và đào tạo giáo viên", ("Giáo dục Tiểu học", "Sư phạm Toán", "Sư phạm Ngữ văn", "Giáo dục Mầm non")),
    ("nghe-thuat",             "Nghệ thuật",                     ("Thiết kế đồ hoạ", "Kiến trúc nội thất", "Âm nhạc học")),
    ("nhan-van",               "Nhân văn",                       ("Ngôn ngữ Anh", "Việt Nam học", "Văn học", "Ngôn ngữ Nhật")),
    ("khxh-hanh-vi",           "Khoa học xã hội và hành vi",     ("Kinh tế", "Tâm lý học", "Xã hội học", "Quốc tế học")),
    ("bao-chi-thong-tin",      "Báo chí và thông tin",           ("Báo chí", "Quan hệ công chúng", "Thông tin - Thư viện")),
    ("kinh-doanh-quan-ly",     "Kinh doanh và quản lý",          ("Quản trị kinh doanh", "Tài chính - Ngân hàng", "Kế toán", "Marketing", "Logistics và Quản lý chuỗi cung ứng")),
    ("phap-luat",              "Pháp luật",                      ("Luật", "Luật kinh tế", "Luật quốc tế")),
    ("khoa-hoc-su-song",       "Khoa học sự sống",               ("Công nghệ sinh học", "Sinh học ứng dụng")),
    ("khoa-hoc-tu-nhien",      "Khoa học tự nhiên",              ("Toán học", "Vật lý học", "Hoá học", "Khoa học môi trường")),
    ("toan-thong-ke",          "Toán và thống kê",               ("Toán ứng dụng", "Thống kê", "Khoa học dữ liệu")),
    ("may-tinh-cntt",          "Máy tính và công nghệ thông tin",("Công nghệ thông tin", "Khoa học máy tính", "Kỹ thuật phần mềm", "An toàn thông tin", "Trí tuệ nhân tạo")),
    ("cong-nghe-ky-thuat",     "Công nghệ kỹ thuật",             ("Công nghệ kỹ thuật cơ khí", "Công nghệ kỹ thuật điện", "Công nghệ kỹ thuật ô tô")),
    ("ky-thuat",               "Kỹ thuật",                       ("Kỹ thuật cơ khí", "Kỹ thuật điện tử - viễn thông", "Kỹ thuật điều khiển và tự động hoá", "Kỹ thuật nhiệt")),
    ("san-xuat-che-bien",      "Sản xuất và chế biến",           ("Công nghệ thực phẩm", "Công nghệ dệt may", "Công nghệ vật liệu")),
    ("kien-truc-xay-dung",     "Kiến trúc và xây dựng",          ("Kiến trúc", "Kỹ thuật xây dựng", "Quản lý xây dựng", "Quy hoạch vùng và đô thị")),
    ("nong-lam-thuy-san",      "Nông, lâm nghiệp và thuỷ sản",   ("Nông nghiệp", "Lâm nghiệp", "Nuôi trồng thuỷ sản", "Khoa học cây trồng")),
    ("thu-y",                  "Thú y",                          ("Thú y",)),
    ("suc-khoe",               "Sức khoẻ",                       ("Y khoa", "Dược học", "Điều dưỡng", "Y học cổ truyền", "Răng - Hàm - Mặt")),
    ("dich-vu-xa-hoi",         "Dịch vụ xã hội",                 ("Công tác xã hội",)),
    ("du-lich-khach-san",      "Du lịch, khách sạn, thể thao",   ("Quản trị dịch vụ du lịch và lữ hành", "Quản trị khách sạn", "Giáo dục thể chất")),
    ("dich-vu-van-tai",        "Dịch vụ vận tải",                ("Khai thác vận tải", "Kỹ thuật tàu thuỷ", "Quản lý hàng hải")),
    ("moi-truong-bao-ve",      "Môi trường và bảo vệ môi trường",("Quản lý tài nguyên và môi trường", "Kỹ thuật môi trường")),
    ("an-ninh-quoc-phong",     "An ninh, quốc phòng",            ("Chỉ huy tham mưu", "An ninh mạng")),
)


def _bam(ma_agent: str, muc: str) -> int:
    """Số tất định từ (mã agent, mục). Dùng blake2b để cùng mã ra cùng kết quả
    trên mọi máy — `hash()` của Python thay đổi mỗi lần chạy, dùng nó ở đây thì
    hồ sơ của một người đổi sau mỗi lần khởi động lại."""
    h = hashlib.blake2b(("%s|%s" % (ma_agent, muc)).encode("utf-8"), digest_size=8)
    return int.from_bytes(h.digest(), "big")


def _chon_theo_ti_le(ma_agent: str, muc: str, danh_sach) -> Dict[str, Any]:
    tong = sum(x["ti_le"] for x in danh_sach)
    diem = (_bam(ma_agent, muc) % 1_000_000) / 1_000_000 * tong
    cong = 0.0
    for x in danh_sach:
        cong += x["ti_le"]
        if diem < cong:
            return x
    return danh_sach[-1]


def ho_so_hoc_van(ma_agent: str) -> Dict[str, Any]:
    """Hồ sơ học vấn TÍNH RA từ mã agent. Không đọc CSDL, không ghi gì.

    Mọi trường đều mang `suy_ra = True`: đây là dữ liệu hệ thống SUY RA, không
    phải người dùng khai. Nhãn ấy phải đi theo dữ liệu tới tận nơi dùng, nếu
    không một con số suy luận sẽ được trích dẫn như một sự thật đã xác minh.
    """
    bac = _chon_theo_ti_le(ma_agent, "bac", BAC_SAU_PT)
    lv = LINH_VUC[_bam(ma_agent, "linh-vuc") % len(LINH_VUC)]
    nganh = lv[2][_bam(ma_agent, "nganh") % len(lv[2])]
    tuoi = 22 + _bam(ma_agent, "tuoi") % 44          # 22–65
    nam_tn_pt = NAM_MOC - (tuoi - 18)

    hs = {
        "ma_agent": ma_agent,
        "suy_ra": True,
        "tuoi": tuoi,
        "pho_thong": {
            "hoan_thanh": True,
            "nam_tot_nghiep": nam_tn_pt,
            "so_mon_da_hoc": sum(len(mon_cua_cap(c["ma"])) for c in CAP_HOC),
        },
        "bac_sau_pho_thong": {"ma": bac["ma"], "ten": bac["ten"]},
    }
    if bac["ma"] != "khong":
        hs["chuyen_mon"] = {
            "linh_vuc_ma": lv[0], "linh_vuc": lv[1], "nganh": nganh,
            "nam_tot_nghiep": min(NAM_MOC, nam_tn_pt + (4 if bac["ma"] in ("dai-hoc", "cao-dang") else 6)),
        }
    return hs


def phan_bo(so_agent: int, tien_to: str = "nd") -> Dict[str, Any]:
    """Phân bố học vấn trên N agent — để kiểm tỉ lệ có ra đúng không."""
    dem_bac: Dict[str, int] = {}
    dem_lv: Dict[str, int] = {}
    for i in range(so_agent):
        hs = ho_so_hoc_van("%s.%08d" % (tien_to, i))
        b = hs["bac_sau_pho_thong"]["ma"]
        dem_bac[b] = dem_bac.get(b, 0) + 1
        if "chuyen_mon" in hs:
            lv = hs["chuyen_mon"]["linh_vuc_ma"]
            dem_lv[lv] = dem_lv.get(lv, 0) + 1
    return {"so_agent": so_agent, "theo_bac": dem_bac, "theo_linh_vuc": dem_lv}


def so_nganh_dai_dien() -> int:
    return sum(len(lv[2]) for lv in LINH_VUC)
