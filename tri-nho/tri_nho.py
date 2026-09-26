#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tri_nho.py — TRÍ NHỚ RIÊNG cho từng agent, quy mô dân số.

=============================================================================
BÀI TOÁN
=============================================================================
Một agent cho mỗi người Việt Nam. Mỗi agent có trí nhớ riêng, và trí nhớ của
người này TUYỆT ĐỐI không được lọt sang người kia.

Số liệu quyết định thiết kế (tính 26/09/2026):
  · 100 triệu agent × ~20 KB trí nhớ = **2 TB**. Lớn, nhưng là một CSDL bình
    thường — không phải điều bất khả.
  · Nhúng vector cho ngần ấy trí nhớ thì cần **12,3 TB chỉ riêng vector**, và
    cần GPU để sinh chúng. BDSG CHƯA CÓ GPU.

=============================================================================
BA QUYẾT ĐỊNH, và vì sao
=============================================================================
1. KHÔNG TẠO SẴN 100 TRIỆU AGENT. Tạo khi một người THẬT xuất hiện.
   Tạo sẵn 100 triệu hồ sơ rỗng là trả tiền lưu trữ cho 98,9 triệu bản ghi
   không có ai đứng sau. Nền tảng THIẾT KẾ cho 100 triệu; số agent thật bằng
   số người thật đã tới. Năm đầu 10.000 người = 0,2 GB.

2. TRUY HỒI BẰNG BM25, KHÔNG BẰNG VECTOR.
   Đây không phải lựa chọn tạm trong lúc chờ GPU — nó là lựa chọn đúng ở quy
   mô này. SQLite FTS5 (và Postgres) làm BM25 sẵn, chạy trên CPU, không cần
   mô hình nhúng, không tốn 12 TB.
   Ý này học từ `agentmemory` (rohitg00/agentmemory, Apache-2.0): dự án ấy có
   "chế độ không khoá" dùng BM25 thay cho nhúng vector. BDSG KHÔNG sao chép mã
   của họ — kho ấy là bộ nhớ CỤC BỘ cho MỘT lập trình viên (chạy ở cổng
   3111–3113 trên máy cá nhân), không phải nền tảng nhiều người thuê. Thứ lấy
   được là Ý TƯỞNG, và ghi công ở đây là để nói đúng chuyện đó.

3. CÁCH LY LÀ MỘT ĐIỀU KIỆN TRONG CHÍNH CÂU TRUY VẤN.
   Mọi hàm đọc đều nhận `ma_agent` và đưa nó vào mệnh đề WHERE. KHÔNG có hàm
   nào trả về trí nhớ rồi mới lọc ở tầng trên. Lý do: một phép lọc sau khi
   truy vấn là một phép lọc CÓ THỂ QUÊN, và quên một lần là lộ trí nhớ của một
   người cho người khác. Dự án này đã dính đúng họ lỗi ấy một lần (phép kiểm
   quyền xoá vẫn xanh khi chủ sở hữu là None), nên ở đây cách ly nằm trong SQL.
"""
import hashlib
import os
import re
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

TRAN_NOI_DUNG = 4_000          # ký tự mỗi mẩu trí nhớ
TRAN_MAU_MOI_AGENT = 10_000    # chặn một agent phình vô hạn


class LoiTriNho(RuntimeError):
    pass


def _ma_moi() -> str:
    return uuid.uuid4().hex


MAU_MA_AGENT = re.compile(r"\A[a-z0-9][a-z0-9_.\-]{0,127}\Z")

# Tiền tố của KHOÁ PHẠM VI. Cố ý là một chuỗi không ai gõ ra được trong câu hỏi
# tiếng Việt, và mọi từ dạng này bị LỌC KHỎI câu hỏi của người dùng trước khi
# truy vấn — nếu không, gõ trúng khoá của người khác là đọc được trí nhớ của họ.
TIEN_TO_PHAM_VI = "zzpv"


def khoa_pham_vi(ma_agent: str) -> str:
    """Một token duy nhất cho mỗi agent, ĐƯA VÀO CHỈ MỤC để thu hẹp tìm kiếm.

    VÌ SAO CẦN — ĐO ĐƯỢC 26/09/2026:
      Bản đầu lọc bằng `AND ma_agent = ?` ở mệnh đề WHERE. Cách ly thì ĐÚNG
      (đo 900/900), nhưng FTS5 không dùng được điều kiện ấy để thu hẹp: nó khớp
      chữ trên TOÀN BỘ chỉ mục rồi mới lọc. Kết quả đo ở 50.000 agent /
      150.000 mẩu: **1.933 ms mỗi lượt tra**. Ở quy mô dân số thì không dùng
      được.
      Nay khoá phạm vi nằm TRONG biểu thức MATCH, nên FTS5 thu hẹp trước bằng
      chính chỉ mục đảo của nó.

    Điều kiện WHERE cũ VẪN GIỮ. Hai lớp cho cùng một việc là cố ý: khoá phạm vi
    là để NHANH, mệnh đề WHERE là để ĐÚNG. Nếu ai đó sửa cách sinh khoá và làm
    hỏng nó, lớp thứ hai vẫn chặn rò rỉ — chỉ chậm đi.
    """
    return TIEN_TO_PHAM_VI + re.sub(r"[^a-z0-9]", "0", ma_agent)


def kiem_ma_agent(ma: str) -> str:
    """Mã agent phải hợp lệ TRƯỚC khi chạm CSDL.

    Neo cuối là \\Z chứ không phải $ — trong Python `$` khớp cả ngay trước một
    ký tự xuống dòng cuối chuỗi, nên "nguoi-01\\n" sẽ lọt. Cùng một lỗi đã sửa
    trong nhan/ ngày 26/09/2026.
    """
    if not isinstance(ma, str) or not MAU_MA_AGENT.match(ma):
        raise LoiTriNho("mã agent %r không hợp lệ" % (ma,))
    return ma


class KhoTriNho:
    """Kho trí nhớ nhiều-người-thuê. Một tệp CSDL, nhiều agent, cách ly bằng SQL."""

    def __init__(self, duong_dan: str = ":memory:") -> None:
        self.db = sqlite3.connect(duong_dan)
        self.db.row_factory = sqlite3.Row
        self._dung_bang()

    def _dung_bang(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent (
                ma          TEXT PRIMARY KEY,
                persona     TEXT NOT NULL DEFAULT '',
                tao_luc     REAL NOT NULL,
                cham_luc    REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mau (
                id          TEXT PRIMARY KEY,
                ma_agent    TEXT NOT NULL REFERENCES agent(ma) ON DELETE CASCADE,
                noi_dung    TEXT NOT NULL,
                nhan        TEXT NOT NULL DEFAULT '',
                bam         TEXT NOT NULL DEFAULT '',
                tao_luc     REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS mau_theo_agent ON mau(ma_agent, tao_luc DESC);
            -- Chỉ mục cho nho_mot_lan(): thiếu nó thì mỗi lần ghi là một phép
            -- quét, và 1,08 triệu lần quét biến việc 20 phút thành việc vài ngày.
            CREATE INDEX IF NOT EXISTS mau_theo_bam ON mau(ma_agent, bam);
            """
        )
        # FTS5 = BM25 sẵn có, chạy trên CPU. `ma_agent` là cột UNINDEXED: nó
        # đi theo bản ghi để lọc được, nhưng KHÔNG vào chỉ mục chữ — nếu không,
        # gõ trúng mã của người khác cũng ra kết quả.
        self.db.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS mau_tim USING fts5(
                pham_vi, noi_dung, nhan, ma_agent UNINDEXED, id UNINDEXED,
                tokenize='unicode61'
            );
            """
        )
        self.db.commit()

    # -- vòng đời agent ------------------------------------------------------

    def mo_agent(self, ma: str, persona: str = "") -> Dict[str, Any]:
        """Lấy agent, TẠO NẾU CHƯA CÓ. Đây là chỗ hiện thực 'tạo theo nhu cầu'.

        Gọi hàm này cho một người chưa từng tới thì agent của họ ra đời ngay lúc
        đó. Không ai phải tạo sẵn 100 triệu bản ghi rỗng.
        """
        kiem_ma_agent(ma)
        gio = time.time()
        cur = self.db.execute("SELECT ma, persona, tao_luc FROM agent WHERE ma = ?", (ma,))
        r = cur.fetchone()
        if r is None:
            self.db.execute(
                "INSERT INTO agent (ma, persona, tao_luc, cham_luc) VALUES (?, ?, ?, ?)",
                (ma, persona, gio, gio),
            )
            self.db.commit()
            return {"ma": ma, "persona": persona, "tao_luc": gio, "moi": True}
        self.db.execute("UPDATE agent SET cham_luc = ? WHERE ma = ?", (gio, ma))
        self.db.commit()
        return {"ma": r["ma"], "persona": r["persona"], "tao_luc": r["tao_luc"], "moi": False}

    def so_agent(self) -> int:
        return self.db.execute("SELECT COUNT(*) c FROM agent").fetchone()["c"]

    # -- ghi nhớ -------------------------------------------------------------

    def nho(self, ma_agent: str, noi_dung: str, nhan: str = "") -> str:
        kiem_ma_agent(ma_agent)
        noi_dung = (noi_dung or "").strip()
        if not noi_dung:
            raise LoiTriNho("không ghi một mẩu trí nhớ rỗng")
        if len(noi_dung) > TRAN_NOI_DUNG:
            noi_dung = noi_dung[:TRAN_NOI_DUNG]
        if self.db.execute("SELECT ma FROM agent WHERE ma = ?", (ma_agent,)).fetchone() is None:
            raise LoiTriNho("agent %r chưa tồn tại — gọi mo_agent() trước" % (ma_agent,))
        dem = self.db.execute(
            "SELECT COUNT(*) c FROM mau WHERE ma_agent = ?", (ma_agent,)).fetchone()["c"]
        if dem >= TRAN_MAU_MOI_AGENT:
            raise LoiTriNho(
                "agent %r đã có %d mẩu, chạm trần %d — một trí nhớ phình vô hạn thì "
                "truy hồi chậm dần rồi vô dụng, và không ai thấy lúc nó bắt đầu hỏng"
                % (ma_agent, dem, TRAN_MAU_MOI_AGENT))
        mid = _ma_moi()
        gio = time.time()
        bam = hashlib.blake2b(noi_dung.encode("utf-8"), digest_size=16).hexdigest()
        self.db.execute(
            "INSERT INTO mau (id, ma_agent, noi_dung, nhan, bam, tao_luc) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (mid, ma_agent, noi_dung, nhan, bam, gio))
        self.db.execute(
            "INSERT INTO mau_tim (pham_vi, noi_dung, nhan, ma_agent, id) "
            "VALUES (?, ?, ?, ?, ?)",
            (khoa_pham_vi(ma_agent), noi_dung, nhan, ma_agent, mid))
        self.db.commit()
        return mid

    def nho_mot_lan(self, ma_agent: str, noi_dung: str, nhan: str = "") -> Optional[str]:
        """Ghi một mẩu CHỈ KHI agent chưa có mẩu y hệt. Trả None nếu đã có.

        VÌ SAO CẦN — TÍNH BẤT BIẾN KHI CHẠY LẠI:
          Nạp 1,08 triệu doanh nghiệp là việc hàng chục phút. Nó sẽ đứt, và sẽ
          phải chạy lại. `nho()` thì lần nào cũng ghi, nên chạy lại hai lần là
          mỗi agent có hai bản mẩu giống hệt — truy hồi trả về hai kết quả
          trùng, và không ai thấy lúc nó bắt đầu sai vì tra cứu vẫn "có kết
          quả". Đúng họ lỗi hỏng-mà-không-báo.

          So sánh bằng BĂM nội dung chứ không bằng LIKE: nội dung có thể dài,
          và so chuỗi dài trên mỗi lần ghi là tự tạo một phép quét toàn bảng.
        """
        kiem_ma_agent(ma_agent)
        noi_dung = (noi_dung or "").strip()
        if not noi_dung:
            raise LoiTriNho("không ghi một mẩu trí nhớ rỗng")
        if len(noi_dung) > TRAN_NOI_DUNG:
            noi_dung = noi_dung[:TRAN_NOI_DUNG]
        bam = hashlib.blake2b(noi_dung.encode("utf-8"), digest_size=16).hexdigest()
        co = self.db.execute(
            "SELECT id FROM mau WHERE ma_agent = ? AND bam = ? LIMIT 1",
            (ma_agent, bam)).fetchone()
        if co is not None:
            return None
        return self.nho(ma_agent, noi_dung, nhan)

    # -- nhớ lại -------------------------------------------------------------

    def nho_lai(self, ma_agent: str, truy_van: str, so_luong: int = 5) -> List[Dict[str, Any]]:
        """Truy hồi BM25 TRONG PHẠM VI MỘT AGENT.

        `ma_agent = ?` nằm ngay trong câu truy vấn, KHÔNG lọc sau. Đây là điều
        kiện bảo mật quan trọng nhất của tệp này: một phép lọc ở tầng trên là
        một phép lọc có thể quên, và quên một lần là lộ trí nhớ của một người.
        """
        kiem_ma_agent(ma_agent)
        truy_van = (truy_van or "").strip()
        if not truy_van:
            return []
        # Chuỗi người dùng KHÔNG đưa thẳng vào cú pháp MATCH: dấu nháy kép và
        # các toán tử của FTS5 sẽ làm câu truy vấn nổ hoặc đổi nghĩa. Bọc từng
        # từ trong nháy kép rồi nối — cú pháp ấy FTS5 hiểu là "cụm từ".
        tu = [t for t in re.split(r"\W+", truy_van, flags=re.UNICODE) if t]
        # BỎ mọi từ trông như khoá phạm vi. Thiếu dòng này thì người dùng gõ
        # đúng khoá của người khác là đọc được trí nhớ của họ — khoá phạm vi
        # vốn sinh ra để NHANH, không được biến thành một cửa vào.
        tu = [t for t in tu if not t.lower().startswith(TIEN_TO_PHAM_VI)]
        if not tu:
            return []
        mau = '"%s" AND (%s)' % (
            khoa_pham_vi(ma_agent),
            " OR ".join('"%s"' % t.replace('"', '""') for t in tu))
        try:
            cur = self.db.execute(
                "SELECT id, noi_dung, nhan, bm25(mau_tim) diem FROM mau_tim "
                "WHERE mau_tim MATCH ? AND ma_agent = ? ORDER BY diem LIMIT ?",
                (mau, ma_agent, int(so_luong)))
        except sqlite3.OperationalError as loi:
            raise LoiTriNho("truy vấn không hợp lệ: %s" % (loi,))
        return [{"id": r["id"], "noi_dung": r["noi_dung"], "nhan": r["nhan"],
                 "diem": r["diem"]} for r in cur.fetchall()]

    def gan_day(self, ma_agent: str, so_luong: int = 5) -> List[Dict[str, Any]]:
        kiem_ma_agent(ma_agent)
        cur = self.db.execute(
            "SELECT id, noi_dung, nhan, tao_luc FROM mau WHERE ma_agent = ? "
            "ORDER BY tao_luc DESC LIMIT ?", (ma_agent, int(so_luong)))
        return [dict(r) for r in cur.fetchall()]

    def dem_mau(self, ma_agent: str) -> int:
        kiem_ma_agent(ma_agent)
        return self.db.execute(
            "SELECT COUNT(*) c FROM mau WHERE ma_agent = ?", (ma_agent,)).fetchone()["c"]

    # -- quên ----------------------------------------------------------------

    def quen_mau(self, ma_agent: str, id_mau: str) -> bool:
        """Xoá một mẩu. Quyền sở hữu nằm TRONG câu lệnh xoá.

        `AND ma_agent = ?` ở đây không thừa: thiếu nó thì ai biết một id là xoá
        được mẩu của người khác. Dự án đã dính đúng lỗi này ở một tuyến xoá hội
        thoại, nên nó được viết vào ngay từ đầu chứ không vá sau.
        """
        kiem_ma_agent(ma_agent)
        cur = self.db.execute(
            "DELETE FROM mau WHERE id = ? AND ma_agent = ?", (id_mau, ma_agent))
        self.db.execute(
            "DELETE FROM mau_tim WHERE id = ? AND ma_agent = ?", (id_mau, ma_agent))
        self.db.commit()
        return cur.rowcount > 0

    def quen_het(self, ma_agent: str) -> int:
        """Xoá TOÀN BỘ trí nhớ của một agent — quyền rút lại của người dùng.

        Nghị định 13/2023/NĐ-CP cho chủ thể dữ liệu quyền yêu cầu xoá. Một nền
        tảng nhớ mà không quên được thì không tuân thủ được, nên đường này phải
        có từ ngày đầu chứ không thêm khi bị hỏi.
        """
        kiem_ma_agent(ma_agent)
        n = self.dem_mau(ma_agent)
        self.db.execute("DELETE FROM mau WHERE ma_agent = ?", (ma_agent,))
        self.db.execute("DELETE FROM mau_tim WHERE ma_agent = ?", (ma_agent,))
        self.db.commit()
        return n

    def xoa_agent(self, ma_agent: str) -> bool:
        kiem_ma_agent(ma_agent)
        self.quen_het(ma_agent)
        cur = self.db.execute("DELETE FROM agent WHERE ma = ?", (ma_agent,))
        self.db.commit()
        return cur.rowcount > 0
