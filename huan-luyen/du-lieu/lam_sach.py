#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loc rac cao web ra khoi ngu lieu JSONL.

=============================================================================
DUA TREN PHEP DO NAO
=============================================================================
Do ngay 25/09/2026 tren CSDL bdsg_chat, bang doan_tri_thuc, phan phat hanh duoc
(11.733 doan / 7.509.969 ky tu / 7,16 MB sau khi loai hai nguon may sinh):

    110 doan con dinh rac cao web (menu web, CSS, JS, URL ngoai)
    0,17 MB tren 7,16 MB  =  2,3% theo dung luong
    Tap trung o nguon ho-so-niem-yet: 110/5.192 doan = 2,1% cua nguon do

Ket luan rut ra luc do, va la ly do tep nay ton tai: 2,3% thi LOC DUOC. Khong
phai ly do de bo ca nguon ho-so-niem-yet — do la nguon lon nhat (4,20 MB).

=============================================================================
TRIET LY LOC
=============================================================================
Hai buoc tach bach, vi chung tra loi hai cau hoi khac nhau:

  Buoc 1 — GO: xoa dung cac doan van ban la rac (the HTML, khoi CSS, dong JS,
           URL ngoai, dong menu). Phan con lai duoc giu.
  Buoc 2 — BO: neu PHAN CON LAI sau khi go khong con la van ban tu te (rong,
           qua ngan, hoac chi la manh vun dau cau) thi bo ca doan.

Vi sao khong bo thang ca doan ngay tu dau: 110 doan la 2,1% cua nguon lon nhat.
Trong so do phan nhieu chi dinh mot dong menu o dau hoac mot dong chan trang o
cuoi — noi dung that ben trong van dung. Bo ca doan la vut du lieu that di.

Vi sao khong chi go ma khong bao gio bo: mot doan 200 ky tu ma go xong con 30 ky
tu thi cai con lai la manh vun, khong phai cau.

=============================================================================
DIEU QUAN TRONG NHAT VE TEP NAY
=============================================================================
Bo loc nao cung an nham. Nen script bat buoc ghi bao cao, va co --xem-thu de
IN RA nhung doan no dinh bo, cho nguoi doc kiem lai bang mat truoc khi tin.
Mot bo loc chay im lang la mot bo loc khong ai biet no dang lam gi.

Chuyen nay da xay ra ngay trong lan chay thu dau tien (25/09/2026). Ban dau
buoc 2 bo doan khi TI LE DA GO vuot 30%. Chay --xem-thu 5 tren sau doan mau thi
thay no bo mat doan nay:

    GOC        : "Trang chu | Gioi thieu | San pham | ... | Dang nhap
                  Bao cao tai chinh hop nhat quy III nam 2026 ... ty le 8%.
                  (c) 2026 Ban quyen thuoc ve cong ty. Dieu khoan | Cookie"
    SAU KHI GO : "Bao cao tai chinh hop nhat quy III nam 2026 ... ty le 8%."
    -> bi bo vi "ti le rac 41%"

Phan con lai la mot cau hoan chinh, dung chu de, dung thu can. Bo no la sai.
Loi nam o chinh tieu chi: "da go bao nhieu" do CONG VIEC CUA BO LOC, khong do
CHAT LUONG cai con lai. Go duoc nhieu rac la bo loc chay TOT, khong phai ly do
de vut phan con lai.

Nen tieu chi da doi: buoc 2 chi nhin PHAN CON LAI.
  - con lai rong                     -> bo
  - con lai ngan hon --toi-thieu-ky-tu  -> bo
  - con lai khong ra van (ti le chu cai qua thap, nhu "; } #333 ]") -> bo
Ti le da go van duoc TINH va GHI VAO BAO CAO, nhung tu no khong bo doan nao.
Ai muon hanh vi cu thi bat --nguong-rac (mac dinh 0 = tat).

Chay:
    # do truoc, chua ghi gi (nen lam lan dau tien voi mot nguon moi):
    python3 lam_sach.py --vao ../../bo-du-lieu/doan_tri_thuc.jsonl --chi-do --xem-thu 10

    # loc that:
    python3 lam_sach.py --vao ../../bo-du-lieu/doan_tri_thuc.jsonl \
                        --ra  ../../bo-du-lieu/doan_tri_thuc.sach.jsonl

Chi can python >= 3.8. Khong can thu vien ngoai.
"""

import argparse
import datetime
import html
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# CAC MAU RAC — dung dung nhung loai da do duoc, khong them mau "cho chac".
# Moi mau co ten tieng Viet vi ten do se hien trong bao cao.
# ---------------------------------------------------------------------------

# The HTML: <div class="...">, </p>, <br/>, <!-- ... -->
MAU_BINH_LUAN_HTML = re.compile(r"<!--.*?-->", re.S)
MAU_THE_HTML = re.compile(r"</?[A-Za-z][A-Za-z0-9]{0,20}(?:\s[^<>]{0,300})?/?>")

# Khoi CSS: chi tinh la CSS khi ben trong ngoac nhon co it nhat mot khai bao
# dang "thuoc-tinh: gia-tri;". Khong co dieu kien nay thi mot cau tieng Viet
# co ngoac nhon cung bi coi la CSS.
MAU_KHOI_CSS = re.compile(
    r"[^{}\n]{0,120}\{[^{}]{0,600}?[a-zA-Z-]{2,30}\s*:\s*[^;{}]{1,120};[^{}]{0,600}?\}", re.S)
MAU_AT_RULE = re.compile(r"@(?:media|import|font-face|keyframes|charset)[^{;]{0,200}(?:\{[^{}]{0,800}\}|;)", re.S)

# Khai bao CSS le, khong co ngoac nhon: "font-size:14px;" "margin:0 auto;"
THUOC_TINH_CSS = (
    "font|margin|padding|color|background|border|width|height|display|position|"
    "z-index|line-height|text-align|float|overflow|opacity|box-shadow|text-decoration|"
    "flex|grid|cursor|visibility|vertical-align|white-space|letter-spacing|transform|transition"
)
MAU_KHAI_BAO_CSS = re.compile(
    r"\b(?:" + THUOC_TINH_CSS + r")[a-z-]{0,20}\s*:\s*[^;{}\n]{1,90};")

# Ma JS
MAU_JS = re.compile(
    r"(?:"
    r"\bfunction\s*\**\s*[A-Za-z_$]{0,40}\s*\([^)]{0,200}\)\s*\{"
    r"|\bdocument\.(?:getElementById|querySelector|createElement|addEventListener|write|cookie)\b"
    r"|\bwindow\.(?:location|onload|open|addEventListener|dataLayer)\b"
    r"|\baddEventListener\s*\("
    r"|\bconsole\.(?:log|error|warn)\s*\("
    r"|\b(?:var|let|const)\s+[A-Za-z_$][\w$]{0,40}\s*=\s*(?:function|\(|\[|\{)"
    r"|\bjQuery\b|\$\(document\)|\$\(['\"]"
    r"|\bnew\s+XMLHttpRequest\b|\bfetch\s*\(\s*['\"]"
    r")[^\n]{0,200}")

# URL. Tach hai loai: URL ngoai va URL cua chinh BDSG.
MAU_URL = re.compile(r"https?://[^\s<>\"'\)\]]{2,300}")
MAU_DATA_URI = re.compile(r"data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]{20,}", re.I)
MAU_TEP_TINH = re.compile(r"\b[\w./-]{1,120}\.(?:css|js|woff2?|ttf|eot|svg|ico|webp)\b(?:\?[\w=&.-]{0,60})?", re.I)

# Tu ngu dieu huong web. Danh sach nay la nguon de sai nhat trong ca tep, vi
# "san pham", "dich vu", "tin tuc" deu la tu tieng Viet binh thuong trong van
# ban kinh doanh. Nen dieu kien kich hoat duoc dat chat: xem ham la_dong_menu.
TU_MENU = [
    "trang chủ", "giới thiệu", "liên hệ", "đăng nhập", "đăng ký", "đăng xuất",
    "tìm kiếm", "xem thêm", "xem chi tiết", "đọc tiếp", "chia sẻ", "bình luận",
    "danh mục", "giỏ hàng", "thêm vào giỏ", "thanh toán", "tài khoản của tôi",
    "điều khoản sử dụng", "chính sách bảo mật", "bản quyền thuộc về",
    "all rights reserved", "copyright", "cookie", "chấp nhận cookie",
    "quay lại", "trang trước", "trang sau", "về đầu trang", "menu",
    "hotline", "địa chỉ:", "email:", "fanpage", "theo dõi chúng tôi",
]
DAU_PHAN_MUC = re.compile(r"[|•·›»]")


def ti_le_chu_cai(s):
    """Ti le ky tu la chu cai / chu so / khoang trang tren tong so ky tu.

    Dung de phan biet "cau van con lai sau khi go" voi "manh vun con lai sau khi
    go" (kieu "; } #333 ]"). Khong dung de phan biet ngon ngu.
    """
    if not s:
        return 0.0
    tot = 0
    for c in s:
        if c.isalpha() or c.isdigit() or c.isspace():
            tot += 1
        elif c in ",.;:%()-/–’":   # dau cau binh thuong cua van xuoi
            tot += 1
    return tot / float(len(s))


def la_dong_menu(dong, nguong_tu=3):
    """Mot dong co phai dong dieu huong web khong.

    Dieu kien duoc dat CHAT co chu y, vi nham o day la an mat cau van that:
      (a) co tu 3 dau phan muc tro len  ( | • · › » )  — dac trung thanh menu; hoac
      (b) co tu `nguong_tu` cum dieu huong tro len VA dong ngan duoi 200 ky tu
          VA khong ket thuc bang dau cham cau cua mot cau hoan chinh.
    Mot cau van that hiem khi thoa ca ba ve cua (b).
    """
    d = dong.strip()
    if not d:
        return False, 0
    thap = d.lower()
    so_cum = sum(1 for t in TU_MENU if t in thap)
    if len(DAU_PHAN_MUC.findall(d)) >= 3:
        return True, so_cum
    if so_cum >= nguong_tu and len(d) < 200 and not d.rstrip().endswith((".", "!", "?", "…")):
        return True, so_cum
    return False, so_cum


def go_rac(van_ban, mien_nha, bo_moi_url=False):
    """Go cac doan rac ra khoi van ban.

    Tra ve (van_ban_sach, so_ky_tu_bi_go_theo_luat, so_lan_dinh_theo_luat).
    """
    goc_dai = len(van_ban)
    go = {}
    dinh = {}

    def ap(ten, mau, s, thay=" "):
        n_lan = 0
        n_ky_tu = 0
        moi = []
        vi_tri = 0
        for m in mau.finditer(s):
            n_lan += 1
            n_ky_tu += m.end() - m.start()
            moi.append(s[vi_tri:m.start()])
            moi.append(thay)
            vi_tri = m.end()
        moi.append(s[vi_tri:])
        if n_lan:
            go[ten] = go.get(ten, 0) + n_ky_tu
            dinh[ten] = dinh.get(ten, 0) + n_lan
        return "".join(moi)

    s = van_ban
    s = ap("binh_luan_html", MAU_BINH_LUAN_HTML, s)
    s = ap("at_rule_css", MAU_AT_RULE, s)
    s = ap("khoi_css", MAU_KHOI_CSS, s)
    s = ap("khai_bao_css", MAU_KHAI_BAO_CSS, s)
    s = ap("ma_js", MAU_JS, s)
    s = ap("data_uri", MAU_DATA_URI, s)
    s = ap("the_html", MAU_THE_HTML, s)
    s = ap("tep_tinh", MAU_TEP_TINH, s)

    # URL: phan biet noi va ngoai. Mac dinh chi go URL ngoai, dung nhu phep do
    # 25/09/2026 mo ta ("URL ngoai"). --bo-moi-url de go ca URL nha.
    def _url(m):
        u = m.group(0)
        if not bo_moi_url and any(mn in u for mn in mien_nha):
            return u
        return " "
    n_lan = n_ky_tu = 0
    moi = []
    vi_tri = 0
    for m in MAU_URL.finditer(s):
        thay = _url(m)
        if thay != m.group(0):
            n_lan += 1
            n_ky_tu += m.end() - m.start()
        moi.append(s[vi_tri:m.start()])
        moi.append(thay)
        vi_tri = m.end()
    moi.append(s[vi_tri:])
    s = "".join(moi)
    if n_lan:
        go["url_ngoai"] = n_ky_tu
        dinh["url_ngoai"] = n_lan

    # Dong menu: xu ly theo TUNG DONG, khong theo ca doan.
    giu = []
    n_menu = n_menu_ky_tu = 0
    for dong in s.split("\n"):
        la_menu, _ = la_dong_menu(dong)
        if la_menu:
            n_menu += 1
            n_menu_ky_tu += len(dong)
            continue
        giu.append(dong)
    s = "\n".join(giu)
    if n_menu:
        go["dong_menu"] = n_menu_ky_tu
        dinh["dong_menu"] = n_menu

    # Giai ma thuc the HTML (&nbsp; &amp; &#39;) — giai ma chu khong xoa, vi
    # chung thuong nam GIUA chu that va xoa di se dinh hai tu vao nhau.
    truoc = len(s)
    s = html.unescape(s)
    if len(s) != truoc:
        go["thuc_the_html"] = go.get("thuc_the_html", 0) + abs(truoc - len(s))
        dinh["thuc_the_html"] = dinh.get("thuc_the_html", 0) + 1

    # Don khoang trang thua do viec go de lai.
    s = re.sub(r"[ \t ]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = "\n".join(d.strip() for d in s.split("\n"))
    s = s.strip()

    tong_go = goc_dai - len(s)
    return s, go, dinh, max(tong_go, 0)


def main(argv=None):
    p = argparse.ArgumentParser(description="Loc rac cao web khoi ngu lieu JSONL")
    p.add_argument("--vao", required=True, help="tep JSONL dau vao")
    p.add_argument("--ra", default=None, help="tep JSONL dau ra (bat buoc tru khi --chi-do)")
    p.add_argument("--truong", default="text",
                   help="ten truong chua van ban (mac dinh 'text'; thu ca 'noi_dung' neu khong thay)")
    p.add_argument("--truong-nguon", default="nguon",
                   help="ten truong ghi nguon, de chia nho bao cao (mac dinh 'nguon')")
    p.add_argument("--nguong-rac", type=float, default=0.0,
                   help="MAC DINH 0 = TAT. Neu dat > 0, bo ca doan khi ti le da go vuot nguong "
                        "nay. Doc phan dau tep truoc khi bat: tieu chi nay tung an nham cau van "
                        "that trong lan chay thu 25/09/2026.")
    p.add_argument("--toi-thieu-ky-tu", type=int, default=80,
                   help="doan ngan hon nay sau khi go thi bo (mac dinh 80)")
    p.add_argument("--toi-thieu-ti-le-chu", type=float, default=0.65,
                   help="phan con lai phai co it nhat ti le nay la chu/so/khoang trang/dau cau "
                        "thong thuong, neu khong thi la manh vun chu khong phai cau (mac dinh 0.65)")
    p.add_argument("--mien-nha", action="append", default=["bdsg.vn"],
                   help="mien duoc coi la cua nha, URL cua no khong bi go (lap lai duoc)")
    p.add_argument("--bo-moi-url", action="store_true", help="go ca URL cua mien nha")
    p.add_argument("--chi-do", action="store_true", help="chi do va bao cao, khong ghi tep ra")
    p.add_argument("--xem-thu", type=int, default=0,
                   help="in ra N doan bi BO de kiem lai bang mat (nen dung lan dau)")
    p.add_argument("--bao-cao", default=None, help="tep JSON ghi bao cao (mac dinh canh tep --ra)")
    args = p.parse_args(argv)

    duong_vao = os.path.abspath(os.path.expanduser(args.vao))
    if not os.path.isfile(duong_vao):
        p.error("Khong thay tep: {}".format(duong_vao))
    if not args.chi_do and not args.ra:
        p.error("Phai co --ra, hoac dung --chi-do de chi do ma khong ghi")

    tk = {
        "vao": 0, "giu": 0, "bo_ngan": 0, "bo_nhieu_rac": 0, "bo_rong": 0,
        "bo_khong_ra_van": 0,
        "ky_tu_vao": 0, "ky_tu_ra": 0, "ky_tu_go": 0,
        "go_theo_luat": {}, "dinh_theo_luat": {}, "theo_nguon": {},
    }
    vi_du_bo = []

    f_ra = None
    if not args.chi_do:
        duong_ra = os.path.abspath(os.path.expanduser(args.ra))
        thu_muc = os.path.dirname(duong_ra)
        if thu_muc and not os.path.isdir(thu_muc):
            os.makedirs(thu_muc)
        f_ra = open(duong_ra, "w", encoding="utf-8")

    with open(duong_vao, "r", encoding="utf-8", errors="ignore") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            try:
                d = json.loads(dong)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if args.truong in d:
                truong = args.truong
            elif "noi_dung" in d:
                truong = "noi_dung"
            elif "text" in d:
                truong = "text"
            else:
                continue
            goc = str(d[truong])
            nguon = str(d.get(args.truong_nguon, "khong-ro"))

            tk["vao"] += 1
            tk["ky_tu_vao"] += len(goc)
            n = tk["theo_nguon"].setdefault(
                nguon, {"vao": 0, "giu": 0, "bo": 0, "ky_tu_vao": 0, "ky_tu_ra": 0, "ky_tu_go": 0})
            n["vao"] += 1
            n["ky_tu_vao"] += len(goc)

            sach, go, dinh, da_go = go_rac(goc, args.mien_nha, args.bo_moi_url)
            for k, v in go.items():
                tk["go_theo_luat"][k] = tk["go_theo_luat"].get(k, 0) + v
            for k, v in dinh.items():
                tk["dinh_theo_luat"][k] = tk["dinh_theo_luat"].get(k, 0) + v
            tk["ky_tu_go"] += da_go
            n["ky_tu_go"] += da_go

            ti_le_rac = da_go / float(len(goc)) if goc else 1.0
            # Ba tieu chi dau CHI NHIN PHAN CON LAI. Xem phan dau tep: tieu chi
            # "da go bao nhieu" do cong viec cua bo loc, khong do chat luong cai
            # con lai, nen no chi chay khi nguoi dung co y bat --nguong-rac.
            ly_do = None
            if not sach:
                ly_do = "bo_rong"
            elif len(sach) < args.toi_thieu_ky_tu:
                ly_do = "bo_ngan"
            elif ti_le_chu_cai(sach) < args.toi_thieu_ti_le_chu:
                ly_do = "bo_khong_ra_van"
            elif args.nguong_rac > 0 and ti_le_rac > args.nguong_rac:
                ly_do = "bo_nhieu_rac"

            if ly_do:
                tk[ly_do] += 1
                n["bo"] += 1
                if len(vi_du_bo) < args.xem_thu:
                    vi_du_bo.append({"ly_do": ly_do, "nguon": nguon,
                                     "ti_le_rac": round(ti_le_rac, 3),
                                     "goc": goc[:400], "sau_khi_go": sach[:400]})
                continue

            tk["giu"] += 1
            tk["ky_tu_ra"] += len(sach)
            n["giu"] += 1
            n["ky_tu_ra"] += len(sach)
            if f_ra is not None:
                d[truong] = sach
                f_ra.write(json.dumps(d, ensure_ascii=False) + "\n")

    if f_ra is not None:
        f_ra.close()

    bo = tk["bo_ngan"] + tk["bo_nhieu_rac"] + tk["bo_rong"] + tk["bo_khong_ra_van"]
    print("")
    print("=" * 78)
    print("LAM SACH — {}".format(os.path.basename(duong_vao)))
    print("=" * 78)
    print("  doan vao        : {:,}".format(tk["vao"]))
    print("  doan giu        : {:,}  ({:.2f}%)".format(
        tk["giu"], 100.0 * tk["giu"] / tk["vao"] if tk["vao"] else 0))
    print("  doan bo         : {:,}  ({:.2f}%)".format(
        bo, 100.0 * bo / tk["vao"] if tk["vao"] else 0))
    print("      rong sau khi go        : {:,}".format(tk["bo_rong"]))
    print("      ngan hon {:>4} ky tu    : {:,}".format(args.toi_thieu_ky_tu, tk["bo_ngan"]))
    print("      con lai khong ra van   : {:,}".format(tk["bo_khong_ra_van"]))
    print("      ti le rac vuot nguong  : {:,}{}".format(
        tk["bo_nhieu_rac"], "" if args.nguong_rac > 0 else "   (--nguong-rac dang TAT)"))
    print("  ky tu vao       : {:,}  ({:.2f} MB)".format(
        tk["ky_tu_vao"], tk["ky_tu_vao"] / 1024.0 / 1024.0))
    print("  ky tu ra        : {:,}  ({:.2f} MB)".format(
        tk["ky_tu_ra"], tk["ky_tu_ra"] / 1024.0 / 1024.0))
    if tk["ky_tu_vao"]:
        print("  mat di          : {:,} ky tu = {:.2f}% dung luong".format(
            tk["ky_tu_vao"] - tk["ky_tu_ra"],
            100.0 * (tk["ky_tu_vao"] - tk["ky_tu_ra"]) / tk["ky_tu_vao"]))

    if tk["go_theo_luat"]:
        print("")
        print("  Tung luat go duoc bao nhieu:")
        print("  {:<18} {:>12} {:>12}".format("luat", "so lan dinh", "so ky tu"))
        print("  " + "-" * 44)
        for k in sorted(tk["go_theo_luat"], key=lambda x: -tk["go_theo_luat"][x]):
            print("  {:<18} {:>12,} {:>12,}".format(
                k, tk["dinh_theo_luat"].get(k, 0), tk["go_theo_luat"][k]))

    if len(tk["theo_nguon"]) > 1:
        print("")
        print("  Theo nguon:")
        print("  {:<22} {:>9} {:>9} {:>9} {:>12}".format("nguon", "vao", "giu", "bo", "MB con lai"))
        print("  " + "-" * 64)
        for ng in sorted(tk["theo_nguon"], key=lambda x: -tk["theo_nguon"][x]["vao"]):
            v = tk["theo_nguon"][ng]
            print("  {:<22} {:>9,} {:>9,} {:>9,} {:>12.2f}".format(
                ng[:22], v["vao"], v["giu"], v["bo"], v["ky_tu_ra"] / 1024.0 / 1024.0))

    print("")
    print("  DOI CHIEU voi phep do 25/09/2026 (11.733 doan / 7,16 MB truoc khi loc):")
    print("    do luc do    : 110 doan dinh rac = 0,17 MB = 2,3% dung luong")
    print("    lan chay nay : {:,} doan bi bo, mat {:.2f}% dung luong".format(
        bo, 100.0 * (tk["ky_tu_vao"] - tk["ky_tu_ra"]) / tk["ky_tu_vao"] if tk["ky_tu_vao"] else 0))
    print("    Neu lan nay bo NHIEU HON han thi kha nang cao la bo loc an nham,")
    print("    khong phai du lieu ban hon. Chay lai voi --xem-thu 20 va doc bang mat.")

    if vi_du_bo:
        print("")
        print("=" * 78)
        print("{} DOAN BI BO — DOC BANG MAT TRUOC KHI TIN BO LOC".format(len(vi_du_bo)))
        print("=" * 78)
        for i, v in enumerate(vi_du_bo, 1):
            print("")
            print("[{}] ly do={}  nguon={}  ti le rac={}".format(
                i, v["ly_do"], v["nguon"], v["ti_le_rac"]))
            print("    GOC       : {}".format(v["goc"].replace("\n", " \\n ")[:300]))
            print("    SAU KHI GO: {}".format(v["sau_khi_go"].replace("\n", " \\n ")[:300]))

    bao_cao = dict(tk)
    bao_cao["ngay_chay"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bao_cao["tep_vao"] = duong_vao
    bao_cao["tep_ra"] = None if args.chi_do else os.path.abspath(os.path.expanduser(args.ra))
    bao_cao["tham_so"] = {"nguong_rac": args.nguong_rac,
                          "toi_thieu_ky_tu": args.toi_thieu_ky_tu,
                          "mien_nha": args.mien_nha,
                          "bo_moi_url": args.bo_moi_url}
    duong_bc = args.bao_cao
    if not duong_bc:
        goc_bc = args.ra if args.ra else duong_vao
        duong_bc = os.path.splitext(os.path.abspath(os.path.expanduser(goc_bc)))[0] + ".bao-cao-lam-sach.json"
    with open(duong_bc, "w", encoding="utf-8") as f:
        json.dump(bao_cao, f, ensure_ascii=False, indent=2)
    print("")
    print("  Bao cao: {}".format(duong_bc))
    if args.chi_do:
        print("  (--chi-do: khong ghi tep du lieu nao)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
