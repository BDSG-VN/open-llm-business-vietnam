#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài tự kiểm cho máy chủ chat nội bộ và kho hội thoại.

CHẠY:
    .venv/bin/python3 phuc-vu/thu_may_chu.py

KHÔNG cần GPU. KHÔNG cần mô hình. KHÔNG cần mạng. Cổng mô hình ở đây là một bản
GIẢ chạy trong cùng tiến trình; máy chủ thật được dựng trên 127.0.0.1 với cổng 0
(hệ điều hành tự cấp một cổng trống) và bị gọi qua HTTP thật.

═══ VÌ SAO GỌI QUA HTTP THẬT CHỨ KHÔNG GỌI THẲNG HÀM ═══

Phần lớn thứ có thể hỏng ở tệp này nằm Ở GIỮA: thứ tự sự kiện SSE, khung `data:`
có đúng một dòng không, mã 404 có thật sự là 404 không, kết nối có đóng đúng lúc
không. Gọi thẳng hàm Python thì không phép nào trong số đó được kiểm — bài kiểm
sẽ ĐẠT trong khi giao diện thật vẫn hỏng.

═══ VÌ SAO CHẠY MÁY CHỦ TRONG MỘT LUỒNG, KHÔNG PHẢI MỘT TIẾN TRÌNH CON ═══

Tiến trình con buộc bài kiểm phải sinh lệnh hệ thống, phải chờ máy chủ lên bằng
cách ngủ một khoảng đoán mò, và làm mất luôn khả năng NHÌN vào đối tượng cổng giả
sau khi chạy (phép kiểm "cổng mô hình bị gọi đúng MỘT lần" dựa vào đúng chỗ đó).
Một luồng trong cùng tiến trình cho cả hai thứ: HTTP thật, và quan sát được bên
trong.

TRẠNG THÁI SỐ LIỆU (26/09/2026): mọi phép ở đây chạy với cổng mô hình GIẢ. Chưa
có phép đo nào về độ trễ, số yêu cầu đồng thời, hay chất lượng câu trả lời — và
bài này không nói gì về những thứ đó.
"""

from __future__ import annotations

import ast
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import traceback
import uuid
from typing import Any, Dict, List, Optional, Tuple

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

import kho_hoi_thoai  # noqa: E402
import may_chu  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# Khung chạy thử tối giản (không dùng pytest, để bài này chạy được ở mọi nơi)
# ──────────────────────────────────────────────────────────────────────────────

_KET_QUA: List[Tuple[str, bool, str]] = []


def phep_kiem(ten: str):
    def bao(ham):
        def chay():
            try:
                ghi_chu = ham()
                _KET_QUA.append((ten, True, ghi_chu or ""))
                print("  DAT   {}{}".format(ten, "  — " + ghi_chu if ghi_chu else ""))
                return True
            except AssertionError as loi:
                _KET_QUA.append((ten, False, str(loi)))
                print("  HONG  {}  — {}".format(ten, loi))
                return False
            except Exception as loi:  # noqa: BLE001
                vet = traceback.format_exc(limit=3).strip().splitlines()[-1]
                _KET_QUA.append((ten, False, "{}: {}".format(type(loi).__name__, loi)))
                print("  HONG  {}  — {}: {}".format(ten, type(loi).__name__, loi))
                print("        {}".format(vet))
                return False

        chay.__name__ = ham.__name__
        return chay

    return bao


def bao_dam(dieu_kien: Any, cau: str) -> None:
    if not dieu_kien:
        raise AssertionError(cau)


# ──────────────────────────────────────────────────────────────────────────────
# Cổng mô hình GIẢ
# ──────────────────────────────────────────────────────────────────────────────


class LoiGiaKhongNoiDuoc(RuntimeError):
    """Lớp lỗi RIÊNG của cổng giả.

    Cố ý KHÔNG kế thừa lớp cùng tên trong `may_chu`: máy chủ phải bắt lớp mà CHÍNH
    cổng mô hình khai ra. Nếu ngày nào đó máy chủ đổi sang bắt lớp của riêng nó
    thì cổng thật (một mô-đun độc lập, lớp lỗi độc lập) sẽ không được bắt nữa, và
    người dùng nhận một vết lỗi thay vì một câu tiếng Việt. Phép kiểm "backend
    mất kết nối" bên dưới sẽ HỎNG ngay nếu điều đó xảy ra.
    """


class CongGia:
    """Cổng mô hình giả: sinh sẵn một dãy mẩu chữ, đếm số lần bị gọi."""

    LoiKhongNoiDuocMayNoiBo = LoiGiaKhongNoiDuoc

    def __init__(
        self,
        cac_mau: Optional[List[str]] = None,
        mo_hinh_that: Optional[str] = None,
        dut_sau: Optional[int] = None,
        trich_dan: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.cac_mau = cac_mau if cac_mau is not None else ["Xin ", "chào ", "BDSG."]
        self.mo_hinh_that = mo_hinh_that
        self.dut_sau = dut_sau          # ném lỗi sau khi đã sinh N mẩu
        self.trich_dan = trich_dan
        self.cac_lan_goi: List[Dict[str, Any]] = []

    def hoi_dong_chay(
        self,
        tin_nhan,
        nhiet: float = 0.7,
        tran_token_ra: Optional[int] = None,
        thu_thap: Optional[Dict[str, Any]] = None,
    ):
        """Cùng chữ ký với `cong_mo_hinh.CongMoHinh.hoi_dong_chay`.

        Cố ý sao đúng chữ ký của cổng THẬT, kể cả các tham số bài này không dùng
        tới. Một bản giả có chữ ký dễ dãi hơn bản thật sẽ ĐẠT ở đây rồi hỏng khi
        nối vào cổng thật — tức là bài kiểm nói dối đúng chỗ nó có nhiệm vụ nói
        thật.
        """
        if thu_thap is None:
            thu_thap = {}
        self.cac_lan_goi.append(
            {
                "tin_nhan": [dict(t) for t in tin_nhan],
                "nhiet": nhiet,
                "tran_token_ra": tran_token_ra,
            }
        )
        return self._sinh(thu_thap)

    def _sinh(self, thu_thap: Dict[str, Any]):
        thu_thap["so_mau"] = 0
        try:
            for chi_so, mau in enumerate(self.cac_mau):
                if self.dut_sau is not None and chi_so >= self.dut_sau:
                    raise LoiGiaKhongNoiDuoc("may phuc vu noi bo dut giua chung (gia lap)")
                thu_thap["so_mau"] = int(thu_thap["so_mau"]) + 1
                yield mau
            if self.dut_sau is not None:
                raise LoiGiaKhongNoiDuoc("may phuc vu noi bo dut giua chung (gia lap)")
        finally:
            # Điền trong `finally`, đúng như cổng thật: tên mô hình phải lấy được
            # CẢ KHI dòng chảy đứt giữa chừng.
            if self.mo_hinh_that is not None:
                thu_thap["mo_hinh_that"] = self.mo_hinh_that
            if self.trich_dan is not None:
                thu_thap["trich_dan"] = self.trich_dan


# ──────────────────────────────────────────────────────────────────────────────
# Dựng máy chủ thử
# ──────────────────────────────────────────────────────────────────────────────


class MayChuThu:
    """Máy chủ thật trên 127.0.0.1, cổng do hệ điều hành cấp, chạy trong một luồng."""

    def __init__(self, cong_gia: Any = None, nguoi: str = "demo") -> None:
        self.thu_muc = tempfile.mkdtemp(prefix="bdsg-thu-chat-")
        self.kho = kho_hoi_thoai.KhoHoiThoai(os.path.join(self.thu_muc, "hoi-thoai.db"))
        self.cong_gia = cong_gia
        self.nguoi = nguoi
        self.may_chu = None
        self.luong = None

    def __enter__(self) -> "MayChuThu":
        self.may_chu = may_chu.tao_may_chu(
            dia_chi="127.0.0.1",
            cong=0,
            kho=self.kho,
            cong_mo_hinh=self.cong_gia,
            # Khai tường minh: bài kiểm KHÔNG được đọc biến môi trường của máy
            # đang chạy, nếu không kết quả đổi theo từng máy.
            cau_hinh_ngoai=None,
            nguoi_demo=self.nguoi,
            thu_muc_giao_dien=os.path.join(may_chu.GOC_KHO, "chat"),
        )
        self.cong = self.may_chu.server_address[1]
        self.luong = threading.Thread(target=self.may_chu.serve_forever, daemon=True)
        self.luong.start()
        return self

    def __exit__(self, *bo_qua) -> None:
        if self.may_chu is not None:
            self.may_chu.shutdown()
            self.may_chu.server_close()
        if self.luong is not None:
            self.luong.join(timeout=5)
        shutil.rmtree(self.thu_muc, ignore_errors=True)

    # -- gọi HTTP --------------------------------------------------------------

    def goi(
        self, phuong_thuc: str, duong: str, than: Any = None
    ) -> Tuple[int, Dict[str, str], str]:
        ket_noi = http.client.HTTPConnection("127.0.0.1", self.cong, timeout=15)
        try:
            dau = {}
            du_lieu = None
            if than is not None:
                du_lieu = json.dumps(than, ensure_ascii=False).encode("utf-8")
                dau["Content-Type"] = "application/json"
            ket_noi.request(phuong_thuc, duong, body=du_lieu, headers=dau)
            phan_hoi = ket_noi.getresponse()
            tho = phan_hoi.read().decode("utf-8", errors="replace")
            return phan_hoi.status, dict(phan_hoi.getheaders()), tho
        finally:
            ket_noi.close()

    def json(self, phuong_thuc: str, duong: str, than: Any = None) -> Tuple[int, Any]:
        ma, _, tho = self.goi(phuong_thuc, duong, than)
        try:
            return ma, json.loads(tho)
        except ValueError:
            return ma, None

    def hoi(self, noi_dung: str, hoi_thoai_id=None, muc="nhanh"):
        """POST /api/hoi, trả (mã HTTP, các sự kiện SSE đã phân tích)."""
        ma, dau, tho = self.goi(
            "POST",
            "/api/hoi",
            {"hoiThoaiId": hoi_thoai_id, "noiDung": noi_dung, "mucNoLuc": muc},
        )
        return ma, dau, phan_tich_sse(tho)


def phan_tich_sse(tho: str) -> List[Tuple[str, Any]]:
    """Phân tích dòng SSE thành [(tên sự kiện, dữ liệu đã giải mã JSON)].

    Viết lại đúng cách giao diện đọc (`docSSE` trong chat/chat.js): khung phân
    cách bằng một dòng trống, `event:` và `data:` đọc theo tiền tố. Nếu máy chủ
    phát ra khung sai khuôn thì phép phân tích này vỡ ở đây — đúng như giao diện
    sẽ vỡ ở đó.
    """
    cac: List[Tuple[str, Any]] = []
    for khung in tho.split("\n\n"):
        if khung.strip() == "":
            continue
        loai = "message"
        du = ""
        for dong in khung.split("\n"):
            if dong.startswith("event:"):
                loai = dong[6:].strip()
            elif dong.startswith("data:"):
                du += dong[5:].strip()
        if du == "":
            continue
        cac.append((loai, json.loads(du)))
    return cac


# ──────────────────────────────────────────────────────────────────────────────
# 1. GET /api/mo-hinh
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("1. GET /api/mo-hinh tra du truong hop dong")
def thu_mo_hinh_du_truong():
    with MayChuThu(CongGia()) as m:
        ma, d = m.json("GET", "/api/mo-hinh")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        for truong in ("moHinh", "mucNoLuc", "mucNoLucMacDinh", "danhSach"):
            bao_dam(truong in d, "thieu truong bat buoc '{}'".format(truong))
        for truong in ("ma", "ten", "moTa"):
            bao_dam(truong in d["moHinh"], "moHinh thieu '{}'".format(truong))
        bao_dam(isinstance(d["danhSach"], list) and d["danhSach"],
                "danhSach phai la danh sach khong rong")
        for muc in d["danhSach"]:
            for truong in ("ma", "ten", "moTa", "suyLuan"):
                bao_dam(truong in muc, "muc danhSach thieu '{}'".format(truong))
        bao_dam(isinstance(d["mucNoLuc"], list) and d["mucNoLuc"], "mucNoLuc rong")
        cac_muc = [k["muc"] for k in d["mucNoLuc"]]
        bao_dam(d["mucNoLucMacDinh"] in cac_muc,
                "mucNoLucMacDinh khong nam trong mucNoLuc")
        # Giao diện đổi mã trong `moHinhThat` thành tên qua danhSach. Mã trọng số
        # nền PHẢI có mặt, nếu không nhãn "câu trả lời đến từ ..." hiện mã trần.
        cac_ma = [k["ma"] for k in d["danhSach"]]
        bao_dam(d["nen"]["maTrongSo"] in cac_ma,
                "danhSach thieu ma trong so nen '{}'".format(d["nen"]["maTrongSo"]))
        return "{} muc mo hinh, {} muc no luc".format(len(d["danhSach"]), len(cac_muc))


@phep_kiem("2. bdsg_la_trong_so_bdsg == False cho trong so Google nguyen ban")
def thu_khong_nhan_vo_trong_so():
    with MayChuThu(CongGia()) as m:
        ma, d = m.json("GET", "/api/mo-hinh")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        bao_dam("bdsg_la_trong_so_bdsg" in d, "thieu truong bdsg_la_trong_so_bdsg")
        bao_dam(d["bdsg_la_trong_so_bdsg"] is False,
                "bdsg_la_trong_so_bdsg phai la False, nhan {!r}".format(
                    d["bdsg_la_trong_so_bdsg"]))
        nen = d.get("nen") or {}
        bao_dam(nen.get("nhaCungCap") == "Google",
                "khoi 'nen' phai ghi cong Google, nhan {!r}".format(nen.get("nhaCungCap")))
        bao_dam(nen.get("giayPhep") == "Apache-2.0",
                "giay phep trong so phai la Apache-2.0, nhan {!r}".format(nen.get("giayPhep")))
        bao_dam(nen.get("lienKet"), "thieu lien ket toi trang trong so")
        return "nen = {} / {}".format(nen.get("nhaCungCap"), nen.get("maTrongSo"))


# ──────────────────────────────────────────────────────────────────────────────
# 3. POST /api/hoi — thứ tự sự kiện
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("3. POST /api/hoi phat du va DUNG THU TU: batdau, chu..., xong")
def thu_thu_tu_su_kien():
    cong = CongGia(cac_mau=["Mot ", "hai ", "ba."], mo_hinh_that="google/gemma-4-31B-it")
    with MayChuThu(cong) as m:
        ma, dau, cac = m.hoi("Xin chao")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        kieu = (dau.get("Content-Type") or "").lower()
        bao_dam("text/event-stream" in kieu, "Content-Type sai: {!r}".format(kieu))
        ten = [t for t, _ in cac]
        bao_dam(len(ten) >= 3, "qua it su kien: {}".format(ten))
        bao_dam(ten[0] == "batdau", "su kien dau phai la batdau, nhan {!r}".format(ten[0]))
        bao_dam(ten[-1] == "xong", "su kien cuoi phai la xong, nhan {!r}".format(ten[-1]))
        bao_dam(set(ten[1:-1]) == {"chu"},
                "giua batdau va xong chi duoc co 'chu', nhan {}".format(ten[1:-1]))
        bao_dam(ten.count("chu") == 3, "mong 3 su kien chu, nhan {}".format(ten.count("chu")))
        bao_dam("loi" not in ten, "khong duoc co su kien loi o duong chay binh thuong")

        batdau = cac[0][1]
        bao_dam(kho_hoi_thoai.la_ma_hop_le(batdau.get("hoiThoaiId")),
                "batdau phai mang mot hoiThoaiId dang UUID, nhan {!r}".format(batdau))
        van = "".join(d["chu"] for t, d in cac if t == "chu")
        bao_dam(van == "Mot hai ba.", "ghep lai sai: {!r}".format(van))

        xong = cac[-1][1]
        bao_dam("trichDan" in xong, "xong phai mang trichDan (rong neu chua co RAG)")
        bao_dam(xong["trichDan"] == [], "chua co RAG thi trichDan phai rong")
        bao_dam("moHinhThat" in xong, "xong phai mang moHinhThat")
        return "{} su kien, {} chu".format(len(ten), ten.count("chu"))


@phep_kiem("4. moHinhThat doc tu phan hoi, KHONG vong lai ten da gui di")
def thu_mo_hinh_that_khong_vong_lai():
    # Cổng giả khai MỘT TÊN KHÁC hẳn cả mã công khai lẫn mã trọng số nền.
    # Nếu máy chủ chỉ vọng lại tên đã gửi đi thì phép kiểm này HỎNG — đó là toàn
    # bộ lý do nó tồn tại. Ca thật: cổng LiteLLM rơi sang mô hình khác khi khoá
    # thượng nguồn chết (đo 20/09/2026, 5 alias đều rơi về cùng một mô hình).
    ten_khac = "mot-mo-hinh-hoan-toan-khac"
    cong = CongGia(cac_mau=["a"], mo_hinh_that=ten_khac)
    with MayChuThu(cong) as m:
        _, d = m.json("GET", "/api/mo-hinh")
        ma_cong_khai = d["moHinh"]["ma"]
        ma_nen = d["nen"]["maTrongSo"]

        _, _, cac = m.hoi("Ai tra loi cau nay?")
        xong = [du for t, du in cac if t == "xong"]
        bao_dam(len(xong) == 1, "mong dung 1 su kien xong, nhan {}".format(len(xong)))
        that = xong[0].get("moHinhThat")
        bao_dam(that == ten_khac,
                "moHinhThat phai la ten may chu bao ({!r}), nhan {!r}".format(ten_khac, that))
        bao_dam(that != ma_cong_khai, "moHinhThat dang vong lai ma cong khai")
        bao_dam(that != ma_nen, "moHinhThat dang vong lai ma trong so nen")
        # Lệch thật thì phải khai lệch, nếu không giao diện không có gì để cảnh báo.
        bao_dam(xong[0].get("lech") is True,
                "ten khac ma trong so nen ma khong khai lech")
        bao_dam(xong[0].get("moHinhYeuCau") == ma_nen,
                "moHinhYeuCau phai la ma trong so da gui di")
        return "bao {!r}, khai lech".format(that)


@phep_kiem("5. cong khong khai ten mo hinh -> moHinhThat rong, KHONG bia ten")
def thu_khong_bia_ten_mo_hinh():
    cong = CongGia(cac_mau=["a"], mo_hinh_that=None)
    with MayChuThu(cong) as m:
        _, _, cac = m.hoi("Cau hoi")
        xong = [du for t, du in cac if t == "xong"][0]
        bao_dam(xong.get("moHinhThat") is None,
                "cong khong khai ten thi phai tra None, nhan {!r}".format(
                    xong.get("moHinhThat")))
        bao_dam("lech" not in xong, "khong biet ten that thi khong duoc khai lech")
        return "tra None thay vi vong lai ten da gui"


# ──────────────────────────────────────────────────────────────────────────────
# 6-7. Máy nội bộ hỏng
# ──────────────────────────────────────────────────────────────────────────────


TU_GOI_RA_NGOAI = (
    "openai", "anthropic", "gemini", "azure", "bedrock", "litellm",
    "openrouter", "dam may", "đám mây", "du phong", "dự phòng", "fallback",
)


@phep_kiem("6. backend dut giua chung -> event loi, noi ro la may NOI BO")
def thu_backend_dut_giua_chung():
    cong = CongGia(cac_mau=["Dang ", "tra ", "loi"], dut_sau=2)
    with MayChuThu(cong) as m:
        ma, _, cac = m.hoi("Cau hoi khi may noi bo chet")
        bao_dam(ma == 200, "dong SSE da mo thi van la 200, nhan {}".format(ma))
        ten = [t for t, _ in cac]
        bao_dam("loi" in ten, "thieu su kien loi, nhan {}".format(ten))
        bao_dam("xong" not in ten, "da bao loi thi KHONG duoc phat xong: {}".format(ten))
        bao_dam(ten[0] == "batdau", "van phai phat batdau truoc")
        bao_dam(ten.count("chu") == 2,
                "phan chu nhan duoc truoc khi dut phai giu lai, nhan {}".format(
                    ten.count("chu")))

        thong_bao = [du["thongBao"] for t, du in cac if t == "loi"][0]
        thap = thong_bao.lower()
        bao_dam("nội bộ" in thap or "noi bo" in thap,
                "cau bao loi phai noi ro la may NOI BO, nhan: {!r}".format(thong_bao))
        bao_dam(len(thong_bao) > 40, "cau bao loi qua ngan de nguoi doc biet kiem gi")

        # ── PHÂN BIỆT HAI NHÁNH LỖI, ĐỪNG BỎ ─────────────────────────────────
        # `_chay_dong` có hai nhánh bắt lỗi: nhánh ĐÚNG (`except lop_loi`) cho
        # câu `CAU_BAO_LOI_NOI_BO`, và nhánh lỗi CHUNG (`except Exception`) cho
        # câu "Cổng mô hình NỘI BỘ gặp lỗi (TênLớp)". Cả hai câu đều chứa chữ
        # "NỘI BỘ" và đều dài hơn 40 ký tự, nên ba phép so ở trên KHÔNG tách
        # được chúng.
        #
        # Đã đo ngày 26/09/2026: sửa `BoiCanh.lop_loi_noi_bo()` cho nó thôi
        # nhìn lớp lỗi của CỔNG (đúng cái hỏng mà phần chú thích của
        # `LoiGiaKhongNoiDuoc` bảo rằng phép kiểm này sẽ bắt được) thì máy chủ
        # rơi hết sang nhánh chung — mà cả bộ vẫn xanh 21/21. Một cổng vẫn xanh
        # sau khi thứ nó canh đã hỏng là một cổng không canh gì.
        #
        # Hai phép dưới đây là chỗ tách. Phép thứ hai không phụ thuộc vào nội
        # dung hằng số: nhánh chung LUÔN nhét tên lớp ngoại lệ vào câu báo, còn
        # nhánh đúng thì không bao giờ.
        bao_dam(thong_bao == may_chu.CAU_BAO_LOI_NOI_BO,
                "roi vao NHANH LOI CHUNG chu khong phai nhanh 'khong noi duoc may "
                "noi bo' — may chu dang khong bat lop loi CUA CONG. Nhan: {!r}".format(
                    thong_bao))
        bao_dam(LoiGiaKhongNoiDuoc.__name__ not in thong_bao,
                "cau bao loi mang ten lop ngoai le ({}) => day la nhanh loi CHUNG, "
                "khong phai nhanh may noi bo".format(LoiGiaKhongNoiDuoc.__name__))

        # Không được có dấu hiệu nào của một lần gọi ra ngoài.
        for tu in TU_GOI_RA_NGOAI:
            if tu in ("dự phòng", "du phong", "fallback"):
                # Ba từ này được phép xuất hiện Ở DẠNG PHỦ ĐỊNH ("không có đường
                # dự phòng ra ngoài"). Chỉ bắt khi KHÔNG có chữ phủ định đứng gần.
                if tu in thap:
                    bao_dam("không" in thap or "khong" in thap,
                            "cau bao loi nhac {!r} ma khong phu dinh".format(tu))
                continue
            bao_dam(tu not in thap,
                    "cau bao loi nhac toi mot nha cung cap ben ngoai: {!r}".format(tu))

        bao_dam(len(cong.cac_lan_goi) == 1,
                "cong mo hinh phai bi goi dung MOT lan (khong thu lai o noi khac), "
                "nhan {}".format(len(cong.cac_lan_goi)))
        return "loi dung luc, {} lan goi cong".format(len(cong.cac_lan_goi))


@phep_kiem("7. chua cai cong mo hinh -> event loi, khong im lang, khong goi ra ngoai")
def thu_chua_co_cong_mo_hinh():
    with MayChuThu(cong_gia=None) as m:
        ma, _, cac = m.hoi("Cau hoi khi chua co cong")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        ten = [t for t, _ in cac]
        bao_dam(ten == ["batdau", "loi"], "mong [batdau, loi], nhan {}".format(ten))
        thong_bao = cac[1][1]["thongBao"]
        thap = thong_bao.lower()
        bao_dam("nội bộ" in thap or "noi bo" in thap,
                "phai noi ro cong NOI BO chua cai: {!r}".format(thong_bao))
        return "bao loi thay vi im lang"


@phep_kiem("8. may_chu.py KHONG nhap thu vien goi mang ra ngoai")
def thu_khong_co_duong_ra_ngoai():
    """Kiểm CẤU TRÚC, không kiểm hành vi.

    Hai phép kiểm trên chứng minh rằng ở ĐƯỜNG CHẠY đã thử, máy chủ không gọi ra
    ngoài. Chúng không chứng minh được rằng không có một nhánh nào khác làm điều
    đó. Phép này đóng khoảng trống ấy từ phía cấu trúc: nếu tệp không nhập nổi một
    thư viện khách HTTP nào thì nó không có cách nào gửi câu hỏi đi đâu — mọi lối
    ra phải đi qua `cong_mo_hinh`, tức đi qua đúng một chỗ kiểm được.
    """
    duong = os.path.join(THU_MUC, "may_chu.py")
    with open(duong, "r", encoding="utf-8") as tep:
        van = tep.read()

    # ĐỌC BẰNG `ast`, KHÔNG BẰNG BIỂU THỨC CHÍNH QUY.
    #
    # Bản đầu của phép kiểm này dùng `re` bắt tên đứng ngay sau `from`/`import`.
    # Nó bỏ lọt đúng dạng viết tự nhiên nhất: `from urllib import request` —
    # chuỗi bắt được là "urllib", mà "urllib" không nằm trong danh sách cấm, nên
    # một đường gọi mạng RA NGOÀI dùng được ngay vẫn ĐẠT. Đã đo ngày 26/09/2026:
    # thêm `from urllib import request` và `from http import client` vào
    # may_chu.py thì cả bộ vẫn xanh 21/21 và phép này vẫn khoe "0 thư viện gọi
    # mạng ra". Một cổng canh luật quan trọng nhất của hệ mà mở sẵn một lối đi
    # thì tệ hơn không có cổng: nó phát ra một lời bảo đảm sai.
    #
    # `ast` dựng lại TÊN ĐẦY ĐỦ của thứ được nhập, nên `from urllib import
    # request` và `import urllib.request` quy về cùng một chuỗi "urllib.request".
    cay = ast.parse(van, filename=duong)

    cam = ("urllib.request", "urllib.error", "http.client", "requests",
           "httpx", "aiohttp", "urllib3", "websockets", "socket", "ssl",
           "ftplib", "smtplib", "telnetlib", "subprocess")

    cac_goi = []          # [(dòng, tên đầy đủ)]
    so_lenh_nhap = 0
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Import):
            so_lenh_nhap += 1
            for ten in nut.names:
                cac_goi.append((nut.lineno, ten.name))
        elif isinstance(nut, ast.ImportFrom):
            so_lenh_nhap += 1
            goc = nut.module or ""
            for ten in nut.names:
                # Xét CẢ hai: gói gốc, và gói gốc nối tên được nhập. Tên được
                # nhập có thể là một mô-đun con (`from urllib import request`)
                # mà cũng có thể chỉ là một hàm (`from typing import Optional`)
                # — nối cả hai rồi so thì không phải đoán nó là loại nào.
                cac_goi.append((nut.lineno, goc + "." + ten.name if goc else ten.name))
            if goc:
                cac_goi.append((nut.lineno, goc))

    thay = []
    for so, goi in cac_goi:
        for xau in cam:
            if goi == xau or goi.startswith(xau + "."):
                thay.append("dong {}: {}".format(so, goi))
    bao_dam(not thay, "may_chu.py nhap thu vien goi mang ra ngoai: {}".format(
        sorted(set(thay))))

    # NHẬP ĐỘNG cũng là một lối ra: `__import__("urllib.request")` và
    # `importlib.import_module(...)` không để lại một nút Import nào. Bắt bằng
    # `ast` chứ không bằng tìm chuỗi, vì chữ "importlib" có mặt trong phần chú
    # thích của may_chu.py ("Không dùng `importlib` thủ công") — tìm chuỗi thì
    # phép kiểm hỏng vì một dòng chú thích, và một phép kiểm kêu oan sẽ bị gỡ.
    nhap_dong = []
    for nut in ast.walk(cay):
        if not isinstance(nut, ast.Call):
            continue
        ham = nut.func
        if isinstance(ham, ast.Name) and ham.id == "__import__":
            nhap_dong.append("dong {}: __import__(...)".format(nut.lineno))
        elif isinstance(ham, ast.Attribute) and ham.attr in (
            "import_module", "load_module", "exec_module"
        ):
            nhap_dong.append("dong {}: ...{}(...)".format(nut.lineno, ham.attr))
    bao_dam(not nhap_dong,
            "may_chu.py nhap mo-dun kieu dong, khong kiem tinh duoc: {}".format(
                nhap_dong))

    return "{} lenh nhap ({} ten goi), 0 thu vien goi mang ra, 0 nhap dong".format(
        so_lenh_nhap, len(cac_goi))


# ──────────────────────────────────────────────────────────────────────────────
# 9-12. Phân quyền hội thoại
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("9. DELETE hoi thoai cua NGUOI KHAC -> 404 va KHONG xoa")
def thu_xoa_cua_nguoi_khac():
    with MayChuThu(CongGia(), nguoi="demo") as m:
        # Hội thoại của một người khác, tạo thẳng trong kho.
        ma_ht = m.kho.tao_hoi_thoai("nguoi-khac", "Bi mat cua nguoi khac")
        m.kho.them_tin_nhan(ma_ht, "nguoi-khac", "nguoi", "noi dung rieng")
        truoc = m.kho.dem(None)

        ma, d = m.json("DELETE", "/api/hoi-thoai/" + ma_ht)
        bao_dam(ma == 404, "mong 404 (khong phai 403), nhan {}".format(ma))
        bao_dam(d.get("daXoa") is not True, "khong duoc bao da xoa")

        sau = m.kho.dem(None)
        bao_dam(sau == truoc, "so hoi thoai doi tu {} thanh {} — DA XOA THAT".format(
            truoc, sau))
        bao_dam(m.kho.doc(ma_ht, "nguoi-khac") is not None,
                "hoi thoai cua nguoi khac da bien mat")
        # 404 chứ không 403: 403 nói "có thứ đó, bạn không được đụng", tức cho
        # người lạ một cách dò xem một mã hội thoại có tồn tại hay không.
        ma_khong_co, _ = m.json("DELETE", "/api/hoi-thoai/" + str(uuid.uuid4()))
        bao_dam(ma_khong_co == 404,
                "'khong co' phai tra CUNG ma voi 'cua nguoi khac', nhan {}".format(
                    ma_khong_co))
        return "404 ca hai ca, {} hoi thoai con nguyen".format(sau)


@phep_kiem("10. DELETE ma khong phai UUID -> 404 va KHONG cham toi kho")
def thu_xoa_ma_rac():
    with MayChuThu(CongGia()) as m:
        cac_ma_rac = [
            "khong-phai-uuid",
            "../../etc/passwd",
            # Dấu cách mã hoá %20: `http.client` từ chối gửi dấu cách thô trong
            # URL, nên viết thô thì bài kiểm chết ở phía KHÁCH và không bao giờ
            # chạm tới máy chủ — một phép kiểm không kiểm được gì.
            "1%20OR%201=1",
            "%27%20OR%20%271",
            "00000000-0000-0000-0000-00000000000",   # thiếu một ký tự
        ]
        truoc = m.kho.so_lan_mo
        for rac in cac_ma_rac:
            ma, _ = m.json("DELETE", "/api/hoi-thoai/" + rac)
            bao_dam(ma == 404, "ma rac {!r} phai tra 404, nhan {}".format(rac, ma))
        sau = m.kho.so_lan_mo
        # Đếm số lần MỞ tệp CSDL. Một phép kiểm chỉ nhìn mã 404 sẽ ĐẠT kể cả khi
        # mỗi lượt quét đường dẫn vẫn mở và khoá tệp một nhịp.
        bao_dam(sau == truoc,
                "kho bi cham {} lan boi cac ma rac (mong 0)".format(sau - truoc))
        return "{} ma rac, 0 lan cham CSDL".format(len(cac_ma_rac))


@phep_kiem("11. GET /api/hoi-thoai chi liet ke hoi thoai CUA MINH")
def thu_liet_ke_theo_chu_so_huu():
    with MayChuThu(CongGia(), nguoi="demo") as m:
        cua_toi = m.kho.tao_hoi_thoai("demo", "Cua toi")
        cua_ho = m.kho.tao_hoi_thoai("nguoi-khac", "Cua ho")
        ma, d = m.json("GET", "/api/hoi-thoai")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        cac_id = [h["id"] for h in d["danhSach"]]
        bao_dam(cua_toi in cac_id, "thieu hoi thoai cua chinh minh")
        bao_dam(cua_ho not in cac_id, "LO hoi thoai cua nguoi khac trong danh sach")
        for h in d["danhSach"]:
            bao_dam(set(h.keys()) == {"id", "tieuDe", "suaLuc"},
                    "muc danh sach co truong thua: {}".format(sorted(h.keys())))
        # Đọc thẳng hội thoại của người khác cũng phải 404.
        ma_doc, _ = m.json("GET", "/api/hoi-thoai/" + cua_ho)
        bao_dam(ma_doc == 404, "doc hoi thoai nguoi khac phai 404, nhan {}".format(ma_doc))
        return "1/2 hoi thoai hien ra, doc cheo -> 404"


@phep_kiem("12. POST /api/hoi vao hoi thoai cua nguoi khac -> 404, khong ghi vao do")
def thu_hoi_vao_hoi_thoai_nguoi_khac():
    cong = CongGia()
    with MayChuThu(cong, nguoi="demo") as m:
        cua_ho = m.kho.tao_hoi_thoai("nguoi-khac", "Cua ho")
        ma, _, _ = m.hoi("Chen cau nay vao hoi thoai nguoi khac", hoi_thoai_id=cua_ho)
        bao_dam(ma == 404, "mong 404, nhan {}".format(ma))
        ho = m.kho.doc(cua_ho, "nguoi-khac")
        bao_dam(ho is not None and ho["tinNhan"] == [],
                "da ghi tin nhan vao hoi thoai cua nguoi khac: {}".format(ho))
        bao_dam(len(cong.cac_lan_goi) == 0,
                "khong duoc goi mo hinh cho mot yeu cau da bi tu choi")
        return "404, 0 tin nhan bi chen, 0 lan goi mo hinh"


# ──────────────────────────────────────────────────────────────────────────────
# 13. Lưu và đọc lại
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("13. Hoi xong doc lai duoc ca cau hoi lan cau tra loi")
def thu_luu_va_doc_lai():
    cong = CongGia(
        cac_mau=["Tra ", "loi."],
        mo_hinh_that="google/gemma-4-31B-it",
        trich_dan=[{"nhan": "1", "nguon": "So tay noi bo", "duongDan": "tai-lieu/a.md"}],
    )
    with MayChuThu(cong) as m:
        _, _, cac = m.hoi("Cau hoi cua toi")
        ma_ht = cac[0][1]["hoiThoaiId"]
        xong = [du for t, du in cac if t == "xong"][0]
        bao_dam(len(xong["trichDan"]) == 1, "trichDan khong di qua")
        bao_dam(set(xong["trichDan"][0].keys()) == {"nhan", "nguon", "duongDan"},
                "trichDan sai hinh dang: {}".format(xong["trichDan"][0]))

        ma, d = m.json("GET", "/api/hoi-thoai/" + ma_ht)
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        bao_dam(len(d["tinNhan"]) == 2, "mong 2 tin nhan, nhan {}".format(len(d["tinNhan"])))
        bao_dam(d["tinNhan"][0]["vaiTro"] == "nguoi", "tin dau phai cua nguoi")
        bao_dam(d["tinNhan"][0]["noiDung"] == "Cau hoi cua toi", "cau hoi bi doi")
        bao_dam(d["tinNhan"][1]["vaiTro"] == "may", "tin sau phai cua may")
        bao_dam(d["tinNhan"][1]["noiDung"] == "Tra loi.", "cau tra loi bi doi")
        bao_dam(d["tinNhan"][1]["moHinh"] == "google/gemma-4-31B-it",
                "ten mo hinh khong duoc luu cung tin nhan")
        bao_dam(d["tinNhan"][1]["trichDan"], "trich dan khong duoc luu")
        return "2 tin nhan, trich dan va ten mo hinh con nguyen"


# ──────────────────────────────────────────────────────────────────────────────
# 14-15. Địa chỉ nghe
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("14. May chu TU CHOI nghe 0.0.0.0 khi chua khai tuong minh")
def thu_tu_choi_nghe_ngoai():
    # Truyền `cho_phep_nghe_ngoai=""` tường minh để phép kiểm không phụ thuộc vào
    # biến môi trường của máy đang chạy.
    for dia_chi in ("0.0.0.0", "::", "192.168.1.10"):
        try:
            may_chu.tao_may_chu(dia_chi=dia_chi, cong=0, cho_phep_nghe_ngoai="")
        except may_chu.LoiDiaChiKhongAnToan as loi:
            bao_dam(may_chu.BIEN_NGHE_NGOAI in str(loi),
                    "cau tu choi phai chi ra bien moi truong de mo khoa")
            continue
        raise AssertionError(
            "KHONG tu choi dia chi {!r} — mot may chu khong xac thuc dang nghe "
            "ca mang".format(dia_chi)
        )
    # Các giá trị hay bị sao chép từ kịch bản khác KHÔNG được mở khoá.
    for gia_tri_sai in ("1", "true", "yes", "True", "toi hieu rui ro"):
        try:
            may_chu.kiem_dia_chi("0.0.0.0", gia_tri_sai)
        except may_chu.LoiDiaChiKhongAnToan:
            continue
        raise AssertionError(
            "gia tri {!r} khong duoc mo khoa viec nghe ngoai".format(gia_tri_sai)
        )
    return "3 dia chi ngoai bi tu choi, 5 gia tri co mo khoa nham bi tu choi"


@phep_kiem("15. Khai tuong minh thi van nghe ngoai duoc (co duong ra cho nguoi van hanh)")
def thu_khai_tuong_minh_thi_cho():
    # Chỉ kiểm phép kiểm địa chỉ, KHÔNG mở socket ra ngoài trong lúc chạy bài thử.
    may_chu.kiem_dia_chi("0.0.0.0", may_chu.GIA_TRI_CHAP_NHAN_RUI_RO)
    may_chu.kiem_dia_chi("127.0.0.1", "")
    may_chu.kiem_dia_chi("::1", "")
    may_chu.kiem_dia_chi("localhost", "")
    return "loopback luon cho, 0.0.0.0 cho khi khai dung cau"


# ──────────────────────────────────────────────────────────────────────────────
# 16-17. Đầu vào hỏng và tệp tĩnh
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("16. Cau hoi hong -> 400 voi ma loi giao dien hieu")
def thu_cau_hoi_hong():
    cong = CongGia()
    with MayChuThu(cong) as m:
        cac_ca = [
            ("", "rong"),
            ("   \n  ", "rong"),
            ("x" * (may_chu.DAI_TOI_DA_CAU_HOI + 1), "qua-dai"),
            ("co ky tu \x00 rac", "ky-tu-dieu-khien"),
        ]
        for noi_dung, mong in cac_ca:
            ma, _, tho = m.goi("POST", "/api/hoi",
                               {"hoiThoaiId": None, "noiDung": noi_dung, "mucNoLuc": "nhanh"})
            bao_dam(ma == 400, "ca {!r} mong 400, nhan {}".format(mong, ma))
            d = json.loads(tho)
            bao_dam(d.get("loi") == mong,
                    "ca {!r}: ma loi sai, nhan {!r}".format(mong, d.get("loi")))
        bao_dam(len(cong.cac_lan_goi) == 0,
                "cau hoi hong khong duoc di toi mo hinh")
        bao_dam(m.kho.dem(None) == 0, "cau hoi hong khong duoc tao hoi thoai")
        return "{} ca, 0 lan goi mo hinh, 0 hoi thoai rac".format(len(cac_ca))


@phep_kiem("17. Tep tinh: phuc vu giao dien, chan di xuyen thu muc")
def thu_tep_tinh():
    with MayChuThu(CongGia()) as m:
        ma, dau, tho = m.goi("GET", "/")
        bao_dam(ma == 200, "trang chu mong 200, nhan {}".format(ma))
        bao_dam("text/html" in (dau.get("Content-Type") or ""),
                "kieu tep sai: {!r}".format(dau.get("Content-Type")))
        bao_dam("chat.js" in tho, "index.html khong co ve la giao dien chat")

        for rac in ("/../README.md", "/..%2fREADME.md", "/tai-lieu/a.md",
                    "/../../etc/hosts", "/chat.js/../../README.md"):
            ma_rac, _, _ = m.goi("GET", rac)
            bao_dam(ma_rac == 404, "duong {!r} phai 404, nhan {}".format(rac, ma_rac))

        ma_js, dau_js, _ = m.goi("GET", "/chat.js")
        bao_dam(ma_js == 200, "chat.js mong 200, nhan {}".format(ma_js))
        bao_dam("javascript" in (dau_js.get("Content-Type") or ""),
                "kieu tep js sai: {!r}".format(dau_js.get("Content-Type")))
        return "index.html + chat.js phuc vu duoc, 5 duong di xuyen bi chan"


@phep_kiem("18. GET /api/toi tu khai la CHUA CO XAC THUC")
def thu_api_toi():
    with MayChuThu(CongGia()) as m:
        ma, d = m.json("GET", "/api/toi")
        bao_dam(ma == 200, "mong 200, nhan {}".format(ma))
        bao_dam(d.get("xacThuc") is False,
                "phai tu khai xacThuc=false, nhan {!r}".format(d.get("xacThuc")))
        bao_dam(d.get("canhBao"), "phai co cau canh bao la ban demo mot nguoi")
        thap = (d.get("canhBao") or "").lower()
        bao_dam("demo" in thap, "cau canh bao phai noi ro day la ban demo")
        bao_dam(not d.get("email"), "ban demo khong duoc bia ra mot dia chi thu")
        return "xacThuc=False, co canh bao"


# ──────────────────────────────────────────────────────────────────────────────
# 19-21. Mặt tiếp giáp với cổng mô hình thật
# ──────────────────────────────────────────────────────────────────────────────


@phep_kiem("19. Tin nhan gui sang cong dung dang OpenAI, co ca lich su")
def thu_hinh_dang_tin_nhan():
    """Kho lưu vai trò tiếng Việt, cổng mô hình nói API tương thích OpenAI.

    Chỗ đổi hình dạng là một biên, và biên là chỗ hay sai nhất. Sai ở đây thì vLLM
    nhận một danh sách nó không hiểu: hoặc nó ném lỗi, hoặc — tệ hơn — nó bỏ qua
    phần lịch sử và mô hình trả lời như chưa từng nói chuyện, mà không ai báo gì.
    """
    cong = CongGia(cac_mau=["ok"], mo_hinh_that="google/gemma-4-31B-it")
    with MayChuThu(cong) as m:
        _, _, cac = m.hoi("Cau hoi thu nhat")
        ma_ht = cac[0][1]["hoiThoaiId"]
        m.hoi("Cau hoi thu hai", hoi_thoai_id=ma_ht)

        bao_dam(len(cong.cac_lan_goi) == 2, "mong 2 lan goi cong")
        lan_hai = cong.cac_lan_goi[1]["tin_nhan"]
        for tin in lan_hai:
            bao_dam(set(tin.keys()) == {"role", "content"},
                    "tin nhan sai dang OpenAI: {}".format(sorted(tin.keys())))
            bao_dam(tin["role"] in ("user", "assistant"),
                    "vai tro phai la user/assistant, nhan {!r}".format(tin["role"]))
        # Lượt hai phải mang theo: hỏi 1, đáp 1, hỏi 2.
        bao_dam(len(lan_hai) == 3, "lich su khong di kem, nhan {} tin".format(len(lan_hai)))
        bao_dam([t["role"] for t in lan_hai] == ["user", "assistant", "user"],
                "thu tu vai tro sai: {}".format([t["role"] for t in lan_hai]))
        bao_dam(lan_hai[0]["content"] == "Cau hoi thu nhat", "mat cau hoi dau")
        bao_dam(lan_hai[-1]["content"] == "Cau hoi thu hai", "cau hoi moi khong o cuoi")
        return "2 luot, luot hai mang 3 tin dung vai tro"


@phep_kiem("20. Tra loi binh thuong KHONG bi dan nhan 'lech'")
def thu_khong_bao_lech_oan():
    """Chốt chặn cho một cái bẫy kiểu dữ liệu đã suýt dính.

    `cong_mo_hinh.doi_chieu_mo_hinh()` trả về TÊN mô hình (một chuỗi), không phải
    đúng/sai. Ai dùng nó làm điều kiện "có lệch không" thì mọi chuỗi không rỗng
    đều đúng ⇒ mọi câu trả lời đều bị dán nhãn lệch, và một cảnh báo kêu ở mọi
    lượt là một cảnh báo không ai còn đọc — đúng lúc nó cần được đọc thì đã muộn.
    """
    try:
        import cong_mo_hinh
    except ImportError:
        cong_mo_hinh = None
    if cong_mo_hinh is not None:
        ket_qua = cong_mo_hinh.doi_chieu_mo_hinh("a", "b")
        bao_dam(isinstance(ket_qua, str),
                "doi_chieu_mo_hinh phai tra CHUOI, nhan {}".format(type(ket_qua).__name__))
        bao_dam(bool(ket_qua) is True,
                "chuoi khong rong luon dung — day chinh la cai bay")

    # Cổng khai ĐÚNG tên trọng số nền ⇒ không có gì lệch.
    cong = CongGia(cac_mau=["x"], mo_hinh_that="google/gemma-4-31B-it")
    with MayChuThu(cong) as m:
        _, d = m.json("GET", "/api/mo-hinh")
        bao_dam(d["nen"]["maTrongSo"] == "google/gemma-4-31B-it", "mac dinh da doi?")
        _, _, cac = m.hoi("Cau hoi binh thuong")
        xong = [du for t, du in cac if t == "xong"][0]
        bao_dam("lech" not in xong,
                "tra loi dung mo hinh ma van bao lech: {}".format(xong))
        bao_dam(xong["moHinhThat"] == "google/gemma-4-31B-it", "moHinhThat sai")
        return "khong bao lech oan"


@phep_kiem("21. Trong so mang tien to google/ LUON la trong so cua Google")
def thu_chot_cung_trong_so_google():
    """Chốt cứng, không phụ thuộc mô-đun nào khác trả lời đúng.

    Trọng số Google NGUYÊN BẢN không thể là trọng số BDSG đã tinh chỉnh — bản đã
    tinh chỉnh thì mang mã khác. Nên `True` ở đây chỉ có thể là một lỗi, và lỗi ở
    đúng dòng này là một lời khai sai về việc AI đã làm ra mô hình.
    """
    for ma in ("google/gemma-4-31B-it", "google/gemma-4-31B",
               "GOOGLE/Gemma-4-31B-it", "  google/gemma-4-31B-it  "):
        bao_dam(may_chu.la_trong_so_bdsg(ma) is False,
                "ma {!r} phai tra False".format(ma))
    # Mã không phải của Google thì hỏi mô-đun cấu hình; ở 26/09/2026 nó vẫn False
    # vì BDSG chưa tinh chỉnh trọng số nào.
    bao_dam(may_chu.la_trong_so_bdsg("bdsg/chua-co") is False,
            "26/09/2026 BDSG chua tinh chinh trong so nao")
    return "4 ma google/ + 1 ma khac deu False"


@phep_kiem("22. Khoi khai xuat xu KHONG gan cho Google mot trong so khong phai cua ho")
def thu_xuat_xu_khong_gan_bua():
    """Chiều ngược của phép 21, và nó cũng là một lời khai sai về xuất xứ.

    Phép 21 chặn việc NHẬN VƠ trọng số của Google là của BDSG. Phép này chặn
    chiều kia: GÁN CHO GOOGLE một trọng số không phải của họ.

    Đã đo 26/09/2026: khối `nen` từng viết cứng `nhaCungCap: "Google"`,
    `giayPhep: "Apache-2.0"` và liên kết mặc định trỏ trang Gemma 4 của Google —
    cả ba đều là hằng số, trong khi mã trọng số là một BIẾN. Trỏ máy chủ sang
    `bdsg/...` thì API vẫn khai "do Google cung cấp, Apache-2.0", kèm liên kết
    tới trang của Google. Ghi công phải đúng theo cả hai chiều.

    Kiểm bằng hàm thuần, không qua HTTP: khối này không phụ thuộc mạng, và gọi
    thẳng thì phép kiểm không phải mượn biến môi trường của máy đang chạy.
    """
    # 1. Trọng số Google nguyên bản: ghi công đầy đủ, có liên kết.
    d = may_chu.dung_phan_hoi_mo_hinh(
        may_chu.doc_cau_hinh_mo_hinh({"ma_mo_hinh": "google/gemma-4-31B-it"})
    )
    bao_dam(d["nen"]["nhaCungCap"] == "Google", "trong so google/ phai ghi cong Google")
    bao_dam(d["nen"]["giayPhep"] == "Apache-2.0",
            "Gemma 4 phat hanh theo Apache-2.0")
    bao_dam("huggingface.co/google/" in d["nen"]["lienKet"],
            "thieu lien ket toi trang trong so cua Google")

    # 2. Trọng số KHÔNG phải của Google: không được khai là của Google, không
    #    được đoán giấy phép, và không được trỏ tới trang của Google.
    for ma_khac in ("bdsg/gemma4-31b-tinh-chinh", "meta-llama/Llama-3-8B"):
        d = may_chu.dung_phan_hoi_mo_hinh(
            may_chu.doc_cau_hinh_mo_hinh({"ma_mo_hinh": ma_khac})
        )
        nen = d["nen"]
        bao_dam(nen["nhaCungCap"] != "Google",
                "trong so {!r} bi gan cho Google".format(ma_khac))
        bao_dam(nen["giayPhep"] != "Apache-2.0",
                "trong so {!r} bi doan giay phep Apache-2.0".format(ma_khac))
        bao_dam("google" not in (nen["lienKet"] or "").lower(),
                "trong so {!r} van tro lien ket toi trang cua Google: {!r}".format(
                    ma_khac, nen["lienKet"]))
        bao_dam("của Google" not in d["moHinh"]["moTa"] and
                "(Google)" not in d["moHinh"]["moTa"],
                "cau mo ta van noi trong so {!r} la 'cua Google'".format(ma_khac))
    return "google/ duoc ghi cong day du; 2 ma khac khong bi gan bua"


# ──────────────────────────────────────────────────────────────────────────────
# Chạy
# ──────────────────────────────────────────────────────────────────────────────

CAC_PHEP_KIEM = [
    thu_mo_hinh_du_truong,
    thu_khong_nhan_vo_trong_so,
    thu_thu_tu_su_kien,
    thu_mo_hinh_that_khong_vong_lai,
    thu_khong_bia_ten_mo_hinh,
    thu_backend_dut_giua_chung,
    thu_chua_co_cong_mo_hinh,
    thu_khong_co_duong_ra_ngoai,
    thu_xoa_cua_nguoi_khac,
    thu_xoa_ma_rac,
    thu_liet_ke_theo_chu_so_huu,
    thu_hoi_vao_hoi_thoai_nguoi_khac,
    thu_luu_va_doc_lai,
    thu_tu_choi_nghe_ngoai,
    thu_khai_tuong_minh_thi_cho,
    thu_cau_hoi_hong,
    thu_tep_tinh,
    thu_api_toi,
    thu_hinh_dang_tin_nhan,
    thu_khong_bao_lech_oan,
    thu_chot_cung_trong_so_google,
    thu_xuat_xu_khong_gan_bua,
]


def main() -> int:
    print("=" * 78)
    print("BAI TU KIEM — may chu chat noi bo (phuc-vu/)")
    print("Cong mo hinh: GIA (khong GPU, khong mang, khong trong so)")
    print("=" * 78)
    print()
    tat_ca_dat = True
    for ham in CAC_PHEP_KIEM:
        if not ham():
            tat_ca_dat = False

    print()
    print("=" * 78)
    so_dat = sum(1 for _, dat, _ in _KET_QUA if dat)
    so_hong = len(_KET_QUA) - so_dat
    if tat_ca_dat:
        print("KET QUA: {}/{} DAT.".format(so_dat, len(_KET_QUA)))
        print()
        print("Nghia la gi: hop dong sau duong va bon su kien SSE chay dung; phan quyen")
        print("hoi thoai chan duoc ca 'cua nguoi khac' lan 'ma rac'; khi may noi bo hong")
        print("thi may chu BAO LOI chu khong goi di dau khac.")
        print("Nghia la gi KHONG: chua chay voi mo hinh that, chua do do tre, chua do so")
        print("yeu cau dong thoi, chua co dang nhap. Ban nay la DEMO MOT NGUOI tren")
        print("localhost — chua dung duoc cho nhieu nhan vien.")
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
