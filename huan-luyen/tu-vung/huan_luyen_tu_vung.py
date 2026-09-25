#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Huan luyen tu vung (tokenizer) HAI ngon ngu cho ho mo hinh BDSG.

Tieng Viet la ngon ngu chinh. Tieng Anh la ngon ngu phu. Khong co ngon ngu thu ba.

=============================================================================
1. VI SAO BDSG PHAI TU HUAN LUYEN TU VUNG — SO DO, KHONG PHAI Y KIEN
=============================================================================
Phep do ngay 25/09/2026 (bien ban day du o ket-qua/do-luong-25-09-2026.md):
tren 1.037.113 ky tu tieng Viet chua tung thay luc huan luyen, hai tu vung
CUNG kich thuoc 6.400, khac nhau dung mot bien la co hoc tieng Viet hay khong:

    tu vung KHONG hoc tieng Viet : 852.285 token  ->  1,22 ky tu moi token
    tu vung CO hoc tieng Viet    : 289.266 token  ->  3,59 ky tu moi token

Giam 66,1% so token. Cung mot ngan sach ngu canh thi chua duoc nhieu hon 2,95
lan chu tieng Viet.

Co che nhin thay duoc, khong phai suy doan: byte-level BPE KHONG BAO GIO bao loi
khi gap chu la. No lang le day chu do xuong tung byte UTF-8 tho. Chu "Cong" o
tu vung khong hoc tieng Viet ton 4 token, vi dau thanh khong co merge nao de
gop. O tu vung co hoc tieng Viet no la 1 token. Ca mot cau thu: 72 token so voi
21 token.

Cho nen: khong co loi nao bao "tu vung cua ban sai voi tieng Viet". Chi co
ngan sach ngu canh bi dot vao dau thanh, va khong ai thay. Day dung la ho loi
hong-ma-khong-bao ma kho nay dat ra de chong. Cach phat hien duy nhat la DO,
bang do_tokenizer.py nam canh tep nay.

Ky thuat dung o day la ky thuat da cong bo, khong phai phat minh cua ai trong
mot kho ma cu the:
  - BPE (byte-pair encoding) cho don vi tu con : arXiv:1508.07909
  - BPE o muc BYTE (khong bao gio co <unk>)    : arXiv:1909.03341
Thu vien `tokenizers` cua HuggingFace la CONG CU hien thuc hai ky thuat do.
Dung mot thu vien la chuyen binh thuong; moi dong chu thich trong tep nay la
cua BDSG, va moi lua chon duoi day la lua chon cua BDSG.

=============================================================================
2. BO TOKEN DAC BIET CUA BDSG — CHON THEO NHU CAU THAT, TUNG CAI MOT
=============================================================================
Mot bo token dac biet khong duoc sao chep tu noi khac. Moi token dac biet an
mot hang trong ma tran nhung va chiem vinh vien mot id. Khai bao token cho mot
kha nang minh khong co (anh, am thanh, video) la KHAI SAI ve mo hinh: nguoi doc
cau hinh se tuong mo hinh nhan duoc anh. Do 26/09/2026: trong ca kho nay khong
co mot duong ong nao doc hay ghi anh, am thanh hay video. Nen khong co token
nao cho chung.

BDSG can dung ba viec, va chi ba viec:

  id 0  <|het-van-ban|>
      Ba vai trong mot: (a) dau ngan cach hai van ban khac nhau khi tien huan
      luyen, (b) token dem (padding) khi xep lo, (c) cho lui neu co gi do doi
      mot token khong ton tai.
      VI SAO DAT O ID 0: bo dem trong torch mac dinh la so 0. Neu id 0 la mot
      tu that, mot tensor quen khoi tao se giai ma ra mot cau tieng Viet troi
      chay va trong nhu du lieu that. Neu id 0 la token nay, no giai ma ra
      "khong co gi" — loi nhin thay duoc ngay.

  id 1  <|mo-luot|>
  id 2  <|dong-luot|>
      Mo va dong mot luot noi. San pham that cua BDSG (chat.bdsg.vn, hoi dap
      tren ho so doanh nghiep) la doi thoai nhieu luot, nen mo hinh phai biet
      luot cua ai bat dau o dau va het o dau.
      VI SAO HAI TOKEN CHU KHONG PHAI MOT: mat na nhan khi huan luyen co giam
      sat phai xac dinh DUNG doan nao la cau tra loi cua tro ly de tinh mat mat
      tren doan do. Voi mot dau hieu duy nhat thi ranh gioi cuoi la mo ho, va
      mat na se lech — ma mat mat VAN giam, mo hinh VAN "hoc", chi la hoc sai
      cho. Hai dau hieu thi ranh gioi la hien nhien.
      VI SAO DUNG ID 1 VA 2: cac tep huan-luyen/cau-hinh/*.json cua kho nay da
      khai bos_token_id=1 va eos_token_id=2. Neu tu vung de hai token nay o id
      khac, mo hinh se sinh va dung o token sai — va khong co loi nao bao. Nen
      ham huan_luyen() KIEM cung ba id nay truoc khi ghi ra dia, va tu choi ghi
      neu lech.

  13 o du tru  <|du-tru-01|> .. <|du-tru-13|>
      Them mot token sau nay lam doi vocab_size, doi vocab_size lam doi hinh
      dang ma tran nhung, va doi ma tran nhung lam HONG moi trong so da phat
      hanh. Luc duy nhat de tru cho re la bay gio, khi chua co trong so nao.
      3 + 13 = 16, mot so tron de con so merge hoc duoc cung tron.
      Chung duoc danh dau special=false trong tokenizer.json, CO CHU Y: neu mot
      o du tru bao gio do hien ra trong dau ra thi co gi do sai, va toi muon
      NHIN THAY no chu khong muon skip_special_tokens=True nuot mat.

=============================================================================
3. TEN TRUONG CAU HINH — QUY UOC CHUNG, GIU NGUYEN
=============================================================================
tokenizer_config.json dung cac ten truong theo CHUAN THU VIEN transformers
(bos_token, eos_token, pad_token, model_max_length, chat_template,
tokenizer_class...). Day la quy uoc chung cua ca he sinh thai, khong phai cua
rieng du an nao, va giu no la dieu kien de thu muc nay nap duoc o may nguoi
khac. Gia tri ben trong thi la cua BDSG.

Mau hoi thoai (chat_template) cung vay: `messages`, `role`, `content` la ten
BIEN ma transformers.apply_chat_template truyen vao mau — khong phai lua chon
cua BDSG. Con GIA TRI cua role thi la cua BDSG: "nguoi" va "tro-ly", dung nhu
dinh dang ngu lieu ma huan-luyen/du-lieu/tron.py xuat ra.

RANG BUOC PHAI GIU CUNG NHAU: mat na nhan khi huan luyen co giam sat phai tim
dung chuoi "<|mo-luot|>tro-ly\n" ... "<|dong-luot|>". Ai doi MAU_HOI_THOAI thi
phai doi ham sinh mat na trong CUNG mot lan sua. Doi mot ben thoi la lam mat na
tro sai cho ma khong co loi nao bao.

=============================================================================
4. TRONG SO NGON NGU DUOC AP DAT NHU THE NAO
=============================================================================
BPE hoc merge tu TAN SUAT. Muon tieng Viet chiem uu the thi phai cho no nhieu
KY TU hon — khong phai nhieu TEP hon, cung khong phai nhieu DONG hon. Mot dong
tieng Anh 40 ky tu khong dang gia bang mot doan tieng Viet 4.000 ky tu, nen dem
dong se cho ti le sai hoan toan.

Nen script chia NGAN SACH KY TU theo ti le, mac dinh --ti-le-viet 0.80 va
--ti-le-anh 0.20.

0,80 / 0,20 la con so DAT, CHUA DO. Toi khong co phep do noi ti le nao la tot
nhat. Cach do no: chay lai script nay o vai ti le khac nhau roi do tung ban
bang do_tokenizer.py, tim cho ky tu/token tieng Viet thoi cai thien va tieng
Anh bat dau te di ro. Chua ai lam phep do do (26/09/2026).

Mot lua chon co y: neu mot ngon ngu KHONG DU du lieu de tieu het ngan sach,
script ghi ro phan thieu vao bao cao va van chay tiep. No KHONG lap lai van ban
de bu cho du. Lap lai lam BPE hoc thuoc chinh nhung chuoi bi lap va de ra merge
rac ma nhin tu vung khong thay duoc. Thieu thi ghi la thieu.

=============================================================================
5. CHAY
=============================================================================
  python3 huan_luyen_tu_vung.py \
      --nguon-viet ../../bo-du-lieu/doan_tri_thuc.sach.jsonl \
      --nguon-viet /duong/dan/wikipedia-vi.jsonl \
      --nguon-anh  /duong/dan/nen-tieng-anh.jsonl \
      --ti-le-viet 0.80 --ti-le-anh 0.20 \
      --tu-vung 24576 \
      --ra ../../bo-du-lieu/tu-vung-bdsg-v1

  # Thu nhanh cho chac script chay (tu sinh du lieu gia, khong dung ngu lieu that):
  python3 huan_luyen_tu_vung.py --tu-kiem

Chi can python >= 3.8 va thu vien `tokenizers`. KHONG can torch, KHONG can
transformers. (Da chay that tren python 3.9.6 + tokenizers 0.22.2, 26/09/2026.)
"""

import argparse
import datetime
import json
import os
import sys
import time

try:
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
except ImportError:
    sys.stderr.write(
        "Thieu thu vien `tokenizers`. Cai bang:\n"
        "    pip install tokenizers\n"
        "Script nay KHONG can torch va KHONG can transformers.\n")
    raise

# Hai ngon ngu, theo dung thu tu uu tien cua du an: Viet truoc, Anh sau.
NGON_NGU = ["vi", "en"]
TI_LE_MAC_DINH = {"vi": 0.80, "en": 0.20}

# --- Bo token dac biet cua BDSG. Ly do tung cai o muc 2 phan dau tep. --------
TOKEN_LOI = ["<|het-van-ban|>", "<|mo-luot|>", "<|dong-luot|>"]
SO_O_DU_TRU = 13
# Hop dong id voi huan-luyen/cau-hinh/*.json. Lech la hong im lang.
ID_BAT_BUOC = {"<|het-van-ban|>": 0, "<|mo-luot|>": 1, "<|dong-luot|>": 2}

# Mau hoi thoai cua BDSG. Ngan co chu y: mau cang dai thi cang nhieu cho de mot
# lan sua tay lam lech mat na nhan ma khong ai thay. Xem muc 3 phan dau tep.
MAU_HOI_THOAI = r"""{%- for tin in messages %}
{{- '<|mo-luot|>' + tin['role'] + '\n' + tin['content'] + '<|dong-luot|>\n' }}
{%- endfor %}
{%- if add_generation_prompt %}
{{- '<|mo-luot|>tro-ly\n' }}
{%- endif %}"""

# Cau thu tieng Viet dung de bao cao ky tu/token ngay sau khi huan luyen. Tu
# viet, khong lay tu nguon co ban quyen. Chu de co tinh: van phong ho so doanh
# nghiep — dung loai van ban mo hinh nay se phai doc.
CAU_THU_TIENG_VIET = (
    "Công ty Cổ phần Tập đoàn BDSG hoạt động trong lĩnh vực bất động sản tại Thanh Hoá."
)


def danh_sach_token_dac_biet():
    """Ba token loi, roi 13 o du tru. Thu tu nay QUYET DINH id, dung sap lai."""
    du_tru = ["<|du-tru-{:02d}|>".format(i) for i in range(1, SO_O_DU_TRU + 1)]
    return TOKEN_LOI + du_tru


# ---------------------------------------------------------------------------
# Doc du lieu
# ---------------------------------------------------------------------------
def doc_van_ban(duong_dan):
    """Sinh tung doan van ban tu mot tep.

    Chap nhan ba dinh dang, vi ca ba deu ton tai trong kho nay:
      - .jsonl tien huan luyen : {"text": "...", "nguon": "...", "ngon_ngu": "vi"}
      - .jsonl tien huan luyen : {"noi_dung": "..."}   (ten truong cu cua CSDL)
      - .jsonl doi thoai BDSG  : {"hoi_thoai": [{"vai": "...", "noi_dung": "..."}]}
      - .txt                   : moi dong la mot doan

    VI SAO HAM NAY PHAI BAO DUOC LA NO KHONG DOC RA GI: neu no am tham tra ve
    rong — vi tep dung ten truong khac chang han — thi BPE se chi hoc tren 256
    byte goc va de ra mot tu vung KHONG CO MERGE NAO. Khong co loi nao. Tu vung
    van ghi ra dia, van nap duoc, va van vo dung. Nen main() dung han neu tong
    so ky tu doc duoc bang 0.
    """
    mo_rong = os.path.splitext(duong_dan)[1].lower()
    with open(duong_dan, "r", encoding="utf-8", errors="ignore") as f:
        for dong in f:
            if mo_rong == ".txt":
                if dong.strip():
                    yield dong.rstrip("\n")
                continue
            dong = dong.strip()
            if not dong:
                continue
            try:
                d = json.loads(dong)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if "text" in d:
                vb = str(d["text"])
            elif "noi_dung" in d and not isinstance(d.get("noi_dung"), (list, dict)):
                vb = str(d["noi_dung"])
            elif "hoi_thoai" in d and isinstance(d["hoi_thoai"], list):
                phan = [m.get("noi_dung") for m in d["hoi_thoai"]
                        if isinstance(m, dict) and m.get("noi_dung")]
                vb = "\n".join(str(x) for x in phan)
            else:
                continue
            if vb.strip():
                yield vb


def gom_mot_ngon_ngu(cac_tep, ngan_sach_ky_tu):
    """Doc XEN KE cac tep cua MOT ngon ngu cho den khi het ngan sach ky tu.

    Xen ke (round-robin) chu khong noi duoi nhau: neu noi duoi nhau, tep to doc
    truoc se an het ngan sach va cac tep sau khong gop duoc chu nao. Loi do
    khong bao gi ca, no chi lam tu vung lech ve mot nguon duy nhat.

    ngan_sach_ky_tu = 0 nghia la doc het (che do tu tinh ngan sach, xem main).

    Tra ve (danh_sach_van_ban, so_ky_tu_da_doc, so_doan, thong_ke_tung_tep).
    """
    luong = [doc_van_ban(t) for t in cac_tep]
    con_song = [True] * len(luong)
    thong_ke = [{"tep": t, "so_doan": 0, "so_ky_tu": 0} for t in cac_tep]
    ket_qua = []
    da_doc = 0
    so_doan = 0
    while any(con_song):
        for i, g in enumerate(luong):
            if not con_song[i]:
                continue
            try:
                vb = next(g)
            except StopIteration:
                con_song[i] = False
                continue
            ket_qua.append(vb)
            n = len(vb)
            da_doc += n
            so_doan += 1
            thong_ke[i]["so_doan"] += 1
            thong_ke[i]["so_ky_tu"] += n
            if ngan_sach_ky_tu and da_doc >= ngan_sach_ky_tu:
                return ket_qua, da_doc, so_doan, thong_ke
    return ket_qua, da_doc, so_doan, thong_ke


def cat_theo_ngan_sach(van_ban, ngan_sach_ky_tu):
    """Cat bot danh sach doan cho vua ngan sach ky tu. Tra ve (danh_sach, so_ky_tu).

    Cat theo DOAN, khong cat giua doan — mot doan bi chem doi se day mot cau cut
    vao ngu lieu hoc merge.

    CHU Y VE SO 0: o ham nay, ngan sach 0 nghia la KHONG LAY GI, khac han
    gom_mot_ngon_ngu() noi 0 nghia la doc het. Hai nghia nguoc nhau nen phai
    ghi ra day. Ly do: ham nay luon nhan mot ngan sach da TINH RA
    (int(tong_dich * ti_le)), nen 0 o day chi xay ra khi nguoi chay dat ti le
    cua mot ngon ngu bang 0 — tuc la co y bo han ngon ngu do. Neu 0 lai co
    nghia "khong gioi han" thi dat --ti-le-viet 0 se nap TOAN BO tieng Viet
    vao, dung nguoc lai y nguoi chay, va khong co loi nao bao. Chinh chuong
    trinh doi chung tu sinh (tu vung chi hoc tieng Anh) can dat ti le 0 nay.
    """
    if ngan_sach_ky_tu <= 0:
        return [], 0
    giu = []
    tong = 0
    for v in van_ban:
        if tong >= ngan_sach_ky_tu:
            break
        giu.append(v)
        tong += len(v)
    return giu, tong


# ---------------------------------------------------------------------------
# Huan luyen
# ---------------------------------------------------------------------------
def huan_luyen(van_ban, tu_vung, thu_muc_ra):
    """Huan luyen byte-level BPE va ghi ra thu muc tuong thich transformers."""
    tokenizer = Tokenizer(models.BPE())
    # add_prefix_space=False: khong tu chen khoang trang truoc chuoi dau vao.
    # Neu bat, "Cong ty" va " Cong ty" cho ra cung day token, va moi phep do
    # ky tu/token se lech mot token moi doan ma khong ai de y.
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)

    tat_ca_dac_biet = danh_sach_token_dac_biet()
    trainer = trainers.BpeTrainer(
        vocab_size=tu_vung,
        show_progress=True,
        # initial_alphabet = 256 byte. Dieu nay bao dam KHONG BAO GIO co <unk>:
        # moi ky tu Unicode deu phan ra duoc thanh byte. Nhac lai cho ro, vi day
        # chinh la cho de hieu nham: "khong bao gio loi" KHONG co nghia la
        # "token hoa tot". Chu tieng Viet co dau ma khong duoc hoc merge se tut
        # xuong 2-3 token byte va chay thang, khong mot loi nao.
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        special_tokens=tat_ca_dac_biet,
    )
    tokenizer.train_from_iterator(van_ban, trainer=trainer)
    tokenizer.decoder = decoders.ByteLevel()

    # --- Kiem hop dong id TRUOC khi ghi ra dia -----------------------------
    # Xem muc 2 phan dau tep. Neu ba id nay khong dung, mo hinh se sinh va dung
    # o token sai, va khong co loi nao bao. Tha hong o day con hon hong sau ba
    # ngay huan luyen.
    for tok, id_mong in sorted(ID_BAT_BUOC.items(), key=lambda kv: kv[1]):
        that = tokenizer.token_to_id(tok)
        if that != id_mong:
            raise RuntimeError(
                "Token {} co id {} nhung huan-luyen/cau-hinh/*.json cho doi {}. "
                "Dung ghi tu vung nay ra — no se lam hong mo hinh mot cach im lang."
                .format(tok, that, id_mong))

    if not os.path.isdir(thu_muc_ra):
        os.makedirs(thu_muc_ra)
    duong_tokenizer = os.path.join(thu_muc_ra, "tokenizer.json")
    tokenizer.save(duong_tokenizer)
    tokenizer.model.save(thu_muc_ra)  # vocab.json + merges.txt, de doc bang mat

    # --- Danh dau lai co "special" -----------------------------------------
    # Chi ba token loi la special. 13 o du tru de special=false CO CHU Y: neu
    # mot o du tru hien ra trong dau ra thi co gi do sai, va toi muon no HIEN
    # RA chu khong muon skip_special_tokens=True nuot mat bang chung.
    with open(duong_tokenizer, "r", encoding="utf-8") as f:
        du_lieu = json.load(f)
    for tt in du_lieu.get("added_tokens", []):
        tt["special"] = tt["content"] in TOKEN_LOI
    with open(duong_tokenizer, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)

    bang_giai_ma = {}
    for tok in tat_ca_dac_biet:
        idx = tokenizer.token_to_id(tok)
        bang_giai_ma[str(idx)] = {
            "content": tok,
            "lstrip": False,
            "normalized": False,
            "rstrip": False,
            "single_word": False,
            "special": tok in TOKEN_LOI,
        }

    # Ten truong duoi day theo CHUAN THU VIEN transformers — quy uoc chung cua
    # he sinh thai, khong phai cua rieng du an nao. Gia tri la cua BDSG.
    cau_hinh = {
        "add_bos_token": False,
        "add_eos_token": False,
        "add_prefix_space": False,
        "added_tokens_decoder": bang_giai_ma,
        "additional_special_tokens": [t for t in TOKEN_LOI if t != "<|het-van-ban|>"],
        "bos_token": "<|mo-luot|>",
        "clean_up_tokenization_spaces": False,
        "eos_token": "<|dong-luot|>",
        # model_max_length = 2048 khop max_position_embeddings trong CA BA tep
        # huan-luyen/cau-hinh/*.json (nho/vua/lon — do lai 26/09/2026, ca ba deu
        # 2048). Dat so lon hon o day khong lam mo hinh doc duoc dai hon — chi
        # lam tokenizer im lang cho qua doan dai hon cai mo hinh xu ly duoc.
        # Truoc 26/09/2026 cho nay ghi 32768, gap 16 lan tran that. Hau qua do
        # duoc: mo-hinh/kien_truc.py nem ValueError ngay khi tong do dai vuot
        # max_position_embeddings, nen moi ai tin con so cua tokenizer roi cat
        # du lieu theo no se dung o batch dau; con buoc chuan bi du lieu (chon
        # --cat-doan trong tron.py) thi sai am tham vi khong ai chay mo hinh luc
        # do. Ai doi max_position_embeddings trong cau-hinh/*.json PHAI doi con
        # so nay trong CUNG mot lan sua.
        "model_max_length": 2048,
        "pad_token": "<|het-van-ban|>",
        "unk_token": "<|het-van-ban|>",
        "spaces_between_special_tokens": False,
        "chat_template": MAU_HOI_THOAI,
        "tokenizer_class": "PreTrainedTokenizerFast",
    }
    with open(os.path.join(thu_muc_ra, "tokenizer_config.json"), "w", encoding="utf-8") as f:
        json.dump(cau_hinh, f, ensure_ascii=False, indent=4)

    return tokenizer, len(du_lieu["model"]["vocab"]), len(du_lieu["model"]["merges"])


# ---------------------------------------------------------------------------
# Dong lenh
# ---------------------------------------------------------------------------
def duong_tuyet_doi(duong):
    return os.path.abspath(os.path.expanduser(duong.strip()))


def chuan_hoa_ti_le(ti_le_viet, ti_le_anh):
    """Chuan hoa ve tong 1,0. Tra ve dict {'vi': .., 'en': ..}."""
    if ti_le_viet < 0 or ti_le_anh < 0:
        raise ValueError("Ti le khong duoc am")
    tong = ti_le_viet + ti_le_anh
    if tong <= 0:
        raise ValueError("Tong --ti-le-viet va --ti-le-anh phai lon hon 0")
    return {"vi": ti_le_viet / tong, "en": ti_le_anh / tong}


def tu_kiem(thu_muc_tam):
    """Tu sinh du lieu gia de chung minh script CHAY DUOC tu dau den cuoi.

    Day KHONG phai phep danh gia chat luong: van ban gia qua nho de noi len dieu
    gi ve tu vung. No tra loi dung mot cau hoi — script co chay tron va de ra
    tep hop le khong, va ba id bat buoc co dung cho khong.
    """
    if not os.path.isdir(thu_muc_tam):
        os.makedirs(thu_muc_tam)
    mau = {
        "vi": ["Doanh nghiệp niêm yết công bố báo cáo tài chính quý ba năm 2026.",
               "Công ty cổ phần bất động sản triển khai dự án tại tỉnh Thanh Hoá.",
               "Ngành nghề kinh doanh chính: tư vấn quản lý và đầu tư hạ tầng."],
        "en": ["The company reported consolidated revenue for the third quarter.",
               "Business registration and industry classification for listed firms."],
    }
    tep = {}
    for ng, cau in mau.items():
        d = os.path.join(thu_muc_tam, "{}.jsonl".format(ng))
        with open(d, "w", encoding="utf-8") as f:
            for _ in range(200):
                for c in cau:
                    f.write(json.dumps({"text": c, "nguon": "tu-kiem", "ngon_ngu": ng},
                                       ensure_ascii=False) + "\n")
        tep[ng] = d
    return tep


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Huan luyen tu vung BPE hai ngon ngu (Viet chinh, Anh phu) cho ho mo hinh BDSG",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nguon-viet", action="append", default=[], metavar="DUONGDAN",
                   help="tep ngu lieu tieng Viet (.jsonl hoac .txt), lap lai duoc")
    p.add_argument("--nguon-anh", action="append", default=[], metavar="DUONGDAN",
                   help="tep ngu lieu tieng Anh (.jsonl hoac .txt), lap lai duoc")
    p.add_argument("--ti-le-viet", type=float, default=TI_LE_MAC_DINH["vi"],
                   help="phan ngan sach KY TU danh cho tieng Viet (mac dinh 0.80)")
    p.add_argument("--ti-le-anh", type=float, default=TI_LE_MAC_DINH["en"],
                   help="phan ngan sach KY TU danh cho tieng Anh (mac dinh 0.20)")
    p.add_argument("--tu-vung", type=int, default=24576,
                   help="kich thuoc tu vung (mac dinh 24576, khop huan-luyen/cau-hinh/*.json)")
    p.add_argument("--ngan-sach-ky-tu", type=int, default=0,
                   help="tong so ky tu dua vao huan luyen BPE. 0 = TU TINH: lay ngan sach lon "
                        "nhat ma du lieu hien co con giu dung ti le (mac dinh 0)")
    p.add_argument("--ra", default="./tu-vung-bdsg", help="thu muc ghi ket qua")
    p.add_argument("--tu-kiem", action="store_true",
                   help="tu sinh du lieu gia va chay thu (chung minh script chay duoc)")
    args = p.parse_args(argv)

    bat_dau = time.time()

    if args.tu_kiem:
        import tempfile
        tam = tempfile.mkdtemp(prefix="tu-vung-tu-kiem-")
        tep = tu_kiem(tam)
        nguon = {"vi": [tep["vi"]], "en": [tep["en"]]}
        args.tu_vung = min(args.tu_vung, 1000)
        args.ngan_sach_ky_tu = 0
        args.ra = os.path.join(tam, "ra")
        print("[tu-kiem] du lieu gia o {}".format(tam))
    else:
        if not args.nguon_viet and not args.nguon_anh:
            p.error("Phai co it nhat mot --nguon-viet hoac --nguon-anh "
                    "(hoac dung --tu-kiem de chay thu)")
        nguon = {"vi": [duong_tuyet_doi(t) for t in args.nguon_viet],
                 "en": [duong_tuyet_doi(t) for t in args.nguon_anh]}

    try:
        ti_le = chuan_hoa_ti_le(args.ti_le_viet, args.ti_le_anh)
    except ValueError as e:
        p.error(str(e))

    thieu_tep = [t for ds in nguon.values() for t in ds if not os.path.isfile(t)]
    if thieu_tep:
        p.error("Khong tim thay tep:\n  " + "\n  ".join(thieu_tep))

    print("")
    print("Ngan sach ky tu : {}".format(
        "TU TINH tu du lieu hien co" if not args.ngan_sach_ky_tu
        else "{:,}".format(args.ngan_sach_ky_tu)))
    print("Ti le ngon ngu  : vi={:.2f}, en={:.2f}  (chuan hoa ve tong 1,0)".format(
        ti_le["vi"], ti_le["en"]))
    print("Kich thuoc tu vung: {:,}".format(args.tu_vung))
    print("")

    # --- Doc du lieu -------------------------------------------------------
    # Hai che do, khac nhau ve BO NHO va can ghi ro:
    #   ngan sach > 0 : doc den khi day ngan sach roi dung. Bo nho co chan.
    #   ngan sach = 0 : doc HET moi tep de biet tung ngon ngu co bao nhieu, roi
    #                   moi tinh ngan sach lon nhat giu dung ti le. Chinh xac
    #                   hon, nhung giu ca ngu lieu trong RAM. O quy mo hien tai
    #                   (ngu lieu BDSG 7,13 MB) thi khong sao; voi vai GB thi
    #                   phai dat --ngan-sach-ky-tu tuong minh.
    kho = {}
    for ng in NGON_NGU:
        if not nguon.get(ng):
            print("  {}: khong co nguon nao -> bo qua".format(ng))
            kho[ng] = {"van_ban": [], "ky_tu_co": 0, "so_doan": 0, "tep": []}
            continue
        if ti_le[ng] <= 0:
            # Ti le 0 = co y bo han ngon ngu nay. Khong doc tep cua no vao RAM
            # lam gi. Che do doi chung tu sinh (--ti-le-viet 0) di duong nay.
            print("  {}: ti le 0 -> khong nap (co y bo han ngon ngu nay)".format(ng))
            kho[ng] = {"van_ban": [], "ky_tu_co": 0, "so_doan": 0, "tep": []}
            continue
        han = int(args.ngan_sach_ky_tu * ti_le[ng]) if args.ngan_sach_ky_tu else 0
        vb, da_doc, so_doan, tk = gom_mot_ngon_ngu(nguon[ng], han)
        kho[ng] = {"van_ban": vb, "ky_tu_co": da_doc, "so_doan": so_doan, "tep": tk}
        print("  {}: doc duoc {:,} doan, {:,} ky tu tu {} tep".format(
            ng, so_doan, da_doc, len(nguon[ng])))

    co_mat = [ng for ng in NGON_NGU if kho[ng]["ky_tu_co"] > 0]
    if not co_mat:
        sys.stderr.write(
            "\nKHONG doc duoc ky tu nao. Neu van chay tiep, BPE chi hoc tren 256 byte\n"
            "goc va de ra mot tu vung khong co merge nao — ma khong bao loi. Dung lai.\n"
            "Kiem lai: tep .jsonl co truong \"text\", \"noi_dung\" hay \"hoi_thoai\" khong?\n")
        return 2

    # --- Quyet dinh ngan sach tung ngon ngu --------------------------------
    if args.ngan_sach_ky_tu:
        tong_dich = args.ngan_sach_ky_tu
    else:
        # Ngon ngu it du lieu nhat quyet dinh quy mo, neu muon giu DUNG ti le.
        # Con so nay TINH RA, khong dat tay, va duoc in ra de nguoi chay thay
        # minh dang phai bo bot bao nhieu cua ngon ngu con lai.
        kha_thi = [kho[ng]["ky_tu_co"] / ti_le[ng] for ng in co_mat if ti_le[ng] > 0]
        tong_dich = int(min(kha_thi)) if kha_thi else sum(kho[ng]["ky_tu_co"] for ng in co_mat)

    print("")
    print("  {:<4} {:>16} {:>16} {:>16} {:>10}".format(
        "ngon", "ky tu co", "ngan sach", "thuc dung", "thieu"))
    print("  " + "-" * 66)
    bao_cao_ngon_ngu = {}
    tat_ca_van_ban = []
    for ng in NGON_NGU:
        han = int(tong_dich * ti_le[ng])
        vb, dung = cat_theo_ngan_sach(kho[ng]["van_ban"], han)
        thieu = max(0, han - dung)
        tat_ca_van_ban.extend(vb)
        bao_cao_ngon_ngu[ng] = {
            "ngan_sach": han, "ky_tu_co": kho[ng]["ky_tu_co"], "ky_tu_dung": dung,
            "so_doan_dung": len(vb), "thieu": thieu, "ti_le_dinh": ti_le[ng],
            "tep": kho[ng]["tep"],
        }
        print("  {:<4} {:>16,} {:>16,} {:>16,} {:>10,}".format(
            ng, kho[ng]["ky_tu_co"], han, dung, thieu))
    for ng in NGON_NGU:
        t = bao_cao_ngon_ngu[ng]["thieu"]
        ns = bao_cao_ngon_ngu[ng]["ngan_sach"]
        if t and ns:
            print("  CANH BAO {}: thieu {:,} ky tu = {:.1f}% ngan sach cua no. "
                  "Script KHONG lap lai van ban de bu.".format(ng, t, 100.0 * t / ns))

    tong_ky_tu = sum(v["ky_tu_dung"] for v in bao_cao_ngon_ngu.values())
    if tong_ky_tu == 0:
        sys.stderr.write("\nNgan sach tinh ra bang 0 ky tu. Dung lai.\n")
        return 2

    print("")
    print("Tong: {:,} doan, {:,} ky tu. Bat dau huan luyen BPE...".format(
        len(tat_ca_van_ban), tong_ky_tu))
    print("")

    thu_muc_ra = duong_tuyet_doi(args.ra)
    tokenizer, so_tu, so_merge = huan_luyen(tat_ca_van_ban, args.tu_vung, thu_muc_ra)
    giay = time.time() - bat_dau

    # Ti le THAT tung ngon ngu chiem trong ngu lieu — con so DUOC, khong phai
    # con so DINH. Hai cot nay lech nhau khi mot ngon ngu thieu du lieu.
    for ng in NGON_NGU:
        bao_cao_ngon_ngu[ng]["ti_le_that"] = (
            bao_cao_ngon_ngu[ng]["ky_tu_dung"] / float(tong_ky_tu)) if tong_ky_tu else 0.0

    # Do ngay mot phep nen tren cau thu tieng Viet. Mot con so o day dat hon ba
    # dong khang dinh: nguoi chay thay lien tu vung vua sinh nen duoc bao nhieu.
    ma = tokenizer.encode(CAU_THU_TIENG_VIET, add_special_tokens=False)
    ky_tu_tren_token = len(CAU_THU_TIENG_VIET) / float(len(ma.ids)) if ma.ids else 0.0

    bao_cao = {
        "ngay_chay": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ngon_ngu": NGON_NGU,
        "tu_vung_yeu_cau": args.tu_vung,
        "tu_vung_that": so_tu,
        "so_merge": so_merge,
        "token_dac_biet": {"loi": TOKEN_LOI, "so_o_du_tru": SO_O_DU_TRU,
                           "tong": len(danh_sach_token_dac_biet())},
        "id_kiem_tra": {t: tokenizer.token_to_id(t) for t in danh_sach_token_dac_biet()[:5]},
        "tong_ky_tu": tong_ky_tu,
        "tong_doan": len(tat_ca_van_ban),
        "ngan_sach_ky_tu": args.ngan_sach_ky_tu or tong_dich,
        "ngan_sach_tu_tinh": not args.ngan_sach_ky_tu,
        "theo_ngon_ngu": bao_cao_ngon_ngu,
        "cau_thu_tieng_viet": {
            "cau": CAU_THU_TIENG_VIET,
            "so_ky_tu": len(CAU_THU_TIENG_VIET),
            "so_token": len(ma.ids),
            "ky_tu_tren_token": round(ky_tu_tren_token, 3),
            "doi_chieu": ("Duong co so 25/09/2026 tren 1.037.113 ky tu tieng Viet: "
                          "3,59 ky tu/token khi hoc tieng Viet, 1,22 khi khong hoc. "
                          "Con so o day do tren MOT cau nen chi la dau hieu som, "
                          "khong thay duoc do_tokenizer.py."),
        },
        "giay_chay": round(giay, 1),
        "ghi_chu": ("Ti le THAT lech ti le DINH khi mot ngon ngu khong du du lieu. "
                    "Xem truong 'thieu'. Script khong lap lai van ban de bu."),
    }
    duong_bao_cao = os.path.join(thu_muc_ra, "bao_cao_tu_vung.json")
    with open(duong_bao_cao, "w", encoding="utf-8") as f:
        json.dump(bao_cao, f, ensure_ascii=False, indent=2)

    print("")
    print("Xong sau {:.1f} giay.".format(giay))
    print("  tu vung that : {:,} tu, {:,} merge".format(so_tu, so_merge))
    print("  token dac biet: {} loi + {} o du tru = {}".format(
        len(TOKEN_LOI), SO_O_DU_TRU, len(danh_sach_token_dac_biet())))
    print("  id bat buoc  : " + ", ".join(
        "{}={}".format(t, tokenizer.token_to_id(t)) for t in TOKEN_LOI))
    print("  cau thu vi   : {} ky tu -> {} token = {:.2f} ky tu/token".format(
        len(CAU_THU_TIENG_VIET), len(ma.ids), ky_tu_tren_token))
    print("  ghi ra       : {}".format(thu_muc_ra))
    print("    tokenizer.json, tokenizer_config.json, vocab.json, merges.txt")
    print("    bao_cao_tu_vung.json")
    print("")
    print("BUOC TIEP THEO — dung tin tu vung nay tot cho den khi do tu te:")
    print("  python3 do_tokenizer.py --bo bdsg={}".format(thu_muc_ra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
