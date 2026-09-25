#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tinh chinh theo chi dan (SFT) cho mo hinh BDSG.

=============================================================================
TEP NAY LAM GI
=============================================================================
Doc JSONL dang

    {"hoi_thoai": [{"vai": "nguoi",  "noi_dung": "..."},
                   {"vai": "tro-ly", "noi_dung": "..."}]}

bien moi hoi thoai thanh mot chuoi token theo DINH DANG HOI THOAI CUA BDSG, CHE
MAT phan cau hoi, va chi tinh mat mat tren phan tra loi cua tro ly.

    python3 tinh_chinh.py \\
        --du-lieu ../du-lieu-da-tron/sft-vi.jsonl \\
        --cau-hinh cau-hinh/nho.json \\
        --tu-vung  tu-vung/ket-qua/tokenizer-vi-24576 \\
        --tu-diem-dung out/tien-huan-luyen-nho/diem-dung.pt \\
        --thu-muc-ra out/nho-tinh-chinh

=============================================================================
VI SAO PHAI CHE MAT NHAN O PHAN CAU HOI — DAY LA DIEU QUAN TRONG NHAT O DAY
=============================================================================
Neu tinh mat mat tren CA cau hoi lan cau tra loi, thi mot phan luc hoc cua mo
hinh bi dung de hoc DU DOAN CAU HOI CUA NGUOI DUNG. Noi cach khac: ta dang day
no VIET LAI cau hoi.

Ba hau qua cu the, khong phai lo xa:

  1. Chia sai luc hoc. Trong ngu lieu hoi-dap nghiep vu, cau hoi thuong ngan va
     RAT co khuon ("Cong ty X kinh doanh gi?"). Do la thu de doan nhat trong ca
     tep. Mat mat tren no giam rat nhanh, keo mat mat trung binh xuong, va lam
     bieu do dep len — trong khi phan tra loi, thu duy nhat ta can, hoc cham hon
     ma khong ai nhin thay rieng no.

  2. Mo hinh hoc thoi quen SINH RA CAU HOI. Vi trong du lieu, sau mot luot tra
     loi luon la mot luot hoi moi, mo hinh duoc thuong khi doan dung rang tiep
     theo la mot cau hoi. Luc chay that, no tra loi xong roi tu hoi tiep.

  3. Loi khong bao. Khong co ngoai le nao duoc nem ra, khong co canh bao nao. Chi
     co mot mo hinh kem hon mot cach kho giai thich.

Cho nen mat na o day duoc dung theo CACH DUNG SAN chu khong phai tim bang chuoi:
chuoi token duoc rap tung doan mot, va moi doan duoc danh dau ngay luc rap la
"co giam sat" hay "khong". Mat na dung theo CAU TRUC, khong phu thuoc vao viec
tim thay hay khong tim thay mot chuoi dau hieu nao do trong day token.

(Cach kia — ma hoa ca hoi thoai roi di TIM chuoi "<|mo-luot|>tro-ly\\n" trong day
token — hong im lang khi mot tin nhan cua nguoi dung tinh co chua dung chuoi ay,
hoac khi BPE gop ranh gioi khac di mot chut. Luc do mat na lech, mat mat van
giam, va khong ai biet.)

=============================================================================
DINH DANG HOI THOAI CUA BDSG — KHAI RO DUNG TOKEN GI
=============================================================================
Token dac biet do huan-luyen/tu-vung/huan_luyen_tu_vung.py dat ra (doc ngay
26/09/2026, khong doan):

    id 0   <|het-van-ban|>   ngan cach van ban + token dem (padding)
    id 1   <|mo-luot|>       mo mot luot noi
    id 2   <|dong-luot|>     dong mot luot noi

Hai vai hop le, VA CHI HAI: "nguoi" va "tro-ly". Khong co vai "he-thong" —
huan-luyen/du-lieu/tron.py tu choi ghi ra ban ghi co vai khac.

Mot hoi thoai hai luot duoc rap thanh dung chuoi nay:

    <|mo-luot|>nguoi\\n{cau hoi}<|dong-luot|>\\n<|mo-luot|>tro-ly\\n{tra loi}<|dong-luot|>\\n

Luc suy luan, mau hoi thoai dung den "<|mo-luot|>tro-ly\\n" roi de mo hinh viet
tiep. Nen phan CO GIAM SAT dung bang thu mo hinh phai tu sinh ra:

    {tra loi}  va  <|dong-luot|>

Dau xuong dong SAU <|dong-luot|> KHONG duoc giam sat: luc chay that, sinh chu
dung ngay o <|dong-luot|>, khong bao gio den dau xuong dong do. Giam sat no la
day mo hinh mot thoi quen no khong bao gio dung toi.

Mat na duoc dat TREN CHINH TOKEN, khong phai tren nhan da dich: nhan[i] = ids[i]
neu token thu i thuoc phan tro-ly phai tu sinh ra, va -100 neu khong. Mo hinh bo
nhan dau (nhan[:, 1:]) nen rieng vi tri 0 khong bao gio duoc dung — moi cho dem
"so token co nhan" o day deu dem tu vi tri 1 tro di cho khop.

=============================================================================
PHU THUOC mo-hinh/
=============================================================================
Giong huan_luyen.py. Hop dong day du o dau huan-luyen/chung.py. Nhac lai dong
quan trong nhat: mo-hinh/ TU DICH NHAN ben trong forward(), nen o day `nhan` co
CUNG HINH DANG voi `ids` va chua CHINH chuoi token do — chi khac o cho nhung vi
tri khong duoc giam sat bi dat thanh -100. Ben nay KHONG dich.
"""

import argparse
import contextlib
import json
import math
import os
import sys

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

import chung  # noqa: E402

# --- Dinh dang hoi thoai cua BDSG -----------------------------------------
# Giu cung mot cho voi MAU_HOI_THOAI trong huan-luyen/tu-vung/huan_luyen_tu_vung.py.
# RANG BUOC PHAI GIU CUNG NHAU: ai doi mot ben phai doi ben kia trong CUNG mot
# lan sua. Doi mot ben thoi thi mat na tro sai cho ma khong co loi nao bao.
MO_LUOT = "<|mo-luot|>"
DONG_LUOT = "<|dong-luot|>"
HET_VAN_BAN = "<|het-van-ban|>"
VAI_HOP_LE = ("nguoi", "tro-ly")
VAI_TRO_LY = "tro-ly"

# Ten truong thay the duoc chap nhan. Ten CHINH la hoi_thoai/vai/noi_dung — dung
# nhu huan-luyen/du-lieu/tron.py --dinh-dang sft xuat ra. Chap nhan them bo ten
# tieng Anh pho bien vi ngu lieu chi dan mo tren mang hau het dung bo do; doi ten
# truong o mot tep 2 trieu dong chi de chay thu la viec khong dang bat ai lam.
TEN_TRUONG_HOI_THOAI = ("hoi_thoai", "conversations", "messages")
TEN_TRUONG_VAI = ("vai", "role")
TEN_TRUONG_NOI_DUNG = ("noi_dung", "content")
# Anh xa vai tieng Anh -> vai BDSG. "system" KHONG co trong bang: BDSG khong co
# vai he-thong, va lang le bien no thanh mot vai khac la lam sai du lieu.
DOI_VAI = {"user": "nguoi", "human": "nguoi", "assistant": "tro-ly", "bot": "tro-ly"}


# ---------------------------------------------------------------------------
# Rap chuoi token va mat na
# ---------------------------------------------------------------------------
def lay_truong(d, cac_ten):
    for t in cac_ten:
        if t in d:
            return d[t]
    return None


def chuan_hoa_hoi_thoai(ban_ghi):
    """Tra ve danh sach [(vai, noi_dung)] hoac (None, ly do bo qua)."""
    ht = lay_truong(ban_ghi, TEN_TRUONG_HOI_THOAI)
    if not isinstance(ht, list) or not ht:
        return None, "khong co truong hoi_thoai hoac no rong"
    ra = []
    for i, luot in enumerate(ht):
        if not isinstance(luot, dict):
            return None, "luot {} khong phai doi tuong".format(i)
        vai = lay_truong(luot, TEN_TRUONG_VAI)
        noi_dung = lay_truong(luot, TEN_TRUONG_NOI_DUNG)
        if vai is None or noi_dung is None:
            return None, "luot {} thieu vai hoac noi_dung".format(i)
        vai = DOI_VAI.get(str(vai), str(vai))
        if vai not in VAI_HOP_LE:
            return None, "luot {} co vai la '{}' (chi chap nhan {})".format(
                i, vai, list(VAI_HOP_LE))
        noi_dung = str(noi_dung)
        if not noi_dung.strip():
            return None, "luot {} co noi_dung rong".format(i)
        ra.append((vai, noi_dung))
    if not any(v == VAI_TRO_LY for v, _ in ra):
        return None, "khong co luot nao cua tro-ly — khong co gi de giam sat"
    return ra, None


def rap_chuoi(hoi_thoai, tok):
    """Rap hoi thoai thanh (ids, giam_sat) — hai danh sach cung do dai.

    giam_sat[i] = True nghia la token ids[i] la thu mo hinh PHAI TU SINH RA luc
    chay that, tuc no duoc tinh vao mat mat. Xem phan giai thich o dau tep.

    Mat na dung theo CAU TRUC: moi doan duoc ma hoa rieng va danh dau ngay luc
    rap. Khong co buoc "di tim chuoi dau hieu" nao ca.
    """
    ids = []
    giam_sat = []

    def them(van_ban, co_giam_sat):
        ma = tok.encode(van_ban).ids
        ids.extend(ma)
        giam_sat.extend([co_giam_sat] * len(ma))

    for vai, noi_dung in hoi_thoai:
        la_tro_ly = (vai == VAI_TRO_LY)
        them(MO_LUOT + vai + "\n", False)   # phan mo luot: khong giam sat
        them(noi_dung, la_tro_ly)           # noi dung: giam sat neu la tro-ly
        them(DONG_LUOT, la_tro_ly)          # dau dong luot: mo hinh phai tu sinh
        them("\n", False)                   # xuong dong: khong bao gio sinh toi
    return ids, giam_sat


def kiem_ghep(hoi_thoai, tok, ids):
    """Kiem rang ma hoa TUNG DOAN cho ra dung ket qua nhu ma hoa CA CHUOI.

    VI SAO PHAI KIEM: BPE gop cap ky tu lien nhau. Cat chuoi ra tung doan roi ma
    hoa rieng CO THE cho day token khac voi ma hoa lien mot mach, vi mot merge
    bac qua ranh gioi doan da bi chan.

    Neu no khac, mat na van dung tren chuoi TA RAP, nhung chuoi ta rap lai khac
    chuoi mo hinh nhin thay luc suy luan — mo hinh se duoc huan luyen tren mot
    cach chia token ma no khong bao gio gap lai. Do la mot lech am tham, khong
    co ngoai le nao duoc nem ra.

    Tra ve None neu khop, hoac (so_token_rap, so_token_lien) neu lech.
    """
    lien = []
    for vai, noi_dung in hoi_thoai:
        lien.append(MO_LUOT + vai + "\n" + noi_dung + DONG_LUOT + "\n")
    ma = tok.encode("".join(lien)).ids
    if ma == ids:
        return None
    return (len(ids), len(ma))


def cat_trai(ids, giam_sat, do_dai_toi_da):
    """Cat bot tu DAU chuoi khi qua dai, giu phan cuoi.

    VI SAO CAT O DAU CHU KHONG O CUOI: phan co giam sat — cau tra loi cuoi cung —
    nam o CUOI chuoi. Cat o cuoi la cat dung thu ta dang huan luyen, de lai mot
    mau van ton dung bay nhieu phep tinh nhung dong gop 0 tin hieu. Cat o dau thi
    mat phan ngu canh cu nhat, va do la thu re nhat de mat.
    """
    if len(ids) <= do_dai_toi_da:
        return ids, giam_sat, False
    return ids[-do_dai_toi_da:], giam_sat[-do_dai_toi_da:], True


def nap_mau(cac_tep, tok, do_dai_toi_da, gioi_han=None, so_mau_kiem_ghep=200):
    """Doc JSONL, rap tung mau. Tra ve (danh sach mau, thong ke).

    Moi mau la (ids, nhan) da DICH SAN:
        ids  = chuoi[:-1]
        nhan = chuoi[1:]  voi -100 o moi vi tri khong duoc giam sat
    """
    mau = []
    tk = {"so_ban_ghi": 0, "so_bo_qua": 0, "so_cat": 0, "so_khong_con_nhan": 0,
          "so_token": 0, "so_token_co_nhan": 0, "so_lech_ghep": 0}
    ly_do_bo = {}

    for tep in cac_tep:
        for d in chung.doc_jsonl(tep):
            tk["so_ban_ghi"] += 1
            ht, ly_do = chuan_hoa_hoi_thoai(d)
            if ht is None:
                tk["so_bo_qua"] += 1
                ly_do_bo[ly_do] = ly_do_bo.get(ly_do, 0) + 1
                continue

            ids, giam_sat = rap_chuoi(ht, tok)

            if tk["so_ban_ghi"] <= so_mau_kiem_ghep:
                lech = kiem_ghep(ht, tok, ids)
                if lech is not None:
                    tk["so_lech_ghep"] += 1
                    if tk["so_lech_ghep"] <= 3:
                        print("  [canh bao] ma hoa tung doan lech ma hoa lien mach: "
                              "{} token so voi {} token. Xem docstring ham kiem_ghep."
                              .format(lech[0], lech[1]))

            ids, giam_sat, bi_cat = cat_trai(ids, giam_sat, do_dai_toi_da)
            if bi_cat:
                tk["so_cat"] += 1
            if len(ids) < 2:
                tk["so_bo_qua"] += 1
                continue

            # KHONG dich o day: mo-hinh/ dich ben trong. nhan la chinh chuoi
            # token, dat -100 o vi tri khong duoc giam sat.
            dau_vao = ids
            nhan = [ids[i] if giam_sat[i] else -100 for i in range(len(ids))]

            # Dem tu vi tri 1: mo hinh tinh loss tren nhan[:, 1:], nen nhan o vi
            # tri 0 khong bao gio duoc dung.
            so_co_nhan = sum(1 for x in nhan[1:] if x != -100)
            if so_co_nhan == 0:
                # Xay ra khi cat trai da cat mat toan bo cau tra loi.
                tk["so_khong_con_nhan"] += 1
                continue

            mau.append((dau_vao, nhan))
            tk["so_token"] += len(dau_vao)
            tk["so_token_co_nhan"] += so_co_nhan

            if gioi_han and len(mau) >= gioi_han:
                return mau, tk, ly_do_bo
    return mau, tk, ly_do_bo


# ---------------------------------------------------------------------------
# Xep lo
# ---------------------------------------------------------------------------
def xep_lo(mau, chi_so, batch, cua_so_gom, gom_theo_do_dai=True):
    """Chia chi so thanh cac lo. Tra ve danh sach cac lo (moi lo la list chi so).

    VI SAO GOM THEO DO DAI: trong mot lo, moi mau phai duoc dem cho bang mau dai
    nhat. Tron ngau nhien mot mau 800 token voi bay mau 40 token thi 90% phep
    tinh cua lo do la tinh tren token dem — tra tien GPU cho con so 0.

    VI SAO CHI GOM TRONG MOT CUA SO CHU KHONG SAP XEP CA TEP: sap ca tep theo do
    dai thi moi lo chi con mot loai do dai, va do dai thuong di kem loai noi
    dung (cau tra loi ngan la mot loai cau hoi khac han). Luc do moi buoc toi uu
    nhin thay mot lat cat lech cua du lieu. Gom trong cua so vai chuc lo thi
    vua bot dem vua giu duoc tinh ngau nhien.
    """
    lo = []
    kich_thuoc_cua_so = batch * max(1, cua_so_gom)
    for dau in range(0, len(chi_so), kich_thuoc_cua_so):
        cua_so = chi_so[dau:dau + kich_thuoc_cua_so]
        if gom_theo_do_dai:
            cua_so = sorted(cua_so, key=lambda i: len(mau[i][0]))
        for j in range(0, len(cua_so), batch):
            phan = cua_so[j:j + batch]
            if len(phan) == batch:
                lo.append(phan)
    return lo


def dung_tensor_lo(mau, chi_so_lo, pad_id, thiet_bi):
    """Bien mot lo chi so thanh (ids, nhan) da dem cho bang nhau.

    DEM O BEN PHAI, va day la dieu KHIEN KHONG CAN MAT NA CHU Y:
    mo hinh la decoder-only nhan qua — moi vi tri chi nhin ve phia truoc. Token
    dem nam SAU toan bo token that, nen khong mot token that nao nhin thay chung.
    Ban than cac vi tri dem co nhan -100 nen khong dong gop vao mat mat. Do do
    ket qua giong het nhu khong co dem.

    Neu dem o BEN TRAI thi lap luan tren SAI: moi token that se nhin thay token
    dem nam truoc no, va mo hinh hoc tren mot ngu canh khong ton tai luc suy
    luan. Ghi ra day vi day la cho de "toi uu" nham.
    """
    torch = chung.torch
    dai_nhat = max(len(mau[i][0]) for i in chi_so_lo)
    ids = torch.full((len(chi_so_lo), dai_nhat), pad_id, dtype=torch.long)
    nhan = torch.full((len(chi_so_lo), dai_nhat), -100, dtype=torch.long)
    for hang, i in enumerate(chi_so_lo):
        a, b = mau[i]
        ids[hang, :len(a)] = torch.tensor(a, dtype=torch.long)
        nhan[hang, :len(b)] = torch.tensor(b, dtype=torch.long)
    return ids.to(thiet_bi), nhan.to(thiet_bi)


def nhom_tham_so(mo_hinh, weight_decay):
    """Giong huan_luyen.py: chi ap suy giam trong so cho tham so >= 2 chieu."""
    co_giam, khong_giam = [], []
    for p in mo_hinh.parameters():
        if not p.requires_grad:
            continue
        (co_giam if p.dim() >= 2 else khong_giam).append(p)
    return [
        {"params": co_giam, "weight_decay": weight_decay},
        {"params": khong_giam, "weight_decay": 0.0},
    ]


def do_phan_kiem(mo_hinh, mau, cac_lo, pad_id, thiet_bi, so_lo_toi_da=30):
    """Mat mat trung binh theo SO TOKEN CO NHAN tren phan kiem.

    Trung binh theo token co nhan chu khong theo lo: cac lo co so token duoc giam
    sat rat khac nhau (cau tra loi dai ngan khac nhau), trung binh theo lo se cho
    nhung lo tra loi ngan trong so qua lon.
    """
    torch = chung.torch
    mo_hinh.eval()
    tong = 0.0
    dem = 0
    with torch.no_grad():
        for lo in cac_lo[:so_lo_toi_da]:
            ids, nhan = dung_tensor_lo(mau, lo, pad_id, thiet_bi)
            _, loss = chung.goi_mo_hinh(mo_hinh, ids, nhan)
            n = chung.dem_token_co_nhan(nhan)
            tong += loss.item() * n
            dem += n
    mo_hinh.train()
    if dem == 0:
        return None
    return tong / dem


# ---------------------------------------------------------------------------
def doc_tham_so(argv=None):
    p = argparse.ArgumentParser(
        description="Tinh chinh theo chi dan (SFT) cho mo hinh BDSG",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    n = p.add_argument_group("dau vao")
    n.add_argument("--du-lieu", help="tep .jsonl hoac thu muc chua cac tep .jsonl")
    n.add_argument("--cau-hinh", default=os.path.join(THU_MUC, "cau-hinh", "nho.json"))
    n.add_argument("--tu-vung", help="tokenizer.json, hoac thu muc chua no")
    n.add_argument("--thu-muc-mo-hinh",
                   default=os.path.abspath(os.path.join(THU_MUC, "..", "mo-hinh")))
    n.add_argument("--tu-diem-dung", default="",
                   help="diem dung tien huan luyen de lay trong so ban dau "
                        "(CHI lay trong so, khong lay trang thai toi uu)")
    n.add_argument("--gioi-han-mau", type=int, default=0,
                   help="chi dung bay nhieu mau dau (0 = het); de chay thu nhanh")

    r = p.add_argument_group("dau ra")
    r.add_argument("--thu-muc-ra", default=os.path.join(THU_MUC, "out"))
    r.add_argument("--ten", default="")

    h = p.add_argument_group("hinh dang lo")
    h.add_argument("--max-seq-len", type=int, default=512)
    h.add_argument("--batch", type=int, default=8)
    h.add_argument("--tich-luy", type=int, default=1)
    h.add_argument("--cua-so-gom", type=int, default=32,
                   help="so lo trong mot cua so gom theo do dai")
    h.add_argument("--khong-gom-do-dai", action="store_true",
                   help="tat viec gom theo do dai (xep lo thuan ngau nhien)")

    o = p.add_argument_group("toi uu")
    o.add_argument("--ky", type=int, default=2,
                   help="SFT thuong chay it ky hon tien huan luyen")
    o.add_argument("--hoc-suat", type=float, default=5e-5,
                   help="thap hon tien huan luyen mot bac: dang tinh chinh mot mo "
                        "hinh da biet ngon ngu, khong phai day lai tu dau")
    o.add_argument("--ti-le-hoc-suat-cuoi", type=float, default=0.1)
    o.add_argument("--ti-le-ham-nong", type=float, default=0.03)
    o.add_argument("--cat-gradient", type=float, default=1.0)
    o.add_argument("--weight-decay", type=float, default=0.0,
                   help="mac dinh 0 o SFT: du lieu it, phat trong so de lam mat "
                        "kien thuc da hoc o tien huan luyen")
    o.add_argument("--beta1", type=float, default=0.9)
    o.add_argument("--beta2", type=float, default=0.95)
    o.add_argument("--so-buoc-toi-da", type=int, default=0)

    m = p.add_argument_group("may")
    m.add_argument("--thiet-bi", default="tu-dong")
    m.add_argument("--amp", action="store_true")
    m.add_argument("--hat-giong", type=int, default=1234)

    k = p.add_argument_group("theo doi va diem dung")
    k.add_argument("--in-moi", type=int, default=10)
    k.add_argument("--luu-moi", type=int, default=500)
    k.add_argument("--ti-le-kiem", type=float, default=0.02)
    k.add_argument("--kiem-moi", type=int, default=500)
    k.add_argument("--tiep-tuc", action="store_true")
    k.add_argument("--so-mau-kiem-ghep", type=int, default=200,
                   help="so mau dau duoc kiem 'ma hoa tung doan == ma hoa lien mach'")

    x = p.add_argument_group("xem thu")
    x.add_argument("--xem-mat-na", type=int, default=0,
                   help="in ra bay nhieu mau dau kem mat na roi thoat (khong huan luyen)")

    return p.parse_args(argv)


def in_mat_na(mau, tok, so_mau):
    """In ra tung token kem dau hieu co giam sat hay khong.

    VI SAO CO CHUC NANG NAY: mat na la thu de sai nhat va kho thay nhat trong ca
    bo. Mot lan nhin bang mat vao ba mau dat hon moi lap luan.
    """
    print("")
    print("XEM MAT NA — dau '+' = co tinh mat mat, '.' = bi che")
    print("=" * 74)
    for i in range(min(so_mau, len(mau))):
        dau_vao, nhan = mau[i]
        print("")
        print("--- mau {} ({} token, {} token co nhan) ---".format(
            i + 1, len(dau_vao), sum(1 for x in nhan[1:] if x != -100)))
        dong = []
        for t in range(len(dau_vao)):
            chu = tok.decode([dau_vao[t]], skip_special_tokens=False)
            chu = chu.replace("\n", "\\n")
            dong.append("{}{}".format("+" if nhan[t] != -100 else ".", chu))
        print(" ".join(dong))
    print("")
    print("=" * 74)
    print("Doc bang nay the nao: dau '+' nam TREN CHINH token duoc giam sat. No")
    print("phai phu dung noi dung luot tro-ly va token <|dong-luot|> dong luot do.")
    print("  - thay '+' o phan cau hoi  => mat na sai, mo hinh dang duoc day viet")
    print("    lai cau hoi cua nguoi dung;")
    print("  - khong thay '+' o dau ca  => khong co tin hieu nao, mo hinh hoc tu 0;")
    print("  - thay '+' o '<|mo-luot|>' hay o chu 'tro-ly' => lech mot doan, vi hai")
    print("    thu do la khung do ta dung, khong phai thu mo hinh phai sinh ra.")


# ---------------------------------------------------------------------------
def main(argv=None):
    args = doc_tham_so(argv)
    chung.doi_hoi_torch()
    torch = chung.torch

    chung.dat_hat_giong(args.hat_giong)
    thiet_bi = chung.chon_thiet_bi(args.thiet_bi)

    if not args.du_lieu:
        raise SystemExit("Thieu --du-lieu (tep .jsonl hoac thu muc chua chung).")
    if not args.tu_vung:
        raise SystemExit("Thieu --tu-vung (tokenizer.json hoac thu muc chua no).")

    cfg, ghi_chu = chung.nap_cau_hinh(args.cau_hinh)
    tok = chung.nap_tu_vung(args.tu_vung)
    chung.kiem_tu_vung(tok, cfg, args.tu_vung)

    pad_id = chung.id_token_dac_biet(tok, HET_VAN_BAN)
    if pad_id is None:
        pad_id = cfg.get("pad_token_id", 0)
        print("  [canh bao] khong thay {} trong tu vung; dung pad_id={}".format(
            HET_VAN_BAN, pad_id))
    for ten in (MO_LUOT, DONG_LUOT):
        if chung.id_token_dac_biet(tok, ten) is None:
            raise SystemExit(
                "Tu vung khong co token {}.\n"
                "  Dinh dang hoi thoai cua BDSG dua tren ba token dac biet do\n"
                "  huan-luyen/tu-vung/huan_luyen_tu_vung.py dat ra. Tu vung dang\n"
                "  dung khong phai tu vung do — kiem lai --tu-vung.".format(ten))

    print("=" * 74)
    print("  TINH CHINH THEO CHI DAN (SFT) — BDSG")
    print("=" * 74)
    chung.in_bang([
        ("thiet bi", chung.mo_ta_thiet_bi(thiet_bi)),
        ("cau hinh", args.cau_hinh),
        ("tu vung", args.tu_vung),
        ("dinh dang", "{}<vai>\\n<noi dung>{}\\n  · vai: {}".format(
            MO_LUOT, DONG_LUOT, " / ".join(VAI_HOP_LE))),
        ("giam sat", "noi dung cua luot tro-ly + token {}".format(DONG_LUOT)),
        ("token dem", "{} (id {})".format(HET_VAN_BAN, pad_id)),
    ])

    # --- du lieu ---
    cac_tep = chung.liet_ke_tep(args.du_lieu)
    print("")
    print("  Nap du lieu tu {} tep...".format(len(cac_tep)))
    mau, tk, ly_do_bo = nap_mau(
        cac_tep, tok, args.max_seq_len,
        gioi_han=args.gioi_han_mau or None,
        so_mau_kiem_ghep=args.so_mau_kiem_ghep)
    if not mau:
        raise SystemExit(
            "Khong rap duoc mau nao.\n"
            "  Ly do bi bo qua: {}".format(ly_do_bo))

    ti_le_nhan = tk["so_token_co_nhan"] / float(max(1, tk["so_token"]))
    chung.in_bang([
        ("ban ghi doc", "{:,}".format(tk["so_ban_ghi"])),
        ("mau dung duoc", "{:,}".format(len(mau))),
        ("bo qua", "{:,}".format(tk["so_bo_qua"])),
        ("bi cat bot dau", "{:,}".format(tk["so_cat"])),
        ("bo vi cat mat het cau tra loi", "{:,}".format(tk["so_khong_con_nhan"])),
        ("token dau vao", "{:,}".format(tk["so_token"])),
        ("token CO TINH mat mat", "{:,}  ({:.1%} — phan con lai bi che)".format(
            tk["so_token_co_nhan"], ti_le_nhan)),
        ("lech ghep token", "{:,}{}".format(
            tk["so_lech_ghep"],
            "  <== xem docstring ham kiem_ghep" if tk["so_lech_ghep"] else " (tot)")),
    ])
    if ly_do_bo:
        print("")
        print("  Ly do bo qua:")
        for ly_do, so in sorted(ly_do_bo.items(), key=lambda x: -x[1])[:8]:
            print("    {:>8,}  {}".format(so, ly_do))
    if ti_le_nhan < 0.05:
        print("")
        print("  [CANH BAO] chi {:.1%} token duoc tinh mat mat. Voi hoi thoai hoi-dap "
              "thong thuong, con so nay thuong o khoang 30-60%. Qua thap thuong nghia "
              "la cau tra loi trong ngu lieu qua ngan so voi cau hoi, hoac vai bi ghi "
              "sai. Xem lai bang --xem-mat-na.".format(ti_le_nhan))

    if args.xem_mat_na:
        in_mat_na(mau, tok, args.xem_mat_na)
        return 0

    # --- chia hoc / kiem ---
    thu_tu = chung.thu_tu_lo(len(mau), args.hat_giong, 0)
    so_kiem = int(len(mau) * args.ti_le_kiem)
    chi_so_kiem = thu_tu[:so_kiem]
    chi_so_hoc = thu_tu[so_kiem:]
    # O SFT, phan kiem LAY NGAU NHIEN duoc — khac tien huan luyen. Ly do: moi mau
    # o day la mot hoi thoai doc lap, khong co chuyen hai mau lien nhau cung den
    # tu mot van ban bi cat doi.
    gom = not args.khong_gom_do_dai
    lo_kiem = xep_lo(mau, chi_so_kiem, args.batch, args.cua_so_gom, gom) if chi_so_kiem else []

    so_lo_moi_ky = len(xep_lo(mau, chi_so_hoc, args.batch, args.cua_so_gom, gom))
    so_buoc_moi_ky = so_lo_moi_ky // args.tich_luy
    if so_buoc_moi_ky < 1:
        raise SystemExit(
            "Khong du mau cho lay mot buoc toi uu: {:,} mau hoc, mot buoc can "
            "batch*tich_luy = {} mau.".format(len(chi_so_hoc), args.batch * args.tich_luy))
    tong_buoc = so_buoc_moi_ky * args.ky
    if args.so_buoc_toi_da:
        tong_buoc = min(tong_buoc, args.so_buoc_toi_da)
    buoc_ham_nong = max(1, int(tong_buoc * args.ti_le_ham_nong))

    # --- mo hinh ---
    CauHinhBDSG, LopMoHinh = chung.nap_kien_truc(args.thu_muc_mo_hinh)
    mo_hinh = LopMoHinh(chung.dung_cau_hinh(CauHinhBDSG, cfg)).to(thiet_bi)
    so_tham_so = sum(p.numel() for p in mo_hinh.parameters())

    bo_toi_uu = torch.optim.AdamW(
        nhom_tham_so(mo_hinh, args.weight_decay),
        lr=args.hoc_suat, betas=(args.beta1, args.beta2))
    dung_amp, kieu_amp, dung_scaler = chung.kieu_du_lieu_tu_dong(thiet_bi, args.amp)
    scaler = torch.amp.GradScaler(thiet_bi.type) if dung_scaler else None

    if args.tu_diem_dung:
        if not os.path.isfile(args.tu_diem_dung):
            raise SystemExit("Khong thay diem dung: {}".format(args.tu_diem_dung))
        # CHI lay trong so. KHONG lay trang thai AdamW cua lan tien huan luyen:
        # hai moment cua no thuoc ve mot bai toan khac (hoc suat khac, du lieu
        # khac), mang sang thi vai tram buoc dau di theo quan tinh cu.
        goi = torch.load(args.tu_diem_dung, map_location=thiet_bi, weights_only=False)
        mo_hinh.load_state_dict(goi["trong_so"])
        print("")
        print("  Lay trong so ban dau tu {} (buoc {:,})".format(
            args.tu_diem_dung, (goi.get("trang_thai") or {}).get("buoc_toan_cuc", 0)))
    else:
        print("")
        print("  [CANH BAO] khong co --tu-diem-dung: dang tinh chinh mot mo hinh")
        print("  KHOI TAO NGAU NHIEN. SFT tren trong so ngau nhien khong sai ve ky")
        print("  thuat nhung gan nhu vo nghia: mo hinh chua biet tieng Viet, no se")
        print("  hoc thuoc vai nghin cau tra loi. Chay huan_luyen.py truoc.")

    print("")
    chung.in_bang([
        ("tham so (DEM DUOC)", "{:,} = {:.2f}M".format(so_tham_so, so_tham_so / 1e6)),
        ("mau hoc / mau kiem", "{:,} / {:,}".format(len(chi_so_hoc), len(chi_so_kiem))),
        ("lo hieu dung", "{} x {} = {} mau/buoc".format(
            args.batch, args.tich_luy, args.batch * args.tich_luy)),
        ("buoc moi ky / tong buoc", "{:,} / {:,}".format(so_buoc_moi_ky, tong_buoc)),
        ("buoc ham nong", "{:,}".format(buoc_ham_nong)),
        ("gom theo do dai", "{}".format(gom)),
        ("autocast", "{} {}".format(dung_amp, kieu_amp if dung_amp else "")),
    ])

    ten = args.ten or os.path.splitext(os.path.basename(args.cau_hinh))[0]
    thu_muc_ra = os.path.join(args.thu_muc_ra, "tinh-chinh-" + ten)
    if not os.path.isdir(thu_muc_ra):
        os.makedirs(thu_muc_ra)
    duong_diem_dung = os.path.join(thu_muc_ra, "diem-dung.pt")
    duong_nhat_ky = os.path.join(thu_muc_ra, "nhat-ky.jsonl")

    buoc_toan_cuc = 0
    if args.tiep_tuc:
        if os.path.isfile(duong_diem_dung):
            trang_thai, _ = chung.nap_diem_dung(
                duong_diem_dung, mo_hinh, bo_toi_uu, thiet_bi, scaler)
            buoc_toan_cuc = int(trang_thai.get("buoc_toan_cuc", 0))
            print("")
            print("  TIEP TUC tu {} — buoc {:,}/{:,}".format(
                duong_diem_dung, buoc_toan_cuc, tong_buoc))
        else:
            print("")
            print("  --tiep-tuc: khong thay {} — bat dau tu dau.".format(duong_diem_dung))
    if buoc_toan_cuc >= tong_buoc:
        print("  Da du {:,} buoc.".format(tong_buoc))
        return 0

    dong_ho = chung.DongHo()
    mo_hinh.train()
    nhat_ky = open(duong_nhat_ky, "a", encoding="utf-8")
    ngat_giua_chung = False

    print("")
    print("-" * 74)
    try:
        for ky in range(args.ky):
            if (ky + 1) * so_buoc_moi_ky <= buoc_toan_cuc:
                continue
            thu_tu_ky = [chi_so_hoc[j] for j in
                         chung.thu_tu_lo(len(chi_so_hoc), args.hat_giong, ky + 1)]
            cac_lo = xep_lo(mau, thu_tu_ky, args.batch, args.cua_so_gom, gom)
            buoc_trong_ky = max(0, buoc_toan_cuc - ky * so_buoc_moi_ky)
            vi_tri = buoc_trong_ky * args.tich_luy

            while buoc_toan_cuc < tong_buoc and vi_tri + args.tich_luy <= len(cac_lo):
                bo_toi_uu.zero_grad(set_to_none=True)
                he_so = chung.he_so_hoc_suat(
                    buoc_toan_cuc, tong_buoc, buoc_ham_nong, args.ti_le_hoc_suat_cuoi)
                hoc_suat = args.hoc_suat * he_so
                chung.dat_hoc_suat(bo_toi_uu, hoc_suat)

                tong_loss = 0.0
                token_co_nhan = 0
                token_da_tinh = 0
                for _ in range(args.tich_luy):
                    ids, nhan = dung_tensor_lo(mau, cac_lo[vi_tri], pad_id, thiet_bi)
                    vi_tri += 1
                    ngu_canh = (torch.autocast(thiet_bi.type, dtype=kieu_amp)
                                if dung_amp else contextlib.nullcontext())
                    with ngu_canh:
                        _, loss = chung.goi_mo_hinh(mo_hinh, ids, nhan)
                    loss_chia = loss / args.tich_luy
                    if scaler is not None:
                        scaler.scale(loss_chia).backward()
                    else:
                        loss_chia.backward()
                    tong_loss += loss.item()
                    token_co_nhan += chung.dem_token_co_nhan(nhan)
                    token_da_tinh += ids.numel()

                if args.cat_gradient > 0:
                    if scaler is not None:
                        scaler.unscale_(bo_toi_uu)
                    torch.nn.utils.clip_grad_norm_(mo_hinh.parameters(), args.cat_gradient)
                if scaler is not None:
                    scaler.step(bo_toi_uu)
                    scaler.update()
                else:
                    bo_toi_uu.step()

                buoc_toan_cuc += 1
                dong_ho.ghi(token_da_tinh)
                loss_tb = tong_loss / args.tich_luy

                if buoc_toan_cuc % args.in_moi == 0 or buoc_toan_cuc == 1:
                    con_lai = dong_ho.con_lai(buoc_toan_cuc, tong_buoc)
                    print("  buoc {:>7,}/{:,} | ky {}/{} | loss {:.4f} | "
                          "nhan {:>6,} token | lr {:.2e} | {:>9,.0f} token/giay | con {}".format(
                              buoc_toan_cuc, tong_buoc, ky + 1, args.ky, loss_tb,
                              token_co_nhan, hoc_suat, dong_ho.toc_do(),
                              chung.dinh_dang_giay(con_lai)))
                    nhat_ky.write(json.dumps({
                        "buoc": buoc_toan_cuc, "ky": ky + 1, "loss": loss_tb,
                        "token_co_nhan": token_co_nhan, "lr": hoc_suat,
                        "token_giay": dong_ho.toc_do()}, ensure_ascii=False) + "\n")
                    nhat_ky.flush()

                if lo_kiem and args.kiem_moi > 0 and buoc_toan_cuc % args.kiem_moi == 0:
                    loss_kiem = do_phan_kiem(mo_hinh, mau, lo_kiem, pad_id, thiet_bi)
                    if loss_kiem is not None:
                        print("  >>> phan kiem: loss {:.4f} | ppl {}".format(
                            loss_kiem, chung.dinh_dang_ppl(loss_kiem)))
                        nhat_ky.write(json.dumps(
                            {"buoc": buoc_toan_cuc, "loss_kiem": loss_kiem},
                            ensure_ascii=False) + "\n")
                        nhat_ky.flush()

                if args.luu_moi > 0 and buoc_toan_cuc % args.luu_moi == 0:
                    chung.luu_diem_dung(
                        duong_diem_dung, mo_hinh, bo_toi_uu,
                        {"buoc_toan_cuc": buoc_toan_cuc, "ky": ky,
                         "tong_buoc": tong_buoc, "loai": "tinh-chinh"},
                        cfg, scaler)
                    print("  >>> da luu diem dung o buoc {:,}".format(buoc_toan_cuc))

            if buoc_toan_cuc >= tong_buoc:
                break
    except KeyboardInterrupt:
        ngat_giua_chung = True
        print("")
        print("  Ctrl-C — dang luu diem dung truoc khi thoat...")
    finally:
        chung.luu_diem_dung(
            duong_diem_dung, mo_hinh, bo_toi_uu,
            {"buoc_toan_cuc": buoc_toan_cuc, "tong_buoc": tong_buoc,
             "loai": "tinh-chinh"},
            cfg, scaler)
        nhat_ky.close()

    print("-" * 74)
    chung.in_bang([
        ("buoc da chay", "{:,}/{:,}".format(buoc_toan_cuc, tong_buoc)),
        ("thoi gian", chung.dinh_dang_giay(dong_ho.da_troi())),
        ("diem dung", duong_diem_dung),
        ("nhat ky", duong_nhat_ky),
    ])
    if ngat_giua_chung:
        print("  Bi ngat giua chung. Chay lai cung lenh kem --tiep-tuc de di tiep.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
