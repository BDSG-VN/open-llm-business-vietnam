#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phuc-vu/cau_hinh.py — CẤU HÌNH LỚP PHỤC VỤ MÔ HÌNH, ĐỌC HẾT TỪ BIẾN MÔI TRƯỜNG.

VÌ SAO KHÔNG CÓ MỘT GIÁ TRỊ MẶC ĐỊNH NÀO CHỨA ĐỊA CHỈ THẬT
----------------------------------------------------------
Kho này CÔNG KHAI. Một địa chỉ máy phục vụ viết cứng trong mã nguồn là hai hỏng
cùng lúc:

  1. Nó lộ hình dạng hạ tầng nội bộ ra kho công khai — đúng thứ cổng
     `cong/khong-ha-tang.py` sinh ra để chặn.
  2. Nguy hơn: nó làm chương trình CHẠY ĐƯỢC khi người dùng quên đặt biến. Chạy
     được mà trỏ sai chỗ là họ lỗi "hỏng mà không báo" — người vận hành tưởng
     mình đang gọi máy của mình, còn câu hỏi thì đi tới một máy khác.

Cho nên `BDSG_VLLM_URL` KHÔNG có mặc định. Thiếu là ném lỗi ngay lúc khởi động,
với câu nói rõ phải đặt biến nào.

VÌ SAO NGỮ CẢNH MẶC ĐỊNH LÀ 8192 CHỨ KHÔNG PHẢI 262144
-------------------------------------------------------
google/gemma-4-31B-it khai `max_position_embeddings = 262144` (ngữ cảnh 256K).
Con số ấy là TRẦN KIẾN TRÚC, không phải giá trị nên đặt mặc định khi phục vụ.

Lý do là bộ nhớ đệm KV: vLLM cấp phát bộ nhớ đệm ấy theo ngữ cảnh tối đa nhân số
luồng chạy song song. Mô hình có 60 lớp, 16 đầu KV, head_dim 256 (đọc từ thẻ mô
hình trên Hugging Face, phiên tra cứu 26/09/2026), nên mỗi token phải giữ khoá và
giá trị cho cả 60 lớp. Đặt 262144 làm mặc định thì bộ nhớ đệm ăn hết phần VRAM
còn lại sau trọng số, và máy phục vụ hoặc không khởi động nổi, hoặc chỉ chạy được
đúng một yêu cầu một lúc.

⚠ CHƯA ĐO: dự án chưa có GPU để đo bộ nhớ đệm KV thật ở 8192 và ở 262144. 8192 là
một giá trị THẬN TRỌNG chọn theo lập luận trên, không phải con số đo được. Ai có
GPU thì nâng dần và đo, đừng nhảy thẳng lên trần.

TRỌNG SỐ LÀ CỦA GOOGLE, KHÔNG PHẢI CỦA BDSG
--------------------------------------------
Lớp này PHỤC VỤ trọng số do Google phát hành (Apache-2.0, xem thẻ mô hình
huggingface.co/google/gemma-4-31B-it). Nó KHÔNG phải trọng số do BDSG huấn luyện.
Trường tự khai `bdsg_la_trong_so_bdsg` phải là `false` cho mọi mã mô hình đi qua
lớp này — xem `bdsg_la_trong_so_bdsg()` ở cuối tệp.

Viết ngày 26/09/2026. Python 3.9.6 (bản đang dùng trong .venv của kho).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


class LoiCauHinh(ValueError):
    """Cấu hình thiếu hoặc sai.

    Tách riêng khỏi ValueError để nơi gọi bắt đúng loại lỗi này mà không nuốt
    nhầm một ValueError từ chỗ khác (ví dụ int() của thư viện chuẩn).
    """


# ── Tên biến môi trường, khai ở MỘT chỗ ──────────────────────────────────────
# Khai thành hằng chứ không rải chuỗi khắp nơi: đổi tên biến thì sửa một dòng, và
# thông báo lỗi luôn nói đúng tên biến hiện hành thay vì một tên đã lạc hậu.
BIEN_URL = "BDSG_VLLM_URL"
BIEN_MO_HINH = "BDSG_VLLM_MODEL"
BIEN_KHOA = "BDSG_VLLM_KHOA"
BIEN_TRAN_TOKEN_RA = "BDSG_TRAN_TOKEN_RA"
BIEN_NGU_CANH = "BDSG_NGU_CANH"
BIEN_HET_GIO = "BDSG_HET_GIO_GIAY"

# Mã mô hình mặc định. Đây là một ĐỊNH DANH CÔNG KHAI trên Hugging Face, không
# phải địa chỉ máy và không phải bí mật — nên nó được phép có mặc định, khác với
# BIEN_URL. Nếu máy phục vụ nạp mô hình khác, vLLM trả lỗi "model not found" ngay
# ở yêu cầu đầu tiên: hỏng to, thấy ngay, không âm thầm.
MO_HINH_MAC_DINH = "google/gemma-4-31B-it"

TRAN_TOKEN_RA_MAC_DINH = 2048
NGU_CANH_MAC_DINH = 8192
HET_GIO_GIAY_MAC_DINH = 300

# Trần kiến trúc của google/gemma-4-31B-it, đọc từ thẻ mô hình ngày 26/09/2026.
# Dùng để cảnh báo khi ai đó đặt ngữ cảnh vượt trần — vượt trần thì vLLM từ chối
# khởi động, và biết trước ở đây rẻ hơn biết sau khi đã nạp 62 GB trọng số.
NGU_CANH_TRAN_CUA_MO_HINH = 262144


def _doc_so_nguyen(ten_bien: str, mac_dinh: int) -> int:
    """Đọc một biến môi trường dạng số nguyên dương.

    Chuỗi rỗng được coi là KHÔNG ĐẶT (trả về mặc định). Lý do: trong các tệp
    docker-compose và systemd, một biến khai mà bỏ trống rất hay xảy ra, và ném
    lỗi ở đó chỉ gây bực chứ không cứu được ai. Còn một chuỗi KHÔNG RỖNG mà không
    phải số thì là lỗi thật: người ta gõ nhầm, và đoán hộ họ là sai.
    """
    tho = os.environ.get(ten_bien, "")
    if tho.strip() == "":
        return mac_dinh
    try:
        gia_tri = int(tho.strip())
    except ValueError:
        raise LoiCauHinh(
            "Biến {} phải là một số nguyên, đang là {!r}. "
            "Bỏ trống thì lấy mặc định {}.".format(ten_bien, tho, mac_dinh)
        )
    return gia_tri


@dataclass
class CauHinhPhucVu:
    """Toàn bộ thứ lớp phục vụ cần biết để nói chuyện với máy vLLM nội bộ."""

    url: str
    ma_mo_hinh: str = MO_HINH_MAC_DINH
    khoa: str = ""
    tran_token_ra: int = TRAN_TOKEN_RA_MAC_DINH
    ngu_canh: int = NGU_CANH_MAC_DINH
    het_gio_giay: int = HET_GIO_GIAY_MAC_DINH

    def __post_init__(self) -> None:
        # Kiểm ngay trong hàm khởi tạo, không để nơi gọi "nhớ" gọi kiem().
        # Một cấu hình sai thì KHÔNG tồn tại được đối tượng cấu hình — chứ không
        # phải "tạo xong rồi trầm ở lời gọi mạng thứ ba mươi".
        self.kiem()

    # ── Đọc từ môi trường ────────────────────────────────────────────────────
    @classmethod
    def tu_moi_truong(cls) -> "CauHinhPhucVu":
        """Dựng cấu hình từ biến môi trường. Ném LoiCauHinh nếu thiếu thứ bắt buộc."""
        url = os.environ.get(BIEN_URL, "").strip()
        if url == "":
            raise LoiCauHinh(
                "Thiếu biến môi trường {}. Lớp phục vụ KHÔNG có địa chỉ mặc định — "
                "cố ý như vậy, để không bao giờ có chuyện chương trình chạy được mà "
                "trỏ vào một máy không ai định trỏ tới. "
                "Ví dụ đặt cho máy chạy ngay trên localhost: "
                "export {}=http://127.0.0.1:8000/v1".format(BIEN_URL, BIEN_URL)
            )

        ma_mo_hinh = os.environ.get(BIEN_MO_HINH, "").strip() or MO_HINH_MAC_DINH
        # Khoá KHÔNG .strip() phần giữa, chỉ bỏ khoảng trắng hai đầu do shell hay
        # thêm vào. Khoá rỗng là HỢP LỆ: vLLM chạy trên máy cục bộ thường không bật
        # xác thực, và bắt buộc phải có khoá ở đó chỉ đẻ ra một khoá giả viết cứng.
        khoa = os.environ.get(BIEN_KHOA, "").strip()

        return cls(
            url=url,
            ma_mo_hinh=ma_mo_hinh,
            khoa=khoa,
            tran_token_ra=_doc_so_nguyen(BIEN_TRAN_TOKEN_RA, TRAN_TOKEN_RA_MAC_DINH),
            ngu_canh=_doc_so_nguyen(BIEN_NGU_CANH, NGU_CANH_MAC_DINH),
            het_gio_giay=_doc_so_nguyen(BIEN_HET_GIO, HET_GIO_GIAY_MAC_DINH),
        )

    # ── Tự kiểm ──────────────────────────────────────────────────────────────
    def kiem(self) -> None:
        """Ném LoiCauHinh ngay nếu cấu hình không dùng được.

        Mọi phép kiểm ở đây đều rẻ (không chạm mạng). Chúng chỉ trả lời câu
        "cấu hình này có VÔ NGHĨA không", chứ không trả lời "máy kia có sống
        không" — câu ấy thuộc về cong_mo_hinh.py.
        """
        if not isinstance(self.url, str) or self.url.strip() == "":
            raise LoiCauHinh("Địa chỉ máy phục vụ ({}) rỗng.".format(BIEN_URL))

        # Bỏ dấu gạch chéo cuối một lần tại đây, để mọi nơi ghép đường dẫn về sau
        # không phải nhớ chuyện ấy. Không chuẩn hoá thì ta có "/v1//models", và
        # một số máy chủ trả 404 cho nó — lỗi rất khó nhìn ra bằng mắt.
        self.url = self.url.strip().rstrip("/")

        phan = urlparse(self.url)
        if phan.scheme not in ("http", "https"):
            raise LoiCauHinh(
                "{} phải bắt đầu bằng http:// hoặc https://, đang là {!r}.".format(
                    BIEN_URL, self.url
                )
            )
        if not phan.netloc:
            raise LoiCauHinh(
                "{} thiếu phần địa chỉ máy, đang là {!r}. "
                "Dạng đúng: <giao thức>://<máy>:<cổng>/v1".format(BIEN_URL, self.url)
            )

        if not isinstance(self.ma_mo_hinh, str) or self.ma_mo_hinh.strip() == "":
            raise LoiCauHinh("{} rỗng.".format(BIEN_MO_HINH))

        for ten_bien, gia_tri in (
            (BIEN_TRAN_TOKEN_RA, self.tran_token_ra),
            (BIEN_NGU_CANH, self.ngu_canh),
            (BIEN_HET_GIO, self.het_gio_giay),
        ):
            if not isinstance(gia_tri, int) or isinstance(gia_tri, bool):
                raise LoiCauHinh("{} phải là số nguyên.".format(ten_bien))
            if gia_tri <= 0:
                raise LoiCauHinh(
                    "{} phải lớn hơn 0, đang là {}.".format(ten_bien, gia_tri)
                )

        # Trần token ra phải NHỎ HƠN ngữ cảnh. Nếu bằng hoặc lớn hơn thì câu hỏi
        # của người dùng không còn chỗ nào để nằm, và vLLM từ chối từng yêu cầu
        # một — hỏng ở mọi lượt hỏi, nhưng chỉ lộ ra sau khi đã dựng xong máy chủ.
        if self.tran_token_ra >= self.ngu_canh:
            raise LoiCauHinh(
                "{}={} phải NHỎ HƠN {}={}: phần sinh ra và phần hỏi vào dùng chung "
                "một cửa sổ ngữ cảnh, nên nếu phần sinh ra chiếm hết thì không còn "
                "chỗ cho câu hỏi.".format(
                    BIEN_TRAN_TOKEN_RA, self.tran_token_ra, BIEN_NGU_CANH, self.ngu_canh
                )
            )

    def canh_bao(self) -> list:
        """Những chỗ KHÔNG sai đủ để chặn, nhưng người vận hành nên biết.

        Tách khỏi kiem() có chủ ý: trộn cảnh báo vào chỗ ném lỗi thì sớm muộn có
        người nới một phép kiểm thật thành cảnh báo cho đỡ vướng.
        """
        cac_canh_bao = []

        if not self.url.rstrip("/").endswith("/v1"):
            cac_canh_bao.append(
                "{} không kết thúc bằng /v1. API tương thích OpenAI của vLLM nằm dưới "
                "tiền tố /v1; thiếu nó thì mọi lời gọi trả 404.".format(BIEN_URL)
            )

        if self.ngu_canh > NGU_CANH_TRAN_CUA_MO_HINH:
            cac_canh_bao.append(
                "{}={} vượt trần kiến trúc của {} ({}). vLLM sẽ từ chối khởi "
                "động.".format(
                    BIEN_NGU_CANH,
                    self.ngu_canh,
                    MO_HINH_MAC_DINH,
                    NGU_CANH_TRAN_CUA_MO_HINH,
                )
            )
        elif self.ngu_canh > 32768:
            cac_canh_bao.append(
                "{}={} là ngữ cảnh lớn. Bộ nhớ đệm KV tăng tuyến tính theo nó và "
                "theo số yêu cầu chạy song song; dự án CHƯA ĐO mức tiêu thụ thật. "
                "Nâng dần và đo, đừng nhảy thẳng lên trần.".format(
                    BIEN_NGU_CANH, self.ngu_canh
                )
            )

        phan = urlparse(self.url)
        may = (phan.hostname or "").lower()
        if may not in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
            cac_canh_bao.append(
                "{} trỏ ra ngoài máy này ({}). Bản phát hành hiện tại CHƯA CÓ đăng "
                "nhập an toàn, chỉ dùng cho DEMO MỘT NGƯỜI trên localhost. Trỏ ra "
                "mạng là tự mở một cổng vào không ai canh.".format(BIEN_URL, may)
            )
        if phan.scheme == "http" and may not in ("127.0.0.1", "localhost", "::1"):
            cac_canh_bao.append(
                "Đang dùng http (không mã hoá) tới một máy KHÔNG phải máy này. "
                "Câu hỏi và câu trả lời đi qua mạng dưới dạng chữ thường."
            )

        return cac_canh_bao

    # ── In ra để người vận hành đọc ──────────────────────────────────────────
    def tom_tat(self) -> str:
        """Trả về cấu hình đang dùng, dạng người đọc được.

        ⚠ TUYỆT ĐỐI KHÔNG IN KHOÁ. Hàm này sinh ra để dán vào nhật ký khởi động và
        vào báo cáo sự cố, mà cả hai chỗ ấy đều đi xa hơn người viết nghĩ. Chỉ nói
        khoá CÓ hay KHÔNG, và dài bao nhiêu ký tự — đủ để bắt lỗi "dán thiếu một
        ký tự", không đủ để tái tạo khoá.

        Bài tự kiểm `thu_cong_mo_hinh.py` đặt một khoá bịa rồi tìm nó trong đầu ra
        của hàm này và ĐÒI không thấy. Ai sửa hàm này mà làm lộ khoá sẽ bị bài ấy
        chặn lại.
        """
        if self.khoa:
            trang_thai_khoa = "đã đặt ({} ký tự, không in ra)".format(len(self.khoa))
        else:
            trang_thai_khoa = "không đặt (hợp lệ với máy cục bộ không bật xác thực)"

        cac_dong = [
            "Cấu hình lớp phục vụ mô hình BDSG",
            "  {:<22} {}".format(BIEN_URL + ":", self.url),
            "  {:<22} {}".format(BIEN_MO_HINH + ":", self.ma_mo_hinh),
            "  {:<22} {}".format(BIEN_KHOA + ":", trang_thai_khoa),
            "  {:<22} {}".format(BIEN_TRAN_TOKEN_RA + ":", self.tran_token_ra),
            "  {:<22} {}".format(BIEN_NGU_CANH + ":", self.ngu_canh),
            "  {:<22} {}".format(BIEN_HET_GIO + ":", self.het_gio_giay),
            "  trọng số:              của Google (Apache-2.0), KHÔNG phải của BDSG",
            # HỎI chính hàm chứ không viết cứng chữ "false". Một dòng viết cứng là
            # một lời khai KHÔNG kiểm chứng: ngày nào hàm kia đổi cho một bản đã
            # tinh chỉnh thật, bản tóm tắt vẫn in "false" và nói sai về thứ đang
            # chạy. Cùng một luật với trường `bdsg_la_trong_so_bdsg` của API.
            "  bdsg_la_trong_so_bdsg: {}".format(
                "true" if bdsg_la_trong_so_bdsg(self.ma_mo_hinh) else "false"
            ),
        ]
        for loi_canh_bao in self.canh_bao():
            cac_dong.append("  ⚠ " + loi_canh_bao)
        return "\n".join(cac_dong)

    # ── Đường dẫn ────────────────────────────────────────────────────────────
    def duong_dan(self, duoi: str) -> str:
        """Ghép một đường dẫn con vào gốc API. `duoi` viết không có gạch chéo đầu."""
        return self.url + "/" + duoi.lstrip("/")

    def dau_de(self, dong_chay: bool = False) -> dict:
        """Các trường đầu đề HTTP cho mọi lời gọi.

        Chỉ gắn Authorization khi THẬT SỰ có khoá. Gắn một đầu đề rỗng làm vài máy
        chủ trả 401 với câu báo lỗi nói về khoá sai — dẫn người đi tìm nhầm hướng.

        `dong_chay` chọn giá trị Accept. Bản đầu khai cứng `text/event-stream` cho
        MỌI lời gọi, kể cả `GET /v1/models` — đường ấy trả JSON thường, không phải
        SSE. vLLM bỏ qua Accept nên không lộ ra, nhưng một proxy hoặc cổng API
        đứng giữa có quyền trả 406 cho một Accept không khớp, và lúc ấy lỗi sẽ
        hiện ra là "máy nội bộ từ chối" mà không ai đoán được vì sao.
        """
        cac_dau_de = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if dong_chay else "application/json",
        }
        if self.khoa:
            cac_dau_de["Authorization"] = "Bearer " + self.khoa
        return cac_dau_de


def bdsg_la_trong_so_bdsg(ma_mo_hinh: Optional[str] = None) -> bool:
    """Trọng số đi qua lớp này có phải do BDSG huấn luyện không?

    Trả về `False`, luôn luôn, ở phiên bản này. Không phải vì lười: tính đến
    26/09/2026 BDSG CHƯA huấn luyện trọng số nào và CHƯA tinh chỉnh Gemma 4.
    Lớp `phuc-vu/` này chỉ PHỤC VỤ trọng số do Google phát hành.

    Ngày nào BDSG thật sự tinh chỉnh xong một bản LoRA/QLoRA trên Gemma 4 thì hàm
    này mới được đổi, và chỉ đổi cho ĐÚNG mã mô hình đã tinh chỉnh — không phải
    cho `google/gemma-4-31B-it` nguyên bản. Tham số `ma_mo_hinh` có mặt từ bây giờ
    để chỗ gọi không phải đổi chữ ký hàm vào ngày ấy.
    """
    del ma_mo_hinh  # chưa dùng; xem giải thích trên
    return False
