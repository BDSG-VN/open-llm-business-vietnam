#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cau hinh kien truc mo hinh BDSG.

VI SAO CO TEP NAY
-----------------
Kien truc o kien_truc.py khong duoc tu doan kich thuoc cua chinh no. Moi con so
quyet dinh hinh dang tensor (so lop, so dau, be rong) phai nam o MOT cho, doc duoc
bang mat thuong, ghi ra JSON duoc, va phai tu kiem tra duoc TRUOC khi cap phat bo nho.

Ly do rat thuc te: mot rang buoc sai — vi du num_attention_heads khong chia het cho
num_key_value_heads — se khong lam chuong trinh chet ngay. No chay qua khoi tao, chay
qua vai batch, roi no tram o mot phep reshape o giua vong huan luyen, sau khi da an
mat hang chuc phut GPU. Do la loi dat tien nhat trong ca duong ong. Vi vay kiem()
duoc goi ngay trong __post_init__: cau hinh sai thi KHONG TON TAI duoc doi tuong
cau hinh, chu khong phai "tao xong roi hong sau".

VE TEN TRUONG — "CHUAN TRANSFORMERS"
------------------------------------
Cac ten hidden_size, num_hidden_layers, num_attention_heads, num_key_value_heads,
intermediate_size, vocab_size, rms_norm_eps, rope_theta, tie_word_embeddings la quy uoc
dat ten chung cua thu vien transformers, duoc ca he sinh thai dung lai (Llama, Mistral,
Qwen, Gemma... deu dung bo ten nay). Day KHONG phai ten rieng cua mot du an nao.
BDSG giu nguyen bo ten do vi mot ly do ky thuat, khong phai vi tien tay:
neu doi ten, trong so BDSG se khong nap duoc o bat ky cong cu nao khac (llama.cpp,
vLLM, transformers), va muc tieu cua du an la NGUOI DUNG TAI VE MAY CA NHAN CHAY DUOC.
Doi ten truong = tu cat duong ra cua chinh minh.

Truong nao la PHAT MINH RIENG cua BDSG thi mang tien to bdsg_ de phan biet ro, va de
cong cu ngoai co the bo qua chung ma van nap duoc mo hinh.

TRANG THAI SO LIEU (26/09/2026)
-------------------------------
so_tham_so() la so TINH RA tu cong thuc, khong phai so DO tren mo hinh that.
Phep kiem doi chieu "tinh ra == dem duoc tu model.parameters()" nam o thu_kien_truc.py.
BDSG chua huan luyen trong so nao, nen moi con so bo nho o day la uoc tinh tu so tham so,
chua phai so do tren thiet bi that.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Union


class LoiCauHinh(ValueError):
    """Cau hinh vi pham mot rang buoc kien truc.

    Tach rieng khoi ValueError de noi goi co the bat dung loai loi nay ma khong
    nuot nham mot ValueError khac tu torch.
    """


# Cac ten truong "chuan transformers" ma kien truc BDSG doc den. Dung de tu_json()
# biet dau la truong no hieu, dau la truong la (se cat vao bdsg_khac thay vi nem loi).
_TRUONG_CHUAN = (
    "hidden_size",
    "num_hidden_layers",
    "num_attention_heads",
    "num_key_value_heads",
    "head_dim",
    "intermediate_size",
    "vocab_size",
    "hidden_act",
    "max_position_embeddings",
    "rms_norm_eps",
    "rope_theta",
    "tie_word_embeddings",
    "attention_dropout",
    "bos_token_id",
    "eos_token_id",
    "pad_token_id",
    "initializer_range",
)


@dataclass
class CauHinhBDSG:
    """Kich thuoc va sieu tham so kien truc cua mot mo hinh BDSG.

    Gia tri mac dinh o day CO Y la mot mo hinh ti hon (hidden 64, 2 lop) — du de
    chay thu tren CPU trong vai giay. Lam vay de khong ai vo tinh cap phat mot mo hinh
    hang tram trieu tham so chi vi quen truyen tham so. Cau hinh that phai duoc ghi ra
    JSON va nap tuong minh bang tu_json().
    """

    # --- Kich thuoc co ban (chuan transformers) ---
    hidden_size: int = 64
    num_hidden_layers: int = 2
    num_attention_heads: int = 4
    # num_key_value_heads < num_attention_heads => Grouped-Query Attention.
    # Bang num_attention_heads => Multi-Head Attention thong thuong.
    # Bang 1 => Multi-Query Attention.
    num_key_value_heads: int = 2
    # head_dim=None nghia la lay hidden_size // num_attention_heads (quy uoc pho bien).
    # Cho phep dat tuong minh vi mot so ho mo hinh tach head_dim khoi hidden_size.
    head_dim: Optional[int] = None
    intermediate_size: int = 176
    vocab_size: int = 128

    # --- Chuan hoa va vi tri ---
    hidden_act: str = "silu"
    max_position_embeddings: int = 512
    rms_norm_eps: float = 1e-6
    rope_theta: float = 1000000.0

    # --- Buoc ra ---
    tie_word_embeddings: bool = True

    # --- Huan luyen ---
    # LUU Y VE PHAM VI: ten truong la "chuan transformers" nen phai giu, nhung o kien truc
    # nay gia tri do dieu khien BA cho dropout chu khong chi mot: sau o_proj cua khoi chu y,
    # sau xuong_proj cua khoi SwiGLU, va ngay sau embedding. Ghi ro ra day vi mot cau hinh
    # de nguoi doc tuong no chi cham vao chu y la cau hinh noi doi ve cai da chay — dung
    # cai loi ma rang buoc hidden_act o duoi tu choi. Mac dinh 0,0 nen khac biet chi xuat
    # hien khi co nguoi dat khac 0. Khong tach thanh nhieu truong vi them truong ngoai
    # chuan se lam cac cong cu khac bo qua mat, va o quy mo nay chua co so do nao bien minh
    # cho viec dat ba muc dropout khac nhau.
    attention_dropout: float = 0.0
    initializer_range: float = 0.02

    # --- Token dac biet ---
    bos_token_id: Optional[int] = 1
    eos_token_id: Optional[int] = 2
    pad_token_id: Optional[int] = None

    # --- Truong rieng cua BDSG (tien to bdsg_) ---
    bdsg_ten: str = "bdsg-thu-nghiem"
    bdsg_ghi_chu: str = ""
    # Khoi tao co gian du cho cac phep chieu DO VAO NHANH RESIDUAL (o_proj, down_proj):
    # chia do lech chuan cho sqrt(2 * so_lop). Ly do o kien_truc.py, ham _khoi_tao_trong_so.
    bdsg_giam_khoi_tao_residual: bool = True
    # Cho phep dung F.scaled_dot_product_attention cua torch (nhanh hon, it bo nho hon).
    # Tat di de chay duong chu y viet tay — dung khi can doi chieu hai duong voi nhau.
    bdsg_dung_sdpa: bool = True
    # Cac khoa JSON khong thuoc kien truc nay (vi du sieu du lieu cua duong ong du lieu).
    # Giu lai de ra_json() khong lam mat thong tin nguoi dung da ghi trong tep.
    bdsg_khac: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Kiem tra rang buoc
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        # head_dim suy ra truoc khi kiem, vi kiem() can gia tri cuoi cung chu khong
        # phai None. Phep chia nay chi hop le khi hidden_size chia het cho so dau —
        # kiem() se bat truong hop khong chia het ngay ben duoi.
        if self.head_dim is None:
            if self.num_attention_heads > 0 and self.hidden_size % self.num_attention_heads == 0:
                self.head_dim = self.hidden_size // self.num_attention_heads
            else:
                # De nguyen None; kiem() se bao loi voi thong diep ro rang hon la
                # mot ZeroDivisionError hoac mot head_dim le loi.
                pass
        self.kiem()

    def kiem(self) -> "CauHinhBDSG":
        """Kiem moi rang buoc kien truc. Nem LoiCauHinh neu sai. Tra ve chinh no.

        Tra ve self de goi duoc kieu `cfg = CauHinhBDSG(...).kiem()` trong ma noi goi.
        """
        loi: List[str] = []

        def duong(ten: str) -> None:
            gia_tri = getattr(self, ten)
            if not isinstance(gia_tri, int) or isinstance(gia_tri, bool) or gia_tri <= 0:
                loi.append("{} phai la so nguyen duong, dang la {!r}".format(ten, gia_tri))

        for ten in (
            "hidden_size",
            "num_hidden_layers",
            "num_attention_heads",
            "num_key_value_heads",
            "intermediate_size",
            "vocab_size",
            "max_position_embeddings",
        ):
            duong(ten)

        if loi:
            # Dung lai o day: cac phep chia ben duoi khong co nghia neu so co ban da sai,
            # va mot thong diep "chia cho 0" chi lam nguoi doc lac huong.
            raise LoiCauHinh(self._gop_loi(loi))

        # --- Rang buoc 1: hidden_size chia het cho num_attention_heads ---
        # Vi sao: tensor sau q_proj duoc reshape thanh (B, T, so_dau, head_dim).
        # Neu khong chia het, phep reshape se nem loi o GIUA vong huan luyen chu khong
        # phai luc dung cau hinh. Bat o day de no chet som va chet ro.
        if self.hidden_size % self.num_attention_heads != 0:
            loi.append(
                "hidden_size ({}) phai chia het cho num_attention_heads ({}); "
                "du {}".format(
                    self.hidden_size,
                    self.num_attention_heads,
                    self.hidden_size % self.num_attention_heads,
                )
            )

        # --- Rang buoc 2: num_attention_heads chia het cho num_key_value_heads ---
        # Vi sao: GQA cho moi dau key/value phuc vu dung mot NHOM dau query co kich thuoc
        # bang nhau. So dau query moi nhom = num_attention_heads // num_key_value_heads.
        # Neu khong chia het thi khong ton tai cach chia nhom deu, va phep lap KV
        # (lap_kv trong kien_truc.py) se tao ra so dau khong khop voi so dau query.
        if self.num_attention_heads % self.num_key_value_heads != 0:
            loi.append(
                "num_attention_heads ({}) phai chia het cho num_key_value_heads ({}); "
                "GQA can chia nhom deu, du {}".format(
                    self.num_attention_heads,
                    self.num_key_value_heads,
                    self.num_attention_heads % self.num_key_value_heads,
                )
            )

        # --- Rang buoc 3: so dau KV khong duoc vuot so dau query ---
        if self.num_key_value_heads > self.num_attention_heads:
            loi.append(
                "num_key_value_heads ({}) khong duoc lon hon num_attention_heads ({})".format(
                    self.num_key_value_heads, self.num_attention_heads
                )
            )

        # --- Rang buoc 4: head_dim duong va CHAN ---
        # Vi sao phai chan: RoPE quay TUNG CAP toa do (2i, 2i+1) trong moi vector dau.
        # head_dim le thi con mot toa do le khong co cap, khong quay duoc.
        if self.head_dim is None:
            loi.append(
                "head_dim khong suy ra duoc vi hidden_size ({}) khong chia het cho "
                "num_attention_heads ({}); hay dat head_dim tuong minh".format(
                    self.hidden_size, self.num_attention_heads
                )
            )
        else:
            if not isinstance(self.head_dim, int) or isinstance(self.head_dim, bool) or self.head_dim <= 0:
                loi.append("head_dim phai la so nguyen duong, dang la {!r}".format(self.head_dim))
            elif self.head_dim % 2 != 0:
                loi.append(
                    "head_dim ({}) phai la so chan: RoPE quay tung cap toa do, "
                    "so le se con mot toa do khong co cap".format(self.head_dim)
                )

        # --- Rang buoc 5: cac so thuc ---
        if not isinstance(self.rms_norm_eps, (int, float)) or self.rms_norm_eps <= 0:
            loi.append(
                "rms_norm_eps phai > 0 (no nam trong can bac hai o mau so; bang 0 se "
                "chia cho 0 khi gap mot vector toan so khong), dang la {!r}".format(self.rms_norm_eps)
            )
        if not isinstance(self.rope_theta, (int, float)) or self.rope_theta <= 1:
            loi.append(
                "rope_theta phai > 1 (no la co so cua luy thua tan so), "
                "dang la {!r}".format(self.rope_theta)
            )
        if not isinstance(self.attention_dropout, (int, float)) or not (0.0 <= float(self.attention_dropout) < 1.0):
            loi.append(
                "attention_dropout phai trong [0, 1), dang la {!r}".format(self.attention_dropout)
            )
        if not isinstance(self.initializer_range, (int, float)) or self.initializer_range <= 0:
            loi.append("initializer_range phai > 0, dang la {!r}".format(self.initializer_range))

        # --- Rang buoc 6: ham kich hoat ---
        # Chi nhan "silu". Vi sao chi mot: khoi feed-forward la SwiGLU, va cong thuc
        # SwiGLU trong bai bao goc (arXiv:2002.05202) dung Swish/SiLU. Nhan them ten khac
        # ma khong cai dat se tao ra mot cau hinh "hop le" nhung mo hinh lai chay silu —
        # tuc la cau hinh NOI DOI ve cai da chay. Tha tu choi con hon.
        if self.hidden_act != "silu":
            loi.append(
                "hidden_act chi ho tro 'silu' (khoi SwiGLU dung Swish/SiLU theo "
                "arXiv:2002.05202), dang la {!r}".format(self.hidden_act)
            )

        # --- Rang buoc 7: token dac biet phai nam trong tu vung ---
        for ten in ("bos_token_id", "eos_token_id", "pad_token_id"):
            gia_tri = getattr(self, ten)
            if gia_tri is None:
                continue
            if not isinstance(gia_tri, int) or isinstance(gia_tri, bool):
                loi.append("{} phai la so nguyen hoac None, dang la {!r}".format(ten, gia_tri))
            elif not (0 <= gia_tri < self.vocab_size):
                loi.append(
                    "{} = {} nam ngoai tu vung [0, {}); embedding se nem loi chi so "
                    "o batch dau tien".format(ten, gia_tri, self.vocab_size)
                )

        if loi:
            raise LoiCauHinh(self._gop_loi(loi))
        return self

    def _gop_loi(self, loi: List[str]) -> str:
        dau = "Cau hinh BDSG khong hop le ({} loi):".format(len(loi))
        return dau + "".join("\n  - " + d for d in loi)

    # ------------------------------------------------------------------
    # Gia tri suy ra
    # ------------------------------------------------------------------

    @property
    def so_dau_moi_nhom(self) -> int:
        """So dau query dung chung mot dau key/value. Bang 1 tuc la MHA thuan."""
        return self.num_attention_heads // self.num_key_value_heads

    @property
    def chieu_q(self) -> int:
        """Tong chieu dau ra cua q_proj."""
        return self.num_attention_heads * int(self.head_dim)

    @property
    def chieu_kv(self) -> int:
        """Tong chieu dau ra cua k_proj (va v_proj)."""
        return self.num_key_value_heads * int(self.head_dim)

    # ------------------------------------------------------------------
    # Dem tham so (TINH RA, khong phai do)
    # ------------------------------------------------------------------

    def so_tham_so(self) -> Dict[str, int]:
        """Tinh so tham so tu cong thuc, khong can torch, khong can dung mo hinh.

        VI SAO QUAN TRONG: moi uoc luong bo nho, thoi gian va chi phi thue GPU deu bat
        dau tu con so nay. Mot cong thuc sai o day lam sai TOAN BO du toan, va khong ai
        phat hien ra cho toi luc da tra tien GPU. Vi vay thu_kien_truc.py doi chieu con so
        nay voi so DEM DUOC tu model.parameters() — do la phep kiem quan trong nhat trong
        ca bai tu kiem.

        CACH DEM (khop tung dong voi kien_truc.py, moi phep chieu deu bias=False):
          embedding : vocab_size * hidden_size
          lm_head   : vocab_size * hidden_size, va CHI dem khi tie_word_embeddings=False.
                      Khi tie=True, lm_head.weight VA embed_tokens.weight la cung mot
                      doi tuong Parameter; nn.Module.parameters() loc trung nen chi dem mot lan.
          moi lop:
            q_proj  : hidden_size * (num_attention_heads * head_dim)
            k_proj  : hidden_size * (num_key_value_heads * head_dim)
            v_proj  : hidden_size * (num_key_value_heads * head_dim)
            o_proj  : (num_attention_heads * head_dim) * hidden_size
            2 RMSNorm : 2 * hidden_size  (chuan hoa truoc chu y + truoc feed-forward)
            SwiGLU  : 3 * hidden_size * intermediate_size  (cong, len, xuong)
          cuoi    : hidden_size  (RMSNorm truoc lm_head)
        KHONG dem: bang cos/sin cua RoPE. Chung la buffer khong hoc, va duoc dang ky
        voi persistent=False nen cung khong nam trong state_dict.
        """
        h = self.hidden_size
        d = int(self.head_dim)
        nq = self.num_attention_heads
        nkv = self.num_key_value_heads
        ffn = self.intermediate_size

        embedding = self.vocab_size * h
        lm_head = 0 if self.tie_word_embeddings else self.vocab_size * h

        chu_y_moi_lop = (
            h * (nq * d)  # q_proj
            + h * (nkv * d)  # k_proj
            + h * (nkv * d)  # v_proj
            + (nq * d) * h  # o_proj
        )
        ffn_moi_lop = 3 * h * ffn
        norm_moi_lop = 2 * h
        moi_lop = chu_y_moi_lop + ffn_moi_lop + norm_moi_lop

        cac_lop = moi_lop * self.num_hidden_layers
        norm_cuoi = h

        tong = embedding + lm_head + cac_lop + norm_cuoi
        return {
            "embedding": embedding,
            "lm_head": lm_head,
            "chu_y_moi_lop": chu_y_moi_lop,
            "ffn_moi_lop": ffn_moi_lop,
            "norm_moi_lop": norm_moi_lop,
            "moi_lop": moi_lop,
            "cac_lop": cac_lop,
            "norm_cuoi": norm_cuoi,
            "tong": tong,
        }

    def bo_nho_trong_so_MB(self, byte_moi_tham_so: int = 2) -> float:
        """Bo nho chi cho TRONG SO, theo MB thap phan (1 MB = 1e6 byte).

        Mac dinh 2 byte = fp16/bf16. CHUA tinh: activation, KV cache, trang thai
        toi uu hoa. Dung con so nay de hua "chay vua X GB" la sai.
        """
        return self.so_tham_so()["tong"] * byte_moi_tham_so / 1e6

    def bo_nho_kv_cache_MB(self, do_dai: int, so_chuoi: int = 1, byte_moi_tham_so: int = 2) -> float:
        """Bo nho KV cache cho `so_chuoi` chuoi dai `do_dai` token.

        VI SAO CO HAM NAY: day chinh la con so bien minh cho lua chon GQA (xem kien_truc.py).
        Voi MHA, thay num_key_value_heads bang num_attention_heads trong cong thuc nay.
        Cong thuc: 2 (K va V) * so_lop * so_dau_kv * head_dim * do_dai * so_chuoi * byte.
        """
        so_o = (
            2
            * self.num_hidden_layers
            * self.num_key_value_heads
            * int(self.head_dim)
            * do_dai
            * so_chuoi
        )
        return so_o * byte_moi_tham_so / 1e6

    # ------------------------------------------------------------------
    # Doc / ghi JSON
    # ------------------------------------------------------------------

    def ra_dict(self) -> Dict[str, Any]:
        """Xuat thanh dict thuan, phang. bdsg_khac duoc rai nguoc ra muc goc."""
        d: Dict[str, Any] = {}
        for f in fields(self):
            if f.name == "bdsg_khac":
                continue
            d[f.name] = getattr(self, f.name)
        # Rai cac khoa la NGUOC ra ngoai, nhung khong de chung de len khoa that.
        for k, v in self.bdsg_khac.items():
            if k not in d:
                d[k] = v
        return d

    def ra_json(self, dep: bool = True) -> str:
        """Xuat thanh chuoi JSON."""
        return json.dumps(
            self.ra_dict(),
            ensure_ascii=False,
            indent=2 if dep else None,
            sort_keys=False,
        )

    def ghi_tep(self, duong_dan: str) -> str:
        """Ghi cau hinh ra tep JSON. Tra ve duong dan da ghi."""
        with open(duong_dan, "w", encoding="utf-8") as f:
            f.write(self.ra_json())
            f.write("\n")
        return duong_dan

    @classmethod
    def tu_dict(cls, d: Dict[str, Any]) -> "CauHinhBDSG":
        """Dung cau hinh tu mot dict.

        Khoa KHONG thuoc kien truc duoc cat vao bdsg_khac thay vi nem loi. Ly do:
        cac tep cau hinh trong kho con mang sieu du lieu cua duong ong du lieu
        (muc dich, canh bao, uoc tinh...). Nem loi vi mot khoa ghi chu la thai do sai —
        nhung IM LANG BO MAT chung khi ghi lai cung sai. Nen: giu lai, va ra_json()
        tra chung ve cho cu.
        """
        if not isinstance(d, dict):
            raise LoiCauHinh("tu_dict can mot dict, nhan duoc {}".format(type(d).__name__))

        ten_truong = {f.name for f in fields(cls)}
        biet: Dict[str, Any] = {}
        la: Dict[str, Any] = {}
        for k, v in d.items():
            if k in ten_truong and k != "bdsg_khac":
                biet[k] = v
            else:
                la[k] = v

        # Ep kieu nhe cho cac truong so: JSON co the cho 1e-6 thanh float, 8 thanh int.
        # Khong ep bua — chi ep khi gia tri ro rang la so.
        for k in ("hidden_size", "num_hidden_layers", "num_attention_heads",
                  "num_key_value_heads", "intermediate_size", "vocab_size",
                  "max_position_embeddings", "head_dim"):
            if k in biet and isinstance(biet[k], float) and float(biet[k]).is_integer():
                biet[k] = int(biet[k])

        cfg = cls(**biet)
        cfg.bdsg_khac = la
        return cfg

    @classmethod
    def tu_json(cls, nguon: Union[str, bytes, Dict[str, Any]]) -> "CauHinhBDSG":
        """Dung cau hinh tu JSON.

        `nguon` nhan ba dang, phan biet bang noi dung chu khong bang tham so rieng:
          - dict            -> dung truc tiep
          - chuoi JSON      -> chuoi bat dau bang '{' (sau khi cat khoang trang)
          - duong dan tep   -> moi chuoi con lai
        Lam vay de noi goi khong phai nho hai ten ham khac nhau cho cung mot viec.
        """
        if isinstance(nguon, dict):
            return cls.tu_dict(nguon)

        if isinstance(nguon, bytes):
            nguon = nguon.decode("utf-8")

        if not isinstance(nguon, str):
            raise LoiCauHinh(
                "tu_json can dict, chuoi JSON hoac duong dan tep; nhan duoc {}".format(
                    type(nguon).__name__
                )
            )

        cat = nguon.strip()
        if cat.startswith("{"):
            try:
                d = json.loads(cat)
            except json.JSONDecodeError as e:
                raise LoiCauHinh("Chuoi JSON hong: {}".format(e)) from e
            return cls.tu_dict(d)

        if not os.path.exists(nguon):
            raise LoiCauHinh(
                "Khong tim thay tep cau hinh: {!r} (chuoi khong bat dau bang '{{' nen "
                "duoc hieu la duong dan)".format(nguon)
            )
        with open(nguon, "r", encoding="utf-8") as f:
            try:
                d = json.load(f)
            except json.JSONDecodeError as e:
                raise LoiCauHinh("Tep {} chua JSON hong: {}".format(nguon, e)) from e
        return cls.tu_dict(d)

    # ------------------------------------------------------------------

    def tom_tat(self) -> str:
        """Mot khoi chu nguoi doc duoc, de in ra log truoc khi huan luyen."""
        ts = self.so_tham_so()
        dong = [
            "Cau hinh BDSG: {}".format(self.bdsg_ten),
            "  hidden_size          = {}".format(self.hidden_size),
            "  num_hidden_layers    = {}".format(self.num_hidden_layers),
            "  num_attention_heads  = {}".format(self.num_attention_heads),
            "  num_key_value_heads  = {}  (GQA {}:1)".format(
                self.num_key_value_heads, self.so_dau_moi_nhom
            ),
            "  head_dim             = {}".format(self.head_dim),
            "  intermediate_size    = {}".format(self.intermediate_size),
            "  vocab_size           = {}".format(self.vocab_size),
            "  tie_word_embeddings  = {}".format(self.tie_word_embeddings),
            "  rope_theta           = {}".format(self.rope_theta),
            "  rms_norm_eps         = {}".format(self.rms_norm_eps),
            "  --- tham so (TINH RA, chua do) ---",
            "  tong                 = {:,} ({:.2f} trieu)".format(ts["tong"], ts["tong"] / 1e6),
            "  trong so fp16        = {:.1f} MB".format(self.bo_nho_trong_so_MB(2)),
            "  KV cache 2048 token  = {:.1f} MB (fp16, 1 chuoi)".format(
                self.bo_nho_kv_cache_MB(2048, 1, 2)
            ),
        ]
        return "\n".join(dong)


def cau_hinh_ti_hon() -> CauHinhBDSG:
    """Mo hinh ti hon dung cho bai tu kiem: chay tren CPU trong vai giay.

    Cac so nay chon de bat loi hinh dang chu khong de hoc duoc gi:
      - hidden 64 / 2 lop / vocab 128: du nho de mot buoc lan truyen nguoc xong tuc thi.
      - 4 dau query tren 2 dau KV: BUOC duong lap KV (so_dau_moi_nhom=2) phai chay,
        chu khong roi vao truong hop tam thuong nkv == nq.
      - hidden 64 / 4 dau = head_dim 16, so chan, RoPE quay duoc.
    """
    return CauHinhBDSG(
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        intermediate_size=176,
        vocab_size=128,
        max_position_embeddings=256,
        tie_word_embeddings=True,
        bdsg_ten="bdsg-ti-hon-tu-kiem",
        bdsg_ghi_chu="Chi dung cho thu_kien_truc.py. Khong phai cau hinh huan luyen.",
    )


if __name__ == "__main__":
    # Chay truc tiep de xem cau hinh mac dinh va so tham so tinh ra.
    cfg = cau_hinh_ti_hon()
    print(cfg.tom_tat())
    print()
    print("Vi du GQA tiet kiem bao nhieu KV cache o mot cau hinh 512/8 lop/8 dau:")
    gqa = CauHinhBDSG(
        hidden_size=512, num_hidden_layers=8, num_attention_heads=8,
        num_key_value_heads=2, intermediate_size=1408, vocab_size=24576,
        max_position_embeddings=2048, bdsg_ten="vi-du-gqa",
    )
    mha = CauHinhBDSG(
        hidden_size=512, num_hidden_layers=8, num_attention_heads=8,
        num_key_value_heads=8, intermediate_size=1408, vocab_size=24576,
        max_position_embeddings=2048, bdsg_ten="vi-du-mha",
    )
    print("  GQA kv=2 : {:.1f} MB KV cache o 2048 token".format(gqa.bo_nho_kv_cache_MB(2048)))
    print("  MHA kv=8 : {:.1f} MB KV cache o 2048 token".format(mha.bo_nho_kv_cache_MB(2048)))
    print("  Tham so  : GQA {:,} vs MHA {:,}".format(
        gqa.so_tham_so()["tong"], mha.so_tham_so()["tong"]))
