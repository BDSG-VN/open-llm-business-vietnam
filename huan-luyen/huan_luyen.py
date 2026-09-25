#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tien huan luyen (pretrain) mo hinh BDSG.

=============================================================================
TEP NAY LAM GI
=============================================================================
Doc mot (hoac nhieu) tep JSONL dang {"text": "..."} , ma hoa thanh token bang tu
vung BDSG, DONG GOI lien tuc thanh cac khoi do dai co dinh, roi huan luyen mo
hinh du doan token ke tiep.

    python3 huan_luyen.py \\
        --du-lieu  ../du-lieu-da-tron/pretrain-vi.jsonl \\
        --cau-hinh cau-hinh/nho.json \\
        --tu-vung  tu-vung/ket-qua/tokenizer-vi-24576 \\
        --thu-muc-ra out/nho-tien-huan-luyen

=============================================================================
TEP NAY PHU THUOC VAO mo-hinh/
=============================================================================
Kien truc (CauHinhBDSG, BDSGChoNgonNgu) do NHOM KHAC viet, trong thu muc mo-hinh/
o goc kho. Bo huan luyen khong duoc sua vao do; cho nao hai ben lech quy uoc thi
BEN NAY nhuong.

Hop dong giua hai ben ghi day du o dau huan-luyen/chung.py. Ba dong quan trong
nhat:
  - BDSGChoNgonNgu(cfg).forward(ids, nhan) -> KetQuaMoHinh(.logits, .loss, ...)
  - MO HINH TU DICH NHAN BEN TRONG. Nen o day: nhan CUNG HINH DANG voi ids va
    chua CHINH chuoi token do, dat -100 o vi tri khong muon giam sat.
  - nhan = -100 nghia la bo qua vi tri do.

Sau khi co mo-hinh/, chay `python3 huan_luyen.py --tu-kiem-dich` TRUOC TIEN. No
kiem dung dieu tren bang cach bat mo hinh hoc thuoc mot lo nho roi doi chieu du
doan. Neu hai ben dich lech nhau mot buoc, loss van giam deu va bieu do van dep,
chi co ket qua sinh chu la hong — day la ho loi "hong ma khong bao", va no dat
hon nhieu neu chi phat hien sau khi da tra tien GPU.

=============================================================================
BA QUYET DINH CO CHU Y, GHI RA DE NGUOI SAU DUNG "SUA" NHAM
=============================================================================
0. NHAN THEO QUY UOC CUA mo-hinh/: nhan = chinh chuoi token, cung hinh dang voi
   ids. Mo hinh bo logit cuoi va bo nhan dau roi moi tinh mat mat. Khoi token o
   day vi vay dai dung max_seq_len, KHONG phai max_seq_len + 1 — ben goi khong
   con phai chua mot token du de dich nua.

1. DONG GOI (packing) CHU KHONG CAT CUT (truncation).
   Cach de lam hon la: moi doan van -> mot mau, dai qua thi cat bo phan duoi.
   Lam vay thi mot doan 4.000 token voi max_seq_len 512 se co 87% noi dung
   KHONG BAO GIO duoc hoc, va khong mot dong log nao noi ra.
   O day moi doan duoc noi duoi nhau thanh mot luong token lien tuc, chen mot
   token ket thuc giua hai doan, roi cat thanh cac khoi bang nhau. Khong bo mat
   chu nao (tru phan du cuoi cung ngan hon mot khoi).
   Cai gia phai tra, noi luon: mot khoi co the vat qua ranh gioi hai doan, nen
   mo hinh nhin thay ngu canh cua doan truoc khi doc doan sau. Token ket thuc la
   tin hieu de no hoc ra cho do la ranh gioi. Day la danh doi da biet va chap
   nhan, khong phai so sot.

2. BO LO CUOI CUNG neu no khong day batch.
   De so buoc toi uu tinh truoc duoc chinh xac — ma lich hoc suat cosine can
   biet TONG SO BUOC ngay tu dau. Mat nhieu nhat (batch - 1) khoi tren mot ky.

3. PHAN KIEM (validation) LAY O CUOI, KHONG LAY NGAU NHIEN.
   Hai khoi lien nhau thuong den tu cung mot van ban. Lay ngau nhien thi phan
   kiem gan nhu chac chan chua nua van ban ma phan hoc da nhin thay — loss kiem
   se dep hon su that, va cai dep do khong phat hien duoc bang mat.
"""

import argparse
import contextlib
import json
import math
import os
import sys

# Them thu muc chua tep nay vao dau sys.path de `import chung` chay duoc du goi
# tu bat cu thu muc nao. Day la cho hay hong khi chay script trong container:
# cwd luc do khong phai thu muc script.
THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

import chung  # noqa: E402


# ---------------------------------------------------------------------------
# Nap va dong goi du lieu
# ---------------------------------------------------------------------------
def dong_goi_token(cac_tep, tok, eos_id, gioi_han_doan=None, lo_ma_hoa=1000):
    """Doc cac tep JSONL {"text": ...}, ma hoa, noi thanh mot luong token phang.

    Tra ve (mang_token, thong_ke).

    Ma hoa theo LO chu khong tung doan mot: encode_batch cua thu vien tokenizers
    chay song song nhieu luong o tang Rust. Voi ngu lieu hang trieu doan, khac
    biet la hang chuc phut.
    """
    luong = chung.mang_token_rong()
    tk = {"so_doan": 0, "so_doan_rong": 0, "so_doan_thieu_truong": 0,
          "so_ky_tu": 0, "so_token": 0}

    dem = [0]

    def xa_lo(lo_van_ban):
        if not lo_van_ban:
            return
        ma = tok.encode_batch(lo_van_ban)
        for e in ma:
            luong.extend(e.ids)
            if eos_id is not None:
                luong.append(eos_id)
        dem[0] += len(lo_van_ban)

    lo = []
    for tep in cac_tep:
        for d in chung.doc_jsonl(tep):
            # Truong chinh la "text". Chap nhan "noi_dung" lam ten thay the vi
            # duong ong lam sach cua nhom khac (huan-luyen/du-lieu/lam_sach.py)
            # giu lai ten truong goc cua ban ghi. Chap nhan mot ten thay the re
            # hon nhieu so voi mot lan chay hong vi ten truong lech.
            vb = d.get("text")
            if vb is None:
                vb = d.get("noi_dung")
            if vb is None:
                tk["so_doan_thieu_truong"] += 1
                continue
            vb = str(vb)
            if not vb.strip():
                tk["so_doan_rong"] += 1
                continue
            tk["so_doan"] += 1
            tk["so_ky_tu"] += len(vb)
            lo.append(vb)
            if len(lo) >= lo_ma_hoa:
                xa_lo(lo)
                lo = []
                print("    ... da ma hoa {:,} doan, {:,} token".format(
                    dem[0], len(luong)))
            if gioi_han_doan and tk["so_doan"] >= gioi_han_doan:
                break
        if gioi_han_doan and tk["so_doan"] >= gioi_han_doan:
            break
    xa_lo(lo)

    tk["so_token"] = len(luong)
    return luong, tk


def chia_khoi(luong, do_dai_khoi):
    """Bien luong token phang thanh tensor (so_khoi, do_dai_khoi) khong sao chep.

    Khoi dai DUNG do_dai_khoi: mo-hinh/ tu dich nhan ben trong, nen ben goi
    khong phai chua them mot token de dich. Moi khoi dong gop do_dai_khoi - 1 vi
    tri co giam sat (vi tri dau khong co nhan de so).

    Tra ve (tensor, mang_goc). PHAI giu tham chieu toi mang_goc suot doi tensor:
    torch.frombuffer khong sao chep, hai ben dung chung bo nho.
    """
    chung.doi_hoi_torch()
    torch = chung.torch
    buoc = do_dai_khoi
    so_khoi = len(luong) // buoc
    if so_khoi < 1:
        raise SystemExit(
            "Khong du token de tao lay mot khoi.\n"
            "  co {:,} token, mot khoi can {:,} (= max_seq_len).\n"
            "  Giam --max-seq-len hoac dua them du lieu vao.".format(len(luong), buoc))
    phang = torch.frombuffer(luong, dtype=torch.int32)
    return phang[:so_khoi * buoc].view(so_khoi, buoc), luong


# ---------------------------------------------------------------------------
# Nhom tham so cho weight decay
# ---------------------------------------------------------------------------
def nhom_tham_so(mo_hinh, weight_decay):
    """Chia tham so lam hai nhom: co suy giam trong so va khong.

    GHI CONG: AdamW — suy giam trong so TACH ROI khoi buoc gradient — la cua
    Loshchilov & Hutter, "Decoupled Weight Decay Regularization",
    arXiv:1711.05101. torch.optim.AdamW cai dat no; ham nay chi chon xem
    tham so nao duoc ap.

    VI SAO KHONG AP WEIGHT DECAY LEN MOI THU: he so cua RMSNorm la mot vector
    nhan, gia tri hop ly cua no quanh 1. Keo no ve 0 lam lop chuan hoa mat tac
    dung — va lam cham mot cach am tham chu khong bao loi. Quy uoc chung la: chi
    ap suy giam cho tham so tu 2 chieu tro len (cac ma tran chieu, bang
    embedding), bo qua tham so 1 chieu (he so chuan hoa, do lech neu co).
    """
    co_giam, khong_giam = [], []
    for p in mo_hinh.parameters():
        if not p.requires_grad:
            continue
        (co_giam if p.dim() >= 2 else khong_giam).append(p)
    return [
        {"params": co_giam, "weight_decay": weight_decay},
        {"params": khong_giam, "weight_decay": 0.0},
    ]


# ---------------------------------------------------------------------------
# Tu kiem hop dong dich nhan
# ---------------------------------------------------------------------------
def tu_kiem_dich(mo_hinh, thiet_bi, vocab_size, so_buoc=300, hoc_suat=1e-3):
    """Bat mo hinh hoc thuoc MOT lo nho, roi kiem xem no du doan LECH MAY BUOC.

    CACH DO HOAT DONG:
      Sau khi hoc thuoc mot lo co dinh, argmax(logits[t]) phai bang nhan[t] o
      hau het vi tri. Neu mo-hinh/ tu dich them mot lan ben trong, no da hoc
      du doan nhan[t+1] o vi tri t; luc do ti le khop voi nhan[t] se thap, con
      ti le khop voi nhan DICH MOT BUOC se cao. Hai con so in ra canh nhau thi
      doc mot cai la biet ngay.

    VI SAO KHONG THE KIEM BANG MO HINH CHUA HOC: mo hinh moi khoi tao doan gan
    nhu ngau nhien, hai ti le deu quanh 1/vocab_size va khong phan biet duoc gi.
    Phai hoc thuoc mot lo truoc — dung ba tram buoc tren mot lo 4x32, chay vai
    giay tren CPU.
    """
    chung.doi_hoi_torch()
    torch = chung.torch
    print("")
    print("TU KIEM HOP DONG DICH NHAN")
    print("-" * 74)
    torch.manual_seed(7)
    B, T = 4, 32
    ids = torch.randint(0, vocab_size, (B, T), device=thiet_bi).long()
    nhan = ids

    mo_hinh.train()
    bo_toi_uu = torch.optim.AdamW(mo_hinh.parameters(), lr=hoc_suat)
    for _ in range(so_buoc):
        bo_toi_uu.zero_grad(set_to_none=True)
        _, loss = chung.goi_mo_hinh(mo_hinh, ids, nhan)
        loss.backward()
        bo_toi_uu.step()

    mo_hinh.eval()
    with torch.no_grad():
        logits, loss = chung.goi_mo_hinh(mo_hinh, ids, nhan)
    du_doan = logits.argmax(dim=-1)

    # Dung: o vi tri t, mo hinh phai doan token KE TIEP, tuc ids[t+1].
    khop_ke_tiep = (du_doan[:, :-1] == ids[:, 1:]).float().mean().item()
    # Neu ben goi VA mo hinh cung dich, mo hinh se doan token CACH HAI: ids[t+2].
    khop_cach_hai = (du_doan[:, :-2] == ids[:, 2:]).float().mean().item()

    chung.in_bang([
        ("loss sau khi hoc thuoc", "{:.4f}".format(loss.item())),
        ("khop voi token KE TIEP  ids[t+1]", "{:.1%}".format(khop_ke_tiep)),
        ("khop voi token CACH HAI ids[t+2]", "{:.1%}".format(khop_cach_hai)),
    ])
    print("-" * 74)
    if khop_ke_tiep >= 0.9:
        print("DAT. Mo hinh du doan dung token ke tiep — le mot buoc khop giua hai ben.")
        return 0
    if khop_cach_hai >= 0.9:
        print("HONG. Mo hinh dang du doan token CACH HAI chu khong phai ke tiep:")
        print("  CHUOI BI DICH HAI LAN — ca ben goi lan mo-hinh/ deu dich.")
        print("  Bo huan luyen nay KHONG dich (nhan = chinh chuoi token). Neu bai")
        print("  nay bao HONG thi mo-hinh/ vua doi quy uoc: no khong con tu dich,")
        print("  hoac no dich hai lan. Xem hop dong o dau huan-luyen/chung.py roi")
        print("  sua DUNG MOT ben, dung sua ca hai.")
        return 1
    print("KHONG KET LUAN DUOC. Ca hai ti le deu thap:")
    print("  mo hinh chua hoc thuoc noi lo nho nay sau {} buoc.".format(so_buoc))
    print("  Co the la loi kien truc, hoc suat, hoac khoi tao. Tang --tu-kiem-buoc")
    print("  roi thu lai; neu van vay thi van de nam trong mo-hinh/, khong phai o day.")
    return 2


# ---------------------------------------------------------------------------
# Danh gia tren phan kiem
# ---------------------------------------------------------------------------
def do_phan_kiem(mo_hinh, du_lieu, chi_so, batch, thiet_bi, so_lo_toi_da=50):
    """Tra ve loss trung binh tren phan kiem (trung binh theo SO TOKEN)."""
    torch = chung.torch
    mo_hinh.eval()
    tong_loss = 0.0
    tong_token = 0
    with torch.no_grad():
        for i in range(0, min(len(chi_so), so_lo_toi_da * batch), batch):
            lo = chi_so[i:i + batch]
            if len(lo) < batch:
                break
            ids = du_lieu[lo].to(thiet_bi).long()
            _, loss = chung.goi_mo_hinh(mo_hinh, ids, ids)
            n = chung.dem_token_co_nhan(ids)
            tong_loss += loss.item() * n
            tong_token += n
    mo_hinh.train()
    if tong_token == 0:
        return None
    return tong_loss / tong_token


# ---------------------------------------------------------------------------
# Tham so dong lenh
# ---------------------------------------------------------------------------
def doc_tham_so(argv=None):
    p = argparse.ArgumentParser(
        description="Tien huan luyen mo hinh BDSG tu JSONL {'text': ...}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    n = p.add_argument_group("dau vao")
    n.add_argument("--du-lieu", help="tep .jsonl hoac thu muc chua cac tep .jsonl")
    n.add_argument("--cau-hinh", default=os.path.join(THU_MUC, "cau-hinh", "nho.json"),
                   help="tep .json cau hinh kien truc")
    n.add_argument("--tu-vung", help="tokenizer.json, hoac thu muc chua no")
    n.add_argument("--thu-muc-mo-hinh",
                   default=os.path.abspath(os.path.join(THU_MUC, "..", "mo-hinh")),
                   help="thu muc chua CauHinhBDSG va lop mo hinh (BDSGChoNgonNgu)")
    n.add_argument("--gioi-han-doan", type=int, default=0,
                   help="chi doc bay nhieu doan dau (0 = het); de chay thu nhanh")

    r = p.add_argument_group("dau ra")
    r.add_argument("--thu-muc-ra", default=os.path.join(THU_MUC, "out"),
                   help="noi ghi diem dung va nhat ky")
    r.add_argument("--ten", default="", help="ten lan chay (mac dinh: lay tu ten cau hinh)")

    h = p.add_argument_group("hinh dang lo")
    h.add_argument("--max-seq-len", type=int, default=512,
                   help="do dai mot khoi token")
    h.add_argument("--batch", type=int, default=8, help="so khoi moi lo nho")
    h.add_argument("--tich-luy", type=int, default=1,
                   help="so lo nho cong don truoc mot buoc toi uu (lo hieu dung = batch * tich-luy)")

    o = p.add_argument_group("toi uu")
    o.add_argument("--ky", type=int, default=1, help="so lan duyet het du lieu")
    o.add_argument("--hoc-suat", type=float, default=3e-4, help="hoc suat dinh")
    o.add_argument("--ti-le-hoc-suat-cuoi", type=float, default=0.1,
                   help="hoc suat cuoi lich = ti le nay * hoc suat dinh")
    o.add_argument("--ti-le-ham-nong", type=float, default=0.02,
                   help="phan tram tong so buoc dung de ham nong")
    o.add_argument("--cat-gradient", type=float, default=1.0,
                   help="chuan L2 toi da cua gradient (0 = khong cat)")
    o.add_argument("--weight-decay", type=float, default=0.1)
    o.add_argument("--beta1", type=float, default=0.9)
    o.add_argument("--beta2", type=float, default=0.95)
    o.add_argument("--so-buoc-toi-da", type=int, default=0,
                   help="dung som sau bay nhieu buoc toi uu (0 = khong gioi han)")

    m = p.add_argument_group("may")
    m.add_argument("--thiet-bi", default="tu-dong",
                   help="tu-dong | cpu | cuda | cuda:0 | mps")
    m.add_argument("--amp", action="store_true",
                   help="bat autocast (chi co tac dung tren CUDA; xem chung.kieu_du_lieu_tu_dong)")
    m.add_argument("--hat-giong", type=int, default=1234)

    k = p.add_argument_group("theo doi va diem dung")
    k.add_argument("--in-moi", type=int, default=10, help="in nhat ky moi bay nhieu buoc")
    k.add_argument("--luu-moi", type=int, default=500, help="luu diem dung moi bay nhieu buoc")
    k.add_argument("--ti-le-kiem", type=float, default=0.01,
                   help="ti le khoi giu lai lam phan kiem (0 = khong giu)")
    k.add_argument("--kiem-moi", type=int, default=500, help="do phan kiem moi bay nhieu buoc")
    k.add_argument("--tiep-tuc", action="store_true",
                   help="tiep tuc tu diem dung moi nhat trong --thu-muc-ra")

    t = p.add_argument_group("tu kiem")
    t.add_argument("--tu-kiem-dich", action="store_true",
                   help="kiem hop dong dich nhan voi mo-hinh/, roi thoat")
    t.add_argument("--tu-kiem-buoc", type=int, default=300,
                   help="so buoc hoc thuoc trong bai tu kiem")

    return p.parse_args(argv)


# ---------------------------------------------------------------------------
def main(argv=None):
    args = doc_tham_so(argv)
    chung.doi_hoi_torch()
    torch = chung.torch

    chung.dat_hat_giong(args.hat_giong)
    thiet_bi = chung.chon_thiet_bi(args.thiet_bi)

    cfg, ghi_chu = chung.nap_cau_hinh(args.cau_hinh)
    CauHinhBDSG, LopMoHinh = chung.nap_kien_truc(args.thu_muc_mo_hinh)

    print("=" * 74)
    print("  TIEN HUAN LUYEN — BDSG")
    print("=" * 74)
    chung.in_bang([
        ("thiet bi", chung.mo_ta_thiet_bi(thiet_bi)),
        ("cau hinh", args.cau_hinh),
        ("kien truc", args.thu_muc_mo_hinh),
    ])

    # --- bai tu kiem chay truoc, khong can du lieu ---
    if args.tu_kiem_dich:
        mo_hinh = LopMoHinh(chung.dung_cau_hinh(CauHinhBDSG, cfg)).to(thiet_bi)
        return tu_kiem_dich(mo_hinh, thiet_bi, cfg["vocab_size"],
                            so_buoc=args.tu_kiem_buoc)

    if not args.du_lieu:
        raise SystemExit("Thieu --du-lieu (tep .jsonl hoac thu muc chua chung).")
    if not args.tu_vung:
        raise SystemExit("Thieu --tu-vung (tokenizer.json hoac thu muc chua no).")

    # --- tu vung ---
    tok = chung.nap_tu_vung(args.tu_vung)
    chung.kiem_tu_vung(tok, cfg, args.tu_vung)
    # Dau ngan cach giua hai van ban khi tien huan luyen la <|het-van-ban|>, KHONG
    # phai <|dong-luot|>. Hai token nay lam hai viec khac nhau va khong thay nhau
    # duoc: <|dong-luot|> dong mot LUOT NOI trong hoi thoai (dung o tinh_chinh.py),
    # con <|het-van-ban|> ngan hai VAN BAN doc lap. Dung nham thi mo hinh hoc rang
    # het mot doan tai lieu la het mot luot noi — va luc tra loi no se dung som.
    # (Vai tro tung token do huan-luyen/tu-vung/huan_luyen_tu_vung.py dat ra, muc 2.)
    ngan_cach = "<|het-van-ban|>"
    eos_id = chung.id_token_dac_biet(tok, ngan_cach)
    if eos_id is None:
        eos_id = cfg.get("pad_token_id", 0)
        print("  [canh bao] khong tim thay {} trong tu vung; dung id={} tu cau hinh. "
              "Kiem lai --tu-vung co dung la tu vung BDSG khong.".format(ngan_cach, eos_id))

    # --- du lieu ---
    cac_tep = chung.liet_ke_tep(args.du_lieu)
    print("")
    print("  Nap du lieu tu {} tep...".format(len(cac_tep)))
    luong, tk = dong_goi_token(cac_tep, tok, eos_id,
                               gioi_han_doan=args.gioi_han_doan or None)
    if tk["so_token"] == 0:
        raise SystemExit("Khong ma hoa duoc token nao. Kiem lai truong 'text' trong JSONL.")

    du_lieu, _giu_mang = chia_khoi(luong, args.max_seq_len)
    so_khoi = du_lieu.size(0)
    so_kiem = int(so_khoi * args.ti_le_kiem)
    # Phan kiem lay o CUOI, khong lay ngau nhien — xem quyet dinh 3 o dau tep.
    chi_so_hoc = list(range(so_khoi - so_kiem))
    chi_so_kiem = list(range(so_khoi - so_kiem, so_khoi))

    ky_tu_moi_token = (tk["so_ky_tu"] / float(tk["so_token"])) if tk["so_token"] else 0.0
    chung.in_bang([
        ("doan doc duoc", "{:,}".format(tk["so_doan"])),
        ("doan bo (rong / thieu truong)",
         "{:,} / {:,}".format(tk["so_doan_rong"], tk["so_doan_thieu_truong"])),
        ("ky tu", "{:,}".format(tk["so_ky_tu"])),
        ("token", "{:,}  ({:.2f} ky tu/token — DO DUOC tren chinh ngu lieu nay)".format(
            tk["so_token"], ky_tu_moi_token)),
        ("khoi {} token".format(args.max_seq_len), "{:,}".format(so_khoi)),
        ("khoi hoc / khoi kiem", "{:,} / {:,}".format(len(chi_so_hoc), len(chi_so_kiem))),
        ("token bo o phan du cuoi",
         "{:,}".format(tk["so_token"] - so_khoi * args.max_seq_len)),
    ])
    if not chi_so_hoc:
        raise SystemExit("Khong con khoi nao de hoc sau khi tach phan kiem.")

    # --- so buoc ---
    so_lo_moi_ky = len(chi_so_hoc) // args.batch          # bo lo cuoi neu khong day
    so_buoc_moi_ky = so_lo_moi_ky // args.tich_luy
    if so_buoc_moi_ky < 1:
        raise SystemExit(
            "Khong du du lieu cho lay mot buoc toi uu.\n"
            "  co {:,} khoi hoc; mot buoc can batch*tich_luy = {} khoi.\n"
            "  Giam --batch hoac --tich-luy, hoac giam --max-seq-len.".format(
                len(chi_so_hoc), args.batch * args.tich_luy))
    tong_buoc = so_buoc_moi_ky * args.ky
    if args.so_buoc_toi_da:
        tong_buoc = min(tong_buoc, args.so_buoc_toi_da)
    buoc_ham_nong = max(1, int(tong_buoc * args.ti_le_ham_nong))
    token_moi_buoc = args.batch * args.tich_luy * args.max_seq_len

    # --- mo hinh ---
    mo_hinh = LopMoHinh(chung.dung_cau_hinh(CauHinhBDSG, cfg)).to(thiet_bi)
    so_tham_so = sum(p.numel() for p in mo_hinh.parameters())
    so_tham_so_hoc = sum(p.numel() for p in mo_hinh.parameters() if p.requires_grad)

    bo_toi_uu = torch.optim.AdamW(
        nhom_tham_so(mo_hinh, args.weight_decay),
        lr=args.hoc_suat, betas=(args.beta1, args.beta2))

    dung_amp, kieu_amp, dung_scaler = chung.kieu_du_lieu_tu_dong(thiet_bi, args.amp)
    scaler = torch.amp.GradScaler(thiet_bi.type) if dung_scaler else None

    print("")
    chung.in_bang([
        ("tham so (DEM DUOC tren mo hinh vua dung)",
         "{:,}  = {:.2f}M".format(so_tham_so, so_tham_so / 1e6)),
        ("tham so hoc duoc", "{:,}".format(so_tham_so_hoc)),
        ("lo hieu dung", "{} x {} = {} khoi = {:,} token/buoc".format(
            args.batch, args.tich_luy, args.batch * args.tich_luy, token_moi_buoc)),
        ("buoc moi ky / tong buoc", "{:,} / {:,}".format(so_buoc_moi_ky, tong_buoc)),
        ("buoc ham nong", "{:,}".format(buoc_ham_nong)),
        ("autocast", "{} {}".format(dung_amp, kieu_amp if dung_amp else "")),
    ])
    print("")
    print("  So tham so DEM DUOC o tren doi chieu voi so TINH RA trong cau hinh:")
    tinh_ra = None
    if ghi_chu and isinstance(ghi_chu, dict):
        tinh_ra = (ghi_chu.get("tham_so") or {}).get("tong")
    if tinh_ra:
        lech = so_tham_so - tinh_ra
        print("    tinh ra {:,} | dem duoc {:,} | lech {:+,}{}".format(
            tinh_ra, so_tham_so, lech,
            "  <== PHAI BANG 0. Lech nghia la mot ben hieu sai kien truc."
            if lech else "  OK"))
    else:
        print("    cau hinh khong ghi so tinh ra — khong doi chieu duoc. Chay")
        print("    `python3 cau-hinh/tinh_tham_so.py <cau hinh>` de co con so do.")

    # --- thu muc ra, diem dung ---
    ten = args.ten or os.path.splitext(os.path.basename(args.cau_hinh))[0]
    thu_muc_ra = os.path.join(args.thu_muc_ra, "tien-huan-luyen-" + ten)
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
        print("  Da du {:,} buoc. Khong con gi de chay.".format(tong_buoc))
        return 0

    # --- vong huan luyen ---
    dong_ho = chung.DongHo()
    mo_hinh.train()
    nhat_ky = open(duong_nhat_ky, "a", encoding="utf-8")
    ngat_giua_chung = False

    print("")
    print("-" * 74)
    try:
        for ky in range(args.ky):
            # Bo qua nguyen ky da lam xong khi tiep tuc tu diem dung.
            if (ky + 1) * so_buoc_moi_ky <= buoc_toan_cuc:
                continue
            thu_tu = chung.thu_tu_lo(len(chi_so_hoc), args.hat_giong, ky)
            buoc_trong_ky = buoc_toan_cuc - ky * so_buoc_moi_ky
            if buoc_trong_ky < 0:
                buoc_trong_ky = 0
            # Nhay thang toi vi tri dang do trong ky: moi buoc an batch*tich_luy khoi.
            vi_tri = buoc_trong_ky * args.batch * args.tich_luy

            while buoc_toan_cuc < tong_buoc and vi_tri + args.batch * args.tich_luy <= len(thu_tu):
                bo_toi_uu.zero_grad(set_to_none=True)
                he_so = chung.he_so_hoc_suat(
                    buoc_toan_cuc, tong_buoc, buoc_ham_nong, args.ti_le_hoc_suat_cuoi)
                hoc_suat = args.hoc_suat * he_so
                chung.dat_hoc_suat(bo_toi_uu, hoc_suat)

                tong_loss_buoc = 0.0
                token_buoc = 0
                for _ in range(args.tich_luy):
                    lo = [chi_so_hoc[j] for j in thu_tu[vi_tri:vi_tri + args.batch]]
                    vi_tri += args.batch
                    # nhan la CHINH chuoi token (khong dich): mo-hinh/ dich ben
                    # trong. Dich them o day la dich hai lan — xem chung.py.
                    ids = du_lieu[lo].to(thiet_bi).long()
                    nhan = ids

                    ngu_canh = (torch.autocast(thiet_bi.type, dtype=kieu_amp)
                                if dung_amp else contextlib.nullcontext())
                    with ngu_canh:
                        _, loss = chung.goi_mo_hinh(mo_hinh, ids, nhan)
                    # Chia cho tich_luy: cong don gradient cua N lo nho phai cho
                    # ra dung gradient cua MOT lo lon gap N lan, khong phai gap N.
                    loss_chia = loss / args.tich_luy
                    if scaler is not None:
                        scaler.scale(loss_chia).backward()
                    else:
                        loss_chia.backward()
                    tong_loss_buoc += loss.item()
                    token_buoc += ids.numel()

                # Cat gradient theo chuan L2 toan cuc — Pascanu, Mikolov & Bengio,
                # "On the difficulty of training Recurrent Neural Networks",
                # arXiv:1211.5063, muc 3.2.
                if args.cat_gradient > 0:
                    if scaler is not None:
                        # Phai bo he so phong dai TRUOC khi cat, neu khong nguong
                        # cat dang ap len gradient da nhan vai nghin lan.
                        scaler.unscale_(bo_toi_uu)
                    torch.nn.utils.clip_grad_norm_(mo_hinh.parameters(), args.cat_gradient)
                if scaler is not None:
                    scaler.step(bo_toi_uu)
                    scaler.update()
                else:
                    bo_toi_uu.step()

                buoc_toan_cuc += 1
                dong_ho.ghi(token_buoc)
                loss_tb = tong_loss_buoc / args.tich_luy

                if buoc_toan_cuc % args.in_moi == 0 or buoc_toan_cuc == 1:
                    con_lai = dong_ho.con_lai(buoc_toan_cuc, tong_buoc)
                    print("  buoc {:>7,}/{:,} | ky {}/{} | loss {:.4f} | ppl {:>11} | "
                          "lr {:.2e} | {:>9,.0f} token/giay | con {}".format(
                              buoc_toan_cuc, tong_buoc, ky + 1, args.ky, loss_tb,
                              chung.dinh_dang_ppl(loss_tb), hoc_suat,
                              dong_ho.toc_do(), chung.dinh_dang_giay(con_lai)))
                    nhat_ky.write(json.dumps({
                        "buoc": buoc_toan_cuc, "ky": ky + 1, "loss": loss_tb,
                        "lr": hoc_suat, "token_giay": dong_ho.toc_do(),
                        "tong_token": dong_ho.tong_token,
                    }, ensure_ascii=False) + "\n")
                    nhat_ky.flush()

                if chi_so_kiem and args.kiem_moi > 0 and buoc_toan_cuc % args.kiem_moi == 0:
                    loss_kiem = do_phan_kiem(mo_hinh, du_lieu, chi_so_kiem,
                                             args.batch, thiet_bi)
                    if loss_kiem is not None:
                        print("  >>> phan kiem: loss {:.4f} | ppl {}".format(
                            loss_kiem, chung.dinh_dang_ppl(loss_kiem)))
                        nhat_ky.write(json.dumps({
                            "buoc": buoc_toan_cuc, "loss_kiem": loss_kiem},
                            ensure_ascii=False) + "\n")
                        nhat_ky.flush()

                if args.luu_moi > 0 and buoc_toan_cuc % args.luu_moi == 0:
                    chung.luu_diem_dung(
                        duong_diem_dung, mo_hinh, bo_toi_uu,
                        {"buoc_toan_cuc": buoc_toan_cuc, "ky": ky,
                         "tong_buoc": tong_buoc, "loai": "tien-huan-luyen"},
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
             "loai": "tien-huan-luyen"},
            cfg, scaler)
        nhat_ky.close()

    print("-" * 74)
    chung.in_bang([
        ("buoc da chay", "{:,}/{:,}".format(buoc_toan_cuc, tong_buoc)),
        ("token da hoc", "{:,}".format(dong_ho.tong_token)),
        ("thoi gian", chung.dinh_dang_giay(dong_ho.da_troi())),
        ("toc do cuoi", "{:,.0f} token/giay".format(dong_ho.toc_do())),
        ("diem dung", duong_diem_dung),
        ("nhat ky", duong_nhat_ky),
    ])
    if ngat_giua_chung:
        print("  Bi ngat giua chung. Chay lai cung lenh kem --tiep-tuc de di tiep.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
