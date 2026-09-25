#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kien truc mo hinh ngon ngu cua BDSG.

Transformer decoder-only viet tu dau bang PyTorch thuan, tu cac ky thuat da cong bo
trong bai bao (RMSNorm, RoPE, GQA, SwiGLU, pre-norm). Xem README.md canh tep nay de
biet bai bao goc cua tung khoi va ly do chon.

DUNG THE NAO
------------
    from mo_hinh import CauHinhBDSG, BDSGChoNgonNgu

    cfg = CauHinhBDSG.tu_json("huan-luyen/cau-hinh/nho.json")
    print(cfg.tom_tat())
    mo_hinh = BDSGChoNgonNgu(cfg)

LUU Y VE TEN THU MUC: thu muc that ten la `mo-hinh` (co gach ngang, theo quy uoc dat ten
cua kho). Gach ngang khong hop le trong ten mo-dun Python, nen khong import truc tiep
`import mo-hinh` duoc. Hai cach dung:
  - chay tep trong thu muc do truc tiep: python3 mo-hinh/thu_kien_truc.py
  - hoac nap bang importlib neu can dung nhu thu vien tu noi khac:
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("mo_hinh", "mo-hinh/__init__.py")
Chua co ban dong goi (setup.py / pyproject.toml) o kho nay tinh den 26/09/2026.

TRANG THAI: chua co trong so nao. Kien truc nay chua tung duoc huan luyen.
"""

from .cau_hinh import (
    CauHinhBDSG,
    LoiCauHinh,
    cau_hinh_ti_hon,
)
from .kien_truc import (
    BDSGChoNgonNgu,
    BoNhoKV,
    ChuYNhomTruyVan,
    KetQuaMoHinh,
    KhoiGiaiMa,
    LopKV,
    MangSwiGLU,
    RMSNorm,
    ap_rope,
    dung_mo_hinh,
    lap_kv,
    quay_nua,
)

__all__ = [
    # Cau hinh
    "CauHinhBDSG",
    "LoiCauHinh",
    "cau_hinh_ti_hon",
    # Mo hinh
    "BDSGChoNgonNgu",
    "dung_mo_hinh",
    "KetQuaMoHinh",
    # Khoi thanh phan (xuat ra de kiem thu va tai su dung tung phan)
    "RMSNorm",
    "ChuYNhomTruyVan",
    "MangSwiGLU",
    "KhoiGiaiMa",
    "ap_rope",
    "quay_nua",
    "lap_kv",
    # Kieu
    "LopKV",
    "BoNhoKV",
]

__version__ = "0.1.0"
