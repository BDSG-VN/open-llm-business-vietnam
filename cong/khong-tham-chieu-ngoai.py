#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cong/khong-tham-chieu-ngoai.py — CỔNG 6/6: chặn tham chiếu tới một dự án NGOÀI, và chặn
một ngôn ngữ đã bị đưa ra khỏi phạm vi dự án.

VÌ SAO CỔNG NÀY TỒN TẠI

  Ngày 26/09/2026 chủ dự án chốt hai điều:

    (1) Phạm vi ngôn ngữ còn đúng HAI: tiếng Việt là chính, tiếng Anh là phụ. Một ngôn ngữ
        thứ ba từng có mặt trong tài liệu bị đưa ra khỏi phạm vi.
    (2) Kiến trúc và bộ huấn luyện là do BDSG viết ĐỘC LẬP, dựng từ kỹ thuật đã công bố
        trong các bài báo (RMSNorm arXiv:1910.07467, RoPE arXiv:2104.09864,
        GQA arXiv:2305.13245, SwiGLU arXiv:2002.05202, pre-norm arXiv:2002.04745).
        Kho KHÔNG dẫn xuất từ mã của một dự án nào khác, nên tài liệu không được nhắc tới
        dự án ấy như thượng nguồn của mình.

  Điều (2) mới là chỗ cần cổng, và lý do phải nói cho kỹ:

    Nếu chỉ XOÁ TÊN mà vẫn giữ mã dẫn xuất thì hỏng cả hai đầu. Về giấy phép: Apache-2.0
    điều 4 buộc giữ ghi công và nêu rõ chỗ đã sửa — xoá tên là vi phạm. Về sự thật: đó là
    lời khai sai về nguồn gốc mô hình, đúng thứ mà kho này đặt ra để chống (xem bảng trạng
    thái trong README: "bdsg_la_trong_so_bdsg = false cho mọi mã").

    Cách làm đúng là VIẾT THẬT TỪ ĐẦU từ bài báo, rồi khoá lại bằng cổng để tên cũ không
    lặng lẽ quay về qua một lần sao chép tài liệu. Cổng này là cái khoá ấy. Nó KHÔNG tự
    chứng minh được mã là độc lập — nó chỉ chứng minh tài liệu không còn khai sai nguồn.
    Ranh giới ấy phải nói thẳng, vì một cổng được tin quá mức còn nguy hơn không có cổng.

  Một tên ĐƯỢC GIỮ có chủ ý: tên trường cấu hình theo chuẩn thư viện `transformers`
  (`hidden_size`, `num_hidden_layers`, `num_attention_heads`, `num_key_value_heads`,
  `intermediate_size`, `vocab_size`, `rms_norm_eps`, `rope_theta`, `tie_word_embeddings`).
  Đó là quy ước chung của cả hệ sinh thái — Llama, Mistral, Qwen đều dùng — không phải của
  riêng ai, và giữ nó là điều kiện để mô hình nạp được ở nơi khác. Bài tự kiểm có một dòng
  sạch gồm đúng các tên ấy, để bất kỳ ai siết cổng về sau cũng lập tức thấy chúng phải lọt.

PHẠM VI TỰ KHAI

  CÓ quét: mọi tệp văn bản trong cây thư mục gốc (kể cả .json, .jsonl, .sh, .md, .py),
    theo sáu luật:
      1. tên dự án ngoài — mọi cách viết hoa, và cả biến thể nối bằng '-', '_' hoặc khoảng
         trắng; không dùng ranh giới từ, nên nó bắt được cả trong URL và trong tên tệp.
      2. tên ngôn ngữ đã bị bỏ, viết tiếng Việt CÓ dấu và KHÔNG dấu.
      3. tên ngôn ngữ ấy viết bằng tiếng Anh.
      4. ký tự chữ Hán (khối CJK chính U+4E00–U+9FFF và khối mở rộng A U+3400–U+4DBF).
      5. mã ngôn ngữ dạng `zh` + gạch nối + mã vùng/hệ chữ.
      6. tên một thư viện tách từ chỉ dùng cho ngôn ngữ ấy.

  KHÔNG quét:
    - Nội dung tệp nhị phân. Tệp nhị phân có đuôi CHƯA khai thì bị báo hỏng (fail-closed),
      chứ không bỏ qua im lặng.
    - Lịch sử git. Cổng quét cây thư mục hiện tại; commit cũ vẫn giữ nguyên tên. Gỡ tên
      khỏi lịch sử là việc khác, và với kho đã đẩy công khai thì gần như không làm được.
    - Thư mục .git, .venv và các thư mục đệm (khai ở BO_QUA_THU_MUC).

  CHỖ MÙ ĐÃ KHAI — đọc trước khi tưởng cổng này chặn hết:
    - Mã `zh` TRẦN (không có gạch nối và mã vùng) KHÔNG bị chặn, và đây là lựa chọn có chủ
      ý chứ không phải sót. "zh" nằm trong "Zhang" — họ của một trong hai tác giả bài báo
      RMSNorm mà chính kho này BẮT BUỘC phải trích dẫn. Một cổng cắt oan tên tác giả bài
      báo sẽ bị tắt, và một cổng bị tắt là một cổng không tồn tại. Hệ quả phải chấp nhận:
      một giá trị enum `zh` trần lọt qua cổng này. Bài tự kiểm có dòng đối chứng cho cả
      hai ca ấy.
    - Chữ Hán trong TÊN TỆP (không phải trong nội dung) không bị bắt. Chưa gặp, chưa viết
      luật, nên đừng tưởng là đã chặn.
    - Tên tác giả/tài khoản của dự án ngoài KHÔNG có trong luật. Ở dạng URL thì nó luôn đi
      kèm tên dự án nên đã bị luật 1 bắt; ở dạng tên người trần thì lọt. Cố ý không thêm:
      một bộ dò mang theo tên riêng của người khác thì chính tệp cổng trở thành chỗ lưu
      tên ấy trong kho công khai — đúng lỗi mà khong-danh-tinh.py đã mắc và đã sửa.

VÌ SAO TỆP NÀY KHÔNG CHỨA CHUỖI NÀO NÓ CHẶN — KỂ CẢ TRONG MẪU THỬ

  Bản đầu của cong/khong-danh-tinh.py viết thẳng bốn danh tính thật vào phần tự kiểm làm
  mẫu thử. Nó ĐẠT — vì cổng ấy tự loại mình khỏi phạm vi quét — rồi được đẩy lên kho công
  khai, mang theo đúng bốn thứ nó sinh ra để chặn.

  Bài học chung: **một bộ dò mang theo danh sách thứ nó dò thì chính nó là chỗ rò.**

  Cổng này chữa bằng hai việc, phải giữ cả hai:

    a) NÓ TỰ QUÉT CHÍNH NÓ. Không có dòng loại trừ nào cho `__file__`. Bài tự kiểm còn
       chép nguyên mã nguồn của chính tệp này vào thư mục tạm rồi quét, và ĐÒI kết quả là
       0 vi phạm, 0 miễn trừ. Đó là phép thử trực tiếp cho câu "cổng này sạch", chứ không
       phải lời hứa trong chú thích.
    b) MỌI chuỗi bị cấm đều được GHÉP LÚC CHẠY từ hai mảnh, ví dụ "tiếng " + "Trung" thay
       vì viết liền. Trong tệp trên đĩa, giữa hai mảnh luôn có dấu nháy và dấu cộng, nên
       chuỗi cấm KHÔNG BAO GIỜ xuất hiện nguyên vẹn trên một dòng — trong khi biểu thức
       chính quy dựng lúc chạy vẫn là chuỗi đầy đủ và vẫn cắn đúng.

  Thủ thuật ghép chuỗi ấy áp cho cả biểu thức chính quy lẫn mẫu thử. Ký tự chữ Hán dùng
  chr(0x4E2D) vì cùng lý do: viết ký tự thật vào đây thì cổng tự bắt mình.

  Hệ quả với tài liệu: cong/README.md cũng KHÔNG viết thẳng các chuỗi này, và cũng vì lý
  do trên. Muốn biết chính xác cổng chặn chữ gì thì đọc phần khai biến ngay dưới đây —
  đó là nguồn duy nhất, và nó đọc được dù không viết chuỗi ra.

MÃ THOÁT: 0 sạch · 1 có vi phạm · 2 cổng tự vỡ (fail-closed).
Viết ngày: 26/09/2026.
"""

import argparse
import os
import re
import shutil
import sys
import tempfile

BO_QUA_THU_MUC = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".idea", ".vscode",
}

DUOI_NHI_PHAN_DA_KHAI = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf",
    ".pdf", ".zip", ".gz", ".bz2", ".xz", ".tar", ".parquet", ".arrow", ".npy", ".npz",
    ".safetensors", ".pth", ".bin", ".onnx", ".gguf", ".mp4", ".webm", ".mp3", ".wav",
}

# ── Miễn trừ nội dòng ─────────────────────────────────────────────────────────
# Cùng cú pháp với khong-ha-tang và khong-lo-hong, và ghép lúc chạy vì cùng một lý do:
# viết thẳng thì mọi dòng trong chính tệp này có nhắc tới cú pháp ấy sẽ TỰ miễn trừ mình,
# và con số "đang dùng N miễn trừ" sai ngay từ dòng đầu.
#
# Vì sao cổng này CÓ miễn trừ, trong khi khong-bi-mat và khong-du-lieu-cam thì không:
# hai cổng kia tuyệt đối — không lý do nào đủ tốt để giữ một khoá thật trong kho công khai.
# Cổng này thì có một ca hợp pháp thật, và ca ấy quan trọng: MỤC LỊCH SỬ THAY ĐỔI. Muốn
# ghi trung thực rằng ngày 26/09/2026 dự án đã BỎ một ngôn ngữ thì phải gọi tên ngôn ngữ
# ấy. Không có đường thoát hợp pháp thì người viết chỉ còn hai lựa chọn: nói dối lịch sử,
# hoặc tắt cổng. Cả hai đều tệ hơn một miễn trừ có ghi lý do.
DAU_MIEN_TRU = "cong" + ":bo-qua"
MIEN_TRU = re.compile(
    re.escape(DAU_MIEN_TRU) + r"\s+khong-tham-chieu-ngoai(?:\s+ly-do=(\S[^\n]*))?"
)

# ── Luật 1: tên dự án ngoài ───────────────────────────────────────────────────
# Ghép từ hai mảnh (xem phần "VÌ SAO TỆP NÀY KHÔNG CHỨA CHUỖI NÀO NÓ CHẶN" ở trên).
# Giữa hai mảnh cho phép tối đa MỘT ký tự nối '-', '_' hoặc khoảng trắng. Không dùng
# \s* hay [\W]* rộng hơn: giữa hai mảnh trong chính dòng mã này là dấu nháy + dấu cộng,
# và một luật rộng tay có thể vô tình khớp qua đó, làm cổng tự bắt mình.
_NGOAI_A = "mini"
_NGOAI_B = "mind"
MAU_TEN_NGOAI = re.compile(_NGOAI_A + r"[-_ ]?" + _NGOAI_B, re.IGNORECASE)

# ── Luật 2 + 3: tên ngôn ngữ đã bị đưa ra khỏi phạm vi ────────────────────────
# Chỉ bắt khi đi SAU chữ "tiếng"/"tieng". Bắt chữ ấy đứng một mình là cắt oan hàng loạt:
# "trung bình", "tập trung", "Trung tâm", "muc_tin_cay = trung-binh" đều là tiếng Việt
# bình thường và có thật trong kho này. Bài tự kiểm có dòng đối chứng cho đúng bốn ca ấy.
_NGON_NGU = "Trung"
MAU_NGON_NGU = re.compile(
    r"ti[eế]ng\s+" + _NGON_NGU
    # Chừa "tiếng trung bình" — cụm hiếm nhưng hợp lệ trong tiếng Việt (nói về âm lượng
    # hoặc quãng giọng). Thà chừa một cụm hiếm còn hơn cắt oan rồi bị tắt cổng.
    + r"(?!\s*b[ìi]nh)",
    re.IGNORECASE,
)
_NGON_NGU_EN = "Chin" + "ese"
MAU_NGON_NGU_EN = re.compile(_NGON_NGU_EN, re.IGNORECASE)

# ── Luật 4: chữ Hán ───────────────────────────────────────────────────────────
# Khối CJK chính + khối mở rộng A. Chữ tiếng Việt có dấu nằm ở Latin Extended Additional
# (U+1EA0–U+1EF9), cách xa hai khối này — có dòng đối chứng trong bài tự kiểm.
#
# BIÊN GIỚI DỰNG BẰNG chr(), KHÔNG BẰNG DÃY THOÁT \\u TRONG CHUỖI NGUỒN. Lý do là một lỗi
# đã xảy ra thật khi viết tệp này ngày 26/09/2026: bản đầu ghi biểu thức dưới dạng dãy
# thoát, và công cụ ghi tệp đã DIỄN GIẢI dãy thoát ấy trước khi ghi, nên trên đĩa nó thành
# bốn ký tự chữ Hán thật — đúng thứ cổng sinh ra để chặn, nằm ngay trong tệp cổng. Bài tự
# kiểm bắt được ngay ở lần chạy đầu (phần 4: quét bản sao mã nguồn của chính cổng), và đó
# là lý do phần thử ấy phải tồn tại. Với chr() thì trên đĩa chỉ có chữ số hex, không có
# cách nào một công cụ trung gian biến chúng thành ký tự thật.
_HAN_KHOI = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF))
MAU_CHU_HAN = re.compile("[" + "".join(chr(a) + "-" + chr(b) for a, b in _HAN_KHOI) + "]")

# ── Luật 5: mã ngôn ngữ ───────────────────────────────────────────────────────
# Rộng hơn một chút so với yêu cầu tối thiểu (`zh` + '-CN'): thêm các mã vùng và mã hệ
# chữ khác, vì chúng cùng chỉ một ngôn ngữ và bỏ sót thì luật này thành hình thức.
# BẮT BUỘC phải có gạch nối + mã theo sau — xem "CHỖ MÙ ĐÃ KHAI" về chữ "Zhang".
MAU_MA_NGON_NGU = re.compile("zh" + r"[-_](?:CN|TW|HK|MO|SG|Hans|Hant)\b", re.IGNORECASE)

# ── Luật 6: thư viện tách từ ──────────────────────────────────────────────────
# Không đặt ranh giới từ: chuỗi này không nằm trong từ nào khác, và bỏ \b thì bắt được cả
# dạng ghim phiên bản kiểu "<tên>==0.42.1" lẫn dạng viết trong tên tệp.
_THU_VIEN = "jie" + "ba"
MAU_THU_VIEN = re.compile(_THU_VIEN, re.IGNORECASE)

LUAT = (
    ("ten-du-an-ngoai", MAU_TEN_NGOAI,
     "tên một dự án ngoài — kho này viết độc lập từ bài báo, không dẫn xuất"),
    ("ngon-ngu-da-bo", MAU_NGON_NGU,
     "tên ngôn ngữ đã bị đưa ra khỏi phạm vi 26/09/2026 (viết tiếng Việt)"),
    ("ngon-ngu-da-bo-en", MAU_NGON_NGU_EN,
     "tên ngôn ngữ đã bị đưa ra khỏi phạm vi 26/09/2026 (viết tiếng Anh)"),
    ("chu-han", MAU_CHU_HAN,
     "ký tự chữ Hán"),
    ("ma-ngon-ngu", MAU_MA_NGON_NGU,
     "mã ngôn ngữ của ngôn ngữ đã bị bỏ"),
    ("thu-vien-tach-tu", MAU_THU_VIEN,
     "thư viện tách từ chỉ dùng cho ngôn ngữ đã bị bỏ"),
)


def duyet_tep(goc):
    """Đi hết cây thư mục. KHÔNG có ngoại lệ nào cho chính tệp cổng — đó là chủ ý."""
    for thu_muc, thu_muc_con, ten_tep in os.walk(goc):
        thu_muc_con[:] = [t for t in thu_muc_con if t not in BO_QUA_THU_MUC]
        for ten in sorted(ten_tep):
            yield os.path.join(thu_muc, ten)


def la_nhi_phan(duong_dan):
    """Một byte NUL trong 8 KiB đầu ⇒ coi là nhị phân.

    Vì sao đọc byte thô chứ không tin đuôi tệp: một byte NUL làm `grep` im lặng coi cả
    tệp là nhị phân rồi bỏ qua, còn lệnh `file` chỉ báo "data". Đã gặp thật ở dự án này
    và suýt dẫn tới kết luận sai rằng một tuyến mã chưa được viết. Ở đây tệp nhị phân
    đuôi lạ bị BÁO HỎNG, không được bỏ qua im lặng.
    """
    with open(duong_dan, "rb") as f:
        return b"\0" in f.read(8192)


def quet_dong(dong):
    """Trả danh sách (mã lỗi, mô tả) cho một dòng. Không đọc trạng thái ngoài."""
    thay = []
    for ma, mau, giai_thich in LUAT:
        khop = mau.search(dong)
        if khop:
            # In lại chuỗi bắt được là ĐÚNG ở cổng này, và cần nói rõ vì sao nó khác
            # khong-bi-mat.py (cổng ấy tuyệt đối không in giá trị ra): thứ bắt được ở đây
            # KHÔNG phải bí mật. Nó là một cái tên phải bị gỡ, và người sửa cần biết chính
            # xác luật nào cắn vào chữ nào — nhất là với luật chữ Hán, nơi ký tự có thể
            # nhìn không ra trên terminal.
            thay.append((ma, "%s: %r (cột %d)" % (giai_thich, khop.group(0), khop.start() + 1)))
    return thay


def quet_kho(goc):
    """Trả (vi_pham, loi_cong, so_mien_tru, so_tep_da_doc)."""
    vi_pham = []
    loi_cong = []
    so_mien_tru = 0
    so_tep = 0

    for duong_dan in duyet_tep(goc):
        tuong_doi = os.path.relpath(duong_dan, goc)
        _, duoi = os.path.splitext(duong_dan.lower())
        try:
            if la_nhi_phan(duong_dan):
                if duoi in DUOI_NHI_PHAN_DA_KHAI:
                    continue
                loi_cong.append((tuong_doi,
                                 "nhị phân đuôi '%s' chưa khai — không chứng minh được là sạch"
                                 % (duoi or "(không có)")))
                continue
            so_tep += 1
            with open(duong_dan, "r", encoding="utf-8", errors="replace") as f:
                for so_dong, dong in enumerate(f, start=1):
                    mt = MIEN_TRU.search(dong)
                    if mt:
                        if mt.group(1) and mt.group(1).strip():
                            so_mien_tru += 1
                            continue
                        vi_pham.append((tuong_doi, so_dong, "mien-tru-khong-ly-do",
                                        "có dấu miễn trừ nhưng thiếu ly-do="))
                        continue
                    for ma, chi_tiet in quet_dong(dong):
                        vi_pham.append((tuong_doi, so_dong, ma, chi_tiet))
        except OSError as loi:
            loi_cong.append((tuong_doi, "không đọc được: %s" % loi.strerror))

    return vi_pham, loi_cong, so_mien_tru, so_tep


def in_bao_cao(goc, vi_pham, loi_cong, so_mien_tru, so_tep):
    print("CỔNG khong-tham-chieu-ngoai — gốc quét: %s" % goc)
    print("  Đã đọc %d tệp văn bản. Miễn trừ nội dòng đang dùng: %d (mỗi cái phải có ly-do=)."
          % (so_tep, so_mien_tru))
    if not vi_pham and not loi_cong:
        print("  ĐẠT: không thấy tên dự án ngoài, không thấy ngôn ngữ đã bị đưa ra khỏi phạm vi.")
        print("  NHẮC: cổng này KHÔNG chứng minh được mã là viết độc lập — nó chỉ chứng minh")
        print("        tài liệu không còn khai sai nguồn gốc. Hai việc ấy khác nhau.")
        print("        Nó cũng KHÔNG quét lịch sử git: commit cũ vẫn giữ nguyên tên.")
        return
    if vi_pham:
        print("  HỎNG: %d vị trí." % len(vi_pham))
        for duong_dan, so_dong, ma, chi_tiet in vi_pham:
            print("    %-52s:%-5d [%s] %s" % (duong_dan, so_dong, ma, chi_tiet))
        print("  Cách xử ĐÚNG, theo thứ tự:")
        print("    1. Viết lại câu cho đúng sự thật mới — kiến trúc dựng từ bài báo")
        print("       (RMSNorm arXiv:1910.07467 · RoPE arXiv:2104.09864 · GQA arXiv:2305.13245")
        print("       · SwiGLU arXiv:2002.05202 · pre-norm arXiv:2002.04745), trích BÀI BÁO")
        print("       chứ không trích kho mã nào.")
        print("    2. CHỈ khi thật sự cần gọi tên (mục lịch sử thay đổi) mới miễn trừ:")
        print("       thêm vào cuối dòng   %s khong-tham-chieu-ngoai ly-do=<lý do cụ thể>"
              % DAU_MIEN_TRU)
        print("    ĐỪNG chỉ xoá tên rồi giữ nguyên phần dẫn xuất: vừa phạm Apache-2.0 điều 4")
        print("    (giữ ghi công, nêu rõ chỗ đã sửa), vừa là lời khai sai về nguồn gốc.")
    if loi_cong:
        print("  HỎNG (fail-closed): %d tệp cổng không tự chứng minh được." % len(loi_cong))
        for duong_dan, ghi_chu in loi_cong:
            print("    %-52s %s" % (duong_dan, ghi_chu))


def tu_kiem():
    """Bài thử ngược BẮT BUỘC: dựng thư mục tạm, cài mẫu xấu, và ĐÒI cổng không cắt oan.

    Ba phần, phần nào thiếu thì cổng này chưa đáng tin:
      1. mẫu-phải-bắt  — chứng minh cổng CẮN.
      2. dòng-sạch     — chứng minh cổng KHÔNG cắt oan. Danh sách này quan trọng ngang
                         phần 1: hai ca đầu trong đó là hai ca đã suýt làm cổng vô dụng.
      3. tự quét mã nguồn của CHÍNH cổng này — chứng minh tệp cổng không mang theo thứ
                         nó chặn (lỗi mà khong-danh-tinh.py đã mắc và đã sửa).
    """
    ten = _NGOAI_A + _NGOAI_B                       # dạng thường
    ten_hoa = _NGOAI_A.capitalize() + _NGOAI_B.capitalize()   # dạng viết hoa lạc đà
    ngon_ngu_co_dau = "tiếng " + _NGON_NGU
    ngon_ngu_khong_dau = "tieng " + _NGON_NGU
    chu_han = chr(0x4E2D)                           # một ký tự trong khối CJK chính

    # ── Phần 1: mỗi dòng PHẢI sinh ít nhất một vi phạm ────────────────────────
    mau = [
        "Dây chuyền huấn luyện dựa trên " + ten_hoa + " (Apache-2.0).",
        "Kho thượng nguồn: github.com/mot-tai-khoan/" + ten,
        "Đọc trực tiếp từ model_" + ten + ".py, nhánh f659b55.",
        "PIPELINE=" + ten.upper(),
        "badge: pipeline-" + _NGOAI_A + "-" + _NGOAI_B + "-orange.svg",
        "Ngữ liệu gốc là " + ngon_ngu_co_dau + " + tiếng Anh.",
        "Ngu lieu goc la " + ngon_ngu_khong_dau + " va tieng Anh.",
        "The corpus is " + _NGON_NGU_EN.lower() + " and English.",
        "Một ký tự lọt vào tài liệu: " + chu_han + " — phải bị bắt.",
        '"ngon_ngu": "' + "zh" + '-CN",',
        "requirements: " + _THU_VIEN + "==0.42.1",
    ]

    # ── Phần 2: mỗi dòng PHẢI sạch ────────────────────────────────────────────
    sach = [
        # Hai ca đầu là hai ca đã suýt làm cổng này thành vô dụng:
        # (a) một luật bắt "zh" trần sẽ cắt oan tên tác giả bài báo RMSNorm — đúng bài báo
        #     mà kho này BẮT BUỘC phải trích dẫn. Cổng cắt oan chỗ ấy sẽ bị tắt ngay.
        "RMSNorm — Zhang và Sennrich, arXiv:1910.07467. Zhejiang, zh trần: KHÔNG chặn.",
        # (b) một luật bắt chữ "Trung" đứng một mình sẽ cắt oan tiếng Việt thường ngày,
        #     và cả bốn cụm dưới đây đều CÓ THẬT trong kho này.
        'muc_tin_cay = "trung-binh"; rác tập trung ở ho-so-niem-yet; Trung tâm dữ liệu;',
        "mst_trung_dang_dien_thoai — tên trường trong bo-du-lieu/xuat.py",
        # Tên trường cấu hình chuẩn transformers — ĐƯỢC GIỮ có chủ ý, vì đó là quy ước
        # chung của cả hệ sinh thái và là điều kiện để mô hình nạp được ở nơi khác.
        "hidden_size · num_hidden_layers · num_attention_heads · num_key_value_heads ·",
        "intermediate_size · vocab_size · rms_norm_eps · rope_theta · tie_word_embeddings",
        # Hai mảnh của tên dự án ngoài CÓ mặt nhưng KHÔNG nối liền nhau.
        "kích thước lô mini-batch, và mindset của người viết tài liệu",
        # Chữ tiếng Việt có dấu nằm ở Latin Extended Additional, không phải khối chữ Hán.
        "ắ ẳ ữ ợ ỹ ậ — dấu tiếng Việt, tuyệt đối không được tính là chữ Hán",
        "Thứ tự ngôn ngữ: tiếng Việt là chính, tiếng Anh là phụ.",
        # Cụm hiếm nhưng hợp lệ, được chừa bằng lookahead — xem MAU_NGON_NGU.
        "giọng nam có tiếng trung bình, không phải giọng cao",
    ]

    # ── Phần 3: hai ca miễn trừ ───────────────────────────────────────────────
    # Đây chính là ca hợp pháp đã nói ở đầu tệp: mục LỊCH SỬ THAY ĐỔI phải được phép gọi
    # tên thứ đã bỏ, nếu không thì tài liệu buộc phải nói dối về lịch sử của chính nó.
    mien_tru_co_ly_do = (
        "| 26/09/2026 | Bỏ " + ngon_ngu_co_dau + " khỏi phạm vi dự án ("
        + _NGON_NGU_EN + " removed) | "
        + DAU_MIEN_TRU + " khong-tham-chieu-ngoai ly-do=mục lịch sử thay đổi, "
        "phải gọi tên thứ đã bỏ thì người đọc mới kiểm được |"
    )
    mien_tru_thieu_ly_do = (
        "Ghi chú cũ về " + ngon_ngu_co_dau + "  " + DAU_MIEN_TRU + " khong-tham-chieu-ngoai"
    )

    tam = tempfile.mkdtemp(prefix="tu-kiem-khong-tham-chieu-ngoai-")
    try:
        duong_ban = os.path.join(tam, "ban.md")
        duong_sach = os.path.join(tam, "sach.md")
        duong_mt = os.path.join(tam, "mien-tru.md")
        duong_cong = os.path.join(tam, "ban-sao-cong.py")

        with open(duong_ban, "w", encoding="utf-8") as f:
            f.write("\n".join(mau) + "\n")
        with open(duong_sach, "w", encoding="utf-8") as f:
            f.write("\n".join(sach) + "\n")
        with open(duong_mt, "w", encoding="utf-8") as f:
            f.write(mien_tru_co_ly_do + "\n" + mien_tru_thieu_ly_do + "\n")
        # Chép nguyên mã nguồn của chính cổng này vào phạm vi quét.
        shutil.copyfile(os.path.abspath(__file__), duong_cong)

        vi_pham, loi_cong, so_mien_tru, _ = quet_kho(tam)
    finally:
        shutil.rmtree(tam, ignore_errors=True)

    hong = []

    if loi_cong:
        hong.append("Quét thư mục tạm mà báo lỗi cổng: %r" % (loi_cong,))

    # 1. Mọi dòng trong ban.md phải bị bắt.
    dong_bi_bat = {so for tep, so, _, _ in vi_pham if tep == "ban.md"}
    thieu = sorted(set(range(1, len(mau) + 1)) - dong_bi_bat)
    for so in thieu:
        hong.append("SÓT (không cắn) ban.md dòng %d: %s" % (so, mau[so - 1]))

    # 2. Không dòng nào trong sach.md được bị bắt.
    for tep, so, ma, chi_tiet in vi_pham:
        if tep == "sach.md":
            hong.append("CẮN OAN sach.md dòng %d [%s] %s — nội dung: %s"
                        % (so, ma, chi_tiet, sach[so - 1]))

    # 3. Miễn trừ: đúng 1 cái có lý do, và cái thiếu lý do bị tính là vi phạm.
    if so_mien_tru != 1:
        hong.append("Miễn trừ CÓ lý do phải được đếm đúng 1 lần, đếm được %d." % so_mien_tru)
    mt_vi_pham = [(so, ma) for tep, so, ma, _ in vi_pham if tep == "mien-tru.md"]
    if mt_vi_pham != [(2, "mien-tru-khong-ly-do")]:
        hong.append("Miễn trừ THIẾU lý do phải bị bắt đúng ở dòng 2, thực tế: %r" % (mt_vi_pham,))

    # 4. Bản sao mã nguồn của chính cổng này phải SẠCH TUYỆT ĐỐI.
    #    Đây là phép thử cho câu "cổng không mang theo thứ nó chặn". Nếu ai đó sửa cổng và
    #    vô tình viết thẳng một chuỗi cấm vào mã hay vào mẫu thử, dòng dưới đây đỏ ngay.
    tu_bat = [(so, ma, ct) for tep, so, ma, ct in vi_pham if tep == "ban-sao-cong.py"]
    if tu_bat:
        hong.append("CỔNG TỰ MANG THEO THỨ NÓ CHẶN — mã nguồn của chính nó bị bắt tại: %r"
                    % (tu_bat,))

    print("TỰ KIỂM khong-tham-chieu-ngoai: %d mẫu cài, %d dòng sạch làm đối chứng, "
          "2 ca miễn trừ, và 1 bản sao mã nguồn của chính cổng." % (len(mau), len(sach)))
    if hong:
        for d in hong:
            print("  HỎNG: %s" % d)
        return 1

    print("  ĐẠT: cắn đủ %d mẫu cài (tên dự án ngoài ở 5 cách viết — thường, lạc đà, HOA,"
          % len(mau))
    print("       nối gạch, trong URL và trong tên tệp; tên ngôn ngữ đã bỏ ở 3 cách viết;")
    print("       chữ Hán; mã ngôn ngữ; thư viện tách từ).")
    print("  ĐẠT: KHÔNG cắt oan Zhang và Sennrich (tác giả bài báo RMSNorm mà kho này phải")
    print("       trích dẫn), không cắt oan 'trung bình'/'tập trung'/'Trung tâm', không cắt")
    print("       oan tên trường cấu hình chuẩn transformers, và không cắt oan dấu tiếng Việt.")
    print("  ĐẠT: mã nguồn của CHÍNH cổng này quét ra 0 vi phạm, 0 miễn trừ — mọi chuỗi cấm")
    print("       trong tệp đều được ghép lúc chạy nên không xuất hiện nguyên vẹn trên đĩa.")
    return 0


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Cổng 6/6: chặn tham chiếu tới dự án ngoài và ngôn ngữ đã bị bỏ khỏi phạm vi.")
    bo_phan_tich.add_argument("--goc", default=None,
                              help="thư mục gốc cần quét (mặc định: thư mục cha của cong/)")
    bo_phan_tich.add_argument("--tu-kiem", action="store_true",
                              help="chạy bài thử ngược, chứng minh cổng cắn và không cắt oan")
    tham_so = bo_phan_tich.parse_args()

    if tham_so.tu_kiem:
        return tu_kiem()

    goc = tham_so.goc or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir(goc):
        print("HỎNG: không thấy thư mục gốc '%s'." % goc)
        return 2
    try:
        vi_pham, loi_cong, so_mien_tru, so_tep = quet_kho(goc)
    except Exception as loi:
        print("HỎNG: cổng tự vỡ khi quét (%s: %s). Coi như KHÔNG đạt."
              % (type(loi).__name__, loi))
        return 2

    in_bao_cao(goc, vi_pham, loi_cong, so_mien_tru, so_tep)
    if vi_pham:
        return 1
    if loi_cong:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
