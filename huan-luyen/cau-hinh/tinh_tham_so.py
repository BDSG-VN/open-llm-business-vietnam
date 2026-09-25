#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tinh so tham so cua mot cau hinh MiniMind ma KHONG can cai torch.

VI SAO CO TEP NAY
-----------------
Cac so "39.33M", "136.87M", "212.38M-A77.90M" ghi trong cac tep .json canh day la
so TINH RA, khong phai so DO tren mo hinh that (25/09/2026: BDSG chua huan luyen
trong so nao, chua co mo hinh de dem). Mot con so tinh ra ma khong kem cach tinh
thi khong kiem chung duoc. Tep nay la cach tinh, chay duoc, ai cung doi chieu lai duoc.

CACH DOI CHIEU (da lam, 25/09/2026)
-----------------------------------
MiniMind cong bo bang tham so trong README_en.md dong 576-580. Chay:
    python3 tinh_tham_so.py --doi-chieu
se dung chinh cong thuc nay tinh lai cac cau hinh cua HO va so voi con so HO ghi:
    768 / 8 lop / kv4 / vocab 6400            -> tinh ra 63.91M, ho ghi 64M
    768 / 8 lop / kv4 / vocab 6400 / 4 expert -> tinh ra 198.42M-A63.94M, ho ghi 198M-A64M
    512 / 8 lop / kv2 / vocab 6400            -> tinh ra 28.98M, ho ghi 26M   (lech 11%)
    768 / 16 lop / kv2 / vocab 6400           -> tinh ra 118.19M, ho ghi 104M (lech 14%)
Hai dong dau khop duoi 0.2%. Hai dong sau LECH, va toi KHONG biet vi sao: ca hai deu la
"phien ban lich su" (README_en.md dong 578-580), rat co the chung dung mot cau hinh khac
voi cai ghi trong bang (vi du intermediate_size khac, hoac ho dem theo cach khac — khong
dem embedding chang han). Toi ghi ca cho lech nay ra thay vi giau no.
=> Cong thuc duoc coi la dung cho nhanh minimind-3 (cai BDSG dung). Voi cac phien ban
   lich su thi chua chac, va do la ly do BDSG khong lay so cua ho lam can cu.

CACH DEM (doc tu model/model_minimind.py cua MiniMind, khong doan)
------------------------------------------------------------------
  embedding   : vocab_size * hidden_size
                Dem MOT LAN neu tie_word_embeddings=True, vi lop
                MiniMindForCausalLM gan model.embed_tokens.weight = lm_head.weight
                (cung mot doi tuong Parameter), va nn.Module.parameters() loc trung.
  moi lop:
    q_proj    : hidden_size * (num_attention_heads * head_dim)
    k_proj    : hidden_size * (num_key_value_heads * head_dim)
    v_proj    : hidden_size * (num_key_value_heads * head_dim)
    o_proj    : (num_attention_heads * head_dim) * hidden_size
    q_norm    : head_dim          (RMSNorm co dung mot vector weight)
    k_norm    : head_dim
    2 RMSNorm : 2 * hidden_size   (input_layernorm + post_attention_layernorm)
    FFN dac   : 3 * hidden_size * intermediate_size   (gate + up + down, deu bias=False)
    FFN MoE   : hidden_size * num_experts             (router gate)
                + num_experts * 3 * hidden_size * moe_intermediate_size
  cuoi cung   : hidden_size       (RMSNorm norm)
  KHONG dem   : freqs_cos / freqs_sin — la buffer (persistent=False), khong phai tham so.

Chay:
    python3 tinh_tham_so.py                    # tinh het cac .json trong thu muc nay
    python3 tinh_tham_so.py nho.json vua.json  # tinh rieng
    python3 tinh_tham_so.py --doi-chieu        # kiem cong thuc voi so MiniMind cong bo
"""

import argparse
import json
import math
import os
import sys

THU_MUC = os.path.dirname(os.path.abspath(__file__))


def intermediate_mac_dinh(hidden_size):
    """Cong thuc mac dinh cua MiniMindConfig: ceil(hidden_size*pi/64)*64."""
    return math.ceil(hidden_size * math.pi / 64) * 64


def doc_cau_hinh(duong_dan):
    with open(duong_dan, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Khoa "bdsg" la ghi chu cua BDSG, KHONG phai tham so cua MiniMindConfig.
    # Ai nap cau hinh nay vao MiniMindConfig(**cfg) phai bo khoa nay truoc.
    cfg.pop("bdsg", None)
    return cfg


def tinh(cfg):
    h = cfg["hidden_size"]
    L = cfg["num_hidden_layers"]
    V = cfg.get("vocab_size", 6400)
    n_q = cfg.get("num_attention_heads", 8)
    n_kv = cfg.get("num_key_value_heads", 4)
    hd = cfg.get("head_dim", h // n_q)
    inter = cfg.get("intermediate_size", intermediate_mac_dinh(h))
    tie = cfg.get("tie_word_embeddings", True)
    dung_moe = bool(cfg.get("use_moe", False))
    n_exp = cfg.get("num_experts", 4)
    n_act = cfg.get("num_experts_per_tok", 1)
    moe_inter = cfg.get("moe_intermediate_size", inter)

    embedding = V * h
    lm_head = 0 if tie else V * h

    attn = h * (n_q * hd) + h * (n_kv * hd) + h * (n_kv * hd) + (n_q * hd) * h
    attn += 2 * hd                      # q_norm + k_norm
    norm_lop = 2 * h                    # hai RMSNorm trong moi block

    ffn_dac = 3 * h * inter
    ffn_moe = h * n_exp + n_exp * 3 * h * moe_inter
    ffn = ffn_moe if dung_moe else ffn_dac

    mot_lop = attn + norm_lop + ffn
    tong = embedding + lm_head + L * mot_lop + h

    # So kich hoat: tinh y het get_model_params trong trainer/trainer_utils.py
    # dong 20-30 cua MiniMind. Luu y: bien 'expert' ben ho la tong tham so cua
    # CHUYEN GIA SO 0 tren TAT CA cac lop, khong phai tren mot lop.
    if dung_moe:
        mot_chuyen_gia_moi_lop = 3 * h * moe_inter
        expert_all_layers = L * mot_chuyen_gia_moi_lop
        base = tong - expert_all_layers * n_exp
        kich_hoat = base + expert_all_layers * n_act
    else:
        kich_hoat = tong

    return {
        "tong": tong,
        "kich_hoat": kich_hoat,
        "embedding": embedding,
        "lm_head": lm_head,
        "mot_lop": mot_lop,
        "attn_mot_lop": attn,
        "ffn_mot_lop": ffn,
        "intermediate_size": inter,
        "head_dim": hd,
        "ti_le_embedding": embedding / float(tong),
    }


def in_ket_qua(ten, cfg, kq):
    nhan = "{:.2f}M".format(kq["tong"] / 1e6)
    if kq["kich_hoat"] < kq["tong"]:
        nhan = "{:.2f}M-A{:.2f}M".format(kq["tong"] / 1e6, kq["kich_hoat"] / 1e6)
    print("")
    print("=" * 72)
    print("  {}".format(ten))
    print("=" * 72)
    print("  hidden={}  lop={}  q_head={}  kv_head={}  head_dim={}  inter={}".format(
        cfg["hidden_size"], cfg["num_hidden_layers"],
        cfg.get("num_attention_heads", 8), cfg.get("num_key_value_heads", 4),
        kq["head_dim"], kq["intermediate_size"]))
    print("  vocab={}  tie_word_embeddings={}  use_moe={}".format(
        cfg.get("vocab_size", 6400), cfg.get("tie_word_embeddings", True),
        bool(cfg.get("use_moe", False))))
    print("  ------------------------------------------------------------------")
    print("  embedding            {:>14,}   ({:.1%} tong so tham so)".format(
        kq["embedding"], kq["ti_le_embedding"]))
    if kq["lm_head"]:
        print("  lm_head (khong buoc) {:>14,}".format(kq["lm_head"]))
    print("  mot lop              {:>14,}   (attn {:,} + ffn {:,})".format(
        kq["mot_lop"], kq["attn_mot_lop"], kq["ffn_mot_lop"]))
    print("  ------------------------------------------------------------------")
    print("  TONG                 {:>14,}   =  {}".format(kq["tong"], nhan))
    print("  Trong so fp16        {:>11.1f} MB".format(kq["tong"] * 2 / 1024.0 / 1024.0))
    print("  Trong so fp32        {:>11.1f} MB".format(kq["tong"] * 4 / 1024.0 / 1024.0))
    print("  Trang thai toi uu AdamW (fp32 + 2 moment + grad = 16 byte/tham so):")
    print("                       {:>11.2f} GB   (CHUA tinh activation)".format(
        kq["tong"] * 16 / 1024.0 ** 3))


def doi_chieu():
    """Tinh lai cac cau hinh MiniMind da cong bo, so voi con so ho ghi."""
    truong_hop = [
        ("minimind-3 (dense)", "64M",
         dict(hidden_size=768, num_hidden_layers=8, vocab_size=6400,
              num_attention_heads=8, num_key_value_heads=4)),
        ("minimind-3-moe", "198M-A64M",
         dict(hidden_size=768, num_hidden_layers=8, vocab_size=6400,
              num_attention_heads=8, num_key_value_heads=4,
              use_moe=True, num_experts=4, num_experts_per_tok=1)),
        ("minimind2-small (ban lich su)", "26M",
         dict(hidden_size=512, num_hidden_layers=8, vocab_size=6400,
              num_attention_heads=8, num_key_value_heads=2)),
        ("minimind2 (ban lich su)", "104M",
         dict(hidden_size=768, num_hidden_layers=16, vocab_size=6400,
              num_attention_heads=8, num_key_value_heads=2)),
    ]
    print("")
    print("DOI CHIEU CONG THUC VOI BANG MiniMind cong bo (README_en.md dong 576-580)")
    print("-" * 72)
    print("{:<34} {:>16} {:>18}".format("cau hinh", "ho ghi", "cong thuc nay"))
    print("-" * 72)
    for ten, ho_ghi, cfg in truong_hop:
        kq = tinh(cfg)
        if kq["kich_hoat"] < kq["tong"]:
            ta = "{:.2f}M-A{:.2f}M".format(kq["tong"] / 1e6, kq["kich_hoat"] / 1e6)
        else:
            ta = "{:.2f}M".format(kq["tong"] / 1e6)
        print("{:<34} {:>16} {:>18}".format(ten, ho_ghi, ta))
    print("-" * 72)
    print("Hai dong dau khop duoi 0.2%. Hai dong 'ban lich su' lech — xem docstring")
    print("dau tep. Cho lech duoc ghi ra thay vi giau di.")


def main():
    p = argparse.ArgumentParser(description="Tinh so tham so cua cau hinh MiniMind (khong can torch)")
    p.add_argument("tep", nargs="*", help="cac tep .json cau hinh; bo trong = tat ca trong thu muc nay")
    p.add_argument("--doi-chieu", action="store_true", help="kiem cong thuc voi so MiniMind da cong bo")
    args = p.parse_args()

    if args.doi_chieu:
        doi_chieu()
        return 0

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
    print("Luu y: day la SO TINH RA. Chua co mo hinh nao ton tai de dem lai (25/09/2026).")
    print("Khi da huan luyen that, doi chieu lai bang dong log 'Model Params' ma")
    print("trainer_utils.get_model_params in ra luc khoi tao.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
