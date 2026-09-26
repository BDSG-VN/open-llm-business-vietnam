#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sinh_ngu_lieu.py — SINH ngữ liệu học thuật bằng mô hình, bám khung GDPT 2018.

=============================================================================
BỐN LUẬT, và mỗi luật vì một lý do đã trả giá
=============================================================================
1. VIẾT MỚI, KHÔNG CHÉP SÁCH. Lời nhắc CẤM tái tạo văn bản sách giáo khoa.
   Sách giáo khoa có bản quyền; chép vào ngữ liệu rồi phát hành mô hình mở là
   vi phạm và không có cách lách. Khung (Thông tư 32/2018) thì công khai —
   viết mới bám khung là hợp pháp, và đó đúng là cách phi-1 đã làm.

2. GHI XUẤT XỨ CHO TỪNG ĐOẠN. Mỗi bản ghi mang: mô hình nào sinh, lúc nào,
   từ lời nhắc nào (băm). Bất biến số 6 của dự án đòi giữ và nâng cấp xuất xứ.
   Thiếu nó thì sáu tháng sau không ai trả lời được "đoạn này ở đâu ra".

3. GẮN NHÃN AI. `do_ai_sinh = True` đi theo bản ghi tới tận nơi dùng. Bất biến
   số 3: suy luận của AI không được giả làm dữ liệu đã xác minh.

4. CỔNG CHỦ QUYỀN CHẠY TRƯỚC KHI GHI, KHÔNG PHẢI SAU. Với môn mang cờ
   `chuan_vn`, đoạn nào chứa chuỗi cấm thì BỊ TỪ CHỐI ngay, không vào tệp.
   Lọc sau là lọc có thể quên, và một câu sai chủ quyền lọt vào bộ huấn luyện
   thì nó ở trong trọng số, không gỡ ra được.

=============================================================================
CHẠY LẠI ĐƯỢC
=============================================================================
3 tỷ token là việc nhiều ngày. Bộ sinh ghi JSONL và BỎ QUA lát đã xong, nên
đứt giữa chừng thì chạy lại tiếp đúng chỗ. Không có tính ấy thì mỗi lần mạng
rớt là mất toàn bộ công.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from khung import CAP_HOC, MON, mon_cua_cap  # noqa: E402

# Chuỗi cấm — ghép từ mảnh để chính tệp này không chứa chúng nguyên văn.
# Cùng kỹ thuật với cong/khong-tham-chieu-ngoai.py và scripts/kiem-tra/chu-quyen.mjs.
_CAM = [
    "tam" + "·" + "sa", "san" + "·" + "sha", "nine" + "·" + "dash",
    "duong luoi bo", "đường lưỡi bò",
]
def _mau_tu_manh(cum: str) -> str:
    """Ghép các mảnh của một chuỗi cấm, CHO PHÉP ký tự nối ở giữa.

    Lỗi đã dính 26/09/2026: bản đầu bỏ dấu phân cách rồi ghép LIỀN, nên mẫu ra
    "ninedash" và KHÔNG bắt được "nine-dash" hay "nine dash". Một bộ dò chỉ bắt
    đúng một cách viết là bộ dò gần như vô dụng — người viết ra chuỗi ấy không
    có nghĩa vụ viết liền giúp mình.
    """
    manh = [x for x in re.split(r"[\u00b7\s\-_]+", cum) if x]
    return r"[\s\-_.]{0,2}".join(re.escape(x) for x in manh)


MAU_CAM = re.compile("|".join(_mau_tu_manh(c) for c in _CAM), re.IGNORECASE)
# Với môn Địa lí / Lịch sử, nhắc tới biển đảo mà THIẾU hai quần đảo là thiếu sót
# phải biết, nên ghi nhận riêng chứ không chặn.
MAU_BIEN = re.compile(r"biển Đông|quần đảo", re.IGNORECASE)
MAU_HS = re.compile(r"Hoàng Sa", re.IGNORECASE)
MAU_TS = re.compile(r"Trường Sa", re.IGNORECASE)


class LoiSinh(RuntimeError):
    pass


SO_BAI_MOI_MON = 70   # một năm học thật ~70 bài mỗi môn


def lat_can_sinh(chi_cap: Optional[str] = None,
                 so_bai: int = SO_BAI_MOI_MON) -> Iterator[Dict[str, Any]]:
    """Liệt kê từng LÁT: một (môn, lớp, BÀI SỐ N) là một lát.

    CHIỀU 'bài số N' thêm 26/09/2026 sau mẻ thử đầu. Bản trước coi mỗi (môn,
    lớp) là MỘT bài, nên cả khung chỉ ra 142 bài = 226.490 token — quá thô để
    gọi là một chương trình học. Một năm học thật có khoảng 70 bài mỗi môn.

    Số đo từ mẻ thử: 1.595 token/bài, 211 token/giây, $0,383/triệu token. Với
    chiều này, phổ thông ra ~15,9 triệu token và tốn khoảng 6 USD.
    """
    for cap in CAP_HOC:
        if chi_cap and cap["ma"] != chi_cap:
            continue
        lop_ds = cap["lop"] or (0,)
        for mon in mon_cua_cap(cap["ma"]):
            for lop in lop_ds:
                for bai in range(1, so_bai + 1):
                    yield {
                        "ma_lat": "%s|%s|%d|b%03d" % (cap["ma"], mon["ma"], lop, bai),
                        "cap": cap["ma"], "cap_ten": cap["ten"],
                        "mon": mon["ma"], "mon_ten": mon["ten"],
                        "lop": lop, "bai": bai, "so_bai": so_bai,
                        "chuan_vn": mon["chuan_vn"],
                    }


LOI_NHAC = """Bạn là người viết học liệu cho chương trình giáo dục phổ thông Việt Nam.

Viết một bài học NGUYÊN BẢN cho:
  Cấp: {cap_ten}
  Môn: {mon_ten}
  {lop_cau}
  Bài số {bai} trong tổng số {so_bai} bài của năm học.
  Chọn chủ đề HỢP LÝ cho vị trí này trong năm: bài đầu năm là kiến thức nền,
  bài cuối năm là kiến thức nâng cao hoặc ôn tập. KHÔNG lặp chủ đề của bài khác.

RÀNG BUỘC BẮT BUỘC:
1. VIẾT MỚI hoàn toàn. TUYỆT ĐỐI không tái tạo, không trích, không diễn đạt lại
   văn bản của bất kỳ bộ sách giáo khoa nào. Bám theo yêu cầu cần đạt của
   Chương trình GDPT 2018, nhưng câu chữ phải là của bạn.
2. Đúng chuẩn Việt Nam: thuật ngữ, ký hiệu toán học, cách gọi tên địa danh,
   cách trình bày lịch sử theo quan điểm chính thống của Việt Nam.
3. Nếu có nhắc tới địa lý hành chính: Việt Nam có 34 tỉnh, thành phố trực thuộc
   trung ương theo Nghị quyết 202/2025/QH15.
4. Nếu có nhắc tới biển đảo: Quần đảo Hoàng Sa thuộc thành phố Đà Nẵng, Quần đảo
   Trường Sa thuộc tỉnh Khánh Hòa, đều là lãnh thổ Việt Nam.
5. Văn phong: rõ, ngắn, đúng lứa tuổi. Có ví dụ cụ thể. Không lan man.
6. Độ dài khoảng {so_tu} từ.

Viết thẳng bài học, không mở đầu bằng lời dẫn."""


def _goi_mo_hinh(goc: str, khoa: str, mo_hinh: str, loi_nhac: str,
                 tran_token: int, het_gio: int = 180) -> Dict[str, Any]:
    body = json.dumps({
        "model": mo_hinh,
        "messages": [{"role": "user", "content": loi_nhac}],
        "max_tokens": tran_token, "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(
        goc.rstrip("/") + "/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + khoa, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=het_gio) as r:
        return json.loads(r.read().decode())


def kiem_chu_quyen(van_ban: str, chuan_vn: bool) -> Dict[str, Any]:
    """Chạy TRƯỚC khi ghi. `dat=False` thì đoạn ấy KHÔNG vào tệp."""
    pham = MAU_CAM.findall(van_ban or "")
    kq = {"dat": not pham, "chuoi_cam": sorted(set(x.lower() for x in pham))}
    if chuan_vn and MAU_BIEN.search(van_ban or ""):
        kq["nhac_bien_dao"] = True
        kq["co_hoang_sa"] = bool(MAU_HS.search(van_ban))
        kq["co_truong_sa"] = bool(MAU_TS.search(van_ban))
    return kq


def sinh_song_song(goc: str, khoa: str, mo_hinh: str, duong_ra: str,
                   so_luong: int = 10, gioi_han: Optional[int] = None,
                   chi_cap: Optional[str] = None, so_tu: int = 900,
                   tran_token: int = 2000, so_bai: int = SO_BAI_MOI_MON,
                   in_moi: int = 50) -> Dict[str, Any]:
    """Sinh bằng NHIỀU LUỒNG. Một luồng mất ~21 giờ cho riêng phần phổ thông.

    BA ĐIỀU PHẢI ĐÚNG, và mỗi điều là một cách hỏng đã lường trước:

    1. MỘT LUỒNG GHI, NHIỀU LUỒNG GỌI. Nhiều luồng cùng ghi vào một tệp thì
       dòng của chúng cài răng lược vào nhau và tệp JSONL hỏng ở những chỗ
       ngẫu nhiên — hỏng theo kiểu chỉ phát hiện ra lúc nạp, sau hàng giờ.
       Nên: các luồng gọi mô hình, kết quả về một hàng đợi, MỘT luồng ghi.

    2. ĐỌC LÁT ĐÃ XONG TRƯỚC KHI BẮT ĐẦU. Chạy lại phải bỏ qua đúng chỗ cũ.

    3. LỖI MỘT LÁT KHÔNG ĐƯỢC GIẾT CẢ MẺ. Một lát hỏng thì đếm rồi đi tiếp;
       hết mẻ mới báo tổng. Dừng cả mẻ vì một lần mạng chập là mất hàng giờ.
    """
    import queue
    import threading

    da_xong = set()
    if os.path.exists(duong_ra):
        with open(duong_ra, encoding="utf-8") as f:
            for d in f:
                try:
                    da_xong.add(json.loads(d)["ma_lat"])
                except Exception:
                    pass

    can = [l for l in lat_can_sinh(chi_cap, so_bai) if l["ma_lat"] not in da_xong]
    if gioi_han is not None:
        can = can[:gioi_han]
    print("  đã có %d lát · còn phải sinh %d lát · %d luồng"
          % (len(da_xong), len(can), so_luong), flush=True)
    if not can:
        return {"lat_moi": 0, "bo_qua": len(da_xong), "ghi_chu": "không còn lát nào"}

    viec = queue.Queue()
    for l in can:
        viec.put(l)
    ket = queue.Queue()
    tk = {"lat_moi": 0, "bo_qua": len(da_xong), "tu_choi_chu_quyen": 0, "loi": 0,
          "token_ra": 0, "token_vao": 0, "thieu_quan_dao": 0}
    khoa_dem = threading.Lock()
    t_tong = time.time()

    def tho():
        while True:
            try:
                lat = viec.get_nowait()
            except queue.Empty:
                return
            ln = LOI_NHAC.format(
                cap_ten=lat["cap_ten"], mon_ten=lat["mon_ten"], so_tu=so_tu,
                bai=lat["bai"], so_bai=lat["so_bai"],
                lop_cau=("Lớp: %d" % lat["lop"]) if lat["lop"] else "Lứa tuổi: mẫu giáo")
            try:
                d = _goi_mo_hinh(goc, khoa, mo_hinh, ln, tran_token)
            except Exception as loi:
                with khoa_dem:
                    tk["loi"] += 1
                continue
            van = (d["choices"][0]["message"]["content"] or "").strip()
            dung = d.get("usage") or {}
            cq = kiem_chu_quyen(van, lat["chuan_vn"])
            if not cq["dat"]:
                with khoa_dem:
                    tk["tu_choi_chu_quyen"] += 1
                print("  [TỪ CHỐI] %s — %s" % (lat["ma_lat"], cq["chuoi_cam"]), flush=True)
                continue
            if cq.get("nhac_bien_dao") and not (cq.get("co_hoang_sa") and cq.get("co_truong_sa")):
                with khoa_dem:
                    tk["thieu_quan_dao"] += 1
            ket.put({
                "ma_lat": lat["ma_lat"], "cap": lat["cap"], "mon": lat["mon"],
                "mon_ten": lat["mon_ten"], "lop": lat["lop"], "bai": lat["bai"],
                "chuan_vn": lat["chuan_vn"], "van_ban": van,
                "do_ai_sinh": True, "mo_hinh": d.get("model") or mo_hinh,
                "luc": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime()),
                "bam_loi_nhac": hashlib.blake2b(ln.encode(), digest_size=8).hexdigest(),
                "kiem_chu_quyen": cq,
                "token_ra": dung.get("completion_tokens"),
                "_vao": dung.get("prompt_tokens") or 0,
            })

    def ghi():
        with open(duong_ra, "a", encoding="utf-8") as ra:
            while True:
                r = ket.get()
                if r is None:
                    return
                vao = r.pop("_vao", 0)
                ra.write(json.dumps(r, ensure_ascii=False) + "\n")
                ra.flush()
                with khoa_dem:
                    tk["lat_moi"] += 1
                    tk["token_ra"] += r.get("token_ra") or 0
                    tk["token_vao"] += vao
                    n = tk["lat_moi"]
                if n % in_moi == 0:
                    g = time.time() - t_tong
                    con = (len(can) - n) / max(n / g, 1e-9)
                    print("  [%5d/%d] %s · %.0f bài/phút · còn ~%.0f phút"
                          % (n, len(can), r["ma_lat"], n / g * 60, con / 60), flush=True)

    t_ghi = threading.Thread(target=ghi, daemon=True)
    t_ghi.start()
    tho_ds = [threading.Thread(target=tho, daemon=True) for _ in range(so_luong)]
    for t in tho_ds:
        t.start()
    for t in tho_ds:
        t.join()
    ket.put(None)
    t_ghi.join()

    tk["tong_giay"] = time.time() - t_tong
    tk["bai_moi_phut"] = tk["lat_moi"] / max(tk["tong_giay"], 1e-9) * 60
    return tk


def sinh(goc: str, khoa: str, mo_hinh: str, duong_ra: str,
         gioi_han: Optional[int] = None, chi_cap: Optional[str] = None,
         so_tu: int = 900, tran_token: int = 2000,
         so_bai: int = SO_BAI_MOI_MON) -> Dict[str, Any]:
    da_xong = set()
    if os.path.exists(duong_ra):
        with open(duong_ra, encoding="utf-8") as f:
            for d in f:
                try:
                    da_xong.add(json.loads(d)["ma_lat"])
                except Exception:
                    pass

    tk = {"lat_moi": 0, "bo_qua": 0, "tu_choi_chu_quyen": 0, "loi": 0,
          "token_ra": 0, "token_vao": 0, "giay": 0.0, "thieu_quan_dao": 0}
    t_tong = time.time()

    with open(duong_ra, "a", encoding="utf-8") as ra:
        for lat in lat_can_sinh(chi_cap, so_bai):
            if gioi_han is not None and tk["lat_moi"] >= gioi_han:
                break
            if lat["ma_lat"] in da_xong:
                tk["bo_qua"] += 1
                continue
            ln = LOI_NHAC.format(
                cap_ten=lat["cap_ten"], mon_ten=lat["mon_ten"], so_tu=so_tu,
                bai=lat["bai"], so_bai=lat["so_bai"],
                lop_cau=("Lớp: %d" % lat["lop"]) if lat["lop"] else "Lứa tuổi: mẫu giáo")
            t0 = time.time()
            try:
                d = _goi_mo_hinh(goc, khoa, mo_hinh, ln, tran_token)
            except Exception as loi:
                tk["loi"] += 1
                print("  [LỖI] %s — %s: %s" % (lat["ma_lat"], type(loi).__name__, str(loi)[:120]))
                continue
            giay = time.time() - t0
            van = (d["choices"][0]["message"]["content"] or "").strip()
            dung = d.get("usage") or {}

            cq = kiem_chu_quyen(van, lat["chuan_vn"])
            if not cq["dat"]:
                tk["tu_choi_chu_quyen"] += 1
                print("  [TỪ CHỐI] %s — chuỗi cấm: %s" % (lat["ma_lat"], cq["chuoi_cam"]))
                continue
            if cq.get("nhac_bien_dao") and not (cq.get("co_hoang_sa") and cq.get("co_truong_sa")):
                tk["thieu_quan_dao"] += 1

            ra.write(json.dumps({
                "ma_lat": lat["ma_lat"], "cap": lat["cap"], "mon": lat["mon"],
                "mon_ten": lat["mon_ten"], "lop": lat["lop"], "bai": lat["bai"],
                "chuan_vn": lat["chuan_vn"],
                "van_ban": van,
                # --- xuất xứ: bất biến 6 ---
                "do_ai_sinh": True,
                "mo_hinh": d.get("model") or mo_hinh,
                "luc": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime()),
                "bam_loi_nhac": hashlib.blake2b(ln.encode(), digest_size=8).hexdigest(),
                "kiem_chu_quyen": cq,
                "token_ra": dung.get("completion_tokens"),
            }, ensure_ascii=False) + "\n")
            ra.flush()
            tk["lat_moi"] += 1
            tk["token_ra"] += dung.get("completion_tokens") or 0
            tk["token_vao"] += dung.get("prompt_tokens") or 0
            tk["giay"] += giay
            print("  [%3d] %-34s %5d token · %5.1fs" %
                  (tk["lat_moi"], lat["ma_lat"], dung.get("completion_tokens") or 0, giay))

    tk["tong_giay"] = time.time() - t_tong
    return tk


def tong_so_lat(chi_cap: Optional[str] = None, so_bai: int = SO_BAI_MOI_MON) -> int:
    return sum(1 for _ in lat_can_sinh(chi_cap, so_bai))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--goc", default=os.environ.get("LITELLM_BASE", "http://127.0.0.1:4000"))
    p.add_argument("--khoa", default=os.environ.get("LITELLM_KEY", ""))
    p.add_argument("--mo-hinh", default="bdsg-fast")
    p.add_argument("--ra", required=True)
    p.add_argument("--gioi-han", type=int, default=None)
    p.add_argument("--cap", default=None)
    p.add_argument("--so-tu", type=int, default=900)
    p.add_argument("--so-bai", type=int, default=SO_BAI_MOI_MON)
    p.add_argument("--luong", type=int, default=1, help="số luồng song song")
    a = p.parse_args()
    if not a.khoa:
        raise SystemExit("Thiếu --khoa (hoặc LITELLM_KEY). KHÔNG ghi khoá vào mã.")
    print("  tổng số lát trong khung: %d" % tong_so_lat(a.cap, a.so_bai))
    if a.luong > 1:
        tk = sinh_song_song(a.goc, a.khoa, a.mo_hinh, a.ra, so_luong=a.luong,
                            gioi_han=a.gioi_han, chi_cap=a.cap, so_tu=a.so_tu,
                            so_bai=a.so_bai)
    else:
        tk = sinh(a.goc, a.khoa, a.mo_hinh, a.ra, a.gioi_han, a.cap, a.so_tu,
                  so_bai=a.so_bai)
    print("")
    print("  ── KẾT QUẢ ──")
    for k, v in tk.items():
        print("    %-22s %s" % (k, v))
