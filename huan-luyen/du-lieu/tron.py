#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tron ngu lieu HAI ngon ngu theo trong so, xuat hai dinh dang cua BDSG.

Tieng Viet la ngon ngu chinh. Tieng Anh la ngon ngu phu. Khong co ngon ngu thu ba.

=============================================================================
1. HAI DINH DANG CUA BDSG
=============================================================================
  --dinh-dang pretrain -> moi dong:
      {"text": "...", "nguon": "...", "ngon_ngu": "vi"}

  --dinh-dang sft      -> moi dong:
      {"hoi_thoai": [{"vai": "nguoi", "noi_dung": "..."},
                     {"vai": "tro-ly", "noi_dung": "..."}],
       "nguon": "..."}

Day la dinh dang CUA BDSG. No khong duoc mo ta la "tuong thich" voi bat ky du
an nao — mot dinh dang tu dinh nghia thi tu no la chuan cua minh, va bat ky bo
nap du lieu nao muon doc no chi can doc ba ten truong tren.

Hai vai hop le va chi hai: "nguoi" va "tro-ly". Khong co vai "he-thong" trong
ban nay. Neu sau nay can, phai them o CA HAI noi trong CUNG mot lan sua: o day
va o ham sinh mat na nhan khi huan luyen. Them mot ben thoi thi khong co loi
nao bao — chi la cac luot mang vai moi khong duoc gan nhan, va mo hinh hoc tu
it tin hieu hon minh tuong.

=============================================================================
2. XUAT XU LA TRUONG BAT BUOC, KHONG PHAI TRUONG THEM
=============================================================================
Moi ban ghi ghi ra deu mang truong `nguon`. Khong co ngoai le, va script TU
CHOI ghi ban ghi nao khong xac dinh duoc xuat xu.

Vi sao khat khe: mot tep ngu lieu khong noi duoc chu no den tu dau la mot tep
khong dung duoc de phat hanh. Sau khi tron xong, ba thang sau, phat hien mot
nguon co van de ve giay phep — neu khong co truong `nguon` tren tung dong thi
cach duy nhat con lai la vut ca tep va tron lai tu dau. Mot truong chuoi ngan
tren moi dong la cai gia re nhat de khoi phai lam viec do.

Xuat xu lay theo thu tu: truong `nguon` co san trong ban ghi (min nhat, do
bo-du-lieu/xuat.py sinh ra) -> ten nguon khai o dong lenh -> tu choi.

=============================================================================
3. TRUONG `ngon_ngu` LA LOI KHAI, KHONG PHAI KET QUA NHAN DANG
=============================================================================
Script nay KHONG nhan dang ngon ngu. Gia tri "vi" hay "en" chi don gian la
nguoi chay da khai tep do o --nguon-viet hay --nguon-anh. Dat mot tep tieng
Anh vao --nguon-viet thi moi ban ghi se mang nhan "vi" va khong co gi bao loi.

De do la khong duoc, nen co mot phep kiem RE TIEN chay kem: dem ti le ban ghi
co chua it nhat mot ky tu mang dau tieng Viet. Tep khai la "vi" ma ti le do
qua thap, hoac tep khai la "en" ma ti le do qua cao, thi script CANH BAO.

Hai nguong (0,50 va 0,20) la con so DAT, chua do tren bo ngu lieu nao. Va phep
kiem nay CHI CANH BAO, khong chan: tieng Viet khong dau la tieng Viet that va
co that trong du lieu doanh nghiep, nen no se lam nguong dau bao dong nham.
Mot canh bao doc duoc con hon mot phep chan dung sai.

=============================================================================
4. TRON RA SAO — VA VI SAO KHONG XEP KHOI
=============================================================================
Tron theo NHIP (xen ke deu), khong noi duoi nhau tung khoi ngon ngu:
  - de ai cat bot duoi tep di van con du hai thu tieng;
  - de doc bieu do mat mat theo thoi gian con co nghia — voi tep xep khoi, mat
    mat se giam roi vot len dung luc doi ngon ngu, va nguoi doc se tuong mo
    hinh hong.

TI LE tinh theo KY TU, khong theo so dong. Mot dong tieng Anh 40 ky tu khong
dang gia bang mot doan tieng Viet 4.000 ky tu; dem dong cho ti le sai hoan toan.

Thuat toan xen ke la chia ghe kieu du phan lon nhat: moi ngon ngu cong don mot
"no" bang ti le cua no moi buoc, ai no nhieu nhat thi duoc ghi truoc. Ket qua
xen ke deu va TAT DINH — cung hat giong cho ra cung tep, byte cho byte.

=============================================================================
5. DIEU SCRIPT NAY TU CHOI LAM
=============================================================================
No KHONG tu bien van ban tron thanh hoi-dap. Muon xuat SFT thi nguon phai THUC
SU co doi thoai — hoac san truong "hoi_thoai", hoac co hai truong cau hoi /
cau tra loi de anh xa bang --truong-hoi va --truong-dap.

Boc mot doan van vao mot cau hoi tu che kieu "Hay noi ve doanh nghiep nay" la
BIA du lieu huan luyen: mo hinh se hoc rang moi doan van deu la cau tra loi cho
mot cau hoi khong ai hoi, va no se tra loi nhu the ke ca khi nguoi ta hoi viec
khac.

=============================================================================
6. CHAY
=============================================================================
    # pretrain, tron hai thu tieng:
    python3 tron.py --dinh-dang pretrain \
        --nguon-viet ho-so-niem-yet=../../bo-du-lieu/doan_tri_thuc.sach.jsonl \
        --nguon-viet wikipedia-vi=/du/lieu/wikipedia-vi.jsonl \
        --nguon-anh  fineweb-edu=/du/lieu/nen-en.jsonl \
        --ti-le-viet 0.80 --ti-le-anh 0.20 \
        --cat-doan 0 \
        --ra ../../bo-du-lieu/pretrain-tron.jsonl

    CHU Y ve --cat-doan: vi du tren de 0 (khong cat) CO CHU Y. Do dai cat phai
    TINH RA tu tu vung that, khong duoc dat bua — xem docstring ham
    cat_theo_cau(). Cach tinh: do so ky tu moi token bang
    huan-luyen/tu-vung/do_tokenizer.py roi nhan voi tran ngu canh
    (max_position_embeddings trong huan-luyen/cau-hinh/*.json, hien la 2048).
    Vi du voi so da do ngay 25/09/2026 — 3,59 ky tu moi token:
        2048 token * 3,59 ky tu/token  ~=  7.350 ky tu
    Con so 3,59 do tren tu vung THU NGHIEM 6.400, khong phai tu vung phat hanh;
    do lai sau khi co tu vung that roi hay dat so nay.

    # sft, chi tu nguon THAT SU co doi thoai:
    python3 tron.py --dinh-dang sft \
        --nguon-viet hoi-dap-noi-bo=../../bo-du-lieu/hoi-dap-vi.jsonl \
        --ra ../../bo-du-lieu/sft-tron.jsonl

Chi can python >= 3.8. Khong can thu vien ngoai.
"""

import argparse
import datetime
import json
import os
import random
import re
import sys
import unicodedata

NGON_NGU = ["vi", "en"]
TI_LE_MAC_DINH = {"vi": 0.80, "en": 0.20}

# Hai vai, va chi hai. Xem muc 1 phan dau tep.
VAI_HOP_LE = ("nguoi", "tro-ly")
VAI_TRO_LY = "tro-ly"

# Cat cau theo dau ket cau cua chu Latin, va CHI chu Latin. Cac dau ket cau cua
# he chu khac da bi go khoi mau nay ngay 26/09/2026, khi pham vi du an rut ve
# hai ngon ngu. Ly do go chu khong phai de nguyen cho chac: mot nhanh khong bao
# gio khop van trong nhu mot kha nang dang duoc ho tro, va nguoi doc sau nay se
# tuong duong ong con xu ly duoc thu tieng ay.
MAU_HET_CAU = re.compile(r"(?<=[.!?])\s+")

# Nguong canh bao ngon ngu. DAT, chua do. Xem muc 3 phan dau tep.
NGUONG_DAU_TOI_THIEU_VI = 0.50
NGUONG_DAU_TOI_DA_EN = 0.20


def co_dau_tieng_viet(ch):
    """True neu ky tu la chu cai Latin mang dau tieng Viet.

    Tach NFD roi tim dau ket hop (category Mn). Rieng d-gach khong co dau ket
    hop trong NFD nen phai liet ke tay.
    """
    if ch in "đĐ":
        return True
    tach = unicodedata.normalize("NFD", ch)
    return len(tach) > 1 and any(unicodedata.category(c) == "Mn" for c in tach)


def co_dau_trong_chuoi(s):
    """True neu chuoi co it nhat mot ky tu mang dau tieng Viet.

    Dung ham dung som (any + generator) chu khong quet het chuoi: mot doan
    4.000 ky tu thuong dinh dau ngay o tu dau, nen quet het la lang phi.
    """
    return any(co_dau_tieng_viet(c) for c in s)


def cat_theo_cau(van_ban, toi_da_ky_tu):
    """Cat doan dai thanh nhieu manh, uu tien ranh gioi cau.

    VI SAO CAN CAT: bo nap du lieu khi tien huan luyen thuong CAT CUT doan dai
    hon do dai chuoi toi da va VUT phan duoi, khong day sang mau sau. Do nguyen
    mot doan 4.000 ky tu vao thi phan lon doan do khong bao gio duoc hoc, va
    khong co dong nhat ky nao noi. Cat truoc o day thi phan nao cung den duoc
    mo hinh.

    Mac dinh --cat-doan = 0 (khong cat), co chu y: do dai cat dung phai tinh
    tu so ky tu tren mot token cua tu vung THAT, do bang
    huan-luyen/tu-vung/do_tokenizer.py. Dat mot so bua o day con te hon khong
    cat, vi no trong nhu da tinh toan.

    Neu mot cau don le da dai hon gioi han thi cat cung tai gioi han — mat mot
    cau bi dut con hon mat ca phan duoi.
    """
    if toi_da_ky_tu <= 0 or len(van_ban) <= toi_da_ky_tu:
        return [van_ban]
    manh = []
    hien_tai = []
    dai = 0
    for cau in MAU_HET_CAU.split(van_ban):
        if not cau:
            continue
        if len(cau) > toi_da_ky_tu:
            if hien_tai:
                manh.append(" ".join(hien_tai))
                hien_tai, dai = [], 0
            for i in range(0, len(cau), toi_da_ky_tu):
                manh.append(cau[i:i + toi_da_ky_tu])
            continue
        if dai + len(cau) + 1 > toi_da_ky_tu and hien_tai:
            manh.append(" ".join(hien_tai))
            hien_tai, dai = [], 0
        hien_tai.append(cau)
        dai += len(cau) + 1
    if hien_tai:
        manh.append(" ".join(hien_tai))
    return [m for m in manh if m.strip()]


def kiem_hoi_thoai(hoi_thoai):
    """Kiem mot doi thoai co dung khuon BDSG khong. Tra ve loi dau tien, hoac None."""
    if not isinstance(hoi_thoai, list) or not hoi_thoai:
        return "hoi_thoai rong hoac khong phai danh sach"
    co_tro_ly = False
    for i, m in enumerate(hoi_thoai):
        if not isinstance(m, dict):
            return "luot {} khong phai doi tuong".format(i)
        vai = m.get("vai")
        if vai not in VAI_HOP_LE:
            return ("vai '{}' khong hop le (chi nhan {}). Vai la se KHONG bao loi luc "
                    "huan luyen, chi lam khong luot nao duoc gan nhan."
                    .format(vai, list(VAI_HOP_LE)))
        if not isinstance(m.get("noi_dung", ""), str):
            return "noi_dung cua luot {} khong phai chuoi".format(i)
        if not str(m.get("noi_dung", "")).strip():
            return "noi_dung cua luot {} rong".format(i)
        if vai == VAI_TRO_LY:
            co_tro_ly = True
    if not co_tro_ly:
        return "khong co luot '{}' nao -> khong co gi de hoc".format(VAI_TRO_LY)
    return None


def doc_nguon(duong_dan, ten_nguon_khai, ma_ngon_ngu, dinh_dang,
              truong_hoi, truong_dap, cat_doan, loi_bo_qua):
    """Sinh (ban_ghi, so_ky_tu, co_dau) da dung dinh dang dich tu mot tep.

    co_dau chi dung cho phep kiem ngon ngu re tien o muc 3 phan dau tep.
    """
    so_dong = 0
    with open(duong_dan, "r", encoding="utf-8", errors="ignore") as f:
        for dong in f:
            so_dong += 1
            dong = dong.strip()
            if not dong:
                continue
            try:
                d = json.loads(dong)
            except ValueError:
                loi_bo_qua.append((duong_dan, so_dong, "khong phai JSON hop le"))
                continue
            if not isinstance(d, dict):
                loi_bo_qua.append((duong_dan, so_dong, "dong khong phai doi tuong JSON"))
                continue

            # --- Xuat xu: truong `nguon` cua ban ghi thang ten khai o dong lenh.
            # Ban ghi min hon vi bo-du-lieu/xuat.py biet tung doan den tu bang
            # nao; ten khai o dong lenh chi biet ca tep.
            nguon = str(d.get("nguon") or "").strip() or (ten_nguon_khai or "").strip()
            if not nguon:
                loi_bo_qua.append((
                    duong_dan, so_dong,
                    "khong xac dinh duoc xuat xu: ban ghi khong co truong 'nguon' va "
                    "dong lenh khong khai ten nguon cho tep nay (dung dang TEN=DUONGDAN)"))
                continue

            if dinh_dang == "pretrain":
                if "text" in d:
                    vb = str(d["text"])
                elif "noi_dung" in d and not isinstance(d.get("noi_dung"), (list, dict)):
                    vb = str(d["noi_dung"])
                elif "hoi_thoai" in d and isinstance(d["hoi_thoai"], list):
                    # Doi thoai van dung lam ngu lieu tien huan luyen duoc: noi
                    # cac luot lai. Chieu nguoc lai thi KHONG (xem muc 5).
                    vb = "\n".join(str(m.get("noi_dung", "")) for m in d["hoi_thoai"]
                                   if isinstance(m, dict))
                else:
                    loi_bo_qua.append((duong_dan, so_dong,
                                       "khong co truong text/noi_dung/hoi_thoai"))
                    continue
                if not vb.strip():
                    continue
                for manh in cat_theo_cau(vb, cat_doan):
                    yield ({"text": manh, "nguon": nguon, "ngon_ngu": ma_ngon_ngu},
                           len(manh), co_dau_trong_chuoi(manh))

            else:  # sft
                if "hoi_thoai" in d:
                    ht = d["hoi_thoai"]
                elif truong_hoi and truong_dap and truong_hoi in d and truong_dap in d:
                    # ANH XA hai truong da co san thanh mot luot hoi-dap. Day la
                    # anh xa du lieu DA CO, khong phai bia cau hoi ra.
                    ht = [{"vai": "nguoi", "noi_dung": str(d[truong_hoi])},
                          {"vai": VAI_TRO_LY, "noi_dung": str(d[truong_dap])}]
                else:
                    loi_bo_qua.append((
                        duong_dan, so_dong,
                        "khong co 'hoi_thoai' va khong co cap --truong-hoi/--truong-dap. "
                        "Script khong tu bia cau hoi tu van ban tron."))
                    continue
                loi = kiem_hoi_thoai(ht)
                if loi:
                    loi_bo_qua.append((duong_dan, so_dong, loi))
                    continue
                sach = [{"vai": m["vai"], "noi_dung": str(m["noi_dung"])} for m in ht]
                n = sum(len(m["noi_dung"]) for m in sach)
                co_dau = any(co_dau_trong_chuoi(m["noi_dung"]) for m in sach)
                yield {"hoi_thoai": sach, "nguon": nguon}, n, co_dau


def phan_tich_nguon(cac_chuoi, ten_tham_so):
    """'ten-nguon=/duong/dan.jsonl' -> [(ten_nguon, duong_dan), ...].

    Cho phep bo ten (chi dua duong dan) — luc do xuat xu phai nam san trong
    tung ban ghi, neu khong ban ghi se bi tu choi. Ghi ro o day de nguoi chay
    khong bat ngo.
    """
    ra = []
    for s in cac_chuoi:
        if "=" in s:
            ten, duong = s.split("=", 1)
            ten = ten.strip()
        else:
            ten, duong = "", s
        duong = os.path.abspath(os.path.expanduser(duong.strip()))
        if not duong:
            raise ValueError("{} thieu duong dan: {!r}".format(ten_tham_so, s))
        ra.append((ten, duong))
    return ra


def chuan_hoa_ti_le(ti_le_viet, ti_le_anh):
    """Chuan hoa ve tong 1,0. Tra ve dict {'vi': .., 'en': ..}."""
    if ti_le_viet < 0 or ti_le_anh < 0:
        raise ValueError("Ti le khong duoc am")
    tong = ti_le_viet + ti_le_anh
    if tong <= 0:
        raise ValueError("Tong --ti-le-viet va --ti-le-anh phai lon hon 0")
    return {"vi": ti_le_viet / tong, "en": ti_le_anh / tong}


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Tron ngu lieu hai ngon ngu (Viet chinh, Anh phu) thanh dinh dang BDSG")
    p.add_argument("--nguon-viet", action="append", default=[], metavar="TEN=DUONGDAN",
                   help="nguon tieng Viet, lap lai duoc. TEN la xuat xu ghi vao tung ban ghi")
    p.add_argument("--nguon-anh", action="append", default=[], metavar="TEN=DUONGDAN",
                   help="nguon tieng Anh, lap lai duoc")
    p.add_argument("--dinh-dang", choices=["pretrain", "sft"], default="pretrain",
                   help="pretrain -> {'text','nguon','ngon_ngu'}; sft -> {'hoi_thoai','nguon'}")
    p.add_argument("--ti-le-viet", type=float, default=TI_LE_MAC_DINH["vi"],
                   help="phan ngan sach KY TU danh cho tieng Viet (mac dinh 0.80)")
    p.add_argument("--ti-le-anh", type=float, default=TI_LE_MAC_DINH["en"],
                   help="phan ngan sach KY TU danh cho tieng Anh (mac dinh 0.20)")
    p.add_argument("--ra", required=True, help="tep JSONL dau ra")
    p.add_argument("--cat-doan", type=int, default=0,
                   help="cat doan dai hon N ky tu theo ranh gioi cau; 0 = khong cat. "
                        "Do so ky tu/token bang do_tokenizer.py truoc khi dat so nay")
    p.add_argument("--tong-ky-tu", type=int, default=0,
                   help="tong ngan sach ky tu dau ra; 0 = lay ngan sach lon nhat ma du lieu "
                        "hien co con giu dung ti le")
    p.add_argument("--truong-hoi", default=None, help="ten truong cau hoi (chi cho --dinh-dang sft)")
    p.add_argument("--truong-dap", default=None, help="ten truong cau tra loi (chi cho --dinh-dang sft)")
    p.add_argument("--hat-giong", type=int, default=42, help="hat giong ngau nhien (mac dinh 42)")
    p.add_argument("--bao-cao", default=None, help="tep JSON ghi bao cao")
    args = p.parse_args(argv)

    if not args.nguon_viet and not args.nguon_anh:
        p.error("Phai co it nhat mot --nguon-viet hoac --nguon-anh")
    try:
        nguon = {"vi": phan_tich_nguon(args.nguon_viet, "--nguon-viet"),
                 "en": phan_tich_nguon(args.nguon_anh, "--nguon-anh")}
        ti_le = chuan_hoa_ti_le(args.ti_le_viet, args.ti_le_anh)
    except ValueError as e:
        p.error(str(e))

    thieu = [d for ds in nguon.values() for _, d in ds if not os.path.isfile(d)]
    if thieu:
        p.error("Khong tim thay tep:\n  " + "\n  ".join(thieu))

    rng = random.Random(args.hat_giong)
    loi_bo_qua = []

    # --- Doc tung ngon ngu vao bo nho -------------------------------------
    # Doc het roi moi tron: can biet tong so ky tu THAT cua tung ngon ngu de
    # tinh nhip xen ke cho dung. O quy mo hien tai (ngu lieu BDSG 7,13 MB cong
    # ngu lieu nen tai ve) thi doc mot luot la du va de kiem hon. Voi vai GB
    # thi phai doi sang cach doc hai luot — ghi ra day de nguoi sau biet gioi
    # han nam o dau.
    kho = {}
    canh_bao_ngon_ngu = []
    print("")
    for ng in NGON_NGU:
        if not nguon[ng]:
            print("  {}: khong co nguon -> bo qua".format(ng))
            kho[ng] = {"ban_ghi": [], "ky_tu_co": 0}
            continue
        ban_ghi = []
        tong = 0
        for ten, t in nguon[ng]:
            so_bg = 0
            so_co_dau = 0
            for bg, n, co_dau in doc_nguon(t, ten, ng, args.dinh_dang,
                                           args.truong_hoi, args.truong_dap,
                                           args.cat_doan, loi_bo_qua):
                ban_ghi.append((bg, n))
                tong += n
                so_bg += 1
                if co_dau:
                    so_co_dau += 1
            # Phep kiem ngon ngu re tien (muc 3). CHI canh bao.
            if so_bg:
                ti = so_co_dau / float(so_bg)
                canh = None
                if ng == "vi" and ti < NGUONG_DAU_TOI_THIEU_VI:
                    canh = ("tep khai la tieng Viet nhung chi {:.1%} ban ghi co dau tieng "
                            "Viet (nguong {:.0%}). Co the dat nham tep, hoac day la tieng "
                            "Viet khong dau — truong hop sau la binh thuong."
                            .format(ti, NGUONG_DAU_TOI_THIEU_VI))
                elif ng == "en" and ti > NGUONG_DAU_TOI_DA_EN:
                    canh = ("tep khai la tieng Anh nhung {:.1%} ban ghi co dau tieng Viet "
                            "(nguong {:.0%}). Co the dat nham tep."
                            .format(ti, NGUONG_DAU_TOI_DA_EN))
                if canh:
                    canh_bao_ngon_ngu.append({"tep": t, "ngon_ngu_khai": ng,
                                              "ti_le_co_dau": round(ti, 4), "canh_bao": canh})
        rng.shuffle(ban_ghi)
        kho[ng] = {"ban_ghi": ban_ghi, "ky_tu_co": tong}
        print("  {}: {:,} ban ghi, {:,} ky tu tu {} tep".format(
            ng, len(ban_ghi), tong, len(nguon[ng])))

    for c in canh_bao_ngon_ngu:
        print("")
        print("  !! CANH BAO NGON NGU: {}".format(os.path.basename(c["tep"])))
        print("     {}".format(c["canh_bao"]))

    if all(not v["ban_ghi"] for v in kho.values()):
        sys.stderr.write("\nKhong doc duoc ban ghi nao. Ly do bi bo qua (20 dau tien):\n")
        for t, d, ly in loi_bo_qua[:20]:
            sys.stderr.write("  {}:{}  {}\n".format(os.path.basename(t), d, ly))
        return 2

    # --- Quyet dinh ngan sach ky tu cho tung ngon ngu ---------------------
    # Ngon ngu it du lieu nhat quyet dinh quy mo, neu muon giu DUNG ti le. Con
    # so nay TINH RA chu khong dat tay, va duoc in ra de nguoi chay thay minh
    # dang phai bo bot bao nhieu cua ngon ngu con lai.
    co_mat = [ng for ng in NGON_NGU if kho[ng]["ban_ghi"]]
    if args.tong_ky_tu:
        tong_dich = args.tong_ky_tu
    else:
        kha_thi = [kho[ng]["ky_tu_co"] / ti_le[ng] for ng in co_mat if ti_le[ng] > 0]
        tong_dich = int(min(kha_thi)) if kha_thi else sum(kho[ng]["ky_tu_co"] for ng in co_mat)

    ngan_sach = dict((ng, min(int(tong_dich * ti_le[ng]), kho[ng]["ky_tu_co"]))
                     for ng in co_mat)

    print("")
    # Cot "ngan sach" la so DINH truoc khi ghi; so ky tu THAT se nhinh hon mot
    # chut vi ngan sach duoc kiem TRUOC khi ghi ban ghi cuoi chu khong cat doi
    # ban ghi do. So that in o phan ket qua ben duoi.
    print("  {:<5} {:>14} {:>14} {:>10} {:>11}".format(
        "ngon", "ky tu co", "ngan sach", "ti le dat", "ti le nsach"))
    print("  " + "-" * 58)
    tong_ns = sum(ngan_sach.values()) or 1
    for ng in co_mat:
        print("  {:<5} {:>14,} {:>14,} {:>10.3f} {:>11.3f}".format(
            ng, kho[ng]["ky_tu_co"], ngan_sach[ng], ti_le[ng],
            ngan_sach[ng] / float(tong_ns)))

    # --- Xen ke theo nhip -------------------------------------------------
    # Chia ghe kieu du phan lon nhat: moi ngon ngu cong don mot "no" bang ti le
    # cua no moi buoc; ai no nhieu nhat thi duoc ghi truoc. Xen ke deu va TAT
    # DINH — cung hat giong cho ra cung tep, byte cho byte.
    vi_tri = dict((ng, 0) for ng in co_mat)
    da_dung = dict((ng, 0) for ng in co_mat)
    no = dict((ng, 0.0) for ng in co_mat)
    tong_ti_le = sum(ti_le[ng] for ng in co_mat) or 1.0

    duong_ra = os.path.abspath(os.path.expanduser(args.ra))
    thu_muc = os.path.dirname(duong_ra)
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc)

    so_ghi = dict((ng, 0) for ng in co_mat)
    dem_nguon = {}
    tong_ghi = 0
    with open(duong_ra, "w", encoding="utf-8") as f:
        while True:
            con = [ng for ng in co_mat
                   if vi_tri[ng] < len(kho[ng]["ban_ghi"]) and da_dung[ng] < ngan_sach[ng]]
            if not con:
                break
            for ng in con:
                no[ng] += ti_le[ng] / tong_ti_le
            chon = max(con, key=lambda x: no[x])
            no[chon] -= 1.0
            bg, n = kho[chon]["ban_ghi"][vi_tri[chon]]
            vi_tri[chon] += 1
            da_dung[chon] += n
            so_ghi[chon] += 1
            tong_ghi += 1
            dem_nguon[bg["nguon"]] = dem_nguon.get(bg["nguon"], 0) + 1
            f.write(json.dumps(bg, ensure_ascii=False) + "\n")

    print("")
    print("  Da ghi {:,} ban ghi ({:,} ky tu) ra {}".format(
        tong_ghi, sum(da_dung.values()), duong_ra))
    for ng in co_mat:
        print("    {}: {:,} ban ghi, {:,} ky tu".format(ng, so_ghi[ng], da_dung[ng]))
    print("")
    print("  Xuat xu tren tung ban ghi (dieu kien de phat hanh duoc):")
    for k in sorted(dem_nguon, key=lambda x: -dem_nguon[x]):
        print("    {:<28} {:>9,} ban ghi".format(k[:28], dem_nguon[k]))

    if loi_bo_qua:
        print("")
        print("  {:,} dong bi bo qua. Ly do (5 dau tien):".format(len(loi_bo_qua)))
        for t, d, ly in loi_bo_qua[:5]:
            print("    {}:{}  {}".format(os.path.basename(t), d, ly))
        print("  (day la con so DANG CHU Y — neu no lon, dinh dang nguon dang sai)")

    bao_cao = {
        "ngay_chay": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dinh_dang": args.dinh_dang,
        "ngon_ngu": NGON_NGU,
        "tep_ra": duong_ra,
        "hat_giong": args.hat_giong,
        "cat_doan": args.cat_doan,
        "ti_le_dat": ti_le,
        "theo_ngon_ngu": dict((ng, {
            "ky_tu_co": kho[ng]["ky_tu_co"],
            "ky_tu_dung": da_dung.get(ng, 0),
            "so_ban_ghi_ghi": so_ghi.get(ng, 0),
            "ti_le_that": da_dung.get(ng, 0) / float(sum(da_dung.values()) or 1),
        }) for ng in co_mat),
        "theo_xuat_xu": dem_nguon,
        "canh_bao_ngon_ngu": canh_bao_ngon_ngu,
        "tong_ban_ghi": tong_ghi,
        "tong_ky_tu": sum(da_dung.values()),
        "so_dong_bo_qua": len(loi_bo_qua),
        "vai_dong_bo_qua": [{"tep": t, "dong": d, "ly_do": ly}
                            for t, d, ly in loi_bo_qua[:50]],
        "ghi_chu": ("Truong ngon_ngu la LOI KHAI cua nguoi chay, khong phai ket qua nhan "
                    "dang. Xem canh_bao_ngon_ngu neu co."),
    }
    duong_bc = args.bao_cao or (os.path.splitext(duong_ra)[0] + ".bao-cao-tron.json")
    with open(duong_bc, "w", encoding="utf-8") as f:
        json.dump(bao_cao, f, ensure_ascii=False, indent=2)
    print("")
    print("  Bao cao: {}".format(duong_bc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
