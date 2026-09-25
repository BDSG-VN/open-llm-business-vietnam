#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tinh so tham so cua mot cau hinh BDSG ma KHONG can cai torch.

=============================================================================
VI SAO CO TEP NAY
=============================================================================
Cac con so "36,18M", "119,56M", "295,75M" ghi trong cac tep .json canh day la so
TINH RA, khong phai so DO tren mo hinh that. Ngay 26/09/2026 BDSG chua huan luyen
trong so nao, nen khong co mo hinh de dem. Mot con so tinh ra ma khong kem cach
tinh thi khong ai kiem chung lai duoc — nen cach tinh nam o day, chay duoc.

Tep nay KHONG tham chieu den kho ma nao khac. No dem theo kien truc ma BDSG
chon, va kien truc do lay tu KY THUAT DA CONG BO trong cac bai bao:

  RMSNorm            arXiv:1910.07467   (Zhang & Sennrich, 2019)
  RoPE               arXiv:2104.09864   (Su et al., 2021)
  GQA                arXiv:2305.13245   (Ainslie et al., 2023)
  SwiGLU             arXiv:2002.05202   (Shazeer, 2020)
  pre-norm           arXiv:2002.04745   (Xiong et al., 2020)
  buoc embedding     arXiv:1608.05859   (Press & Wolf, 2016) — tie_word_embeddings

Ten cac truong cau hinh (hidden_size, num_hidden_layers, ...) theo CHUAN
TRANSFORMERS: day la quy uoc chung cua ca he sinh thai (Llama, Mistral, Qwen deu
dung ten nay), khong phai cua rieng du an nao. Giu dung ten la dieu kien de mo
hinh BDSG nap duoc o noi khac ma khong phai viet lop chuyen doi.

=============================================================================
CACH DEM — TUNG DONG MOT, KHONG DOAN
=============================================================================
Mo hinh la decoder-only, pre-norm, khong dung bias o cac lop tuyen tinh
(chuan tu dong Llama tro di: bias o q/k/v/o va o FFN khong cai thien gi do duoc
o quy mo nay, ma them tham so va them mot duong lech).

  embedding      V * h
                 Dem MOT LAN neu tie_word_embeddings = true: luc do lop dau ra
                 (lm_head) dung CHUNG doi tuong Parameter voi bang embedding, va
                 nn.Module.parameters() loc trung nen no chi xuat hien mot lan.
                 Neu tie = false thi cong them V * h nua cho lm_head.

  moi lop:
    q_proj       h * (num_attention_heads   * head_dim)
    k_proj       h * (num_key_value_heads   * head_dim)     <- GQA: kv it hon q
    v_proj       h * (num_key_value_heads   * head_dim)
    o_proj       (num_attention_heads * head_dim) * h
    2 RMSNorm    2 * h
                 RMSNorm chi co MOT vector he so nhan, khong co do lech (beta) —
                 do la khac biet voi LayerNorm, va la ly do no re hon.
                 Hai cai: mot truoc attention, mot truoc FFN (pre-norm).
    FFN SwiGLU   3 * h * intermediate_size
                 Ba ma tran: gate, up, down. SwiGLU can BA chu khong phai hai
                 nhu FFN co dien — do la ly do intermediate_size thuong lay
                 khoang 8/3 * h chu khong phai 4 * h, de tong tham so FFN giu
                 nguyen muc 8 * h^2.

  cuoi cung      h        (mot RMSNorm truoc lop dau ra)

  KHONG dem:
    - bang cos/sin cua RoPE. No la dai luong TINH RA tu vi tri, khong hoc, nen
      dang le phai dang ky la buffer (persistent=False) va khong nam trong tep
      trong so. No VAN chiem RAM luc chay — xem phan "bo nho RoPE" ben duoi.
    - mat na nhan qua (causal mask), cung la buffer.

  GIA DINH PHAI NOI RO: cong thuc nay gia dinh kien truc KHONG dung QK-norm
  (chuan hoa rieng cho q va k truoc khi tinh diem chu y). Neu mo-hinh/ ma nhom
  kia dang viet co them QK-norm thi phai cong them 2 * head_dim moi lop. Voi
  cau hinh "nho" do la 128 tham so tren 36 trieu — khong doi con so lam tron,
  nhung ghi ra de khong ai phai doan.

=============================================================================
SO TINH RA vs SO DEM DUOC — DOI CHIEU THE NAO
=============================================================================
Khi mo-hinh/ da co ma that, chay:

    python3 -c "
    import importlib.util, sys, json
    # Thu muc ten la 'mo-hinh' co gach ngang nen khong import thang duoc; phai nap
    # theo duong dan tep. Lop mo hinh ten that la BDSGChoNgonNgu (doc 26/09/2026).
    spec = importlib.util.spec_from_file_location(
        'mo_hinh', 'mo-hinh/__init__.py', submodule_search_locations=['mo-hinh'])
    mh = importlib.util.module_from_spec(spec); sys.modules['mo_hinh'] = mh
    spec.loader.exec_module(mh)
    cfg = json.load(open('huan-luyen/cau-hinh/nho.json')); cfg.pop('bdsg', None)
    m = mh.BDSGChoNgonNgu(mh.CauHinhBDSG(**cfg))
    print(sum(p.numel() for p in m.parameters()))
    "
(chay tu GOC KHO. Lenh nay da chay that 26/09/2026 — ket qua o muc ngay duoi.)

roi so voi cot TONG o day. Hai so PHAI khop tuyet doi, khong phai khop xap xi:
ca hai deu la phep dem so nguyen tren cung mot kien truc. Lech du mot tham so
nghia la mot ben hieu sai kien truc — thuong la chuyen buoc embedding (tie) hoac
chuyen bias. Lech thi SUA, dung lam tron cho qua.

DA DOI CHIEU THAT, 26/09/2026 — ket qua:
    nho.json  tinh ra 36.184.576  ·  dem duoc 36.184.576  ·  lech 0
    vua.json  tinh ra 119.563.008 ·  dem duoc 119.563.008 ·  lech 0
    lon.json  tinh ra 295.748.608 ·  dem duoc 295.748.608 ·  lech 0
CauHinhBDSG.so_tham_so() cua mo-hinh/ — mot phep dem thu ba, viet doc lap — cung
ra dung cac so ay, khop den tung phan (embedding 12.582.912 · mot lop 2.950.144 ·
norm cuoi 512 cho nho.json).

Luu y: sum(p.numel() for p in m.parameters()) da tu loc trung khi tie=True, vi
tap parameters() duoc de-duplicate theo dinh danh doi tuong.

=============================================================================
CHAY
=============================================================================
    python3 tinh_tham_so.py                     # tinh het cac .json trong thu muc nay
    python3 tinh_tham_so.py nho.json lon.json   # tinh rieng
    python3 tinh_tham_so.py --tu-kiem           # kiem cong thuc bang so hoc tay
"""

import argparse
import json
import math
import os
import sys

THU_MUC = os.path.dirname(os.path.abspath(__file__))

# DON VI — doc ky, day la cho hai tep trong kho tung noi hai so khac nhau.
# Moi con so bo nho o tep nay tinh theo LUY THUA 2: 1 MiB = 1024^2 byte,
# 1 GiB = 1024^3. Ly do: cau hoi thuc te la "co vua RAM/VRAM khong", ma RAM va
# VRAM deu duoc dem theo luy thua 2.
# CANH BAO KHI DOI CHIEU: mo-hinh/cau_hinh.py co ham bo_nho_trong_so_MB() va
# bo_nho_kv_cache_MB() tinh theo MB THAP PHAN (1 MB = 1e6 byte). Cung mot mo hinh
# se ra hai con so lech nhau 4,86% — khong phai hai ben bat dong, ma la hai don vi.
# Vi du nho.json: 69,0 MiB = 72,4 MB thap phan. Cot "tai ve" ben duoi in ca hai,
# vi kich thuoc tep tai ve thi the gioi quen doc theo MB thap phan.
MiB = 1024.0 * 1024.0
GiB = 1024.0 * 1024.0 * 1024.0
KiB = 1024.0
MB_THAP_PHAN = 1e6


def intermediate_mac_dinh(hidden_size, boi_so=128):
    """Gia tri intermediate_size mac dinh khi cau hinh khong ghi ro.

    8/3 * h roi lam tron LEN theo boi so 128. Vi sao 8/3: FFN co dien co hai ma
    tran voi kich thuoc trung gian 4h, tong 8 * h^2 tham so. SwiGLU can ba ma
    tran, nen de giu nguyen ngan sach 8 * h^2 thi kich thuoc trung gian phai la
    8h/3. Vi sao lam tron len boi so 128: cac nhan GEMM tren GPU chia khoi theo
    boi so cua 64/128; mot chieu le lam giam hieu suat ma khong doi ket qua.
    """
    return int(math.ceil(hidden_size * 8.0 / 3.0 / boi_so) * boi_so)


def doc_cau_hinh(duong_dan):
    with open(duong_dan, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Khoa "bdsg" la ghi chu cua BDSG (muc dich, cach tinh, canh bao), KHONG phai
    # tham so kien truc. Ai nap cau hinh nay vao CauHinhBDSG(**cfg) phai bo khoa
    # nay truoc, neu khong se nhan TypeError ve tham so la.
    cfg.pop("bdsg", None)
    return cfg


def tinh(cfg):
    """Dem tham so tu mot dict cau hinh. Tra ve dict cac phan da tach rieng."""
    h = cfg["hidden_size"]
    L = cfg["num_hidden_layers"]
    V = cfg["vocab_size"]
    n_q = cfg["num_attention_heads"]
    n_kv = cfg.get("num_key_value_heads", n_q)
    hd = cfg.get("head_dim", h // n_q)
    inter = cfg.get("intermediate_size", intermediate_mac_dinh(h))
    tie = bool(cfg.get("tie_word_embeddings", True))
    ctx = cfg.get("max_position_embeddings", 2048)

    embedding = V * h
    lm_head = 0 if tie else V * h

    attn = (
        h * (n_q * hd)        # q_proj
        + h * (n_kv * hd)     # k_proj
        + h * (n_kv * hd)     # v_proj
        + (n_q * hd) * h      # o_proj
    )
    norm_lop = 2 * h
    ffn = 3 * h * inter

    mot_lop = attn + norm_lop + ffn
    tong = embedding + lm_head + L * mot_lop + h

    # Bo dem KV luc suy luan, MOI TOKEN, o fp16:
    #   2 (K va V) * so_lop * num_key_value_heads * head_dim * 2 byte
    # Day la cho GQA tra cong: n_kv nho hon n_q bao nhieu lan thi bo dem nho di
    # bay nhieu lan. Voi ngu canh dai, bo dem nay lon hon ca trong so.
    kv_moi_token = 2 * L * n_kv * hd * 2

    # Bang cos/sin cua RoPE dung luc chay: hai tensor float32 co (ctx, head_dim/2)
    # neu luu dang goc, hoac (ctx, head_dim) neu luu ca hai nua da nhan doi.
    # Tinh theo truong hop ton kem hon (ctx * head_dim moi bang) de khong hua hep.
    rope_byte = 2 * ctx * hd * 4

    return {
        "tong": tong,
        "embedding": embedding,
        "lm_head": lm_head,
        "mot_lop": mot_lop,
        "attn_mot_lop": attn,
        "ffn_mot_lop": ffn,
        "norm_mot_lop": norm_lop,
        "tong_cac_lop": L * mot_lop,
        "intermediate_size": inter,
        "head_dim": hd,
        "num_key_value_heads": n_kv,
        "max_position_embeddings": ctx,
        "ti_le_embedding": embedding / float(tong),
        "kv_moi_token_byte": kv_moi_token,
        "rope_byte": rope_byte,
    }


def bo_nho(tong_tham_so):
    """Bo nho tinh tu so tham so.

    DON VI: MiB/GiB (luy thua 2) — xem khoi chu thich canh hang so o dau tep.
    Khoa `fp16_MB_thap_phan` la CUNG mot luong byte do, doi sang MB thap phan
    (1e6 byte), vi do la don vi ma kich thuoc tep tai ve thuong duoc doc.

    AdamW giu bon thu cho MOI tham so khi huan luyen o fp32:
        ban trong so fp32        4 byte
        gradient        fp32     4 byte
        moment bac mot (m)       4 byte
        moment bac hai (v)       4 byte
                                = 16 byte / tham so
    Con so 16 byte nay la SAN, KHONG phai tran: no CHUA tinh activation. Activation
    phu thuoc batch_size, do dai chuoi va viec co bat gradient checkpointing hay
    khong — khong tinh truoc duoc o day, va cung KHONG duoc doan bua.
    """
    return {
        "fp16_MiB": tong_tham_so * 2 / MiB,
        "fp32_MiB": tong_tham_so * 4 / MiB,
        "adamw_fp32_GiB": tong_tham_so * 16 / GiB,
        "fp16_MB_thap_phan": tong_tham_so * 2 / MB_THAP_PHAN,
    }


def in_ket_qua(ten, cfg, kq):
    bn = bo_nho(kq["tong"])
    print("")
    print("=" * 74)
    print("  {}".format(ten))
    print("=" * 74)
    print("  hidden={}  lop={}  q_head={}  kv_head={}  head_dim={}  inter={}".format(
        cfg["hidden_size"], cfg["num_hidden_layers"], cfg["num_attention_heads"],
        kq["num_key_value_heads"], kq["head_dim"], kq["intermediate_size"]))
    print("  vocab={}  ctx={}  tie_word_embeddings={}".format(
        cfg["vocab_size"], kq["max_position_embeddings"],
        bool(cfg.get("tie_word_embeddings", True))))
    print("  " + "-" * 70)
    print("  embedding            {:>14,}   ({:.1%} tong so tham so)".format(
        kq["embedding"], kq["ti_le_embedding"]))
    if kq["lm_head"]:
        print("  lm_head (khong buoc) {:>14,}".format(kq["lm_head"]))
    print("  mot lop              {:>14,}   (attn {:,} + norm {:,} + ffn {:,})".format(
        kq["mot_lop"], kq["attn_mot_lop"], kq["norm_mot_lop"], kq["ffn_mot_lop"]))
    print("  {} lop               {:>14,}".format(
        str(cfg["num_hidden_layers"]).rjust(2), kq["tong_cac_lop"]))
    print("  " + "-" * 70)
    print("  TONG                 {:>14,}   =  {:.2f}M".format(
        kq["tong"], kq["tong"] / 1e6))
    print("  " + "-" * 70)
    print("  Trong so fp16                       {:>9.1f} MiB  (= {:.1f} MB thap phan)".format(
        bn["fp16_MiB"], bn["fp16_MB_thap_phan"]))
    print("  Trong so fp32                       {:>9.1f} MiB".format(bn["fp32_MiB"]))
    print("  Trang thai AdamW fp32 (16 byte/ts)  {:>9.2f} GiB (CHUA co activation)".format(
        bn["adamw_fp32_GiB"]))
    print("  Bo dem KV moi token (fp16)          {:>9.1f} KiB".format(
        kq["kv_moi_token_byte"] / KiB))
    print("  Bo dem KV cho {:>5} token           {:>9.1f} MiB".format(
        kq["max_position_embeddings"],
        kq["kv_moi_token_byte"] * kq["max_position_embeddings"] / MiB))
    print("  Bang cos/sin RoPE luc chay          {:>9.1f} MiB  (buffer, khong trong .pt)".format(
        kq["rope_byte"] / MiB))
    print("  (MiB = 1024^2 byte. mo-hinh/cau_hinh.py in cung cac dai luong nay theo MB")
    print("   thap phan 1e6 byte, nen so o do lon hon 4,86% — hai don vi, khong phai")
    print("   hai ket qua. Xem khoi chu thich hang so o dau tep nay.)")


def tu_kiem():
    """Kiem cong thuc bang mot truong hop tinh tay duoc het bang giay but.

    VI SAO KHONG DOI CHIEU VOI SO CUA MOT KHO MA KHAC: vi lam vay la lay con so
    cua nguoi khac lam chuan cho kien truc cua minh, ma cai can chung minh o day
    chi la PHEP DEM co dung so hoc hay khong. Mot truong hop nho, moi so viet ra
    bang tay, la du va khong muon no gi cua ai.

    Truong hop: h=8, L=2, V=10, q=2, kv=1, head_dim=4, inter=16, tie=true.
      embedding = 10 * 8                          = 80
      q_proj    = 8 * (2*4) = 8*8                 = 64
      k_proj    = 8 * (1*4) = 8*4                 = 32
      v_proj    = 8 * (1*4) = 8*4                 = 32
      o_proj    = (2*4) * 8 = 8*8                 = 64
      attn                                        = 192
      2 RMSNorm = 2 * 8                           = 16
      ffn       = 3 * 8 * 16                      = 384
      mot lop   = 192 + 16 + 384                  = 592
      2 lop                                       = 1184
      norm cuoi = 8                               = 8
      TONG      = 80 + 1184 + 8                   = 1272
    """
    cfg = dict(hidden_size=8, num_hidden_layers=2, vocab_size=10,
               num_attention_heads=2, num_key_value_heads=1, head_dim=4,
               intermediate_size=16, tie_word_embeddings=True)
    kq = tinh(cfg)
    mong_doi = {"embedding": 80, "attn_mot_lop": 192, "norm_mot_lop": 16,
                "ffn_mot_lop": 384, "mot_lop": 592, "tong_cac_lop": 1184,
                "tong": 1272}
    print("")
    print("TU KIEM PHEP DEM (truong hop tinh tay duoc, xem docstring ham tu_kiem)")
    print("-" * 74)
    print("{:<20} {:>12} {:>12}   {}".format("muc", "tinh tay", "ham tinh()", "ket qua"))
    print("-" * 74)
    hong = 0
    for khoa in ["embedding", "attn_mot_lop", "norm_mot_lop", "ffn_mot_lop",
                 "mot_lop", "tong_cac_lop", "tong"]:
        that = kq[khoa]
        cho = mong_doi[khoa]
        ok = (that == cho)
        if not ok:
            hong += 1
        print("{:<20} {:>12,} {:>12,}   {}".format(khoa, cho, that, "DAT" if ok else "HONG"))
    print("-" * 74)

    # Kiem them cong thuc intermediate mac dinh: 8/3 * h lam tron len boi so 128.
    for h, mong in [(512, 1408), (768, 2048), (1024, 2816)]:
        ra = intermediate_mac_dinh(h)
        ok = (ra == mong)
        if not ok:
            hong += 1
        print("intermediate_mac_dinh({:>4}) = {:>5}  (cho {:>5})   {}".format(
            h, ra, mong, "DAT" if ok else "HONG"))

    # Kiem viec bo buoc embedding lam tang dung V*h.
    cfg2 = dict(cfg)
    cfg2["tie_word_embeddings"] = False
    kq2 = tinh(cfg2)
    ok = (kq2["tong"] - kq["tong"] == 80)
    if not ok:
        hong += 1
    print("bo tie_word_embeddings lam tong tang {:>4} (cho 80)   {}".format(
        kq2["tong"] - kq["tong"], "DAT" if ok else "HONG"))
    print("-" * 74)
    if hong:
        print("HONG {} muc — phep dem sai, KHONG duoc dung so tu tep nay.".format(hong))
        return 1
    print("DAT toan bo — phep dem nay dung so hoc.")
    print("")
    print("Bai tu kiem nay CHI chung minh phep dem dung so hoc. No khong chung minh")
    print("cong thuc ta khop voi kien truc that. Phep do do la phep doi chieu voi")
    print("mo-hinh/, va no DA CHAY 26/09/2026: ba cau hinh nho/vua/lon deu cho")
    print("36.184.576 / 119.563.008 / 295.748.608 o ca ba duong dem doc lap")
    print("(tep nay · CauHinhBDSG.so_tham_so() · sum(p.numel() for p in m.parameters()))")
    print("— lech 0. Cach chay lai: xem docstring dau tep.")
    return 0


def main():
    p = argparse.ArgumentParser(
        description="Tinh so tham so cua cau hinh BDSG (khong can torch)")
    p.add_argument("tep", nargs="*",
                   help="cac tep .json cau hinh; bo trong = tat ca .json trong thu muc nay")
    p.add_argument("--tu-kiem", action="store_true",
                   help="kiem phep dem bang truong hop tinh tay duoc")
    args = p.parse_args()

    if args.tu_kiem:
        return tu_kiem()

    tep = args.tep
    if not tep:
        tep = sorted(os.path.join(THU_MUC, t) for t in os.listdir(THU_MUC)
                     if t.endswith(".json"))
    if not tep:
        print("Khong tim thay tep .json nao trong {}".format(THU_MUC), file=sys.stderr)
        return 1

    for t in tep:
        if not os.path.isabs(t):
            t = os.path.join(THU_MUC, t)
        cfg = doc_cau_hinh(t)
        in_ket_qua(os.path.basename(t), cfg, tinh(cfg))

    print("")
    print("=" * 74)
    print("Day la SO TINH RA — no DA duoc doi chieu voi phep dem that tren mo-hinh/")
    print("ngay 26/09/2026, lech 0 o ca ba cau hinh (chi tiet trong docstring dau tep).")
    print("CHUA do va van chua do: toc do token/giay, va bo nho that luc chay — BDSG")
    print("chua huan luyen trong so nao nen khong co gi de bam gio.")
    print("Chay `python3 tinh_tham_so.py --tu-kiem` de kiem phep dem truoc da.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
