#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Do chat luong tu vung (tokenizer) tren tieng Viet va tieng Anh — va so sanh nhieu bo.

=============================================================================
TEP NAY LA CAI GI
=============================================================================
Kho nay khang dinh: mot tu vung khong hoc tieng Viet se bam chu tieng Viet co
dau thanh qua nhieu token. Mot khang dinh khong co so do di kem thi chi la y
kien. Tep nay la cai may do.

No tra loi bon cau hoi, va chi bon cau hoi do:

  1. Mot ky tu tieng Viet ton bao nhieu token?  (thap la tot)
  2. Chu CO DAU co bi bam vun hon chu KHONG DAU khong, trong CUNG mot tu vung?
     Day moi la phep so co gia tri nhat: no loai bo moi khac biet ve do dai tu,
     ve chu de van ban, ve kich thuoc tu vung — chi con lai dung mot bien la
     dau thanh.
  3. Bao nhieu token khong che duoc tron mot ky tu moi nao (manh byte)?
     Byte-level BPE khong bao gio bao loi khi gap chu la, no tut xuong muc byte.
     Mot chu tieng Viet trong UTF-8 chiem 2-3 byte, nen mot chu khong co merge
     se thanh 2-3 token byte. Day la cho tien ngu canh chay ra ma khong ai thay.
  4. So sanh truc tiep hai hay nhieu tu vung tren CUNG mot van ban.

NO KHONG tra loi: tu vung nao lam mo hinh thong minh hon. Do phai do bang bo
danh gia tren mo hinh da huan luyen (danh-gia/), khong phai bang may dem token.
Nen tot la dieu kien CAN, khong phai dieu kien DU.

=============================================================================
CACH SO SANH CONG BANG — DOC TRUOC KHI TIN BAT KY CON SO NAO
=============================================================================
Hai luat, vi pham mot trong hai la phep do vo nghia:

  LUAT 1 — CUNG KICH THUOC TU VUNG. Tu vung lon hon LUON nen tot hon, bat ke no
  hoc tieng gi. Khoe "toi giam duoc 66% token" trong khi am tham tang tu vung
  tu 6.400 len 24.576 la so sanh gian. Script nay IN RA kich thuoc that cua
  tung bo va CANH BAO khi chung lech nhau, de khong ai vo tinh doc nham.

  LUAT 2 — DOI CHUNG PHAI TU SINH DUOC. Doi chung tot nhat khong phai tu vung
  cua nguoi khac ma la tu vung do CHINH minh huan luyen, chi khac mot bien.
  Sinh no nhu sau (khong can du lieu cua ai):

      python3 huan_luyen_tu_vung.py --nguon-anh <ngu-lieu-tieng-anh.jsonl> \\
          --ti-le-viet 0 --ti-le-anh 1 --tu-vung 6400 --ra /tmp/doi-chung-en

  Ban do chung la mot tu vung CUNG 6.400 nhung KHONG hoc tieng Viet. So no voi
  ban hoc tieng Viet thi khac biet con dung mot bien, va ca phep do tu chua —
  khong phu thuoc vao tu vung cua bat ky ai.

=============================================================================
CHAY
=============================================================================
  # so hai bo tren van ban mau co san:
  python3 do_tokenizer.py --bo bdsg=../../bo-du-lieu/tu-vung-bdsg-v1 \\
                          --bo doi-chung-en=/tmp/doi-chung-en

  # do tren ngu lieu that cua minh thay vi van ban mau:
  python3 do_tokenizer.py --bo bdsg=<thu-muc> --van-ban vi_co_dau=/du/lieu/bdsg.jsonl

  # ghi ket qua ra JSON de dua vao bao cao:
  python3 do_tokenizer.py --bo ... --ra ket-qua-do.json

Chi can python >= 3.8 va thu vien `tokenizers`. KHONG can torch/transformers.
"""

import argparse
import json
import os
import sys
import unicodedata

try:
    from tokenizers import Tokenizer
except ImportError:
    sys.stderr.write("Thieu thu vien `tokenizers`. Cai bang: pip install tokenizers\n")
    raise

# ---------------------------------------------------------------------------
# Van ban mau. Tu viet, khong lay tu nguon co ban quyen.
#
# Ba nhan, va ba nhan nay la mot thiet ke chu khong phai liet ke tuy tien:
#   vi_co_dau    — tieng Viet dung chinh ta day du. Day la cai can do.
#   vi_khong_dau — DUNG NOI DUNG AY, chi bo dau. Day la doi chung noi bo: moi
#                  khac biet giua hai dong nay chi con do dau thanh gay ra.
#   en           — tieng Anh, de thay tu vung co thien vi ngon ngu nao.
#
# Chu de co tinh: van phong ho so doanh nghiep — dung loai van ban ma mo hinh
# nay se phai doc. Do tokenizer tren van chuong roi ket luan cho ho so tai
# chinh la do sai doi tuong.
# ---------------------------------------------------------------------------
VAN_BAN_MAU = {
    "vi_co_dau": [
        "Công ty cổ phần đầu tư và phát triển bất động sản công bố báo cáo tài chính "
        "hợp nhất quý ba năm 2026, với doanh thu thuần đạt mức tăng trưởng hai con số "
        "so với cùng kỳ năm trước.",
        "Doanh nghiệp đăng ký ngành nghề kinh doanh chính là tư vấn quản lý, xây dựng "
        "công trình kỹ thuật dân dụng và kinh doanh bất động sản, quyền sử dụng đất "
        "thuộc chủ sở hữu, chủ sử dụng hoặc đi thuê.",
        "Hội đồng quản trị thông qua nghị quyết về việc triển khai dự án khu đô thị "
        "mới tại tỉnh Thanh Hóa, tổng mức đầu tư dự kiến được phê duyệt trong kỳ họp "
        "thường niên sắp tới.",
    ],
    "vi_khong_dau": [
        "Cong ty co phan dau tu va phat trien bat dong san cong bo bao cao tai chinh "
        "hop nhat quy ba nam 2026, voi doanh thu thuan dat muc tang truong hai con so "
        "so voi cung ky nam truoc.",
        "Doanh nghiep dang ky nganh nghe kinh doanh chinh la tu van quan ly, xay dung "
        "cong trinh ky thuat dan dung va kinh doanh bat dong san, quyen su dung dat "
        "thuoc chu so huu, chu su dung hoac di thue.",
        "Hoi dong quan tri thong qua nghi quyet ve viec trien khai du an khu do thi "
        "moi tai tinh Thanh Hoa, tong muc dau tu du kien duoc phe duyet trong ky hop "
        "thuong nien sap toi.",
    ],
    "en": [
        "The company published its consolidated financial statements for the third "
        "quarter of 2026, reporting double-digit growth in net revenue compared with "
        "the same period last year.",
        "The registered lines of business include management consulting, civil "
        "engineering construction, and real estate trading of land use rights owned, "
        "used or leased by the enterprise.",
    ],
}

NHAN = {
    "vi_co_dau": "tieng Viet CO dau",
    "vi_khong_dau": "tieng Viet KHONG dau",
    "en": "tieng Anh",
}

# Cua so ngu canh dung de quy doi con so tru tuong "token moi ky tu" thanh cau
# "doc duoc bao nhieu chu". 2048 KHONG phai so dat de minh hoa: do la dung
# max_position_embeddings ma ca ba tep huan-luyen/cau-hinh/*.json (nho/vua/lon)
# khai, do lai 26/09/2026. Lay dung tran that de cau "doc duoc bao nhieu chu"
# noi ve mo hinh BDSG chu khong ve mot mo hinh tuong tuong. Doi bang --cua-so
# neu muon quy doi sang mot tran khac.
CUA_SO_MAC_DINH = 2048


def co_dau_tieng_viet(ch):
    """True neu ky tu la chu cai Latin mang dau tieng Viet.

    Cach do: tach ky tu ra dang NFD; neu con lai mot dau ket hop (category Mn)
    thi la chu co dau. Rieng d-gach (d/D) khong co dau ket hop trong NFD nen
    phai liet ke tay — bo sot no lam moi con so "tu co dau" thap di mot cach
    co he thong.
    """
    if ch in "đĐ":
        return True
    tach = unicodedata.normalize("NFD", ch)
    return len(tach) > 1 and any(unicodedata.category(c) == "Mn" for c in tach)


def tach_tu(van_ban):
    """Tach thanh tu theo khoang trang, bo dau cau o hai dau."""
    ra = []
    for tho in van_ban.split():
        tu = tho.strip(".,;:!?()[]{}\"'’“”–—")
        if tu:
            ra.append(tu)
    return ra


def nap_tokenizer(duong_dan):
    """Nhan duong dan thu muc (co tokenizer.json) hoac chinh tep tokenizer.json."""
    d = os.path.abspath(os.path.expanduser(duong_dan))
    if os.path.isdir(d):
        d = os.path.join(d, "tokenizer.json")
    if not os.path.isfile(d):
        raise IOError("Khong thay tokenizer.json tai: {}".format(d))
    return Tokenizer.from_file(d), d


def do_van_ban(tok, van_ban):
    """Do nen ngu canh tren mot doan van ban."""
    enc = tok.encode(van_ban, add_special_tokens=False)
    so_token = len(enc.ids)
    so_ky_tu = len(van_ban)

    # Token khong che duoc ky tu MOI nao = manh byte giua chung mot ky tu. Voi
    # ByteLevel, nhieu token lien tiep cung tro vao mot ky tu se cho khoang
    # offset khong phu them ky tu nao. Dem theo offset chac an hon la doan tu
    # hinh dang chuoi token.
    da_che = [False] * so_ky_tu
    token_khong_che = 0
    for (a, b) in enc.offsets:
        if b <= a:
            token_khong_che += 1
            continue
        moi = False
        for i in range(a, min(b, so_ky_tu)):
            if not da_che[i]:
                da_che[i] = True
                moi = True
        if not moi:
            token_khong_che += 1

    return {
        "so_ky_tu": so_ky_tu,
        "so_token": so_token,
        "token_tren_ky_tu": so_token / float(so_ky_tu) if so_ky_tu else 0.0,
        "ky_tu_tren_token": so_ky_tu / float(so_token) if so_token else 0.0,
        "token_khong_che_ky_tu_moi": token_khong_che,
        "ti_le_token_khong_che": token_khong_che / float(so_token) if so_token else 0.0,
    }


def do_tu_co_dau(tok, van_ban):
    """So sanh chu CO dau va chu KHONG dau trong CUNG mot van ban, CUNG mot tu vung.

    Do tu kem mot khoang trang dang truoc (" " + tu), vi trong van chay that tu
    nao cung di sau mot khoang trang, va ByteLevel coi khoang trang do la mot
    phan cua token. Do tu tran trui se cho con so dep hon thuc te.
    """
    co_dau_n, co_dau_tok, co_dau_bam = 0, 0, 0
    khong_dau_n, khong_dau_tok, khong_dau_bam = 0, 0, 0
    for tu in tach_tu(van_ban):
        n_tok = len(tok.encode(" " + tu, add_special_tokens=False).ids)
        if any(co_dau_tieng_viet(c) for c in tu):
            co_dau_n += 1
            co_dau_tok += n_tok
            if n_tok > 1:
                co_dau_bam += 1
        else:
            khong_dau_n += 1
            khong_dau_tok += n_tok
            if n_tok > 1:
                khong_dau_bam += 1
    return {
        "so_tu_co_dau": co_dau_n,
        "token_tb_tu_co_dau": co_dau_tok / float(co_dau_n) if co_dau_n else 0.0,
        "ti_le_tu_co_dau_bi_bam": co_dau_bam / float(co_dau_n) if co_dau_n else 0.0,
        "so_tu_khong_dau": khong_dau_n,
        "token_tb_tu_khong_dau": khong_dau_tok / float(khong_dau_n) if khong_dau_n else 0.0,
        "ti_le_tu_khong_dau_bi_bam": khong_dau_bam / float(khong_dau_n) if khong_dau_n else 0.0,
    }


def boc_van_ban_tu_tep(duong, toi_da_ky_tu):
    """Doc .jsonl (text / noi_dung / hoi_thoai cua BDSG) hoac .txt thanh mot chuoi."""
    doan = []
    tong = 0
    la_txt = duong.lower().endswith(".txt")
    with open(duong, "r", encoding="utf-8", errors="ignore") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            if la_txt:
                vb = dong
            else:
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
                    vb = "\n".join(str(m.get("noi_dung", "")) for m in d["hoi_thoai"]
                                   if isinstance(m, dict))
                else:
                    continue
            if not vb.strip():
                continue
            doan.append(vb)
            tong += len(vb)
            if toi_da_ky_tu and tong >= toi_da_ky_tu:
                break
    return "\n".join(doan)


def gom_van_ban(args):
    """Tra ve ({nhan: van_ban}, mo_ta_nguon). Uu tien ngu lieu that neu nguoi dung dua."""
    if not args.van_ban:
        return dict((k, "\n".join(v)) for k, v in VAN_BAN_MAU.items()), "van ban mau co san"
    ra = {}
    for s in args.van_ban:
        if "=" not in s:
            raise ValueError("--van-ban phai co dang <nhan>=<duong_dan>")
        nhan, duong = s.split("=", 1)
        duong = os.path.abspath(os.path.expanduser(duong.strip()))
        ra[nhan.strip()] = boc_van_ban_tu_tep(duong, args.toi_da_ky_tu)
    return ra, "ngu lieu that nguoi dung dua"


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Do va so sanh chat luong tokenizer tren tieng Viet va tieng Anh")
    p.add_argument("--bo", action="append", default=[], metavar="TEN=DUONGDAN",
                   help="tu vung can do, lap lai duoc. "
                        "Vi du: --bo bdsg=../../bo-du-lieu/tu-vung-bdsg-v1")
    p.add_argument("--van-ban", action="append", default=[], metavar="NHAN=DUONGDAN",
                   help="do tren ngu lieu that thay vi van ban mau (.jsonl hoac .txt)")
    p.add_argument("--toi-da-ky-tu", type=int, default=2000000,
                   help="doc toi da bao nhieu ky tu moi nhan khi dung --van-ban (mac dinh 2 trieu)")
    p.add_argument("--cua-so", type=int, default=CUA_SO_MAC_DINH,
                   help="cua so ngu canh dung de quy doi ra 'doc duoc bao nhieu chu' "
                        "(mac dinh {})".format(CUA_SO_MAC_DINH))
    p.add_argument("--ra", default=None, help="ghi ket qua ra tep JSON")
    args = p.parse_args(argv)

    if not args.bo:
        p.error("Phai co it nhat mot --bo <ten>=<duong dan tu vung>")

    cac_bo = []
    for s in args.bo:
        if "=" not in s:
            p.error("--bo phai co dang <ten>=<duong_dan>, nhan duoc: {}".format(s))
        ten, duong = s.split("=", 1)
        try:
            tok, duong_that = nap_tokenizer(duong)
        except IOError as e:
            p.error(str(e))
        cac_bo.append((ten.strip(), tok, duong_that))

    try:
        van_ban, nguon_vb = gom_van_ban(args)
    except ValueError as e:
        p.error(str(e))

    print("")
    print("Nguon van ban : {}".format(nguon_vb))
    print("Tu vung do    : " + ", ".join(
        "{} ({:,} tu)".format(t, tok.get_vocab_size()) for t, tok, _ in cac_bo))

    # LUAT 1 o phan dau tep: kich thuoc lech nhau thi phep so khong con cong
    # bang. Canh bao chu KHONG dung chay — doi khi nguoi ta co y so hai kich
    # thuoc khac nhau, chi can ho biet minh dang lam gi.
    cac_kich_thuoc = set(tok.get_vocab_size() for _, tok, _ in cac_bo)
    if len(cac_kich_thuoc) > 1:
        print("")
        print("  !! CANH BAO: cac bo KHONG cung kich thuoc tu vung ({}).".format(
            ", ".join("{:,}".format(k) for k in sorted(cac_kich_thuoc))))
        print("     Tu vung lon hon LUON nen tot hon, bat ke no hoc tieng gi. Moi so")
        print("     chenh lech duoi day deu lan ca hai nguyen nhan, khong tach ra duoc.")
        print("     Muon ket luan ve NGON NGU thi phai do o cung mot kich thuoc.")
    print("")

    ket_qua = {
        "nguon_van_ban": nguon_vb,
        "cua_so_ngu_canh": args.cua_so,
        "cung_kich_thuoc_tu_vung": len(cac_kich_thuoc) == 1,
        "tu_vung": {}, "theo_nhan": {},
    }
    for ten, tok, duong in cac_bo:
        ket_qua["tu_vung"][ten] = {"duong_dan": duong, "so_tu": tok.get_vocab_size()}

    # --- Bang 1: nen ngu canh ---------------------------------------------
    print("=" * 86)
    print("BANG 1 — MOT KY TU TON BAO NHIEU TOKEN  (thap la tot; cot cuoi: token la manh byte)")
    print("=" * 86)
    print("{:<22} {:<16} {:>9} {:>9} {:>9} {:>11}".format(
        "van ban", "tu vung", "ky tu", "token", "tok/kt", "manh byte"))
    print("-" * 86)
    for nhan in sorted(van_ban.keys()):
        vb = van_ban[nhan]
        if not vb.strip():
            continue
        ket_qua["theo_nhan"].setdefault(nhan, {})
        for ten, tok, _ in cac_bo:
            d = do_van_ban(tok, vb)
            ket_qua["theo_nhan"][nhan].setdefault(ten, {}).update(d)
            print("{:<22} {:<16} {:>9,} {:>9,} {:>9.3f} {:>10.1%}".format(
                NHAN.get(nhan, nhan)[:22], ten[:16], d["so_ky_tu"], d["so_token"],
                d["token_tren_ky_tu"], d["ti_le_token_khong_che"]))
        print("-" * 86)

    # --- Bang 2: dau thanh ------------------------------------------------
    print("")
    print("=" * 86)
    print("BANG 2 — DAU THANH LAM TON THEM BAO NHIEU")
    print("=" * 86)
    print("So trong CUNG mot van ban, CUNG mot tu vung: tu co dau va tu khong dau.")
    print("Cot 'gap' > 1 nghia la dau thanh that su lam tu bi bam nho hon.")
    print("")
    print("{:<22} {:<16} {:>9} {:>9} {:>7} {:>12}".format(
        "van ban", "tu vung", "tok/tu+", "tok/tu-", "gap", "%tu+ bi bam"))
    print("-" * 86)
    for nhan in sorted(van_ban.keys()):
        vb = van_ban[nhan]
        if not vb.strip():
            continue
        da_in = False
        for ten, tok, _ in cac_bo:
            d = do_tu_co_dau(tok, vb)
            # Van ban khong co chu nao mang dau tieng Viet thi khong co gi de so.
            if d["so_tu_co_dau"] == 0:
                continue
            ket_qua["theo_nhan"].setdefault(nhan, {}).setdefault(ten, {}).update(d)
            gap = (d["token_tb_tu_co_dau"] / d["token_tb_tu_khong_dau"]
                   if d["token_tb_tu_khong_dau"] else 0.0)
            print("{:<22} {:<16} {:>9.2f} {:>9.2f} {:>7.2f} {:>11.1%}".format(
                NHAN.get(nhan, nhan)[:22], ten[:16],
                d["token_tb_tu_co_dau"], d["token_tb_tu_khong_dau"], gap,
                d["ti_le_tu_co_dau_bi_bam"]))
            da_in = True
        if da_in:
            print("-" * 86)
    print("tok/tu+ = so token trung binh cho mot tu CO dau")
    print("tok/tu- = so token trung binh cho mot tu KHONG dau, trong cung van ban do")
    print("(chi in cac van ban that su co tu mang dau tieng Viet)")

    # --- Ket luan: MAY TINH RA, khong phai nguoi viet san ------------------
    print("")
    print("=" * 86)
    print("DOC RA SAO")
    print("=" * 86)
    tn = ket_qua["theo_nhan"]
    if "vi_co_dau" in tn:
        muc = tn["vi_co_dau"]
        xep = sorted(muc.items(), key=lambda kv: kv[1].get("token_tren_ky_tu", 9e9))
        print("Tren tieng Viet CO dau:")
        for ten, d in xep:
            print("  {:<16} {:.3f} token moi ky tu   ({:.2f} ky tu moi token)".format(
                ten, d["token_tren_ky_tu"], d["ky_tu_tren_token"]))
        if len(xep) >= 2:
            tot, te = xep[0], xep[-1]
            ti = te[1]["token_tren_ky_tu"] / tot[1]["token_tren_ky_tu"]
            print("")
            print("  '{}' ton gap {:.2f} lan '{}' cho cung mot doan van.".format(
                te[0], ti, tot[0]))
            print("  Voi cua so ngu canh {:,} token: {:,} vs {:,} ky tu lot vao duoc.".format(
                args.cua_so,
                int(args.cua_so / te[1]["token_tren_ky_tu"]),
                int(args.cua_so / tot[1]["token_tren_ky_tu"])))
            if not ket_qua["cung_kich_thuoc_tu_vung"]:
                print("  (nhac lai: cac bo KHONG cung kich thuoc, nen ti so nay khong")
                print("   quy duoc cho rieng chuyen hoc ngon ngu nao)")
        else:
            print("  (chi co mot tu vung — them --bo thu hai de so sanh cheo)")

        # Doi chung NOI BO: cung tu vung, cung noi dung, chi khac dau thanh.
        # Phep nay khong can tu vung thu hai, va la phep kho cai nhat.
        if "vi_khong_dau" in tn:
            print("")
            print("Cung mot tu vung, cung noi dung, CHI KHAC dau thanh:")
            for ten, d in xep:
                dk = tn["vi_khong_dau"].get(ten, {}).get("token_tren_ky_tu")
                if dk:
                    print("  {:<16} co dau {:.3f} vs khong dau {:.3f}  ->  dau thanh lam "
                          "moi ky tu ton gap {:.2f} lan".format(
                              ten, d["token_tren_ky_tu"], dk,
                              d["token_tren_ky_tu"] / dk))

        # Thien vi ngon ngu, trong CUNG mot tu vung.
        if "en" in tn:
            print("")
            print("Cung mot tu vung, tieng Viet co dau so voi tieng Anh:")
            for ten, d in xep:
                den = tn["en"].get(ten, {}).get("token_tren_ky_tu")
                if den:
                    print("  {:<16} vi {:.3f} vs en {:.3f}  ->  moi ky tu tieng Viet ton "
                          "gap {:.2f} lan mot ky tu tieng Anh".format(
                              ten, d["token_tren_ky_tu"], den,
                              d["token_tren_ky_tu"] / den))
    else:
        print("Khong co van ban tieng Viet co dau trong tap do nen khong ket luan gi.")
        print("Dat nhan 'vi_co_dau' cho --van-ban neu muon phan nay chay.")
    print("")
    print("LUU Y: day la phep do NEN NGU CANH, khong phai phep do chat luong mo hinh.")
    print("Tu vung nen tot la dieu kien CAN, khong phai dieu kien DU.")

    if args.ra:
        with open(os.path.abspath(os.path.expanduser(args.ra)), "w", encoding="utf-8") as f:
            json.dump(ket_qua, f, ensure_ascii=False, indent=2)
        print("")
        print("Da ghi ket qua ra: {}".format(args.ra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
