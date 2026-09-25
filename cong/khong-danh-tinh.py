#!/usr/bin/env python3
"""
CỔNG khong-danh-tinh — chặn danh tính cá nhân lọt vào kho CÔNG KHAI.

═══ VÌ SAO CÓ CỔNG NÀY ═══

Ngày 26/09/2026, bốn cổng `khong-bi-mat`, `khong-ha-tang`, `khong-du-lieu-cam`,
`khong-lo-hong` đều ĐẠT trên toàn kho. Một lượt soát tay ĐỘC LẬP chạy ngay sau
đó vẫn tìm thấy họ tên thật của chủ dự án trong một thẻ dữ liệu.

Không cổng nào sai — không cổng nào trong bốn cổng ấy có luật về TÊN NGƯỜI. Bài
học không phải "cổng vô dụng" mà là: một lượt soát độc lập vẫn cần, và thứ nó
tìm ra phải trở thành cổng, nếu không lần sau nó lọt.

═══ VÌ SAO DANH SÁCH KHÔNG NẰM TRONG TỆP NÀY ═══

Bản đầu của cổng này viết thẳng bốn danh tính thật vào phần tự kiểm làm mẫu thử.
Nó ĐẠT — vì cổng loại chính nó khỏi phạm vi quét — rồi được đẩy lên kho công
khai, mang theo đúng bốn thứ nó sinh ra để chặn.

Đó là một họ lỗi chung: **một bộ dò mang theo danh sách thứ nó dò thì chính nó
là chỗ rò**. Cách chữa không phải nhớ cẩn thận hơn, mà là tách hẳn: tệp này
phát hành CƠ CHẾ, còn DANH SÁCH nằm ở `cong/danh-tinh.local` — bị `.gitignore`
chặn, không bao giờ rời máy.

Không có tệp ấy thì cổng chạy với danh sách rỗng và NÓI THẲNG rằng nó đang
không chặn gì, chứ không im lặng ĐẠT.

═══ VÌ SAO KHÔNG DÒ TÊN NGƯỜI TỔNG QUÁT ═══

Tiếng Việt có tên người trùng tên doanh nghiệp rất nhiều — "Công ty TNHH Kim
Ngân Thuý", "Doanh nghiệp tư nhân Dũng Liêm" đều là tên hợp lệ trong bộ dữ liệu
này. Một bộ dò "họ tên người Việt" sẽ bắt oan hàng loạt, và một cổng bắt oan
hàng loạt là một cổng sẽ bị tắt.
"""
import re
import sys
import pathlib

TEP_DANH_SACH = pathlib.Path(__file__).resolve().parent / "danh-tinh.local"

MAU_TEP = """\
# Mỗi dòng: <biểu thức chính quy><TAB hoặc 2 dấu cách><mô tả ngắn>
# Dòng trống và dòng bắt đầu bằng # bị bỏ qua.
# Viết biểu thức chịu được thiếu dấu — người ta hay gõ tên không dấu.
# TỆP NÀY BỊ .gitignore CHẶN. Đừng bỏ chặn.
"""

MIEN_TRU = re.compile(r"ly-do=")
BO_QUA_THU_MUC = {".git", ".venv", "node_modules", "__pycache__"}
BO_QUA_DUOI = {".json", ".jsonl", ".png", ".jpg", ".webp", ".pdf", ".safetensors", ".bin"}


def doc_danh_sach(tep: pathlib.Path):
    """Đọc danh sách danh tính. Trả về [] khi không có tệp — nơi gọi phải nói rõ điều đó."""
    if not tep.exists():
        return []
    ra = []
    for dong in tep.read_text(encoding="utf-8").splitlines():
        dong = dong.strip()
        if not dong or dong.startswith("#"):
            continue
        phan = re.split(r"\t|  +", dong, maxsplit=1)
        mau = phan[0].strip()
        ten = phan[1].strip() if len(phan) > 1 else "danh tính đã khai"
        try:
            re.compile(mau)
        except re.error as loi:
            print(f"  BỎ QUA dòng sai cú pháp trong {tep.name}: {loi}")
            continue
        ra.append((mau, ten))
    return ra


def quet(goc: pathlib.Path, danh_sach):
    """Quét TOÀN BỘ kho, KHÔNG loại trừ tệp này — vì tệp này không còn chứa danh tính nào."""
    thay = []
    for p in sorted(goc.rglob("*")):
        if not p.is_file() or any(b in p.parts for b in BO_QUA_THU_MUC):
            continue
        if p.suffix in BO_QUA_DUOI:
            continue
        try:
            noi_dung = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for so, dong in enumerate(noi_dung.splitlines(), 1):
            if MIEN_TRU.search(dong):
                continue
            for mau, ten in danh_sach:
                if re.search(mau, dong):
                    thay.append((str(p.relative_to(goc)), so, ten))
    return thay


def tu_kiem() -> int:
    """
    Chứng minh cổng CẮN — bằng danh tính BỊA, không bao giờ bằng danh tính thật.

    Đây chính là chỗ bản trước sai: nó dùng danh tính thật làm mẫu thử, rồi tự
    loại mình khỏi phạm vi quét nên không bao giờ tự bắt được.
    """
    danh_sach = [
        (r"Nguy[eễ]n\s+V[aă]n\s+A", "tên bịa để thử"),
        (r"[A-Za-z0-9._%+-]+@vidu-cong-ty\.test", "email bịa để thử"),
    ]
    cai = [
        "Người chịu trách nhiệm: Nguyễn Văn A, KTS trưởng.",
        "Nguoi chiu trach nhiem: Nguyen Van A",
        "Liên hệ: lienhe@vidu-cong-ty.test",
    ]
    sach = [
        "Người chịu trách nhiệm chuyên môn: Kiến trúc sư trưởng tư vấn, BDSG.",
        "Công Ty TNHH Kim Ngân Thuý",
        "DOANH NGHIỆP TƯ NHÂN DŨNG LIÊM",
        "liên hệ qua kho mã công khai",
        "a@example.com",
        "Phạm vi áp dụng của giấy phép này",
        "Nguyễn Trãi là một con đường ở Hà Nội",
        "bỏ qua dòng này  ly-do=mẫu trong tài liệu · Nguyễn Văn A",
    ]

    def bat(d):
        if MIEN_TRU.search(d):
            return False
        return any(re.search(m, d) for m, _ in danh_sach)

    sot = [d for d in cai if not bat(d)]
    oan = [d for d in sach if bat(d)]
    print(f"TỰ KIỂM khong-danh-tinh: {len(cai)} mẫu cài (danh tính BỊA), "
          f"{len(sach)} dòng sạch làm đối chứng.")
    if sot or oan:
        for d in sot:
            print(f"  SÓT (không cắn): {d}")
        for d in oan:
            print(f"  CẮN OAN:         {d}")
        return 1
    print("  ĐẠT: cắn đủ mẫu cài (gồm bản thiếu dấu), KHÔNG cắn nhầm tên doanh nghiệp")
    print("       tiếng Việt, và tôn trọng miễn trừ `ly-do=`.")
    print("  ⚠ Tự kiểm này KHÔNG dùng danh tính thật — chúng ở cong/danh-tinh.local,")
    print("    tệp bị .gitignore chặn. Một bộ dò mang theo danh sách thứ nó dò thì")
    print("    chính nó là chỗ rò; bản trước của cổng này đã mắc đúng lỗi ấy.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()

    goc = pathlib.Path(__file__).resolve().parent.parent
    print(f"CỔNG khong-danh-tinh — gốc quét: {goc}")

    danh_sach = doc_danh_sach(TEP_DANH_SACH)
    if not danh_sach:
        print(f"  KHÔNG CHẶN GÌ: thiếu {TEP_DANH_SACH.name} hoặc tệp rỗng.")
        print("  Cổng này chỉ có tác dụng khi người vận hành khai danh tính cần chặn.")
        print("  Tạo tệp theo mẫu:")
        for d in MAU_TEP.strip().splitlines():
            print(f"    {d}")
        print("  Thoát KHÁC 0 — vì 'không có danh sách' không phải là 'đã kiểm'.")
        return 2

    thay = quet(goc, danh_sach)
    if thay:
        print(f"  HỎNG: {len(thay)} chỗ lộ danh tính cá nhân.")
        for f, so, ten in thay:
            print(f"    {f}:{so}  ({ten})")
        print("  Kho này là kho CÔNG KHAI: đăng lên là việc MỘT CHIỀU.")
        return 1

    print(f"  ĐẠT: không thấy danh tính nào trong {len(danh_sach)} danh tính đã khai.")
    print("  NHẮC: đây là DANH SÁCH ĐEN HẸP do người vận hành khai. Nó không tìm được")
    print("        danh tính chưa ai khai, nên ĐẠT nghĩa là 'không thấy thứ đã khai'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
