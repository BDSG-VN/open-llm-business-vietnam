#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cong/khong-ha-tang.py — CỔNG 2/4: chặn dấu vết hạ tầng nội bộ.

VÌ SAO CỔNG NÀY TỒN TẠI
  Bí mật (cổng 1) thì thu hồi được: đổi khoá là xong. Hạ tầng thì KHÔNG thu hồi được.
  Một địa chỉ IP máy chủ, một đường dẫn /home/<người dùng>, một tên container, một số cổng
  nội bộ — đăng lên kho công khai là đăng vĩnh viễn, và nó cho người lạ bản đồ để dò.
  Đây là thứ không có nút "revoke".

PHẠM VI TỰ KHAI
  CÓ quét: IPv4 công cộng, đường dẫn vận hành (theo HÌNH DẠNG), tên container/dịch vụ và
    tên miền quản trị nội bộ (so theo BĂM), số cổng nội bộ đã khai. Quét mọi tệp văn bản.
  Danh sách tên nội bộ lưu dưới dạng BĂM, không viết thẳng — lý do đầy đủ ghi ngay tại chỗ
    khai BAM_TEN_NOI_BO. Nói trước giới hạn để không ai tin quá mức: băm KHÔNG phải mã hoá,
    tên ngắn và đoán được thì dò từ điển ra ngay. Thứ băm giải quyết được đúng một việc —
    tệp cổng không còn là bản kê hạ tầng ĐỌC ĐƯỢC và TÌM KIẾM ĐƯỢC trong kho công khai.
  KHÔNG quét: IPv6 (CHƯA ĐO — dự án chưa dùng, nên chưa viết luật; đừng tưởng là đã chặn).
    Nội dung tệp nhị phân. Ảnh chụp màn hình (một ảnh terminal lộ đủ mọi thứ mà cổng
    này mù tịt — đây là lỗ thủng đã biết, ghi ra để người sau đừng tin nhầm).
  CÓ miễn trừ nội dòng: cổng này là heuristic, sẽ có dương tính giả thật (xem BẪY ĐO 2).
    Miễn trừ bằng một dấu ghi ngay trên dòng đó, kèm BẮT BUỘC phần ly-do=<lý do cụ thể>.
    Cú pháp đầy đủ nằm trong cong/README.md — cố ý không viết thẳng ở đây, xem ghi chú
    tại chỗ khai DAU_MIEN_TRU bên dưới.
    Miễn trừ KHÔNG có phần lý do thì chính nó là vi phạm. Một ngoại lệ không lý do là
    một lỗ thủng mà vài tháng sau không ai nhớ vì sao đã mở.

BẪY ĐO ĐÃ GẶP THẬT — ĐỌC TRƯỚC KHI SỬA CỔNG NÀY
  1) `git grep` dùng POSIX ERE và KHÔNG hiểu `\\b`. Câu lệnh dò IP viết kèm `\\b` trả về
     0 kết quả, suýt cho kết luận "kho sạch" trong khi kho bẩn. Cho nên cổng này viết bằng
     Python re, và có --tu-kiem cài sẵn một chuỗi IP công cộng để chứng minh cổng CẮN.
     Quy tắc rút ra: cổng nào chưa bị thử ngược thì chưa được tin.
  2) Số tiền kiểu Việt Nam trông y hệt địa chỉ IP. Lần quét ngữ liệu ngày 25/09/2026 có
     5 khớp "địa chỉ IP" thì CẢ 5 đều là dương tính giả, đều là số tiền (ví dụ dạng
     120.086.720.000 đồng). Cách chặn ở đây KHÔNG phải nới luật mà là siết đúng chỗ:
       - octet có số 0 đứng đầu mà dài hơn 1 chữ số thì không phải IP thật (086, 000);
       - hai bên khớp không được dính chữ số hoặc dấu chấm (chặn chuỗi số dài hơn);
       - ngay sau khớp là "đồng"/"VND"/"₫" thì là tiền.
     Ba luật ấy loại sạch 5 dương tính giả đã gặp mà không bỏ lọt IP thật.
  3) BẢN ĐẦU CỦA CHÍNH CỔNG NÀY LÀ MỘT BẢN KÊ HẠ TẦNG (phát hiện trong lần soát đối kháng
     25/09/2026). Nó liệt kê thẳng tên container, tên miền quản trị và thư mục vận hành,
     chỉ tách bằng dấu "+" để cổng không tự bắt mình. Cách ấy qua được cổng nhưng KHÔNG qua
     được người đọc: tệp cổng nằm trong kho CÔNG KHAI, nên nó trở thành đúng cái bản đồ mà
     nó sinh ra để chặn — đọc bằng mắt được, tìm bằng máy tìm kiếm mã nguồn được. Tệ hơn,
     một dòng còn chú thích rõ thư mục nào trên máy chủ có chứa bí mật.
     Bài học: né được cổng KHÔNG phải là đạt cổng. Khi phải viết chuỗi cấm vào chính cổng,
     cách đúng là đừng viết nó ra — so theo hình dạng, hoặc so theo băm.

MÃ THOÁT: 0 sạch · 1 có vi phạm · 2 cổng tự vỡ (fail-closed).
Đo lần đầu: 25/09/2026.
"""

import argparse
import hashlib
import os
import re
import sys
import tempfile

BO_QUA_THU_MUC = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"}

DUOI_NHI_PHAN_DA_KHAI = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf",
    ".pdf", ".zip", ".gz", ".bz2", ".xz", ".tar", ".parquet", ".arrow", ".npy", ".npz",
    ".safetensors", ".pth", ".bin", ".onnx", ".gguf", ".mp4", ".webm", ".mp3", ".wav",
}

# Dấu miễn trừ được GHÉP lúc chạy. Lý do rất thực tế: nếu viết thẳng, mọi dòng trong
# chính tệp này có nhắc tới cú pháp ấy sẽ tự miễn trừ chính nó, và bảng tổng kết sẽ
# báo "đang dùng N miễn trừ" trong khi kho chưa dùng cái nào — một con số sai ngay từ đầu.
# Cú pháp đầy đủ cho người dùng được ghi trong cong/README.md (và dòng ví dụ ở đó tự
# miễn trừ chính nó, kèm lý do — coi như bản trình diễn cơ chế đang chạy thật).
DAU_MIEN_TRU = "cong" + ":bo-qua"
MIEN_TRU = re.compile(re.escape(DAU_MIEN_TRU) + r"\s+khong-ha-tang(?:\s+ly-do=(\S[^\n]*))?")

# ── IPv4 ───────────────────────────────────────────────────────────────────────
# Hai bên chặn [\d.] để không cắt một khúc giữa của chuỗi số dài (số tiền, mã số).
MAU_IPV4 = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?![\d.])")
SAU_KHOP_LA_TIEN = re.compile(r"\s*(đồng|VNĐ|VND|₫|tỷ|triệu)", re.IGNORECASE)

# Dải được phép xuất hiện, kèm LÝ DO từng dải. Không có dải nào vào đây mà không có lý do.
def phan_loai_ip(o1, o2, o3, o4):
    """Trả (duoc_phep, ly_do). Chỉ IP định tuyến công cộng mới bị chặn."""
    if o1 == 127:
        return True, "loopback — không trỏ tới máy nào ngoài máy đang chạy"
    if o1 == 0:
        return True, "0.0.0.0/8 — nghĩa là 'lắng nghe mọi giao diện', không lộ máy chủ nào"
    if o1 == 10:
        return True, "RFC1918 mạng riêng — không định tuyến trên Internet"
    if o1 == 172 and 16 <= o2 <= 31:
        return True, "RFC1918 mạng riêng (dải Docker mặc định hay rơi vào đây)"
    if o1 == 192 and o2 == 168:
        return True, "RFC1918 mạng riêng"
    if o1 == 169 and o2 == 254:
        return True, "link-local, tự cấp khi không có DHCP"
    if o1 == 100 and 64 <= o2 <= 127:
        return True, "CGNAT của nhà mạng, không trỏ tới máy chủ dự án"
    if (o1, o2, o3) in ((192, 0, 2), (198, 51, 100), (203, 0, 113)):
        return True, "RFC5737 — dải DÀNH RIÊNG cho ví dụ trong tài liệu, dùng thoải mái"
    if o1 >= 224:
        return True, "multicast/dành riêng/broadcast"
    return False, ""


def octet_hop_le(chuoi):
    """'086' và '000' KHÔNG phải octet: IP thật không viết số 0 đứng đầu.

    Đây chính là luật giết sạch 5 dương tính giả 'số tiền Việt Nam' đo ngày 25/09/2026.
    """
    if len(chuoi) > 1 and chuoi[0] == "0":
        return False
    return 0 <= int(chuoi) <= 255


# ── Đường dẫn vận hành: bắt theo HÌNH DẠNG, không theo tên ─────────────────────
# Hình dạng thì mô tả được mà không phải viết ra tên thật của ai. Đổi lại, luật hẹp hơn
# bản cũ: "/home/<người dùng>" trần KHÔNG còn bị bắt, phải có tiếp "domains"/"public_html"
# mới bắt — đó chính là hình dạng bố cục hosting, thứ đáng giấu. Khai ra chỗ hẹp đi này
# để người sau biết cổng KHÔNG hứa nhiều hơn nó làm được.
DUONG_DAN_VAN_HANH = [
    (re.compile(r"/home/[A-Za-z0-9_\-]+/(?:domains|public_html)\b"),
     "bố cục thư mục tên miền của bảng điều khiển máy chủ"),
    (re.compile(r"/root/\.[A-Za-z0-9_.\-]+"),
     "thư mục ẩn trong home của root — nơi hay cất khoá và chứng chỉ"),
    (re.compile(r"/usr/local/(?:directadmin|cpanel|plesk)\b"),
     "đường dẫn bảng điều khiển máy chủ"),
    (re.compile(r"(?<![A-Za-z0-9_./\-])/[A-Z][A-Z0-9_]{2,}/"),
     "thư mục viết hoa ngay tại gốc hệ tệp — không phải chuẩn FHS, nên gần như luôn là "
     "thư mục vận hành riêng của một tổ chức"),
]

# ── Tên nội bộ: LƯU BĂM, không lưu tên ────────────────────────────────────────
# Xem BẪY ĐO 3 ở đầu tệp để biết vì sao. Tóm tắt: bản đầu viết thẳng tên, chỉ tách bằng
# dấu "+" cho cổng khỏi tự bắt mình — qua được cổng, không qua được người đọc.
#
# So khớp theo TỪ KHOÁ TRỌN VẸN rồi so BẰNG, không phải phép "có chứa". Cách này còn bịt
# luôn một cái bẫy của bản đầu: tên miền gốc là CON của tên miền con ("vi-du.com" nằm trong
# "quan-tri.vi-du.com"), nên hễ dùng phép "có chứa" thì chỉ cần đưa tên miền gốc vào danh
# sách được phép là miễn trừ nhầm toàn bộ tên miền quản trị. Cắt trọn từ khoá rồi so bằng
# thì cái bẫy ấy biến mất theo cấu trúc — không phải nhớ nữa.
#
# Thêm một tên vào danh sách:  python3 cong/khong-ha-tang.py --bam "<chuỗi>"
# rồi dán dòng nó in ra vào đây. Đừng viết chuỗi gốc vào tệp này.
MAU_TU_KHOA = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*")
DAI_TOI_THIEU_DE_BAM = 4  # từ ngắn hơn thì băm vô nghĩa và dễ trùng với từ thường


def bam(chuoi):
    """Băm rút gọn 16 ký tự hex. KHÔNG phải mã hoá, và cổng không giả vờ là mã hoá."""
    return hashlib.sha256(chuoi.strip().strip(".-_").lower().encode("utf-8")).hexdigest()[:16]


BAM_TEN_NOI_BO = {
    "47d7e9d20f53f71d": ("ten-container", "tên container nội bộ đã khai"),
    "f91534fcd63a00cd": ("ten-container", "tên container nội bộ đã khai"),
    "959cd2042cfed151": ("ten-container", "tên container nội bộ đã khai"),
    "9274c9ad4900cb27": ("ten-container", "tên container nội bộ đã khai"),
    "3ae0c49f9d404c7b": ("ten-mien-noi-bo", "tên miền quản trị nội bộ đã khai"),
    "b6b0aecc89fc2aa4": ("ten-mien-noi-bo", "tên miền quản trị nội bộ đã khai"),
    "661bf74d5b9ed9b7": ("ten-mien-noi-bo", "tên miền quản trị nội bộ đã khai"),
    "b6482fdbdc88e681": ("ten-mien-noi-bo", "tên miền quản trị nội bộ đã khai"),
}
# Tên miền SẢN PHẨM không cần danh sách "được phép" nữa: chúng đơn giản là không có băm
# trong bảng trên. Bớt được một danh sách là bớt được một chỗ để miễn trừ nhầm.

CONG_NOI_BO = {
    "4000": "cổng một dịch vụ nội bộ đã khai",
    "5432": "cổng cơ sở dữ liệu",
    "5434": "cổng cơ sở dữ liệu thứ hai",
}
# Ghép lúc chạy để trong tệp này không tồn tại chuỗi "dấu hai chấm + số cổng".
# CỐ Ý không đặt lookbehind chặn chữ số trước dấu hai chấm: dạng hay gặp nhất là
# <máy chủ kết thúc bằng số>:<cổng>, chặn chữ số ở đó là tự làm cổng mù đúng ca cần bắt.
MAU_CONG = re.compile(re.escape(":") + r"(" + "|".join(sorted(CONG_NOI_BO)) + r")(?!\d)")
TRUOC_CONG_LA_NOI_BO = re.compile(r"(127\.0\.0\.1|localhost|0\.0\.0\.0|\[::1\])$")


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


def quet_dong(dong):
    """Trả danh sách (ma_luat, chi_tiet_khong_lo_gia_tri) cho một dòng."""
    thay = []

    # 1. IPv4 công cộng
    for khop in MAU_IPV4.finditer(dong):
        cac_octet = khop.groups()
        if not all(octet_hop_le(o) for o in cac_octet):
            continue  # số tiền Việt Nam, mã số có số 0 đứng đầu, v.v.
        if SAU_KHOP_LA_TIEN.match(dong[khop.end():]):
            continue  # "120.86.72.10 đồng" — là tiền, không phải máy chủ
        truoc = dong[:khop.start()]
        if truoc.endswith(("v", "V")) or truoc.endswith(("version ", "phiên bản ")):
            continue  # chuỗi phiên bản kiểu v1.2.3.4
        o1, o2, o3, o4 = (int(x) for x in cac_octet)
        duoc_phep, _ = phan_loai_ip(o1, o2, o3, o4)
        if not duoc_phep:
            # Che 2 octet cuối: đủ để tìm lại chỗ sửa, không đủ để trở thành bản đồ.
            thay.append(("ip-cong-cong", "%d.%d.x.x (cột %d)" % (o1, o2, khop.start() + 1)))

    # 2. Đường dẫn vận hành — theo hình dạng
    for bieu_thuc, ly_do in DUONG_DAN_VAN_HANH:
        khop = bieu_thuc.search(dong)
        if khop:
            thay.append(("duong-dan-van-hanh", "%s (cột %d)" % (ly_do, khop.start() + 1)))

    # 3. Tên nội bộ — cắt trọn từ khoá rồi so BĂM
    for khop in MAU_TU_KHOA.finditer(dong):
        tu = khop.group(0).strip(".-_")
        if len(tu) < DAI_TOI_THIEU_DE_BAM:
            continue
        muc = BAM_TEN_NOI_BO.get(bam(tu))
        if muc:
            ma, ly_do = muc
            # In lại từ khoá là đúng: nó đã nằm sẵn trên dòng bị bắt, và người sửa cần biết
            # phải xoá chữ nào. Cổng chỉ không in ra thứ mà kho CHƯA có.
            thay.append((ma, "%s — %s (cột %d)" % (tu, ly_do, khop.start() + 1)))

    # 4. Cổng nội bộ
    for khop in MAU_CONG.finditer(dong):
        if TRUOC_CONG_LA_NOI_BO.search(dong[:khop.start()]):
            continue  # gắn với loopback: không lộ máy chủ nào ở xa
        thay.append(("cong-noi-bo", "cổng %s (cột %d)" % (khop.group(1), khop.start() + 1)))

    return thay


def quet_kho(goc):
    vi_pham = []
    loi_cong = []
    so_mien_tru = 0

    for duong_dan in duyet_tep(goc):
        tuong_doi = os.path.relpath(duong_dan, goc)
        _, duoi = os.path.splitext(duong_dan.lower())
        try:
            if la_nhi_phan(duong_dan):
                if duoi in DUOI_NHI_PHAN_DA_KHAI:
                    continue
                loi_cong.append((tuong_doi, "nhị phân đuôi '%s' chưa khai — không chứng minh được là sạch" % (duoi or "(không có)")))
                continue
            with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
                for so_dong, dong in enumerate(f, start=1):
                    mt = MIEN_TRU.search(dong)
                    if mt:
                        if mt.group(1) and mt.group(1).strip():
                            so_mien_tru += 1
                            continue
                        vi_pham.append((tuong_doi, so_dong, "mien-tru-khong-ly-do",
                                        "có cong:bo-qua nhưng thiếu ly-do="))
                        continue
                    for ma, chi_tiet in quet_dong(dong):
                        vi_pham.append((tuong_doi, so_dong, ma, chi_tiet))
        except OSError as loi:
            loi_cong.append((tuong_doi, "không đọc được: %s" % loi.strerror))

    return vi_pham, loi_cong, so_mien_tru


def in_bao_cao(goc, vi_pham, loi_cong, so_mien_tru):
    print("CỔNG khong-ha-tang — gốc quét: %s" % goc)
    print("  Miễn trừ nội dòng đang dùng: %d (mỗi cái đều phải có ly-do=, xem cong/README.md)." % so_mien_tru)
    if not vi_pham and not loi_cong:
        print("  ĐẠT: không thấy IPv4 công cộng, đường dẫn vận hành, tên container, tên miền quản trị, cổng nội bộ.")
        print("  NHẮC: cổng này KHÔNG đọc ảnh chụp màn hình và CHƯA có luật IPv6 — hai chỗ ấy vẫn phải soi bằng mắt.")
        return
    if vi_pham:
        print("  HỎNG: %d vị trí." % len(vi_pham))
        for duong_dan, so_dong, ma, chi_tiet in vi_pham:
            print("    %-46s:%-5d [%s] %s" % (duong_dan, so_dong, ma, chi_tiet))
        print("  Cách xử: bỏ chuỗi ra khỏi tài liệu, hoặc thay bằng dải ví dụ RFC5737 (192.0.2.x,")
        print("  198.51.100.x, 203.0.113.x) vốn sinh ra để làm ví dụ. Chỉ khi thật sự cần mới miễn trừ:")
        print("  thêm vào cuối dòng   %s khong-ha-tang ly-do=<lý do cụ thể>" % DAU_MIEN_TRU)
    if loi_cong:
        print("  HỎNG (fail-closed): %d tệp cổng không tự chứng minh được." % len(loi_cong))
        for duong_dan, ghi_chu in loi_cong:
            print("    %-52s %s" % (duong_dan, ghi_chu))


def tu_kiem():
    """Bài thử ngược BẮT BUỘC — sinh ra vì bẫy `\\b` của git grep từng cho kết luận sai.

    Chuỗi IP thử được ghép lúc chạy, và CỐ Ý không phải IP thật của dự án.
    """
    # Hai octet đầu 198.18 thuộc dải mà RFC 2544 dành riêng cho việc đo đạc, và dải ấy
    # KHÔNG BAO GIỜ được định tuyến trên Internet. (Viết hai octet chứ không viết đủ bốn:
    # đủ bốn thì chính cổng bắt dòng chú thích này — đã bị bắt thật một lần khi sửa.)
    # Chọn dải ấy thay cho một địa chỉ bịa ngẫu nhiên là có chủ ý: một địa
    # chỉ "bịa" vẫn có thể là máy thật của người khác, và kho này là kho công khai — đăng
    # lên là chỉ tay vào máy người ta. Dải RFC5737 thì không dùng được ở đây, vì cổng cố ý
    # miễn trừ nó, nên nó không chứng minh được cổng CẮN.
    ip_thu = "198" + "." + "18" + "." + "0" + "." + "7"
    # Hai tên BỊA, chỉ tồn tại trong bài thử này, được nạp băm lúc chạy. Mục đích: chứng
    # minh CƠ CHẾ băm cắn được, mà không phải viết một tên nội bộ thật vào kho công khai.
    # Nạp xong thì gỡ ra ở cuối hàm — bài thử không được để lại dấu vết lên lần quét thật.
    ten_gia = "vi-du-container-noi-bo.test"
    mien_gia = "quan-tri.vi-du-noi-bo.test"
    BAM_TEN_NOI_BO[bam(ten_gia)] = ("ten-container", "mẫu bịa, chỉ dùng trong bài tự kiểm")
    BAM_TEN_NOI_BO[bam(mien_gia)] = ("ten-mien-noi-bo", "mẫu bịa, chỉ dùng trong bài tự kiểm")
    mau = {
        "ip-cong-cong": "MAY_CHU = '" + ip_thu + "'",
        # Ghép lúc chạy, cùng lý do như mọi mẫu khác: viết thẳng thì cổng bắt chính tệp này.
        "duong-dan-van-hanh": "rsync tới " + "/home/" + "nguoi-dung-vi-du" + "/domains/",
        "ten-container": "docker restart " + ten_gia,
        "ten-mien-noi-bo": "đăng nhập " + mien_gia,
        "cong-noi-bo": "gateway tại 10.1.2.3" + ":" + "4000",
        "mien-tru-khong-ly-do": "MAY = '" + ip_thu + "'  # " + DAU_MIEN_TRU + " khong-ha-tang",
    }
    sach = [
        "# Số tiền Việt Nam — 5/5 dương tính giả đã gặp ngày 25/09/2026, phải KHÔNG bị bắt:",
        "doanh_thu = '120.086.720.000 đồng'",
        "von = '10.000.000.000 đồng'",
        "# Dải ví dụ RFC5737 và loopback phải KHÔNG bị bắt:",
        "VI_DU = '203.0.113.7'   ;  CUC_BO = '127.0.0.1'  ;  MOI_GIAO_DIEN = '0.0.0.0'",
        "MANG_RIENG = '172.17.0.2'",
        "# Tên miền sản phẩm công khai phải KHÔNG bị bắt:",
        "API = 'https://llm.bdsg.vn/v1/models'",
        "# Cổng nội bộ gắn loopback phải KHÔNG bị bắt:",
        "CUC_BO_GATEWAY = 'http://127.0.0.1" + ":" + "4000'",
        "# So BẰNG trên trọn từ khoá, không phải 'có chứa': một từ khác CHỨA tên cấm bên",
        "# trong nó vẫn là một từ khác, phải KHÔNG bị bắt.",
        "KHAC = 'khong-phai-" + ten_gia + "'",
        "# Miễn trừ CÓ lý do phải KHÔNG bị bắt:",
        "MAY = '" + ip_thu + "'  # " + DAU_MIEN_TRU + " khong-ha-tang ly-do=IP dải RFC2544 trong bài thử ngược",
    ]
    hong = []
    with tempfile.TemporaryDirectory() as tam:
        for ma, noi_dung in mau.items():
            with open(os.path.join(tam, "cai_%s.txt" % ma.replace("-", "_")), "w", encoding="utf-8") as f:
                f.write(noi_dung + "\n")
        with open(os.path.join(tam, "sach.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sach) + "\n")

        vi_pham, loi_cong, so_mien_tru = quet_kho(tam)
        da_bat = set(v[2] for v in vi_pham)
        for ma in mau:
            if ma not in da_bat:
                hong.append("KHÔNG bắt được mẫu '%s' — cổng thủng ở luật này." % ma)
        ban_nham = [v for v in vi_pham if v[0] == "sach.txt"]
        for v in ban_nham:
            hong.append("Bắt nhầm dòng sạch %s:%d [%s] %s" % v)
        if so_mien_tru != 1:
            hong.append("Miễn trừ CÓ lý do phải được đếm đúng 1 lần, đếm được %d." % so_mien_tru)
        if loi_cong:
            hong.append("Có lỗi cổng ngoài dự kiến trong bài thử: %s" % loi_cong)

    del BAM_TEN_NOI_BO[bam(ten_gia)]
    del BAM_TEN_NOI_BO[bam(mien_gia)]

    print("TỰ KIỂM khong-ha-tang: %d mẫu cài, %d dòng sạch làm đối chứng." % (len(mau), len(sach)))
    if hong:
        for d in hong:
            print("  HỎNG: %s" % d)
        return 1
    print("  ĐẠT: cổng CẮN đủ 6 mẫu cài (gồm 1 địa chỉ IP dải RFC2544 và 2 tên nội bộ BỊA")
    print("       nạp băm lúc chạy — chứng minh cơ chế băm cắn mà không viết tên thật vào kho);")
    print("       và KHÔNG cắn nhầm số tiền Việt Nam, dải RFC5737, loopback, tên miền sản phẩm,")
    print("       hay một từ khác chỉ CHỨA tên cấm bên trong nó.")
    return 0


def main():
    bo_phan_tich = argparse.ArgumentParser(description="Cổng 2/4: chặn dấu vết hạ tầng nội bộ.")
    bo_phan_tich.add_argument("--goc", default=None, help="thư mục gốc cần quét (mặc định: thư mục cha của cong/)")
    bo_phan_tich.add_argument("--tu-kiem", action="store_true", help="chạy bài thử ngược, chứng minh cổng cắn")
    bo_phan_tich.add_argument("--bam", metavar="CHUỖI", default=None,
                              help="in dòng băm để dán vào BAM_TEN_NOI_BO (đừng viết chuỗi gốc vào tệp cổng)")
    tham_so = bo_phan_tich.parse_args()

    if tham_so.bam:
        # In băm ra màn hình người đang gõ lệnh, KHÔNG ghi vào tệp nào. Chuỗi gốc không
        # bao giờ được để lại trong kho — đó là toàn bộ điểm của việc lưu băm.
        print('    "%s": ("ten-container", "tên nội bộ đã khai"),  # sửa mã luật cho đúng loại'
              % bam(tham_so.bam))
        return 0

    if tham_so.tu_kiem:
        return tu_kiem()

    goc = tham_so.goc or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir(goc):
        print("HỎNG: không thấy thư mục gốc '%s'." % goc)
        return 2
    try:
        vi_pham, loi_cong, so_mien_tru = quet_kho(goc)
    except Exception as loi:
        print("HỎNG: cổng tự vỡ khi quét (%s: %s). Coi như KHÔNG đạt." % (type(loi).__name__, loi))
        return 2

    in_bao_cao(goc, vi_pham, loi_cong, so_mien_tru)
    if vi_pham:
        return 1
    if loi_cong:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
