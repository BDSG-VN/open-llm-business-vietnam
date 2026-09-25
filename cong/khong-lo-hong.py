#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cong/khong-lo-hong.py — CỔNG 4/4: chặn việc công bố chi tiết lỗ hổng ĐANG SỐNG.

VÌ SAO CỔNG NÀY TỒN TẠI — đọc kỹ, vì đây là cổng dễ bị hiểu sai nhất
  Ba cổng trước chặn thứ thuộc về người khác (bí mật, hạ tầng, dữ liệu). Cổng này chặn
  một thứ khác hẳn: SỰ THẬT VỀ CHÍNH MÌNH, loại sự thật mà nói ra lúc này thì có người
  bị hại.

  Bối cảnh đo ngày 25/09/2026: dự án có ít nhất một vấn đề xác thực mới bịt tạm ở một đầu,
  phần gốc CHƯA sửa; và một đợt xâm nhập hồi 24/08 để lại bài học là hệ đang chạy không
  sạch như người ta tưởng. Trong hoàn cảnh ấy:
    - viết một đường khai thác vào kho công khai mất 10 giây;
    - vá nó trên hệ đang chạy mất nhiều ngày;
    - và việc đẩy lên là MỘT CHIỀU: GitHub giữ lịch sử, bản fork giữ bản sao, bộ nhớ đệm
      máy tìm kiếm giữ nội dung. Xoá commit KHÔNG thu hồi được thứ đã công bố.
  Khoảng chênh giữa 10 giây và nhiều ngày chính là cửa sổ tấn công. Cổng này đóng cửa sổ đó.

  ĐÂY KHÔNG PHẢI LỆNH CẤM NÓI THẬT. Cổng chặn CÁCH KHAI THÁC, không chặn LỜI THỪA NHẬN.
  Viết "hệ có một vấn đề xác thực chưa vá xong, đang xử lý" — ĐƯỢC, và nên viết.
  Viết kèm tên tệp, số dòng, tên cookie và giá trị của nó — KHÔNG, vì đó là hướng dẫn
  từng bước cho người lạ. Ranh giới là: người đọc có thể LÀM LẠI được hay không.
  Khi hệ đã vá xong thì bỏ miễn trừ và viết đầy đủ — công bố sau khi vá là điều tử tế,
  công bố trước khi vá là chuyện khác.

PHẠM VI TỰ KHAI
  Luật 1: tên cookie phiên đi KÈM một giá trị trông như thật.
  Luật 2: cờ bảo mật bị tắt (chống giả mạo, chống đọc cookie bằng JavaScript, kiểm chứng
          chỉ TLS…). Thứ này vừa là mô tả lỗ hổng, vừa là mã xấu người ta hay chép lại.
  Luật 3: đường dẫn tệp nội bộ của hệ PHP đang chạy.
  Luật 4: số dòng của tệp hệ đang chạy (dạng <tệp>.php:<số dòng>).
  Luật 5 (HAI YẾU TỐ): một từ mô tả khai thác CHỈ bị tính là vi phạm khi trên cùng dòng
          còn có một VẬT THỂ CỤ THỂ của hệ đang chạy (khớp luật 3, luật 4, hoặc một tên
          miền quản trị nội bộ). Cố ý làm hai yếu tố, vì nếu chỉ dò từ khoá thì cổng sẽ
          cắn nát mọi tài liệu bảo mật tử tế — kể cả chính phần VÌ SAO bạn đang đọc.
  KHÔNG quét: ảnh chụp màn hình, tệp nhị phân. Một ảnh chụp bảng điều khiển lộ nhiều hơn
          mọi thứ cổng này bắt được — chỗ đó vẫn phải soi bằng mắt. CHƯA ĐO, đừng tin nhầm.
  CÓ miễn trừ nội dòng kèm lý do bắt buộc (cú pháp đầy đủ ở cong/README.md), vì luật 5 là
          heuristic và chắc chắn có dương tính giả.

MÃ THOÁT: 0 sạch · 1 có vi phạm · 2 cổng tự vỡ (fail-closed).
Đo lần đầu: 25/09/2026.
"""

import argparse
import os
import re
import sys
import tempfile

BO_QUA_THU_MUC = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"}
DUOI_BO_QUA = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf",
    ".pdf", ".zip", ".gz", ".bz2", ".xz", ".tar", ".parquet", ".npy", ".npz",
    ".safetensors", ".pth", ".bin", ".onnx", ".gguf", ".mp4", ".webm", ".mp3", ".wav",
}

# Xem ghi chú cùng tên trong khong-ha-tang.py: ghép lúc chạy để tệp này không tự miễn trừ
# chính nó và làm sai con số "đang dùng bao nhiêu miễn trừ".
DAU_MIEN_TRU = "cong" + ":bo-qua"
MIEN_TRU = re.compile(re.escape(DAU_MIEN_TRU) + r"\s+khong-lo-hong(?:\s+ly-do=(\S[^\n]*))?")

# ── Luật 1: cookie phiên kèm giá trị ──────────────────────────────────────────
TEN_COOKIE_PHIEN = [
    "bdsg_dn", "PHPSESSID", "sessionid", "session_id", "csrftoken",
    "laravel_session", "ci_session", "remember_token", "access_token", "refresh_token",
]
COOKIE_KEM_GIA_TRI = re.compile(
    r"(?i)\b(" + "|".join(TEN_COOKIE_PHIEN) + r")\s*[=:]\s*[\"']?([A-Za-z0-9._\-]{8,})")
# Giá trị giả trong tài liệu thì được: tài liệu phải chỉ được chỗ điền.
GIA_TRI_GIA = re.compile(
    r"^(?:\$\{[^}]*\}|<[^>]*>|\{\{[^}]*\}\}|x{3,}|\.{3,}|GIA_TRI[A-Z_]*|REDACTED|AN_DI|"
    r"CHUOI_PHIEN|MAU_[A-Z_]+|None|null|true|false)$", re.IGNORECASE)

# ── Luật 2: cờ bảo mật bị tắt ─────────────────────────────────────────────────
# Viết tên cờ bằng chuỗi ghép để chính tệp này không khớp luật của chính nó.
CO_BAO_MAT_TAT = [
    (re.compile(r"(?i)\b" + "http" + r"only\s*[=:]\s*(?:false|0|off|no)\b"),
     "cờ chặn JavaScript đọc cookie bị tắt — công bố kèm tên cookie là chỉ luôn đường lấy phiên"),
    (re.compile(r"(?i)\bsecure\s*[=:]\s*(?:false|0|off)\b"),
     "cookie được phép đi trên kênh không mã hoá"),
    (re.compile(r"(?i)\bsame" + r"site\s*[=:]\s*[\"']?none\b"),
     "cookie gửi kèm cả yêu cầu từ trang khác"),
    (re.compile(r"(?i)\bverify\s*=\s*False\b"),
     "tắt kiểm chứng chỉ TLS — vừa là lỗ hổng, vừa là mã xấu người ta hay chép lại"),
    (re.compile(r"(?i)\breject" + r"Unauthorized\s*:\s*false\b"),
     "tắt kiểm chứng chỉ TLS phía Node"),
    (re.compile(r"(?i)@csrf" + r"_exempt\b"),
     "tắt chống giả mạo yêu cầu trên một tuyến cụ thể"),
    (re.compile(r"(?i)\bALLOWED_HOSTS\s*=\s*\[\s*[\"']\*[\"']\s*\]"),
     "nhận mọi tên miền — thường đi kèm sự cố thật"),
]

# ── Luật 3 và 4: vật thể cụ thể của hệ đang chạy ──────────────────────────────
DUONG_DAN_PHP_NOI_BO = re.compile(
    r"/(?:application|modules|system|administrator)/"
    r"(?:controllers|models|views|libraries|helpers|hooks|config)/[A-Za-z0-9_\-/]+\.php")
DUONG_DAN_NGUOI_DUNG_PHP = re.compile(r"/home/[a-z0-9_]+/(?:domains|public_html)/[^\s\"']+\.(?:php|inc)")
SO_DONG_HE_DANG_CHAY = re.compile(r"[A-Za-z0-9_\-/]+\.(?:php|inc)\s*(?::|,\s*dòng\s*|\s+line\s+)\d{1,5}\b")
TEN_MIEN_QUAN_TRI = re.compile(r"\b(?:crm|admin|sv|metadata|bdsgerp|bdsghost)\.[a-z0-9\-]+\.[a-z]{2,}\b")

# ── Luật 5: từ mô tả khai thác (chỉ tính khi đi kèm vật thể cụ thể) ───────────
TU_KHAI_THAC = re.compile(
    r"(?i)\b(khai thác|đường khai thác|bypass|vượt qua xác thực|chiếm quyền|leo thang đặc quyền|"
    r"SQL ?injection|SQLi|XSS|CSRF|RCE|path traversal|deserializ\w*|cửa hậu|backdoor|web ?shell|"
    r"chiếm phiên|đoạt phiên|giả mạo phiên)\b")


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


def vat_the_cu_the(dong):
    """Trả mô tả vật thể cụ thể của hệ đang chạy có trên dòng, hoặc None.

    Đây là yếu tố thứ hai của luật 5. Không có nó thì một câu văn bàn về bảo mật
    vẫn chỉ là câu văn bàn về bảo mật.
    """
    khop = DUONG_DAN_PHP_NOI_BO.search(dong) or DUONG_DAN_NGUOI_DUNG_PHP.search(dong)
    if khop:
        return "đường dẫn tệp nội bộ"
    if SO_DONG_HE_DANG_CHAY.search(dong):
        return "số dòng của tệp hệ đang chạy"
    if TEN_MIEN_QUAN_TRI.search(dong):
        return "tên miền quản trị nội bộ"
    return None


def quet_dong(dong):
    """Trả danh sách (ma_luat, chi_tiet). Chi tiết KHÔNG bao giờ chứa giá trị phiên thật."""
    thay = []

    for khop in COOKIE_KEM_GIA_TRI.finditer(dong):
        ten, gia_tri = khop.group(1), khop.group(2)
        if GIA_TRI_GIA.match(gia_tri):
            continue  # chỗ điền trong tài liệu, không phải phiên thật
        thay.append(("cookie-phien-kem-gia-tri",
                     "cookie '%s' đi kèm một giá trị dài %d ký tự (giá trị KHÔNG in ra). "
                     "Nếu là phiên thật thì phải huỷ phiên, không phải chỉ xoá dòng."
                     % (ten, len(gia_tri))))

    for bieu_thuc, ly_do in CO_BAO_MAT_TAT:
        if bieu_thuc.search(dong):
            thay.append(("co-bao-mat-tat", ly_do))

    for bieu_thuc, ma in ((DUONG_DAN_PHP_NOI_BO, "duong-dan-php-noi-bo"),
                          (DUONG_DAN_NGUOI_DUNG_PHP, "duong-dan-php-noi-bo")):
        if bieu_thuc.search(dong):
            thay.append((ma, "đường dẫn tệp của hệ PHP đang chạy — vẽ sẵn bản đồ mã nguồn cho người dò"))
            break

    if SO_DONG_HE_DANG_CHAY.search(dong):
        thay.append(("so-dong-he-dang-chay",
                     "trỏ đúng số dòng của hệ đang chạy — chỉ có ích cho người muốn tới đó trước khi nó được vá"))

    khop_tu = TU_KHAI_THAC.search(dong)
    if khop_tu:
        vat_the = vat_the_cu_the(dong)
        if vat_the:
            thay.append(("mo-ta-khai-thac",
                         "từ '%s' đi kèm %s trên cùng một dòng ⇒ đủ để làm lại. "
                         "Giữ phần thừa nhận, bỏ phần chỉ đường." % (khop_tu.group(1), vat_the)))

    return thay


def quet_kho(goc):
    vi_pham = []
    loi_cong = []
    so_mien_tru = 0

    for duong_dan in duyet_tep(goc):
        tuong_doi = os.path.relpath(duong_dan, goc)
        _, duoi = os.path.splitext(duong_dan.lower())
        if duoi in DUOI_BO_QUA:
            continue
        try:
            if la_nhi_phan(duong_dan):
                continue  # đã khai ở PHẠM VI: cổng này không đọc nhị phân
            with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
                for so_dong, dong in enumerate(f, start=1):
                    mt = MIEN_TRU.search(dong)
                    if mt:
                        if mt.group(1) and mt.group(1).strip():
                            so_mien_tru += 1
                            continue
                        vi_pham.append((tuong_doi, so_dong, "mien-tru-khong-ly-do",
                                        "có dấu miễn trừ nhưng thiếu phần ly-do="))
                        continue
                    for ma, chi_tiet in quet_dong(dong):
                        vi_pham.append((tuong_doi, so_dong, ma, chi_tiet))
        except OSError as loi:
            loi_cong.append((tuong_doi, "không đọc được: %s" % loi.strerror))

    return vi_pham, loi_cong, so_mien_tru


def in_bao_cao(goc, vi_pham, loi_cong, so_mien_tru):
    print("CỔNG khong-lo-hong — gốc quét: %s" % goc)
    print("  Miễn trừ nội dòng đang dùng: %d." % so_mien_tru)
    if not vi_pham and not loi_cong:
        print("  ĐẠT: không thấy cookie phiên kèm giá trị, cờ bảo mật bị tắt, đường dẫn/số dòng")
        print("  của hệ đang chạy, hay mô tả khai thác gắn với vật thể cụ thể.")
        print("  NHẮC: cổng KHÔNG đọc ảnh chụp màn hình. Một ảnh terminal lộ nhiều hơn tất cả.")
        return
    if vi_pham:
        print("  HỎNG: %d vị trí." % len(vi_pham))
        for duong_dan, so_dong, ma, chi_tiet in vi_pham:
            print("    %s:%d" % (duong_dan, so_dong))
            print("        [%s] %s" % (ma, chi_tiet))
        print("  Cách xử ĐÚNG: giữ lời thừa nhận, bỏ phần làm lại được. Ví dụ, thay một dòng")
        print("  chỉ rõ tệp và số dòng bằng: 'còn một vấn đề chưa vá ở lớp xác thực, đang xử lý'.")
        print("  Khi hệ đã vá xong thì viết đầy đủ — công bố sau khi vá là điều tử tế.")
    if loi_cong:
        print("  HỎNG (fail-closed): %d tệp không đọc được." % len(loi_cong))
        for tep, ghi_chu in loi_cong:
            print("    %-52s %s" % (tep, ghi_chu))


def tu_kiem():
    """Bài thử ngược: chứng minh cổng CẮN, và chứng minh luật 5 KHÔNG cắn văn xuôi bảo mật."""
    gia_tri_phien = "a1b2c3d4e5f6a7b8c9d0"           # chuỗi bịa, không phải phiên thật
    duong_dan_gia = "/application/controllers/" + "Ho_so.php"
    mau = {
        "cookie-phien-kem-gia-tri": "Set-Cookie: " + "PHPSESSID" + "=" + gia_tri_phien,
        "co-bao-mat-tat": "cookie đặt " + "Http" + "Only" + "=false khi phát hành",
        "duong-dan-php-noi-bo": "sửa tại " + duong_dan_gia,
        "so-dong-he-dang-chay": "kiểm tra ở " + "Ho_so" + ".php" + ":" + "412",
        "mo-ta-khai-thac": "có thể " + "chiếm quyền" + " qua " + duong_dan_gia,
        "mien-tru-khong-ly-do": "Set-Cookie: " + "ci_session" + "=" + gia_tri_phien
                                + "  # " + DAU_MIEN_TRU + " khong-lo-hong",
    }
    sach = [
        "# Lời thừa nhận tử tế — phải KHÔNG bị bắt (luật 5 cần yếu tố thứ hai):",
        "Hệ đang chạy còn một vấn đề ở lớp xác thực chưa vá xong, đội đang xử lý.",
        "Chúng tôi không công bố đường khai thác cho tới khi vá xong; đây là chính sách, không phải giấu giếm.",
        "Tài liệu có bàn về XSS, CSRF và SQL injection ở mức khái niệm, không kèm tệp hay số dòng.",
        "# Chỗ điền trong tài liệu — phải KHÔNG bị bắt:",
        "Set-Cookie: " + "PHPSESSID" + "=<GIA_TRI_PHIEN>",
        "# Miễn trừ CÓ lý do — phải KHÔNG bị bắt:",
        "Set-Cookie: " + "sessionid" + "=" + gia_tri_phien
        + "  # " + DAU_MIEN_TRU + " khong-lo-hong ly-do=chuỗi bịa trong bài thử ngược",
    ]
    hong = []
    with tempfile.TemporaryDirectory() as tam:
        for ma, noi_dung in mau.items():
            with open(os.path.join(tam, "cai_%s.txt" % ma.replace("-", "_")), "w", encoding="utf-8") as f:
                f.write(noi_dung + "\n")
        with open(os.path.join(tam, "sach.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(sach) + "\n")

        vi_pham, loi_cong, so_mien_tru = quet_kho(tam)
        da_bat = set(v[2] for v in vi_pham)
        for ma in mau:
            if ma not in da_bat:
                hong.append("KHÔNG bắt được mẫu '%s' — cổng thủng ở luật này." % ma)
        for v in vi_pham:
            if v[0] == "sach.md":
                hong.append("Bắt nhầm văn xuôi sạch %s:%d [%s] %s" % v)
        if so_mien_tru != 1:
            hong.append("Miễn trừ CÓ lý do phải đếm đúng 1, đếm được %d." % so_mien_tru)
        if loi_cong:
            hong.append("Lỗi cổng ngoài dự kiến: %s" % loi_cong)

    print("TỰ KIỂM khong-lo-hong: %d mẫu cài, %d dòng văn xuôi bảo mật làm đối chứng." % (len(mau), len(sach)))
    if hong:
        for d in hong:
            print("  HỎNG: %s" % d)
        return 1
    print("  ĐẠT: cổng cắn đủ 6 mẫu cài, và KHÔNG cắn lời thừa nhận 'còn một vấn đề chưa vá'")
    print("       hay đoạn bàn về XSS/CSRF/SQL injection ở mức khái niệm — đúng mục tiêu:")
    print("       chặn CÁCH KHAI THÁC, không chặn LỜI THỪA NHẬN.")
    return 0


def main():
    bo_phan_tich = argparse.ArgumentParser(description="Cổng 4/4: chặn công bố chi tiết lỗ hổng đang sống.")
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
