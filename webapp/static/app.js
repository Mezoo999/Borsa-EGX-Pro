/* EGX Pro — منطق الصفحة الرئيسية */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const cls = (v) => v > 0 ? "up" : (v < 0 ? "down" : "flat");
let prevVals = {};

function flashIfChanged(el, key, val) {
  const prev = prevVals[key];
  prevVals[key] = val;
  if (prev !== undefined && Math.abs(val - prev) > 0.005) {
    el.classList.remove("flash-up", "flash-down");
    void el.offsetWidth;
    el.classList.add(val > prev ? "flash-up" : "flash-down");
  }
}

function updateClock() {
  const now = new Date();
  $("clock").textContent = now.toLocaleTimeString("ar-EG", { timeZone: "Africa/Cairo", hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "Africa/Cairo", weekday: "short", hour: "numeric", hour12: false }).formatToParts(now);
  const wd = parts.find(p => p.type === "weekday").value;
  const h = parseInt(parts.find(p => p.type === "hour").value);
  const weekend = ["Fri", "Sat"].includes(wd);
  const open = !weekend && h >= 10 && h < 14.5;
  const chip = $("statusChip");
  chip.textContent = open ? "🟢 السوق مفتوح" : "🔴 السوق مغلق";
  chip.className = "status-chip " + (open ? "status-open" : "status-closed");
}
setInterval(updateClock, 1000);
updateClock();

// البحث
const input = $("searchInput"), drop = $("searchDrop");
let searchTimer = null;
input.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const q = input.value.trim();
    if (!q) { drop.style.display = "none"; return; }
    const res = await fetch("/api/search?q=" + encodeURIComponent(q)).then(r => r.json());
    drop.innerHTML = res.map(r => `<a href="/stock/${r.symbol}"><span><b>${r.short}</b> — ${r.name}</span><span class="muted">تحليل ←</span></a>`).join("");
    drop.style.display = res.length ? "block" : "none";
  }, 250);
});
document.addEventListener("click", (e) => { if (!e.target.closest(".search-wrap")) drop.style.display = "none"; });

function renderOverview(d) {
  // المؤشرات + الاتساع
  const idxRow = $("idxRow");
  idxRow.innerHTML = d.indices.map(i => `
    <div class="idx-card">
      <div class="lbl">${i.key === "EGX30" ? "EGX30 الرئيسي" : i.key === "EGX70EWI" ? "EGX70" : i.key}</div>
      <div class="val" id="idx_${i.key}">${fmt(i.value)}</div>
      <div class="chg ${cls(i.chg)}" id="idxc_${i.key}">${i.chg >= 0 ? "▲" : "▼"} ${Math.abs(i.chg).toFixed(2)}%</div>
    </div>`).join("") + `
    <div class="idx-card" style="display:flex;flex-direction:column;justify-content:center;">
      <div class="lbl">اتساع السوق</div>
      <div class="val" style="font-size:0.95rem;"><span class="up">▲${d.breadth.up}</span> <span class="flat">=${d.breadth.flat}</span> <span class="down">▼${d.breadth.down}</span></div>
    </div>
    <div class="regime-banner" style="flex:2;min-width:240px;border-color:${d.regime.color};">
      <b style="color:${d.regime.color};">${d.regime.label}</b>
      <small>${d.regime.desc}</small>
    </div>`;
  d.indices.forEach(i => flashIfChanged($("idx_" + i.key), "idx_" + i.key, i.value));

  // الشريط المتحرك
  const items = d.tape.map(t => `<span class="tape-item" onclick="location.href='/stock/${t.symbol}'"><b>${t.symbol}</b><span class="num">${fmt(t.price)}</span><span class="${cls(t.chg)}">${t.chg >= 0 ? "▲" : "▼"}${Math.abs(t.chg).toFixed(2)}%</span></span>`).join("");
  $("tape").innerHTML = items + items; // مضاعفة للحلقة المستمرة

  // الماكرو
  $("macroRow").innerHTML = `<div class="idx-card macro-chip" style="min-width:150px;"><div class="lbl">🌍 السياق العالمي</div><div class="val" style="font-size:0.8rem;color:${d.regime.color};">${d.regime.label.split(" ").slice(1).join(" ")}</div></div>` +
    d.macro.map(m => `
    <div class="idx-card macro-chip">
      <div class="lbl">${m.label}</div>
      <div class="val num">${fmt(m.value)}</div>
      <div class="chg ${cls(m.day)}" style="font-size:0.68rem;">${m.day >= 0 ? "+" : ""}${m.day.toFixed(2)}% <span class="wk">أسبوع ${m.week >= 0 ? "+" : ""}${m.week.toFixed(2)}%</span></div>
    </div>`).join("") +
    (d.macro_signals[0] ? `<div class="idx-card" style="flex:2;min-width:260px;display:flex;align-items:center;font-size:0.75rem;color:#cfd8dc;">
      ${d.macro_signals[0].tone === "pos" ? "🟢" : d.macro_signals[0].tone === "neg_mixed" ? "🟠" : "🔴"} ${d.macro_signals[0].text.slice(0, 130)}...
    </div>` : "");

  // التحركات (صفوف قابلة للنقر)
  const rowHtml = (r) => `<tr class="clickable" onclick="location.href='/stock/${r.symbol}'">
    <td class="sym">${r.symbol}</td><td class="nm">${r.name}</td>
    <td class="num">${fmt(r.price)}</td><td class="num ${cls(r.chg)}">${r.chg >= 0 ? "+" : ""}${r.chg.toFixed(2)}%</td></tr>`;
  $("upTable").querySelector("tbody").innerHTML = d.movers.up.map(rowHtml).join("");
  $("downTable").querySelector("tbody").innerHTML = d.movers.down.map(rowHtml).join("");
  $("breadthLine").textContent = `من إجمالي ${d.breadth.up + d.breadth.down + d.breadth.flat} سهماً متداولاً — المصدر: TradingView (يُحدَّث تلقائياً)`;

  // القطاعات
  const names = d.sectors.map(s => `${s.name} (${s.count})`).reverse();
  const values = d.sectors.map(s => s.chg).reverse();
  echarts.init($("sectors")).setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: "#10141d", borderColor: "#1f2d45", textStyle: { color: "#e8edf4" } },
    grid: { left: 10, right: 60, top: 5, bottom: 5, containLabel: true },
    xAxis: { type: "value", axisLabel: { color: "#7d8db1", formatter: "{value}%" }, splitLine: { lineStyle: { color: "rgba(31,45,69,0.45)" } } },
    yAxis: { type: "category", data: names, axisLabel: { color: "#cfd8dc", fontSize: 11 }, axisLine: { lineStyle: { color: "rgba(31,45,69,0.45)" } } },
    series: [{ type: "bar", barMaxWidth: 22, animationDuration: 1500, animationEasing: "elasticOut",
      data: values.map(v => ({ value: v, itemStyle: { color: v > 0 ? "#00c853" : (v < 0 ? "#ff5c76" : "#546e7a") } })),
      label: { show: true, position: "right", color: "#cfd8dc", formatter: "{c}%" } }],
  });

  // الأخبار
  $("news").innerHTML = d.news.length ? d.news.map(n => `
    <div class="news-item"><a class="t" href="${n.link}" target="_blank">${n.title}</a>
    <div class="m">${n.symbol} • ${n.pub} • ${n.source || "مصدر خارجي"}</div></div>`).join("")
    : '<div class="loading">لا توجد أخبار الآن</div>';
}

async function loadOverview() {
  try {
    const d = await fetch("/api/overview").then(r => r.json());
    renderOverview(d);
  } catch (e) { console.error(e); }
}
loadOverview();
setInterval(loadOverview, 30000);
