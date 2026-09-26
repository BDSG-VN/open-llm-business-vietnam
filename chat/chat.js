/**
 * BDSG Chat — giao diện.
 *
 * Không khung, không bước đóng gói. Đây không phải sự tiết kiệm mà là một
 * quyết định: dự án này đã mất nhiều giờ vì "đã sửa mã mà trang vẫn phục vụ
 * gói cũ". Khi tệp được phục vụ CHÍNH LÀ tệp trong kho mã, cả họ lỗi đó biến
 * mất.
 */

const $ = (id) => document.getElementById(id);

const trangThai = {
  hoiThoaiId: null,
  dangChay: false,
  toi: null,        // null = khách
  hanMuc: null,
  moHinh: null,
  mucNoLuc: null,
  huy: null,
};

// ════════════════════════════════════════════════════════════════════════
// Hiển thị chữ AN TOÀN
//
// Câu trả lời của mô hình là dữ liệu KHÔNG TIN ĐƯỢC: nó có thể chứa thẻ HTML,
// và nội dung nó sinh ra một phần đến từ câu hỏi của người dùng. Nên không có
// `innerHTML` cho nội dung mô hình ở bất cứ đâu trong tệp này. Định dạng nhẹ
// dưới đây dựng bằng DOM thật, không bằng chuỗi HTML.
// ════════════════════════════════════════════════════════════════════════

/** Dựng nội dung có khối mã và chữ đậm, bằng DOM — không nối chuỗi HTML. */
function veNoiDung(el, van) {
  el.textContent = "";
  // Tách theo khối mã ```…```
  const phan = van.split(/```/g);
  phan.forEach((doan, i) => {
    if (i % 2 === 1) {
      const boc = document.createElement("div");
      boc.className = "boc-ma";
      const pre = document.createElement("pre");
      const code = document.createElement("code");
      // Bỏ tên ngôn ngữ ở dòng đầu nếu có.
      const nl = doan.indexOf("\n");
      const ten = nl > -1 && !doan.slice(0, nl).includes(" ") ? doan.slice(0, nl).trim() : "";
      code.textContent = ten !== "" ? doan.slice(nl + 1) : doan;
      pre.append(code);

      /* Đầu khối: tên ngôn ngữ (nếu có) và nút chép.
         Chép khối mã bằng cách bôi đen là việc dễ trượt — một dòng thừa hay
         thiếu là mã chạy sai. Một nút là một lần bấm, và luôn chép đúng khối. */
      const dau = document.createElement("div");
      dau.className = "boc-ma__dau";
      const nhan = document.createElement("span");
      nhan.className = "boc-ma__ten";
      nhan.textContent = ten;
      const nut = document.createElement("button");
      nut.type = "button";
      nut.className = "boc-ma__chep";
      nut.textContent = "Chép";
      nut.addEventListener("click", async () => {
        const ok = await chepVanBan(code.textContent || "");
        nut.textContent = ok ? "Đã chép" : "Không chép được";
        setTimeout(() => { nut.textContent = "Chép"; }, 1600);
      });
      dau.append(nhan, nut);

      boc.append(dau, pre);
      el.append(boc);
      return;
    }
    veDoanThuong(el, doan);
  });
}

function veDoanThuong(el, van) {
  // **đậm** và `mã ngắn`. Dùng biểu thức có bắt nhóm rồi duyệt từng mẩu.
  const mau = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let cuoi = 0;
  let m;
  while ((m = mau.exec(van)) !== null) {
    if (m.index > cuoi) el.append(document.createTextNode(van.slice(cuoi, m.index)));
    const t = m[0];
    if (t.startsWith("**")) {
      const b = document.createElement("strong");
      b.textContent = t.slice(2, -2);
      el.append(b);
    } else {
      const c = document.createElement("code");
      c.textContent = t.slice(1, -1);
      el.append(c);
    }
    cuoi = m.index + t.length;
  }
  if (cuoi < van.length) el.append(document.createTextNode(van.slice(cuoi)));
}

// ════════════════════════════════════════════════════════════════════════
// Khung tin nhắn
// ════════════════════════════════════════════════════════════════════════

function themTin(vaiTro, van) {
  $("chao")?.remove();
  const tin = document.createElement("article");
  tin.className = `tin ${vaiTro}`;

  const anh = document.createElement("div");
  anh.className = "anh";
  anh.textContent = vaiTro === "nguoi" ? (trangThai.toi?.ten?.[0]?.toUpperCase() ?? "B") : "AI";
  anh.setAttribute("aria-hidden", "true");

  const than = document.createElement("div");
  than.className = "than";
  const ai = document.createElement("div");
  ai.className = "ai";
  ai.textContent = vaiTro === "nguoi" ? (trangThai.toi?.ten ?? "Bạn") : "BDSG Chat";
  const nd = document.createElement("div");
  nd.className = "noi-dung";
  veNoiDung(nd, van);

  than.append(ai, nd);
  tin.append(anh, than);
  $("dongTin").append(tin);
  xuongDay();
  return { tin, nd, than };
}

/**
 * Cuộn xuống đáy — NHƯNG chỉ khi người đọc đang ở đáy.
 *
 * Bản trước cuộn vô điều kiện sau mỗi mẩu chữ nhận được. Hậu quả: đang đọc lại
 * một đoạn ở giữa thì bị giật xuống đáy mỗi vài trăm mili giây, không đọc nổi.
 * Ngưỡng 80px là để "gần đáy" vẫn tính là đáy — người ta hiếm khi dừng đúng
 * pixel cuối.
 */
function xuongDay(ep = false) {
  const c = $("cuon");
  if (!c) return;
  const conCach = c.scrollHeight - c.scrollTop - c.clientHeight;
  if (ep || conCach < 80) c.scrollTop = c.scrollHeight;
}

/**
 * Thanh công cụ dưới mỗi câu trả lời: chép, và sinh lại.
 *
 * Chỉ gắn khi câu trả lời ĐÃ XONG. Gắn lúc đang chảy thì nút "sinh lại" bấm
 * được giữa chừng, và người dùng có hai lượt sinh chồng lên nhau trong cùng
 * một hội thoại — hỏng ở chỗ khó lần ra.
 */
function themThanhCongCu(than, van, cauHoiGoc) {
  than.querySelector(".cong-cu-tin")?.remove();
  const thanh = document.createElement("div");
  thanh.className = "cong-cu-tin";

  thanh.append(nutCongCu("Chép", "chep", async (nut) => {
    const xong = await chepVanBan(van);
    nut.querySelector(".cc-chu").textContent = xong ? "Đã chép" : "Không chép được";
    setTimeout(() => { nut.querySelector(".cc-chu").textContent = "Chép"; }, 1600);
  }));

  if (cauHoiGoc) {
    thanh.append(nutCongCu("Sinh lại", "sinh-lai", () => {
      if (trangThai.dangChay) return;
      /* Gỡ CẢ cặp câu hỏi + câu trả lời cũ khỏi màn hình trước khi hỏi lại.
         Để lại câu hỏi cũ thì nó hiện hai lần. */
      const tinMay = than.closest(".tin");
      const tinNguoi = tinMay?.previousElementSibling;
      tinMay?.remove();
      if (tinNguoi?.classList.contains("nguoi")) tinNguoi.remove();
      hoi(cauHoiGoc);
    }));
  }
  than.append(thanh);
}

function nutCongCu(chu, ma, khiBam) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = `cc cc--${ma}`;
  b.title = chu;
  const t = document.createElement("span");
  t.className = "cc-chu";
  t.textContent = chu;
  b.append(t);
  b.addEventListener("click", () => khiBam(b));
  return b;
}

/**
 * Chép vào bộ nhớ tạm.
 *
 * `navigator.clipboard` không có ở ngữ cảnh không bảo mật và có thể bị chính
 * sách quyền từ chối, nên phải có đường lùi. Trả true/false để nơi gọi nói
 * đúng sự thật với người dùng thay vì luôn hiện "Đã chép".
 */
async function chepVanBan(van) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(van);
      return true;
    }
  } catch { /* rơi xuống đường lùi */ }
  try {
    const o = document.createElement("textarea");
    o.value = van;
    o.setAttribute("readonly", "");
    o.style.position = "fixed";
    o.style.opacity = "0";
    document.body.append(o);
    o.select();
    const ok = document.execCommand("copy");
    o.remove();
    return ok;
  } catch { return false; }
}

function baoLoi(van, coNutDangNhap) {
  const p = document.createElement("div");
  p.className = "bao-loi";
  p.append(document.createTextNode(van));
  if (coNutDangNhap) {
    p.append(document.createTextNode(" "));
    const a = document.createElement("a");
    a.href = duongDangNhap();
    a.textContent = "Đăng nhập bằng tài khoản BDSG →";
    p.append(a);
  }
  $("dongTin").append(p);
  xuongDay();
}

function duongDangNhap() {
  return `/api/dang-nhap/bat-dau?ve=${encodeURIComponent(location.pathname + location.search)}`;
}

// ════════════════════════════════════════════════════════════════════════
// Gọi máy chủ
// ════════════════════════════════════════════════════════════════════════

async function layJson(duong, tuyChon) {
  const r = await fetch(duong, { credentials: "same-origin", ...tuyChon });
  if (!r.ok) throw new Error(`${duong} → HTTP ${r.status}`);
  return r.json();
}

/**
 * Đọc dòng SSE từ một phản hồi fetch.
 *
 * Tự đọc thay vì dùng `EventSource` vì EventSource chỉ làm được GET, mà câu
 * hỏi phải đi bằng POST (nó dài và không nên nằm trong URL — URL vào nhật ký
 * máy chủ, còn câu hỏi của người dùng thì không nên).
 *
 * Khung SSE có thể bị CẮT ĐÔI giữa hai lần đọc; `du` giữ phần dở dang lại.
 */
async function* docSSE(rep) {
  const doc = rep.body.getReader();
  const giaiMa = new TextDecoder();
  let du = "";
  for (;;) {
    const { done, value } = await doc.read();
    if (done) break;
    du += giaiMa.decode(value, { stream: true });
    let i;
    while ((i = du.indexOf("\n\n")) !== -1) {
      const khung = du.slice(0, i);
      du = du.slice(i + 2);
      let loai = "message";
      let duLieu = "";
      for (const dong of khung.split("\n")) {
        if (dong.startsWith("event:")) loai = dong.slice(6).trim();
        else if (dong.startsWith("data:")) duLieu += dong.slice(5).trim();
      }
      if (duLieu === "") continue;
      try {
        yield { loai, du: JSON.parse(duLieu) };
      } catch {
        /* khung hỏng thì bỏ, không làm đứt cả câu trả lời */
      }
    }
  }
}

async function hoi(cauHoi) {
  if (trangThai.dangChay || cauHoi.trim() === "") return;
  trangThai.dangChay = true;
  /* Nút gửi ĐỔI VAI thành nút dừng thay vì bị vô hiệu hoá.
     Một nút xám trong lúc mô hình nói ba mươi giây là ba mươi giây người dùng
     không có cách nào thoát ra ngoài việc tải lại trang — và tải lại trang thì
     mất luôn câu đang chảy. */
  datVaiNutGui("dung");
  $("o").value = "";
  $("o").style.height = "auto";

  const huy = new AbortController();
  trangThai.huy = huy;

  themTin("nguoi", cauHoi);

  const { nd } = themTin("may", "");
  const gomay = document.createElement("div");
  gomay.className = "dang-go";
  gomay.append(...[0, 1, 2].map(() => document.createElement("span")));
  nd.append(gomay);

  let daNhan = "";
  try {
    const rep = await fetch("/api/hoi", {
      method: "POST",
      credentials: "same-origin",
      headers: { "content-type": "application/json" },
      signal: huy.signal,
      body: JSON.stringify({
        hoiThoaiId: trangThai.hoiThoaiId,
        noiDung: cauHoi,
        mucNoLuc: trangThai.mucNoLuc,
      }),
    });

    if (rep.status === 429) {
      nd.closest(".tin").remove();
      const g = await rep.json().catch(() => ({}));
      const gio = g.moLaiSauGiay ? Math.ceil(g.moLaiSauGiay / 3600) : null;
      baoLoi(
        `Bạn đã dùng hết lượt hỏi miễn phí${gio ? ` (mở lại sau ~${gio} giờ)` : ""}.`,
        true,
      );
      return;
    }
    if (!rep.ok) {
      nd.closest(".tin").remove();
      const g = await rep.json().catch(() => ({}));
      baoLoi(moTaLoi(g.loi) , false);
      return;
    }

    for await (const { loai, du } of docSSE(rep)) {
      if (loai === "batdau") {
        trangThai.hoiThoaiId = du.hoiThoaiId;
      } else if (loai === "chu") {
        daNhan += du.chu;
        veNoiDung(nd, daNhan);
        xuongDay();
      } else if (loai === "loi") {
        gomay.remove();
        baoLoi(du.thongBao, false);
      } else if (loai === "xong") {
        gomay.remove();
        veNoiDung(nd, daNhan);
        veTrichDan(nd.parentElement, du.trichDan);
        ghiNhanMoHinh(nd.parentElement, du);
        themThanhCongCu(nd.parentElement, daNhan, cauHoi);
      }
    }
  } catch (e) {
    gomay.remove();
    if (e && e.name === "AbortError") {
      /* Người dùng tự bấm dừng. GIỮ phần đã nhận — vứt đi là phạt họ vì đã
         dừng đúng lúc. Gắn thanh công cụ để sinh lại được ngay. */
      if (daNhan !== "") {
        veNoiDung(nd, daNhan);
        const ghi = document.createElement("div");
        ghi.className = "da-dung";
        ghi.textContent = "Đã dừng theo yêu cầu.";
        nd.append(ghi);
        themThanhCongCu(nd.parentElement, daNhan, cauHoi);
      } else {
        nd.closest(".tin")?.remove();
      }
    } else {
      baoLoi("Mất kết nối giữa chừng. Thử lại nhé.", false);
    }
  } finally {
    gomay.remove();
    trangThai.dangChay = false;
    trangThai.huy = null;
    datVaiNutGui("gui");
    $("o").focus();
    napToi();
    napDsHoiThoai();
  }
}

/**
 * Đổi nút gửi giữa hai vai: gửi và dừng.
 *
 * Dùng MỘT nút đổi vai chứ không phải hai nút cạnh nhau, vì hai nút thì lúc
 * nào cũng có một cái vô nghĩa, và ở màn hẹp chúng ăn mất chỗ của ô chữ.
 */
function datVaiNutGui(vai) {
  const b = $("gui");
  if (!b) return;
  const dung = vai === "dung";
  b.classList.toggle("gui--dung", dung);
  b.setAttribute("aria-label", dung ? "Dừng sinh" : "Gửi");
  b.title = dung ? "Dừng sinh" : "Gửi";
  b.disabled = false;
  b.innerHTML = dung
    ? '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="1.5"/></svg>'
    : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
}

function moTaLoi(ma) {
  if (ma === "rong") return "Câu hỏi đang trống.";
  if (ma === "qua-dai") return "Câu hỏi dài quá (tối đa 12.000 ký tự).";
  if (ma === "ky-tu-dieu-khien") return "Câu hỏi chứa ký tự không hợp lệ.";
  return "Có lỗi khi gửi câu hỏi. Thử lại sau ít phút.";
}

/**
 * Hiện tên mô hình ĐÃ TRẢ LỜI, không phải tên đã yêu cầu.
 *
 * Cổng LiteLLM có thể lặng lẽ rơi sang mô hình khác khi khoá thượng nguồn
 * chết (đo ngày 20/09/2026: 5 alias đều rơi về deepseek-flash). Nếu giao diện
 * hiện tên đã YÊU CẦU thì người dùng bị nói dối và không ai biết.
 */
/**
 * Bảng NGUỒN dưới câu trả lời.
 *
 * Mô hình viết "[1]", "[2]" trong câu trả lời. Không có bảng này thì đó là
 * những con số trỏ vào hư không — vẻ ngoài của một câu có nguồn mà người đọc
 * không có cách nào kiểm. Đúng thứ cả hệ được dựng ra để chống.
 *
 * Không có nguồn thì KHÔNG vẽ khung rỗng: một tiêu đề "Nguồn" với danh sách
 * trống còn tệ hơn không có tiêu đề nào.
 */
function veTrichDan(khung, ds) {
  if (!khung || !Array.isArray(ds) || ds.length === 0) return;
  const cu = khung.querySelector(".trich-dan");
  if (cu) cu.remove();
  const d = document.createElement("div");
  d.className = "trich-dan";
  const t = document.createElement("div");
  t.className = "trich-dan__tieu-de";
  t.textContent = ds.length + " nguồn BDSG tra cứu được";
  d.appendChild(t);
  const ul = document.createElement("ul");
  for (const x of ds) {
    const li = document.createElement("li");
    const nhan = document.createElement("span");
    nhan.className = "trich-dan__nhan";
    nhan.textContent = "[" + x.nhan + "]";
    li.appendChild(nhan);
    // textContent, KHÔNG innerHTML: đường dẫn tới từ CSDL, và một tên doanh
    // nghiệp có dấu ngoặc nhọn sẽ thành thẻ HTML nếu nhét thẳng vào innerHTML.
    li.appendChild(document.createTextNode(" " + x.nguon + " · " + x.duongDan));
    ul.appendChild(li);
  }
  d.appendChild(ul);
  khung.appendChild(d);
}

function ghiNhanMoHinh(than, du) {
  if (du.lech && du.moHinhThat) {
    const c = document.createElement("div");
    c.className = "nhan-lech";
    c.textContent = `Lưu ý: yêu cầu “${du.moHinhYeuCau}” nhưng câu trả lời đến từ “${du.moHinhThat}”.`;
    than.append(c);
    return;
  }
  if (!du.moHinhThat) return;
  const n = document.createElement("div");
  n.className = "nhan-mo-hinh";
  const ten = trangThai.moHinh?.danhSach?.find((m) => m.ma === du.moHinhThat)?.ten ?? du.moHinhThat;
  n.textContent = du.tokenRa ? `${ten} · ${du.tokenRa} token` : ten;
  than.append(n);
}

// ════════════════════════════════════════════════════════════════════════
// Cột trái
// ════════════════════════════════════════════════════════════════════════

async function napToi() {
  try {
    const t = await layJson("/api/toi");
    trangThai.toi = t.dangNhap ? { ten: t.ten, email: t.email, anh: t.anh } : null;
    trangThai.hanMuc = t.hanMuc;
    veChan();
  } catch { /* không chặn việc chat vì một lời chào */ }
}

function veChan() {
  const chan = $("canhChan");
  chan.textContent = "";

  if (trangThai.toi) {
    const hang = document.createElement("div");
    hang.className = "toi";
    if (trangThai.toi.anh) {
      const img = document.createElement("img");
      img.src = trangThai.toi.anh;
      img.alt = "";
      img.referrerPolicy = "no-referrer";
      hang.append(img);
    } else {
      const d = document.createElement("div");
      d.className = "chu-cai";
      d.textContent = (trangThai.toi.ten || "?")[0].toUpperCase();
      hang.append(d);
    }
    const ten = document.createElement("div");
    ten.className = "toi-ten";
    ten.textContent = trangThai.toi.ten;
    const ra = document.createElement("button");
    ra.className = "nut-icon";
    ra.type = "button";
    ra.title = "Đăng xuất";
    ra.setAttribute("aria-label", "Đăng xuất");
    ra.textContent = "⎋";
    ra.addEventListener("click", async () => {
      await fetch("/api/dang-xuat", { method: "POST", credentials: "same-origin" });
      location.href = "/";
    });
    hang.append(ten, ra);
    chan.append(hang);
    return;
  }

  const p = document.createElement("p");
  p.className = "the-khach";
  const hm = trangThai.hanMuc;
  if (hm) {
    p.append(document.createTextNode("Còn "));
    const b = document.createElement("b");
    b.textContent = `${hm.conLai}/${hm.conLai + hm.daDung}`;
    p.append(b, document.createTextNode(" lượt hỏi miễn phí."));
  } else {
    p.textContent = "Đăng nhập để lưu lịch sử hội thoại.";
  }
  const a = document.createElement("a");
  a.className = "nut-dang-nhap";
  a.href = duongDangNhap();
  a.textContent = "Đăng nhập bằng BDSG";
  chan.append(p, a);
}

async function napDsHoiThoai() {
  try {
    const { danhSach } = await layJson("/api/hoi-thoai");
    const ds = $("dsHoiThoai");
    ds.textContent = "";
    if (danhSach.length === 0) {
      const p = document.createElement("p");
      p.className = "ds-trong";
      p.textContent = "Chưa có hội thoại nào.";
      ds.append(p);
      return;
    }
    for (const h of danhSach) {
      /* Mỗi mục là một hàng chứa liên kết + nút xoá, chứ không phải một liên
         kết chứa nút. Nút nằm TRONG thẻ <a> thì bấm nút cũng kích hoạt liên
         kết, và người dùng vừa xoá vừa bị chuyển sang hội thoại vừa xoá. */
      const hang = document.createElement("div");
      hang.className = "hang-ht";

      const a = document.createElement("a");
      a.href = `#${h.id}`;
      a.textContent = h.tieuDe;
      a.title = h.tieuDe;
      if (h.id === trangThai.hoiThoaiId) {
        a.setAttribute("aria-current", "true");
        hang.classList.add("hang-ht--dang-mo");
      }
      a.addEventListener("click", (ev) => {
        ev.preventDefault();
        moHoiThoai(h.id);
      });

      const xoa = document.createElement("button");
      xoa.type = "button";
      xoa.className = "ht-xoa";
      xoa.title = "Xoá hội thoại";
      xoa.setAttribute("aria-label", `Xoá hội thoại: ${h.tieuDe}`);
      xoa.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">'
        + '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>';
      xoa.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        /* Hỏi lại trước khi xoá. Xoá hội thoại là việc KHÔNG lùi được — không
           có thùng rác ở phía máy chủ — nên một lần bấm nhầm là mất hẳn. */
        if (!window.confirm(`Xoá hội thoại “${h.tieuDe}”?\n\nKhông khôi phục lại được.`)) return;
        xoa.disabled = true;
        try {
          const rep = await fetch(`/api/hoi-thoai/${encodeURIComponent(h.id)}`, {
            method: "DELETE",
            credentials: "same-origin",
          });
          if (!rep.ok) throw new Error(String(rep.status));
          /* Đang mở chính hội thoại vừa xoá thì phải dọn màn hình, nếu không
             người dùng còn nhìn thấy nội dung của một thứ không còn tồn tại. */
          if (trangThai.hoiThoaiId === h.id) hoiThoaiMoi();
          napDsHoiThoai();
        } catch {
          xoa.disabled = false;
          baoLoi("Không xoá được hội thoại này. Thử lại nhé.", false);
        }
      });

      hang.append(a, xoa);
      ds.append(hang);
    }
  } catch { /* danh sách hỏng không được làm chết ô chat */ }
}

async function moHoiThoai(id) {
  try {
    const d = await layJson(`/api/hoi-thoai/${id}`);
    trangThai.hoiThoaiId = id;
    $("dongTin").textContent = "";
    for (const t of d.tinNhan) themTin(t.vaiTro === "nguoi" ? "nguoi" : "may", t.noiDung);
    dongCanh();
    napDsHoiThoai();
  } catch {
    baoLoi("Không mở được hội thoại này.", false);
  }
}

/**
 * Nạp mô hình và mức nỗ lực.
 *
 * ═══ VÌ SAO KHÔNG CÒN Ô CHỌN BỐN MÔ HÌNH ═══
 *
 * Bốn tên cũ trộn HAI trục vào một danh sách phẳng — "có truy hồi hay không"
 * và "nghĩ nhanh hay nghĩ kỹ" — nên người dùng phải tự suy ra tích của hai
 * trục mới chọn đúng. Đo ở mốc M5: 28/31 lượt rơi vào nhánh KHÔNG truy hồi,
 * tức phần lớn người dùng không bao giờ chạm tới dữ liệu của BDSG. Nay còn
 * một cái tên và một nút mức nỗ lực; truy hồi luôn bật ở cả hai mức.
 *
 * `trangThai.moHinh.danhSach` VẪN giữ, vì `nhanMoHinh()` dùng nó để đổi mã đọc
 * được từ phản hồi thành tên người đọc được. Bỏ đi thì nhãn "câu trả lời đến
 * từ …" hiện ra mã trần — hỏng ngay tại chỗ có nhiệm vụ chống nói dối tên.
 */
async function napMoHinh() {
  try {
    const d = await layJson("/api/mo-hinh");
    trangThai.moHinh = d;

    const oTen = $("tenMoHinh");
    if (oTen && d.moHinh) {
      oTen.textContent = d.moHinh.ten;
      /* Chú giải đặt trên NÚT, không trên span: span nằm lọt trong nút nên
         chuột đi qua mép nút sẽ không hiện chú giải nếu gắn vào span. */
      const nutCha = oTen.closest("button");
      if (nutCha) nutCha.title = d.moHinh.moTa || "";
    }

    const muc = Array.isArray(d.mucNoLuc) ? d.mucNoLuc : [];
    if (muc.length === 0) return;

    /* Nhớ lựa chọn giữa các lần mở. Bọc try/catch vì ở chế độ riêng tư trình
       duyệt có thể ném ngay tại bước ĐỌC, không chỉ bước ghi. */
    let daChon = d.mucNoLucMacDinh || muc[0].muc;
    try {
      const luu = localStorage.getItem("bdsg_muc_no_luc");
      if (luu && muc.some((k) => k.muc === luu)) daChon = luu;
    } catch { /* không đọc được thì dùng mặc định */ }
    trangThai.mucNoLuc = daChon;

    const bang = $("bangNoLuc");
    const nut = $("nutNoLuc");
    const nhan = $("nhanNoLuc");
    if (!bang || !nut || !nhan) return;

    function ve() {
      bang.textContent = "";
      const dau = document.createElement("div");
      dau.className = "bang-no-luc__dau";
      dau.textContent = "Chọn mức nỗ lực";
      bang.append(dau);
      for (const k of muc) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "muc" + (k.muc === trangThai.mucNoLuc ? " muc--chon" : "");
        b.setAttribute("role", "option");
        b.setAttribute("aria-selected", String(k.muc === trangThai.mucNoLuc));
        const t = document.createElement("span");
        t.className = "muc__ten";
        t.textContent = k.ten;
        const m = document.createElement("span");
        m.className = "muc__mo";
        m.textContent = k.moTa || "";
        b.append(t, m);
        b.addEventListener("click", () => {
          trangThai.mucNoLuc = k.muc;
          try { localStorage.setItem("bdsg_muc_no_luc", k.muc); } catch { /* bỏ qua */ }
          dong();
          ve();
        });
        bang.append(b);
      }
      const dc = muc.find((k) => k.muc === trangThai.mucNoLuc);
      nhan.textContent = dc ? dc.ten : muc[0].ten;
    }

    function mo() { bang.hidden = false; nut.setAttribute("aria-expanded", "true"); }
    function dong() { bang.hidden = true; nut.setAttribute("aria-expanded", "false"); }

    nut.addEventListener("click", (e) => {
      e.stopPropagation();
      if (bang.hidden) mo(); else dong();
    });
    document.addEventListener("click", (e) => {
      if (!bang.hidden && !bang.contains(e.target) && !nut.contains(e.target)) dong();
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") dong(); });

    ve();
  } catch { /* để trống thì máy chủ dùng mặc định */ }
}

/* Giữ MỘT bản sao màn hình chào ngay khi trang nạp.
   `themTin()` xoá thẻ #chao ở lượt hỏi đầu tiên, nên tới lúc cần dựng lại thì
   nó đã không còn trong DOM để mà chép. */
const MAN_CHAO = document.getElementById("chao")?.cloneNode(true) ?? null;

// ════════════════════════════════════════════════════════════════════════
// Nối dây
// ════════════════════════════════════════════════════════════════════════

function moCanh() { $("canh").classList.add("mo"); $("phuCanh").hidden = false; }
function dongCanh() { $("canh").classList.remove("mo"); $("phuCanh").hidden = true; }

$("form").addEventListener("submit", (e) => {
  e.preventDefault();
  /* Cùng một nút, hai vai. Đang chảy thì bấm là DỪNG, không phải gửi câu mới —
     nếu không, Enter lúc đang chảy sẽ xếp hàng một lượt thứ hai. */
  if (trangThai.dangChay) { trangThai.huy?.abort(); return; }
  hoi($("o").value);
});

$("o").addEventListener("keydown", (e) => {
  // Enter gửi, Shift+Enter xuống dòng. Trên màn hình hẹp thì Enter luôn là
  // xuống dòng: bàn phím ảo không có Shift tiện, và gửi nhầm khó chịu hơn.
  if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 820) {
    e.preventDefault();
    hoi($("o").value);
  }
});

$("o").addEventListener("input", () => {
  const o = $("o");
  o.style.height = "auto";
  o.style.height = Math.min(o.scrollHeight, 200) + "px";
});

/**
 * Mở một hội thoại mới — dọn màn hình TẠI CHỖ, không tải lại trang.
 *
 * Bản trước gọi `location.reload()`. Nó chạy được, nhưng tải lại toàn bộ trang
 * để xoá vài thẻ DOM là chậm hơn hẳn và làm mất luôn tiêu điểm bàn phím. Quan
 * trọng hơn: hàm này còn được gọi sau khi XOÁ hội thoại đang mở, và tải lại
 * trang ở đó sẽ nhấp nháy một nhịp khó chịu ngay sau một thao tác vừa xong.
 */
function hoiThoaiMoi() {
  trangThai.huy?.abort();
  trangThai.hoiThoaiId = null;
  if (location.hash !== "") history.replaceState(null, "", location.pathname + location.search);
  const dong = $("dongTin");
  if (dong) {
    dong.textContent = "";
    if (MAN_CHAO !== null) dong.append(MAN_CHAO.cloneNode(true));
  }
  $("o")?.focus();
  napDsHoiThoai();
}

$("nutMoi").addEventListener("click", hoiThoaiMoi);

$("moCanh").addEventListener("click", moCanh);
$("dongCanh").addEventListener("click", dongCanh);
$("phuCanh").addEventListener("click", dongCanh);

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-hoi]");
  if (b) hoi(b.dataset.hoi);
});

// Báo lỗi đăng nhập quay về từ app.bdsg.vn.
const thamSo = new URLSearchParams(location.search);
if (thamSo.has("loi")) {
  const ma = thamSo.get("loi");
  const noi = {
    "xung-dot-danh-tinh":
      "Tài khoản này đang xung đột với một tài khoản khác. BDSG đã ghi nhận, vui lòng liên hệ hỗ trợ.",
    "state-khong-hop-le": "Phiên đăng nhập đã quá hạn. Bấm đăng nhập lại.",
  }[ma] ?? "Đăng nhập không thành công. Thử lại nhé.";
  setTimeout(() => baoLoi(noi, false), 0);
  history.replaceState(null, "", location.pathname);
}

napMoHinh();
napToi();
napDsHoiThoai();
$("o").focus();
