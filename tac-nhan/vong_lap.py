#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vong_lap.py — VÒNG LẶP TÁC NHÂN: biến khung chat thành thực thi tác vụ.

=============================================================================
TỆP NÀY LÀ THỨ CÒN THIẾU
=============================================================================
`nhan/` đã trả lời được "ai đang hỏi, được làm gì, bao nhiêu, ghi lại ra sao".
`phuc-vu/` đã nối được tới mô hình. Thứ chưa có là cái vòng ở giữa: nhận một
câu hỏi, gọi công cụ NHIỀU LƯỢT, tự đọc kết quả, rồi báo cáo. Không có nó thì
chat.bdsg.vn là một ô chat; có nó thì nó thực thi được tác vụ.

=============================================================================
BẢY LUẬT CỦA VÒNG LẶP — mỗi luật có bài kiểm riêng
=============================================================================
1. MỌI LỜI GỌI ĐI QUA NHÂN. Vòng lặp KHÔNG giữ tham chiếu tới hàm công cụ và
   không có đường nào gọi thẳng. Nó chỉ biết `nhan.goi(...)`.
2. CÓ TRẦN LƯỢT. Hết trần thì DỪNG và NÓI RÕ đã dừng vì sao. Cắt ngang im lặng
   là kiểu hỏng tệ nhất: người dùng tưởng việc đã xong.
3. CÔNG CỤ KHÔNG TỒN TẠI → báo lại CÓ ÍCH (kèm danh sách công cụ có thật), chứ
   không sập và cũng không im lặng bỏ qua.
4. CÔNG CỤ NÉM LỖI → đưa lỗi về cho mô hình thử lại, NHƯNG đếm số lần lặp LẠI
   CÙNG MỘT LỖI và dừng khi vượt ngưỡng. Không đếm thì một mô hình bướng sẽ
   quay vòng tới hết trần.
5. HÀNH ĐỘNG GHI PHẢI QUA CỔNG XÁC NHẬN TÁCH RỜI. Vòng lặp KHÔNG được tự quyết
   thực hiện một việc không lùi được.
6. MỖI LƯỢT SINH MỘT SỰ KIỆN. Giao diện đọc chúng qua SSE; bản ghi phiên là
   cùng một dòng sự kiện ấy, nên thứ người dùng thấy và thứ được ghi lại KHÔNG
   THỂ lệch nhau.
7. KHÔNG TỰ LÀM LẠI VIỆC CỦA NHÂN. Vòng lặp không kiểm quyền, không đếm hạn
   mức, không ghi nhật ký công cụ. Làm lại là tạo ra một mô hình quyền thứ hai
   và không ai biết cái nào đang có hiệu lực.
"""
from typing import Any, Callable, Dict, List, Optional

# Nhập được CẢ HAI lối: như một gói (`from tac_nhan import ...`) và khi chạy
# thẳng tệp trong thư mục này (bài tự kiểm của kho chạy theo lối ấy). Thiếu một
# trong hai thì một nửa cách dùng gãy mà bên kia vẫn xanh.
try:
    from .phoi_cong_cu import TEN_CONG_CU_META, BoPhoiCongCu   # noqa: F401
except ImportError:  # pragma: no cover - lối chạy thẳng
    from phoi_cong_cu import TEN_CONG_CU_META, BoPhoiCongCu    # noqa: F401

TRAN_LUOT_MAC_DINH = 12
TRAN_LAP_LOI_MAC_DINH = 3


class LoiVongLap(RuntimeError):
    pass


class CanXacNhan(Exception):
    """Vòng lặp dừng vì gặp một hành động GHI chưa được duyệt.

    Là ngoại lệ chứ không phải giá trị trả về, để không một nhánh nào lỡ bỏ qua
    nó rồi chạy tiếp. Một hành động không lùi được mà "lỡ bỏ qua" thì không có
    đường sửa.
    """

    def __init__(self, ten_cong_cu: str, tham_so: Dict[str, Any], ma_theo_doi: str) -> None:
        super().__init__("cần xác nhận cho hành động ghi %r" % (ten_cong_cu,))
        self.ten_cong_cu = ten_cong_cu
        self.tham_so = tham_so
        self.ma_theo_doi = ma_theo_doi


class BanGhiPhien:
    """Dòng sự kiện của một phiên. Vừa là thứ giao diện hiện, vừa là thứ ghi lại."""

    def __init__(self) -> None:
        self.su_kien: List[Dict[str, Any]] = []

    def them(self, loai: str, **truong: Any) -> Dict[str, Any]:
        sk = {"loai": loai}
        sk.update(truong)
        self.su_kien.append(sk)
        return sk

    def cac_loai(self) -> List[str]:
        return [s["loai"] for s in self.su_kien]

    def dem(self, loai: str) -> int:
        return sum(1 for s in self.su_kien if s["loai"] == loai)


class VongLapTacNhan:
    """Vòng lặp tác nhân đặt TRÊN nhân.

    `mo_hinh` là một hàm: (tin_nhan, cong_cu) -> dict. Dict trả về phải có khoá
    `loai` bằng "chu" (trả lời bằng chữ, kết thúc) hoặc "goi_cong_cu" (kèm `ten`
    và `tham_so`). Giao diện hẹp như vậy là cố ý: nó cho phép cắm một mô hình
    giả có kịch bản vào bài kiểm mà không cần mạng.
    """

    def __init__(
        self,
        nhan: Any,
        mo_hinh: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]],
        bo_phoi: BoPhoiCongCu,
        tran_luot: int = TRAN_LUOT_MAC_DINH,
        tran_lap_loi: int = TRAN_LAP_LOI_MAC_DINH,
        cho_phep_ghi: bool = False,
    ) -> None:
        if tran_luot < 1:
            raise LoiVongLap("trần lượt phải ≥ 1")
        self.nhan = nhan
        self.mo_hinh = mo_hinh
        self.bo_phoi = bo_phoi
        self.tran_luot = tran_luot
        self.tran_lap_loi = tran_lap_loi
        self.cho_phep_ghi = cho_phep_ghi

    # -----------------------------------------------------------------------

    def chay(self, danh_tinh: Any, cau_hoi: str) -> BanGhiPhien:
        ban_ghi = BanGhiPhien()
        ban_ghi.them("bat_dau", cau_hoi=cau_hoi)
        tin_nhan: List[Dict[str, Any]] = [{"vai": "nguoi", "noi_dung": cau_hoi}]
        dem_loi: Dict[str, int] = {}

        for luot in range(1, self.tran_luot + 1):
            cong_cu = self.bo_phoi.ban_khai_cho_mo_hinh()
            try:
                y = self.mo_hinh(list(tin_nhan), cong_cu)
            except Exception as loi:
                ban_ghi.them("loi_mo_hinh", luot=luot,
                             loai_loi=type(loi).__name__, ly_do=str(loi)[:300])
                return ban_ghi

            if not isinstance(y, dict) or "loai" not in y:
                # Mô hình trả về thứ không đọc được. Nói lại cho nó ĐÚNG khuôn
                # cần có, thay vì sập — đây là dạng hỏng hay gặp nhất của mọi
                # vòng lặp tác nhân.
                ban_ghi.them("phan_hoi_hong", luot=luot, tho=repr(y)[:300])
                tin_nhan.append({"vai": "he", "noi_dung":
                                 "Phản hồi không đọc được. Trả về một đối tượng có "
                                 "khoá 'loai' là 'chu' hoặc 'goi_cong_cu'."})
                continue

            if y["loai"] == "chu":
                ban_ghi.them("tra_loi", luot=luot, noi_dung=y.get("noi_dung", ""))
                ban_ghi.them("xong", ly_do="mô hình đã trả lời", so_luot=luot)
                return ban_ghi

            if y["loai"] != "goi_cong_cu":
                ban_ghi.them("phan_hoi_hong", luot=luot, tho=repr(y)[:300])
                tin_nhan.append({"vai": "he", "noi_dung":
                                 "Loại %r không hợp lệ." % (y["loai"],)})
                continue

            ten = y.get("ten") or ""
            tham_so = y.get("tham_so") or {}
            ban_ghi.them("goi_cong_cu", luot=luot, ten=ten, tham_so=dict(tham_so))

            # --- công cụ meta: mở lĩnh vực. KHÔNG đi qua nhân vì nó không chạm
            #     vào nền tảng nào — nó chỉ đổi thứ mô hình NHÌN THẤY.
            if ten == TEN_CONG_CU_META:
                lv = tham_so.get("linh_vuc")
                try:
                    cau = self.bo_phoi.mo_linh_vuc(lv)
                except KeyError as loi:
                    cau = str(loi)
                ban_ghi.them("ket_qua_cong_cu", luot=luot, ten=ten, ok=True, ket_qua=cau)
                tin_nhan.append({"vai": "cong_cu", "ten": ten, "noi_dung": cau})
                continue

            # --- LUẬT 5: hành động GHI phải qua cổng xác nhận tách rời --------
            if self._la_ghi(ten) and not self.cho_phep_ghi:
                ban_ghi.them("cho_xac_nhan", luot=luot, ten=ten, tham_so=dict(tham_so))
                raise CanXacNhan(ten, dict(tham_so), ma_theo_doi="")

            # --- LUẬT 1: mọi lời gọi đi qua nhân ------------------------------
            kq = self.nhan.goi(danh_tinh, ten, tham_so)

            if kq.ok:
                dem_loi.clear()
                ban_ghi.them("ket_qua_cong_cu", luot=luot, ten=ten, ok=True,
                             ma_theo_doi=kq.ma_theo_doi, ket_qua=kq.ket_qua)
                tin_nhan.append({"vai": "cong_cu", "ten": ten,
                                 "noi_dung": repr(kq.ket_qua)[:2000]})
                continue

            # --- LUẬT 3 + 4: lỗi ----------------------------------------------
            ly_do = kq.ly_do
            if self._khong_ton_tai(kq):
                co_that = [b["ten"] for b in self.bo_phoi.ban_khai_cho_mo_hinh()]
                ly_do = (ly_do + " | công cụ đang có: " + ", ".join(co_that))

            khoa = "%s::%s" % (ten, kq.loai_loi or kq.ly_do[:60])
            dem_loi[khoa] = dem_loi.get(khoa, 0) + 1
            ban_ghi.them("ket_qua_cong_cu", luot=luot, ten=ten, ok=False,
                         ma_theo_doi=kq.ma_theo_doi, ly_do=ly_do,
                         lan_lap=dem_loi[khoa])

            if dem_loi[khoa] >= self.tran_lap_loi:
                ban_ghi.them("xong", so_luot=luot, ly_do=(
                    "dừng: lặp lại cùng một lỗi %d lần trên %r — tiếp nữa chỉ tốn "
                    "hạn mức mà không đổi kết quả" % (dem_loi[khoa], ten)))
                return ban_ghi

            tin_nhan.append({"vai": "cong_cu", "ten": ten, "noi_dung": "LỖI: " + ly_do})

        # --- LUẬT 2: hết trần thì nói rõ ------------------------------------
        ban_ghi.them("xong", so_luot=self.tran_luot, ly_do=(
            "dừng: hết trần %d lượt mà chưa có câu trả lời. Việc CHƯA xong."
            % (self.tran_luot,)))
        return ban_ghi

    # -----------------------------------------------------------------------

    def _la_ghi(self, ten: str) -> bool:
        """Công cụ này có GHI không — hỏi bản khai, không tự đoán từ tên.

        Đoán từ tên (`.ghi`, `.xoa`, `.tao`) là một luật ngầm mà không gì bắt
        trình điều khiển tuân theo, nên một công cụ ghi đặt tên khác sẽ lọt.
        """
        # HỎI BẢN KHAI GỐC, KHÔNG HỎI DANH SÁCH ĐANG PHƠI. Sửa 26/09/2026:
        # bản đầu hỏi `ban_khai_cho_mo_hinh()`, nên một công cụ GHI đang bị ẩn
        # trả về False và ĐI VÒNG qua cổng xác nhận. Ẩn là chuyện độ chính xác;
        # ghi là chuyện không lùi được. Trộn hai thứ ấy là mở một đường vòng
        # quanh đúng cái cổng quan trọng nhất của vòng lặp.
        b = self.bo_phoi.ban_khai_goc(ten)
        if b is not None:
            return bool(b.get("ghi"))
        # KHÔNG KHAI → False, và đó là an toàn chứ không phải lỏng tay: một công
        # cụ chưa khai thì NHÂN sẽ từ chối nó, nên nó không chạy được dù có đi
        # qua đây. Trả True ở đây chỉ đổi một lời từ chối CÓ ÍCH ("không có công
        # cụ X, đang có: …") thành một lần dừng chờ xác nhận khó hiểu cho một
        # việc vốn không thể xảy ra.
        return False

    @staticmethod
    def _khong_ton_tai(kq: Any) -> bool:
        ly = (getattr(kq, "ly_do", "") or "").lower()
        return "không có công cụ" in ly or "khong co cong cu" in ly or "chưa đăng ký" in ly
