#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phuc-vu/gia_lap.py — BACKEND GIẢ, ĐỂ KIỂM THỬ. KHÔNG DÙNG Ở SẢN XUẤT.

⚠⚠⚠  MỌI THỨ TỆP NÀY SINH RA ĐỀU LÀ CHỮ BỊA SẴN. Ở ĐÂY KHÔNG CÓ MÔ HÌNH NÀO.  ⚠⚠⚠

VÌ SAO CẦN MỘT BACKEND GIẢ
--------------------------
Cả đường chạy từ giao diện tới mô hình có rất nhiều chỗ hỏng được mà không liên
quan gì tới mô hình: hợp đồng SSE bốn sự kiện, đường báo lỗi khi máy nội bộ mất
kết nối, phân quyền hội thoại, cách giao diện xử lý một dòng chảy bị cắt. Bắt mọi
phép kiểm ấy phải có GPU 62 GB thì hoặc là không ai chạy chúng, hoặc là chúng chỉ
chạy một lần trước khi phát hành. Cả hai đều dẫn tới cùng một kết cục: hợp đồng
trôi dạt và không ai biết.

Backend giả này chạy trong vài mili giây trên máy xách tay, nên các phép kiểm ấy
chạy được ở MỌI lần sửa mã.

VÌ SAO NÓ PHẢI KHÓ BẬT NHẦM — BA LỚP KHOÁ
------------------------------------------
Một backend giả bật nhầm ở sản xuất là kịch bản tệ nhất trong cả kho này: hệ thống
CHẠY, giao diện hiện chữ, không có lỗi nào — và mọi câu trả lời đều bịa. Đó là họ
lỗi "hỏng mà không báo" ở dạng độc nhất của nó, vì người dùng không có cách nào
nhận ra bằng mắt. Nên ba lớp khoá, mỗi lớp chặn được một kiểu bất cẩn khác nhau:

  1. PHẢI đặt BDSG_DUNG_GIA_LAP=1. Không có nó thì hàm khởi tạo NÉM LỖI, không
     phải cảnh báo rồi chạy tiếp. (Chặn: quên cấu hình.)
  2. Mỗi lần bật, in một khối cảnh báo to ra luồng lỗi chuẩn. (Chặn: bật lúc thử
     rồi quên tắt — khối cảnh báo nằm trong nhật ký khởi động.)
  3. Mã mô hình nó tự khai là `bdsg-gia-lap-khong-phai-mo-hinh-that`, và câu trả
     lời nó sinh ra mở đầu bằng đúng chữ ấy. (Chặn: cả hai lớp trên bị vượt qua
     bằng cách nào đó — nhãn "câu trả lời đến từ …" trên giao diện sẽ nói thật,
     vì nó lấy tên từ `moHinhThat`.)

Lớp 3 mới là lớp cuối cùng đáng tin, vì nó không phụ thuộc vào ai nhớ điều gì.

Viết ngày 26/09/2026. Python 3.9.6.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict, Iterator, List, Optional, Sequence

if __package__:
    from .cong_mo_hinh import (
        LoiCongMoHinh,
        LoiKhongNoiDuocMayNoiBo,
        LoiMayNoiBoTraLoiSai,
        doi_chieu_mo_hinh,
    )
else:  # chạy thẳng tệp: thư mục có gạch ngang nên không import gói được
    from cong_mo_hinh import (  # type: ignore
        LoiCongMoHinh,
        LoiKhongNoiDuocMayNoiBo,
        LoiMayNoiBoTraLoiSai,
        doi_chieu_mo_hinh,
    )

__all__ = [
    "LoiGiaLapChuaBat",
    "CongMoHinhGiaLap",
    "MA_MO_HINH_GIA",
    "BIEN_BAT",
    "BIEN_CHE_DO_LOI",
    "dang_bat",
]

BIEN_BAT = "BDSG_DUNG_GIA_LAP"
BIEN_CHE_DO_LOI = "BDSG_GIA_LAP_LOI"
BIEN_TRE = "BDSG_GIA_LAP_TRE_GIAY"

# Tên này CỐ Ý dài và cố ý tự tố cáo mình. Nó đi thẳng vào trường `moHinhThat` của
# sự kiện SSE `xong`, rồi lên nhãn "câu trả lời đến từ …" trên giao diện. Một tên
# ngắn gọn kiểu "gia-lap" sẽ lướt qua mắt người đọc; tên này thì không.
MA_MO_HINH_GIA = "bdsg-gia-lap-khong-phai-mo-hinh-that"

# Ba chế độ lỗi, đủ để thử ba đường hỏng khác nhau của lớp trên.
LOI_TRUOC_KHI_CHAY = "khong-noi-duoc"   # máy "nội bộ" chết trước khi sinh chữ nào
LOI_GIUA_DONG = "giua-dong"             # đứt sau khi đã trả một phần chữ
LOI_MAY_TRA_LOI_SAI = "may-tra-loi-sai"  # máy sống nhưng từ chối yêu cầu
CAC_CHE_DO_LOI = (LOI_TRUOC_KHI_CHAY, LOI_GIUA_DONG, LOI_MAY_TRA_LOI_SAI)

TRE_MAC_DINH_GIAY = 0.004  # đủ để thấy chữ hiện dần, đủ nhỏ để bài kiểm chạy nhanh

_CAU_TRA_LOI_BIA = (
    "[" + MA_MO_HINH_GIA + "] Đây là câu trả lời BỊA SẴN của backend giả, không "
    "đến từ mô hình nào. Nó tồn tại để kiểm thử hợp đồng SSE bốn sự kiện "
    "(batdau, chu, loi, xong) mà không cần GPU. Thấy câu này ở nơi đáng lẽ phải "
    "có trợ lý thật, nghĩa là biến môi trường " + BIEN_BAT + " đang bật nhầm."
)

_DA_CANH_BAO = False


def dang_bat() -> bool:
    """Backend giả có đang được bật không?

    So BẰNG với chuỗi "1", không dùng phép "có giá trị là bật". Lý do: shell và
    docker-compose rất hay để lại biến bằng "0", "false" hay "no" sau một lần thử,
    và phép "có giá trị là bật" sẽ coi cả ba là BẬT. Ở một công tắc mà bật nhầm
    thì mọi câu trả lời đều bịa, phải chọn cách đọc chặt nhất.
    """
    return os.environ.get(BIEN_BAT, "").strip() == "1"


class LoiGiaLapChuaBat(LoiCongMoHinh):
    """Có người cố dùng backend giả mà chưa bật nó tường minh."""


def _canh_bao_to() -> None:
    """In một khối cảnh báo ra luồng lỗi chuẩn, mỗi tiến trình một lần.

    Ra stderr chứ không ra stdout: stdout của một máy chủ hay bị nuốt hoặc bị
    chuyển hướng vào chỗ không ai đọc, còn stderr thì hầu như luôn vào nhật ký.
    """
    global _DA_CANH_BAO
    if _DA_CANH_BAO:
        return
    _DA_CANH_BAO = True
    vach = "!" * 78
    print(vach, file=sys.stderr)
    print("!! BACKEND GIẢ ĐANG BẬT ({}=1).".format(BIEN_BAT), file=sys.stderr)
    print("!! Mọi câu trả lời từ đây là CHỮ BỊA SẴN. Không có mô hình nào chạy.",
          file=sys.stderr)
    print("!! Chỉ dùng để kiểm thử. TẮT trước khi cho bất kỳ ai dùng thật.",
          file=sys.stderr)
    print(vach, file=sys.stderr)


class CongMoHinhGiaLap:
    """Giả lập CongMoHinh: cùng tên hàm, cùng loại lỗi, không chạm mạng.

    Cố ý ném ĐÚNG các lớp lỗi của `cong_mo_hinh` chứ không ném lỗi riêng. Nếu nó
    ném một lớp lỗi khác thì bài kiểm sẽ chứng minh đường xử lý lỗi của backend
    giả chạy đúng — mà đường ấy không phải đường chạy ở sản xuất. Kiểm một thứ
    rồi phát hành một thứ khác là cách tự lừa mình tốn kém nhất.
    """

    def __init__(self, cau_hinh=None, che_do_loi: Optional[str] = None) -> None:
        if not dang_bat():
            raise LoiGiaLapChuaBat(
                "Backend giả CHƯA được bật. Nó chỉ chạy khi đặt tường minh {}=1. "
                "Đây là chốt chặn để chữ bịa không bao giờ đi ra ngoài dưới danh "
                "nghĩa câu trả lời thật.".format(BIEN_BAT)
            )
        _canh_bao_to()

        self.cau_hinh = cau_hinh
        if che_do_loi is None:
            che_do_loi = os.environ.get(BIEN_CHE_DO_LOI, "").strip()
        if che_do_loi and che_do_loi not in CAC_CHE_DO_LOI:
            raise LoiGiaLapChuaBat(
                "Chế độ lỗi {!r} không có. Các chế độ hợp lệ: {}.".format(
                    che_do_loi, ", ".join(CAC_CHE_DO_LOI)
                )
            )
        self.che_do_loi = che_do_loi

        try:
            self.tre_giay = float(os.environ.get(BIEN_TRE, "") or TRE_MAC_DINH_GIAY)
        except ValueError:
            self.tre_giay = TRE_MAC_DINH_GIAY
        if self.tre_giay < 0:
            self.tre_giay = 0.0

    # ── Cùng chữ ký với CongMoHinh ──────────────────────────────────────────
    def danh_sach_mo_hinh(self) -> List[Dict[str, str]]:
        if self.che_do_loi == LOI_TRUOC_KHI_CHAY:
            raise LoiKhongNoiDuocMayNoiBo(
                "Không nối được tới máy mô hình NỘI BỘ (backend giả đang diễn cảnh "
                "máy nội bộ không chạy)."
            )
        return [{"ma": MA_MO_HINH_GIA, "chu_so_huu": "bdsg-gia-lap"}]

    def hoi_dong_chay(
        self,
        tin_nhan: Sequence[Dict[str, str]],
        nhiet: float = 0.7,
        tran_token_ra: Optional[int] = None,
        thu_thap: Optional[Dict[str, object]] = None,
    ) -> Iterator[str]:
        """Sinh ra câu trả lời bịa, từng mẩu chữ một."""
        del tin_nhan, nhiet, tran_token_ra  # backend giả không đọc câu hỏi

        if thu_thap is None:
            thu_thap = {}
        # Điền tên mô hình NGAY từ đầu, không đợi tới cuối: nếu dòng chảy đứt giữa
        # chừng, lớp trên vẫn phải có một cái tên đúng để đưa vào sự kiện `xong`.
        thu_thap["mo_hinh_that"] = doi_chieu_mo_hinh(MA_MO_HINH_GIA, MA_MO_HINH_GIA)
        thu_thap["so_mau"] = 0
        thu_thap["ly_do_dung"] = None

        if self.che_do_loi == LOI_TRUOC_KHI_CHAY:
            raise LoiKhongNoiDuocMayNoiBo(
                "Không nối được tới máy mô hình NỘI BỘ (backend giả đang diễn cảnh "
                "máy nội bộ không chạy). Trợ lý này không có đường dự phòng ra "
                "ngoài, nên câu hỏi không đi đâu cả."
            )
        if self.che_do_loi == LOI_MAY_TRA_LOI_SAI:
            raise LoiMayNoiBoTraLoiSai(
                "Máy nội bộ trả mã 404 (backend giả đang diễn cảnh sai mã mô hình)."
            )

        # Cắt theo TỪ chứ không theo ký tự. Mô hình thật trả về token, mà token
        # gần với từ hơn là với ký tự — cắt theo ký tự sẽ cho giao diện một nhịp
        # chảy mượt hơn thực tế, và giấu mất những lỗi ghép chữ chỉ lộ ra khi
        # mẩu chữ dài hơn một ký tự.
        cac_mau = _cat_thanh_mau(_CAU_TRA_LOI_BIA)
        cat_o = len(cac_mau) // 3 if self.che_do_loi == LOI_GIUA_DONG else None

        for chi_so, mau in enumerate(cac_mau):
            if cat_o is not None and chi_so >= cat_o:
                raise LoiKhongNoiDuocMayNoiBo(
                    "Mất kết nối tới máy mô hình NỘI BỘ giữa lúc đang sinh chữ "
                    "(backend giả đang diễn cảnh đứt giữa dòng)."
                )
            if self.tre_giay:
                time.sleep(self.tre_giay)
            thu_thap["so_mau"] = int(thu_thap["so_mau"]) + 1  # type: ignore[arg-type]
            yield mau

        thu_thap["ly_do_dung"] = "stop"


def _cat_thanh_mau(cau: str) -> List[str]:
    """Cắt một câu thành các mẩu dạng '<từ> ', giữ nguyên toàn bộ ký tự.

    Ghép lại các mẩu phải ra đúng câu gốc — bài tự kiểm kiểm đúng chuyện đó, vì
    một bộ cắt làm rơi khoảng trắng sẽ cho mọi phép so sánh chuỗi về sau một sai
    số không ai truy ra được.
    """
    cac_mau: List[str] = []
    dem = ""
    for ky_tu in cau:
        dem += ky_tu
        if ky_tu == " ":
            cac_mau.append(dem)
            dem = ""
    if dem:
        cac_mau.append(dem)
    return cac_mau
