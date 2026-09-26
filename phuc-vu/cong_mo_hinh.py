#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phuc-vu/cong_mo_hinh.py — NÓI CHUYỆN VỚI MÁY vLLM NỘI BỘ QUA API TƯƠNG THÍCH OpenAI.

Đây là chỗ DUY NHẤT trong kho chạm vào mạng để hỏi mô hình. Gom về một tệp có
chủ ý: một luật như "không bao giờ gửi dữ liệu ra ngoài" chỉ kiểm chứng được khi
có đúng một chỗ để đọc.

════════════════════════════════════════════════════════════════════════════
KHÔNG CÓ ĐƯỜNG DỰ PHÒNG RA NHÀ CUNG CẤP NGOÀI. VIẾT RÕ VÌ SAO, ĐỂ NGƯỜI SAU
ĐỪNG "THÊM CHO TIỆN".
════════════════════════════════════════════════════════════════════════════

  Cái bẫy nghe rất hợp lý: "thử máy cục bộ trước, hỏng thì gọi đám mây, người
  dùng đỡ phải chờ". Nó phá đúng thứ hệ này hứa.

  Người vận hành bật trợ lý nội bộ vì tài liệu doanh nghiệp KHÔNG được rời khỏi
  máy của họ. Với một đường dự phòng, câu hỏi nào cũng có thể ra ngoài — và ra
  đúng vào lúc tệ nhất, là lúc máy nội bộ hỏng nên không ai đang nhìn. Không có
  thông báo nào. Không có dòng nhật ký nào người dùng đọc. Dữ liệu đã đi rồi.

  Hỏng ồn ào thì có người sửa trong mười phút. Rò rỉ im lặng thì không ai biết,
  cho tới khi biết bằng một cách khác.

  Cho nên: máy nội bộ hỏng ⇒ NÉM `LoiKhongNoiDuocMayNoiBo`, câu tiếng Việt nói
  thẳng là máy NỘI BỘ không chạy. Không thử chỗ khác. Không có biến môi trường
  nào bật được hành vi ấy. Muốn có đường ra ngoài thì phải viết mã mới và phải
  giải thích được vì sao — không kế thừa được sự im lặng của mã cũ.

VÌ SAO CHỈ DÙNG THƯ VIỆN CHUẨN (urllib) CHỨ KHÔNG DÙNG requests/httpx
----------------------------------------------------------------------
Kho này hiện không có requests cũng không có httpx trong .venv. Thêm một phụ
thuộc chỉ để gọi hai đường HTTP là trả một cái giá thật (một cây phụ thuộc nữa
phải vá, một nguồn CVE nữa phải theo) để mua một tiện lợi nhỏ. `urllib.request`
đọc dòng chảy được, và phần khó của việc này không nằm ở thư viện HTTP mà nằm ở
bộ đọc SSE bên dưới.

BẪY ĐÃ BIẾT CỦA MỌI BỘ ĐỌC SSE — ĐÂY LÀ LÝ DO CÓ LỚP `BoDocSSE`
----------------------------------------------------------------
Máy chủ gửi SSE theo GÓI MẠNG, không theo DÒNG. Một mẩu chữ hoàn toàn có thể bị
cắt làm đôi giữa hai gói:

    gói 1:  b'data: {"choices":[{"delta":{"cont'
    gói 2:  b'ent":"xin"}}]}\\n\\n'

Bộ đọc nào gọi json.loads() lên từng gói sẽ ném lỗi ở gói 1 và mất luôn mẩu chữ.
Tệ hơn: lỗi này gần như không bao giờ xuất hiện trên máy cục bộ với câu trả lời
ngắn, mà xuất hiện khi mạng chậm hoặc câu trả lời dài — tức là trên máy thật, với
người dùng thật. Cho nên `BoDocSSE` giữ một bộ đệm và chỉ bóc khi đã đủ một dòng
trọn vẹn, và bài tự kiểm có hẳn một phép kiểm cắt đôi gói.

Viết ngày 26/09/2026. Python 3.9.6.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Dict, Iterator, List, Optional, Sequence

if __package__:
    from .cau_hinh import CauHinhPhucVu, LoiCauHinh
else:  # chạy thẳng tệp: thư mục có gạch ngang nên không import gói được
    from cau_hinh import CauHinhPhucVu, LoiCauHinh  # type: ignore

__all__ = [
    "LoiCongMoHinh",
    "LoiKhongNoiDuocMayNoiBo",
    "LoiMayNoiBoTraLoiSai",
    "BoDocSSE",
    "CongMoHinh",
    "boc_mau_chu",
    "doi_chieu_mo_hinh",
]


# ── Cây lỗi ──────────────────────────────────────────────────────────────────
# Ba lớp chứ không phải một, vì ba tình huống này đòi ba hành động khác nhau từ
# người vận hành, và trộn chúng lại thì thông báo nào cũng thành "có gì đó hỏng".


class LoiCongMoHinh(Exception):
    """Gốc của mọi lỗi phát ra từ cổng mô hình."""


class LoiKhongNoiDuocMayNoiBo(LoiCongMoHinh):
    """KHÔNG chạm tới được máy phục vụ NỘI BỘ.

    Cố ý là một lớp RIÊNG, không phải một urllib.error.URLError để nguyên.

    Vì sao: nếu để lỗi HTTP trần trôi lên giao diện, người dùng đọc được
    "Connection refused" hoặc "HTTP Error 502" và không biết hỏng ở đâu — máy
    mình? mạng? nhà cung cấp nào đó? Trong một hệ hứa "mọi thứ chạy trên máy
    bạn", câu hỏi ấy phải được trả lời ngay trong câu báo lỗi. Mọi thông báo của
    lớp này đều chứa chữ "nội bộ", và bài tự kiểm kiểm đúng chuyện đó.
    """


class LoiMayNoiBoTraLoiSai(LoiCongMoHinh):
    """Máy nội bộ CÓ trả lời, nhưng trả lời một thứ không dùng được.

    Khác hẳn lớp trên về cách sửa: ở đây máy đang chạy, nên đi khởi động lại nó
    là phí công. Phải đọc mã trạng thái và thân trả lời — thường là sai mã mô
    hình, sai đường dẫn /v1, hoặc sai khoá.
    """


# ── Bộ đọc SSE ───────────────────────────────────────────────────────────────


class BoDocSSE:
    """Bóc các gói `data:` từ một dòng chảy SSE đến theo từng gói mạng.

    Dùng: gọi `nap(byte)` cho mỗi gói nhận được, lặp qua thứ nó sinh ra.
    Mỗi thứ sinh ra là phần CHỮ đứng sau `data:` của một dòng trọn vẹn.

    Ba điều lớp này cố ý làm:

      1. GIỮ BỘ ĐỆM. Gói mạng cắt ở đâu cũng được; chỉ bóc khi đã thấy ký tự
         xuống dòng. Xem phần "BẪY ĐÃ BIẾT" ở đầu tệp.
      2. BỎ QUA dòng rỗng và dòng bắt đầu bằng dấu hai chấm (SSE dùng chúng làm
         nhịp giữ kết nối; coi chúng là dữ liệu thì json.loads() ném lỗi).
      3. KHÔNG tự phân giải JSON. Việc ấy để `boc_mau_chu()` làm, tách ra để
         kiểm thử được bộ đệm mà không phải dựng JSON hợp lệ mỗi lần.
    """

    def __init__(self) -> None:
        self._dem = b""

    def nap(self, goi: bytes) -> Iterator[str]:
        """Nạp một gói byte, sinh ra phần chữ sau `data:` của mỗi dòng đã trọn."""
        if not goi:
            return
        self._dem += goi
        while b"\n" in self._dem:
            dong_byte, self._dem = self._dem.split(b"\n", 1)
            # Máy chủ có thể dùng CRLF. Cắt \r ở cuối, nếu không thì mẩu chữ cuối
            # cùng của mỗi dòng dính thêm một ký tự không ai nhìn thấy.
            dong = dong_byte.rstrip(b"\r").decode("utf-8", errors="replace")
            if dong == "":
                continue  # ranh giới giữa hai sự kiện
            if dong.startswith(":"):
                continue  # chú thích / nhịp giữ kết nối
            if dong.startswith("data:"):
                yield dong[len("data:"):].strip()
            # Dòng `event:` và `id:` bị bỏ qua có chủ ý: API tương thích OpenAI
            # của vLLM chỉ dùng `data:`. Bỏ qua thay vì ném lỗi, để một máy chủ
            # lịch sự hơn không làm hỏng cả dòng chảy.

    def con_du(self) -> bytes:
        """Phần còn nằm trong bộ đệm khi dòng chảy kết thúc.

        Có hàm này để nơi gọi PHÁT HIỆN ĐƯỢC chuyện dòng chảy bị cắt giữa chừng.
        Một bộ đệm còn dư khi đã hết dữ liệu nghĩa là dòng cuối chưa bao giờ trọn
        — tức là kết nối đứt, chứ không phải câu trả lời đã xong.
        """
        return self._dem


def boc_mau_chu(goi_json: str) -> Dict[str, Optional[str]]:
    """Bóc một gói `data:` của vLLM thành thứ lớp trên dùng được.

    Trả về dict có ba khoá:
      - "chu":     mẩu chữ mới, hoặc None nếu gói này không mang chữ
      - "mo_hinh": tên mô hình MÁY CHỦ tự khai, hoặc None
      - "xong":    "[DONE]" hay lý do dừng, hoặc None

    Gói đầu tiên của mọi dòng chảy OpenAI chỉ mang `delta.role` mà không mang
    `content` — trả về chu=None cho nó là đúng, không phải lỗi.
    """
    ket_qua: Dict[str, Optional[str]] = {"chu": None, "mo_hinh": None, "xong": None}

    if goi_json.strip() == "[DONE]":
        ket_qua["xong"] = "[DONE]"
        return ket_qua

    try:
        du_lieu = json.loads(goi_json)
    except ValueError as loi:
        raise LoiMayNoiBoTraLoiSai(
            "Máy nội bộ gửi một gói SSE không phải JSON hợp lệ ({}). "
            "Thường là do địa chỉ trỏ vào một dịch vụ khác, không phải vLLM.".format(loi)
        )

    if not isinstance(du_lieu, dict):
        raise LoiMayNoiBoTraLoiSai("Gói SSE của máy nội bộ không phải một đối tượng JSON.")

    # vLLM báo lỗi giữa dòng chảy bằng chính một gói data: có khoá "error".
    # Không đọc khoá này thì lỗi ấy im lặng biến thành "câu trả lời rỗng".
    if "error" in du_lieu:
        chi_tiet = du_lieu["error"]
        if isinstance(chi_tiet, dict):
            chi_tiet = chi_tiet.get("message", chi_tiet)
        raise LoiMayNoiBoTraLoiSai(
            "Máy nội bộ báo lỗi giữa lúc đang sinh chữ: {}".format(chi_tiet)
        )

    mo_hinh = du_lieu.get("model")
    if isinstance(mo_hinh, str) and mo_hinh.strip():
        ket_qua["mo_hinh"] = mo_hinh.strip()

    cac_lua_chon = du_lieu.get("choices")
    if isinstance(cac_lua_chon, list) and cac_lua_chon:
        dau = cac_lua_chon[0]
        if isinstance(dau, dict):
            lech = dau.get("delta")
            if isinstance(lech, dict):
                chu = lech.get("content")
                if isinstance(chu, str) and chu != "":
                    ket_qua["chu"] = chu
            ly_do = dau.get("finish_reason")
            if isinstance(ly_do, str) and ly_do:
                ket_qua["xong"] = ly_do

    return ket_qua


def doi_chieu_mo_hinh(da_gui: str, doc_duoc: Optional[str]) -> str:
    """Tên mô hình THẬT để hiện cho người đọc.

    VÌ SAO KHÔNG ĐƯỢC LẤY LUÔN TÊN MÌNH GỬI ĐI

      Tên gửi đi là thứ ta MUỐN. Tên máy chủ trả về là thứ ta ĐANG CÓ. Hai thứ
      ấy lệch nhau được: một bí danh trỏ sang mô hình khác, một máy chủ nạp bản
      lượng tử hoá dưới tên khác, một cấu hình cũ chưa nạp lại. Hiện tên gửi đi
      trong những ca ấy là khai sai tên mô hình — đúng thứ kho này đặt ra để
      chống, và đúng thứ trường `moHinhThat` trong hợp đồng SSE tồn tại để nói.

      Nên: máy chủ có khai tên thì tên ấy THẮNG, kể cả khi nó khác tên ta gửi.
      Máy chủ không khai gì thì mới đành lấy tên gửi đi, vì không còn nguồn nào
      khác — và đó là câu trả lời trung thực nhất có được trong hoàn cảnh ấy.
    """
    if isinstance(doc_duoc, str) and doc_duoc.strip():
        return doc_duoc.strip()
    return da_gui


# ── Cổng mô hình ─────────────────────────────────────────────────────────────


class CongMoHinh:
    """Cổng tới một máy vLLM nội bộ nói API tương thích OpenAI."""

    def __init__(self, cau_hinh: CauHinhPhucVu) -> None:
        if not isinstance(cau_hinh, CauHinhPhucVu):
            raise LoiCauHinh("CongMoHinh cần một CauHinhPhucVu.")
        self.cau_hinh = cau_hinh

    # ── Lời gọi HTTP dùng chung ─────────────────────────────────────────────
    def _mo(self, duong_dan: str, than: Optional[bytes] = None, dong_chay: bool = False):
        """Mở một lời gọi HTTP và trả về đối tượng trả lời, hoặc ném lỗi đã dịch.

        Mọi lỗi mạng đều được DỊCH sang cây lỗi ở trên tại đúng chỗ này. Không
        để một urllib.error trôi lên trên: lớp gọi sẽ phải biết về urllib, và
        người dùng cuối sẽ đọc được một câu tiếng Anh không nói gì về máy của họ.
        """
        yeu_cau = urllib.request.Request(
            self.cau_hinh.duong_dan(duong_dan),
            data=than,
            headers=self.cau_hinh.dau_de(dong_chay=dong_chay),
            method="POST" if than is not None else "GET",
        )
        try:
            return urllib.request.urlopen(yeu_cau, timeout=self.cau_hinh.het_gio_giay)
        except urllib.error.HTTPError as loi:
            # CÓ máy chủ, máy chủ từ chối. Đọc thân trả lời: vLLM nói khá rõ
            # trong đó (sai mã mô hình, quá ngữ cảnh, sai khoá).
            try:
                than_loi = loi.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001 — đọc thân lỗi mà hỏng thì bỏ qua
                than_loi = "(không đọc được thân trả lời)"
            raise LoiMayNoiBoTraLoiSai(
                "Máy nội bộ trả mã {} cho {}. Máy ĐANG CHẠY nhưng từ chối yêu cầu — "
                "khởi động lại không giúp gì. Máy chủ nói: {}".format(
                    loi.code, duong_dan, than_loi
                )
            )
        except urllib.error.URLError as loi:
            raise LoiKhongNoiDuocMayNoiBo(self._cau_bao_khong_noi_duoc(loi.reason))
        except socket.timeout:
            raise LoiKhongNoiDuocMayNoiBo(
                self._cau_bao_khong_noi_duoc(
                    "quá {} giây không trả lời".format(self.cau_hinh.het_gio_giay)
                )
            )
        except OSError as loi:
            # socket.timeout là con của OSError từ Python 3.10; bắt cả ở đây để
            # bài này chạy đúng trên cả 3.9 lẫn bản mới hơn.
            raise LoiKhongNoiDuocMayNoiBo(self._cau_bao_khong_noi_duoc(loi))

    def _cau_bao_khong_noi_duoc(self, nguyen_nhan) -> str:
        """Câu báo lỗi cho người đọc. LUÔN chứa chữ 'nội bộ'.

        Người dùng phải biết ngay hỏng nằm ở MÁY CỦA HỌ, không phải ở một dịch vụ
        xa nào đó — vì hệ này không gọi dịch vụ xa nào cả.
        """
        return (
            "Không nối được tới máy mô hình NỘI BỘ tại {} ({}). "
            "Trợ lý này CHỈ gọi mô hình chạy trên máy nội bộ và KHÔNG có đường dự "
            "phòng ra nhà cung cấp bên ngoài, nên câu hỏi của bạn không đi đâu cả. "
            "Hãy kiểm tra máy phục vụ vLLM đã chạy chưa và biến BDSG_VLLM_URL có "
            "trỏ đúng không.".format(self.cau_hinh.url, nguyen_nhan)
        )

    # ── GET /models ─────────────────────────────────────────────────────────
    def danh_sach_mo_hinh(self) -> List[Dict[str, str]]:
        """Hỏi máy nội bộ đang nạp những mô hình nào.

        Trả về danh sách dict `{"ma": ..., "chu_so_huu": ...}`. Đây cũng là phép
        thử sống-chết rẻ nhất: gọi được đường này nghĩa là máy chủ đang chạy và
        đường dẫn /v1 đúng.
        """
        tra_loi = self._mo("models")
        try:
            tho = tra_loi.read().decode("utf-8", errors="replace")
        finally:
            tra_loi.close()

        try:
            du_lieu = json.loads(tho)
        except ValueError:
            raise LoiMayNoiBoTraLoiSai(
                "Đường {} trả về thứ không phải JSON. Địa chỉ có thể đang trỏ vào "
                "một dịch vụ khác chứ không phải vLLM.".format(
                    self.cau_hinh.duong_dan("models")
                )
            )

        cac_muc = du_lieu.get("data") if isinstance(du_lieu, dict) else None
        if not isinstance(cac_muc, list):
            raise LoiMayNoiBoTraLoiSai(
                "Trả lời của {} thiếu mảng 'data' theo đúng chuẩn OpenAI.".format(
                    self.cau_hinh.duong_dan("models")
                )
            )

        ket_qua = []
        for muc in cac_muc:
            if isinstance(muc, dict) and isinstance(muc.get("id"), str):
                ket_qua.append(
                    {
                        "ma": muc["id"],
                        "chu_so_huu": str(muc.get("owned_by", "")),
                    }
                )
        return ket_qua

    # ── POST /chat/completions (dòng chảy) ──────────────────────────────────
    def hoi_dong_chay(
        self,
        tin_nhan: Sequence[Dict[str, str]],
        nhiet: float = 0.7,
        tran_token_ra: Optional[int] = None,
        thu_thap: Optional[Dict[str, object]] = None,
    ) -> Iterator[str]:
        """Hỏi mô hình, sinh ra từng mẩu chữ một.

        `tin_nhan` theo đúng dạng OpenAI: [{"role": "user", "content": "..."}].
        Chat template của Gemma do CHÍNH vLLM áp, đọc từ tokenizer đi kèm trọng
        số Google. Ở đây KHÔNG tự ghép chuỗi lời nhắc: tokenizer 6.400 token của
        BDSG là một nhánh nghiên cứu riêng và không được chạm vào đường này.

        `thu_thap` (tuỳ chọn): một dict sẽ được điền các khoá "mo_hinh_that",
        "so_mau", "ly_do_dung". Dùng dict thay vì giá trị trả về của hàm sinh vì
        nơi gọi lặp bằng vòng `for` không bao giờ thấy giá trị trả về ấy — mà
        `moHinhThat` trong hợp đồng SSE thì bắt buộc phải lấy được.
        """
        if thu_thap is None:
            thu_thap = {}
        thu_thap["mo_hinh_that"] = self.cau_hinh.ma_mo_hinh
        thu_thap["so_mau"] = 0
        thu_thap["ly_do_dung"] = None

        than = json.dumps(
            {
                "model": self.cau_hinh.ma_mo_hinh,
                "messages": list(tin_nhan),
                "stream": True,
                "temperature": nhiet,
                "max_tokens": tran_token_ra or self.cau_hinh.tran_token_ra,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        tra_loi = self._mo("chat/completions", than=than, dong_chay=True)
        bo_doc = BoDocSSE()
        mo_hinh_may_chu_khai: Optional[str] = None
        da_xong_sach = False

        try:
            while True:
                try:
                    goi = tra_loi.read(4096)
                except socket.timeout:
                    raise LoiKhongNoiDuocMayNoiBo(
                        self._cau_bao_khong_noi_duoc(
                            "đứt giữa chừng, quá {} giây không có chữ mới".format(
                                self.cau_hinh.het_gio_giay
                            )
                        )
                    )
                except OSError as loi:
                    raise LoiKhongNoiDuocMayNoiBo(
                        self._cau_bao_khong_noi_duoc("đứt giữa chừng ({})".format(loi))
                    )

                if not goi:
                    break

                for goi_json in bo_doc.nap(goi):
                    boc = boc_mau_chu(goi_json)
                    if boc["mo_hinh"]:
                        mo_hinh_may_chu_khai = boc["mo_hinh"]
                    if boc["xong"]:
                        if boc["xong"] == "[DONE]":
                            da_xong_sach = True
                        else:
                            thu_thap["ly_do_dung"] = boc["xong"]
                    if boc["chu"] is not None:
                        thu_thap["so_mau"] = int(thu_thap["so_mau"]) + 1  # type: ignore[arg-type]
                        yield boc["chu"]
        finally:
            try:
                tra_loi.close()
            except Exception:  # noqa: BLE001 — đóng mà hỏng thì không cứu được gì
                pass
            thu_thap["mo_hinh_that"] = doi_chieu_mo_hinh(
                self.cau_hinh.ma_mo_hinh, mo_hinh_may_chu_khai
            )

        # ── Phát hiện dòng chảy bị cắt ──────────────────────────────────────
        # Im lặng ở đây thì giao diện hiện một câu trả lời cụt như thể nó đã
        # xong — hỏng mà không báo. Nói ra, kể cả khi người dùng đã nhận được
        # phần lớn câu chữ.
        #
        # SỬA 26/09/2026 — phép kiểm cũ CHỈ nhìn bộ đệm còn dư, và đã ĐO ĐƯỢC là
        # nó để lọt ca hay gặp nhất: máy chủ (hoặc một proxy đứng giữa) đóng kết
        # nối ĐÚNG vào ranh giới một dòng SSE trọn vẹn. Khi ấy bộ đệm rỗng, vòng
        # đọc thấy b"" rồi thoát êm, và hàm này trả về như thể câu trả lời đã
        # xong. Đo bằng một máy chủ thật đóng sạch sau hai gói: nhận đúng "Xin
        # chao " rồi KHÔNG có lỗi nào.
        #
        # Dấu hiệu đúng của "đã xong" không phải là bộ đệm rỗng, mà là máy chủ
        # có nói lời kết hay không. Nhận CẢ HAI lời kết, vì không phải máy chủ
        # tương thích OpenAI nào cũng gửi đủ hai:
        #   - nhãn `data: [DONE]`            → da_xong_sach
        #   - `finish_reason` trong gói cuối → thu_thap["ly_do_dung"]
        # Không có cái nào trong hai thì dòng chảy đã đứt, dù bộ đệm sạch.
        if not da_xong_sach and thu_thap.get("ly_do_dung") is None:
            if bo_doc.con_du().strip():
                ly_do = "dòng chảy kết thúc giữa một gói dở dang, câu trả lời bị cắt"
            else:
                ly_do = (
                    "dòng chảy kết thúc mà máy chủ chưa gửi dấu kết thúc nào "
                    "(không có [DONE], không có finish_reason) — câu trả lời bị cắt"
                )
            raise LoiKhongNoiDuocMayNoiBo(self._cau_bao_khong_noi_duoc(ly_do))
