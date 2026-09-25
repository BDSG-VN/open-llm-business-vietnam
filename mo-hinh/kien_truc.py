#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kien truc mo hinh ngon ngu BDSG: transformer decoder-only, PyTorch thuan.

PHAM VI
-------
Tep nay chi phu thuoc torch. KHONG phu thuoc thu vien transformers, KHONG phu thuoc
numpy. Ly do o README.md muc "vi sao khong dung thu vien co san".

NGUON KY THUAT — TAT CA LA KY THUAT DA CONG BO TRONG BAI BAO
------------------------------------------------------------
Moi khoi duoi day duoc viet lai tu MO TA TOAN HOC trong bai bao goc:

  RMSNorm    Zhang & Sennrich 2019, "Root Mean Square Layer Normalization"
             arXiv:1910.07467
  RoPE       Su et al. 2021, "RoFormer: Enhanced Transformer with Rotary Position
             Embedding", arXiv:2104.09864
  GQA        Ainslie et al. 2023, "GQA: Training Generalized Multi-Query Transformer
             Models from Multi-Head Checkpoints", arXiv:2305.13245
  SwiGLU     Shazeer 2020, "GLU Variants Improve Transformer", arXiv:2002.05202
  Pre-norm   Xiong et al. 2020, "On Layer Normalization in the Transformer
             Architecture", arXiv:2002.04745
  Transformer  Vaswani et al. 2017, "Attention Is All You Need", arXiv:1706.03762
  Decoder-only Radford et al. 2018/2019 (GPT, GPT-2) — bao cao ky thuat, khong co ma arXiv;
             va Brown et al. 2020, arXiv:2005.14165 (GPT-3) cho cach khoi tao co gian.

Khong mot dong nao o day duoc chep tu mot kho ma nao. Cac ten TRUONG CAU HINH
(hidden_size, num_attention_heads...) la quy uoc dat ten chung cua he sinh thai
transformers va duoc giu de trong so nap duoc o noi khac — xem cau_hinh.py.

TRANG THAI (26/09/2026)
-----------------------
Kien truc nay CHUA duoc huan luyen. Khong co trong so nao ton tai. Nhung con so chat
luong duy nhat BDSG do duoc den hom nay la o tokenizer (giam 66,1% so token, xem
huan-luyen/tu-vung/ket-qua/) va o bo danh gia M3 cua he RAG dang chay — khong phai
cua mo hinh nay.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .cau_hinh import CauHinhBDSG

# Mot lop cua bo nho KV: (key, value), moi cai hinh dang (B, num_key_value_heads, S, head_dim).
LopKV = Tuple[torch.Tensor, torch.Tensor]
BoNhoKV = List[LopKV]


@dataclass
class KetQuaMoHinh:
    """Dau ra cua BDSGChoNgonNgu.forward().

    Dung dataclass thay vi tuple de ma noi goi doc duoc bang ten. Mot tuple ba phan tu
    rat de bi lay nham thu tu, va loi do khong bao gi ca — no chi lam loss sai.
    """

    logits: torch.Tensor
    loss: Optional[torch.Tensor] = None
    bo_nho_kv: Optional[BoNhoKV] = None


# ======================================================================
# 1. RMSNorm — Zhang & Sennrich 2019, arXiv:1910.07467
# ======================================================================


class RMSNorm(nn.Module):
    """Chuan hoa theo can bac hai trung binh binh phuong.

    CONG THUC (bai bao, cong thuc 4):
        y_i = x_i / RMS(x) * g_i,   RMS(x) = sqrt( (1/n) * sum_j x_j^2 + eps )

    VI SAO RMSNorm THAY VI LayerNorm
    --------------------------------
    LayerNorm lam hai viec: doi tam (tru trung binh) va doi ti le (chia do lech chuan).
    Bai bao tren cho thay phan DOI TAM gan nhu khong dong gop gi vao kha nang hoi tu —
    cai lam nen tac dung la phan doi ti le. Bo phan doi tam di thi:
      - bot mot luot rut gon (reduction) tren chieu an va mot phep tru,
      - bot mot tham so bias moi lop chuan hoa.
    O mo hinh nho chay tren MAY CA NHAN (muc tieu cua du an nay), moi luot rut gon deu
    dat vi CPU khong giau bang thong bo nho. Day la ly do chinh chon RMSNorm.

    VI SAO TINH TRONG FLOAT32
    -------------------------
    x^2 o fp16 tran so rat som (fp16 het tam o khoang 65504). Mot gia tri kich hoat
    240 la du de 240^2 tran. Khi tran, tong thanh inf, rsqrt(inf) thanh 0, ca vector ra 0
    va loss thanh NaN — mot lop sau, khong co dau vet nao chi ve day. Vi vay phep tinh
    RMS luon ep sang float32 roi moi ep nguoc ve kieu goc.
    """

    def __init__(self, chieu: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.eps = eps
        # Chi co he so nhan, khong co bias — RMSNorm khong doi tam nen bias khong co vai tro
        # doi xung voi LayerNorm. Khoi tao bang 1 de lop chuan hoa luc dau la phep dong nhat.
        self.weight = nn.Parameter(torch.ones(chieu))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        kieu_goc = x.dtype
        x32 = x.float()
        rms_nghich = torch.rsqrt(x32.pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return (x32 * rms_nghich).to(kieu_goc) * self.weight

    def extra_repr(self) -> str:
        return "chieu={}, eps={}".format(tuple(self.weight.shape), self.eps)


# ======================================================================
# 2. RoPE — Su et al. 2021, arXiv:2104.09864
# ======================================================================


def _dung_bang_rope(
    head_dim: int,
    do_dai: int,
    theta: float,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Dung bang cos/sin cua RoPE, hinh dang (do_dai, head_dim).

    CONG THUC (bai bao, muc 3.2.2): voi moi cap toa do (2i, 2i+1) trong vector mot dau,
    goc quay tai vi tri m la  m * theta_i  voi  theta_i = base^(-2i/d).
    Base mac dinh cua bai bao la 10000; o day lay tu cau hinh (rope_theta) vi base lon hon
    lam tan so thap hon, tuc la RoPE "cham" hon va ngoai suy ra chuoi dai tot hon.

    Bang luon dung o float32 du mo hinh chay fp16: goc quay o vi tri lon (chuc nghin)
    mat do chinh xac rat nhanh o fp16, va sai so goc lam hong chinh cai ma RoPE mang lai
    (khoang cach tuong doi giua hai vi tri).
    """
    # nghich_tan_so[i] = theta^(-2i/d), i = 0..d/2-1
    nua = torch.arange(0, head_dim, 2, dtype=torch.float32, device=device)
    nghich_tan_so = 1.0 / (theta ** (nua / head_dim))  # (d/2,)
    vi_tri = torch.arange(do_dai, dtype=torch.float32, device=device)  # (T,)
    goc = torch.outer(vi_tri, nghich_tan_so)  # (T, d/2)
    # Nhan doi theo quy uoc "hai nua": toa do i va i + d/2 lam thanh mot cap.
    # Xem chu thich o quay_nua() ve vi sao chon quy uoc nay.
    goc_day_du = torch.cat((goc, goc), dim=-1)  # (T, d)
    return goc_day_du.cos(), goc_day_du.sin()


def quay_nua(x: torch.Tensor) -> torch.Tensor:
    """Quay 90 do trong mat phang cua tung cap toa do: (a, b) -> (-b, a).

    VE QUY UOC GHEP CAP: bai bao goc ghep cap KE NHAU (0,1), (2,3), ... Cai dat nay ghep
    HAI NUA: (i, i + d/2). Hai quy uoc la mot phep hoan vi toa do cua nhau, cung mot phep
    quay, cung ket qua hoc; nhung trong so cua chung KHONG doi cho duoc cho nhau.
    Chon quy uoc hai nua vi do la quy uoc ma phan lon cong cu suy luan pho bien gia dinh
    khi nap mo hinh kieu Llama — va muc tieu cua du an la nguoi dung tai ve may ca nhan
    chay duoc bang cong cu san co. Doi quy uoc nay ve sau = lam hong moi trong so da huan luyen.
    """
    nua = x.shape[-1] // 2
    x1 = x[..., :nua]
    x2 = x[..., nua:]
    return torch.cat((-x2, x1), dim=-1)


def ap_rope(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Ap phep quay vi tri vao query va key.

    q: (B, nq, T, D) · k: (B, nkv, T, D) · cos/sin: (T, D)
    Chi q va k duoc quay, KHONG quay v. Ly do nam o chinh dinh ly cua bai bao: tich vo huong
    <R_m q, R_n k> chi phu thuoc (m - n). Vi tri di vao mo hinh qua DIEM SO chu y, khong
    di vao noi dung duoc mang ra. Quay v se pha tinh chat do.
    """
    cos = cos.unsqueeze(0).unsqueeze(0).to(q.dtype)  # (1, 1, T, D)
    sin = sin.unsqueeze(0).unsqueeze(0).to(q.dtype)
    q_quay = q * cos + quay_nua(q) * sin
    k_quay = k * cos + quay_nua(k) * sin
    return q_quay, k_quay


# ======================================================================
# 3. Grouped-Query Attention — Ainslie et al. 2023, arXiv:2305.13245
# ======================================================================


def lap_kv(x: torch.Tensor, so_lap: int) -> torch.Tensor:
    """Lap moi dau key/value `so_lap` lan de khop so dau query.

    x: (B, nkv, S, D) -> (B, nkv * so_lap, S, D)

    Dung expand + reshape chu khong dung repeat: expand khong sao chep bo nho, chi tao
    mot khung nhin co stride 0. Phep reshape sau do buoc phai vat chat hoa, nhung ca hai
    buoc gop lai van it phan bo hon mot repeat truc tiep tren tensor lon.

    LUU Y VE THU TU: phai expand o chieu NGAY SAU nkv roi reshape, de cac ban sao cua
    cung mot dau KV nam lien nhau. Neu expand nham chieu, dau query thu j se nhin vao
    dau KV sai — va khong co gi bao loi ca, mo hinh chi hoc kem di.
    """
    if so_lap == 1:
        return x
    B, nkv, S, D = x.shape
    x = x[:, :, None, :, :].expand(B, nkv, so_lap, S, D)
    return x.reshape(B, nkv * so_lap, S, D)


class ChuYNhomTruyVan(nn.Module):
    """Chu y nhan-tich co ti le, dang Grouped-Query, co mat na nhan qua.

    VI SAO GQA THAY VI MHA O CO MO HINH NAY
    ---------------------------------------
    Day la lua chon quan trong nhat cua ca kien truc, va ly do khong phai ve chat luong
    ma ve BO NHO LUC SUY LUAN.

    Khi sinh tung token, mo hinh phai giu lai K va V cua moi token da sinh, o moi lop.
    Kich thuoc bo nho do (KV cache) la:
        2 * so_lop * so_dau_KV * head_dim * do_dai * so_byte
    No KHONG phu thuoc so tham so, va no LON LEN THEO DO DAI NGU CANH. Voi mot mo hinh
    nho, o ngu canh dai, KV cache co the vuot ca trong so mo hinh.

    Muc tieu cua du an nay la NGUOI DUNG TAI VE MAY CA NHAN CHAY DUOC (VPS cua BDSG da do
    la khong chay noi LLM tu host: 7B chi dat 0,3 token/giay — xem README). Tren may ca nhan,
    RAM la thu khan hiem hon FLOP. GQA cat so_dau_KV xuong con mot phan cua so dau query,
    nen cat KV cache theo dung ti le do: GQA 4:1 dung 1/4 bo nho KV cua MHA.

    Cai gia phai tra: theo arXiv:2305.13245, GQA mat mot phan nho chat luong so voi MHA,
    nhung GIU duoc gan het chat luong do trong khi Multi-Query Attention (nkv=1) thi mat
    ro rang. GQA la diem giua co chu dich — do cung la ket luan cua bai bao.
    So cu the mat bao nhieu o quy mo cua BDSG thi CHUA DO, vi chua huan luyen mo hinh nao.
    Khong duoc trich so cua bai bao nhu la so cua BDSG.

    Luu y: `num_key_value_heads == num_attention_heads` lam khoi nay tro thanh MHA thuan
    (lap_kv tra ve chinh no), nen khong can hai cai dat rieng.
    """

    def __init__(self, cfg: CauHinhBDSG, chi_so_lop: int) -> None:
        super().__init__()
        self.cfg = cfg
        self.chi_so_lop = chi_so_lop
        self.nq = cfg.num_attention_heads
        self.nkv = cfg.num_key_value_heads
        self.so_lap = cfg.so_dau_moi_nhom
        self.head_dim = int(cfg.head_dim)
        self.dropout = float(cfg.attention_dropout)

        # bias=False o ca bon phep chieu. Ly do: ngay truoc moi khoi con nay da co mot
        # RMSNorm, ma RMSNorm khong doi tam; mot bias o day chi them tham so ma khong
        # them kha nang bieu dien dang ke. Cac ho mo hinh hien dai deu bo bias o day.
        self.q_proj = nn.Linear(cfg.hidden_size, self.nq * self.head_dim, bias=False)
        self.k_proj = nn.Linear(cfg.hidden_size, self.nkv * self.head_dim, bias=False)
        self.v_proj = nn.Linear(cfg.hidden_size, self.nkv * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.nq * self.head_dim, cfg.hidden_size, bias=False)
        # Danh dau de _khoi_tao_trong_so() giam do lech chuan o phep chieu nay.
        self.o_proj._bdsg_residual = True  # type: ignore[attr-defined]

        self.dropout_ra = nn.Dropout(self.dropout)

        self._co_sdpa = hasattr(F, "scaled_dot_product_attention")

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        kv_cu: Optional[LopKV] = None,
        dung_bo_nho: bool = False,
    ) -> Tuple[torch.Tensor, Optional[LopKV]]:
        B, T, _ = x.shape

        q = self.q_proj(x).view(B, T, self.nq, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.nkv, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.nkv, self.head_dim).transpose(1, 2)
        # q: (B, nq, T, D) · k, v: (B, nkv, T, D)

        # RoPE ap TRUOC khi noi bo nho cu vao: cos/sin da duoc cat dung doan vi tri
        # [vi_tri_bat_dau, vi_tri_bat_dau + T) o lop goi, nen phan k cu trong bo nho
        # da mang goc quay cua chinh no tu luot truoc. Quay lai lan nua se sai.
        q, k = ap_rope(q, k, cos, sin)

        if kv_cu is not None:
            k = torch.cat((kv_cu[0], k), dim=2)
            v = torch.cat((kv_cu[1], v), dim=2)
        kv_moi: Optional[LopKV] = (k, v) if dung_bo_nho else None

        S = k.shape[2]  # tong do dai khoa, >= T khi co bo nho

        # Nhan ban KV cho du so dau query.
        k_du = lap_kv(k, self.so_lap)
        v_du = lap_kv(v, self.so_lap)

        # --- Mat na nhan qua ---
        # Token o vi tri tuyet doi (S - T + i) chi duoc nhin j <= S - T + i.
        # Khi khong co bo nho, S == T va day la mat na tam giac duoi thong thuong.
        # Khi T == 1 (sinh tung token), moi vi tri deu hop le nen khong can mat na.
        can_mat_na = T > 1
        mat_na = None
        if can_mat_na:
            hang = torch.arange(S - T, S, device=x.device).unsqueeze(1)  # (T, 1)
            cot = torch.arange(S, device=x.device).unsqueeze(0)  # (1, S)
            mat_na = (cot <= hang).view(1, 1, T, S)  # True = duoc nhin

        p_dropout = self.dropout if self.training else 0.0

        if self.cfg.bdsg_dung_sdpa and self._co_sdpa:
            # SDPA cua torch chon nhan duong toi uu (flash / mem-efficient) va khong
            # vat chat hoa ma tran diem so (B, nq, T, S) — do chinh la thu chiem bo nho
            # nhieu nhat khi T lon.
            if not can_mat_na:
                ra = F.scaled_dot_product_attention(q, k_du, v_du, dropout_p=p_dropout)
            elif S == T:
                # Duong nhanh nhat: khong truyen mat na, de torch tu sinh tam giac duoi.
                ra = F.scaled_dot_product_attention(
                    q, k_du, v_du, dropout_p=p_dropout, is_causal=True
                )
            else:
                # Co bo nho VA T > 1 (vi du nap lai mot doan prompt vao bo nho san co):
                # is_causal=True se sai vi no gia dinh q va k cung do dai. Phai truyen
                # mat na tuong minh. Day dung la cho de sai nhat trong ca tep nay.
                ra = F.scaled_dot_product_attention(
                    q, k_du, v_du, attn_mask=mat_na, dropout_p=p_dropout
                )
        else:
            # Duong viet tay — giu lai de doi chieu voi duong SDPA khi nghi ngo.
            diem = torch.matmul(q, k_du.transpose(2, 3)) / math.sqrt(self.head_dim)
            if mat_na is not None:
                diem = diem.masked_fill(~mat_na, torch.finfo(diem.dtype).min)
            trong_so = F.softmax(diem.float(), dim=-1).to(q.dtype)
            if p_dropout > 0.0:
                trong_so = F.dropout(trong_so, p=p_dropout, training=True)
            ra = torch.matmul(trong_so, v_du)

        # (B, nq, T, D) -> (B, T, nq*D)
        ra = ra.transpose(1, 2).contiguous().view(B, T, self.nq * self.head_dim)
        return self.dropout_ra(self.o_proj(ra)), kv_moi


# ======================================================================
# 4. SwiGLU feed-forward — Shazeer 2020, arXiv:2002.05202
# ======================================================================


class MangSwiGLU(nn.Module):
    """Khoi feed-forward dang cong don tuyen tinh co cua (gated linear unit).

    CONG THUC (bai bao, muc 2):
        SwiGLU(x) = ( Swish(x W_cong) * (x W_len) ) W_xuong
    voi Swish(z) = z * sigmoid(z), tuc la SiLU.

    VI SAO SwiGLU THAY VI FFN + ReLU/GELU
    -------------------------------------
    FFN co dien la mot phep chieu len roi mot ham kich hoat theo tung phan tu. SwiGLU thay
    no bang mot CO: mot nhanh quyet dinh "cho bao nhieu di qua", nhanh kia mang noi dung.
    Bai bao do tren T5 va thay bien the co an hon cac bien the khong co o cung ngan sach
    tinh toan. Day la ket qua THUC NGHIEM, va bai bao noi thang la khong giai thich duoc
    vi sao (cau cuoi cua bai: tac gia quy no cho "su quan phong").

    VI SAO intermediate_size khong phai 4 * hidden_size
    ---------------------------------------------------
    SwiGLU dung BA ma tran thay vi hai. De giu nguyen so tham so va so phep tinh so voi
    FFN hai ma tran o be rong 4h, be rong trong phai rut xuong khoang (2/3) * 4h = 8h/3.
    Do la ly do cac cau hinh trong kho dat intermediate_size quanh 2,7 lan hidden_size
    chu khong phai 4 lan. Con so cu the do cau hinh quyet dinh, tep nay khong tu doan.
    """

    def __init__(self, cfg: CauHinhBDSG) -> None:
        super().__init__()
        h, m = cfg.hidden_size, cfg.intermediate_size
        self.cong_proj = nn.Linear(h, m, bias=False)  # nhanh cua (gate)
        self.len_proj = nn.Linear(h, m, bias=False)  # nhanh noi dung (up)
        self.xuong_proj = nn.Linear(m, h, bias=False)  # tra ve chieu an (down)
        self.xuong_proj._bdsg_residual = True  # type: ignore[attr-defined]
        # Dung chung gia tri cfg.attention_dropout du day khong phai khoi chu y — xem ghi chu
        # ve pham vi cua truong do trong cau_hinh.py. Mac dinh 0,0.
        self.dropout = nn.Dropout(float(cfg.attention_dropout))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.xuong_proj(F.silu(self.cong_proj(x)) * self.len_proj(x)))


# ======================================================================
# 5. Khoi giai ma (pre-norm) — Xiong et al. 2020, arXiv:2002.04745
# ======================================================================


class KhoiGiaiMa(nn.Module):
    """Mot lop transformer decoder-only, chuan hoa TRUOC (pre-norm).

    SO DO:
        x = x + ChuY( RMSNorm(x) )
        x = x + SwiGLU( RMSNorm(x) )

    VI SAO PRE-NORM THAY VI POST-NORM
    ---------------------------------
    Bai bao tren phan tich gradient luc khoi tao: o post-norm (kieu bai Vaswani 2017),
    gradient tai cac lop gan dau ra lon theo so lop, nen phai co giai doan lam am
    (learning-rate warmup) dai thi moi khong no. O pre-norm, duong residual di THANG tu
    dau vao toi dau ra khong qua mot lop chuan hoa nao, nen gradient khong bi khuech dai
    theo do sau, va co the bo warmup hoac rut ngan no.

    Voi BDSG day la lua chon ve RUI RO chu khong ve diem so: du an chua thue GPU lan nao
    (26/09/2026). Mot lan huan luyen phan ky vi dat sai warmup la mot lan tra tien GPU
    cho khong. Pre-norm lam cho viec huan luyen it nhay cam hon voi sieu tham so, tuc la
    lan chay dau tien it kha nang do song hon.
    """

    def __init__(self, cfg: CauHinhBDSG, chi_so_lop: int) -> None:
        super().__init__()
        self.chuan_truoc_chu_y = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.chu_y = ChuYNhomTruyVan(cfg, chi_so_lop)
        self.chuan_truoc_ffn = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.ffn = MangSwiGLU(cfg)

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        kv_cu: Optional[LopKV] = None,
        dung_bo_nho: bool = False,
    ) -> Tuple[torch.Tensor, Optional[LopKV]]:
        ra_chu_y, kv_moi = self.chu_y(
            self.chuan_truoc_chu_y(x), cos, sin, kv_cu=kv_cu, dung_bo_nho=dung_bo_nho
        )
        x = x + ra_chu_y
        x = x + self.ffn(self.chuan_truoc_ffn(x))
        return x, kv_moi


# ======================================================================
# 6. Mo hinh day du
# ======================================================================


class BDSGChoNgonNgu(nn.Module):
    """Mo hinh ngon ngu nhan qua cua BDSG (decoder-only, du doan token ke tiep).

    Ten cac mo-dun con (embed_tokens, layers, norm, lm_head) theo quy uoc chung cua he
    sinh thai transformers, cung ly do voi ten truong cau hinh: de state_dict doc duoc
    o noi khac. Xem cau_hinh.py.
    """

    def __init__(self, cfg: CauHinhBDSG) -> None:
        super().__init__()
        cfg.kiem()  # phong truong hop cau hinh bi sua truc tiep sau khi dung
        self.cfg = cfg

        self.embed_tokens = nn.Embedding(cfg.vocab_size, cfg.hidden_size)
        self.layers = nn.ModuleList(
            [KhoiGiaiMa(cfg, i) for i in range(cfg.num_hidden_layers)]
        )
        self.norm = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.lm_head = nn.Linear(cfg.hidden_size, cfg.vocab_size, bias=False)
        # Cung dung cfg.attention_dropout (xem ghi chu ve pham vi trong cau_hinh.py).
        self.dropout_nhung = nn.Dropout(float(cfg.attention_dropout))

        # Khoi tao TRUOC khi buoc trong so, de gia tri cua embedding la cai duoc giu lai.
        self.apply(self._khoi_tao_trong_so)

        # --- Buoc trong so dau vao va dau ra ---
        # VI SAO: hai ma tran nay cung hinh dang (vocab_size, hidden_size) va cung bieu dien
        # "token <-> vector". Buoc chung lam giam so tham so di vocab_size * hidden_size —
        # o cau hinh nho cua BDSG (vocab 24.576, hidden 512) do la 12,6 trieu tham so,
        # tuc mot phan ba ca mo hinh. O mo hinh nho, ti le do lon den muc khong buoc la lang phi.
        # Cach buoc: GAN CHUNG MOT doi tuong Parameter. nn.Module.parameters() loc trung theo
        # dinh danh doi tuong, nen so tham so dem duoc giam dung bang mot ban embedding —
        # day la dieu so_tham_so() trong cau_hinh.py dua vao.
        if cfg.tie_word_embeddings:
            self.lm_head.weight = self.embed_tokens.weight

        # Bang RoPE: dung lazy va cho lon dan. Dang ky buffer voi persistent=False de
        # chung KHONG nam trong state_dict — chung la gia tri tinh ra tu (head_dim, theta),
        # khong phai tham so hoc duoc. Neu luu vao state_dict thi moi lan doi do dai ngu canh
        # la mot lan tep trong so khong nap duoc, ma khong co ly do gi.
        self.register_buffer("rope_cos", torch.empty(0), persistent=False)
        self.register_buffer("rope_sin", torch.empty(0), persistent=False)
        self._bao_dam_bang_rope(min(cfg.max_position_embeddings, 1024), self.embed_tokens.weight.device)

    # ------------------------------------------------------------------

    def _khoi_tao_trong_so(self, mo_dun: nn.Module) -> None:
        """Khoi tao chuan, co gian du cho cac phep chieu do vao nhanh residual.

        VI SAO GIAM DO LECH CHUAN O o_proj VA xuong_proj
        ------------------------------------------------
        Duong residual cong don qua tung khoi. Neu moi khoi dong gop mot luong co phuong sai
        s^2, thi sau L lop phuong sai cua duong residual xap xi L * s^2 — tuc la do lon cua
        kich hoat lon theo CAN cua so lop. Bao cao GPT-2 xu ly bang cach chia do lech chuan
        khoi tao cua cac phep chieu DO VAO residual cho sqrt(N) voi N la so duong residual
        (o day N = 2 * so_lop, vi moi lop co hai: mot cho chu y, mot cho FFN).
        Khong lam viec nay thi mo hinh sau van huan luyen duoc, nhung nhung buoc dau bat on
        hon — va voi mot du an chua tung thue GPU thi nhung buoc dau la thu dat nhat.

        Tat bang cfg.bdsg_giam_khoi_tao_residual=False neu muon doi chieu.
        """
        std = float(self.cfg.initializer_range)
        if isinstance(mo_dun, nn.Linear):
            if self.cfg.bdsg_giam_khoi_tao_residual and getattr(mo_dun, "_bdsg_residual", False):
                std = std / math.sqrt(2.0 * self.cfg.num_hidden_layers)
            nn.init.normal_(mo_dun.weight, mean=0.0, std=std)
            if mo_dun.bias is not None:
                nn.init.zeros_(mo_dun.bias)
        elif isinstance(mo_dun, nn.Embedding):
            nn.init.normal_(mo_dun.weight, mean=0.0, std=std)
        # RMSNorm.weight da la ones tu __init__ cua chinh no — khong dung vao.

    def _bao_dam_bang_rope(self, do_dai_can: int, device: torch.device) -> None:
        """Dung lai bang cos/sin neu bang hien co ngan hon do_dai_can.

        VI SAO KHONG DUNG SAN CA BANG max_position_embeddings: voi ngu canh 32.768 va
        head_dim 64, bang cos+sin o float32 ton 32768*64*2*4 = 16,8 MB — tra bang RAM
        ngay tu luc nap mo hinh, cho MOT kha nang ma phan lon lan chay khong dung toi.
        O muc tieu "chay tren may ca nhan" thi 16,8 MB khong phai khong dang ke.

        Bang cung duoc dung lai khi kieu du lieu khong con la float32: goi .half() tren
        mo hinh se ep CA buffer sang fp16, lam mat do chinh xac cua goc quay o vi tri lon.
        Kiem dtype o day de cai chu thich "bang luon o float32" van dung sau .half().
        """
        if (
            self.rope_cos.numel() > 0
            and self.rope_cos.shape[0] >= do_dai_can
            and self.rope_cos.device == device
            and self.rope_cos.dtype == torch.float32
        ):
            return
        # Cap phat co du: lam tron len boi cua 256 de khong phai dung lai o moi token khi sinh.
        do_dai = max(256, int(math.ceil(do_dai_can / 256.0)) * 256)
        cos, sin = _dung_bang_rope(
            int(self.cfg.head_dim), do_dai, float(self.cfg.rope_theta), device
        )
        self.rope_cos = cos
        self.rope_sin = sin

    def dem_tham_so(self, chi_hoc_duoc: bool = False) -> int:
        """Dem tham so THAT tu model.parameters().

        Doi chieu voi cfg.so_tham_so()["tong"] (so tinh ra). Hai con so phai bang nhau;
        thu_kien_truc.py kiem dieu do. nn.Module.parameters() tu loc trung nen trong so
        da buoc (tie_word_embeddings) chi duoc dem mot lan.
        """
        return sum(
            p.numel() for p in self.parameters() if (p.requires_grad or not chi_hoc_duoc)
        )

    # ------------------------------------------------------------------

    def forward(
        self,
        ids: torch.Tensor,
        nhan: Optional[torch.Tensor] = None,
        bo_nho_kv: Optional[BoNhoKV] = None,
        dung_bo_nho: bool = False,
    ) -> KetQuaMoHinh:
        """Mot luot xuoi.

        ids  : (B, T) so nguyen trong [0, vocab_size)
        nhan : (B, T) so nguyen, hoac None. Neu co, tra ve them loss.
               Quy uoc -100 = bo qua o vi tri do (giong ignore_index mac dinh cua torch),
               dung cho phan dem hoac phan prompt khong tinh loss.
        bo_nho_kv : bo nho KV tu luot truoc, hoac None.
        dung_bo_nho : True thi tra ve bo nho KV moi de luot sau dung lai.
        """
        if ids.dim() != 2:
            raise ValueError("ids phai co hinh dang (B, T), dang la {}".format(tuple(ids.shape)))
        B, T = ids.shape

        vi_tri_bat_dau = 0 if bo_nho_kv is None else bo_nho_kv[0][0].shape[2]
        tong_do_dai = vi_tri_bat_dau + T
        if tong_do_dai > self.cfg.max_position_embeddings:
            # Nem loi thay vi lang le cat bot. Cat bot ngu canh ma khong bao la dung lop
            # loi "hong ma khong bao": ket qua van ra chu, chi la sai — va khong ai biet.
            raise ValueError(
                "Do dai {} vuot max_position_embeddings = {}. Hay tang cau hinh hoac "
                "cat ngu canh o phia goi (co y thuc), dung de lop nay cat ngam.".format(
                    tong_do_dai, self.cfg.max_position_embeddings
                )
            )

        self._bao_dam_bang_rope(tong_do_dai, ids.device)
        cos = self.rope_cos[vi_tri_bat_dau:tong_do_dai]
        sin = self.rope_sin[vi_tri_bat_dau:tong_do_dai]

        x = self.dropout_nhung(self.embed_tokens(ids))

        bo_nho_ra: Optional[BoNhoKV] = [] if dung_bo_nho else None
        for i, lop in enumerate(self.layers):
            kv_cu = bo_nho_kv[i] if bo_nho_kv is not None else None
            x, kv_moi = lop(x, cos, sin, kv_cu=kv_cu, dung_bo_nho=dung_bo_nho)
            if bo_nho_ra is not None and kv_moi is not None:
                bo_nho_ra.append(kv_moi)

        x = self.norm(x)
        logits = self.lm_head(x)

        loss = None
        if nhan is not None:
            if nhan.shape != ids.shape:
                raise ValueError(
                    "nhan phai cung hinh dang voi ids; {} vs {}".format(
                        tuple(nhan.shape), tuple(ids.shape)
                    )
                )
            # Du doan token KE TIEP: logit o vi tri t du doan nhan o vi tri t+1.
            # Vi vay bo logit cuoi va bo nhan dau. Dat lech sai mot o la loi kinh dien —
            # mo hinh van huan luyen duoc, loss van giam, nhung no hoc chep lai dau vao.
            logits_lech = logits[:, :-1, :].contiguous()
            nhan_lech = nhan[:, 1:].contiguous()
            loss = F.cross_entropy(
                logits_lech.view(-1, logits_lech.size(-1)).float(),
                nhan_lech.view(-1),
                ignore_index=-100,
            )

        return KetQuaMoHinh(logits=logits, loss=loss, bo_nho_kv=bo_nho_ra)

    # ------------------------------------------------------------------

    @torch.no_grad()
    def sinh(
        self,
        ids: torch.Tensor,
        so_token_moi: int,
        nhiet_do: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        eos_token_id: Optional[int] = None,
        dung_bo_nho: bool = True,
    ) -> torch.Tensor:
        """Sinh token tung cai mot. Tra ve CA CHUOI (prompt + phan moi).

        Hinh dang tra ve: (B, T_prompt + so_token_da_sinh). Khi eos_token_id=None, so token
        sinh ra dung bang so_token_moi — thu_kien_truc.py kiem dieu do.

        nhiet_do <= 0 nghia la lay tham lam (argmax), khong lay mau.
        top_k va top_p co the dung chung; top_k ap truoc.

        GIOI HAN DA BIET: cac chuoi trong mot lo phai CUNG do dai. Kien truc nay chua co
        mat na dem (padding mask) — huan luyen cua BDSG dung chuoi dong goi do dai co dinh
        nen chua can den. Neu ve sau can sinh theo lo voi prompt dai ngan khac nhau thi phai
        them mat na dem; ghi ra day de khong ai tuong la da co.
        """
        if so_token_moi < 0:
            raise ValueError("so_token_moi phai >= 0, dang la {}".format(so_token_moi))
        dang_huan_luyen = self.training
        self.eval()
        try:
            bo_nho: Optional[BoNhoKV] = None
            dau_vao = ids
            for _ in range(so_token_moi):
                ket_qua = self.forward(dau_vao, bo_nho_kv=bo_nho, dung_bo_nho=dung_bo_nho)
                logit_cuoi = ket_qua.logits[:, -1, :].float()  # (B, V)
                if dung_bo_nho:
                    bo_nho = ket_qua.bo_nho_kv

                if nhiet_do is None or nhiet_do <= 0:
                    token_moi = torch.argmax(logit_cuoi, dim=-1, keepdim=True)
                else:
                    logit_cuoi = logit_cuoi / float(nhiet_do)
                    logit_cuoi = _loc_top_k(logit_cuoi, top_k)
                    logit_cuoi = _loc_top_p(logit_cuoi, top_p)
                    xac_suat = F.softmax(logit_cuoi, dim=-1)
                    token_moi = torch.multinomial(xac_suat, num_samples=1)

                ids = torch.cat((ids, token_moi), dim=1)
                # Voi bo nho KV, luot sau chi can dua token MOI vao; khong co bo nho thi
                # phai dua lai ca chuoi. Day la toan bo ly do ton tai cua KV cache.
                dau_vao = token_moi if dung_bo_nho else ids

                if eos_token_id is not None and bool((token_moi == eos_token_id).all()):
                    break
            return ids
        finally:
            # Tra lai dung trang thai cu du co ngoai le — neu khong, mot lan sinh giua
            # vong huan luyen se tat dropout vinh vien ma khong ai thay.
            self.train(dang_huan_luyen)


# ======================================================================
# 7. Loc lay mau
# ======================================================================


def _loc_top_k(logits: torch.Tensor, top_k: Optional[int]) -> torch.Tensor:
    """Giu k logit lon nhat, phan con lai dat -inf. logits: (B, V)."""
    if top_k is None or top_k <= 0:
        return logits
    k = min(int(top_k), logits.size(-1))
    nguong = torch.topk(logits, k, dim=-1).values[:, -1:]  # (B, 1)
    return logits.masked_fill(logits < nguong, float("-inf"))


def _loc_top_p(logits: torch.Tensor, top_p: Optional[float]) -> torch.Tensor:
    """Lay mau theo nhan (nucleus sampling). logits: (B, V).

    Giu tap token nho nhat co tong xac suat >= top_p. LUON giu it nhat mot token:
    neu mot token don da co xac suat vuot top_p thi phep so sanh ngay tho se loai HET,
    va softmax cua toan -inf ra NaN. Cho nen so sanh dung la (cong_don - xac_suat) > p,
    tuc la chi loai token khi tap TRUOC no da du.
    """
    if top_p is None or not (0.0 < float(top_p) < 1.0):
        return logits
    p = float(top_p)
    logits_sap, chi_so_sap = torch.sort(logits, descending=True, dim=-1)
    xac_suat = F.softmax(logits_sap, dim=-1)
    cong_don = torch.cumsum(xac_suat, dim=-1)
    bo = (cong_don - xac_suat) > p
    logits_sap = logits_sap.masked_fill(bo, float("-inf"))
    return torch.full_like(logits, float("-inf")).scatter(-1, chi_so_sap, logits_sap)


def dung_mo_hinh(cfg: Optional[CauHinhBDSG] = None) -> BDSGChoNgonNgu:
    """Tao mo hinh tu cau hinh (mac dinh: cau hinh ti hon de thu)."""
    if cfg is None:
        from .cau_hinh import cau_hinh_ti_hon

        cfg = cau_hinh_ti_hon()
    return BDSGChoNgonNgu(cfg)
