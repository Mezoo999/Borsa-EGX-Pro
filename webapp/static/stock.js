/* EGX Pro — صفحة السهم */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const cls = (v) => v > 0 ? "up" : (v < 0 ? "down" : "flat");

const SYM = decodeURIComponent(location.pathname.split("/").pop()).toUpperCase();
const API_SYM = SYM.endsWith(".CA") ? SYM : SYM + ".CA";

// الساعة وحالة السوق (نفس منطق الرئيسية)
function updateClock() {
  const now = new Date();
  $("clock").textContent = now.toLocaleTimeString("ar-EG", { timeZone: "Africa/Cairo", hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "Africa/Cairo", weekday: "short", hour: "numeric", hour12: false }).formatToParts(now);
  const wd = parts.find(p => p.type === "weekday").value;
  const h = parseInt(parts.find(p => p.type === "hour").value);
  const open = !["Fri", "Sat"].includes(wd) && h >= 10 && h < 14.5;
  const chip = $("statusChip");
  chip.textContent = open ? "🟢 السوق مفتوح" : "🔴 السوق مغلق";
  chip.className = "status-chip " + (open ? "status-open" : "status-closed");
}
setInterval(updateClock, 1000); updateClock();

// البحث
const input = $("searchInput"), drop = $("searchDrop");
let t = null;
input.addEventListener("input", () => {
  clearTimeout(t);
  t = setTimeout(async () => {
    const q = input.value.trim();
    if (!q) { drop.style.display = "none"; return; }
    const res = await fetch("/api/search?q=" + encodeURIComponent(q)).then(r => r.json());
    drop.innerHTML = res.map(r => `<a href="/stock/${r.symbol}"><b>${r.short}</b> — ${r.name}</a>`).join("");
    drop.style.display = res.length ? "block" : "none";
  }, 250);
});
document.addEventListener("click", (e) => { if (!e.target.closest(".search-wrap")) drop.style.display = "none"; });

// الرسم الحي
let chart = null, candleSeries = null, volSeries = null, s20 = null, s50 = null;
function initChart() {
  chart = LightweightCharts.createChart($("chart"), {
    width: $("chart").clientWidth, height: 520,
    layout: { background: { type: "solid", color: "#10141d" }, textColor: "#cfd8dc" },
    grid: { vertLines: { color: "rgba(31,45,69,0.45)" }, horzLines: { color: "rgba(31,45,69,0.45)" } },
    crosshair: { mode: 0, vertLine: { color: "#2962ff", labelBackgroundColor: "#2962ff" }, horzLine: { color: "#2962ff", labelBackgroundColor: "#2962ff" } },
    rightPriceScale: { borderColor: "#1f2d45" },
    timeScale: { borderColor: "#1f2d45" },
  });
  candleSeries = chart.addCandlestickSeries({ upColor: "#00c853", downColor: "#ff5c76", borderVisible: false, wickUpColor: "#00c853", wickDownColor: "#ff5c76", priceLineColor: "#2962ff" });
  volSeries = chart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "" });
  volSeries.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
  s20 = chart.addLineSeries({ color: "#ffab00", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
  s50 = chart.addLineSeries({ color: "#29b6f6", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
  window.addEventListener("resize", () => chart.applyOptions({ width: $("chart").clientWidth }));
}
initChart();

async function loadCandles() {
  const d = await fetch(`/api/stock/${encodeURIComponent(API_SYM)}/candles`).then(r => r.json());
  if (!d.candles || !d.candles.length) return;
  candleSeries.setData(d.candles);
  volSeries.setData(d.volumes || []);
  s20.setData(d.sma20 || []);
  s50.setData(d.sma50 || []);
  chart.timeScale().fitContent();
}

let prevLive = null;
async function loadStock() {
  const d = await fetch(`/api/stock/${encodeURIComponent(API_SYM)}`).then(r => r.json());
  if (d.error) { $("stockHeader").innerHTML = `<div class="loading">${d.error}</div>`; return; }

  $("stockHeader").innerHTML = `
    <h1>${d.name}</h1><span class="sym-code">${d.symbol}</span>
    <span class="sector-chip">${d.sector || "سهم مصري"}</span>
    <div class="price-big" id="livePrice">${fmt(d.live)}</div>
    <div class="price-chg ${cls(d.live_chg)}">${d.live_chg >= 0 ? "▲" : "▼"} ${Math.abs(d.live_chg).toFixed(2)}%</div>`;
  const lp = $("livePrice");
  if (prevLive !== null && Math.abs(d.live - prevLive) > 0.005) {
    lp.classList.remove("flash-up", "flash-down"); void lp.offsetWidth;
    lp.classList.add(d.live > prevLive ? "flash-up" : "flash-down");
  }
  prevLive = d.live;

  // المؤشرات
  const ind = d.indicators || {};
  $("indGrid").innerHTML = Object.entries({
    "آخر إغلاق": fmt(d.close), "الدعم": d.support ? fmt(d.support) : "—",
    "المقاومة": d.resistance ? fmt(d.resistance) : "—",
    "الإشارة": d.signal, "النموذج": d.setup || "—",
    ...Object.fromEntries(Object.entries(ind).map(([k, v]) => [k, typeof v === "number" ? fmt(v, 1) : v])),
  }).map(([k, v]) => `<div class="ind-cell"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");

  // بطاقة الذكاء الاصطناعي
  if (d.ml) {
    const prob = d.ml.prob;
    const m = d.ml.metrics || {};
    const color = prob >= 60 ? "#00c853" : (prob >= 45 ? "#ffab00" : "#ff5c76");
    const verdict = prob >= 60 ? "النموذج واثق — فرصة جيدة إحصائياً" : (prob >= 45 ? "منطقة حيرة — يفضل الانتظار" : "النموذج لا يرى ميزة — الأفضل الابتعاد");
    $("mlCard").innerHTML = `
      <h3>🤖 احتمالية نجاح الشراء (5 جلسات)</h3>
      <div class="ml-prob" style="color:${color};">${prob.toFixed(1)}%</div>
      <div class="ml-bar"><div class="ml-marker" style="left:${Math.min(97, Math.max(3, prob))}%;"></div></div>
      <div style="font-weight:700;color:${color};margin-bottom:0.4rem;">${verdict}</div>
      <div class="ml-meta">
        مدرب على ${fmt(m.samples_train || 0, 0)} صفقة تاريخية • اختبار زمني على ${fmt(m.samples_test || 0, 0)} صفقة<br>
        دقة الاختبار: <b>${m.accuracy_test || "—"}%</b> (المعدل الأساسي ${m.base_rate_up || "—"}%)<br>
        صفقات ثقته النموذج >60%: نجاح <b>${m.confident_win_rate || "—"}%</b> من ${m.confident_trades || 0} صفقة<br>
        آخر تدريب: ${m.trained_at || "—"}
      </div>`;
  } else {
    $("mlCard").innerHTML = `<h3>🤖 احتمالية نجاح الشراء</h3><div class="loading">النموذج غير مدرّب بعد — شغّل ml_train.py</div>`;
  }

  // خطة الصفقة
  const tk = d.ticket;
  if (tk) {
    $("ticketCard").innerHTML = `
      <h3>📋 خطة الصفقة التنفيذية</h3>
      <div style="font-size:0.8rem;color:#00e676;font-weight:700;margin-bottom:0.4rem;">⏱️ ${tk.type} — صلاحية 5 جلسات</div>
      <div class="ticket-row"><span>سعر التفعيل</span><b class="num">${fmt(tk.entry)}</b></div>
      <div class="ticket-row"><span>🛡️ وقف الخسارة</span><b class="num" style="color:var(--red);">${fmt(tk.stop)}</b></div>
      <div class="ticket-row"><span>🎯 الهدف الأول</span><b class="num" style="color:var(--green);">${fmt(tk.t1)}</b></div>
      <div class="ticket-row"><span>🚀 الهدف الثاني</span><b class="num" style="color:var(--purple);">${fmt(tk.t2)}</b></div>
      <div class="ticket-row"><span>⚖️ العائد/المخاطرة</span><b class="num" style="color:var(--green);">${tk.rr}</b></div>
      <div class="caption">نفّذ من ثاندر كأمر معلق بهذه الأسعار — لا تطارد السعر خارج الخطة</div>`;
  }

  // الأخبار
  $("stockNews").innerHTML = d.news && d.news.length ? d.news.map(n => `
    <div class="news-item"><a class="t" href="${n.link}" target="_blank">${n.title}</a>
    <div class="m">${n.pub} • ${n.source || ""}</div></div>`).join("") : '<div class="loading">لا توجد أخبار حديثة</div>';
}

loadCandles();
loadStock();
setInterval(loadStock, 30000);   // السعر والاحتمال كل 30 ثانية
setInterval(loadCandles, 120000); // الشموع كل دقيقتين
