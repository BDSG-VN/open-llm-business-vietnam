#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phan dung chung cua bo huan luyen BDSG.

=============================================================================
VI SAO CO TEP NAY
=============================================================================
huan_luyen.py (tien huan luyen) va tinh_chinh.py (SFT) khac nhau o dung MOT
diem: cach bien du lieu thanh (ids, nhan). Moi thu con lai — chon thiet bi, nap
kien truc, nap tu vung, lich hoc suat, cat gradient, tich luy gradient, diem
dung, dong ho token/giay — la y het nhau.

Chep hai ban cua nhung thu do la cach chac chan nhat de sau sau thang chung
lech nhau ma khong ai biet. Nen chung nam o day, mot ban.

=============================================================================
TEP NAY PHU THUOC GI
=============================================================================
  torch        — BAT BUOC luc chay, KHONG bat buoc luc `python3 -m py_compile`.
                 Import duoc boc trong try/except de `--help` va py_compile chay
                 duoc tren may chua cai torch (moi truong .venv cua kho nay ngay
                 26/09/2026 chua co torch: co tokenizers 0.22.2, khong co torch).
  tokenizers   — co san trong .venv cua kho.
  mo-hinh/     — thu muc kien truc do NHOM KHAC dang viet. Ngay 26/09/2026 thu
                 muc nay CHUA TON TAI. Cac ham o day nap no theo duong dan va
                 bao loi ro rang neu chua co, chu khong im lang.

=============================================================================
HOP DONG VOI mo-hinh/ — DOC RA TU MA THAT NGAY 26/09/2026, KHONG PHAI GIA DINH
=============================================================================
Thu muc mo-hinh/ do NHOM KHAC viet. Ngay 26/09/2026 no DA CO MA. Cac dong duoi
day duoc doc thang tu mo-hinh/__init__.py va mo-hinh/kien_truc.py, khong doan:

1. mo-hinh/ lo ra `CauHinhBDSG` va `BDSGChoNgonNgu`.
   (Ban dac ta ban dau cua viec nay goi lop mo hinh la `MoHinhBDSG`. Ten that la
   `BDSGChoNgonNgu`. Ham nap o day chap nhan CA HAI ten, uu tien ten that.)

2. CauHinhBDSG(...) nhan cac truong CHUAN TRANSFORMERS: hidden_size,
   num_hidden_layers, num_attention_heads, num_key_value_heads, head_dim,
   intermediate_size, vocab_size, hidden_act, max_position_embeddings,
   rms_norm_eps, rope_theta, tie_word_embeddings, attention_dropout,
   initializer_range, bos/eos/pad_token_id.
   No KHONG nhan attention_bias / mlp_bias: kien truc cua BDSG khong co bias o
   bat cu phep chieu tuyen tinh nao, do la tinh chat co dinh cua kien truc chu
   khong phai mot cong tac bat tat. Cac tep cau hinh trong cau-hinh/ da bo hai
   khoa do. Ham dung_cau_hinh() ben duoi VAN kiem lai, va bao ro neu co khoa
   la — khong am tham vut di.

3. BDSGChoNgonNgu(cfg).forward(ids, nhan=None, bo_nho_kv=None, dung_bo_nho=False)
   tra ve mot doi tuong `KetQuaMoHinh` co ba truong: .logits, .loss, .bo_nho_kv
   (dataclass, KHONG phai tuple). goi_mo_hinh() ben duoi doc duoc ca dataclass
   lan tuple, nen hai ben doi qua lai khong lam hong tep nay.

4. LE MOT BUOC — DIEU QUAN TRONG NHAT, VA NO DA TUNG LA CHO LECH THAT:
   mo-hinh/ TU DICH NHAN BEN TRONG forward(). Ma cua ho (kien_truc.py):

       nhan_lech = nhan[:, 1:]
       loss = cross_entropy(logits[:, :-1], nhan_lech, ignore_index=-100)

   Nghia la quy uoc cua ho: `nhan` co CUNG HINH DANG voi `ids` va chua CHINH
   CHUOI TOKEN DO, khong dich truoc. Mo hinh moi la ben dich.

   Ban dac ta ban dau cua bo huan luyen nay noi nguoc lai: ben goi dich san.
   Hai quy uoc deu chay duoc, deu khong nem loi, va neu ap CA HAI thi chuoi bi
   dich HAI LAN: mo hinh hoc du doan token cach hai buoc, loss van giam deu, do
   thi van dep, chi rieng ket qua sinh chu la hong. Dung ho loi "hong ma khong
   bao" ma kho nay dat ra de chong.

   QUYET DINH: huan-luyen/ DI THEO QUY UOC CUA mo-hinh/. Ly do khong phai ky
   thuat ma la quyen so huu — mo-hinh/ la thu muc cua nhom khac, bo huan luyen
   khong duoc sua vao do, nen ben phai nhuong la ben nay. Cu the:

       ids  = chuoi token day du            (B, T)
       nhan = CUNG chuoi token do, dat -100 o nhung vi tri khong muon giam sat

   Vi mo hinh bo nhan dau tien (nhan[:, 1:]), nhan[0] khong bao gio duoc dung —
   do la dieu binh thuong, va cac cho dem "so token co nhan" o day deu dem tu
   vi tri 1 tro di cho khop voi thuc te.

5. NHAN = -100 nghia la BO QUA vi tri do (quy uoc ignore_index mac dinh cua
   torch.nn.functional.cross_entropy).

CACH DO LAI LE MOT BUOC BAT CU LUC NAO:

    python3 huan_luyen.py --tu-kiem-dich --cau-hinh cau-hinh/nho.json

No bat mo hinh hoc thuoc mot lo nho roi doi chieu du doan, va in ra hai ti le
canh nhau: khop voi token KE TIEP, va khop voi token CACH HAI. Neu mot ngay nao
do mo-hinh/ doi quy uoc, bai nay bao ngay — truoc khi tieu mot giay GPU nao.
"""

import array
import collections
import importlib.util
import json
import math
import os
import random
import sys
import time

# ---------------------------------------------------------------------------
# torch: bat buoc luc chay, khong bat buoc luc bien dich
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn.functional as F
    _LOI_TORCH = None
except ImportError as loi:          # pragma: no cover - tuy may
    torch = None
    F = None
    _LOI_TORCH = loi


def doi_hoi_torch():
    """Dung han voi loi doc duoc neu may chua cai torch.

    VI SAO KHONG DE NO NO TU NHIEN: ImportError tran ra giua vong huan luyen thi
    thong diep la 'No module named torch' o mot dong ngau nhien. O day noi ro
    phai cai gi va vi sao tep requirements cua kho khong tu cai.
    """
    if torch is None:
        raise SystemExit(
            "Chua cai torch.\n"
            "  Bo huan luyen can torch; cac buoc chuan bi du lieu va tu vung thi khong.\n"
            "  Kho nay co y KHONG ghi torch vao danh sach phu thuoc chung, vi ban torch\n"
            "  dung cho CPU, cho CUDA va cho Apple Silicon la ba goi khac nhau — chon ho\n"
            "  nguoi dung la chon sai.\n"
            "  Cai theo huong dan o pytorch.org, roi chay lai.\n"
            "  Loi goc: {}".format(_LOI_TORCH))


# ---------------------------------------------------------------------------
# Thiet bi
# ---------------------------------------------------------------------------
def chon_thiet_bi(yeu_cau="tu-dong"):
    """Chon thiet bi tinh toan. 'tu-dong' = cuda > mps > cpu.

    VI SAO THU TU DO: cuda nhanh nhat khi co. mps (Apple Silicon) nhanh hon cpu
    dang ke o cac phep nhan ma tran lon, va may lam viec cua BDSG la Apple M1 —
    bo mps di thi ban nho khong con cho nao chay thu duoc truoc khi thue GPU.
    """
    doi_hoi_torch()
    if yeu_cau != "tu-dong":
        return torch.device(yeu_cau)
    if torch.cuda.is_available():
        return torch.device("cuda")
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def mo_ta_thiet_bi(thiet_bi):
    doi_hoi_torch()
    ten = thiet_bi.type
    if ten == "cuda":
        chi_so = thiet_bi.index or 0
        thuoc_tinh = torch.cuda.get_device_properties(chi_so)
        return "cuda:{} — {} ({:.1f} GB)".format(
            chi_so, thuoc_tinh.name, thuoc_tinh.total_memory / 1024.0 ** 3)
    if ten == "mps":
        return "mps — Apple Silicon (bo nho dung chung voi he thong)"
    return "cpu"


def kieu_du_lieu_tu_dong(thiet_bi, bat_amp):
    """Tra ve (dung_autocast, kieu, dung_gradscaler).

    VI SAO KHONG BAT AMP MOI NOI:
      - CUDA co bf16 (Ampere tro len): dung bf16, KHONG can GradScaler vi bf16 co
        cung dai so mu nhu fp32 nen khong tran duoi.
      - CUDA khong co bf16: dung fp16 + GradScaler. Thieu GradScaler thi gradient
        fp16 tran ve 0 va loss dung im — lai la mot loi khong bao.
      - MPS: autocast tren MPS con thieu nhieu phep va tung tra ket qua khac CPU.
        Mac dinh TAT. Ai muon thu thi tu bat, va phai tu kiem lai ket qua.
      - CPU: bf16 tren CPU chi nhanh khi co AVX512-BF16/AMX. Mac dinh TAT.
    """
    doi_hoi_torch()
    if not bat_amp:
        return False, None, False
    if thiet_bi.type == "cuda":
        if torch.cuda.is_bf16_supported():
            return True, torch.bfloat16, False
        return True, torch.float16, True
    return False, None, False


# ---------------------------------------------------------------------------
# Kien truc: nap tu thu muc mo-hinh/
# ---------------------------------------------------------------------------
def nap_kien_truc(thu_muc):
    """Nap CauHinhBDSG va MoHinhBDSG tu thu muc mo-hinh/.

    VI SAO PHAI NAP BANG DUONG DAN CHU KHONG PHAI `import mo_hinh`:
    thu muc ten la 'mo-hinh', co dau gach ngang. Dinh danh module Python khong
    duoc chua gach ngang, nen `import mo-hinh` la loi cu phap va khong cach nao
    lach duoc bang cu phap import thong thuong. importlib nap theo duong dan tep
    thi khong vuong dieu do — va giu duoc ten thu muc tieng Viet khong dau dung
    quy uoc dat ten cua kho.

    Ho tro ca hai cach nhom kia co the to chuc ma:
      (a) mo-hinh/__init__.py  -> nap nhu mot GOI, de import tuong doi ben trong
          (vi du `from .lop_chu_y import ChuY`) van chay.
      (b) mo-hinh/*.py roi rac -> nap tung tep cho den khi thay du hai ten.
    """
    thu_muc = os.path.abspath(thu_muc)
    if not os.path.isdir(thu_muc):
        raise SystemExit(
            "Khong thay thu muc kien truc: {}\n"
            "  Bo huan luyen nay PHU THUOC vao mo-hinh/ — noi dinh nghia CauHinhBDSG\n"
            "  va MoHinhBDSG. Thu muc do do NHOM KHAC viet va ngay 26/09/2026 chua\n"
            "  ton tai. Cac tep trong huan-luyen/ duoc viet truoc, co chu y, de khi\n"
            "  mo-hinh/ xong thi khong phai viet lai gi.\n"
            "  Doi duong dan bang --thu-muc-mo-hinh neu no nam cho khac.".format(thu_muc))

    ten_goi = "bdsg_kien_truc"
    duong_init = os.path.join(thu_muc, "__init__.py")

    if os.path.isfile(duong_init):
        spec = importlib.util.spec_from_file_location(
            ten_goi, duong_init, submodule_search_locations=[thu_muc])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[ten_goi] = mod
        spec.loader.exec_module(mod)
        ung_vien = [mod]
    else:
        # Them thu muc vao sys.path de cac tep trong do import lan nhau duoc
        # bang ten thuong (`import lop_chu_y`). Them vao DAU danh sach, va chi
        # them mot lan — day la cho hay sai khi chay script trong container.
        if thu_muc not in sys.path:
            sys.path.insert(0, thu_muc)
        ung_vien = []
        # Uu tien vai ten de doan truoc, roi den moi tep .py con lai. Uu tien de
        # khong phai nap het ca thu muc chi de tim hai ten.
        ten_tep = sorted(t for t in os.listdir(thu_muc) if t.endswith(".py"))
        uu_tien = ["mo_hinh.py", "kien_truc.py", "mo_hinh_bdsg.py"]
        ten_tep = ([t for t in uu_tien if t in ten_tep]
                   + [t for t in ten_tep if t not in uu_tien])
        for t in ten_tep:
            ten_mod = "{}_{}".format(ten_goi, os.path.splitext(t)[0])
            spec = importlib.util.spec_from_file_location(
                ten_mod, os.path.join(thu_muc, t))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[ten_mod] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception as loi:      # tep phu co the loi rieng, khong chan
                print("  [canh bao] khong nap duoc {}: {}".format(t, loi))
                continue
            ung_vien.append(mod)
            if _tim_hai_ten(mod):
                break

    for mod in ung_vien:
        cap = _tim_hai_ten(mod)
        if cap:
            return cap

    raise SystemExit(
        "Nap duoc {} nhung khong thay cap ten can tim.\n"
        "  Can: CauHinhBDSG, va mot trong cac ten lop mo hinh {}.\n"
        "  Hop dong day du giua huan-luyen/ va mo-hinh/ ghi o dau huan-luyen/chung.py."
        .format(thu_muc, list(TEN_LOP_MO_HINH)))


# Ten that trong mo-hinh/ (doc 26/09/2026) la BDSGChoNgonNgu. MoHinhBDSG la ten
# trong ban dac ta ban dau cua bo huan luyen. Chap nhan ca hai, uu tien ten that.
TEN_LOP_MO_HINH = ("BDSGChoNgonNgu", "MoHinhBDSG")


def _tim_hai_ten(mod):
    if not hasattr(mod, "CauHinhBDSG"):
        return None
    for ten in TEN_LOP_MO_HINH:
        if hasattr(mod, ten):
            return mod.CauHinhBDSG, getattr(mod, ten)
    return None


# ---------------------------------------------------------------------------
# Cau hinh va tu vung
# ---------------------------------------------------------------------------
def nap_cau_hinh(duong_dan):
    """Doc tep .json cau hinh, bo khoa ghi chu 'bdsg'."""
    with open(duong_dan, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    ghi_chu = cfg.pop("bdsg", None)
    return cfg, ghi_chu


def nap_tu_vung(duong_dan):
    """Nap tokenizer.json bang thu vien `tokenizers` (khong can transformers).

    VI SAO KHONG DUNG transformers: ca bo chuan bi du lieu cua kho nay chay bang
    Python thuan + tokenizers, de lam duoc tren may xach tay. Keo transformers
    vao chi de doc mot tep .json la them mot phu thuoc nang ma khong duoc gi.
    """
    try:
        from tokenizers import Tokenizer
    except ImportError as loi:
        raise SystemExit(
            "Chua cai thu vien `tokenizers`: {}\n"
            "  pip install tokenizers".format(loi))
    if os.path.isdir(duong_dan):
        duong_dan = os.path.join(duong_dan, "tokenizer.json")
    if not os.path.isfile(duong_dan):
        raise SystemExit(
            "Khong thay tu vung: {}\n"
            "  Tu vung do huan-luyen/tu-vung/huan_luyen_tu_vung.py sinh ra.".format(duong_dan))
    return Tokenizer.from_file(duong_dan)


def kiem_tu_vung(tok, cfg, duong_dan_tu_vung):
    """Dung han neu vocab_size trong cau hinh lech voi tu vung that.

    VI SAO KIEM: day la loi im lang kinh dien cua ca ho bo huan luyen nay.
      - Cau hinh khai vocab_size LON hon tu vung that: khong bao loi gi ca. Mo
        hinh co mot mang embedding khong bao gio duoc dung va khong bao gio duoc
        hoc; no chi an bo nho va lam logits co nhung cot vinh vien la rac.
      - Cau hinh khai vocab_size NHO hon tu vung that: bao loi chi so ngay batch
        dau — truong hop nay may, vi no on ao.
    Truong hop thu nhat la truong hop nguy hiem. Nen kiem o day, truoc khi tieu
    mot giay GPU nao.
    """
    that = tok.get_vocab_size()
    khai = cfg.get("vocab_size")
    if khai is None:
        raise SystemExit("Cau hinh khong co truong vocab_size.")
    if that != khai:
        raise SystemExit(
            "vocab_size LECH — dung han truoc khi huan luyen.\n"
            "  cau hinh khai : {}\n"
            "  tu vung that  : {}  ({})\n"
            "  Lech kieu 'cau hinh lon hon tu vung' KHONG bao loi luc chay: no chi\n"
            "  tao ra mot mang embedding chet, hoc mai khong toi. Sua mot trong hai\n"
            "  cho cho khop roi chay lai.".format(khai, that, duong_dan_tu_vung))
    return that


def id_token_dac_biet(tok, ten):
    """Tra ve id cua mot token dac biet theo NOI DUNG chu, hoac None.

    VI SAO TRA CUU THEO NOI DUNG CHU KHONG PHAI THEO SO CO DINH: cau hinh ghi
    bos_token_id=1, eos_token_id=2 vi tu vung hien tai dat nhu vay. Neu ai huan
    luyen lai tu vung va thu tu token dac biet doi, con so cung trong cau hinh
    se im lang tro thanh SAI. Tra cuu theo chu thi lech se lo ra ngay.
    """
    return tok.token_to_id(ten)


# ---------------------------------------------------------------------------
# Doc du lieu
# ---------------------------------------------------------------------------
def doc_jsonl(duong_dan, bao_loi_dong=True):
    """Doc tep .jsonl, tra ve tung dict. Bo qua dong trong.

    Dong hong duoc DEM va BAO, khong duoc nuot im lang: mot tep 2 trieu dong ma
    hong 1,9 trieu dong thi van 'chay xong', va do la cach de tieu tien GPU cho
    mot phan tram du lieu.
    """
    so_hong = 0
    with open(duong_dan, "r", encoding="utf-8") as f:
        for so_dong, dong in enumerate(f, 1):
            dong = dong.strip()
            if not dong:
                continue
            try:
                yield json.loads(dong)
            except ValueError:
                so_hong += 1
                if bao_loi_dong and so_hong <= 5:
                    print("  [canh bao] {}:{} khong phai JSON hop le".format(
                        os.path.basename(duong_dan), so_dong))
    if so_hong:
        print("  [canh bao] tong cong {} dong hong trong {}".format(
            so_hong, os.path.basename(duong_dan)))


def liet_ke_tep(duong_dan):
    """Nhan mot tep .jsonl hoac mot thu muc chua chung. Tra ve danh sach tep."""
    if os.path.isdir(duong_dan):
        ra = sorted(os.path.join(duong_dan, t) for t in os.listdir(duong_dan)
                    if t.endswith(".jsonl"))
        if not ra:
            raise SystemExit("Thu muc {} khong co tep .jsonl nao.".format(duong_dan))
        return ra
    if not os.path.isfile(duong_dan):
        raise SystemExit("Khong thay du lieu: {}".format(duong_dan))
    return [duong_dan]


def dung_cau_hinh(CauHinhBDSG, cfg):
    """Goi CauHinhBDSG(**cfg), loc bo khoa ma lop do khong nhan — MOT CACH ON AO.

    VI SAO KHONG GOI THANG CauHinhBDSG(**cfg): hai thu muc do hai nhom giu, va
    tap truong cau hinh cua hai ben se troi khoi nhau theo thoi gian. Goi thang
    thi mot khoa thua lam ca lan chay chet bang TypeError kho doc.

    VI SAO KHONG AM THAM VUT KHOA LA: vut im lang la cach danh mat mot tham so
    quan trong. Neu khoa bi bo nam trong danh sach TRONG YEU (vocab_size, so
    lop, ...) thi ham nay DUNG HAN — vi mo hinh dung mac dinh cua no thay cho
    con so ta khai la mot mo hinh khac han cai ta dinh dung, ma khong bao gi.
    Khoa khong trong yeu thi bi bo, nhung duoc IN RA.
    """
    import inspect
    TRONG_YEU = {"vocab_size", "hidden_size", "num_hidden_layers",
                 "num_attention_heads", "num_key_value_heads", "head_dim",
                 "intermediate_size", "max_position_embeddings",
                 "tie_word_embeddings", "rms_norm_eps", "rope_theta"}
    try:
        tham_so = inspect.signature(CauHinhBDSG.__init__).parameters
    except (TypeError, ValueError):
        return CauHinhBDSG(**cfg)
    if any(p.kind == p.VAR_KEYWORD for p in tham_so.values()):
        return CauHinhBDSG(**cfg)     # lop nhan **kwargs: dua het vao

    nhan_duoc = set(tham_so) - {"self"}
    bi_bo = sorted(k for k in cfg if k not in nhan_duoc)
    bo_trong_yeu = [k for k in bi_bo if k in TRONG_YEU]
    if bo_trong_yeu:
        raise SystemExit(
            "CauHinhBDSG cua mo-hinh/ khong nhan cac khoa TRONG YEU sau: {}\n"
            "  Day khong phai chuyen bo qua duoc: thieu chung, mo hinh se lay gia\n"
            "  tri mac dinh cua no va tro thanh mot mo hinh KHAC cai cau hinh mo ta,\n"
            "  ma khong co loi nao bao. Doi cau hinh hoac doi mo-hinh/ cho khop."
            .format(", ".join(bo_trong_yeu)))
    if bi_bo:
        print("  [ghi chu] CauHinhBDSG khong nhan {} khoa, da bo: {}".format(
            len(bi_bo), ", ".join(bi_bo)))
    return CauHinhBDSG(**{k: v for k, v in cfg.items() if k in nhan_duoc})


# ---------------------------------------------------------------------------
# Lich hoc suat
# ---------------------------------------------------------------------------
def he_so_hoc_suat(buoc, tong_buoc, buoc_ham_nong, ti_le_day=0.1):
    """He so nhan vao hoc suat goc: ham nong tuyen tinh roi giam theo cosine.

    buoc          : chi so buoc toi uu hien tai, dem tu 0
    tong_buoc     : tong so buoc toi uu cua ca lan chay
    buoc_ham_nong : so buoc dau tang tuyen tinh tu ~0 len 1
    ti_le_day     : he so o cuoi lich (khong ve 0). Ve dung 0 thi nhung batch
                    cuoi cung khong dong gop gi — phi mot phan du lieu.

    VI SAO HAM NONG: nhung buoc dau, hai moment cua AdamW chua co thong ke; buoc
    di luc do gan nhu la nhieu chia cho mot uoc luong phuong sai rat nho, de lam
    no loss. Ham nong la cach re nhat de khong phai xu ly chuyen do ve sau.

    VI SAO COSINE: no giam nhanh o giua va cham dan ve cuoi, cho mo hinh nhieu
    buoc nho o giai doan tinh chinh cuoi ma khong can chia giai doan bang tay.
    """
    if buoc_ham_nong > 0 and buoc < buoc_ham_nong:
        return float(buoc + 1) / float(buoc_ham_nong)
    con_lai = max(1, tong_buoc - buoc_ham_nong)
    tien = float(buoc - buoc_ham_nong) / float(con_lai)
    tien = min(1.0, max(0.0, tien))
    return ti_le_day + (1.0 - ti_le_day) * 0.5 * (1.0 + math.cos(math.pi * tien))


def dat_hoc_suat(bo_toi_uu, hoc_suat):
    for nhom in bo_toi_uu.param_groups:
        nhom["lr"] = hoc_suat


# ---------------------------------------------------------------------------
# Dong ho: token/giay va uoc tinh thoi gian con lai
# ---------------------------------------------------------------------------
class DongHo(object):
    """Do toc do token/giay va uoc tinh thoi gian con lai.

    Dung CUA SO TRUOT chu khong phai trung binh tu dau: nhung buoc dau bao gom
    ca thoi gian nap du lieu, bien dich nhan CUDA va lan cap phat bo nho dau
    tien. Trung binh tu dau se keo uoc tinh sai suot ca lan chay dai.
    """

    def __init__(self, cua_so_giay=60.0):
        self.bat_dau = time.time()
        self.cua_so_giay = cua_so_giay
        self.lich_su = collections.deque()   # (thoi diem, so token cong don)
        self.tong_token = 0
        self.lich_su.append((self.bat_dau, 0))

    def ghi(self, so_token):
        self.tong_token += so_token
        bay_gio = time.time()
        self.lich_su.append((bay_gio, self.tong_token))
        while len(self.lich_su) > 2 and bay_gio - self.lich_su[0][0] > self.cua_so_giay:
            self.lich_su.popleft()

    def toc_do(self):
        """token/giay trong cua so truot. Tra ve 0.0 khi chua du du lieu."""
        if len(self.lich_su) < 2:
            return 0.0
        t0, n0 = self.lich_su[0]
        t1, n1 = self.lich_su[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0
        return (n1 - n0) / dt

    def da_troi(self):
        return time.time() - self.bat_dau

    def con_lai(self, buoc_da_lam, tong_buoc):
        """Uoc tinh giay con lai theo toc do buoc trong cua so truot."""
        if buoc_da_lam <= 0 or tong_buoc <= buoc_da_lam:
            return None
        toc_do_token = self.toc_do()
        if toc_do_token <= 0:
            return None
        token_moi_buoc = self.tong_token / float(buoc_da_lam)
        return (tong_buoc - buoc_da_lam) * token_moi_buoc / toc_do_token


def dinh_dang_ppl(loss):
    """Do roi (perplexity) = exp(loss), dinh dang de doc.

    VI SAO KHONG IN THANG math.exp(loss): voi loss lon (mo hinh moi khoi tao, hoac
    khoi tao sai), exp(loss) tran kieu so thuc. Cach vá thong thuong la chan loss
    lai roi in exp cua gia tri da chan — va luc do man hinh hien mot con so cu the,
    TRONG NHU SO THAT, nhung thuc ra la con so cua cai tran chu khong phai cua mo
    hinh. Do la noi doi bang dinh dang. O day, tren nguong thi noi thang la tren
    nguong.
    """
    if loss is None:
        return "?"
    if loss >= 20.0:
        return ">4,9e8"
    return "{:,.1f}".format(math.exp(loss))


def dinh_dang_giay(giay):
    """Doi giay thanh chuoi 1g 23p 45s. None -> '?'."""
    if giay is None:
        return "?"
    giay = int(giay)
    gio, du = divmod(giay, 3600)
    phut, giay = divmod(du, 60)
    if gio:
        return "{}g {:02d}p {:02d}s".format(gio, phut, giay)
    if phut:
        return "{}p {:02d}s".format(phut, giay)
    return "{}s".format(giay)


# ---------------------------------------------------------------------------
# Diem dung (checkpoint)
# ---------------------------------------------------------------------------
def luu_diem_dung(duong_dan, mo_hinh, bo_toi_uu, trang_thai, cfg, scaler=None):
    """Luu diem dung mot cach AN TOAN: ghi tep tam roi doi ten.

    VI SAO GHI TEP TAM: mot diem dung 500 MB ghi mat vai giay. Neu may mat dien
    hoac nguoi dung bam Ctrl-C giua chung thi tep .pt cu — cai duy nhat con dung
    — da bi ghi de mot nua va hong. Doi ten (os.replace) la thao tac nguyen tu
    tren cung mot he tep, nen tep cu chi bien mat khi tep moi da ghi xong.
    """
    doi_hoi_torch()
    thu_muc = os.path.dirname(os.path.abspath(duong_dan))
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc)
    goi = {
        "trong_so": mo_hinh.state_dict(),
        "toi_uu": bo_toi_uu.state_dict(),
        "trang_thai": trang_thai,
        "cau_hinh": cfg,
        "ngau_nhien": {
            "python": random.getstate(),
            "torch": torch.get_rng_state(),
        },
    }
    if scaler is not None:
        goi["scaler"] = scaler.state_dict()
    tam = duong_dan + ".dang-ghi"
    torch.save(goi, tam)
    os.replace(tam, duong_dan)


def nap_diem_dung(duong_dan, mo_hinh, bo_toi_uu, thiet_bi, scaler=None):
    """Nap diem dung. Tra ve dict trang_thai da luu."""
    doi_hoi_torch()
    goi = torch.load(duong_dan, map_location=thiet_bi, weights_only=False)
    mo_hinh.load_state_dict(goi["trong_so"])
    if bo_toi_uu is not None and "toi_uu" in goi:
        bo_toi_uu.load_state_dict(goi["toi_uu"])
    if scaler is not None and "scaler" in goi:
        scaler.load_state_dict(goi["scaler"])
    ngau_nhien = goi.get("ngau_nhien") or {}
    if "python" in ngau_nhien:
        random.setstate(ngau_nhien["python"])
    if "torch" in ngau_nhien:
        # Trang thai RNG phai la tensor uint8 tren CPU. torch.load voi
        # map_location='cuda' co the da doi no sang GPU — doi lai truoc khi dat,
        # neu khong set_rng_state nem loi kieu du lieu.
        tt = ngau_nhien["torch"]
        try:
            torch.set_rng_state(tt.cpu().to(torch.uint8))
        except Exception as loi:
            print("  [canh bao] khong khoi phuc duoc trang thai ngau nhien: {}".format(loi))
    return goi.get("trang_thai", {}), goi.get("cau_hinh")


def dat_hat_giong(hat_giong):
    """Dat hat giong cho python va torch.

    Khong dat torch.use_deterministic_algorithms(True): tren GPU no lam mot so
    nhan cham han, va tai lap tuyet doi khong phai muc tieu o day. Muc tieu la
    hai lan chay CUNG cau hinh cho ket qua gan nhau va thu tu du lieu lap lai
    duoc khi tiep tuc tu diem dung.
    """
    random.seed(hat_giong)
    if torch is not None:
        torch.manual_seed(hat_giong)


def thu_tu_lo(so_mau, hat_giong, ky):
    """Thu tu duyet mau cua mot ky (epoch), tai lap duoc.

    VI SAO KHONG DUNG random.shuffle TREN BIEN TOAN CUC: khi tiep tuc tu diem
    dung o giua ky thu ba, ta phai dung LAI DUNG thu tu cua ky thu ba. Sinh thu
    tu tu (hat_giong, ky) thi lam duoc dieu do ma khong phai luu ca danh sach
    hang trieu chi so vao diem dung.
    """
    rng = random.Random(hat_giong * 1000003 + ky)
    chi_so = list(range(so_mau))
    rng.shuffle(chi_so)
    return chi_so


# ---------------------------------------------------------------------------
# Tinh loss khi mo hinh khong tu tinh
# ---------------------------------------------------------------------------
def goi_mo_hinh(mo_hinh, ids, nhan):
    """Goi mo hinh va luon tra ve (logits, loss) voi loss khac None.

    Doc duoc ca hai kieu tra ve:
      - dataclass KetQuaMoHinh cua mo-hinh/ (co .logits va .loss)   <- kieu that
      - tuple (logits, loss)                                         <- kieu cu
    De hai thu muc doi qua lai ma tep nay khong hong.

    Neu mo hinh tra loss=None (vi du mot ban chi lam phan xuoi), ta tu tinh —
    VA TINH DUNG QUY UOC CUA mo-hinh/: bo logit cuoi, bo nhan dau. Dieu nay phai
    khop tuyet doi voi ma cua ho, neu khong thi cung mot bo du lieu se cho hai
    ket qua khac nhau tuy mo hinh co tu tinh loss hay khong — mot cho lech gan
    nhu khong the tim ra tu trieu chung.
    """
    doi_hoi_torch()
    ra = mo_hinh(ids, nhan)
    logits = getattr(ra, "logits", None)
    loss = getattr(ra, "loss", None)
    if logits is None:
        if isinstance(ra, (tuple, list)):
            logits = ra[0]
            loss = ra[1] if len(ra) > 1 else None
        else:
            logits = ra
    if loss is None:
        loss = F.cross_entropy(
            logits[:, :-1].reshape(-1, logits.size(-1)).float(),
            nhan[:, 1:].reshape(-1),
            ignore_index=-100,
        )
    return logits, loss


def dem_token_co_nhan(nhan):
    """So token THAT SU dong gop vao loss.

    Dem tu cot 1 tro di, khong dem cot 0: mo-hinh/ tinh loss tren nhan[:, 1:],
    nen nhan o cot 0 khong bao gio duoc dung. Dem ca cot 0 se bao cao thua — it
    thoi, nhung la mot con so sai, va con so sai nay lai chinh la con so nguoi
    ta dung de kiem xem mat na co dung khong.
    """
    doi_hoi_torch()
    return int((nhan[:, 1:] != -100).sum().item())


# ---------------------------------------------------------------------------
# Tien ich nho
# ---------------------------------------------------------------------------
def mang_token_rong():
    """Mang token phang, 4 byte moi token (array('i') = so nguyen co dau 32 bit).

    VI SAO KHONG DUNG list PYTHON: mot list 100 trieu so nguyen ton khoang 4 GB —
    moi phan tu la mot con tro 8 byte cong mot doi tuong int rieng. array('i')
    ton dung 4 byte moi token, khong co doi tuong trung gian: 100 trieu token =
    400 MB.

    VI SAO 32 BIT LA DU: vocab_size cua ca ba cau hinh la 24.576. Tran cua kieu
    nay la 2^31 — thua xa, va van con dung duoc neu sau nay tu vung to len hang
    tram nghin.

    LOI ICH THEM: array('i') lo ra giao thuc buffer, nen torch.frombuffer doc no
    thanh tensor int32 MA KHONG SAO CHEP. Voi ngu lieu hang GB do la khac biet
    giua 'chay duoc' va 'het RAM'. Doi lai: tensor va mang DUNG CHUNG bo nho, nen
    khong duoc them phan tu vao mang sau khi da tao tensor — them co the lam mang
    cap phat lai cho khac va tensor tro vao vung da giai phong.
    """
    return array.array("i")


def in_bang(cac_dong, thut=2):
    """In mot bang hai cot can le, de log doc duoc."""
    if not cac_dong:
        return
    rong = max(len(str(a)) for a, _ in cac_dong)
    for a, b in cac_dong:
        print("{}{}  {}".format(" " * thut, str(a).ljust(rong), b))
