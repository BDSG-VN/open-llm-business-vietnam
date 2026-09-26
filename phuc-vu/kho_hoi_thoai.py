#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kho hội thoại cho máy chủ chat nội bộ — sqlite3 của thư viện chuẩn.

CHẠY THỬ NHANH:
    .venv/bin/python3 -m py_compile phuc-vu/kho_hoi_thoai.py

Bài tự kiểm của kho này nằm chung trong `phuc-vu/thu_may_chu.py` (kho và máy chủ
được kiểm cùng nhau, vì phần lớn luật phân quyền chỉ có nghĩa khi đi qua đường HTTP).

═══ VÌ SAO LÀ SQLITE, KHÔNG PHẢI MỘT CSDL MÁY CHỦ ═══

Bản này là DEMO MỘT NGƯỜI trên máy nội bộ (xem phần cảnh báo ở `may_chu.py`). Một
CSDL máy chủ thêm một tiến trình phải chạy, một chuỗi kết nối phải giữ bí mật, và
một cổng mạng nữa phải đóng. sqlite3 nằm sẵn trong thư viện chuẩn, dữ liệu là MỘT
tệp, và tệp ấy bị `.gitignore` chặn — ba thứ đó đúng với cỡ của bản này.

Khi có đăng nhập thật và nhiều nhân viên thì đổi lớp này, KHÔNG đổi hợp đồng: máy
chủ chỉ gọi các hàm dưới đây, không viết câu lệnh SQL nào.

═══ HAI QUYẾT ĐỊNH VỀ AN TOÀN, GHI RA ĐỂ NGƯỜI SAU ĐỪNG "SỬA" NHẦM ═══

1. ĐIỀU KIỆN SỞ HỮU NẰM TRONG CHÍNH CÂU LỆNH SQL, không phải ở tầng trên.

   Cách sai trông rất tự nhiên:

       ht = kho.doc(ma)                      # câu lệnh 1
       if ht["chu_so_huu"] != nguoi: return  # so ở Python
       kho.xoa(ma)                           # câu lệnh 2

   Nó có HAI câu lệnh và một khoảng hở giữa chúng, và tệ hơn: `xoa(ma)` trở thành
   một hàm xoá vô điều kiện đang nằm sẵn trong kho mã. Ngày nào một người viết
   đường mới gọi thẳng `xoa(ma)` mà quên bước so, dữ liệu người khác biến mất, và
   không có gì báo. Ở đây `xoa()` KHÔNG THỂ gọi mà thiếu chủ sở hữu — chủ sở hữu là
   tham số bắt buộc và nó đi thẳng vào mệnh đề WHERE.

2. "KHÔNG CÓ" VÀ "CỦA NGƯỜI KHÁC" TRẢ CÙNG MỘT KẾT QUẢ (False).

   Phân biệt hai ca ấy là tặng người lạ một phép dò: gửi một mã bất kỳ, nếu nhận
   "không được phép" thay vì "không có" thì mã đó CÓ TỒN TẠI. Kho này không nói
   điều đó, nên máy chủ không có cách nào nói hộ.

═══ THAM SỐ TRUYỀN VÀO SQL ═══

Mọi giá trị đi vào SQL bằng dấu `?`, không bằng phép nối chuỗi. Đây không phải
sở thích trình bày: một mã hội thoại đến từ URL của người lạ.

TRẠNG THÁI SỐ LIỆU (26/09/2026): chưa đo hiệu năng kho này (chưa có phép đo tải
nào chạy thật). Mọi con số về độ trễ ở tài liệu khác không nói gì về tệp này.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

# Tên biến môi trường khai đường dẫn tệp CSDL. Mặc định là một tệp trong thư mục
# làm việc hiện tại chứ KHÔNG phải trong kho mã: người chạy thử không nên vô tình
# tạo dữ liệu thật ngay cạnh mã nguồn rồi commit nhầm. `.gitignore` chặn `*.db`
# như một lớp thứ hai, nhưng lớp thứ nhất là đừng đặt tệp vào chỗ dễ nhầm.
BIEN_DUONG_DAN = "BDSG_CHAT_CSDL"
TEN_TEP_MAC_DINH = "hoi-thoai.db"

VAI_TRO_HOP_LE = ("nguoi", "may")

# Độ dài tiêu đề cắt từ câu hỏi đầu tiên. Đủ để nhận ra hội thoại trong thanh bên,
# không đủ để một câu hỏi dài làm vỡ bố cục cột trái.
DAI_TIEU_DE = 60


def la_ma_hop_le(ma: Any) -> bool:
    """Chuỗi `ma` có đúng là một UUID viết chuẩn không?

    VÌ SAO KIỂM TRƯỚC KHI CHẠM CSDL: mã hội thoại đến thẳng từ URL. Một chuỗi rác
    đưa vào truy vấn vẫn an toàn (có tham số hoá), nhưng nó vẫn mở một kết nối,
    vẫn khoá tệp một nhịp, và vẫn để lại một lượt truy vấn cho mỗi lần ai đó quét
    đường dẫn. Chặn ở đây thì một lượt quét không chạm tới đĩa.

    So cả dạng viết chuẩn (`str(uuid.UUID(...))`) chứ không chỉ gọi `uuid.UUID`:
    `uuid.UUID` chấp nhận cả dạng có ngoặc nhọn, có tiền tố `urn:uuid:` và dạng
    32 ký tự không gạch. Ba dạng ấy trỏ cùng một mã nhưng là ba chuỗi khác nhau,
    tức ba khoá khác nhau trong bảng — nhận chúng là tự mở một cách để cùng một
    hội thoại có nhiều tên.
    """
    if not isinstance(ma, str) or len(ma) != 36:
        return False
    try:
        return str(uuid.UUID(ma)) == ma.lower()
    except (ValueError, AttributeError, TypeError):
        return False


def _bay_gio() -> str:
    """Thời điểm dạng ISO-8601 theo giờ UTC, giây tròn.

    Dùng UTC chứ không dùng giờ máy: hai máy khác múi giờ ghi vào cùng một tệp CSDL
    sẽ cho một dòng thời gian lộn xộn, và thứ tự "sửa gần đây nhất" sai theo.
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class KhoHoiThoai:
    """Lưu hội thoại và tin nhắn, có chủ sở hữu, trên một tệp sqlite3.

    MỘT KẾT NỐI CHO MỖI THAO TÁC, KHÔNG PHẢI MỘT KẾT NỐI DÙNG CHUNG.

    Máy chủ chạy trên `ThreadingHTTPServer`, tức mỗi yêu cầu nằm trên một luồng
    khác. Đối tượng kết nối của sqlite3 mặc định TỪ CHỐI bị dùng từ luồng khác
    luồng đã tạo ra nó (`check_same_thread`), và cách hay bị chọn để "sửa" là tắt
    kiểm tra ấy đi — nhưng tắt xong thì hai luồng dùng chung một con trỏ giao dịch,
    và lỗi sinh ra là loại chỉ hiện dưới tải. Ở đây mỗi thao tác mở kết nối riêng,
    đóng ngay sau khi xong. Với cỡ một người dùng thì chi phí mở tệp không đáng kể,
    còn mô hình đồng thời thì đơn giản đến mức không có chỗ để sai.
    """

    def __init__(self, duong_dan: Optional[str] = None) -> None:
        if duong_dan is None:
            duong_dan = os.environ.get(BIEN_DUONG_DAN, "").strip() or TEN_TEP_MAC_DINH
        self.duong_dan = duong_dan
        # Đếm số lần thật sự mở tệp CSDL. Có hai công dụng: bài tự kiểm dùng nó để
        # CHỨNG MINH rằng một mã hội thoại rác không chạm tới kho (không đếm được
        # thì câu "không chạm tới kho" chỉ là một lời khai), và khi cần đo tải thì
        # đây là con số sẵn có.
        self.so_lan_mo = 0
        self._khoa_dem = threading.Lock()
        self._dung_bang()

    # ------------------------------------------------------------------
    # Nền
    # ------------------------------------------------------------------

    def _ket_noi(self) -> sqlite3.Connection:
        with self._khoa_dem:
            self.so_lan_mo += 1
        # timeout: khi một luồng khác đang giữ khoá ghi, chờ tới 5 giây thay vì
        # ném "database is locked" ngay lập tức. Mặc định của sqlite3 là 5 giây,
        # ghi ra tường minh để người sau biết con số ấy tồn tại và sửa được.
        ket_noi = sqlite3.connect(self.duong_dan, timeout=5.0)
        ket_noi.row_factory = sqlite3.Row
        # Bật ràng buộc khoá ngoại. sqlite3 TẮT nó theo mặc định, và phải bật lại
        # trên TỪNG kết nối — một pragma đặt ở chỗ khác không có tác dụng ở đây.
        ket_noi.execute("PRAGMA foreign_keys = ON")
        return ket_noi

    def _dung_bang(self) -> None:
        ket_noi = self._ket_noi()
        try:
            with ket_noi:
                ket_noi.execute(
                    """
                    CREATE TABLE IF NOT EXISTS hoi_thoai (
                        id          TEXT PRIMARY KEY,
                        chu_so_huu  TEXT NOT NULL,
                        tieu_de     TEXT NOT NULL,
                        tao_luc     TEXT NOT NULL,
                        sua_luc     TEXT NOT NULL
                    )
                    """
                )
                ket_noi.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tin_nhan (
                        stt          INTEGER PRIMARY KEY AUTOINCREMENT,
                        hoi_thoai_id TEXT NOT NULL
                                     REFERENCES hoi_thoai(id) ON DELETE CASCADE,
                        vai_tro      TEXT NOT NULL,
                        noi_dung     TEXT NOT NULL,
                        mo_hinh      TEXT,
                        trich_dan    TEXT,
                        tao_luc      TEXT NOT NULL
                    )
                    """
                )
                # Chỉ mục theo chủ sở hữu: mọi truy vấn liệt kê đều lọc theo cột này.
                ket_noi.execute(
                    "CREATE INDEX IF NOT EXISTS chi_muc_chu_so_huu "
                    "ON hoi_thoai(chu_so_huu, sua_luc DESC)"
                )
                ket_noi.execute(
                    "CREATE INDEX IF NOT EXISTS chi_muc_tin_nhan "
                    "ON tin_nhan(hoi_thoai_id, stt)"
                )
        finally:
            ket_noi.close()

    # ------------------------------------------------------------------
    # Ghi
    # ------------------------------------------------------------------

    def tao_hoi_thoai(self, chu_so_huu: str, tieu_de: str) -> str:
        """Tạo một hội thoại mới, trả về mã UUID của nó."""
        if not chu_so_huu:
            # Chủ sở hữu rỗng nghĩa là "của mọi người" — tức của không ai. Chặn ở
            # đây vì một hàng như thế sẽ khớp mọi phép so sau này.
            raise ValueError("chu_so_huu không được rỗng")
        ma = str(uuid.uuid4())
        luc = _bay_gio()
        ket_noi = self._ket_noi()
        try:
            with ket_noi:
                ket_noi.execute(
                    "INSERT INTO hoi_thoai (id, chu_so_huu, tieu_de, tao_luc, sua_luc) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (ma, chu_so_huu, cat_tieu_de(tieu_de), luc, luc),
                )
        finally:
            ket_noi.close()
        return ma

    def them_tin_nhan(
        self,
        hoi_thoai_id: str,
        chu_so_huu: str,
        vai_tro: str,
        noi_dung: str,
        mo_hinh: Optional[str] = None,
        trich_dan: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Thêm một tin nhắn vào hội thoại CỦA NGƯỜI NÀY. Trả False nếu không được.

        Điều kiện sở hữu nằm trong chính câu lệnh INSERT (qua `SELECT ... WHERE`),
        cùng lý do như ở `xoa()`: không để tồn tại một đường ghi vô điều kiện.
        """
        if vai_tro not in VAI_TRO_HOP_LE:
            raise ValueError("vai_tro phải là một trong %r" % (VAI_TRO_HOP_LE,))
        if not la_ma_hop_le(hoi_thoai_id) or not chu_so_huu:
            return False
        luc = _bay_gio()
        van_trich_dan = None
        if trich_dan:
            van_trich_dan = json.dumps(trich_dan, ensure_ascii=False)
        ket_noi = self._ket_noi()
        try:
            with ket_noi:
                con_tro = ket_noi.execute(
                    """
                    INSERT INTO tin_nhan
                           (hoi_thoai_id, vai_tro, noi_dung, mo_hinh, trich_dan, tao_luc)
                    SELECT ?, ?, ?, ?, ?, ?
                      FROM hoi_thoai
                     WHERE id = ? AND chu_so_huu = ?
                    """,
                    (
                        hoi_thoai_id, vai_tro, noi_dung, mo_hinh, van_trich_dan, luc,
                        hoi_thoai_id, chu_so_huu,
                    ),
                )
                if con_tro.rowcount != 1:
                    return False
                ket_noi.execute(
                    "UPDATE hoi_thoai SET sua_luc = ? WHERE id = ? AND chu_so_huu = ?",
                    (luc, hoi_thoai_id, chu_so_huu),
                )
        finally:
            ket_noi.close()
        return True

    # ------------------------------------------------------------------
    # Đọc
    # ------------------------------------------------------------------

    def liet_ke(self, chu_so_huu: str) -> List[Dict[str, str]]:
        """Danh sách hội thoại của một người, mới sửa xếp trước.

        Trả đúng ba trường mà giao diện đọc: `id`, `tieuDe`, `suaLuc`. Không trả
        `chu_so_huu` ra ngoài — giao diện không cần nó, và một trường không gửi đi
        là một trường không thể lộ.
        """
        if not chu_so_huu:
            return []
        ket_noi = self._ket_noi()
        try:
            hang = ket_noi.execute(
                "SELECT id, tieu_de, sua_luc FROM hoi_thoai "
                "WHERE chu_so_huu = ? ORDER BY sua_luc DESC, id DESC",
                (chu_so_huu,),
            ).fetchall()
        finally:
            ket_noi.close()
        return [
            {"id": h["id"], "tieuDe": h["tieu_de"], "suaLuc": h["sua_luc"]}
            for h in hang
        ]

    def doc(self, hoi_thoai_id: str, chu_so_huu: str) -> Optional[Dict[str, Any]]:
        """Đọc một hội thoại CỦA NGƯỜI NÀY. Trả None cho cả hai ca không được đọc."""
        if not la_ma_hop_le(hoi_thoai_id) or not chu_so_huu:
            return None
        ket_noi = self._ket_noi()
        try:
            hang = ket_noi.execute(
                "SELECT id, tieu_de FROM hoi_thoai WHERE id = ? AND chu_so_huu = ?",
                (hoi_thoai_id, chu_so_huu),
            ).fetchone()
            if hang is None:
                return None
            # Điều kiện sở hữu lặp lại ở cả truy vấn tin nhắn. Thừa một phép nối,
            # nhưng nó làm câu lệnh này an toàn kể cả khi ai đó gọi thẳng nó.
            tin = ket_noi.execute(
                """
                SELECT t.vai_tro, t.noi_dung, t.mo_hinh, t.trich_dan
                  FROM tin_nhan t
                  JOIN hoi_thoai h ON h.id = t.hoi_thoai_id
                 WHERE t.hoi_thoai_id = ? AND h.chu_so_huu = ?
                 ORDER BY t.stt ASC
                """,
                (hoi_thoai_id, chu_so_huu),
            ).fetchall()
        finally:
            ket_noi.close()
        return {
            "id": hang["id"],
            "tieuDe": hang["tieu_de"],
            "tinNhan": [
                {
                    "vaiTro": t["vai_tro"],
                    "noiDung": t["noi_dung"],
                    "moHinh": t["mo_hinh"],
                    "trichDan": _doc_trich_dan(t["trich_dan"]),
                }
                for t in tin
            ],
        }

    def dem(self, chu_so_huu: Optional[str] = None) -> int:
        """Đếm hội thoại — của một người, hoặc của cả kho khi `chu_so_huu` là None.

        Có hàm này vì bài tự kiểm cần ĐO rằng một lượt xoá bị từ chối thật sự không
        xoá gì. Một phép thử chỉ nhìn mã HTTP 404 sẽ ĐẠT kể cả khi hàng đã biến mất.
        """
        ket_noi = self._ket_noi()
        try:
            if chu_so_huu is None:
                hang = ket_noi.execute("SELECT COUNT(*) AS n FROM hoi_thoai").fetchone()
            else:
                hang = ket_noi.execute(
                    "SELECT COUNT(*) AS n FROM hoi_thoai WHERE chu_so_huu = ?",
                    (chu_so_huu,),
                ).fetchone()
        finally:
            ket_noi.close()
        return int(hang["n"])

    # ------------------------------------------------------------------
    # Xoá
    # ------------------------------------------------------------------

    def xoa(self, hoi_thoai_id: str, chu_so_huu: str) -> bool:
        """Xoá hội thoại CỦA NGƯỜI NÀY. Trả False cho cả "không có" lẫn "của người khác".

        `chu_so_huu` là THAM SỐ BẮT BUỘC và đi thẳng vào WHERE của cả hai câu lệnh
        DELETE. Không tồn tại đường xoá vô điều kiện trong tệp này — đó là điểm
        chính, xem phần đầu tệp.

        Hai câu lệnh (tin nhắn trước, hội thoại sau) tuy đã có `ON DELETE CASCADE`
        đứng sau lưng: cascade chỉ chạy khi `PRAGMA foreign_keys` đang bật, mà pragma
        ấy phải bật lại trên từng kết nối. Một ngày nào đó một kết nối quên bật thì
        cascade im lặng không chạy và tin nhắn ở lại. Câu lệnh tường minh không phụ
        thuộc vào pragma, và nó cũng mang điều kiện sở hữu.
        """
        if not la_ma_hop_le(hoi_thoai_id) or not chu_so_huu:
            # Ra trước khi mở kết nối: một mã rác không được phép chạm tới đĩa.
            return False
        ket_noi = self._ket_noi()
        try:
            with ket_noi:
                ket_noi.execute(
                    """
                    DELETE FROM tin_nhan
                     WHERE hoi_thoai_id IN (
                           SELECT id FROM hoi_thoai WHERE id = ? AND chu_so_huu = ?
                     )
                    """,
                    (hoi_thoai_id, chu_so_huu),
                )
                con_tro = ket_noi.execute(
                    "DELETE FROM hoi_thoai WHERE id = ? AND chu_so_huu = ?",
                    (hoi_thoai_id, chu_so_huu),
                )
                return con_tro.rowcount == 1
        finally:
            ket_noi.close()


def cat_tieu_de(van: str) -> str:
    """Rút tiêu đề hội thoại từ câu hỏi đầu tiên.

    Gộp mọi khoảng trắng về một dấu cách: câu hỏi dán từ tài liệu thường có xuống
    dòng, và một tiêu đề nhiều dòng làm vỡ hàng trong thanh bên.
    """
    gon = " ".join(str(van or "").split())
    if not gon:
        return "Hội thoại mới"
    if len(gon) <= DAI_TIEU_DE:
        return gon
    return gon[: DAI_TIEU_DE - 1].rstrip() + "…"


def _doc_trich_dan(van: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """Giải mã cột trích dẫn. Hỏng thì trả None chứ không làm đứt cả hội thoại.

    Một hàng JSON hỏng trong CSDL không nên làm người dùng mất luôn quyền đọc lại
    câu trả lời — phần chữ vẫn còn nguyên và vẫn đáng đọc.
    """
    if not van:
        return None
    try:
        gia_tri = json.loads(van)
    except (ValueError, TypeError):
        return None
    if isinstance(gia_tri, list):
        return gia_tri
    return None
