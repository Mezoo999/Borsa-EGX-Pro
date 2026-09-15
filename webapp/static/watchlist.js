/* EGX Pro — صفحة المتابعة والتنبيهات */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const cls = (v) => v > 0 ? "up" : (v < 0 ? "down" : "flat");

let wlSym = "", alSym = "";
EGX.attachPicker($("wlInput"), $("wlDrop"), (s) => { wlSym = s; $("wlInput").value = s.replace(".CA", ""); $("wlDrop").style.display = "none"; });
EGX.attachPicker($("alInput"), $("alDrop"), (s) => { alSym = s; $("alInput").value = s.replace(".CA", ""); $("alDrop").style.display = "none"; });

$("wlAdd").addEventListener("click", async () => {
  if (!wlSym) return;
  await fetch("/api/watchlist", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ symbol: wlSym }) });
  $("wlInput").value = ""; wlSym = ""; loadWatch();
});
$("alAdd").addEventListener("click", async () => {
  if (!alSym) return;
  const above = parseFloat($("alAbove").value) || null;
  const below = parseFloat($("alBelow").value) || null;
  if (!above && !below) return;
  await fetch("/api/alerts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ symbol: alSym, above: above, below: below }) });
  $("alInput").value = ""; $("alAbove").value = ""; $("alBelow").value = ""; alSym = ""; loadAlerts();
});

async function loadWatch() {
  try {
    const d = await fetch("/api/watchlist").then((r) => r.json());
    if (!d.length) { $("wlList").innerHTML = '<div class="empty" style="padding:1.2rem;">قائمتك فارغة — أضف أسهماً من الأعلى.</div>'; return; }
    $("wlList").innerHTML = d.map((w) => {
      const sigColor = w.signal && w.signal.indexOf("شراء") >= 0 ? "var(--green)" : (w.signal && w.signal.indexOf("بيع") >= 0 ? "var(--red)" : "var(--muted)");
      return `<div class="wl-item" onclick="location.href='/stock/${encodeURIComponent(w.symbol)}'" style="cursor:pointer;">
        <div style="flex:1.3;min-width:110px;"><div class="sym">${w.short}</div><div class="nm">${w.name}</div></div>
        <div style="flex:1;text-align:center;"><div style="font-weight:800;">${w.price != null ? fmt(w.price) : "—"}</div>
        <div class="${cls(w.chg || 0)}" style="font-size:0.72rem;">${w.chg != null ? (w.chg >= 0 ? "+" : "") + fmt(w.chg) + "%" : ""}</div></div>
        <span class="pill" style="color:${sigColor};border-color:${sigColor}66;">${w.signal}</span>
        <button class="btn-ghost" onclick="event.stopPropagation();delWatch('${w.symbol}')">✕</button>
      </div>`;
    }).join("");
  } catch (e) { $("wlList").innerHTML = `<div class="error">${e.message}</div>`; }
}
async function delWatch(sym) { await fetch("/api/watchlist/" + encodeURIComponent(sym), { method: "DELETE" }); loadWatch(); }

async function loadAlerts() {
  try {
    const d = await fetch("/api/alerts").then((r) => r.json());
    if (!d.length) { $("alList").innerHTML = '<div class="empty" style="padding:1.2rem;">لا توجد تنبيهات — اضبط أول تنبيه من الأعلى.</div>'; return; }
    $("alList").innerHTML = d.map((a) => {
      const parts = [];
      if (a.above) { const hit = a.price != null && a.price >= a.above; parts.push(`<span class="pill" style="color:${hit ? "var(--red)" : "var(--green)"};border-color:${hit ? "var(--red)" : "var(--green)"}66;">${hit ? "🚨" : "⏳"} فوق ${fmt(a.above)}</span>`); }
      if (a.below) { const hit = a.price != null && a.price <= a.below; parts.push(`<span class="pill" style="color:${hit ? "var(--red)" : "var(--green)"};border-color:${hit ? "var(--red)" : "var(--green)"}66;">${hit ? "🚨" : "⏳"} تحت ${fmt(a.below)}</span>`); }
      return `<div class="wl-item">
        <div style="flex:1.2;min-width:100px;"><div class="sym">${a.short}</div><div class="nm">الآن ${a.price != null ? fmt(a.price) : "—"}</div></div>
        <div style="flex:1.5;display:flex;gap:0.4rem;flex-wrap:wrap;">${parts.join("")}</div>
        <button class="btn-ghost" onclick="delAlert('${a.symbol}')">🗑️</button>
      </div>`;
    }).join("");
  } catch (e) { $("alList").innerHTML = `<div class="error">${e.message}</div>`; }
}
async function delAlert(sym) { await fetch("/api/alerts/" + encodeURIComponent(sym), { method: "DELETE" }); loadAlerts(); }

loadWatch();
loadAlerts();
setInterval(() => { loadWatch(); loadAlerts(); }, 30000);
