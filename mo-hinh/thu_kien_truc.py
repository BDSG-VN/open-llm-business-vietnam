#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bai tu kiem cho kien truc mo hinh BDSG.

CHAY:
    .venv/bin/python3 mo-hinh/thu_kien_truc.py

KHONG can GPU. KHONG can du lieu. KHONG can trong so. Mo hinh dung trong bai nay la
mo hinh ti hon (hidden 64, 2 lop, vocab 128) — du de bat moi loi HINH DANG va moi loi
CONG THUC, khong du de hoc duoc gi that.

VI SAO CO BAI NAY
-----------------
Kien truc la phan duy nhat trong ca duong ong ma loi cua no KHONG BAO. Mot mat na nhan qua
dat sai, mot phep lech nhan sai mot o, mot bo nho KV quay RoPE hai lan: mo hinh van chay,
loss van giam, khong co ngoai le nao duoc nem ra. Chi den luc danh gia moi thay ket qua kem,
va luc do khong con biet kem vi kien truc hay vi du lieu. Nhung phep kiem duoi day la cach
duy nhat tach hai nguyen nhan do ra TRUOC khi tieu tien GPU.

13 phep kiem. Phep kiem QUAN TRONG NHAT la so 4: so tham so TINH RA phai bang so tham so
DEM DUOC.
Cong thuc tinh la thu duoc dung de uoc luong bo nho, thoi gian va chi phi thue GPU cua
ca du an. Neu no sai, moi du toan sai theo, va khong ai phat hien ra cho toi luc da tra tien.

TRANG THAI (26/09/2026): kien truc chua tung duoc huan luyen. Bai nay kiem TINH DUNG cua
ma, khong noi gi ve chat luong mo hinh — chat luong chua do duoc vi chua co trong so.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import traceback

THU_MUC = os.path.dirname(os.path.abspath(__file__))
GOC_KHO = os.path.dirname(THU_MUC)


# ----------------------------------------------------------------------
# Nap goi. Thu muc that ten la "mo-hinh" — gach ngang khong hop le trong ten
# mo-dun Python, nen khi chay tep nay truc tiep (khong co __package__) phai nap
# thu muc bang importlib duoi mot ten hop le.
# ----------------------------------------------------------------------
if __package__:
    from .cau_hinh import CauHinhBDSG, LoiCauHinh, cau_hinh_ti_hon
    from .kien_truc import BDSGChoNgonNgu, RMSNorm, ap_rope, lap_kv
else:
    _spec = importlib.util.spec_from_file_location(
        "mo_hinh",
        os.path.join(THU_MUC, "__init__.py"),
        submodule_search_locations=[THU_MUC],
    )
    if _spec is None or _spec.loader is None:
        print("HONG: khong nap duoc goi tu {}".format(THU_MUC))
        sys.exit(1)
    _goi = importlib.util.module_from_spec(_spec)
    sys.modules["mo_hinh"] = _goi
    _spec.loader.exec_module(_goi)
    CauHinhBDSG = _goi.CauHinhBDSG
    LoiCauHinh = _goi.LoiCauHinh
    cau_hinh_ti_hon = _goi.cau_hinh_ti_hon
    BDSGChoNgonNgu = _goi.BDSGChoNgonNgu
    RMSNorm = _goi.RMSNorm
    ap_rope = _goi.ap_rope
    lap_kv = _goi.lap_kv

try:
    import torch
    import torch.nn.functional as F
except ImportError:
    print("HONG: chua co torch. Cai bang:  .venv/bin/pip install torch")
    sys.exit(1)


# ----------------------------------------------------------------------
# Khung chay thu toi gian (khong dung pytest de bai nay chay duoc o moi noi)
# ----------------------------------------------------------------------

_KET_QUA = []


def phep_kiem(ten):
    def bao(ham):
        def chay():
            try:
                ghi_chu = ham()
                _KET_QUA.append((ten, True, ghi_chu or ""))
                print("  [DAT ] {}{}".format(ten, "  — " + ghi_chu if ghi_chu else ""))
                return True
            except Exception as e:  # noqa: BLE001 — bai tu kiem phai bat het
                _KET_QUA.append((ten, False, "{}: {}".format(type(e).__name__, e)))
                print("  [HONG] {}".format(ten))
                print("         {}: {}".format(type(e).__name__, e))
                for dong in traceback.format_exc().splitlines()[-6:]:
                    print("         | " + dong)
                return False

        chay.__name__ = ham.__name__
        return chay

    return bao


def bang(dieu_kien, thong_diep):
    if not dieu_kien:
        raise AssertionError(thong_diep)


def _hoc_thuoc_mot_chuoi(seed=4242, so_chuoi=2, do_dai=16, so_buoc=60, lr=3e-3):
    """Huan luyen mo hinh ti hon cho hoc THUOC mot chuoi co dinh.

    Tra ve (mo_hinh o che do eval, chuoi da hoc, loss cuoi).

    VI SAO NHIEU PHEP KIEM CAN DEN CAI NAY
    --------------------------------------
    Mo hinh CHUA huan luyen co dau ra SUY BIEN: lay tham lam roi ngay vao mot diem co dinh
    va lap mai mot token (do 26/09/2026 tren cau hinh ti hon: chuoi sinh ra la
    [58, 125, 75, 118, 103, 103, 103, ...]). Tren mot dau ra suy bien nhu vay, HAI duong
    tinh khac nhau — ke ca mot duong dang sai — van cho ra cung mot day token, nen moi phep
    so sanh theo token deu vo hieu ma van in "DAT".
    Do chinh la cho phep kiem 6 tung hut mutation "co bo nho KV ma van dua lai ca chuoi":
    so sanh tren mo hinh chua huan luyen thi hai duong TRUNG nhau, so sanh tren mo hinh da
    hoc thuoc thi chung KHAC nhau tu vi tri thu 13 cua chuoi (dem tu 0).
    Huan luyen 60 buoc tren CPU het chua toi mot giay o cau hinh ti hon.
    """
    torch.manual_seed(seed)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg)
    m.train()
    day = torch.randint(0, cfg.vocab_size, (so_chuoi, do_dai))
    toi_uu = torch.optim.AdamW(m.parameters(), lr=lr)
    loss_cuoi = float("nan")
    for _ in range(so_buoc):
        kq = m(day, nhan=day)
        toi_uu.zero_grad(set_to_none=True)
        kq.loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        toi_uu.step()
        loss_cuoi = float(kq.loss.detach())
    m.eval()
    return m, day, loss_cuoi


def gan_bang(a, b, sai_so, thong_diep):
    lech = float(torch.max(torch.abs(a - b)))
    if not (lech <= sai_so):
        raise AssertionError("{} (lech lon nhat {:.3e} > {:.3e})".format(thong_diep, lech, sai_so))
    return lech


# ======================================================================
# 1. Cau hinh: rang buoc sai phai NEM LOI NGAY LUC DUNG
# ======================================================================


@phep_kiem("1. Cau hinh tu chan rang buoc sai ngay luc dung")
def kiem_cau_hinh_chan_loi():
    truong_hop = [
        (
            "num_attention_heads khong chia het cho num_key_value_heads",
            dict(hidden_size=64, num_attention_heads=6, num_key_value_heads=4),
        ),
        (
            "hidden_size khong chia het cho num_attention_heads",
            dict(hidden_size=64, num_attention_heads=6, num_key_value_heads=2, head_dim=None),
        ),
        (
            "head_dim le (RoPE khong quay duoc)",
            dict(hidden_size=64, num_attention_heads=4, num_key_value_heads=2, head_dim=15),
        ),
        (
            "num_key_value_heads > num_attention_heads",
            dict(hidden_size=64, num_attention_heads=2, num_key_value_heads=4),
        ),
        (
            "so lop bang 0",
            dict(num_hidden_layers=0),
        ),
        (
            "rms_norm_eps = 0 (chia cho 0 o vector toan so khong)",
            dict(rms_norm_eps=0.0),
        ),
        (
            "eos_token_id nam ngoai tu vung",
            dict(vocab_size=128, eos_token_id=999),
        ),
        (
            "hidden_act khong phai silu trong khi FFN la SwiGLU",
            dict(hidden_act="gelu"),
        ),
    ]
    for mo_ta, tham_so in truong_hop:
        try:
            CauHinhBDSG(**tham_so)
        except LoiCauHinh:
            continue
        raise AssertionError(
            "Cau hinh le ra phai bi tu choi nhung lai dung duoc: {} ({})".format(mo_ta, tham_so)
        )

    # Va cau hinh hop le thi phai dung duoc, khong bao dong gia.
    cfg = cau_hinh_ti_hon()
    bang(cfg.head_dim == 16, "head_dim phai tu suy ra = 64/4 = 16, dang la {}".format(cfg.head_dim))
    bang(cfg.so_dau_moi_nhom == 2, "so_dau_moi_nhom phai = 4/2 = 2")
    return "{} truong hop sai deu bi tu choi; cau hinh dung van dung duoc".format(len(truong_hop))


@phep_kiem("2. tu_json / ra_json di ve khong mat thong tin")
def kiem_json_vong_tron():
    cfg = cau_hinh_ti_hon()
    chuoi = cfg.ra_json()
    lai = CauHinhBDSG.tu_json(chuoi)
    for ten in ("hidden_size", "num_hidden_layers", "num_attention_heads",
                "num_key_value_heads", "head_dim", "intermediate_size", "vocab_size",
                "rms_norm_eps", "rope_theta", "tie_word_embeddings"):
        bang(
            getattr(cfg, ten) == getattr(lai, ten),
            "{} khong khop sau vong JSON: {} vs {}".format(ten, getattr(cfg, ten), getattr(lai, ten)),
        )

    # Khoa la phai duoc giu lai, khong duoc lam mat va khong duoc lam chet chuong trinh.
    # Day la truong hop THAT: cac tep cau hinh trong kho mang them khoa ghi chu "bdsg",
    # "attention_bias", "mlp_bias"... khong thuoc kien truc.
    co_khoa_la = json.loads(chuoi)
    co_khoa_la["bdsg"] = {"ghi_chu": "sieu du lieu cua duong ong, khong phai kien truc"}
    co_khoa_la["attention_bias"] = False
    cfg2 = CauHinhBDSG.tu_json(co_khoa_la)
    bang("bdsg" in cfg2.bdsg_khac, "khoa la 'bdsg' phai duoc giu trong bdsg_khac")
    bang("attention_bias" in cfg2.bdsg_khac, "khoa la 'attention_bias' phai duoc giu")
    ra_lai = json.loads(cfg2.ra_json())
    bang("bdsg" in ra_lai, "khoa la phai quay tro ra khi ghi lai JSON")

    # Doc tu TEP (khong phai tu chuoi) cung phai chay.
    duong_dan = os.path.join(THU_MUC, "_thu_cau_hinh_tam.json")
    try:
        cfg.ghi_tep(duong_dan)
        tu_tep = CauHinhBDSG.tu_json(duong_dan)
        bang(tu_tep.hidden_size == cfg.hidden_size, "doc tu tep khong khop")
    finally:
        if os.path.exists(duong_dan):
            os.remove(duong_dan)
    return "chuoi, dict va tep deu doc duoc; khoa la duoc giu nguyen"


# ======================================================================
# 3. Hinh dang dau ra
# ======================================================================


@phep_kiem("3. Hinh dang dau ra dung")
def kiem_hinh_dang():
    torch.manual_seed(0)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()

    B, T = 3, 11
    ids = torch.randint(0, cfg.vocab_size, (B, T))

    kq = m(ids)
    bang(
        tuple(kq.logits.shape) == (B, T, cfg.vocab_size),
        "logits phai la (B, T, vocab) = ({}, {}, {}), dang la {}".format(
            B, T, cfg.vocab_size, tuple(kq.logits.shape)
        ),
    )
    bang(kq.loss is None, "khong truyen nhan thi loss phai la None")
    bang(kq.bo_nho_kv is None, "khong yeu cau bo nho thi bo_nho_kv phai la None")
    bang(torch.isfinite(kq.logits).all(), "logits co gia tri khong huu han (NaN/inf)")

    kq2 = m(ids, nhan=ids)
    bang(kq2.loss is not None, "co nhan thi phai co loss")
    bang(tuple(kq2.loss.shape) == (), "loss phai la mot so vo huong, dang la {}".format(tuple(kq2.loss.shape)))
    bang(torch.isfinite(kq2.loss), "loss khong huu han")

    # Luc khoi tao, mo hinh chua hoc gi nen loss phai gan ln(vocab_size) — phan bo deu.
    # Lech xa gia tri nay la dau hieu khoi tao sai (vi du do lech chuan qua lon).
    ky_vong = math.log(cfg.vocab_size)
    thuc = float(kq2.loss.detach())
    bang(
        abs(thuc - ky_vong) < 0.5,
        "loss luc khoi tao = {:.4f}, le ra phai gan ln({}) = {:.4f}. Lech xa nghia la "
        "khoi tao trong so sai.".format(thuc, cfg.vocab_size, ky_vong),
    )

    # Bo nho KV phai co dung so lop va dung hinh dang.
    kq3 = m(ids, dung_bo_nho=True)
    bang(
        len(kq3.bo_nho_kv) == cfg.num_hidden_layers,
        "bo nho KV phai co {} lop, dang co {}".format(cfg.num_hidden_layers, len(kq3.bo_nho_kv)),
    )
    k, v = kq3.bo_nho_kv[0]
    mong = (B, cfg.num_key_value_heads, T, cfg.head_dim)
    bang(
        tuple(k.shape) == mong and tuple(v.shape) == mong,
        "moi lop bo nho KV phai la {}, dang la K{} V{}".format(mong, tuple(k.shape), tuple(v.shape)),
    )
    return "logits (3, 11, 128); loss khoi tao {:.3f} ~ ln(128)={:.3f}".format(thuc, ky_vong)


# ======================================================================
# 4. SO THAM SO: TINH RA phai bang DEM DUOC  <-- phep kiem quan trong nhat
# ======================================================================


@phep_kiem("4. So tham so TINH RA == so tham so DEM DUOC  (phep kiem quan trong nhat)")
def kiem_so_tham_so():
    # Nhieu hinh dang khac nhau, moi cai cham mot nhanh cong thuc khac nhau:
    cac_cau_hinh = [
        ("GQA 2:1, co buoc trong so", dict(
            hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
            num_key_value_heads=2, intermediate_size=176, vocab_size=128,
            tie_word_embeddings=True)),
        ("GQA 2:1, KHONG buoc trong so", dict(
            hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
            num_key_value_heads=2, intermediate_size=176, vocab_size=128,
            tie_word_embeddings=False)),
        ("MHA (nkv == nq)", dict(
            hidden_size=64, num_hidden_layers=3, num_attention_heads=4,
            num_key_value_heads=4, intermediate_size=176, vocab_size=128,
            tie_word_embeddings=True)),
        ("MQA (nkv == 1)", dict(
            hidden_size=64, num_hidden_layers=2, num_attention_heads=8,
            num_key_value_heads=1, intermediate_size=176, vocab_size=128,
            tie_word_embeddings=True)),
        ("head_dim dat tuong minh, khac hidden/nq", dict(
            hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
            num_key_value_heads=2, head_dim=32, intermediate_size=176,
            vocab_size=128, tie_word_embeddings=False)),
        ("mot lop, tu vung lon hon chieu an nhieu", dict(
            hidden_size=32, num_hidden_layers=1, num_attention_heads=2,
            num_key_value_heads=1, intermediate_size=88, vocab_size=512,
            tie_word_embeddings=True)),
    ]

    dong = []
    for mo_ta, tham_so in cac_cau_hinh:
        cfg = CauHinhBDSG(max_position_embeddings=128, bdsg_ten="thu", **tham_so)
        m = BDSGChoNgonNgu(cfg)
        tinh = cfg.so_tham_so()["tong"]
        dem = m.dem_tham_so()
        bang(
            tinh == dem,
            "SAI CONG THUC o '{}': cong thuc tinh ra {:,} nhung model.parameters() dem duoc "
            "{:,} (lech {:+,}). Moi uoc luong bo nho va chi phi GPU dua tren cong thuc nay "
            "deu sai theo.".format(mo_ta, tinh, dem, dem - tinh),
        )
        dong.append("{} = {:,}".format(mo_ta, dem))

    # Buoc trong so phai THUC SU tiet kiem dung mot ban embedding — neu khong, phep gan
    # lm_head.weight = embed_tokens.weight da khong tao ra doi tuong dung chung.
    chung = dict(hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
                 num_key_value_heads=2, intermediate_size=176, vocab_size=128,
                 max_position_embeddings=128)
    co_buoc = BDSGChoNgonNgu(CauHinhBDSG(tie_word_embeddings=True, **chung)).dem_tham_so()
    khong_buoc = BDSGChoNgonNgu(CauHinhBDSG(tie_word_embeddings=False, **chung)).dem_tham_so()
    chenh = khong_buoc - co_buoc
    mong_doi = 128 * 64
    bang(
        chenh == mong_doi,
        "buoc trong so phai tiet kiem dung vocab*hidden = {:,} tham so, thuc te chenh "
        "{:,}. Neu bang 0 thi phep buoc khong co tac dung; neu khac thi co cho dem trung.".format(
            mong_doi, chenh
        ),
    )

    # Va phai la CUNG MOT doi tuong, khong phai hai ban sao bang nhau.
    m_buoc = BDSGChoNgonNgu(CauHinhBDSG(tie_word_embeddings=True, **chung))
    bang(
        m_buoc.lm_head.weight is m_buoc.embed_tokens.weight,
        "lm_head.weight va embed_tokens.weight phai la CUNG mot doi tuong Parameter",
    )
    return "{} cau hinh khop tuyet doi; buoc trong so tiet kiem dung {:,}".format(
        len(cac_cau_hinh), mong_doi
    )


# ======================================================================
# 5. Lan truyen nguoc chay duoc va loss giam
# ======================================================================


@phep_kiem("5. Lan truyen nguoc chay duoc va loss giam tren du lieu bia")
def kiem_lan_truyen_nguoc():
    torch.manual_seed(1234)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg)
    m.train()

    B, T = 4, 16
    # Du lieu BIA, co dinh: mo hinh chi viec nho thuoc long mot lo. Muc dich khong phai
    # hoc duoc gi, ma la chung minh gradient chay ve toi moi tham so va buoc toi uu co tac dung.
    ids = torch.randint(0, cfg.vocab_size, (B, T))

    # Truoc khi buoc: moi tham so phai nhan duoc gradient. Mot tham so co grad None nghia la
    # no khong nam tren duong tinh — tuc la co mot khoi duoc dung nen nhung khong duoc goi.
    kq = m(ids, nhan=ids)
    kq.loss.backward()
    thieu = [ten for ten, p in m.named_parameters() if p.requires_grad and p.grad is None]
    bang(
        not thieu,
        "cac tham so sau khong nhan duoc gradient (khong nam tren duong tinh): {}".format(thieu),
    )
    m.zero_grad(set_to_none=True)

    toi_uu = torch.optim.AdamW(m.parameters(), lr=3e-3)
    loss_dau = None
    loss_cuoi = None
    for buoc in range(40):
        kq = m(ids, nhan=ids)
        toi_uu.zero_grad(set_to_none=True)
        kq.loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        toi_uu.step()
        if buoc == 0:
            loss_dau = float(kq.loss)
        loss_cuoi = float(kq.loss)
        bang(math.isfinite(loss_cuoi), "loss thanh NaN/inf o buoc {}".format(buoc))

    bang(
        loss_cuoi < loss_dau * 0.5,
        "sau 40 buoc tren mot lo co dinh, loss phai giam ro ret. Dau {:.4f} -> cuoi {:.4f}. "
        "Khong giam nghia la gradient khong toi duoc noi can toi.".format(loss_dau, loss_cuoi),
    )
    return "loss {:.4f} -> {:.4f} sau 40 buoc; moi tham so deu co gradient".format(loss_dau, loss_cuoi)


# ======================================================================
# 6. sinh() tra dung so token
# ======================================================================


@phep_kiem("6. sinh() tra dung so token yeu cau")
def kiem_sinh():
    torch.manual_seed(7)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()

    B, T = 2, 5
    ids = torch.randint(0, cfg.vocab_size, (B, T))

    for so_moi in (1, 12):
        for ten_cach, tham_so in (
            ("tham lam", dict(nhiet_do=0.0)),
            ("nhiet do 0,8", dict(nhiet_do=0.8)),
            ("top_k=5", dict(nhiet_do=1.0, top_k=5)),
            ("top_p=0,9", dict(nhiet_do=1.0, top_p=0.9)),
            ("top_k=10 + top_p=0,9", dict(nhiet_do=1.0, top_k=10, top_p=0.9)),
            ("khong dung bo nho KV", dict(nhiet_do=0.0, dung_bo_nho=False)),
        ):
            ra = m.sinh(ids, so_token_moi=so_moi, eos_token_id=None, **tham_so)
            bang(
                tuple(ra.shape) == (B, T + so_moi),
                "sinh({} token, {}) phai tra ({}, {}), dang tra {}".format(
                    so_moi, ten_cach, B, T + so_moi, tuple(ra.shape)
                ),
            )
            bang(
                torch.equal(ra[:, :T], ids),
                "sinh() phai giu nguyen phan prompt o dau ({})".format(ten_cach),
            )
            bang(
                bool(((ra >= 0) & (ra < cfg.vocab_size)).all()),
                "sinh() tra token nam ngoai tu vung ({})".format(ten_cach),
            )

    # so_token_moi = 0 phai tra lai dung prompt, khong nem loi.
    bang(torch.equal(m.sinh(ids, 0), ids), "sinh(0) phai tra lai dung prompt")

    # --- eos phai dung som duoc ---
    # Khong nan trong so de ep ra token mong muon: voi tie_word_embeddings=True thi
    # lm_head.weight CHINH LA embed_tokens.weight, nen ghi de len no la pha luon embedding
    # va mo hinh sinh ra cai khac han cai minh dinh ep. (Da mac dung loi nay khi viet bai
    # kiem nay — giu ghi chu lai o day.)
    # Cach dung: hoi mo hinh xem no sinh token gi truoc da, roi lay CHINH token do lam eos.
    ids1 = ids[:1]  # mot chuoi: dieu kien dung xet tren ca lo nen phai dong nhat
    token_dau = int(m.sinh(ids1, so_token_moi=1, nhiet_do=0.0)[0, -1])
    ra_eos = m.sinh(ids1, so_token_moi=20, nhiet_do=0.0, eos_token_id=token_dau)
    bang(
        tuple(ra_eos.shape) == (1, T + 1),
        "sinh ra eos ngay token dau thi phai dung ngay: mong (1, {}), duoc {}".format(
            T + 1, tuple(ra_eos.shape)
        ),
    )
    # Va khi eos KHONG bao gio duoc sinh ra thi phai chay het so token yeu cau.
    #
    # BAN TRUOC CUA PHEP KIEM NAY VO NGHIA — giu ghi chu lai vi day la bai hoc thuc.
    # No khang dinh `ra_du.shape[1] in (T+1, T+2, T+3, T+4)`. Nhung voi so_token_moi=4,
    # vong sinh chay toi da 4 lan va noi it nhat 1 token truoc khi xet dieu kien dung,
    # nen do dai tra ve CHI CO THE la mot trong bon gia tri do. Khang dinh phu tron mien
    # gia tri => khong bao gio HONG duoc => no in "DAT" ma khong do gi ca (do 26/09/2026).
    #
    # Ban dung: lay chuoi tham lam KHONG eos lam chan ly, chon mot eos chac chan KHONG
    # nam trong phan sinh ra, roi doi hoi hai chuoi TRUNG KHIT. Tham lam nen tat dinh.
    tham_lam = m.sinh(ids1, so_token_moi=4, nhiet_do=0.0, eos_token_id=None)
    da_sinh = set(int(t) for t in tham_lam[0, T:])
    khong_phai_eos = next(t for t in range(cfg.vocab_size) if t not in da_sinh)
    ra_du = m.sinh(ids1, so_token_moi=4, nhiet_do=0.0, eos_token_id=khong_phai_eos)
    bang(
        torch.equal(ra_du, tham_lam),
        "dat eos bang mot token KHONG he duoc sinh ra ma van dung som: mong chuoi {} "
        "(dai {}), duoc {} (dai {})".format(
            tham_lam[0].tolist(), tham_lam.shape[1], ra_du[0].tolist(), ra_du.shape[1]
        ),
    )

    # --- Bo nho KV khong duoc lam DOI ket qua sinh ---
    # VI SAO TACH RIENG KHOI PHEP KIEM 7: phep kiem 7 doi chieu bo nho KV o muc forward(),
    # con day la o muc sinh(). Hai cho do sai khac nhau: sinh() con phai quyet dinh dua CAI GI
    # vao luot sau (chi token moi khi co bo nho, ca chuoi khi khong). Dua nham ca chuoi vao
    # trong khi bo nho da giu phan truoc thi vi tri RoPE va do dai khoa deu sai — ma moi
    # khang dinh ve HINH DANG o tren van dat het.
    #
    # VI SAO PHAI DUNG MO HINH DA HOC THUOC: do 26/09/2026, so sanh tren mo hinh CHUA huan
    # luyen khong bat duoc loi do — dau ra suy bien lap mai mot token nen hai duong cho cung
    # mot day. Tren mo hinh da hoc thuoc, chung khac nhau tu token thu 13. Xem
    # _hoc_thuoc_mot_chuoi().
    m_hoc, day_hoc, loss_hoc = _hoc_thuoc_mot_chuoi()
    bang(
        loss_hoc < 0.5,
        "mo hinh khong hoc thuoc noi chuoi thu (loss {:.4f}); phep doi chieu bo nho KV ben "
        "duoi chi co nghia khi dau ra da het suy bien".format(loss_hoc),
    )
    moi_nhac = day_hoc[:1, :6]
    co_bo_nho = m_hoc.sinh(moi_nhac, so_token_moi=10, nhiet_do=0.0, dung_bo_nho=True)
    khong_bo_nho = m_hoc.sinh(moi_nhac, so_token_moi=10, nhiet_do=0.0, dung_bo_nho=False)
    bang(
        torch.equal(co_bo_nho, khong_bo_nho),
        "sinh() co bo nho KV va khong bo nho KV ra hai chuoi khac nhau:\n    co   bo nho: {}"
        "\n    khong bo nho: {}\nBo nho KV la mot phep toi uu, no khong duoc phep doi ket qua.".format(
            co_bo_nho[0].tolist(), khong_bo_nho[0].tolist()
        ),
    )
    return ("6 cach lay mau x 2 do dai deu dung so token; eos dung som dung luc; "
            "sinh co/khong bo nho KV trung khit tren mo hinh da hoc thuoc")


# ======================================================================
# 7. Bo nho KV cho ket qua GIONG het khong dung bo nho
# ======================================================================


@phep_kiem("7. Bo nho KV cho ket qua trung voi duong khong bo nho")
def kiem_bo_nho_kv():
    torch.manual_seed(21)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()

    B, T = 2, 13
    ids = torch.randint(0, cfg.vocab_size, (B, T))

    with torch.no_grad():
        day_du = m(ids).logits  # (B, T, V) — chan ly doi chieu

        # (a) nap 5 token dau, roi di tung token mot.
        bo_nho = None
        kq = m(ids[:, :5], dung_bo_nho=True)
        bo_nho = kq.bo_nho_kv
        lech_max = gan_bang(kq.logits, day_du[:, :5], 2e-4, "doan nap dau lech")
        for t in range(5, T):
            kq = m(ids[:, t : t + 1], bo_nho_kv=bo_nho, dung_bo_nho=True)
            bo_nho = kq.bo_nho_kv
            lech = gan_bang(
                kq.logits[:, 0], day_du[:, t], 2e-4,
                "logits o vi tri {} lech giua duong co bo nho va duong khong bo nho. "
                "Thuong la do RoPE bi ap sai vi tri khi co bo nho.".format(t),
            )
            lech_max = max(lech_max, lech)

        # (b) NHANH DE SAI NHAT: da co bo nho VA dua vao NHIEU token mot luc.
        # O nhanh nay q dai 4 con k dai 9, nen is_causal=True cua SDPA se sai —
        # phai dung mat na tuong minh. Neu cai dat sai, phep kiem nay bat duoc.
        kq = m(ids[:, :5], dung_bo_nho=True)
        kq2 = m(ids[:, 5:9], bo_nho_kv=kq.bo_nho_kv, dung_bo_nho=True)
        lech_khoi = gan_bang(
            kq2.logits, day_du[:, 5:9], 2e-4,
            "dua mot KHOI nhieu token vao khi da co bo nho cho ket qua sai — "
            "mat na nhan qua o truong hop q ngan hon k bi dat sai",
        )
    return "tung token lech <= {:.2e}; khoi 4 token tren bo nho 5 lech <= {:.2e}".format(
        lech_max, lech_khoi
    )


# ======================================================================
# 8. Mat na nhan qua that su chan tuong lai
# ======================================================================


@phep_kiem("8. Mat na nhan qua: token sau khong anh huong token truoc")
def kiem_nhan_qua():
    """Kiem tren CA HAI duong chu y.

    VI SAO PHAI CHAY HAI LAN: o cau hinh mac dinh (bdsg_dung_sdpa=True) va khi khong co
    bo nho KV thi S == T, va kien_truc.py di duong nhanh `is_causal=True` — tuc la mat na
    do TORCH sinh, con mat na BDSG tu dung (bien `mat_na`) KHONG he duoc dung den. Chay mot
    lan o duong do thi phep kiem nay chi chung nhan mat na cua torch.
    Do duoc 26/09/2026: gai loi `cot <= hang + 1` (cho nhin truoc 1 token) vao mat na cua
    BDSG thi ban cu cua phep kiem nay VAN DAT. Tat SDPA di thi no HONG ngay.
    """
    torch.manual_seed(33)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()

    T = 9
    ids = torch.randint(0, cfg.vocab_size, (1, T))
    # Doi token CUOI thanh mot token khac han.
    doi = ids.clone()
    doi[0, -1] = (int(ids[0, -1]) + 57) % cfg.vocab_size

    ghi_chu = []
    for dung_sdpa in (True, False):
        # cfg la CUNG mot doi tuong o mo hinh va o moi lop chu y, nen dat mot cho la du;
        # van dat ca hai cho cho ro y va de khong phu thuoc vao chi tiet do.
        m.cfg.bdsg_dung_sdpa = dung_sdpa
        for lop in m.layers:
            lop.chu_y.cfg.bdsg_dung_sdpa = dung_sdpa
        ten_duong = "SDPA" if dung_sdpa else "viet tay"

        with torch.no_grad():
            goc = m(ids).logits
            sau = m(doi).logits

        gan_bang(
            goc[:, :-1], sau[:, :-1], 1e-5,
            "[duong {}] doi token cuoi lam thay doi logits o cac vi tri TRUOC do — mat na "
            "nhan qua bi ro ri, mo hinh dang nhin thay tuong lai. Loi nay khong bao gi ca, "
            "chi lam danh gia sai".format(ten_duong),
        )
        # Va phai thuc su co thay doi o vi tri cuoi, neu khong thi phep kiem tren vo nghia.
        lech_cuoi = float(torch.max(torch.abs(goc[:, -1] - sau[:, -1])))
        bang(
            lech_cuoi > 1e-6,
            "[duong {}] doi token cuoi ma logits cuoi khong doi — dau vao khong den duoc "
            "dau ra".format(ten_duong),
        )
        ghi_chu.append("{} {:.3e}".format(ten_duong, lech_cuoi))

    m.cfg.bdsg_dung_sdpa = True
    for lop in m.layers:
        lop.chu_y.cfg.bdsg_dung_sdpa = True
    return "vi tri truoc khong doi o ca hai duong; vi tri cuoi doi: " + ", ".join(ghi_chu)


# ======================================================================
# 9. Tinh chat toan hoc cua tung khoi
# ======================================================================


@phep_kiem("9. RMSNorm dung cong thuc va chiu duoc gia tri lon")
def kiem_rmsnorm():
    torch.manual_seed(5)
    chuan = RMSNorm(16, eps=1e-6).eval()
    x = torch.randn(3, 7, 16)
    ra = chuan(x)
    # Doi chieu voi cong thuc viet thang ra, khong qua mo-dun.
    tay = x / torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + 1e-6)
    gan_bang(ra, tay, 1e-5, "RMSNorm khong khop cong thuc x / sqrt(mean(x^2) + eps)")

    # Khoi tao weight = 1 nen luc dau phai giu nguyen chuan RMS = 1.
    rms = ra.pow(2).mean(dim=-1).sqrt()
    gan_bang(rms, torch.ones_like(rms), 1e-4, "RMS cua dau ra phai bang 1 khi weight = 1")

    # Gia tri du lon de x^2 tran fp16 (65504): 300^2 = 90.000. Neu tinh trong fp16 se ra inf.
    #
    # BAN TRUOC CUA KHANG DINH NAY KHONG DO DUOC GI — giu ghi chu lai vi day la bai hoc thuc.
    # No chi hoi `torch.isfinite(ra16).all()`. Nhung day chinh la duong di cua loi tran so:
    # x^2 -> inf, mean -> inf, rsqrt(inf) -> 0, x * 0 -> 0,0. KHONG PHAI NaN, khong phai inf,
    # ma la SO KHONG — va so khong thi isfinite van tra True. Do 26/09/2026: ban RMSNorm co y
    # bo phep ep float32 cung qua duoc khang dinh cu (ra 0,0 nhung isfinite=True).
    #
    # Ban dung: doi hoi GIA TRI. Vector hang so 300 co RMS dung bang 300, nen dau ra phai la
    # 1,0 o moi toa do khi weight = 1. Ban dung cho 1,0; ban tran so cho 0,0 — tach han nhau.
    x_lon = torch.full((1, 1, 16), 300.0, dtype=torch.float16)
    chuan16 = RMSNorm(16, eps=1e-6).half().eval()
    ra16 = chuan16(x_lon)
    bang(
        bool(torch.isfinite(ra16).all()),
        "RMSNorm ra NaN/inf o fp16 voi dau vao 300.0",
    )
    gan_bang(
        ra16.float(), torch.ones_like(ra16, dtype=torch.float32), 1e-2,
        "RMSNorm tran so o fp16 voi dau vao 300.0: vector hang so co RMS = chinh no nen dau ra "
        "phai la 1,0; ra {:.4f} nghia la x^2 da tran thanh inf va rsqrt(inf) da ve 0 — phep "
        "tinh khong duoc ep sang float32".format(float(ra16.float().flatten()[0])),
    )
    return "khop cong thuc; dau vao 300.0 o fp16 cho dung 1,0 (khong tran so)"


@phep_kiem("10. RoPE bao toan tich vo huong theo khoang cach TUONG DOI")
def kiem_rope():
    torch.manual_seed(11)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()
    m._bao_dam_bang_rope(64, torch.device("cpu"))
    cos, sin = m.rope_cos, m.rope_sin

    D = int(cfg.head_dim)
    q = torch.randn(1, 1, 1, D)
    k = torch.randn(1, 1, 1, D)

    # Dinh ly trung tam cua RoPE (arXiv:2104.09864): <R_m q, R_n k> chi phu thuoc (m - n).
    # Kiem: cung khoang cach 3 o hai vi tri tuyet doi khac nhau phai cho cung tich vo huong.
    def tich(m_vt, n_vt):
        qq, _ = ap_rope(q, q, cos[m_vt : m_vt + 1], sin[m_vt : m_vt + 1])
        _, kk = ap_rope(k, k, cos[n_vt : n_vt + 1], sin[n_vt : n_vt + 1])
        return (qq * kk).sum()

    a = tich(5, 2)   # khoang cach 3
    b = tich(30, 27)  # cung khoang cach 3, vi tri tuyet doi khac han
    gan_bang(
        a, b, 1e-4,
        "RoPE khong bao toan tich vo huong theo khoang cach tuong doi ({:.6f} vs {:.6f}) — "
        "bang goc quay dung sai cong thuc".format(float(a), float(b)),
    )

    # Khoang cach KHAC thi tich phai khac, neu khong phep kiem tren vo nghia.
    c = tich(5, 1)  # khoang cach 4
    bang(
        abs(float(a) - float(c)) > 1e-4,
        "khoang cach khac nhau ma tich vo huong nhu nhau — RoPE khong ma hoa gi ca",
    )

    # Phep quay phai bao toan do dai vector.
    qq, _ = ap_rope(q, q, cos[9:10], sin[9:10])
    gan_bang(qq.norm(), q.norm(), 1e-5, "RoPE lam doi do dai vector — do khong phai phep quay")
    return "tich vo huong chi phu thuoc (m-n); do dai vector duoc bao toan"


@phep_kiem("11. lap_kv nhan ban dung dau, dung thu tu")
def kiem_lap_kv():
    # (B=1, nkv=2, S=3, D=2), moi dau mang mot gia tri rieng de nhan ra sau khi lap.
    x = torch.tensor([[[[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]],
                       [[2.0, 2.0], [2.0, 2.0], [2.0, 2.0]]]])
    bang(tuple(x.shape) == (1, 2, 3, 2), "du lieu thu dung sai hinh dang")

    ra = lap_kv(x, 3)
    bang(tuple(ra.shape) == (1, 6, 3, 2), "lap_kv sai hinh dang: {}".format(tuple(ra.shape)))
    # Cac ban sao cua CUNG mot dau phai nam LIEN NHAU: [1,1,1,2,2,2] chu khong phai [1,2,1,2,1,2].
    # Neu nam xen ke, dau query thu j se nhin vao dau KV sai — va khong co gi bao loi.
    duoc = [float(ra[0, h, 0, 0]) for h in range(6)]
    bang(
        duoc == [1.0, 1.0, 1.0, 2.0, 2.0, 2.0],
        "thu tu lap KV sai: duoc {} , phai la [1,1,1,2,2,2] (cac ban sao cung mot dau "
        "phai lien nhau)".format(duoc),
    )
    bang(torch.equal(lap_kv(x, 1), x), "lap_kv(x, 1) phai tra lai chinh x")
    return "hinh dang (1,6,3,2); thu tu [1,1,1,2,2,2] dung"


@phep_kiem("12. Duong SDPA va duong chu y viet tay cho cung ket qua")
def kiem_hai_duong_chu_y():
    torch.manual_seed(99)
    cfg_a = cau_hinh_ti_hon()
    cfg_a.bdsg_dung_sdpa = True
    m = BDSGChoNgonNgu(cfg_a).eval()

    ids = torch.randint(0, cfg_a.vocab_size, (2, 10))
    with torch.no_grad():
        ra_sdpa = m(ids).logits
        # Doi duong tinh tren CUNG mot mo hinh, cung trong so.
        m.cfg.bdsg_dung_sdpa = False
        for lop in m.layers:
            lop.chu_y.cfg.bdsg_dung_sdpa = False
        ra_tay = m(ids).logits

    lech = gan_bang(
        ra_sdpa, ra_tay, 2e-4,
        "duong SDPA va duong viet tay cho ket qua khac nhau — mot trong hai cai dat sai "
        "mat na hoac he so ti le 1/sqrt(head_dim)",
    )
    return "hai duong khop, lech lon nhat {:.2e}".format(lech)


# ======================================================================
# 13. Huong lech nhan: doan token KE TIEP, khong phai chep lai dau vao
# ======================================================================


@phep_kiem("13. Loss doan token KE TIEP, khong phai chep lai dau vao")
def kiem_huong_lech_nhan():
    """Ghim HUONG cua phep lech nhan trong forward().

    VI SAO PHAI CO RIENG MOT PHEP KIEM CHO VIEC NAY
    -----------------------------------------------
    Dat lech nhan sai mot o la loi kinh dien nhat cua mo hinh ngon ngu, va no khong bao:
    mo hinh van huan luyen duoc, loss van giam — giam NHANH HON la dang khac, vi chep lai
    dau vao de hon nhieu so voi doan token ke tiep. Chi den luc sinh chu moi thay mo hinh
    lap lai de bai.

    Do duoc 26/09/2026 bang cach gai loi: doi `logits[:, :-1] / nhan[:, 1:]` thanh
    `logits[:, 1:] / nhan[:, :-1]` (lech NGUOC) thi 12 phep kiem truoc do DAT HET, thoat
    ma 0. Doi thanh lech 2 o: cung DAT HET. Tuc la truoc phep kiem nay, huong lech khong
    he duoc ghim o dau trong ca bai. (Chi truong hop bo lech HAN moi bi phep kiem 3 bat,
    va chi bat gian tiep qua gia tri loss luc khoi tao.)

    HAI TANG KIEM
    -------------
    a) Dong nhat thuc: tu tinh lai loss tu chinh logits ma forward() tra ve, theo cap
       (logit tai t <-> nhan tai t+1). Phep nay TAT DINH va chinh xac tuyet doi o ban dung.
    b) Hanh vi: cho mo hinh ti hon hoc thuoc mot chuoi co dinh, roi hoi no doan gi. Day moi
       la phep tach that, vi o mo hinh CHUA huan luyen ba cach ghep cap cho ba gia tri loss
       gan bang nhau (deu ~ln(vocab), co luc chi lech 5,6e-04 — do 26/09/2026), nen mot
       minh tang (a) khong du de phan biet chac chan.
    """
    # --- (a) Dong nhat thuc tren mo hinh chua huan luyen ---
    torch.manual_seed(4242)
    cfg = cau_hinh_ti_hon()
    m = BDSGChoNgonNgu(cfg).eval()
    B, T = 2, 12
    ids = torch.randint(0, cfg.vocab_size, (B, T))
    # nhan KHAC ids de khong vo tinh lam ba cach ghep cap trung nhau.
    nhan = torch.randint(0, cfg.vocab_size, (B, T))

    with torch.no_grad():
        kq = m(ids, nhan=nhan)
        lg = kq.logits.float()
        mong = float(
            F.cross_entropy(
                lg[:, :-1, :].reshape(-1, lg.size(-1)),
                nhan[:, 1:].reshape(-1),
                ignore_index=-100,
            )
        )
    thuc = float(kq.loss)
    bang(
        abs(thuc - mong) < 1e-5,
        "loss cua forward() khong bang cross_entropy(logits[:, :-1], nhan[:, 1:]): "
        "{:.6f} vs {:.6f}. Phep lech nhan da bi dat khac.".format(thuc, mong),
    )

    # --- (b) Hanh vi: hoc thuoc mot chuoi roi hoi no doan gi ---
    m2, day, loss_cuoi = _hoc_thuoc_mot_chuoi()
    B2, T2 = day.shape
    bang(
        loss_cuoi < 0.5,
        "mo hinh khong hoc thuoc noi mot chuoi {} token sau 60 buoc (loss {:.4f}); phep kiem "
        "hanh vi ben duoi chi co nghia khi no da hoc thuoc".format(T2, loss_cuoi),
    )

    with torch.no_grad():
        doan = m2(day).logits.argmax(dim=-1)  # (B2, T2)

    tong = B2 * (T2 - 1)
    ke_tiep = int((doan[:, :-1] == day[:, 1:]).sum())      # dung: logit tai t -> day[t+1]
    chep_lai = int((doan == day).sum())                     # khong lech: logit tai t -> day[t]
    lui_lai = int((doan[:, 1:] == day[:, :-1]).sum())       # lech nguoc: logit tai t -> day[t-1]

    bang(
        ke_tiep >= tong - 1,
        "mo hinh da hoc thuoc chuoi nhung logit tai t KHONG doan day[t+1]: chi khop {}/{}. "
        "Khop 'chep lai chinh no' {}/{}, khop 'lui lai mot o' {}/{}. Phep lech nhan trong "
        "forward() dat sai huong — mo hinh dang hoc chep lai dau vao chu khong hoc du doan.".format(
            ke_tiep, tong, chep_lai, B2 * T2, lui_lai, tong
        ),
    )
    bang(
        ke_tiep > chep_lai and ke_tiep > lui_lai,
        "so khop 'token ke tiep' ({}) khong troi hon 'chep lai chinh no' ({}) va 'lui lai "
        "mot o' ({}) — khong tach duoc ba truong hop".format(ke_tiep, chep_lai, lui_lai),
    )
    return "loss khop dong nhat thuc; sau khi hoc thuoc: ke tiep {}/{}, chep lai {}/{}, lui lai {}/{}".format(
        ke_tiep, tong, chep_lai, B2 * T2, lui_lai, tong
    )


# ======================================================================
# Doi chieu cong thuc voi cac cau hinh that trong kho (KHONG BAT BUOC)
# ======================================================================


def doi_chieu_cau_hinh_kho():
    """Doi chieu so tham so TINH RA voi so ghi trong cac tep cau hinh that cua kho.

    KHONG phai phep kiem bat buoc: cac tep do thuoc thu muc khac va co the dang duoc sua.
    Chay khong dung mo hinh (khong cap phat bo nho), chi tinh cong thuc, nen rat re.
    In ra de nguoi doc tu thay hai nguon so co khop khong.
    """
    thu_muc = os.path.join(GOC_KHO, "huan-luyen", "cau-hinh")
    if not os.path.isdir(thu_muc):
        print("  (bo qua: khong co {})".format(thu_muc))
        return
    ten_tep = sorted(t for t in os.listdir(thu_muc) if t.endswith(".json"))
    if not ten_tep:
        print("  (bo qua: khong co tep .json nao)")
        return
    for ten in ten_tep:
        duong_dan = os.path.join(thu_muc, ten)
        try:
            cfg = CauHinhBDSG.tu_json(duong_dan)
        except Exception as e:  # noqa: BLE001
            print("  {:<12} khong doc duoc: {}: {}".format(ten, type(e).__name__, e))
            continue
        tinh = cfg.so_tham_so()["tong"]
        # So ma tep tu ghi, neu co (nam trong khoa ghi chu "bdsg").
        ghi = None
        bdsg = cfg.bdsg_khac.get("bdsg")
        if isinstance(bdsg, dict):
            for khoa in ("tham_so", "tham_so_uoc_tinh"):
                if isinstance(bdsg.get(khoa), dict) and "tong" in bdsg[khoa]:
                    ghi = bdsg[khoa]["tong"]
                    break
        if ghi is None:
            print("  {:<12} cong thuc tinh ra {:>12,}  (tep khong ghi so de doi chieu)".format(ten, tinh))
        elif int(ghi) == tinh:
            print("  {:<12} cong thuc tinh ra {:>12,}  == so tep ghi  KHOP".format(ten, tinh))
        else:
            print(
                "  {:<12} cong thuc tinh ra {:>12,}  != so tep ghi {:,}  LECH {:+,}".format(
                    ten, tinh, int(ghi), int(ghi) - tinh
                )
            )


# ======================================================================

CAC_PHEP_KIEM = [
    kiem_cau_hinh_chan_loi,
    kiem_json_vong_tron,
    kiem_hinh_dang,
    kiem_so_tham_so,
    kiem_lan_truyen_nguoc,
    kiem_sinh,
    kiem_bo_nho_kv,
    kiem_nhan_qua,
    kiem_rmsnorm,
    kiem_rope,
    kiem_lap_kv,
    kiem_hai_duong_chu_y,
    kiem_huong_lech_nhan,
]


def main() -> int:
    torch.manual_seed(0)
    # Mot luong: ket qua phai lap lai duoc giua cac lan chay va giua cac may.
    torch.set_num_threads(1)

    print("=" * 78)
    print("BAI TU KIEM KIEN TRUC MO HINH BDSG")
    print("=" * 78)
    print("torch   : {}".format(torch.__version__))
    print("python  : {}".format(sys.version.split()[0]))
    print("thiet bi: CPU (bai nay khong can GPU, khong can du lieu, khong can trong so)")
    print()

    cfg = cau_hinh_ti_hon()
    print(cfg.tom_tat())
    print()

    print("PHEP KIEM")
    print("-" * 78)
    tat_ca_dat = True
    for ham in CAC_PHEP_KIEM:
        if not ham():
            tat_ca_dat = False

    print()
    print("DOI CHIEU CONG THUC VOI CAU HINH THAT CUA KHO (khong bat buoc)")
    print("-" * 78)
    try:
        doi_chieu_cau_hinh_kho()
    except Exception as e:  # noqa: BLE001
        print("  (bo qua, loi khi doc: {}: {})".format(type(e).__name__, e))

    print()
    print("=" * 78)
    so_dat = sum(1 for _, dat, _ in _KET_QUA if dat)
    so_hong = len(_KET_QUA) - so_dat
    if tat_ca_dat:
        print("KET QUA: {}/{} DAT.".format(so_dat, len(_KET_QUA)))
        print()
        print("Nghia la gi: ma kien truc chay dung ve HINH DANG va CONG THUC. Cu the, so tham so")
        print("tinh ra khop tuyet doi voi so dem duoc, nen cac uoc luong bo nho va chi phi GPU")
        print("dua tren cong thuc do la dang tin.")
        print("Nghia la gi KHONG: bai nay KHONG noi gi ve chat luong mo hinh. Kien truc nay chua")
        print("tung duoc huan luyen (26/09/2026), chua co trong so nao, chua co phep do chat luong nao.")
    else:
        print("KET QUA: {}/{} DAT, {} HONG.".format(so_dat, len(_KET_QUA), so_hong))
        print()
        print("Cac phep kiem hong:")
        for ten, dat, ghi_chu in _KET_QUA:
            if not dat:
                print("  - {}: {}".format(ten, ghi_chu))
    print("=" * 78)
    return 0 if tat_ca_dat else 1


if __name__ == "__main__":
    sys.exit(main())
