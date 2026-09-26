#!/usr/bin/env python3
"""
GOM TOAN BO NGU LIEU CUA BDSG THANH MOT KHO HUAN LUYEN.

═══ VI SAO KHONG GOM BANG "LAY HET CAC COT TEXT" ═══

Do ngay 26/09/2026 tren CSDL that, ba nguon trong RAT to:

    core.entity_relationships.note     57.831 dong · 2,75 MB
    economy.indicator_values.note      30.082 dong · 1,13 MB
    geo.site_score_components.note     12.750 dong · 1,40 MB
                                       ─────────────────────
                                       tong  5,28 MB

Dem so gia tri KHAC NHAU: 971 · 2 · 15. Tuc 5,28 MB ay chua khoang **0,05 MB**
van ban that; phan con lai la MOT chuoi xuat xu ETL lap di lap lai. Nap chung
vao la day mo hinh doc thuoc mot cau 57.831 lan — va no se hoc rat nhanh, vi do
la thu de hoc nhat trong ca kho.

Cai bay o day khong phai "quen loc trung lap". Cai bay la **do bang dung luong
thay vi do bang luong thong tin**. Mot bang 2,75 MB trong bang gia tri gap 55
lan mot bang 0,05 MB, va bang thong tin thi bang nhau.

Nen tep nay co mot cong: **nguon nao co ti le gia tri khac nhau duoi NGUONG thi
bi TU CHOI**, va chuong trinh noi ro ly do thay vi lang le bo qua.

═══ VI SAO PHAI DIEN DU KIEU THANH VAN XUOI ═══

3.321 xa va 34 tinh nam trong CSDL duoi dang cot: dien tich, dan so, mat do,
sap nhap tu dau, can cu phap ly. Do la du kien, khong phai cau. Mot mo hinh ngon
ngu khong hoc duoc gi tu mot hang bang.

Nen chung phai duoc DIEN thanh cau. Va cau dien ra phai DA DANG — neu moi xa
deu mot khuon "X co dien tich Y, dan so Z", mo hinh hoc dung mot khuon ay va lap
lai no mai. Bo dien o duoi doi khuon theo ma xa, nen 3.321 xa cho ra nhieu dang
cau khac nhau tu cung mot bo du kien.

═══ BA LOP GIAY PHEP, KHONG PHAI HAI ═══

    mo       — BDSG tu viet, phat hanh cong khai duoc
    noi-bo   — BDSG so huu nhung khong phat hanh (du lieu khach, cau hinh thuong mai)
    cam      — cua nguoi khac (giay phep ben thu ba, noi dung nguoi dung dang)

HUAN LUYEN va PHAT HANH la hai viec khac nhau. Mot mo hinh noi bo huan luyen
tren lop `noi-bo` thi duoc; mot bo du lieu cong khai thi khong. Tep nay gan nhan
tung ban ghi de quyet dinh ay lam duoc SAU, chu khong phai tron lan roi khong
con go ra duoc.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────
# Cong chan
# ──────────────────────────────────────────────────────────────────────────

# Ti le gia tri khac nhau toi thieu. Duoi nguong nay, nguon bi TU CHOI.
# 0,30 chon tu so da do: ba nguon rac co ti le 0,017 / 0,00007 / 0,001; ba nguon
# that co 1,00 / 0,996 / 0,999. Khoang trong giua hai nhom rat rong, nen nguong
# dat o dau trong khoang (0,01 ; 0,98) cung cho cung ket qua. Chon 0,30 de con
# cho cho mot nguon that su co nhieu ban ghi giong nhau ma van dung.
NGUONG_KHAC_NHAU = 0.30

# Do dai toi thieu cua mot doan. Duoi muc nay thuong la nhan, ma, hoac mot cum
# tu — khong day duoc mo hinh cach dung cau.
DAI_TOI_THIEU = 60

# Rac cao web — da do 25/09/2026: 110 doan dinh tren 11.733.
RAC = [
    re.compile(r"\{\s*(?:color|font-size|background|margin|padding|fill)\s*:"),
    re.compile(r"(?:handlePayload|bootloader|rsrcMap|window\.|function\s*\()"),
    re.compile(r"(?:Toggle navigation|Home Home|Read More|Click here)"),
    re.compile(r"</?(?:div|span|script|style)\b"),
]

# Du lieu ca nhan. Ten doanh nghiep va ma so thue KHONG nam o day: ma so thue la
# thong tin dang ky cong khai o Viet Nam, con ten doanh nghiep la chinh thu mo
# hinh phai hoc.
CA_NHAN = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "dien-thoai": re.compile(r"(?<!\d)(?:\+?84|0)(?:3[2-9]|5[2689]|7[06-9]|8[1-9]|9\d)\d{7}(?!\d)"),
    "the-can-cuoc": re.compile(r"(?<!\d)\d{12}(?!\d)"),
}


class NguonBiTuChoi(Exception):
    """Nem khi mot nguon khong qua cong. KHONG bat roi bo qua — do la ca diem."""


# ──────────────────────────────────────────────────────────────────────────
# Khai bao nguon — moi dong la mot quyet dinh, kem ly do
# ──────────────────────────────────────────────────────────────────────────

# (khoa, cau lenh, lop giay phep, ghi chu)
NGUON_SQL: List[Tuple[str, str, str, str]] = [
    (
        "ho-so-dn",
        "SELECT summary FROM business.company_profiles WHERE summary IS NOT NULL",
        "mo",
        "Ho so doanh nghiep do BDSG viet. CHU Y: cung mot van ban nay con nam o "
        "core.organizations.description va business.companies.description — da do "
        "26/09/2026: 6.584 gia tri khac nhau o ca ba, giao nhau dung 6.584. Lay MOT cho.",
    ),
    (
        "nang-luc-dn",
        "SELECT note FROM business.company_capabilities WHERE note IS NOT NULL",
        "mo",
        "JSON {mo_ta, tu_khoa}. Chi lay truong mo_ta — xem boc_json().",
    ),
    (
        "du-an",
        "SELECT description FROM projects.projects WHERE description IS NOT NULL",
        "mo",
        "Mo ta du an.",
    ),
    (
        "san-giao-dich",
        "SELECT description FROM innovation.exchange_listings WHERE description IS NOT NULL",
        "mo",
        "Tin dang tren san trao doi.",
    ),
    (
        "ocop",
        "SELECT mo_ta FROM ocop.san_pham WHERE mo_ta IS NOT NULL",
        "cam",
        "Van quang cao cua nguoi ban, url tro ra ngoai. Khong phai cua BDSG. "
        "Chi vao kho NOI BO, khong bao gio vao ban phat hanh.",
    ),
]

# Ba nguon duoi day CO Y bi bo, va ly do phai o lai trong ma — neu khong, sau
# nay se co nguoi thay chung "to" roi them vao.
NGUON_DA_LOAI = {
    "core.entity_relationships.note": "57.831 dong nhung 971 gia tri khac nhau (1,7%) — chuoi xuat xu ETL",
    "economy.indicator_values.note": "30.082 dong nhung 2 gia tri khac nhau — chuoi xuat xu ETL",
    "geo.site_score_components.note": "12.750 dong nhung 15 gia tri khac nhau — chuoi xuat xu ETL",
    "business.capabilities.description": "11.927 dong nhung 58 gia tri khac nhau — chuoi xuat xu ETL",
    "map5d.khach_dn.*": "1.079.991 ban ghi TEN doanh nghiep, khong phai van xuoi; va xuat xu la CRM",
    "*.geojson_don_gian": "toa do, khong phai ngon ngu",
}


# ──────────────────────────────────────────────────────────────────────────
# Dien du kien thanh van xuoi
# ──────────────────────────────────────────────────────────────────────────

def _so(x) -> Optional[str]:
    """Dinh dang so kieu Viet Nam. Tra None khi khong co so — de cau bo han ve ay."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if f <= 0:
        return None
    return f"{f:,.0f}".replace(",", ".") if f >= 1000 else f"{f:,.1f}".replace(".", ",")


def dien_tinh(h: Dict, chi_so: int) -> Optional[str]:
    """
    Dien mot tinh thanh van xuoi.

    Bon khuon cau, doi theo chi_so. Mot khuon duy nhat cho 34 tinh se day mo hinh
    hoc dung mot cach noi ve dia phuong.
    """
    ten = (h.get("ten") or "").strip()
    if not ten:
        return None
    dt, ds, md, sx = _so(h.get("dien_tich_km2")), _so(h.get("dan_so_quy_doi")), _so(h.get("mat_do_quy_doi")), h.get("so_xa")
    vung, cc, sn = h.get("vung"), h.get("can_cu_phap_ly"), h.get("sap_nhap_tu")
    mo_ta = (h.get("mo_ta") or "").strip()

    y: List[str] = []
    k = chi_so % 4
    if k == 0:
        y.append(f"{ten} là một tỉnh, thành phố trực thuộc trung ương của Việt Nam.")
        if dt: y.append(f"Diện tích {dt} km².")
        if ds: y.append(f"Dân số quy đổi khoảng {ds} người.")
        if md: y.append(f"Mật độ khoảng {md} người trên một ki-lô-mét vuông.")
    elif k == 1:
        d = [p for p in (f"diện tích {dt} km²" if dt else None,
                         f"dân số khoảng {ds} người" if ds else None) if p]
        y.append(f"{ten} có " + " và ".join(d) + "." if d else f"{ten} là một đơn vị hành chính cấp tỉnh.")
        if sx: y.append(f"Tỉnh gồm {sx} đơn vị hành chính cấp xã.")
    elif k == 2:
        y.append(f"Về {ten}: đây là một trong 34 tỉnh, thành phố của Việt Nam"
                 + (f", thuộc vùng {vung}." if vung else "."))
        if md: y.append(f"Mật độ dân số khoảng {md} người/km².")
        if dt: y.append(f"Tổng diện tích {dt} km².")
    else:
        y.append(f"Hỏi về {ten}. Đây là một tỉnh, thành phố của Việt Nam"
                 + (f" ở vùng {vung}" if vung else "") + ".")
        if sx and ds: y.append(f"Địa phương này có {sx} xã, phường với khoảng {ds} người.")

    if sn: y.append(f"{ten} được hình thành trên cơ sở sáp nhập {sn}.")
    if cc: y.append(f"Căn cứ pháp lý: {cc}.")
    if mo_ta and len(mo_ta) > 30: y.append(mo_ta)

    van = " ".join(y)
    return van if len(van) >= DAI_TOI_THIEU else None


def dien_xa(h: Dict, ten_tinh: Optional[str], chi_so: int) -> Optional[str]:
    """Dien mot xa, phuong thanh van xuoi. Ba khuon cau, doi theo chi_so."""
    ten = (h.get("ten") or "").strip()
    if not ten:
        return None
    loai = (h.get("loai") or "").strip()
    dt, ds, md = _so(h.get("dien_tich_km2")), _so(h.get("dan_so_quy_doi")), _so(h.get("mat_do_quy_doi"))
    cu, ubnd, cc = h.get("quan_huyen_cu"), h.get("ubnd"), h.get("can_cu_phap_ly")
    o_tinh = f" thuộc {ten_tinh}" if ten_tinh else ""

    y: List[str] = []
    k = chi_so % 3
    if k == 0:
        y.append(f"{ten} là một {loai or 'đơn vị hành chính cấp xã'}{o_tinh}.")
        if dt: y.append(f"Diện tích {dt} km².")
        if ds: y.append(f"Dân số khoảng {ds} người.")
    elif k == 1:
        d = [p for p in (f"diện tích {dt} km²" if dt else None,
                         f"khoảng {ds} người" if ds else None) if p]
        y.append(f"{ten}{o_tinh} có " + " và ".join(d) + "." if d
                 else f"{ten} là một {loai or 'xã, phường'}{o_tinh}.")
        if md: y.append(f"Mật độ khoảng {md} người/km².")
    else:
        y.append(f"Về {ten}: đây là {loai or 'một xã, phường'}{o_tinh}.")
        if ds and dt: y.append(f"Địa bàn rộng {dt} km² với khoảng {ds} người sinh sống.")

    if cu: y.append(f"Trước sắp xếp, địa bàn này thuộc {cu}.")
    if ubnd: y.append(f"Trụ sở Uỷ ban nhân dân đặt tại {ubnd}.")
    if cc: y.append(f"Căn cứ pháp lý: {cc}.")

    van = " ".join(y)
    return van if len(van) >= DAI_TOI_THIEU else None


# ──────────────────────────────────────────────────────────────────────────
# Boc van xuoi khoi ma nguon giao dien
# ──────────────────────────────────────────────────────────────────────────

DAU_VN = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
    re.IGNORECASE,
)
CHUOI_MA = re.compile(
    r'"((?:[^"\\]|\\.){%d,})"' % DAI_TOI_THIEU
    + r"|'((?:[^'\\]|\\.){%d,})'" % DAI_TOI_THIEU
    + r"|`((?:[^`\\]|\\.){%d,})`" % DAI_TOI_THIEU
)


def boc_van_tu_ma(goc: str) -> Iterable[Tuple[str, str]]:
    """
    Lay cac chuoi tieng Viet dai trong ma nguon giao dien.

    Day la cho kien thuc TU VAN, TRIEN KHAI, VAN HANH cua BDSG that su nam — do
    26/09/2026: 2,54 MB van xuoi tieng Viet trong ma giao dien, 2,0 MB trong
    rieng modules/bdsg-os. CSDL Django chi co 0,61 MB.

    Loc bang MAT DO DAU: mot chuoi tieng Viet that co nhieu nguyen am co dau.
    Nguong 5 dau loai duoc ten lop CSS, duong dan, va chuoi tieng Anh dai.
    """
    for thu_muc, _, ten_tep in os.walk(goc):
        if any(b in thu_muc for b in (".git", "node_modules", "dist", "build")):
            continue
        for t in ten_tep:
            if not t.endswith((".js", ".jsx", ".ts", ".tsx")) or ".test." in t:
                continue
            duong = os.path.join(thu_muc, t)
            try:
                noi_dung = open(duong, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for m in CHUOI_MA.finditer(noi_dung):
                s = m.group(1) or m.group(2) or m.group(3) or ""
                if len(DAU_VN.findall(s)) < 5:
                    continue
                s = s.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
                s = re.sub(r"\s+", " ", s).strip()
                if len(s) >= DAI_TOI_THIEU:
                    yield s, os.path.relpath(duong, goc)


# ──────────────────────────────────────────────────────────────────────────
# Lam sach va cong kiem
# ──────────────────────────────────────────────────────────────────────────

def boc_json(van: str) -> str:
    """Neu chuoi la JSON co truong mo_ta thi lay truong ay; khong thi tra nguyen."""
    v = van.strip()
    if not v.startswith("{"):
        return van
    try:
        d = json.loads(v)
    except json.JSONDecodeError:
        return van
    if isinstance(d, dict):
        for k in ("mo_ta", "mota", "description", "noi_dung"):
            if isinstance(d.get(k), str) and len(d[k]) >= DAI_TOI_THIEU:
                return d[k]
    return van


def la_rac(van: str) -> bool:
    return any(p.search(van) for p in RAC)


def chuan_hoa(van: str) -> str:
    van = unicodedata.normalize("NFC", van)
    return re.sub(r"[ \t]+", " ", van.replace("\r", " ").replace("\n", " ")).strip()


def kiem_nguon(ten: str, cac_van: List[str]) -> Tuple[List[str], Dict]:
    """
    Cong: tu choi nguon co ti le gia tri khac nhau duoi nguong.

    Nem `NguonBiTuChoi` chu khong tra danh sach rong — mot nguon bi loai am tham
    se lam so tong nho di ma khong ai biet vi sao.
    """
    if not cac_van:
        return [], {"so_dong": 0, "khac_nhau": 0, "ti_le": 0.0}
    bam = {hashlib.md5(v.encode("utf-8")).hexdigest() for v in cac_van}
    ti_le = len(bam) / len(cac_van)
    so_do = {"so_dong": len(cac_van), "khac_nhau": len(bam), "ti_le": round(ti_le, 4)}
    if ti_le < NGUONG_KHAC_NHAU:
        raise NguonBiTuChoi(
            f"nguon {ten!r}: {len(cac_van):,} dong nhung chi {len(bam):,} gia tri khac nhau "
            f"({ti_le:.1%} < nguong {NGUONG_KHAC_NHAU:.0%}). Day la dau hieu chuoi xuat xu "
            f"ETL lap lai, khong phai van xuoi. Neu that su muon nap, phai ha nguong TUONG MINH "
            f"va ghi ly do — dung sua o day."
        )
    return cac_van, so_do


def quet_ca_nhan(cac_van: Iterable[str]) -> Dict[str, int]:
    d = {k: 0 for k in CA_NHAN}
    for v in cac_van:
        for k, p in CA_NHAN.items():
            d[k] += len(p.findall(v))
    return d


# ──────────────────────────────────────────────────────────────────────────
# Chay
# ──────────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Gom toan bo ngu lieu BDSG thanh mot kho huan luyen.")
    p.add_argument("--sql-ra", help="thu muc chua ket xuat SQL dang <khoa>.txt (mot ban ghi mot dong)")
    p.add_argument("--tinh-json", help="tep JSON mang cac hang map5d.tinh")
    p.add_argument("--xa-json", help="tep JSON mang cac hang map5d.xa")
    p.add_argument("--ma-giao-dien", help="thu muc goc ma nguon giao dien")
    p.add_argument("--ra", required=True, help="tep JSONL ket qua")
    p.add_argument("--gom-cam", action="store_true",
                   help="gom ca lop giay phep 'cam' (chi dung cho kho NOI BO, khong phat hanh)")
    t = p.parse_args()

    ban_ghi: List[Dict] = []
    da_thay = set()
    bao_cao: List[Tuple[str, str, int, int, str]] = []
    bi_tu_choi: List[str] = []

    def them(van: str, nguon: str, lop: str, xuat_xu: str) -> bool:
        van = chuan_hoa(boc_json(van))
        if len(van) < DAI_TOI_THIEU or la_rac(van):
            return False
        h = hashlib.md5(van.encode("utf-8")).hexdigest()
        if h in da_thay:
            return False
        da_thay.add(h)
        ban_ghi.append({"text": van, "nguon": nguon, "lop": lop, "xuat_xu": xuat_xu, "ngon_ngu": "vi"})
        return True

    # ── 1. Nguon tu CSDL ──
    if t.sql_ra:
        for khoa, _cau, lop, _ghi in NGUON_SQL:
            if lop == "cam" and not t.gom_cam:
                bao_cao.append((khoa, lop, 0, 0, "bo qua (lop 'cam', khong co --gom-cam)"))
                continue
            duong = os.path.join(t.sql_ra, f"{khoa}.txt")
            if not os.path.exists(duong):
                bao_cao.append((khoa, lop, 0, 0, "khong co tep ket xuat"))
                continue
            tho = [l.rstrip("\n") for l in open(duong, encoding="utf-8") if l.strip()]
            sach = [chuan_hoa(boc_json(v)) for v in tho]
            sach = [v for v in sach if len(v) >= DAI_TOI_THIEU]
            try:
                sach, so_do = kiem_nguon(khoa, sach)
            except NguonBiTuChoi as loi:
                bi_tu_choi.append(str(loi))
                bao_cao.append((khoa, lop, len(tho), 0, "TU CHOI — xem canh bao"))
                continue
            n = sum(1 for v in sach if them(v, khoa, lop, f"CSDL/{khoa}"))
            bao_cao.append((khoa, lop, len(tho), n, f"{so_do['ti_le']:.1%} khac nhau"))

    # ── 2. Dien 34 tinh ──
    ten_theo_ma: Dict[str, str] = {}
    if t.tinh_json and os.path.exists(t.tinh_json):
        hang = json.load(open(t.tinh_json, encoding="utf-8"))
        n = 0
        for i, h in enumerate(hang):
            if h.get("ma_tinh") and h.get("ten"):
                ten_theo_ma[str(h["ma_tinh"])] = h["ten"]
            v = dien_tinh(h, i)
            if v and them(v, "hanh-chinh-tinh", "mo", "map5d.tinh (diễn từ dữ kiện)"):
                n += 1
        bao_cao.append(("hanh-chinh-tinh", "mo", len(hang), n, "diễn từ dữ kiện"))

    # ── 3. Dien 3.321 xa ──
    if t.xa_json and os.path.exists(t.xa_json):
        hang = json.load(open(t.xa_json, encoding="utf-8"))
        n = 0
        for i, h in enumerate(hang):
            v = dien_xa(h, ten_theo_ma.get(str(h.get("ma_tinh"))), i)
            if v and them(v, "hanh-chinh-xa", "mo", "map5d.xa (diễn từ dữ kiện)"):
                n += 1
        bao_cao.append(("hanh-chinh-xa", "mo", len(hang), n, "diễn từ dữ kiện"))

    # ── 4. Van xuoi trong ma giao dien ──
    if t.ma_giao_dien and os.path.isdir(t.ma_giao_dien):
        tho = list(boc_van_tu_ma(t.ma_giao_dien))
        n = sum(1 for v, tep in tho if them(v, "tri-thuc-nghiep-vu", "mo", f"giao-dien/{tep}"))
        bao_cao.append(("tri-thuc-nghiep-vu", "mo", len(tho), n, "tư vấn · triển khai · vận hành"))

    # ── 5. Ghi ra ──
    os.makedirs(os.path.dirname(os.path.abspath(t.ra)) or ".", exist_ok=True)
    with open(t.ra, "w", encoding="utf-8") as f:
        for b in ban_ghi:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    # ── 6. Bao cao ──
    ky_tu = sum(len(b["text"]) for b in ban_ghi)
    print("=" * 78)
    print("  GOM NGU LIEU BDSG")
    print("=" * 78)
    print(f"  {'nguồn':22s} {'lớp':8s} {'thô':>9s} {'nhận':>9s}  ghi chú")
    print("  " + "-" * 74)
    for ten, lop, tho_n, nhan, ghi in bao_cao:
        print(f"  {ten:22s} {lop:8s} {tho_n:9,} {nhan:9,}  {ghi}")
    print("  " + "-" * 74)
    print(f"  {'TỔNG':22s} {'':8s} {'':>9s} {len(ban_ghi):9,}  "
          f"{ky_tu:,} ký tự · {ky_tu/1048576:.2f} MB")

    if bi_tu_choi:
        print()
        print("  ── NGUỒN BỊ CỔNG TỪ CHỐI ──")
        for c in bi_tu_choi:
            print(f"    ✗ {c}")

    cn = quet_ca_nhan(b["text"] for b in ban_ghi)
    print()
    print("  ── QUÉT DỮ LIỆU CÁ NHÂN ──")
    for k, v in cn.items():
        print(f"    {'⚠' if v else '✓'} {k:14s} {v}")

    theo_lop: Dict[str, int] = {}
    for b in ban_ghi:
        theo_lop[b["lop"]] = theo_lop.get(b["lop"], 0) + len(b["text"])
    print()
    print("  ── THEO LỚP GIẤY PHÉP ──")
    for k, v in sorted(theo_lop.items(), key=lambda x: -x[1]):
        print(f"    {k:10s} {v/1048576:6.2f} MB")

    print()
    print(f"  Đã ghi: {t.ra}")
    print()
    print("  Ý nghĩa: đây là số ký tự SAU khi khử trùng lặp, lọc rác và chặn nguồn")
    print("  có tỉ lệ giá trị khác nhau dưới ngưỡng. Nó KHÔNG nói gì về chất lượng")
    print("  mô hình — chất lượng phải đo bằng bộ đánh giá.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
