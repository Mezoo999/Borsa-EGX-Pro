/* EGX Pro — صفحة المحفظة */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const cls = (v) => v > 0 ? "up" : (v < 0 ? "down" : "flat");

let pickedSym = "";

EGX.attachPicker($("symInput"), $("symDrop"), (sym) => {
  pickedSym = sym;
  $("symInput").value = sym.replace(".CA", "");
  $("symDrop").style.display = "none";
  // اقتراح سعر الشراء بالسعر اللحظي
  fetch(`/api/quote/${encodeURIComponent(sym)}`).then((r) => r.json()).then((q) => {
    if (q && q.price) $("costInput").value = q.price.toFixed(2);
  }).catch(() => {});
});

$("addBtn").addEventListener("click", async () => {
  const msg = $("addMsg");
  const shares = parseFloat($("sharesInput").value);
  const cost = parseFloat($("costInput").value);
  if (!pickedSym) { msg.className = "error"; msg.textContent = "اختر سهماً من البحث أولاً."; return; }
  if (!shares || shares <= 0 || !cost || cost <= 0) { msg.className = "error"; msg.textContent = "أدخل عدد أسهم وسعر شراء صحيحين."; return; }
  try {
    const r = await fetch("/api/portfolio", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: pickedSym, shares: shares, avg_cost: cost })
    });
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || "خطأ"); }
    msg.className = "notice";
    msg.innerHTML = `✓ سُجّل ${shares} سهم ${pickedSym.replace(".CA", "")} بمتوسط ${cost.toFixed(2)}`;
    $("sharesInput").value = 100; $("costInput").value = ""; $("symInput").value = ""; pickedSym = "";
    load();
  } catch (e) { msg.className = "error"; msg.textContent = "تعذّر التسجيل: " + e.message; }
});

function render(d) {
  const s = d.summary;
  const plColor = s.pl >= 0 ? "var(--green)" : "var(--red)";
  $("sumGrid").innerHTML = `
    <div class="sum-card"><div class="lbl">القيمة السوقية</div><div class="val">${fmt(s.value, 0)} ج.م</div></div>
    <div class="sum-card"><div class="lbl">التكلفة</div><div class="val">${fmt(s.cost, 0)} ج.م</div></div>
    <div class="sum-card"><div class="lbl">الربح/الخسارة</div><div class="val" style="color:${plColor}">${s.pl >= 0 ? "+" : ""}${fmt(s.pl, 0)} ج.م</div></div>
    <div class="sum-card"><div class="lbl">العائد الكلي</div><div class="val" style="color:${plColor}">${s.pl_pct >= 0 ? "+" : ""}${fmt(s.pl_pct)}%</div></div>
    <div class="sum-card"><div class="lbl">عدد المراكز</div><div class="val">${s.count}</div></div>`;

  if (!d.positions.length) {
    $("list").innerHTML = '<div class="empty">لا توجد مراكز بعد — سجّل أول صفقة من النموذج أعلاه.</div>';
    return;
  }
  $("list").innerHTML = d.positions.map((p) => `
    <div class="wl-item">
      <div style="flex:1.4;min-width:130px;">
        <div class="sym">${p.short}</div>
        <div class="nm">${p.name} • ${p.shares} سهم</div>
      </div>
      <div style="flex:1;text-align:center;">
        <div style="font-size:0.7rem;color:var(--muted);">متوسط / الآن</div>
        <div style="font-weight:700;">${fmt(p.avg_cost)} / ${fmt(p.price)}</div>
        <div class="${cls(p.chg)}" style="font-size:0.72rem;">${p.chg >= 0 ? "+" : ""}${fmt(p.chg)}% اليوم</div>
      </div>
      <div style="flex:1;text-align:center;">
        <div style="font-size:0.7rem;color:var(--muted);">القيمة</div>
        <div style="font-weight:700;">${fmt(p.value, 0)}</div>
        <div class="${cls(p.pl)}" style="font-size:0.72rem;">${p.pl >= 0 ? "+" : ""}${fmt(p.pl, 0)} (${p.pl_pct >= 0 ? "+" : ""}${fmt(p.pl_pct)}%)</div>
      </div>
      <div style="display:flex;gap:0.4rem;">
        <button class="btn-ghost" onclick="openStock('${p.symbol}')">تحليل</button>
        <button class="btn-ghost" onclick="delPos('${p.symbol}')">🗑️</button>
      </div>
    </div>`).join("");
}

function openStock(sym) { location.href = "/stock/" + encodeURIComponent(sym); }
async function delPos(sym) {
  if (!confirm("حذف المركز بالكامل؟")) return;
  await fetch("/api/portfolio/" + encodeURIComponent(sym), { method: "DELETE" });
  load();
}

async function load() {
  try {
    const d = await fetch("/api/portfolio").then((r) => r.json());
    render(d);
  } catch (e) {
    $("list").innerHTML = `<div class="error">تعذّر التحميل: ${e.message}</div>`;
  }
}
load();
setInterval(load, 30000);
