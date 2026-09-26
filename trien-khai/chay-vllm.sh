#!/usr/bin/env bash
# trien-khai/chay-vllm.sh — khởi động vLLM phục vụ google/gemma-4-31B-it.
#
# ════════════════════════════════════════════════════════════════════════════
# VÌ SAO KỊCH BẢN NÀY TỒN TẠI
#
#   Gõ tay `vllm serve google/gemma-4-31B-it` thì ba cờ quan trọng nhất
#   (--max-model-len, --gpu-memory-utilization, --quantization) thường bị bỏ trống,
#   và bỏ trống cờ đầu tiên là tự bắn vào chân với ĐÚNG mô hình này:
#
#     Cấu hình Gemma 4 31B khai max_position_embeddings = 262.144 (ngữ cảnh 256K).
#     vLLM lấy giá trị ấy làm mặc định và cố cấp KV cache cho ngần ấy token. Ước tính
#     ở hàm tinh_kv_mib() bên dưới: ~80 GiB cho MỘT chuỗi, chưa tính trọng số. Máy hết
#     VRAM trước khi trả lời được câu hỏi đầu tiên, kèm một thông báo lỗi khó đọc giữa
#     chừng — đúng họ lỗi mà kho này đặt ra để chống.
#
#   Cho nên kịch bản này KIỂM TRƯỚC RỒI MỚI CHẠY: đủ vLLM chưa, có GPU chưa, đủ VRAM
#   chưa. Thiếu thì dừng ngay với một câu nói rõ thiếu gì và sửa thế nào.
#
# ════════════════════════════════════════════════════════════════════════════
# BỐN ĐIỀU KỊCH BẢN NÀY KHÔNG LÀM — đừng thêm vào
#
#   1. KHÔNG TẢI TRỌNG SỐ. Trọng số BF16 của mô hình này khoảng 62,5 GB. Một kịch bản
#      khởi động lỡ tay tải 62,5 GB là một tai nạn băng thông và một tai nạn hoá đơn.
#      Mặc định kịch bản đòi trọng số đã có sẵn trên đĩa (DUONG_DAN_TRONG_SO). Muốn để
#      vLLM tự kéo từ Hugging Face thì phải bật tường minh CHO_PHEP_TAI_TRONG_SO=co.
#
#   2. KHÔNG GHI TOKEN TRUY CẬP VÀO ĐÂU CẢ. Kho này công khai. Token đọc từ biến môi
#      trường HUGGING_FACE_HUB_TOKEN nếu cần; kịch bản không in nó ra, không ghi nó
#      vào tệp nào, không đặt giá trị mặc định cho nó.
#      (Đo 26/09/2026: hai kho trọng số Gemma 4 31B khai gated = false, nên thường
#      KHÔNG cần token. Ghi đường đọc token ở đây là để phòng khi Google đổi ý.)
#
#   3. KHÔNG CÓ ĐƯỜNG DỰ PHÒNG RA NHÀ CUNG CẤP BÊN NGOÀI. Máy nội bộ hỏng thì báo lỗi
#      và dừng. Một chuỗi "cục bộ trước, đám mây sau" phá đúng thứ hệ này hứa: người
#      dùng tưởng đang chạy cục bộ, còn câu hỏi thì âm thầm đi ra ngoài.
#
#   4. KHÔNG ĐỔI TÊN CHO TRỌNG SỐ THÀNH CỦA BDSG. Trọng số là của Google (Apache-2.0).
#      Hàm kiem_ten_phuc_vu() chặn việc đặt --served-model-name có chữ "bdsg" cho trọng
#      số Google nguyên bản. Xem lý do đầy đủ tại chỗ khai hàm ấy.
#
# ════════════════════════════════════════════════════════════════════════════
# DÙNG
#   trien-khai/chay-vllm.sh              # kiểm rồi chạy
#   trien-khai/chay-vllm.sh --chi-kiem   # chỉ chạy phần kiểm, KHÔNG khởi động
#   trien-khai/chay-vllm.sh --in-lenh    # kiểm xong thì in lệnh ra, KHÔNG khởi động
#   trien-khai/chay-vllm.sh --tu-kiem    # bài thử ngược các hàm tính, chạy được KHÔNG CẦN GPU
#
#   Cấu hình đọc từ biến môi trường. Bản mẫu kèm chú thích: trien-khai/cau-hinh.mau.env
#     set -a; . ./cau-hinh.env; set +a; trien-khai/chay-vllm.sh
#
# MÃ THOÁT: 0 = đạt · 1 = kiểm không đạt (KHÔNG khởi động) · 2 = tham số sai.
#
# Viết ngày 26/09/2026. Mọi con số VRAM trong tệp này là SỐ TÍNH RA từ số tham số và
# cấu hình đã công bố, KHÔNG phải số đo trên máy thật — dự án chưa có GPU để đo.
# ════════════════════════════════════════════════════════════════════════════

set -u

# ── Hằng số của mô hình — đọc từ cấu hình Google công bố, tra ngày 26/09/2026 ──
# Không đặt các số này thành biến môi trường: chúng là THUỘC TÍNH CỦA MÔ HÌNH, không
# phải lựa chọn của người vận hành. Cho phép sửa từ ngoài thì sớm muộn có người sửa để
# phép kiểm VRAM "đạt", rồi máy vẫn hết bộ nhớ như cũ — chỉ mất thêm một giờ để hiểu.
SO_THAM_SO=31273088876      # 31,27 tỷ tham số
SO_LOP=60
SO_LOP_TRUOT=50             # layer_types: 50 sliding_attention
SO_LOP_TOAN=10              #              + 10 full_attention
CUA_SO_TRUOT=1024           # sliding_window
SO_DAU_KV=16                # num_key_value_heads
HEAD_DIM_TRUOT=256          # head_dim
HEAD_DIM_TOAN=512           # global_head_dim
BYTE_MOI_PHAN_TU_KV=2       # KV cache BF16

PHIEN_BAN_VLLM_TOI_THIEU="0.19.0"   # bản đầu tiên có kiến trúc gemma4 (phát hành 02/04/2026)

# Dự phòng cho kích hoạt, đồ thị CUDA, bộ đệm nội bộ của vLLM. Con số này là MỘT KHOẢN
# CHỪA THEO KINH NGHIỆM CHUNG, CHƯA ĐO trên mô hình này. Ghi ra để không ai tưởng nó
# là kết quả đo.
DU_PHONG_MIB=2048

# ── Cấu hình, đọc từ biến môi trường, mặc định AN TOÀN ────────────────────────
MO_HINH_GEMMA="${MO_HINH_GEMMA:-google/gemma-4-31B-it}"
DUONG_DAN_TRONG_SO="${DUONG_DAN_TRONG_SO:-}"
CHO_PHEP_TAI_TRONG_SO="${CHO_PHEP_TAI_TRONG_SO:-khong}"
TEN_PHUC_VU="${TEN_PHUC_VU:-gemma-4-31b-it}"
BDSG_DA_TINH_CHINH="${BDSG_DA_TINH_CHINH:-khong}"

# Mặc định NGHE LOOPBACK. Đây là quyết định an toàn, không phải lười cấu hình: bản này
# CHƯA CÓ ĐĂNG NHẬP. Mở ra 0.0.0.0 khi chưa có lớp xác thực là mở một API sinh chữ cho
# cả mạng — xem mục cảnh báo trong tai-lieu/GEMMA4-31B.md.
DIA_CHI_NGHE="${DIA_CHI_NGHE:-127.0.0.1}"
CONG_NGHE="${CONG_NGHE:-8000}"

NGU_CANH_TOI_DA="${NGU_CANH_TOI_DA:-8192}"
TY_LE_BO_NHO_GPU="${TY_LE_BO_NHO_GPU:-0.90}"
LUONG_TU_HOA="${LUONG_TU_HOA:-}"
KIEU_DU_LIEU="${KIEU_DU_LIEU:-bfloat16}"
SO_GPU_SONG_SONG="${SO_GPU_SONG_SONG:-1}"
SO_CHUOI_DONG_THOI="${SO_CHUOI_DONG_THOI:-2}"
PYTHON_VLLM="${PYTHON_VLLM:-python3}"

# ── In ấn ─────────────────────────────────────────────────────────────────────
loi()   { printf 'HỎNG: %s\n' "$*" >&2; }
nhac()  { printf '  %s\n' "$*"; }
tieu()  { printf '\n──── %s ────\n' "$*"; }

# ── Phiên bản ─────────────────────────────────────────────────────────────────
chuan_hoa_phien_ban() {
    # "v0.24.0rc1" → "0.24.0" · "0.19" → "0.19.0" · "0.20.0.dev0+g1a2b" → "0.20.0"
    local chuoi p1 p2 p3
    chuoi="$(printf '%s' "$1" | sed -E 's/^[^0-9]*//; s/[^0-9.].*$//')"
    IFS='.' read -r p1 p2 p3 _ <<< "$chuoi"
    printf '%d.%d.%d' "${p1:-0}" "${p2:-0}" "${p3:-0}"
}

du_phien_ban() {
    # du_phien_ban <có> <cần> → mã thoát 0 nếu <có> >= <cần>.
    #
    # VÌ SAO KHÔNG SO SÁNH CHUỖI: theo thứ tự chữ cái thì "0.9.0" > "0.19.0", còn theo
    # phiên bản thì 0.9.0 < 0.19.0 — ngược hẳn. Một phép so chuỗi ở đây sẽ cho vLLM 0.9.x
    # đi qua cổng, rồi nó chết vì không biết kiến trúc gemma4, và thông báo lỗi lúc ấy
    # KHÔNG hề nhắc gì tới phiên bản. Bài tự kiểm có đúng cặp số này làm mẫu.
    local co can c1 c2 c3 k1 k2 k3
    co="$(chuan_hoa_phien_ban "$1")"; can="$(chuan_hoa_phien_ban "$2")"
    IFS='.' read -r c1 c2 c3 <<< "$co"
    IFS='.' read -r k1 k2 k3 <<< "$can"
    if [ "$c1" -ne "$k1" ]; then [ "$c1" -gt "$k1" ]; return $?; fi
    if [ "$c2" -ne "$k2" ]; then [ "$c2" -gt "$k2" ]; return $?; fi
    [ "$c3" -ge "$k3" ]
}

# ── Tính bộ nhớ — TÍNH RA, CHƯA ĐO ────────────────────────────────────────────
byte_moi_tham_so_x100() {
    # Trả số byte mỗi tham số NHÂN 100, để mọi phép tính ở dưới chạy bằng số nguyên
    # (bash không có số thực). Ba giá trị, mỗi giá trị kèm lý do:
    #   200 = 2,00 byte — BF16, không lượng tử hoá.
    #   105 = 1,05 byte — FP8: 1 byte trọng số + ~5% cho hệ số tỉ lệ từng tensor.
    #    60 = 0,60 byte — INT4: 0,5 byte trọng số + hệ số tỉ lệ và điểm không theo nhóm.
    # Ba con số này là ƯỚC TÍNH THEO ĐỊNH DẠNG, chưa đo trên tệp trọng số thật.
    case "$1" in
        ""|khong|none|bf16|bfloat16|fp16|float16) printf '200' ;;
        fp8|fp8_e4m3|fp8_e5m2)                    printf '105' ;;
        awq|awq_marlin|gptq|gptq_marlin|bitsandbytes|compressed-tensors) printf '60' ;;
        *) printf '0' ;;   # 0 = không biết định dạng này ⇒ hàm gọi phải dừng
    esac
}

tinh_trong_so_mib() {
    local don_vi; don_vi="$(byte_moi_tham_so_x100 "$1")"
    [ "$don_vi" -eq 0 ] && { printf '0'; return 1; }
    printf '%d' $(( SO_THAM_SO * don_vi / 100 / 1048576 ))
}

tinh_kv_mib() {
    # tinh_kv_mib <độ dài ngữ cảnh> <số chuỗi đồng thời>
    #
    # CÔNG THỨC, viết ra để ai cũng kiểm lại được:
    #   lớp cửa sổ trượt: KV bị CHẶN ở CUA_SO_TRUOT token, dài hơn cũng không tốn thêm.
    #   lớp chú ý toàn cục: KV lớn theo đúng độ dài ngữ cảnh — đây là chỗ 256K giết máy.
    #   mỗi token mỗi lớp = 2 (K và V) × số đầu KV × head_dim × byte mỗi phần tử.
    #
    # ⚠ HAI CHỖ ƯỚC TÍNH NÀY CÓ THỂ CAO HƠN THỰC TẾ, và nói ra là đúng hơn giấu:
    #   (a) cấu hình khai attention_k_eq_v = true. Nếu điều đó nghĩa là K và V dùng
    #       chung một tensor thì số thật CHỈ BẰNG MỘT NỬA phần này. Chưa kiểm chứng
    #       được cách vLLM cài, nên ở đây tính K và V tách rời — tức tính về phía AN
    #       TOÀN (thừa bộ nhớ thì chạy được, thiếu thì chết giữa chừng).
    #   (b) vLLM cấp KV cache theo khối, và cấp trước theo phần VRAM còn trống chứ
    #       không cấp đúng bằng nhu cầu. Con số ở đây là NHU CẦU, không phải mức cấp.
    local L="$1" N="$2" L_truot byte_truot byte_toan
    L_truot=$(( L < CUA_SO_TRUOT ? L : CUA_SO_TRUOT ))
    byte_truot=$(( 2 * SO_DAU_KV * HEAD_DIM_TRUOT * BYTE_MOI_PHAN_TU_KV ))
    byte_toan=$((  2 * SO_DAU_KV * HEAD_DIM_TOAN  * BYTE_MOI_PHAN_TU_KV ))
    printf '%d' $(( (SO_LOP_TRUOT * L_truot * byte_truot + SO_LOP_TOAN * L * byte_toan) * N / 1048576 ))
}

# ── Tên phục vụ: chặn lời khai sai về quyền sở hữu trọng số ───────────────────
kiem_ten_phuc_vu() {
    # Mã thoát 0 = tên chấp nhận được.
    #
    # VÌ SAO CÓ PHÉP KIỂM NÀY. Tên trong --served-model-name là thứ hiện ra ở /v1/models
    # và ở nhãn "câu trả lời đến từ …" trên giao diện. Đặt tên "bdsg-…" cho trọng số
    # Google nguyên bản là nói với người đọc rằng BDSG đã huấn luyện ra nó. Không đúng:
    # BDSG PHỤC VỤ trọng số của Google. Hai việc ấy khác nhau, và kho này tồn tại một
    # phần để giữ đúng ranh giới ấy (xem bảng trạng thái trong README).
    #
    # Chỉ khi CHÍNH BDSG huấn luyện ra trọng số đang nạp thì mới được đặt BDSG_DA_TINH_CHINH=co.
    local ten_thuong
    ten_thuong="$(printf '%s' "$1" | tr 'A-Z' 'a-z')"
    case "$ten_thuong" in
        *bdsg*)
            if [ "$2" != "co" ]; then return 1; fi ;;
    esac
    return 0
}

tinh_vram_dung_duoc() {
    # tinh_vram_dung_duoc <VRAM từng GPU, cách nhau bằng khoảng trắng> <số GPU song song> <tỉ lệ>
    # In ra số MiB vLLM THẬT SỰ được phép dùng. Mã thoát 1 = không đủ GPU.
    #
    # VÌ SAO KHÔNG CỘNG TỔNG VRAM CỦA MỌI CARD — đây là một lỗi đã có trong bản đầu
    # của tệp này, sửa ngày 26/09/2026. vLLM chỉ trải mô hình lên đúng
    # --tensor-parallel-size card; những card còn lại nó không đụng tới. Cộng tổng thì
    # một máy 4 × 24 GB chạy SO_GPU_SONG_SONG=1 "đạt" ở cổng này (88.473 MiB dùng được
    # > 68.416 MiB cần) rồi chết vì hết bộ nhớ lúc nạp — đúng họ lỗi "cổng cho qua rồi
    # hỏng giữa chừng" mà cả kịch bản này ra đời để chặn, và nó còn mâu thuẫn với chính
    # bảng cấu hình máy trong tai-lieu/GEMMA4-31B.md §9 ("1 × 24 GB: chỉ INT4").
    #
    # Lấy card NHỎ NHẤT trong nhóm rồi nhân với số card: tensor parallel chia đều các
    # lát, nên card nhỏ nhất là chỗ thắt. Máy trộn nhiều cỡ card thì đây là con số đúng,
    # không phải tổng.
    local ds="$1" n="$2" ty_le="$3" mot dem=0 nho_nhat=0
    for mot in $ds; do
        [ "$dem" -ge "$n" ] && break
        dem=$((dem + 1))
        if [ "$nho_nhat" -eq 0 ] || [ "$mot" -lt "$nho_nhat" ]; then nho_nhat="$mot"; fi
    done
    if [ "$dem" -lt "$n" ] || [ "$nho_nhat" -le 0 ]; then printf '0'; return 1; fi
    printf '%d' $(( nho_nhat * n * $(ty_le_phan_tram "$ty_le") / 100 ))
}

ty_le_phan_tram() {
    # "0.90" → 90 · "0.9" → 90 · "0.85" → 85 · "1.0" → 100
    #
    # VÌ SAO KHÔNG CẮT CHUỖI CHO NHANH. Bản đầu của dòng này viết ${TY_LE.../0./} —
    # tức "bỏ tiền tố 0." — và nó ĐÚNG với "0.90" nhưng SAI với "0.9": ra 9, tức 9%
    # thay vì 90%. Phép kiểm VRAM khi ấy đòi gấp mười lần chỗ thật sự cần, và người
    # vận hành sẽ đi giảm ngữ cảnh để chiều một con số sai. Đệm rồi cắt đúng hai chữ
    # số thì cả hai cách viết đều ra 90. Bài tự kiểm khoá cả hai.
    local s="$1" nguyen thap
    IFS='.' read -r nguyen thap <<< "$s"
    if [ "$((10#${nguyen:-0}))" -ge 1 ]; then printf '100'; return 0; fi
    thap="${thap:-0}00"
    # "10#" ép cơ số 10: không có nó thì "08" và "09" bị đọc là số bát phân và báo lỗi.
    printf '%d' "$((10#${thap:0:2}))"
}

# ── Bài thử ngược: chạy được KHÔNG CẦN GPU ───────────────────────────────────
tu_kiem() {
    local hong=0
    _dung() {  # _dung <nhãn> <thu được> <mong đợi>
        if [ "$2" = "$3" ]; then printf '  ĐẠT  %-46s = %s\n' "$1" "$2"
        else printf '  HỎNG %-46s = %s (mong đợi %s)\n' "$1" "$2" "$3"; hong=$((hong+1)); fi
    }
    _thoat() {  # _thoat <nhãn> <mã thoát thật> <mã mong đợi>
        if [ "$2" = "$3" ]; then printf '  ĐẠT  %-46s mã %s\n' "$1" "$2"
        else printf '  HỎNG %-46s mã %s (mong đợi %s)\n' "$1" "$2" "$3"; hong=$((hong+1)); fi
    }

    printf 'TỰ KIỂM chay-vllm.sh — các hàm tính, không cần GPU.\n\n'

    printf ' 1. Chuẩn hoá chuỗi phiên bản\n'
    _dung "chuan_hoa_phien_ban 0.24.0"      "$(chuan_hoa_phien_ban '0.24.0')"        "0.24.0"
    _dung "chuan_hoa_phien_ban v0.19.0"     "$(chuan_hoa_phien_ban 'v0.19.0')"       "0.19.0"
    _dung "chuan_hoa_phien_ban 0.24.0rc1"   "$(chuan_hoa_phien_ban '0.24.0rc1')"     "0.24.0"
    _dung "chuan_hoa_phien_ban 0.20.0.dev0" "$(chuan_hoa_phien_ban '0.20.0.dev0')"   "0.20.0"
    _dung "chuan_hoa_phien_ban 0.19"        "$(chuan_hoa_phien_ban '0.19')"          "0.19.0"

    printf '\n 2. So sánh phiên bản — BẪY CHÍNH: so chuỗi thì 0.9.0 > 0.19.0, sai\n'
    du_phien_ban "0.9.0"  "$PHIEN_BAN_VLLM_TOI_THIEU"; _thoat "0.9.0  đủ 0.19.0?  (phải KHÔNG)" "$?" "1"
    du_phien_ban "0.19.0" "$PHIEN_BAN_VLLM_TOI_THIEU"; _thoat "0.19.0 đủ 0.19.0?  (phải CÓ)"    "$?" "0"
    du_phien_ban "0.24.0" "$PHIEN_BAN_VLLM_TOI_THIEU"; _thoat "0.24.0 đủ 0.19.0?  (phải CÓ)"    "$?" "0"
    du_phien_ban "0.18.9" "$PHIEN_BAN_VLLM_TOI_THIEU"; _thoat "0.18.9 đủ 0.19.0?  (phải KHÔNG)" "$?" "1"
    du_phien_ban "1.0.0"  "$PHIEN_BAN_VLLM_TOI_THIEU"; _thoat "1.0.0  đủ 0.19.0?  (phải CÓ)"    "$?" "0"

    printf '\n 3. Bộ nhớ trọng số theo mức lượng tử hoá (TÍNH RA, chưa đo)\n'
    local bf16 fp8 int4
    bf16="$(tinh_trong_so_mib '')"; fp8="$(tinh_trong_so_mib 'fp8')"; int4="$(tinh_trong_so_mib 'awq')"
    printf '     BF16 %s MiB · FP8 %s MiB · INT4 %s MiB\n' "$bf16" "$fp8" "$int4"
    if [ "$bf16" -gt 57000 ] && [ "$bf16" -lt 62000 ]; then
        printf '  ĐẠT  BF16 nằm trong khoảng ~59.000 MiB (≈62,5 GB thập phân)\n'
    else printf '  HỎNG BF16 = %s MiB, lệch khỏi khoảng đã tính tay\n' "$bf16"; hong=$((hong+1)); fi
    if [ "$int4" -lt "$fp8" ] && [ "$fp8" -lt "$bf16" ]; then
        printf '  ĐẠT  thứ tự INT4 < FP8 < BF16\n'
    else printf '  HỎNG thứ tự ba mức lượng tử hoá sai\n'; hong=$((hong+1)); fi
    tinh_trong_so_mib "khong-phai-dinh-dang-nao" >/dev/null; _thoat "định dạng lạ phải báo hỏng" "$?" "1"

    printf '\n 3a. KHOÁ ĐÚNG CON SỐ tài liệu đã công bố (GEMMA4-31B.md §3.1)\n'
    # VÌ SAO PHẢI KHOÁ CHÍNH XÁC, KHÔNG CHỈ KHOÁ KHOẢNG VÀ THỨ TỰ. Bản đầu của bài tự
    # kiểm này chỉ kiểm khoảng và thứ tự. Thử ngược ngày 26/09/2026 cho thấy lỗ hổng:
    # đảo SO_LOP_TRUOT=10/SO_LOP_TOAN=50 làm KV ở 8K nhảy từ 3.360 lên 12.960 MiB mà bài
    # tự kiểm VẪN ĐẠT TOÀN BỘ, mã thoát 0 — trong khi tài liệu và cau-hinh.mau.env vẫn
    # in con số cũ. Tức cổng xanh mà tài liệu đã sai: đúng họ "hỏng mà không báo".
    # Từ nay mỗi con số in trong tài liệu đều có một dòng khoá ở đây.
    _dung "tinh_trong_so_mib BF16 = 59.648"  "$bf16" "59648"
    _dung "tinh_trong_so_mib FP8  = 31.315"  "$fp8"  "31315"
    _dung "tinh_trong_so_mib INT4 = 17.894"  "$int4" "17894"
    _dung "SO_LOP_TRUOT + SO_LOP_TOAN = 60"  "$(( SO_LOP_TRUOT + SO_LOP_TOAN ))" "60"
    _dung "SO_LOP_TRUOT = 50 (cấu hình Google)" "$SO_LOP_TRUOT" "50"

    printf '\n 3b. Đổi tỉ lệ bộ nhớ GPU sang phần trăm — bẫy "0.9" thành 9%%\n'
    _dung "ty_le_phan_tram 0.90" "$(ty_le_phan_tram '0.90')" "90"
    _dung "ty_le_phan_tram 0.9"  "$(ty_le_phan_tram '0.9')"  "90"
    _dung "ty_le_phan_tram 0.85" "$(ty_le_phan_tram '0.85')" "85"
    _dung "ty_le_phan_tram 0.08" "$(ty_le_phan_tram '0.08')" "8"
    _dung "ty_le_phan_tram 1.0"  "$(ty_le_phan_tram '1.0')"  "100"

    printf '\n 4. KV cache — chỗ ngữ cảnh 256K giết máy (TÍNH RA, chưa đo)\n'
    local kv8k kv32k kv256k
    kv8k="$(tinh_kv_mib 8192 1)"; kv32k="$(tinh_kv_mib 32768 1)"; kv256k="$(tinh_kv_mib 262144 1)"
    printf '     1 chuỗi:  8K → %s MiB · 32K → %s MiB · 256K → %s MiB\n' "$kv8k" "$kv32k" "$kv256k"
    if [ "$kv8k" -lt "$kv32k" ] && [ "$kv32k" -lt "$kv256k" ]; then
        printf '  ĐẠT  KV tăng theo độ dài ngữ cảnh\n'
    else printf '  HỎNG KV không tăng theo ngữ cảnh\n'; hong=$((hong+1)); fi
    if [ "$kv256k" -gt 81920 ]; then
        printf '  ĐẠT  256K một chuỗi vượt 80 GiB ⇒ cảnh báo trong tài liệu là có cơ sở\n'
    else printf '  HỎNG 256K chỉ ra %s MiB, cảnh báo trong tài liệu phải sửa\n' "$kv256k"; hong=$((hong+1)); fi
    local kv8k_x4; kv8k_x4="$(tinh_kv_mib 8192 4)"
    if [ "$kv8k_x4" -eq $(( kv8k * 4 )) ]; then
        printf '  ĐẠT  KV tỉ lệ thuận với số chuỗi đồng thời\n'
    else printf '  HỎNG KV không tỉ lệ với số chuỗi đồng thời\n'; hong=$((hong+1)); fi

    printf '\n 4a. KHOÁ ĐÚNG CON SỐ bảng KV trong tài liệu (GEMMA4-31B.md §3.2 và cau-hinh.mau.env §4)\n'
    # Bảy dòng này là bảy ô của bảng KV đã in ra. Sửa hằng số mô hình mà quên sửa bảng
    # thì hỏng ở đây, không hỏng lặng lẽ trong đầu người đọc. Xem lý do dài ở mục 3a.
    _dung "tinh_kv_mib   4.096 × 1 =  2.080" "$(tinh_kv_mib 4096 1)"   "2080"
    _dung "tinh_kv_mib   8.192 × 1 =  3.360" "$kv8k"                   "3360"
    _dung "tinh_kv_mib  16.384 × 1 =  5.920" "$(tinh_kv_mib 16384 1)"  "5920"
    _dung "tinh_kv_mib  32.768 × 1 = 11.040" "$kv32k"                  "11040"
    _dung "tinh_kv_mib  65.536 × 1 = 21.280" "$(tinh_kv_mib 65536 1)"  "21280"
    _dung "tinh_kv_mib 131.072 × 1 = 41.760" "$(tinh_kv_mib 131072 1)" "41760"
    _dung "tinh_kv_mib 262.144 × 1 = 82.720" "$kv256k"                 "82720"
    # Bảng tổng cần ở §3.3: trọng số + KV + dự phòng. Khoá hai mốc hay bị trích nhất.
    _dung "tổng cần BF16 · 8K · 1 chuỗi = 65.056" \
          "$(( bf16 + $(tinh_kv_mib 8192 1) + DU_PHONG_MIB ))" "65056"
    _dung "tổng cần BF16 · 8K · 2 chuỗi = 68.416" \
          "$(( bf16 + $(tinh_kv_mib 8192 2) + DU_PHONG_MIB ))" "68416"

    printf '\n 4b. VRAM dùng được — KHÔNG được cộng tổng card mà vLLM không đụng tới\n'
    # Bẫy này là một LỖI THẬT đã có trong bản đầu, tìm ra ngày 26/09/2026: phép kiểm cộng
    # VRAM của MỌI card bất kể SO_GPU_SONG_SONG, nên một máy 4 × 24 GB chạy tensor
    # parallel = 1 được cho qua rồi chết lúc nạp.
    _dung "4 × 24 GB, TP=1 → chỉ 1 card"        "$(tinh_vram_dung_duoc '24576 24576 24576 24576' 1 0.90)" "22118"
    _dung "4 × 24 GB, TP=4 → cả 4 card"         "$(tinh_vram_dung_duoc '24576 24576 24576 24576' 4 0.90)" "88473"
    _dung "1 × 80 GB (H100 báo 81.559), TP=1"   "$(tinh_vram_dung_duoc '81559' 1 0.90)"                   "73403"
    _dung "card lệch cỡ → lấy card NHỎ NHẤT"    "$(tinh_vram_dung_duoc '81559 24576' 2 0.90)"             "44236"
    tinh_vram_dung_duoc '81559' 2 0.90 >/dev/null; _thoat "đòi 2 card mà chỉ có 1 → báo hỏng" "$?" "1"
    # Phép then chốt: 4 × 24 GB với TP=1 KHÔNG được đủ chỗ cho BF16 (cần 68.416 MiB).
    if [ "$(tinh_vram_dung_duoc '24576 24576 24576 24576' 1 0.90)" -lt 68416 ]; then
        printf '  ĐẠT  4 × 24 GB với TP=1 bị CHẶN đúng (tổng 4 card sẽ cho qua nhầm)\n'
    else printf '  HỎNG 4 × 24 GB với TP=1 lọt qua cổng VRAM\n'; hong=$((hong+1)); fi

    printf '\n 5. Chặn lời khai sai về quyền sở hữu trọng số\n'
    kiem_ten_phuc_vu "gemma-4-31b-it" "khong";  _thoat "tên trung thực, chưa tinh chỉnh → nhận"  "$?" "0"
    kiem_ten_phuc_vu "bdsg-gemma-31b" "khong";  _thoat "tên có 'bdsg', chưa tinh chỉnh → CHẶN"   "$?" "1"
    kiem_ten_phuc_vu "BDSG-Gemma-31B" "khong";  _thoat "viết hoa cũng phải CHẶN"                 "$?" "1"
    kiem_ten_phuc_vu "bdsg-gemma-31b" "co";     _thoat "BDSG đã tự tinh chỉnh → nhận"            "$?" "0"

    printf '\n'
    if [ "$hong" -gt 0 ]; then
        printf 'TỰ KIỂM HỎNG: %d phép thử không đạt.\n' "$hong"
        return 1
    fi
    printf 'TỰ KIỂM ĐẠT toàn bộ. NHẮC: bài này chỉ chứng minh các hàm TÍNH đúng như đã\n'
    printf 'viết. Nó KHÔNG chứng minh con số khớp VRAM thật — chưa có GPU để đo.\n'
    return 0
}

# ── Phân tích tham số ─────────────────────────────────────────────────────────
CHE_DO="chay"
while [ $# -gt 0 ]; do
    case "$1" in
        --tu-kiem)  CHE_DO="tu-kiem"; shift ;;
        --chi-kiem) CHE_DO="chi-kiem"; shift ;;
        --in-lenh)  CHE_DO="in-lenh"; shift ;;
        -h|--help)  sed -n '1,58p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) loi "không hiểu tham số '$1'. Xem --help."; exit 2 ;;
    esac
done

if [ "$CHE_DO" = "tu-kiem" ]; then
    tu_kiem
    exit $?
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHẦN KIỂM — mọi bước đều DỪNG khi hỏng. Không bước nào được "cảnh báo rồi chạy tiếp":
# chạy tiếp với một điều kiện chưa đạt chính là cách sinh ra thông báo lỗi khó hiểu ở
# giữa chừng mà kịch bản này ra đời để tránh.
# ══════════════════════════════════════════════════════════════════════════════
SO_HONG=0
bao_hong() { loi "$1"; SO_HONG=$((SO_HONG + 1)); }

printf '════════════════════════════════════════════════════════════════════════\n'
printf ' KIỂM TRƯỚC KHI KHỞI ĐỘNG vLLM — Gemma 4 31B\n'
printf '════════════════════════════════════════════════════════════════════════\n'

# ── 1. Nguồn trọng số ────────────────────────────────────────────────────────
tieu "1 · Nguồn trọng số"
DUONG_DAN_NAP=""
if [ -n "$DUONG_DAN_TRONG_SO" ]; then
    if [ ! -d "$DUONG_DAN_TRONG_SO" ]; then
        bao_hong "DUONG_DAN_TRONG_SO='$DUONG_DAN_TRONG_SO' không phải thư mục."
    elif [ ! -f "$DUONG_DAN_TRONG_SO/config.json" ]; then
        bao_hong "'$DUONG_DAN_TRONG_SO' thiếu config.json — đây không phải thư mục trọng số Hugging Face."
    else
        DUONG_DAN_NAP="$DUONG_DAN_TRONG_SO"
        nhac "Nạp từ đĩa: $DUONG_DAN_NAP"
        nhac "Kịch bản này KHÔNG tải gì thêm."
    fi
elif [ "$CHO_PHEP_TAI_TRONG_SO" = "co" ]; then
    DUONG_DAN_NAP="$MO_HINH_GEMMA"
    nhac "CHO_PHEP_TAI_TRONG_SO=co ⇒ vLLM sẽ tự kéo '$MO_HINH_GEMMA' từ Hugging Face."
    nhac "⚠ Bản BF16 khoảng 62,5 GB. Kiểm dung lượng đĩa và băng thông TRƯỚC khi để nó chạy."
    if [ -n "${HUGGING_FACE_HUB_TOKEN:-}" ]; then
        nhac "Có HUGGING_FACE_HUB_TOKEN trong môi trường (kịch bản KHÔNG in và KHÔNG ghi giá trị)."
    else
        nhac "Không có HUGGING_FACE_HUB_TOKEN. Đo 26/09/2026: kho Gemma 4 31B khai gated = false"
        nhac "nên thường không cần. Nếu Hugging Face trả 401/403 thì đặt biến ấy rồi chạy lại."
    fi
else
    bao_hong "Chưa biết lấy trọng số ở đâu. Chọn một trong hai, tường minh:"
    nhac "  (a) đã có trên đĩa  →  DUONG_DAN_TRONG_SO=/duong/dan/toi/gemma-4-31b-it"
    nhac "  (b) cho phép tải    →  CHO_PHEP_TAI_TRONG_SO=co   (~62,5 GB, BF16)"
    nhac "Không có mặc định nào ở đây là CỐ Ý: mặc định tải 62,5 GB là một tai nạn chờ sẵn."
fi

# ── 2. Tên phục vụ ───────────────────────────────────────────────────────────
tieu "2 · Tên phục vụ (--served-model-name)"
if kiem_ten_phuc_vu "$TEN_PHUC_VU" "$BDSG_DA_TINH_CHINH"; then
    nhac "TEN_PHUC_VU='$TEN_PHUC_VU' — chấp nhận."
    if [ "$BDSG_DA_TINH_CHINH" != "co" ]; then
        nhac "Trọng số đang nạp được khai là CỦA GOOGLE, BDSG chỉ phục vụ."
        nhac "⇒ bdsg_la_trong_so_bdsg phải là FALSE ở mọi chỗ khai ra ngoài."
    fi
else
    bao_hong "TEN_PHUC_VU='$TEN_PHUC_VU' có chữ 'bdsg' nhưng BDSG_DA_TINH_CHINH != co."
    nhac "Tên ấy nói với người đọc rằng BDSG đã huấn luyện ra trọng số này. Không đúng."
    nhac "Đặt tên trung thực (ví dụ 'gemma-4-31b-it'), hoặc — CHỈ khi chính BDSG đã huấn"
    nhac "luyện ra tệp trọng số đang nạp — đặt BDSG_DA_TINH_CHINH=co."
fi

# ── 3. vLLM ──────────────────────────────────────────────────────────────────
tieu "3 · vLLM"
PHIEN_BAN_VLLM=""
if ! command -v "$PYTHON_VLLM" >/dev/null 2>&1; then
    bao_hong "không thấy trình thông dịch '$PYTHON_VLLM'. Đặt PYTHON_VLLM cho đúng."
else
    PHIEN_BAN_VLLM="$("$PYTHON_VLLM" -c 'import vllm; print(vllm.__version__)' 2>/dev/null)"
    if [ -z "$PHIEN_BAN_VLLM" ]; then
        bao_hong "'$PYTHON_VLLM' không nạp được vLLM."
        nhac "Cài theo trien-khai/yeu-cau.txt. Kiến trúc gemma4 chỉ có từ vLLM $PHIEN_BAN_VLLM_TOI_THIEU."
    elif ! du_phien_ban "$PHIEN_BAN_VLLM" "$PHIEN_BAN_VLLM_TOI_THIEU"; then
        bao_hong "vLLM $PHIEN_BAN_VLLM < $PHIEN_BAN_VLLM_TOI_THIEU — bản này CHƯA biết kiến trúc gemma4."
        nhac "Chạy tiếp thì lỗi sẽ là 'kiến trúc không được hỗ trợ', không hề nhắc tới phiên bản."
    else
        nhac "vLLM $PHIEN_BAN_VLLM (≥ $PHIEN_BAN_VLLM_TOI_THIEU) — đạt."
    fi
fi
if ! command -v vllm >/dev/null 2>&1; then
    bao_hong "không thấy lệnh 'vllm' trong PATH."
fi

# ── 4. GPU và VRAM ───────────────────────────────────────────────────────────
tieu "4 · GPU và VRAM"
TRONG_SO_MIB="$(tinh_trong_so_mib "$LUONG_TU_HOA")"
if [ "$TRONG_SO_MIB" -eq 0 ]; then
    bao_hong "LUONG_TU_HOA='$LUONG_TU_HOA' không nằm trong danh sách đã khai ⇒ không tính được bộ nhớ."
    nhac "Để trống (BF16), hoặc: fp8 · awq · awq_marlin · gptq · gptq_marlin · bitsandbytes · compressed-tensors"
else
    KV_MIB="$(tinh_kv_mib "$NGU_CANH_TOI_DA" "$SO_CHUOI_DONG_THOI")"
    CAN_MIB=$(( TRONG_SO_MIB + KV_MIB + DU_PHONG_MIB ))
    nhac "Trọng số  : $TRONG_SO_MIB MiB  (mức lượng tử hoá: ${LUONG_TU_HOA:-bf16/không})"
    nhac "KV cache  : $KV_MIB MiB  (ngữ cảnh $NGU_CANH_TOI_DA × $SO_CHUOI_DONG_THOI chuỗi)"
    nhac "Dự phòng  : $DU_PHONG_MIB MiB  (khoản chừa theo kinh nghiệm, CHƯA ĐO)"
    nhac "⇒ Cần    : $CAN_MIB MiB — toàn bộ là SỐ TÍNH RA, chưa đo trên máy thật."

    if ! command -v nvidia-smi >/dev/null 2>&1; then
        bao_hong "không thấy nvidia-smi ⇒ không chứng minh được máy này có GPU NVIDIA."
        nhac "Không đoán và không chạy tiếp: vLLM sẽ chết ở bước nạp, sau khi đã đọc xong trọng số."
        nhac "Máy không có GPU NVIDIA thì mô hình 31B này KHÔNG chạy được ở đây — xem"
        nhac "tai-lieu/GEMMA4-31B.md, mục cấu hình máy."
    else
        DS_VRAM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null)"
        if [ -z "$DS_VRAM" ]; then
            bao_hong "nvidia-smi có mặt nhưng không trả về GPU nào."
        else
            SO_GPU=0; TONG_VRAM=0; DS_MOT_DONG=""
            while read -r MOT; do
                [ -z "$MOT" ] && continue
                SO_GPU=$((SO_GPU + 1)); TONG_VRAM=$((TONG_VRAM + MOT))
                DS_MOT_DONG="$DS_MOT_DONG $MOT"
            done <<< "$DS_VRAM"
            nhac "Thấy $SO_GPU GPU, tổng $TONG_VRAM MiB VRAM."

            if [ "$SO_GPU_SONG_SONG" -gt "$SO_GPU" ]; then
                bao_hong "SO_GPU_SONG_SONG=$SO_GPU_SONG_SONG nhưng máy chỉ có $SO_GPU GPU."
            fi
            # vLLM chỉ được dùng TY_LE_BO_NHO_GPU phần VRAM; phần còn lại để cho trình
            # điều khiển và các tiến trình khác. Và nó chỉ trải mô hình lên đúng
            # SO_GPU_SONG_SONG card — so với TỔNG VRAM của cả máy là cách tự cho mình đi
            # qua rồi chết lúc nạp. Xem lý do đầy đủ tại chỗ khai tinh_vram_dung_duoc().
            DUNG_DUOC="$(tinh_vram_dung_duoc "$DS_MOT_DONG" "$SO_GPU_SONG_SONG" "$TY_LE_BO_NHO_GPU")"
            nhac "vLLM được dùng ~$DUNG_DUOC MiB trên $SO_GPU_SONG_SONG card (TY_LE_BO_NHO_GPU=$TY_LE_BO_NHO_GPU)."
            if [ "$SO_GPU" -gt "$SO_GPU_SONG_SONG" ]; then
                nhac "⚠ Máy có $SO_GPU GPU nhưng SO_GPU_SONG_SONG=$SO_GPU_SONG_SONG ⇒ $(( SO_GPU - SO_GPU_SONG_SONG )) card KHÔNG được dùng."
                nhac "  VRAM của các card ấy KHÔNG được cộng vào phép kiểm dưới đây, vì vLLM không đụng tới chúng."
            fi
            if [ "$DUNG_DUOC" -le 0 ]; then
                bao_hong "không tính được VRAM dùng được (thiếu GPU cho SO_GPU_SONG_SONG=$SO_GPU_SONG_SONG)."
            elif [ "$CAN_MIB" -gt "$DUNG_DUOC" ]; then
                bao_hong "Cần $CAN_MIB MiB > dùng được $DUNG_DUOC MiB. DỪNG."
                nhac "Ba cách, theo thứ tự ít mất chất lượng nhất:"
                nhac "  1. giảm NGU_CANH_TOI_DA (hiện $NGU_CANH_TOI_DA) hoặc SO_CHUOI_DONG_THOI (hiện $SO_CHUOI_DONG_THOI)"
                nhac "  2. tăng SO_GPU_SONG_SONG nếu máy còn GPU trống"
                nhac "  3. đặt LUONG_TU_HOA=fp8 hoặc awq — ĐỌC cảnh báo lượng tử hoá trong"
                nhac "     tai-lieu/GEMMA4-31B.md trước khi chọn cách này"
            else
                nhac "Đủ chỗ theo phép tính: cần $CAN_MIB MiB ≤ dùng được $DUNG_DUOC MiB."
            fi
        fi
    fi
fi

# ── 5. Ngữ cảnh ──────────────────────────────────────────────────────────────
tieu "5 · Ngữ cảnh"
if [ "$NGU_CANH_TOI_DA" -gt 262144 ]; then
    bao_hong "NGU_CANH_TOI_DA=$NGU_CANH_TOI_DA vượt max_position_embeddings của mô hình (262144)."
elif [ "$NGU_CANH_TOI_DA" -gt 32768 ]; then
    nhac "⚠ NGU_CANH_TOI_DA=$NGU_CANH_TOI_DA là lớn. KV cache tăng TUYẾN TÍNH theo số này ở 10"
    nhac "  lớp chú ý toàn cục. Bảng đầy đủ trong tai-lieu/GEMMA4-31B.md."
else
    nhac "NGU_CANH_TOI_DA=$NGU_CANH_TOI_DA — trong khoảng an toàn."
fi

# ── Kết luận phần kiểm ───────────────────────────────────────────────────────
printf '\n════════════════════════════════════════════════════════════════════════\n'
if [ "$SO_HONG" -gt 0 ]; then
    printf ' KIỂM KHÔNG ĐẠT: %d vấn đề. KHÔNG khởi động vLLM.\n' "$SO_HONG"
    printf '════════════════════════════════════════════════════════════════════════\n'
    exit 1
fi
printf ' KIỂM ĐẠT toàn bộ.\n'
printf '════════════════════════════════════════════════════════════════════════\n'

# ── Dựng lệnh ────────────────────────────────────────────────────────────────
# Dùng MẢNG chứ không dùng chuỗi: một đường dẫn có khoảng trắng sẽ bị chuỗi tách sai,
# và cách sửa mà người ta hay chọn là bọc thêm một lớp trình bao — tức là mở đúng cái
# cửa mà cong/khong-cua-hau.py chặn.
LENH=(vllm serve "$DUONG_DAN_NAP"
      --served-model-name "$TEN_PHUC_VU"
      --host "$DIA_CHI_NGHE"
      --port "$CONG_NGHE"
      --max-model-len "$NGU_CANH_TOI_DA"
      --gpu-memory-utilization "$TY_LE_BO_NHO_GPU"
      --max-num-seqs "$SO_CHUOI_DONG_THOI"
      --tensor-parallel-size "$SO_GPU_SONG_SONG"
      --dtype "$KIEU_DU_LIEU")
if [ -n "$LUONG_TU_HOA" ]; then
    LENH+=(--quantization "$LUONG_TU_HOA")
fi
if [ -n "${VLLM_API_KEY:-}" ]; then
    # KHÔNG truyền giá trị khoá qua dòng lệnh: dòng lệnh đọc được bằng `ps` từ tài khoản
    # khác trên cùng máy. vLLM tự đọc biến môi trường VLLM_API_KEY, nên chỉ cần để nó ở đó.
    nhac "Có VLLM_API_KEY trong môi trường — vLLM sẽ tự đọc. Kịch bản không in và không truyền lại."
fi

if [ "$CHE_DO" = "chi-kiem" ]; then
    printf '\n--chi-kiem: dừng tại đây, không khởi động.\n'
    exit 0
fi
if [ "$CHE_DO" = "in-lenh" ]; then
    printf '\nLệnh sẽ chạy:\n'
    printf '  %q' "${LENH[@]}"; printf '\n'
    exit 0
fi

printf '\nKhởi động vLLM…\n'
printf '  %q' "${LENH[@]}"; printf '\n\n'
exec "${LENH[@]}"
