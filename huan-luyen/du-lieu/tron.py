#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tron ngu lieu ba thu tieng theo ti le, xuat dung dinh dang MiniMind doc duoc.

=============================================================================
XUAT RA CAI GI
=============================================================================
Hai dinh dang, vi MiniMind co hai lop Dataset khac nhau doc chung
(da doc dataset/lm_dataset.py, khong doan):

  --dinh-dang pretrain -> moi dong: {"text": "..."}
       PretrainDataset (lm_dataset.py dong 40-58) doc truong "text".
  --dinh-dang sft      -> moi dong: {"conversations": [{"role": .., "content": ..}, ...]}
       SFTDataset (lm_dataset.py dong 61-123) doc truong "conversations".

=============================================================================
BA DIEU DA DOC RA TU MA CUA HO, VA HAU QUA
=============================================================================
1. PretrainDataset CAT CUT, KHONG GHEP GOI.
   Dong 52: tokenizer(..., max_length=self.max_length - 2, truncation=True).
   Nghia la mot doan dai hon max_seq_len thi phan duoi bi VUT, khong duoc day
   sang mau sau. train_pretrain.py de mac dinh max_seq_len=340.
   => Neu do nguyen doan 4.000 ky tu vao, phan lon doan do khong bao gio duoc
      hoc, ma khong co dong log nao noi. Vi vay script nay CAT DOAN (--cat-doan)
      theo ranh gioi cau truoc khi ghi ra. Mac dinh 0 = khong cat; phai tu bat
      sau khi do so ky tu tren mot token bang do_tokenizer.py.

2. SFTDataset ep kieu du lieu chat.
   Dong 66: Features({'conversations': [{'role': Value('string'),
            'content': Value('string'), 'reasoning_content': ..., 'tools': ...,
            'tool_calls': ...}]}). Tat ca deu la CHUOI.
   => tools va tool_calls neu co phai la chuoi JSON, khong phai doi tuong.
      Script nay kiem lai truoc khi ghi, va bao loi som thay vi de load_dataset
      no giua chung huan luyen.

3. Nhan huan luyen SFT duoc tim bang chuoi.
   generate_labels (dong 91-107) tim "<bos>assistant\\n" ... "<eos>\\n" de biet
   phan nao la cau tra loi cua tro ly. Cho nen vai tro (role) phai dung ten
   chuan: system / user / assistant / tool. Viet "bot" hay "ai" thi khong bao
   loi — chi la khong co doan nao duoc gan nhan, va mo hinh hoc tu con so 0
   tin hieu. Script nay tu choi ghi ra neu gap vai tro la.

=============================================================================
TRON RA SAO — VA VI SAO KHONG XEP KHOI
=============================================================================
Tron theo NHIP (xen ke deu), khong noi duoi nhau tung khoi ngon ngu. Ly do:
  - De ai cat bot tep di cung con du ba thu tieng.
  - De doc log mat mat theo thoi gian con co nghia.
PretrainDataset co xao tron o tang tren (train_pretrain.py dong 151 dung
torch.randperm), nen xen ke khong phai de thay xao tron — la de tep TU NO da
can bang o moi doan.

TI LE tinh theo KY TU, khong theo so dong. Mot dong tieng Trung 50 ky tu khong
bang mot doan tieng Viet 5.000 ky tu; dem dong se cho ti le sai hoan toan.

=============================================================================
DIEU SCRIPT NAY TU CHOI LAM
=============================================================================
No KHONG tu bien van ban tron thanh hoi-dap. Muon xuat SFT thi nguon phai
THUC SU co doi thoai — hoac san truong "conversations", hoac co hai truong cau
hoi / cau tra loi de anh xa bang --truong-hoi va --truong-dap.
Boc mot doan van vao mot cau hoi tu che kieu "Hay noi ve doanh nghiep nay" la
BIA du lieu huan luyen: mo hinh se hoc rang moi doan van deu la cau tra loi cho
mot cau hoi khong ai hoi.

Chay:
    # pretrain, tron ba thu tieng:
    python3 tron.py --dinh-dang pretrain \
        --nguon vi=../../bo-du-lieu/bdsg.sach.jsonl \
        --nguon vi=../../bo-du-lieu/wikipedia-vi.jsonl \
        --nguon en=../../bo-du-lieu/nen-en.jsonl \
        --nguon zh=../../bo-du-lieu/nen-zh.jsonl \
        --ti-le vi=0.70,en=0.20,zh=0.10 \
        --cat-doan 1200 \
        --ra ../../bo-du-lieu/pretrain-tron.jsonl

    # sft, chi tu nguon that su co doi thoai:
    python3 tron.py --dinh-dang sft \
        --nguon vi=../../bo-du-lieu/hoi-dap-vi.jsonl \
        --ra ../../bo-du-lieu/sft-tron.jsonl

Chi can python >= 3.8. Khong can thu vien ngoai.
"""

import argparse
import datetime
import json
import os
import random
import re
import sys

NGON_NGU = ["vi", "en", "zh"]
TI_LE_MAC_DINH = {"vi": 0.70, "en": 0.20, "zh": 0.10}
VAI_TRO_HOP_LE = {"system", "user", "assistant", "tool"}

# Cat cau: dau cham cau ket thuc cau cua ca ba he chu viet.
MAU_HET_CAU = re.compile(r"(?<=[.!?。！？])\s+")


def cat_theo_cau(van_ban, toi_da_ky_tu):
    """Cat doan dai thanh nhieu manh, uu tien ranh gioi cau.

    Neu mot cau don le da dai hon gioi han thi cat cung tai gioi han — mat mot
    cau bi dut con hon mat ca phan duoi vi PretrainDataset cat cut (xem dau tep).
    """
    if toi_da_ky_tu <= 0 or len(van_ban) <= toi_da_ky_tu:
        return [van_ban]
    manh = []
    hien_tai = []
    dai = 0
    for cau in MAU_HET_CAU.split(van_ban):
        if not cau:
            continue
        if len(cau) > toi_da_ky_tu:
            if hien_tai:
                manh.append(" ".join(hien_tai))
                hien_tai, dai = [], 0
            for i in range(0, len(cau), toi_da_ky_tu):
                manh.append(cau[i:i + toi_da_ky_tu])
            continue
        if dai + len(cau) + 1 > toi_da_ky_tu and hien_tai:
            manh.append(" ".join(hien_tai))
            hien_tai, dai = [], 0
        hien_tai.append(cau)
        dai += len(cau) + 1
    if hien_tai:
        manh.append(" ".join(hien_tai))
    return [m for m in manh if m.strip()]


def kiem_doi_thoai(hoi_thoai, so_dong):
    """Kiem mot doi thoai co dung khuon SFTDataset khong. Tra ve loi dau tien."""
    if not isinstance(hoi_thoai, list) or not hoi_thoai:
        return "conversations rong hoac khong phai danh sach"
    co_assistant = False
    for i, m in enumerate(hoi_thoai):
        if not isinstance(m, dict):
            return "phan tu {} khong phai doi tuong".format(i)
        vt = m.get("role")
        if vt not in VAI_TRO_HOP_LE:
            return ("vai tro '{}' khong hop le (chi nhan {}). "
                    "Vai tro la se KHONG bao loi luc huan luyen, chi lam khong doan "
                    "nao duoc gan nhan.".format(vt, sorted(VAI_TRO_HOP_LE)))
        if not isinstance(m.get("content", ""), str):
            return "content cua phan tu {} khong phai chuoi".format(i)
        for truong in ("tools", "tool_calls", "reasoning_content"):
            if truong in m and m[truong] is not None and not isinstance(m[truong], str):
                return ("truong '{}' o phan tu {} phai la CHUOI JSON, khong phai doi tuong "
                        "— SFTDataset khai bao Features kieu Value('string') "
                        "(lm_dataset.py dong 66).".format(truong, i))
        if vt == "assistant":
            co_assistant = True
    if not co_assistant:
        return "khong co luot 'assistant' nao -> khong co gi de hoc"
    return None


def doc_nguon(duong_dan, dinh_dang, truong_hoi, truong_dap, cat_doan, loi_bo_qua):
    """Sinh tung ban ghi da dung dinh dang dich, kem so ky tu cua no."""
    so_dong = 0
    with open(duong_dan, "r", encoding="utf-8", errors="ignore") as f:
        for dong in f:
            so_dong += 1
            dong = dong.strip()
            if not dong:
                continue
            try:
                d = json.loads(dong)
            except ValueError:
                loi_bo_qua.append((duong_dan, so_dong, "khong phai JSON hop le"))
                continue
            if not isinstance(d, dict):
                loi_bo_qua.append((duong_dan, so_dong, "dong khong phai doi tuong JSON"))
                continue

            if dinh_dang == "pretrain":
                if "text" in d:
                    vb = str(d["text"])
                elif "noi_dung" in d:
                    vb = str(d["noi_dung"])
                elif "conversations" in d:
                    # Doi thoai van dung lam ngu lieu tien-huan-luyen duoc: noi
                    # cac luot lai. Nguoc lai thi khong (xem dau tep).
                    vb = "\n".join(str(m.get("content", "")) for m in d["conversations"]
                                   if isinstance(m, dict))
                else:
                    loi_bo_qua.append((duong_dan, so_dong, "khong co truong text/noi_dung/conversations"))
                    continue
                if not vb.strip():
                    continue
                for manh in cat_theo_cau(vb, cat_doan):
                    yield {"text": manh}, len(manh)

            else:  # sft
                if "conversations" in d:
                    ht = d["conversations"]
                elif truong_hoi and truong_dap and truong_hoi in d and truong_dap in d:
                    # Anh xa hai truong co san thanh mot luot hoi-dap. Day la
                    # ANH XA du lieu da co, khong phai bia cau hoi.
                    ht = [{"role": "user", "content": str(d[truong_hoi])},
                          {"role": "assistant", "content": str(d[truong_dap])}]
                else:
                    loi_bo_qua.append((
                        duong_dan, so_dong,
                        "khong co 'conversations' va khong co cap --truong-hoi/--truong-dap. "
                        "Script khong tu bia cau hoi tu van ban tron."))
                    continue
                loi = kiem_doi_thoai(ht, so_dong)
                if loi:
                    loi_bo_qua.append((duong_dan, so_dong, loi))
                    continue
                sach = []
                for m in ht:
                    moi = {"role": m["role"], "content": str(m.get("content", ""))}
                    for truong in ("reasoning_content", "tools", "tool_calls"):
                        if m.get(truong):
                            moi[truong] = m[truong]
                    sach.append(moi)
                n = sum(len(m["content"]) for m in sach)
                yield {"conversations": sach}, n


def phan_tich_nguon(cac_chuoi):
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
    if not s:
        return dict(TI_LE_MAC_DINH)
    ra = {}
    for phan in s.split(","):
        if "=" not in phan:
            raise ValueError("--ti-le phai co dang vi=0.70,en=0.20,zh=0.10")
        k, v = phan.split("=", 1)
        k = k.strip().lower()
        if k not in NGON_NGU:
            raise ValueError("Ngon ngu '{}' khong nam trong {}".format(k, NGON_NGU))
        ra[k] = float(v)
    tong = sum(ra.values())
    if tong <= 0:
        raise ValueError("Tong ti le phai lon hon 0")
    return dict((k, v / tong) for k, v in ra.items())


def main(argv=None):
    p = argparse.ArgumentParser(description="Tron ngu lieu ba thu tieng cho MiniMind")
    p.add_argument("--nguon", action="append", default=[], required=False,
                   metavar="NGONNGU=DUONGDAN", help="nguon du lieu, lap lai duoc")
    p.add_argument("--dinh-dang", choices=["pretrain", "sft"], default="pretrain",
                   help="pretrain -> {'text':..}; sft -> {'conversations':[..]}")
    p.add_argument("--ti-le", default=None, metavar="vi=0.70,en=0.20,zh=0.10",
                   help="ti le KY TU theo ngon ngu (mac dinh vi=0.70,en=0.20,zh=0.10)")
    p.add_argument("--ra", required=True, help="tep JSONL dau ra")
    p.add_argument("--cat-doan", type=int, default=0,
                   help="cat doan dai hon N ky tu theo ranh gioi cau; 0 = khong cat. "
                        "XEM phan dau tep: PretrainDataset cat cut phan thua ma khong bao.")
    p.add_argument("--tong-ky-tu", type=int, default=0,
                   help="tong ngan sach ky tu dau ra; 0 = dung het du lieu co")
    p.add_argument("--truong-hoi", default=None, help="ten truong cau hoi (chi cho --dinh-dang sft)")
    p.add_argument("--truong-dap", default=None, help="ten truong cau tra loi (chi cho --dinh-dang sft)")
    p.add_argument("--hat-giong", type=int, default=42, help="hat giong ngau nhien (mac dinh 42)")
    p.add_argument("--bao-cao", default=None, help="tep JSON ghi bao cao")
    args = p.parse_args(argv)

    if not args.nguon:
        p.error("Phai co it nhat mot --nguon <ngon_ngu>=<duong_dan>")
    try:
        nguon = phan_tich_nguon(args.nguon)
        ti_le = phan_tich_ti_le(args.ti_le)
    except ValueError as e:
        p.error(str(e))

    thieu = [t for ds in nguon.values() for t in ds if not os.path.isfile(t)]
    if thieu:
        p.error("Khong tim thay tep:\n  " + "\n  ".join(thieu))

    rng = random.Random(args.hat_giong)
    loi_bo_qua = []

    # --- Doc tung ngon ngu vao bo nho -------------------------------------
    # Doc het roi moi tron: can biet tong so ky tu that cua tung ngon ngu de
    # tinh nhip xen ke cho dung. Voi ngu lieu co vai GB thi phai doi sang cach
    # doc hai luot; o quy mo hien tai (7,16 MB BDSG + ngu lieu nen tai ve) thi
    # doc mot luot la du va de kiem hon.
    kho = {}
    print("")
    for ng in NGON_NGU:
        if ng not in nguon:
            print("  {}: khong co nguon -> bo qua".format(ng))
            continue
        ban_ghi = []
        tong = 0
        for t in nguon[ng]:
            for bg, n in doc_nguon(t, args.dinh_dang, args.truong_hoi, args.truong_dap,
                                   args.cat_doan, loi_bo_qua):
                ban_ghi.append((bg, n))
                tong += n
        rng.shuffle(ban_ghi)
        kho[ng] = {"ban_ghi": ban_ghi, "ky_tu_co": tong}
        print("  {}: {:,} ban ghi, {:,} ky tu tu {} tep".format(
            ng, len(ban_ghi), tong, len(nguon[ng])))

    if not kho or all(not v["ban_ghi"] for v in kho.values()):
        sys.stderr.write("\nKhong doc duoc ban ghi nao. Xem phan 'dong bi bo qua' ben duoi.\n")
        for t, d, ly in loi_bo_qua[:20]:
            sys.stderr.write("  {}:{}  {}\n".format(os.path.basename(t), d, ly))
        return 2

    # --- Quyet dinh ngan sach ky tu cho tung ngon ngu ---------------------
    # Ngon ngu nao it du lieu nhat se quyet dinh quy mo, neu muon giu DUNG ti le.
    # Con so nay tinh ra chu khong dat tay, va duoc in ra de nguoi chay thay
    # minh dang phai bo bot bao nhieu cua cac ngon ngu con lai.
    co_mat = [ng for ng in NGON_NGU if kho.get(ng, {}).get("ban_ghi")]
    if args.tong_ky_tu:
        tong_dich = args.tong_ky_tu
    else:
        kha_thi = []
        for ng in co_mat:
            r = ti_le.get(ng, 0.0)
            if r > 0:
                kha_thi.append(kho[ng]["ky_tu_co"] / r)
        tong_dich = int(min(kha_thi)) if kha_thi else sum(kho[ng]["ky_tu_co"] for ng in co_mat)

    ngan_sach = {}
    for ng in co_mat:
        muon = int(tong_dich * ti_le.get(ng, 0.0))
        ngan_sach[ng] = min(muon, kho[ng]["ky_tu_co"])

    print("")
    # Cot "ngan sach" la so DINH truoc khi ghi; so ky tu THAT se nhinh hon mot
    # chut vi ngan sach duoc kiem TRUOC khi ghi ban ghi cuoi, khong cat doi no.
    # Con so that in o phan ket qua ben duoi.
    print("  {:<5} {:>14} {:>14} {:>9} {:>9}".format(
        "ngon", "ky tu co", "ngan sach", "ti le dat", "ti le nsach"))
    print("  " + "-" * 56)
    tong_dung = sum(ngan_sach.values()) or 1
    for ng in co_mat:
        print("  {:<5} {:>14,} {:>14,} {:>9.3f} {:>9.3f}".format(
            ng, kho[ng]["ky_tu_co"], ngan_sach[ng], ti_le.get(ng, 0.0),
            ngan_sach[ng] / float(tong_dung)))

    # --- Xen ke theo nhip -------------------------------------------------
    # Moi ngon ngu co mot "no" cong don moi buoc bang ti le cua no; ai no nhieu
    # nhat thi duoc ghi truoc. Day la thuat toan chia ghe kieu du phan lon nhat,
    # cho ra chuoi xen ke deu va TAT DINH (cung hat giong -> cung tep).
    vi_tri = dict((ng, 0) for ng in co_mat)
    da_dung = dict((ng, 0) for ng in co_mat)
    no = dict((ng, 0.0) for ng in co_mat)
    tong_ti_le = sum(ti_le.get(ng, 0.0) for ng in co_mat) or 1.0

    duong_ra = os.path.abspath(os.path.expanduser(args.ra))
    thu_muc = os.path.dirname(duong_ra)
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc)

    so_ghi = dict((ng, 0) for ng in co_mat)
    tong_ghi = 0
    with open(duong_ra, "w", encoding="utf-8") as f:
        while True:
            con = [ng for ng in co_mat
                   if vi_tri[ng] < len(kho[ng]["ban_ghi"]) and da_dung[ng] < ngan_sach[ng]]
            if not con:
                break
            for ng in con:
                no[ng] += ti_le.get(ng, 0.0) / tong_ti_le
            chon = max(con, key=lambda x: no[x])
            no[chon] -= 1.0
            bg, n = kho[chon]["ban_ghi"][vi_tri[chon]]
            vi_tri[chon] += 1
            da_dung[chon] += n
            so_ghi[chon] += 1
            tong_ghi += 1
            f.write(json.dumps(bg, ensure_ascii=False) + "\n")

    print("")
    print("  Da ghi {:,} ban ghi ({:,} ky tu) ra {}".format(
        tong_ghi, sum(da_dung.values()), duong_ra))
    for ng in co_mat:
        print("    {}: {:,} ban ghi, {:,} ky tu".format(ng, so_ghi[ng], da_dung[ng]))

    if loi_bo_qua:
        print("")
        print("  {:,} dong bi bo qua. Ly do (5 dau tien):".format(len(loi_bo_qua)))
        for t, d, ly in loi_bo_qua[:5]:
            print("    {}:{}  {}".format(os.path.basename(t), d, ly))
        print("  (day la con so DANG CHU Y — neu no lon, dinh dang nguon dang sai)")

    bao_cao = {
        "ngay_chay": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dinh_dang": args.dinh_dang,
        "tep_ra": duong_ra,
        "hat_giong": args.hat_giong,
        "cat_doan": args.cat_doan,
        "ti_le_dat": ti_le,
        "theo_ngon_ngu": dict((ng, {
            "ky_tu_co": kho[ng]["ky_tu_co"],
            "ky_tu_dung": da_dung.get(ng, 0),
            "so_ban_ghi_ghi": so_ghi.get(ng, 0),
            "ti_le_that": da_dung.get(ng, 0) / float(sum(da_dung.values()) or 1),
        }) for ng in co_mat),
        "tong_ban_ghi": tong_ghi,
        "tong_ky_tu": sum(da_dung.values()),
        "so_dong_bo_qua": len(loi_bo_qua),
        "vai_dong_bo_qua": [{"tep": t, "dong": d, "ly_do": ly} for t, d, ly in loi_bo_qua[:50]],
    }
    duong_bc = args.bao_cao or (os.path.splitext(duong_ra)[0] + ".bao-cao-tron.json")
    with open(duong_bc, "w", encoding="utf-8") as f:
        json.dump(bao_cao, f, ensure_ascii=False, indent=2)
    print("")
    print("  Bao cao: {}".format(duong_bc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
