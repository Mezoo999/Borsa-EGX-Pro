/* EGX Pro — صفحة الفرص */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const cls = (v) => v > 0 ? "up" : (v < 0 ? "down" : "flat");

let uni = 30;
const seg = $("universeSeg");
seg.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  uni = +b.dataset.n;
  seg.querySelectorAll("button").forEach((x) => x.classList.toggle("active", +x.dataset.n === uni));
  load();
});
$("runBtn").addEventListener("click", load);

function card(r) {
  const buy = r.signal && r.signal.indexOf("شراء") >= 0;
  const sell = r.signal && r.signal.indexOf("بيع") >= 0;
  const sigColor = buy ? "#00c853" : (sell ? "#ff5c76" : "#90a4ae");
  const scoreColor = r.score >= 60 ? "#00c853" : (r.score >= 45 ? "#ffab00" : "#ff5c76");
  return `<a class="opp-card" href="/stock/${r.symbol}">
    <div class="opp-top">
      <div><div class="opp-sym">${r.short}</div><div class="opp-name">${r.name || ""}</div></div>
      <span class="badge" style="background:${sigColor}22;color:${sigColor};border-color:${sigColor}66">${r.signal || "—"}</span>
    </div>
    <div class="opp-score">
      <div class="opp-score-num" style="color:${scoreColor}">${r.score}<span>/100</span></div>
      <div class="bar"><div class="bar-fill" style="width:${r.score}%;background:${scoreColor}"></div></div>
    </div>
    <div class="opp-setup">📌 ${r.setup || "—"} <span class="muted">• ${r.wyckoff || ""}</span></div>
    <div class="opp-price">${fmt(r.price)} <span class="${cls(r.chg)}">${r.chg >= 0 ? "▲" : "▼"} ${Math.abs(r.chg).toFixed(2)}%</span></div>
    <div class="opp-meta">
      <span style="color:var(--green);">🎯 ${fmt(r.target1)}</span>
      <span style="color:var(--red);">🛡️ ${fmt(r.stop)}</span>
      <span style="color:var(--blue2);">⚖️ R:R ${r.rr}</span>
    </div>
    <div class="opp-foot"><span class="tier">${r.tier || ""}</span><span class="muted">${r.liquidity || ""}</span></div>
  </a>`;
}

async function load() {
  $("status").innerHTML = '<div class="loading">جاري تحليل السوق (قد يستغرق 15–30 ثانية)...</div>';
  $("cards").innerHTML = "";
  try {
    const d = await fetch(`/api/opportunities?universe=${uni}`).then((r) => r.json());
    if (!d || !d.length) {
      $("status").innerHTML = "";
      $("cards").innerHTML = '<div class="empty">لا توجد فرص تستوفي الشروط الآن — عدم الدخول أفضل من دخول ضعيف.</div>';
      return;
    }
    $("status").innerHTML = `<span class="muted">${d.length} سهم محلّل — مرتّب بالأقوى.</span>`;
    $("cards").innerHTML = d.map(card).join("");
  } catch (e) {
    $("status").innerHTML = "";
    $("cards").innerHTML = `<div class="error">تعذّر تحميل الفرص: ${e.message}</div>`;
  }
}
load();
