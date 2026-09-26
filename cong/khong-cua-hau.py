#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cong/khong-cua-hau.py — CỔNG 7/7: chặn khuôn "cửa hậu có giao diện đẹp" tái xuất hiện
trong kho.

VÌ SAO CỔNG NÀY TỒN TẠI — ĐO NGÀY 26/09/2026

  BDSG đã có một máy chủ MCP chạy thật. Nó nằm NGOÀI kho này (kho này công khai, máy chủ
  ấy thì không), nên ở đây chỉ ghi số đo, không ghi đường dẫn:

    - 221 dòng, 7 công cụ, nói JSON-RPC qua stdio, phục vụ Unomi CDP + OpenMetadata.
    - OpenMetadata đang quản trị 3 nguồn (một MariaDB, một Postgres, một MySQL).

  Ba giới hạn đã đo, và giới hạn thứ nhất là toàn bộ lý do cổng này ra đời:

    (a) VẬN CHUYỂN LÀ SSH VÀO MÁY CHỦ SẢN PHẨM. Mỗi công cụ dựng một dòng lệnh rồi giao
        cho một tiến trình con chạy nó trên máy chủ đang phục vụ khách, bằng một khoá
        root ghi cứng trong mã. Nói cho đúng tên: mỗi công cụ là MỘT LỆNH TUỲ Ý TRÊN
        PRODUCTION. Đó không phải trình điều khiển, đó là cửa hậu có giao diện đẹp.
    (b) 7 công cụ, một lĩnh vực, một tệp phẳng. Thêm một nền tảng thì phải sửa tệp.
    (c) KHÔNG có lớp quyền, KHÔNG có nhật ký. Tìm ba chữ "quyen", "auth", "nhat_ky"
        trong mã ấy trả về RỖNG. Không trả lời được câu "ai đã làm gì".

  Kho này đang thành một hệ điều hành cho doanh nghiệp, và bốn quyết định kiến trúc đã
  chốt ngày 26/09/2026 nói rằng: MCP là ranh giới lời gọi hệ thống; NHÂN giữ danh tính,
  quyền, hạn mức, nhật ký; TRÌNH ĐIỀU KHIỂN chỉ đổi một lời gọi công cụ thành một lời gọi
  API của nền tảng nó phụ trách; mặc định CHỈ ĐỌC.

  Một trình điều khiển mở tiến trình con để chạy lệnh trên máy khác thì phá cả bốn điều
  cùng lúc — nó vòng qua nhân, nên không có quyền, không có hạn mức, không có nhật ký, và
  không có ranh giới đọc/ghi nào cả. Cổng này khoá đúng khuôn ấy lại, để nó không quay về
  qua một lần sao chép mã.

  CỔNG NÀY KHÔNG LÀM GÌ VỚI MÁY CHỦ MCP CŨ. Nó chỉ chặn khuôn ấy TÁI XUẤT HIỆN TRONG KHO
  NÀY. Ranh giới ấy phải nói thẳng: một cổng được tin quá mức còn nguy hơn không có cổng.

PHẠM VI TỰ KHAI

  CÓ quét: mọi tệp văn bản trong cây thư mục gốc (kể cả .md, .py, .js, .sh, .json), theo
    ba họ luật:

      Họ 1 — GỌI LỆNH HỆ THỐNG BẰNG CHUỖI GHÉP TỪ THAM SỐ
        1a. hàm luôn đi qua trình bao (shell): os + dấu chấm + system, os + dấu chấm +
            popen, và hai hàm getoutput/getstatusoutput của thư viện tiến trình con.
        1b. cờ shell bật (tên cờ là "shell", giá trị True).
        1c. hàm tiến trình con nhận đối số đầu tiên là một CHUỖI f (f-string).
        1d. hàm tiến trình con nhận đối số đầu tiên là một chuỗi được NỐI thêm bằng
            dấu cộng, bằng toán tử định dạng phần trăm, hoặc bằng .format(...).
        1e. một danh sách đối số mà PHẦN TỬ ĐẦU là chương trình ssh — tức là dùng SSH
            làm phương tiện gọi công cụ. Đây chính là khuôn đã đo ở trên.

      Họ 2 — ĐƯỜNG DẪN KHOÁ SSH GHI CỨNG
        2a. một đường dẫn chứa đoạn thư mục khoá của người dùng (dấu gạch chéo, dấu
            chấm, chữ ssh, dấu gạch chéo).
        2b. một đường dẫn kết thúc bằng tên khoá riêng mặc định (id_ + rsa/dsa/ecdsa/
            ed25519), BẮT BUỘC có dấu gạch chéo đứng trước.
        2c. chỉ thị trỏ tệp khoá trong tệp cấu hình SSH (hai từ Identity + File viết
            liền) kèm một đường dẫn. Tên chỉ thị ấy KHÔNG được viết liền ở đây: dòng
            tài liệu này nằm trong phạm vi quét, và bản đầu viết liền đã bị chính bài
            tự kiểm bắt ngay lần chạy đầu, 26/09/2026.
        2d. trên cùng một dòng: chương trình ssh, rồi cờ -i, rồi một đường dẫn tuyệt đối
            hoặc bắt đầu bằng dấu ngã.

      Họ 3 — THỰC THI ĐỘNG
        3a. lời gọi eval kèm dấu mở ngoặc ngay sau.
        3b. lời gọi exec kèm dấu mở ngoặc ngay sau.
        Cả hai chỉ tính khi KHÔNG có dấu chấm hay ký tự chữ đứng ngay trước.

  KHÔNG quét:
    - Nội dung tệp nhị phân. Tệp nhị phân có đuôi CHƯA khai thì bị báo hỏng
      (fail-closed), chứ không bỏ qua im lặng.
    - Lịch sử git. Cổng quét cây thư mục hiện tại.
    - Thư mục .git, .venv và các thư mục đệm (khai ở BO_QUA_THU_MUC).

  CHỖ MÙ ĐÃ KHAI — đọc trước khi tưởng cổng này chặn hết. Mỗi mục dưới đây là một lỗ
  thủng CÓ THẬT, khai ra vì một cổng không nói rõ chỗ mù của mình sẽ được hiểu là bảo vệ
  toàn diện, và đó là lúc nó nguy hiểm hơn cả không có cổng:

    - LỆNH DỰNG Ở DÒNG KHÁC THÌ LỌT. Cổng đọc từng dòng một. Nếu chuỗi lệnh được ghép ở
      dòng trên rồi dòng dưới chỉ viết `chay(lenh)` với `lenh` là một biến, cổng không
      thấy gì. Đây là chỗ mù lớn nhất và không vá được bằng biểu thức chính quy — muốn
      vá thật thì phải phân tích cây cú pháp, và đó là một cổng khác, chưa viết.
    - `eval` và `exec` CÓ DẤU CÁCH trước ngoặc thì lọt. Đây là đánh đổi có chủ ý, không
      phải sót: cho phép dấu cách thì mọi câu tiếng Việt kiểu "bộ eval (đánh giá) 227
      câu" sẽ bị cắt oan. Một cổng cắt oan sẽ bị tắt, và một cổng bị tắt là một cổng
      không tồn tại.
    - `sh -c` / `bash -c` trong một danh sách đối số KHÔNG có luật. Cùng lý do: chuỗi ấy
      xuất hiện tự nhiên trong tài liệu, và luật cho nó sẽ cắt oan nhiều hơn bắt đúng.
    - Cổng KHÔNG biết dữ liệu đến từ đâu. Nó không phân biệt được `eval` trên hằng số với
      `eval` trên thân yêu cầu. Nó coi MỌI lời gọi động là vi phạm — fail-closed — và
      đường thoát hợp pháp là miễn trừ nội dòng có ghi lý do.
    - Ngôn ngữ khác Python/JS (Go, PHP, Rust) chưa có luật riêng. Một số khuôn trùng tình
      cờ sẽ bị bắt, nhưng đừng coi đó là đã phủ.

VÌ SAO TỆP NÀY KHÔNG CHỨA NGUYÊN VẸN CHUỖI NÀO NÓ CHẶN

  Bản đầu của cong/khong-danh-tinh.py viết thẳng bốn danh tính thật vào phần tự kiểm làm
  mẫu thử. Nó ĐẠT — vì cổng ấy tự loại mình khỏi phạm vi quét — rồi được đẩy lên kho công
  khai, mang theo đúng bốn thứ nó sinh ra để chặn.

  Bài học chung: MỘT BỘ DÒ MANG THEO DANH SÁCH THỨ NÓ DÒ THÌ CHÍNH NÓ LÀ CHỖ RÒ.

  Cổng này chữa bằng hai việc, phải giữ cả hai:

    a) NÓ TỰ QUÉT CHÍNH NÓ. Không có dòng loại trừ nào cho __file__. Bài tự kiểm còn chép
       nguyên mã nguồn của chính tệp này vào thư mục tạm rồi quét, và ĐÒI kết quả là
       0 vi phạm, 0 miễn trừ.
    b) MỌI chuỗi bị cấm đều được GHÉP LÚC CHẠY từ hai mảnh trở lên. Ví dụ tên hàm chạy
       lệnh hệ thống được viết thành hai mảnh có dấu nháy và dấu cộng ở giữa, nên trên
       đĩa chuỗi cấm KHÔNG BAO GIỜ xuất hiện nguyên vẹn trên một dòng — trong khi biểu
       thức chính quy dựng lúc chạy vẫn là chuỗi đầy đủ và vẫn cắn đúng.

  Thủ thuật ấy áp cho CẢ biểu thức chính quy LẪN mẫu thử, vì cả hai đều nằm trên đĩa.
  Hệ quả với tài liệu: cong/README.md cũng không viết thẳng các chuỗi này, cùng một lý do
  — cong/README.md nằm trong phạm vi quét. Muốn biết chính xác cổng chặn chữ gì thì đọc
  phần khai biến ngay dưới đây; nó đọc được dù không viết chuỗi ra.

MỘT ĐIỂM KHÁC CÁC CỔNG KHÁC: IN GÌ RA BÁO CÁO

  Với họ 1 và họ 3, cổng IN chuỗi bắt được — đó là một khuôn mã, không phải bí mật, và
  người sửa cần thấy chính xác chỗ nào cắn.
  Với họ 2 thì KHÔNG in, chỉ in vị trí. Đường dẫn khoá là hạ tầng: in ra là làm lộ lần
  thứ hai, lần này vào log CI, mà log CI thường dễ đọc hơn cả kho.

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
# Cùng cú pháp với khong-ha-tang, khong-lo-hong, khong-danh-tinh và
# khong-tham-chieu-ngoai. Ghép lúc chạy vì cùng một lý do với chúng: viết thẳng thì mọi
# dòng trong chính tệp này có nhắc tới cú pháp ấy sẽ TỰ miễn trừ mình, và con số
# "đang dùng N miễn trừ" sai ngay từ dòng đầu.
#
# Vì sao cổng này CÓ miễn trừ, trong khi khong-bi-mat và khong-du-lieu-cam thì không:
# hai cổng kia tuyệt đối. Cổng này có một ca hợp pháp thật và ca ấy quan trọng — TÀI LIỆU
# KIẾN TRÚC PHẢI TRƯNG ĐƯỢC KHUÔN BỊ TỪ CHỐI. Muốn giải thích vì sao SSH-vào-production
# là sai thì phải cho người đọc thấy nó trông như thế nào. Không có đường thoát hợp pháp
# thì người viết chỉ còn hai lựa chọn: mô tả mập mờ, hoặc tắt cổng. Cả hai đều tệ hơn một
# miễn trừ có ghi lý do.
DAU_MIEN_TRU = "cong" + ":bo-qua"
MIEN_TRU = re.compile(
    re.escape(DAU_MIEN_TRU) + r"\s+khong-cua-hau(?:\s+ly-do=(\S[^\n]*))?"
)

# ── Mảnh ghép dùng chung ──────────────────────────────────────────────────────
# Không mảnh nào ở đây là một chuỗi cấm hoàn chỉnh; chúng chỉ thành chuỗi cấm sau khi nối.
_SSH = "s" + "sh"
_TIEN_TRINH = "sub" + "process"
_HAM = r"(?:run|call|check_call|check_output|Popen)"

# ── Họ 1: gọi lệnh hệ thống bằng chuỗi ghép từ tham số ────────────────────────

# 1a. Bốn hàm LUÔN đi qua trình bao, bất kể đối số là gì. Không có cách dùng an toàn nào
#     cho chúng trong một trình điều khiển, nên bắt vô điều kiện.
MAU_LUON_QUA_SHELL = re.compile(
    r"(?:os\." + "system" + r"|os\." + "popen"
    + r"|" + _TIEN_TRINH + r"\." + "getoutput"
    + r"|" + _TIEN_TRINH + r"\." + "getstatusoutput" + r")\s*\("
)

# 1b. Cờ bật trình bao. Bắt cả dạng có khoảng trắng quanh dấu bằng.
MAU_CO_SHELL = re.compile(r"\b" + "shell" + r"\s*=\s*" + "True" + r"\b")

# 1c. Đối số đầu là một chuỗi f. Đây là dạng ghép-từ-tham-số phổ biến nhất năm 2026, và
#     là dạng dễ đọc nhầm thành an toàn nhất vì nó trông gọn.
MAU_LENH_CHUOI_F = re.compile(_TIEN_TRINH + r"\." + _HAM + r"\(\s*f[\"']")

# 1d. Đối số đầu là một chuỗi rồi NỐI thêm: dấu cộng, toán tử định dạng phần trăm, hoặc
#     .format(...). Cố ý KHÔNG bắt dạng `chay(bien)` với bien là biến — xem CHỖ MÙ ĐÃ KHAI.
MAU_LENH_CHUOI_NOI = re.compile(
    _TIEN_TRINH + r"\." + _HAM + r"\(\s*[\"'][^\"']*[\"']\s*(?:\+|%|\.format\()"
)

# 1e. Danh sách đối số mà PHẦN TỬ ĐẦU là chương trình ssh. Đây đúng là khuôn đã đo ngày
#     26/09/2026. Luật đòi dấu mở ngoặc/ngoặc vuông + dấu nháy + tên chương trình + dấu
#     nháy + dấu phẩy, nên một câu văn nhắc tới SSH KHÔNG bị bắt — và câu văn ấy có trong
#     dòng đối chứng của bài tự kiểm.
MAU_SSH_LAM_VAN_CHUYEN = re.compile(r"[\[(]\s*[\"']" + _SSH + r"[\"']\s*,", re.IGNORECASE)

# ── Họ 2: đường dẫn khoá SSH ghi cứng ─────────────────────────────────────────

# 2a. Đoạn thư mục khoá của người dùng. Ba tên bị CHỪA vì chúng không phải khoá riêng:
#     tệp cấu hình, danh sách máy đã biết, danh sách khoá được phép. Khoá công khai (.pub)
#     cũng được chừa — công bố khoá công khai là việc bình thường.
_THU_MUC_KHOA = "/." + _SSH + "/"
MAU_KHOA_TRONG_THU_MUC = re.compile(
    re.escape(_THU_MUC_KHOA)
    + r"(?!config\b|known_hosts\b|authorized_keys\b)"
    + r"(?![\w.\-]*\.pub\b)"
    + r"[\w.\-]+"
)

# 2b. Tên khoá riêng mặc định, BẮT BUỘC có dấu gạch chéo đứng trước.
#     Vì sao bắt buộc: cong/khong-bi-mat.py có bảng dò liệt kê đúng các tên ấy dưới dạng
#     khoá từ điển, không kèm đường dẫn. Một luật bắt tên trần sẽ cắt oan chính cổng bí
#     mật của kho này — và cổng cắt oan cổng khác thì chắc chắn bị tắt. Có dòng đối chứng
#     lấy nguyên văn từ tệp ấy trong bài tự kiểm.
MAU_TEN_KHOA_MAC_DINH = re.compile(r"/" + "id_" + r"(?:rsa|dsa|ecdsa|ed25519)\b(?!\.pub)")

# 2c. Chỉ thị trỏ khoá trong tệp cấu hình SSH.
_CHI_THI_KHOA = "Identity" + "File"
MAU_CHI_THI_KHOA = re.compile(_CHI_THI_KHOA + r"\s+[^\s#]+", re.IGNORECASE)

# 2d. Trên cùng một dòng: chương trình ssh, rồi cờ chỉ định tệp khoá, rồi một đường dẫn.
#     Bắt được cả dạng dòng lệnh lẫn dạng danh sách đối số đã trích dẫn.
#
#     VÍ DỤ ĐẦY ĐỦ CỐ Ý KHÔNG VIẾT RA ĐÂY. Bản đầu của tệp này có viết, và bài tự kiểm
#     bắt ngay ở lần chạy đầu tiên (26/09/2026): dòng chú thích giải thích luật lại
#     chính là dòng vi phạm luật. Đó đúng là lý do phần 4 của bài tự kiểm — quét bản
#     sao mã nguồn của chính cổng — phải tồn tại. Muốn xem khuôn đầy đủ thì đọc phần
#     ghép chuỗi trong tu_kiem(), nơi nó được dựng lúc chạy chứ không nằm trên đĩa.
MAU_SSH_CO_CO_I = re.compile(
    r"\b" + _SSH + r"\b[^\n]{0,120}?[\"'\s,]-i[\"'\s,]+\s*[\"']?[~/][^\s\"',]+",
    re.IGNORECASE,
)

# ── Họ 3: thực thi động ───────────────────────────────────────────────────────
# Chặn trước dấu chấm và ký tự chữ. Ba dương tính giả CÓ THẬT trong kho này mà luật này
# phải tránh, cả ba đều có dòng đối chứng trong bài tự kiểm:
#   - mo_hinh.eval() — chế độ suy luận của PyTorch, 15 chỗ trong mo-hinh/ và huan-luyen/.
#   - mau.exec(van)  — RegExp.exec của JavaScript, trong chat/chat.js.
#   - ast.literal_eval(...) — bộ phân tích an toàn; chữ đứng trước là dấu gạch dưới.
MAU_THUC_THI_EVAL = re.compile(r"(?<![\w.])" + "eval" + r"\(")
MAU_THUC_THI_EXEC = re.compile(r"(?<![\w.])" + "exec" + r"\(")

# (mã lỗi, mẫu, giải thích, có in chuỗi bắt được không)
LUAT = (
    ("lenh-qua-shell", MAU_LUON_QUA_SHELL, True,
     "hàm luôn chạy qua trình bao — mọi tham số thành cú pháp shell"),
    ("co-shell-bat", MAU_CO_SHELL, True,
     "cờ trình bao đang bật — tham số thành cú pháp shell"),
    ("lenh-chuoi-f", MAU_LENH_CHUOI_F, True,
     "dòng lệnh dựng bằng chuỗi f — đây là ghép lệnh từ tham số"),
    ("lenh-chuoi-noi", MAU_LENH_CHUOI_NOI, True,
     "dòng lệnh dựng bằng nối chuỗi — đây là ghép lệnh từ tham số"),
    ("ssh-lam-van-chuyen", MAU_SSH_LAM_VAN_CHUYEN, True,
     "SSH làm phương tiện gọi công cụ — đó là lệnh tuỳ ý trên máy khác, không phải API"),
    ("khoa-ssh-ghi-cung", MAU_KHOA_TRONG_THU_MUC, False,
     "đường dẫn khoá riêng SSH ghi cứng"),
    ("khoa-ssh-ten-mac-dinh", MAU_TEN_KHOA_MAC_DINH, False,
     "đường dẫn tới khoá riêng SSH tên mặc định"),
    ("khoa-ssh-chi-thi", MAU_CHI_THI_KHOA, False,
     "chỉ thị trỏ tệp khoá riêng SSH"),
    ("khoa-ssh-co-i", MAU_SSH_CO_CO_I, False,
     "gọi ssh kèm cờ chỉ định tệp khoá"),
    ("thuc-thi-dong-eval", MAU_THUC_THI_EVAL, True,
     "thực thi động: cổng không biết dữ liệu đến từ đâu nên tính là vi phạm"),
    ("thuc-thi-dong-exec", MAU_THUC_THI_EXEC, True,
     "thực thi động: cổng không biết dữ liệu đến từ đâu nên tính là vi phạm"),
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
    và suýt dẫn tới kết luận sai rằng một tuyến mã chưa được viết.
    """
    with open(duong_dan, "rb") as f:
        return b"\0" in f.read(8192)


def quet_dong(dong):
    """Trả danh sách (mã lỗi, mô tả) cho một dòng. Không đọc trạng thái ngoài."""
    thay = []
    for ma, mau, in_gia_tri, giai_thich in LUAT:
        khop = mau.search(dong)
        if not khop:
            continue
        if in_gia_tri:
            thay.append((ma, "%s: %r (cột %d)"
                         % (giai_thich, khop.group(0), khop.start() + 1)))
        else:
            # Không in giá trị: đường dẫn khoá là hạ tầng, in ra là làm lộ lần thứ hai
            # vào log CI. Vị trí đủ để người sửa tìm ra dòng.
            thay.append((ma, "%s (cột %d — KHÔNG in giá trị, xem tận nơi)"
                         % (giai_thich, khop.start() + 1)))
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
    print("CỔNG khong-cua-hau — gốc quét: %s" % goc)
    print("  Đã đọc %d tệp văn bản. Miễn trừ nội dòng đang dùng: %d (mỗi cái phải có ly-do=)."
          % (so_tep, so_mien_tru))
    if not vi_pham and not loi_cong:
        print("  ĐẠT: không thấy lệnh hệ thống ghép từ tham số, không thấy khoá SSH ghi cứng,")
        print("       không thấy thực thi động.")
        print("  NHẮC: cổng đọc TỪNG DÒNG. Lệnh dựng ở dòng trên rồi chạy bằng một biến ở")
        print("        dòng dưới thì cổng KHÔNG thấy. Xem mục CHỖ MÙ ĐÃ KHAI ở đầu tệp này.")
        return
    if vi_pham:
        print("  HỎNG: %d vị trí." % len(vi_pham))
        for duong_dan, so_dong, ma, chi_tiet in vi_pham:
            print("    %-52s:%-5d [%s] %s" % (duong_dan, so_dong, ma, chi_tiet))
        print("  Cách xử ĐÚNG, theo thứ tự:")
        print("    1. Trình điều khiển chỉ được đổi một lời gọi công cụ thành một lời gọi")
        print("       API của nền tảng nó phụ trách. Không mở tiến trình con, không SSH,")
        print("       không chạy lệnh trên máy khác. Nền tảng chưa có API thì việc phải làm")
        print("       là thêm API cho nền tảng ấy, không phải mượn trình bao làm API.")
        print("    2. Danh tính, quyền, hạn mức và nhật ký thuộc về NHÂN, không thuộc trình")
        print("       điều khiển. Trình điều khiển tự xác thực thì mỗi nền tảng cho ra một")
        print("       mô hình quyền khác nhau, và không ai trả lời được 'ai đã làm gì'.")
        print("    3. Mặc định CHỈ ĐỌC. Công cụ có ghi phải khai tường minh và đi cổng riêng.")
        print("    4. CHỈ khi thật sự cần trưng khuôn bị từ chối (tài liệu kiến trúc) mới")
        print("       miễn trừ: thêm vào cuối dòng")
        print("       %s khong-cua-hau ly-do=<lý do cụ thể>" % DAU_MIEN_TRU)
    if loi_cong:
        print("  HỎNG (fail-closed): %d tệp cổng không tự chứng minh được." % len(loi_cong))
        for duong_dan, ghi_chu in loi_cong:
            print("    %-52s %s" % (duong_dan, ghi_chu))


def tu_kiem():
    """Bài thử ngược BẮT BUỘC: dựng thư mục tạm, cài mẫu xấu, và ĐÒI cổng không cắt oan.

    Bốn phần, phần nào thiếu thì cổng này chưa đáng tin:
      1. mẫu-phải-bắt  — chứng minh cổng CẮN.
      2. dòng-sạch     — chứng minh cổng KHÔNG cắt oan. Danh sách này quan trọng NGANG
                         phần 1, và phần lớn các dòng trong đó lấy NGUYÊN VĂN từ kho này
                         (PyTorch .eval(), RegExp.exec(), bảng dò của cong/khong-bi-mat.py).
                         Cắt oan một trong số đó là làm hỏng kho hoặc làm tắt cổng.
      3. miễn trừ      — một cái có lý do (phải được đếm), một cái thiếu lý do (phải bị bắt).
      4. tự quét mã nguồn của CHÍNH cổng này — chứng minh tệp cổng không mang theo thứ nó
                         chặn (lỗi mà khong-danh-tinh.py đã mắc và đã sửa).
    """
    # Mọi mẫu xấu được GHÉP LÚC CHẠY. Không dòng nào dưới đây tồn tại nguyên vẹn trên đĩa.
    mo = "("
    nhay = '"'
    mau = [
        "os." + "system" + mo + "f" + nhay + "curl {url}" + nhay + ")",
        _TIEN_TRINH + ".run" + mo + "f" + nhay + _SSH + " {may} {lenh}" + nhay + ")",
        _TIEN_TRINH + ".Popen(lenh, " + "shell" + "=" + "True" + ")",
        _TIEN_TRINH + ".run" + mo + nhay + _SSH + " " + nhay + " + may_chu + "
        + nhay + " " + nhay + " + lenh)",
        _TIEN_TRINH + "." + "getoutput" + mo + nhay + "docker ps" + nhay + ")",
        "SSH = [" + nhay + _SSH + nhay + ", " + nhay + "-i" + nhay + ", "
        + nhay + "/nha/nguoi-dung/." + _SSH + "/khoa_may_chu" + nhay + "]",
        "KHOA = " + nhay + "/goc/bi-mat/." + _SSH + "/khoa_root" + nhay,
        "duong_dan_khoa = " + nhay + "/goc/bi-mat/" + "id_" + "ed25519" + nhay,
        _CHI_THI_KHOA + " /goc/bi-mat/khoa-vps",
        "ket_qua = " + "eval" + mo + "than_yeu_cau)",
        "exe" + "c" + mo + "noi_dung_tai_ve)",
    ]

    # Mỗi dòng dưới đây PHẢI sạch. Bảy dòng đầu lấy nguyên văn hoặc gần nguyên văn từ kho.
    sach = [
        # (a) Dạng danh sách đối số — an toàn, vì không có trình bao nào diễn giải chúng.
        'subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)',
        # (b) Một câu văn nhắc tới SSH trong TÀI LIỆU, không phải mã. Tài liệu kiến trúc
        #     bắt buộc phải nói được câu này mà không cần miễn trừ.
        "Vận chuyển của máy chủ MCP cũ là SSH vào máy chủ sản phẩm; câu này là tài liệu.",
        # (c) Chữ exec trong một câu văn tiếng Việt, không có dấu mở ngoặc ngay sau.
        "Trình chạy tác vụ exec vào container rồi đọc nhật ký, đó là cách nói thường gặp.",
        # (d) Chế độ suy luận của PyTorch — có thật 15 chỗ trong mo-hinh/ và huan-luyen/.
        "    mo_hinh.eval()",
        # (e) RegExp.exec của JavaScript — có thật trong chat/chat.js.
        "  while ((m = mau.exec(van)) !== null) {",
        # (f) Bảng dò của cong/khong-bi-mat.py: tên khoá dạng khoá từ điển, KHÔNG có đường
        #     dẫn. Cắt oan dòng này là cắt oan cổng bí mật của chính kho này.
        '    "id_rsa": "khoá riêng SSH",',
        # (g) Bộ phân tích an toàn. Ký tự đứng ngay trước là dấu gạch dưới.
        "    cau_hinh = ast.literal_eval(van_ban)",
        # (h) CHỖ MÙ đã khai, viết ra để lần siết luật sau không lặng lẽ đóng nó mà quên
        #     cập nhật phần khai phạm vi: dấu cách trước ngoặc thì lọt.
        "Chạy bộ eval (đánh giá) 227 câu trước khi phát hành.",
        # (i) Tệp cấu hình và khoá CÔNG KHAI — không phải khoá riêng.
        "Tệp ~/.ssh/config và khoá công khai ~/.ssh/id_ed25519.pub không phải khoá riêng.",
        # (j) Dòng thật trong cong/chay-tat-ca.sh: gọi một chương trình bằng danh sách
        #     tham số đã trích dẫn, không có trình bao nào diễn giải thêm.
        '  "$PYTHON" "$DUONG_DAN" --tu-kiem',
        # (k) CHỖ MÙ đã khai: lệnh nằm trong một biến thì cổng không thấy. Viết ra đây để
        #     không ai tưởng phần 1 đã phủ hết.
        "    ket_qua = subprocess.run(danh_sach_tham_so, check=True)",
    ]

    mien_tru_co_ly_do = (
        "Khuôn BỊ TỪ CHỐI, trưng ra để người đọc nhận mặt: " + "os." + "system" + mo
        + "f" + nhay + "..." + nhay + ")  " + DAU_MIEN_TRU + " khong-cua-hau "
        "ly-do=tài liệu kiến trúc phải trưng khuôn bị từ chối thì người đọc mới nhận ra nó"
    )
    mien_tru_thieu_ly_do = (
        "Ghi chú cũ: " + "os." + "system" + mo + "lenh)   " + DAU_MIEN_TRU + " khong-cua-hau"
    )

    tam = tempfile.mkdtemp(prefix="tu-kiem-khong-cua-hau-")
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
    #    vô tình viết thẳng một khuôn cấm vào mã hay vào mẫu thử, dòng dưới đây đỏ ngay.
    tu_bat = [(so, ma, ct) for tep, so, ma, ct in vi_pham if tep == "ban-sao-cong.py"]
    if tu_bat:
        hong.append("CỔNG TỰ MANG THEO THỨ NÓ CHẶN — mã nguồn của chính nó bị bắt tại: %r"
                    % (tu_bat,))

    print("TỰ KIỂM khong-cua-hau: %d mẫu cài, %d dòng sạch làm đối chứng, "
          "2 ca miễn trừ, và 1 bản sao mã nguồn của chính cổng." % (len(mau), len(sach)))
    if hong:
        for d in hong:
            print("  HỎNG: %s" % d)
        return 1

    print("  ĐẠT: cắn đủ %d mẫu cài — bốn dạng ghép lệnh (hàm luôn qua trình bao, cờ trình"
          % len(mau))
    print("       bao, chuỗi f, nối chuỗi), SSH làm phương tiện, ba dạng khoá ghi cứng,")
    print("       và hai dạng thực thi động.")
    print("  ĐẠT: KHÔNG cắt oan danh sách đối số đã trích dẫn, câu văn nhắc SSH trong tài")
    print("       liệu, chữ exec trong câu tiếng Việt, PyTorch .eval(), RegExp.exec() của")
    print("       JavaScript, bảng dò tên khoá của cong/khong-bi-mat.py, ast.literal_eval,")
    print("       tệp cấu hình ~/.ssh/config và khoá công khai .pub.")
    print("  ĐẠT: mã nguồn của CHÍNH cổng này quét ra 0 vi phạm, 0 miễn trừ — mọi khuôn cấm")
    print("       trong tệp đều được ghép lúc chạy nên không xuất hiện nguyên vẹn trên đĩa.")
    return 0


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Cổng 7/7: chặn khuôn cửa hậu (ghép lệnh hệ thống, khoá SSH ghi cứng, "
                    "thực thi động) tái xuất hiện trong kho.")
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
