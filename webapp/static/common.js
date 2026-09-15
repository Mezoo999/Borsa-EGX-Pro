/* EGX Pro — عناصر مشتركة */
(function () {
  // شريط التنقل
  var nav = document.getElementById("nav");
  if (nav) {
    var pages = [
      { id: "market", href: "/", label: "🏠 السوق" },
      { id: "opportunities", href: "/opportunities", label: "💡 الفرص" },
      { id: "portfolio", href: "/portfolio", label: "💼 محفظتي" },
      { id: "watchlist", href: "/watchlist", label: "⭐ المتابعة" }
    ];
    var cur = nav.getAttribute("data-page") || "";
    nav.innerHTML = '<nav class="topnav">' +
      pages.map(function (p) {
        return '<a href="' + p.href + '" class="' + (cur === p.id ? "active" : "") + '">' + p.label + "</a>";
      }).join("") + "</nav>";
  }

  // الساعة + حالة السوق (لصفحات لا تملك هذا المنطق)
  function updateClock() {
    var clock = document.getElementById("clock");
    var chip = document.getElementById("statusChip");
    if (!clock && !chip) return;
    var now = new Date();
    if (clock) clock.textContent = now.toLocaleTimeString("ar-EG", { timeZone: "Africa/Cairo", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    if (chip) {
      try {
        var parts = new Intl.DateTimeFormat("en-US", { timeZone: "Africa/Cairo", weekday: "short", hour: "numeric", hour12: false }).formatToParts(now);
        var wd = parts.find(function (p) { return p.type === "weekday"; }).value;
        var h = parseInt(parts.find(function (p) { return p.type === "hour"; }).value);
        var open = !["Fri", "Sat"].includes(wd) && h >= 10 && h < 14.5;
        chip.textContent = open ? "🟢 السوق مفتوح" : "🔴 السوق مغلق";
        chip.className = "status-chip " + (open ? "status-open" : "status-closed");
      } catch (e) {}
    }
  }
  if (document.getElementById("clock") || document.getElementById("statusChip")) {
    updateClock();
    setInterval(updateClock, 1000);
  }

  // منتقي رمز سهم (بحث + قائمة)
  window.EGX = {
    attachPicker: function (input, drop, onPick) {
      if (!input || !drop) return;
      var t;
      input.addEventListener("input", function () {
        clearTimeout(t);
        t = setTimeout(async function () {
          var q = input.value.trim();
          if (!q) { drop.style.display = "none"; return; }
          try {
            var res = await fetch("/api/search?q=" + encodeURIComponent(q)).then(function (r) { return r.json(); });
            drop.innerHTML = res.map(function (r) {
              return '<a href="#" data-sym="' + r.symbol + '"><b>' + r.short + "</b> — " + r.name + "</a>";
            }).join("");
            drop.style.display = res.length ? "block" : "none";
          } catch (e) {}
        }, 250);
      });
      drop.addEventListener("click", function (e) {
        var a = e.target.closest("a");
        if (a) { e.preventDefault(); onPick(a.getAttribute("data-sym")); }
      });
      document.addEventListener("click", function (e) {
        var wrap = input.closest(".picker");
        if (wrap && !wrap.contains(e.target)) drop.style.display = "none";
      });
    }
  };
})();
