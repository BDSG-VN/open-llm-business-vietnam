#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhan/mcp.py — PHƠI NHÂN RA NGOÀI DƯỚI DẠNG MỘT MÁY CHỦ MCP (JSON-RPC qua stdio).

QUYẾT ĐỊNH KIẾN TRÚC SỐ 1, VIẾT THÀNH MÃ
----------------------------------------
MCP là RANH GIỚI LỜI GỌI HỆ THỐNG của hệ điều hành này. Không phải REST, không
phải một API cắm trình cắm riêng. Lý do: MCP là thứ mô hình ĐÃ NÓI sẵn, nên lấy
nó làm ranh giới thì mọi máy khách biết MCP đều là một cái vỏ hợp lệ — giao diện
trò chuyện của chính kho này, một trợ lý khác, hay một kịch bản chạy nền. Còn
một công cụ MCP thì đóng đúng vai một lời gọi hệ thống: có chữ ký, có quyền, ghi
nhật ký được.

Tệp này CỐ Ý mỏng. Nó không quyết định gì cả — nó dịch JSON-RPC thành lời gọi
`Nhan.goi` và dịch ngược kết quả. Mọi quyết định nằm ở `dinh_tuyen`, `quyen`,
`han_muc`. Nếu một ngày cần thêm ranh giới thứ hai (ống dẫn HTTP chẳng hạn) thì
nó cũng mỏng như vậy, và không được phép có luật riêng.

DANH TÍNH TRÊN MỘT ỐNG DẪN KHÔNG CÓ TIÊU ĐỀ
-------------------------------------------
stdio không mang theo tiêu đề xác thực nào. Nên danh tính được giải MỘT LẦN ở
bước `initialize`, bằng một hàm tiêm vào (`giai_danh_tinh`) — hàm ấy đọc chứng
thư ở đâu là việc của bên triển khai: tham số `initialize`, biến môi trường do
tiến trình cha đặt, hay một tệp chỉ chủ tiến trình đọc được.

Không giải được ⇒ `self.danh_tinh = None`, và:
  · `tools/list`  trả DANH SÁCH RỖNG
  · `tools/call`  trả lỗi "không xác định được danh tính"
`initialize` VẪN thành công. Cố ý: một máy khách MCP bị đá ra ngay từ bắt tay
thường chỉ hiện "máy chủ không chạy", còn bắt tay xong rồi thấy không có công cụ
nào kèm câu giải thích thì người dùng biết đường đi sửa. Đây KHÔNG phải đường
lùi im lặng — không có công cụ nào chạy cả.

VÌ SAO `tools/list` LỌC THEO QUYỀN
----------------------------------
Yêu cầu nói rõ, và lý do đúng: liệt kê hết rồi từ chối lúc gọi là bày người dùng
đi một vòng vô ích. Với một mô hình ngôn ngữ ở đầu kia thì nó còn đốt lượt gọi
để thử lại. Danh sách ở đây tính theo thời điểm hỏi, nên khi cổng ghi của nhân
đóng thì công cụ ghi biến mất khỏi danh sách.

⚠ MỘT SỰ THẬT PHẢI NÓI THẲNG VỀ MÔ HÌNH RIÊNG CỦA BDSG
------------------------------------------------------
Trọng số đầu tiên do BDSG huấn luyện (26/09/2026) có 26.878.464 tham số. Một mô
hình cỡ ấy KHÔNG gọi công cụ được một cách đáng tin: nó không giữ nổi định dạng
lời gọi qua nhiều lượt. Cho nên máy chủ MCP này, tính đến hôm nay, phục vụ các
máy khách khác — chứ không phải mô hình 26,88 triệu tham số của chính dự án.
Ranh giới MCP vẫn là chỗ đúng để đặt, vì nó không đổi khi mô hình lớn lên; nhưng
hứa ngược lại chính là kiểu "mở giả" mà kho này lập ra để chống.

PHIÊN BẢN GIAO THỨC
-------------------
`PHIEN_BAN_GIAO_THUC` là phiên bản máy chủ này KHAI. Nó chưa được đối chiếu với
một máy khách thật trong kho này tính đến 26/09/2026 — bài tự kiểm chỉ kiểm hình
dạng thông điệp, không kiểm tính tương thích.

Viết ngày 26/09/2026.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict, List, Optional

from .danh_tinh import DanhTinh
from .dinh_tuyen import Nhan

PHIEN_BAN_GIAO_THUC = "2025-06-18"

# Mã lỗi JSON-RPC 2.0 chuẩn.
LOI_PHAN_TICH = -32700
LOI_YEU_CAU_SAI = -32600
LOI_KHONG_CO_PHUONG_THUC = -32601
LOI_THAM_SO_SAI = -32602
LOI_NOI_BO = -32603


def _khong_co_danh_tinh(_params: Dict[str, Any]) -> Optional[DanhTinh]:
    """Hàm giải danh tính MẶC ĐỊNH: luôn trả None.

    Mặc định phải là "không biết anh là ai", không phải "cho qua đi". Bên triển
    khai muốn máy chủ làm được việc thì phải tiêm hàm của mình vào — và lúc ấy
    họ buộc phải nghĩ xem chứng thư đến từ đâu.
    """
    return None


class MayChuMCP:
    """Phơi một `Nhan` ra ngoài theo JSON-RPC 2.0 trên stdio."""

    def __init__(
        self,
        nhan: Nhan,
        giai_danh_tinh: Callable[[Dict[str, Any]], Optional[DanhTinh]] = _khong_co_danh_tinh,
        ten_may: str = "bdsg-os-nhan",
        phien_ban: str = "0.1.0",
    ) -> None:
        self.nhan = nhan
        self.giai_danh_tinh = giai_danh_tinh
        self.ten_may = ten_may
        self.phien_ban = phien_ban
        self.danh_tinh: Optional[DanhTinh] = None
        self.da_bat_tay = False
        self.ly_do_danh_tinh = "chưa bắt tay"

    # -- dựng thông điệp ------------------------------------------------------

    @staticmethod
    def _tra_loi(ma_id: Any, ket_qua: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": ma_id, "result": ket_qua}

    @staticmethod
    def _tra_loi_loi(ma_id: Any, ma_loi: int, thong_diep: str, du_lieu: Any = None) -> Dict[str, Any]:
        loi: Dict[str, Any] = {"code": ma_loi, "message": thong_diep}
        if du_lieu is not None:
            loi["data"] = du_lieu
        return {"jsonrpc": "2.0", "id": ma_id, "error": loi}

    @staticmethod
    def _noi_dung_van_ban(van_ban: str, la_loi: bool = False) -> Dict[str, Any]:
        return {"content": [{"type": "text", "text": van_ban}], "isError": bool(la_loi)}

    # -- xử lý một gói tin ----------------------------------------------------

    def xu_ly(self, goi_tin: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trả về gói tin đáp, hoặc None nếu đây là thông báo (không có `id`).

        Tách khỏi vòng lặp stdio để bài tự kiểm gọi thẳng được, không cần ống
        dẫn, không cần tiến trình con. Một máy chủ chỉ kiểm được khi đã chạy
        thật là một máy chủ gần như không được kiểm.
        """
        if not isinstance(goi_tin, dict):
            return self._tra_loi_loi(None, LOI_YEU_CAU_SAI, "gói tin không phải đối tượng JSON")

        ma_id = goi_tin.get("id")
        phuong_thuc = goi_tin.get("method")
        params = goi_tin.get("params") or {}
        if not isinstance(params, dict):
            return self._tra_loi_loi(ma_id, LOI_THAM_SO_SAI, "params phải là đối tượng")
        la_thong_bao = "id" not in goi_tin

        if not isinstance(phuong_thuc, str):
            return None if la_thong_bao else self._tra_loi_loi(
                ma_id, LOI_YEU_CAU_SAI, "thiếu trường method"
            )

        if phuong_thuc == "initialize":
            return self._initialize(ma_id, params)

        if phuong_thuc.startswith("notifications/"):
            # Thông báo: KHÔNG đáp. Đáp một thông báo là lỗi giao thức, và một số
            # máy khách sẽ treo vì nhận đáp cho thứ chúng không chờ.
            return None

        if phuong_thuc == "ping":
            return None if la_thong_bao else self._tra_loi(ma_id, {})

        if phuong_thuc == "tools/list":
            return self._tools_list(ma_id)

        if phuong_thuc == "tools/call":
            return self._tools_call(ma_id, params)

        return None if la_thong_bao else self._tra_loi_loi(
            ma_id, LOI_KHONG_CO_PHUONG_THUC, "không hỗ trợ phương thức %r" % (phuong_thuc,)
        )

    # -- từng phương thức -----------------------------------------------------

    def _initialize(self, ma_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            dt = self.giai_danh_tinh(params)
        except Exception as loi:
            # Hàm giải danh tính là mã của bên triển khai. Nó nổ ⇒ KHÔNG có danh
            # tính, chứ không phải ⇒ cho qua.
            dt = None
            self.ly_do_danh_tinh = "hàm giải danh tính nổ: %s" % type(loi).__name__
        else:
            if dt is None:
                self.ly_do_danh_tinh = "không giải được danh tính từ tham số initialize"
            elif not isinstance(dt, DanhTinh):
                self.ly_do_danh_tinh = "hàm giải danh tính trả về %s chứ không phải DanhTinh" % type(dt).__name__
                dt = None
            else:
                self.ly_do_danh_tinh = "danh tính %r qua nguồn %r" % (dt.ma, dt.nguon)

        self.danh_tinh = dt
        self.da_bat_tay = True

        so_cong_cu = len(self.nhan.danh_sach_cong_cu(dt))
        return self._tra_loi(
            ma_id,
            {
                "protocolVersion": PHIEN_BAN_GIAO_THUC,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": self.ten_may, "version": self.phien_ban},
                # `instructions` là chỗ MCP dành cho máy chủ nói với mô hình. Nói
                # thẳng tình trạng danh tính ở đây, vì nếu im thì mô hình sẽ đoán
                # là mình gọi được và đi thử.
                "instructions": (
                    "Nhân BDSG OS. Trạng thái danh tính: %s. Số công cụ bạn được "
                    "gọi: %d. Mặc định của nhân là CHỈ ĐỌC; công cụ ghi chỉ hiện "
                    "ra khi cổng ghi đang mở và vai của bạn được cấp tường minh."
                    % (self.ly_do_danh_tinh, so_cong_cu)
                ),
            },
        )

    def _tools_list(self, ma_id: Any) -> Dict[str, Any]:
        cac = self.nhan.danh_sach_cong_cu(self.danh_tinh)
        tools: List[Dict[str, Any]] = []
        for cc in cac:
            tools.append(
                {
                    "name": cc["ten"],
                    "description": cc["mo_ta"],
                    "inputSchema": cc["luoc_do"],
                    # `readOnlyHint` chỉ là GỢI Ý cho máy khách hiển thị. Việc
                    # chặn thật nằm ở `quyen.py` + cổng ghi. Đừng bao giờ để một
                    # phép kiểm an toàn phụ thuộc vào một trường tên là *Hint.
                    "annotations": {"readOnlyHint": not cc["ghi"]},
                }
            )
        return self._tra_loi(ma_id, {"tools": tools})

    def _tools_call(self, ma_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        ten = params.get("name")
        tham_so = params.get("arguments") or {}
        if not isinstance(ten, str) or not ten:
            return self._tra_loi_loi(ma_id, LOI_THAM_SO_SAI, "thiếu tên công cụ")
        if not isinstance(tham_so, dict):
            return self._tra_loi_loi(ma_id, LOI_THAM_SO_SAI, "arguments phải là đối tượng")

        if self.danh_tinh is None:
            # Trả về dạng KẾT QUẢ có isError, không phải lỗi JSON-RPC: lỗi giao
            # thức là chuyện của ống dẫn, còn "bạn không được phép" là chuyện của
            # ứng dụng và mô hình cần đọc được nó như một câu trả lời.
            # Vẫn đi qua nhân để chuyện này có một dòng nhật ký.
            kq = self.nhan.goi(None, ten, tham_so)
            return self._tra_loi(
                ma_id,
                self._noi_dung_van_ban(
                    "Từ chối: không xác định được danh tính (%s). Mã theo dõi: %s"
                    % (self.ly_do_danh_tinh, kq.ma_theo_doi),
                    la_loi=True,
                ),
            )

        kq = self.nhan.goi(self.danh_tinh, ten, tham_so)
        if not kq.ok:
            return self._tra_loi(
                ma_id,
                self._noi_dung_van_ban(
                    "%s (mã theo dõi: %s)" % (kq.ly_do, kq.ma_theo_doi), la_loi=True
                ),
            )

        try:
            van_ban = json.dumps(kq.ket_qua, ensure_ascii=False, default=str, indent=None)
        except Exception:
            van_ban = str(kq.ket_qua)
        return self._tra_loi(ma_id, self._noi_dung_van_ban(van_ban, la_loi=False))

    # -- vòng lặp stdio -------------------------------------------------------

    def phuc_vu(self, dong_vao=None, dong_ra=None) -> int:
        """Đọc từng dòng JSON từ stdin, ghi từng dòng JSON ra stdout.

        ⚠ stdout CHỈ dành cho giao thức. Nhật ký mặc định đi ra stderr (xem
        `nhat_ky.py`); in bất cứ thứ gì khác vào stdout là bẻ gãy ống dẫn, và
        triệu chứng ("máy khách không hiểu gì") nằm rất xa nguyên nhân.
        """
        dong_vao = sys.stdin if dong_vao is None else dong_vao
        dong_ra = sys.stdout if dong_ra is None else dong_ra

        for dong in dong_vao:
            dong = dong.strip()
            if not dong:
                continue
            try:
                goi_tin = json.loads(dong)
            except Exception as loi:
                dap = self._tra_loi_loi(None, LOI_PHAN_TICH, "JSON hỏng: %s" % (loi,))
            else:
                try:
                    dap = self.xu_ly(goi_tin)
                except Exception as loi:
                    # Lưới cuối cùng. Một máy chủ MCP chết vì một gói tin méo là
                    # một máy chủ bị hạ bằng một dòng văn bản.
                    dap = self._tra_loi_loi(
                        goi_tin.get("id") if isinstance(goi_tin, dict) else None,
                        LOI_NOI_BO,
                        "lỗi nội bộ: %s" % type(loi).__name__,
                    )
            if dap is not None:
                dong_ra.write(json.dumps(dap, ensure_ascii=False) + "\n")
                dong_ra.flush()
        return 0
