#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Huan luyen tu vung (tokenizer) ba thu tieng: tieng Viet -> tieng Anh -> tieng Trung.

=============================================================================
VI SAO TEP NAY TON TAI, DU MiniMind KHUYEN DUNG LAM
=============================================================================
Dong dau tien cua trainer/train_tokenizer.py trong MiniMind viet nguyen van:
"khong khuyen nghi huan luyen lai tokenizer" — ly do ho neu ra la mo hinh huan
luyen tren tu dien khac se cho dau ra khong thong nhat, lam giam kha nang dung
lai trong so trong cong dong.

Canh bao do DUNG, nhung no danh cho nguoi DUNG LAI trong so da phat hanh cua
MiniMind. BDSG huan luyen TU DAU, khong nap mot byte trong so nao cua ho, nen
khong co gi de "khong thong nhat" voi. Nguoc lai, giu tu vung cua ho moi la sai:
tu vung 6.400 cua MiniMind duoc huan luyen tren ngu lieu tieng Trung + tieng Anh,
khong co tieng Viet. Byte-level BPE khong bao gio bao loi khi gap chu co dau —
no chi lang le bam chu do thanh nhieu token hon, va ngan sach ngu canh bi dot
vao dau thanh dieu.

Do khong phai suy doan. Chay huan-luyen/tu-vung/do_tokenizer.py de tu do lai
tren may minh: no dem so token tren mot ky tu tieng Viet cua tung tu vung va
so sanh truc tiep. So do la bang chung; cau van nay chi la loi dan.

=============================================================================
GIU NGUYEN CAI GI CUA MiniMind, DOI CAI GI
=============================================================================
GIU NGUYEN (bat buoc, neu khong mo hinh se khong chay duoc voi ma cua ho):
  - models.BPE + pre_tokenizers.ByteLevel(add_prefix_space=False)
    + decoders.ByteLevel, y het trainer/train_tokenizer.py dong 47 va 72.
  - Dung 36 vi tri token dac biet, DUNG THU TU do. Thu tu quan trong vi no
    quyet dinh id: <|endoftext|>=0, <|im_start|>=1, <|im_end|>=2. Ba id nay
    duoc viet cung vao cau hinh mo hinh (bos_token_id=1, eos_token_id=2 trong
    MiniMindConfig, model/model_minimind.py dong 18-19) va vao cac tep
    cau-hinh/*.json cua BDSG. Doi thu tu = hong im lang.
  - chat_template y nguyen ban cua MiniMind. Ly do: dataset/lm_dataset.py dong
    91-107 (ham generate_labels) tim chuoi "<bos>assistant\\n" va "<eos>\\n" trong chuoi da token hoa
    de dung nhan huan luyen. Doi mau hoi thoai ma khong doi ham do thi nhan se
    sai het ma KHONG bao loi — mat mat van giam, mo hinh van "hoc", chi la hoc
    sai cho. Day la kieu loi hong-ma-khong-bao.

DOI:
  - vocab_size: tham so dong lenh, mac dinh 24576 thay vi 6400. Xem README.
  - Nguon du lieu: nhieu tep, co TRONG SO theo ngon ngu, thay vi mot tep duy nhat.

=============================================================================
TRONG SO NGON NGU DUOC AP DAT NHU THE NAO
=============================================================================
BPE hoc merge tu TAN SUAT xuat hien. Muon tieng Viet chiem uu the thi phai cho
no nhieu KY TU hon trong ngu lieu huan luyen tu vung — chu khong phai nhieu tep
hon hay nhieu dong hon (mot dong tieng Trung 50 ky tu khong bang mot doan tieng
Viet 5.000 ky tu).

Nen script nay chia NGAN SACH KY TU theo ti le, mac dinh vi=0.60 / en=0.25 /
zh=0.15, roi doc tung ngon ngu cho den khi het ngan sach cua no.

Mot lua chon co y: neu mot ngon ngu KHONG DU du lieu de tieu het ngan sach,
script ghi ro phan thieu vao bao cao va van chay tiep. No KHONG lap lai van ban
de bu cho du. Lap lai van ban se lam BPE hoc thuoc chinh nhung chuoi bi lap,
sinh ra merge rac ma nhin tu vung khong thay duoc. Thieu thi ghi la thieu.

=============================================================================
CHAY
=============================================================================
  python3 huan_luyen_tu_vung.py \
      --nguon vi=/duong/dan/bdsg-da-lam-sach.jsonl \
      --nguon vi=/duong/dan/wikipedia-vi.jsonl \
      --nguon en=/duong/dan/nen-tieng-anh.jsonl \
      --nguon zh=/duong/dan/nen-tieng-trung.jsonl \
      --ti-le vi=0.60,en=0.25,zh=0.15 \
      --vocab-size 24576 \
      --ngan-sach-ky-tu 200000000 \
      --ra ../../bo-du-lieu/tu-vung-bdsg-v1

  # Thu nhanh cho chac script chay (tu sinh du lieu gia, khong dung du lieu that):
  python3 huan_luyen_tu_vung.py --tu-kiem

Chi can: python >= 3.8 va thu vien `tokenizers`. KHONG can torch, KHONG can
transformers. (Da chay thu tren python 3.9.6 + tokenizers 0.22.2, 25/09/2026.)
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

# ---------------------------------------------------------------------------
# 36 VI TRI TOKEN DAC BIET — sao chep tu trainer/train_tokenizer.py cua MiniMind
# (dong 49-60). Thu tu la hop dong voi mo hinh, dung sap xep lai.
# ---------------------------------------------------------------------------
TOKEN_DAC_BIET_LOI = [
    "<|endoftext|>", "<|im_start|>", "<|im_end|>",
    "<|object_ref_start|>", "<|object_ref_end|>", "<|box_start|>", "<|box_end|>",
    "<|quad_start|>", "<|quad_end|>",
    "<|vision_start|>", "<|vision_end|>", "<|vision_pad|>", "<|image_pad|>", "<|video_pad|>",
    "<|audio_start|>", "<|audio_end|>", "<|audio_pad|>",
    "<tts_pad>", "<tts_text_bos>", "<tts_text_eod>", "<tts_text_bos_single>",
]
TOKEN_THEM = [
    "<tool_call>", "</tool_call>",
    "<tool_response>", "</tool_response>",
    "<think>", "</think>",
]
SO_TOKEN_DAC_BIET = 36

# Mau hoi thoai (chat template) sao chep NGUYEN VAN tu model/tokenizer_config.json
# cua MiniMind (3.895 ky tu). Da doi chieu: chuoi nay giong het chuoi trong
# trainer/train_tokenizer.py (kiem bang difflib, 25/09/2026, khong co dong khac biet).
# Dung sua tay. Neu can doi, phai doi ca SFTDataset.generate_labels trong
# dataset/lm_dataset.py cung luc.
MAU_HOI_THOAI = '{%- if tools %}\n    {{- \'<|im_start|>system\\n\' }}\n    {%- if messages[0].role == \'system\' %}\n        {{- messages[0].content + \'\\n\\n\' }}\n    {%- endif %}\n    {{- "# Tools\\n\\nYou may call one or more functions to assist with the user query.\\n\\nYou are provided with function signatures within <tools></tools> XML tags:\\n<tools>" }}\n    {%- for tool in tools %}\n        {{- "\\n" }}\n        {{- tool | tojson }}\n    {%- endfor %}\n    {{- "\\n</tools>\\n\\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\\n<tool_call>\\n{\\"name\\": <function-name>, \\"arguments\\": <args-json-object>}\\n</tool_call><|im_end|>\\n" }}\n{%- else %}\n    {%- if messages[0].role == \'system\' %}\n        {{- \'<|im_start|>system\\n\' + messages[0].content + \'<|im_end|>\\n\' }}\n    {%- endif %}\n{%- endif %}\n{%- set ns = namespace(multi_step_tool=true, last_query_index=messages|length - 1) %}\n{%- for message in messages[::-1] %}\n    {%- set index = (messages|length - 1) - loop.index0 %}\n    {%- if ns.multi_step_tool and message.role == "user" and message.content is string and not(message.content.startswith(\'<tool_response>\') and message.content.endswith(\'</tool_response>\')) %}\n        {%- set ns.multi_step_tool = false %}\n        {%- set ns.last_query_index = index %}\n    {%- endif %}\n{%- endfor %}\n{%- for message in messages %}\n    {%- if message.content is string %}\n        {%- set content = message.content %}\n    {%- else %}\n        {%- set content = \'\' %}\n    {%- endif %}\n    {%- if (message.role == "user") or (message.role == "system" and not loop.first) %}\n        {{- \'<|im_start|>\' + message.role + \'\\n\' + content + \'<|im_end|>\' + \'\\n\' }}\n    {%- elif message.role == "assistant" %}\n        {%- set reasoning_content = \'\' %}\n        {%- if message.reasoning_content is string %}\n            {%- set reasoning_content = message.reasoning_content %}\n        {%- else %}\n            {%- if \'</think>\' in content %}\n                {%- set reasoning_content = content.split(\'</think>\')[0].rstrip(\'\\n\').split(\'<think>\')[-1].lstrip(\'\\n\') %}\n                {%- set content = content.split(\'</think>\')[-1].lstrip(\'\\n\') %}\n            {%- endif %}\n        {%- endif %}\n        {%- if true %}\n            {{- \'<|im_start|>\' + message.role + \'\\n<think>\\n\' + reasoning_content.strip(\'\\n\') + \'\\n</think>\\n\\n\' + content.lstrip(\'\\n\') }}\n        {%- endif %}\n        {%- if message.tool_calls %}\n            {%- for tool_call in message.tool_calls %}\n                {%- if (loop.first and content) or (not loop.first) %}\n                    {{- \'\\n\' }}\n                {%- endif %}\n                {%- if tool_call.function %}\n                    {%- set tool_call = tool_call.function %}\n                {%- endif %}\n                {{- \'<tool_call>\\n{"name": "\' }}\n                {{- tool_call.name }}\n                {{- \'", "arguments": \' }}\n                {%- if tool_call.arguments is string %}\n                    {{- tool_call.arguments }}\n                {%- else %}\n                    {{- tool_call.arguments | tojson }}\n                {%- endif %}\n                {{- \'}\\n</tool_call>\' }}\n            {%- endfor %}\n        {%- endif %}\n        {{- \'<|im_end|>\\n\' }}\n    {%- elif message.role == "tool" %}\n        {%- if loop.first or (messages[loop.index0 - 1].role != "tool") %}\n            {{- \'<|im_start|>user\' }}\n        {%- endif %}\n        {{- \'\\n<tool_response>\\n\' }}\n        {{- content }}\n        {{- \'\\n</tool_response>\' }}\n        {%- if loop.last or (messages[loop.index0 + 1].role != "tool") %}\n            {{- \'<|im_end|>\\n\' }}\n        {%- endif %}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- \'<|im_start|>assistant\\n\' }}\n    {%- if open_thinking is defined and open_thinking is true %}\n        {{- \'<think>\\n\' }}\n    {%- else %}\n        {{- \'<think>\\n\\n</think>\\n\\n\' }}\n    {%- endif %}\n{%- endif %}'

# Ba ngon ngu, theo dung thu tu uu tien cua du an.
NGON_NGU = ["vi", "en", "zh"]
TI_LE_MAC_DINH = {"vi": 0.60, "en": 0.25, "zh": 0.15}


# ---------------------------------------------------------------------------
# Doc du lieu
# ---------------------------------------------------------------------------
def doc_van_ban(duong_dan):
    """Sinh tung doan van ban tu mot tep.

    Chap nhan ba dinh dang, vi ca ba deu ton tai trong du an:
      - .jsonl kieu tien-huan-luyen : {"text": "..."}
      - .jsonl kieu SFT            : {"conversations": [{"role":..,"content":..}, ...]}
      - .txt                       : moi dong la mot doan

    Ham get_texts cua MiniMind (trainer/train_tokenizer.py dong 13-43) co mot ghi
    chu dang doc: ban dau ho chi boc truong "conversations", nen khi tro DATA_PATH
    sang tep tien-huan-luyen thi khong lay duoc dong nao, BPE chi hoc tren
    initial_alphabet va de ra mot tu vung KHONG CO MERGE NAO — ma khong bao loi.
    Do la ly do ham nay xu ly ca hai dinh dang, va ly do ham chay chinh dung lai
    neu tong so ky tu doc duoc bang 0.
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
            elif "conversations" in d:
                phan = [m.get("content") for m in d.get("conversations", [])
                        if isinstance(m, dict) and m.get("content")]
                vb = "\n".join(str(x) for x in phan)
            else:
                continue
            if vb.strip():
                yield vb


def luong_theo_ngon_ngu(cac_tep, ngan_sach_ky_tu):
    """Doc xen ke cac tep cua MOT ngon ngu cho den khi het ngan sach ky tu.

    Xen ke (round-robin) chu khong noi duoi nhau: neu noi duoi nhau, mot tep to
    doc truoc se an het ngan sach va cac tep sau khong gop duoc chu nao. Loi do
    khong bao gi ca, chi lam tu vung lech ve mot nguon.

    Tra ve (danh_sach_van_ban, so_ky_tu_da_dung, so_doan, thong_ke_tung_tep).
    """
    luong = [doc_van_ban(t) for t in cac_tep]
    con_song = [True] * len(luong)
    thong_ke = [{"tep": t, "so_doan": 0, "so_ky_tu": 0} for t in cac_tep]
    ket_qua = []
    da_dung = 0
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
            da_dung += n
            so_doan += 1
            thong_ke[i]["so_doan"] += 1
            thong_ke[i]["so_ky_tu"] += n
            if ngan_sach_ky_tu and da_dung >= ngan_sach_ky_tu:
                return ket_qua, da_dung, so_doan, thong_ke
    return ket_qua, da_dung, so_doan, thong_ke


# ---------------------------------------------------------------------------
# Huan luyen
# ---------------------------------------------------------------------------
def danh_sach_token_dac_biet():
    con_lai = SO_TOKEN_DAC_BIET - len(TOKEN_DAC_BIET_LOI) - len(TOKEN_THEM)
    if con_lai < 0:
        raise ValueError("Danh sach token dac biet dai hon {} vi tri".format(SO_TOKEN_DAC_BIET))
    dem = ["<|buffer{}|>".format(i) for i in range(1, con_lai + 1)]
    return TOKEN_DAC_BIET_LOI + TOKEN_THEM + dem


def huan_luyen(van_ban, vocab_size, thu_muc_ra):
    tokenizer = Tokenizer(models.BPE())
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)

    tat_ca_dac_biet = danh_sach_token_dac_biet()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        show_progress=True,
        # initial_alphabet = 256 byte: bao dam khong bao gio co token <unk>.
        # Chu tieng Viet co dau va chu Han deu tut xuong byte neu chua hoc merge,
        # nen "khong loi" khong co nghia la "token hoa tot".
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        special_tokens=tat_ca_dac_biet,
    )
    tokenizer.train_from_iterator(van_ban, trainer=trainer)
    tokenizer.decoder = decoders.ByteLevel()
    tokenizer.add_special_tokens(TOKEN_DAC_BIET_LOI)

    # --- Kiem tra hop dong id truoc khi ghi ra dia -------------------------
    # Neu ba id nay khong dung, cau hinh mo hinh (bos_token_id=1, eos_token_id=2)
    # se tro sai token, va hong nay KHONG bao loi luc huan luyen.
    mong_doi = {"<|endoftext|>": 0, "<|im_start|>": 1, "<|im_end|>": 2}
    for tok, id_mong in mong_doi.items():
        that = tokenizer.token_to_id(tok)
        if that != id_mong:
            raise RuntimeError(
                "Token {} co id {} nhung cau hinh mo hinh cho doi {}. "
                "Dung ghi tu vung nay ra — no se lam hong mo hinh mot cach im lang."
                .format(tok, that, id_mong))

    if not os.path.isdir(thu_muc_ra):
        os.makedirs(thu_muc_ra)
    duong_tokenizer = os.path.join(thu_muc_ra, "tokenizer.json")
    tokenizer.save(duong_tokenizer)
    tokenizer.model.save(thu_muc_ra)  # vocab.json + merges.txt, de doc bang mat

    # Danh dau lai co "special": chi 21 token loi la special, phan con lai la
    # token thuong. Buoc nay sao y MiniMind (train_tokenizer.py dong 80-84).
    with open(duong_tokenizer, "r", encoding="utf-8") as f:
        du_lieu = json.load(f)
    for tt in du_lieu.get("added_tokens", []):
        if tt["content"] not in TOKEN_DAC_BIET_LOI:
            tt["special"] = False
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
            "special": tok in TOKEN_DAC_BIET_LOI,
        }

    cau_hinh = {
        "add_bos_token": False,
        "add_eos_token": False,
        "add_prefix_space": False,
        "added_tokens_decoder": bang_giai_ma,
        "additional_special_tokens": [t for t in TOKEN_DAC_BIET_LOI if t != "<|endoftext|>"],
        "bos_token": "<|im_start|>",
        "clean_up_tokenization_spaces": False,
        "eos_token": "<|im_end|>",
        "legacy": True,
        "model_max_length": 131072,
        "pad_token": "<|endoftext|>",
        "sp_model_kwargs": {},
        "spaces_between_special_tokens": False,
        "unk_token": "<|endoftext|>",
        "image_token": "<|image_pad|>",
        "audio_token": "<|audio_pad|>",
        "video_token": "<|video_pad|>",
        "vision_bos_token": "<|vision_start|>",
        "vision_eos_token": "<|vision_end|>",
        "audio_bos_token": "<|audio_start|>",
        "audio_eos_token": "<|audio_end|>",
        "chat_template": MAU_HOI_THOAI,
        "tokenizer_class": "PreTrainedTokenizerFast",
    }
    with open(os.path.join(thu_muc_ra, "tokenizer_config.json"), "w", encoding="utf-8") as f:
        json.dump(cau_hinh, f, ensure_ascii=False, indent=4)

    return tokenizer, len(du_lieu["model"]["vocab"]), len(du_lieu["model"]["merges"])


# ---------------------------------------------------------------------------
# Dong lenh
# ---------------------------------------------------------------------------
def phan_tich_nguon(cac_chuoi):
    """'vi=/duong/dan.jsonl' -> {'vi': ['/duong/dan.jsonl', ...], ...}"""
    ra = {}
    for s in cac_chuoi:
        if "=" not in s:
            raise ValueError("--nguon phai co dang <ngon_ngu>=<duong_dan>, nhan duoc: {}".format(s))
        ng, duong = s.split("=", 1)
        ng = ng.strip().lower()
        if ng not in NGON_NGU:
            raise ValueError("Ngon ngu '{}' khong nam trong {}".format(ng, NGON_NGU))
        ra.setdefault(ng, []).append(os.path.abspath(os.path.expanduser(duong.strip())))
    return ra


def phan_tich_ti_le(s):
    """'vi=0.6,en=0.25,zh=0.15' -> dict da chuan hoa ve tong 1.0"""
    if not s:
        return dict(TI_LE_MAC_DINH)
    ra = {}
    for phan in s.split(","):
        if "=" not in phan:
            raise ValueError("--ti-le phai co dang vi=0.6,en=0.25,zh=0.15")
        k, v = phan.split("=", 1)
        k = k.strip().lower()
        if k not in NGON_NGU:
            raise ValueError("Ngon ngu '{}' khong nam trong {}".format(k, NGON_NGU))
        ra[k] = float(v)
    tong = sum(ra.values())
    if tong <= 0:
        raise ValueError("Tong ti le phai lon hon 0")
    return dict((k, v / tong) for k, v in ra.items())


def tu_kiem(thu_muc_tam):
    """Tu sinh du lieu gia de chung minh script CHAY DUOC.

    Day KHONG phai danh gia chat luong — van ban gia qua nho de noi len dieu gi
    ve tu vung. No chi tra loi mot cau hoi: script co chay tron tu dau den cuoi
    va de ra tep hop le khong.
    """
    if not os.path.isdir(thu_muc_tam):
        os.makedirs(thu_muc_tam)
    mau = {
        "vi": ["Doanh nghiep niem yet cong bo bao cao tai chinh quy ba nam 2026.",
               "Cong ty co phan bat dong san trien khai du an tai tinh Thanh Hoa.",
               "Nganh nghe kinh doanh chinh: tu van quan ly va dau tu ha tang."],
        "en": ["The company reported consolidated revenue for the third quarter.",
               "Business registration and industry classification for listed firms."],
        "zh": ["公司公布了第三季度财务报告。",
               "上市公司的主要经营范围包括基础设施投资。"],
    }
    tep = {}
    for ng, cau in mau.items():
        d = os.path.join(thu_muc_tam, "{}.jsonl".format(ng))
        with open(d, "w", encoding="utf-8") as f:
            for _ in range(200):
                for c in cau:
                    f.write(json.dumps({"text": c}, ensure_ascii=False) + "\n")
        tep[ng] = d
    return tep


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Huan luyen tu vung BPE ba thu tieng cho ho mo hinh BDSG",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nguon", action="append", default=[], metavar="NGONNGU=DUONGDAN",
                   help="nguon du lieu, lap lai duoc. Vi du: --nguon vi=/du/lieu.jsonl")
    p.add_argument("--ti-le", default=None, metavar="vi=0.6,en=0.25,zh=0.15",
                   help="ti le ngan sach ky tu theo ngon ngu (mac dinh vi=0.60,en=0.25,zh=0.15)")
    p.add_argument("--vocab-size", type=int, default=24576,
                   help="kich thuoc tu vung (mac dinh 24576; MiniMind dung 6400 cho hai thu tieng)")
    p.add_argument("--ngan-sach-ky-tu", type=int, default=200000000,
                   help="tong so ky tu dua vao huan luyen BPE; 0 = khong gioi han (mac dinh 200 trieu)")
    p.add_argument("--ra", default="./tu-vung-bdsg", help="thu muc ghi ket qua")
    p.add_argument("--tu-kiem", action="store_true",
                   help="tu sinh du lieu gia va chay thu (chung minh script chay duoc)")
    args = p.parse_args(argv)

    bat_dau = time.time()

    if args.tu_kiem:
        import tempfile
        tam = tempfile.mkdtemp(prefix="tu-vung-tu-kiem-")
        tep = tu_kiem(tam)
        nguon = dict((k, [v]) for k, v in tep.items())
        args.vocab_size = min(args.vocab_size, 1000)
        args.ngan_sach_ky_tu = 0
        args.ra = os.path.join(tam, "ra")
        print("[tu-kiem] du lieu gia o {}".format(tam))
    else:
        if not args.nguon:
            p.error("Phai co it nhat mot --nguon (hoac dung --tu-kiem de chay thu)")
        nguon = phan_tich_nguon(args.nguon)

    ti_le = phan_tich_ti_le(args.ti_le)

    thieu_tep = []
    for ng, ds in nguon.items():
        for t in ds:
            if not os.path.isfile(t):
                thieu_tep.append(t)
    if thieu_tep:
        p.error("Khong tim thay tep:\n  " + "\n  ".join(thieu_tep))

    print("")
    print("Ngan sach ky tu: {}".format(
        "khong gioi han" if not args.ngan_sach_ky_tu else "{:,}".format(args.ngan_sach_ky_tu)))
    print("Ti le ngon ngu : " + ", ".join("{}={:.2f}".format(k, ti_le.get(k, 0.0)) for k in NGON_NGU))
    print("vocab_size     : {}".format(args.vocab_size))
    print("")

    tat_ca_van_ban = []
    bao_cao_ngon_ngu = {}
    for ng in NGON_NGU:          # luon theo thu tu vi -> en -> zh
        if ng not in nguon:
            print("  {}: khong co nguon nao -> bo qua".format(ng))
            bao_cao_ngon_ngu[ng] = {"ngan_sach": 0, "da_dung": 0, "so_doan": 0,
                                    "thieu": 0, "tep": []}
            continue
        ngan_sach = int(args.ngan_sach_ky_tu * ti_le.get(ng, 0.0)) if args.ngan_sach_ky_tu else 0
        vb, da_dung, so_doan, tk = luong_theo_ngon_ngu(nguon[ng], ngan_sach)
        thieu = max(0, ngan_sach - da_dung) if ngan_sach else 0
        tat_ca_van_ban.extend(vb)
        bao_cao_ngon_ngu[ng] = {"ngan_sach": ngan_sach, "da_dung": da_dung,
                                "so_doan": so_doan, "thieu": thieu, "tep": tk}
        canh_bao = ""
        if thieu:
            canh_bao = "  <-- THIEU {:,} ky tu ({:.1f}% ngan sach). Khong bu bang cach lap lai.".format(
                thieu, 100.0 * thieu / ngan_sach)
        print("  {}: {:,} doan, {:,} ky tu{}".format(ng, so_doan, da_dung, canh_bao))

    tong_ky_tu = sum(v["da_dung"] for v in bao_cao_ngon_ngu.values())
    if tong_ky_tu == 0:
        sys.stderr.write(
            "\nKHONG doc duoc ky tu nao. Neu van chay tiep, BPE chi hoc tren 256 byte\n"
            "goc va de ra mot tu vung khong co merge nao — ma khong bao loi. Dung lai.\n"
            "Kiem lai: tep .jsonl co truong \"text\" hoac \"conversations\" khong?\n")
        return 2

    print("")
    print("Tong: {:,} doan, {:,} ky tu. Bat dau huan luyen BPE...".format(
        len(tat_ca_van_ban), tong_ky_tu))
    print("")

    thu_muc_ra = os.path.abspath(os.path.expanduser(args.ra))
    tokenizer, so_tu, so_merge = huan_luyen(tat_ca_van_ban, args.vocab_size, thu_muc_ra)
    giay = time.time() - bat_dau

    # Ti le thuc te tung ngon ngu chiem trong ngu lieu huan luyen — ghi lai con
    # so DUOC, khong phai con so DINH.
    for ng in NGON_NGU:
        bao_cao_ngon_ngu[ng]["ti_le_dinh"] = ti_le.get(ng, 0.0)
        bao_cao_ngon_ngu[ng]["ti_le_that"] = (
            bao_cao_ngon_ngu[ng]["da_dung"] / float(tong_ky_tu)) if tong_ky_tu else 0.0

    bao_cao = {
        "ngay_chay": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "vocab_size_yeu_cau": args.vocab_size,
        "vocab_size_that": so_tu,
        "so_merge": so_merge,
        "so_token_dac_biet": SO_TOKEN_DAC_BIET,
        "id_kiem_tra": {t: tokenizer.token_to_id(t) for t in
                        ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<think>", "</think>"]},
        "tong_ky_tu": tong_ky_tu,
        "tong_doan": len(tat_ca_van_ban),
        "ngan_sach_ky_tu": args.ngan_sach_ky_tu,
        "theo_ngon_ngu": bao_cao_ngon_ngu,
        "giay_chay": round(giay, 1),
        "ghi_chu": ("Ti le THAT co the lech ti le DINH neu mot ngon ngu khong du du lieu. "
                    "Xem truong 'thieu'. Script khong lap lai van ban de bu."),
    }
    duong_bao_cao = os.path.join(thu_muc_ra, "bao_cao_tu_vung.json")
    with open(duong_bao_cao, "w", encoding="utf-8") as f:
        json.dump(bao_cao, f, ensure_ascii=False, indent=2)

    print("")
    print("Xong sau {:.1f} giay.".format(giay))
    print("  tu vung that : {} tu, {} merge".format(so_tu, so_merge))
    print("  id kiem tra  : " + ", ".join(
        "{}={}".format(k, v) for k, v in bao_cao["id_kiem_tra"].items()))
    print("  ghi ra       : {}".format(thu_muc_ra))
    print("    tokenizer.json, tokenizer_config.json, vocab.json, merges.txt")
    print("    bao_cao_tu_vung.json")
    print("")
    print("BUOC TIEP THEO — dung tin tu vung nay tot cho den khi do:")
    print("  python3 do_tokenizer.py --bo bdsg={} \\".format(thu_muc_ra))
    print("                          --bo minimind=<thu-muc-minimind>/model")
    return 0


if __name__ == "__main__":
    sys.exit(main())
