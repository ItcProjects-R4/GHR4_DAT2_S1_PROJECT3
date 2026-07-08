// =====================================================================
// برج التحكم - منطق الواجهة (Fetch + تفاعلات + حركة split-flap)
// =====================================================================

const state = { categories: null };

// ---------------------------------------------------------------------
// أدوات مساعدة
// ---------------------------------------------------------------------
function el(id) { return document.getElementById(id); }

function fillSelect(select, values, skipIndex) {
  select.innerHTML = "";
  values.forEach((v, i) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    select.appendChild(opt);
  });
  if (typeof skipIndex === "number" && values.length > skipIndex) {
    select.selectedIndex = skipIndex;
  }
}

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(data.error || `Server connection failed (${res.status})`);
  }
  return data;
}

// ---------------------------------------------------------------------
// شاشة الإقلاع (Boot sequence) - polling لحد ما الموديل يبقى جاهز
// ---------------------------------------------------------------------
async function bootSequence() {
  const bootScreen = el("boot-screen");
  const statusLine = el("boot-status-line");
  const app = el("app");

  while (true) {
    try {
      const status = await api("/api/status");
      statusLine.textContent = status.message || "Initializing...";
      if (status.ready) break;
      if (status.error) {
        showBootError(status.error);
        return;
      }
    } catch (e) {
      statusLine.textContent = "Unable to connect to the server. Retrying...";
    }
    await new Promise(r => setTimeout(r, 900));
  }

  bootScreen.style.display = "none";
  app.style.display = "block";
  await initApp();
}

function showBootError(message) {
  const bootScreen = el("boot-screen");
  bootScreen.innerHTML = `
    <div class="boot-plane">🛫</div>
    <div class="boot-error">❌ An error occurred while loading the data or model:\n\n${message}</div>
    <button class="btn secondary" style="width:auto;padding:10px 24px" onclick="location.reload()">Retry 🔄</button>
`;
}

// ---------------------------------------------------------------------
// تهيئة التطبيق بعد الجاهزية
// ---------------------------------------------------------------------
async function initApp() {
  const cats = await api("/api/categories");
  state.categories = cats;

  fillSelect(el("a-airline"), cats.airlines);
  fillSelect(el("a-day"), cats.days);
  fillSelect(el("a-dep"), cats.departures);
  fillSelect(el("a-arr"), cats.arrivals, 1);
  el("route-dep-code").textContent = el("a-dep").value;
  el("route-arr-code").textContent = el("a-arr").value;

  fillSelect(el("m-airline"), cats.airlines);
  fillSelect(el("m-day"), cats.days);
  fillSelect(el("m-dep"), cats.departures);
  fillSelect(el("m-arr"), cats.arrivals, 1);

  el("a-dep").addEventListener("change", () => el("route-dep-code").textContent = el("a-dep").value);
  el("a-arr").addEventListener("change", () => el("route-arr-code").textContent = el("a-arr").value);

  setupTabs();
  el("predict-auto-btn").addEventListener("click", predictAuto);
  el("predict-manual-btn").addEventListener("click", predictManual);
  el("retrain-btn").addEventListener("click", retrain);
}

// ---------------------------------------------------------------------
// تبويبات مع مؤشر منزلق (segmented control)
// ---------------------------------------------------------------------
function setupTabs() {
  const buttons = Array.from(document.querySelectorAll(".tab-btn"));
  const highlight = el("tab-highlight");

  function moveHighlight(btn) {
    highlight.style.width = btn.offsetWidth + "px";
    highlight.style.transform = `translateX(${btn.offsetLeft}px)`;
  }

  function activate(tabName, btn) {
    buttons.forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    el(`panel-${tabName}`).classList.add("active");
    moveHighlight(btn);
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => activate(btn.dataset.tab, btn));
  });

  // تفعيل أول تبويب بعد ما العرض يترسم فعلياً
  requestAnimationFrame(() => activate(buttons[0].dataset.tab, buttons[0]));
  window.addEventListener("resize", () => {
    const activeBtn = buttons.find(b => b.classList.contains("active"));
    if (activeBtn) moveHighlight(activeBtn);
  });
}

// ---------------------------------------------------------------------
// حركة split-flap لعرض النتيجة (اللحظة المميزة في التصميم)
// ---------------------------------------------------------------------
function flipWord(elm, newText, className) {
  elm.classList.remove("flip-word");
  void elm.offsetWidth; // إعادة تشغيل الحركة
  elm.textContent = newText;
  elm.className = "status-word flip-word " + className;
}

function flipDigits(container, text) {
  const chars = text.split("");
  container.innerHTML = "";
  chars.forEach((ch, i) => {
    const flap = document.createElement("div");
    flap.className = "flap";
    flap.textContent = ch;
    container.appendChild(flap);
    setTimeout(() => {
      flap.classList.add("flip");
    }, i * 60);
  });
}

const MATCH_LEVEL_LABELS = {
  "route+airline+day": "Very High Accuracy (Same Route + Airline + Day)",
  "route+day": "High Accuracy (Same Route & Day)",
  "route": "Medium Accuracy (General Route Data)",
  "airport_average": "Low Accuracy (Airport Average, Limited Historical Data)",

};

function renderResult(prefix, pred, proba, extraDetailsHtml) {
  const resultBox = el(prefix + "-result");
  const statusWord = el(prefix + "-status-word");
  const flapBoard = el(prefix + "-flap-board");
  const details = el(prefix + "-details");
  const errorBox = el(prefix + "-error");

  errorBox.classList.remove("show");
  resultBox.classList.add("show");

  const isDelayed = pred === 1;
  flipWord(statusWord, isDelayed ? "🔴 Delayed" : "🟢 On Time",
    isDelayed ? "delayed" : "ontime");
  flipDigits(flapBoard, (proba * 100).toFixed(1) + "%");
  details.innerHTML = extraDetailsHtml;
}

function renderError(prefix, message) {
  const resultBox = el(prefix + "-result");
  const errorBox = el(prefix + "-error");
  resultBox.classList.remove("show");
  errorBox.textContent = "❌ " + message;
  errorBox.classList.add("show");
}

// ---------------------------------------------------------------------
// تنبؤ تلقائي
// ---------------------------------------------------------------------
async function predictAuto() {
  const btn = el("predict-auto-btn");
  const payload = {
    airline: el("a-airline").value,
    dep: el("a-dep").value,
    arr: el("a-arr").value,
    day: el("a-day").value,
  };

  if (payload.dep === payload.arr) {
    renderError("a", "Please select a different arrival airport.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Predicting...";
  try {
    const data = await api("/api/predict/auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const est = data.estimated;
    const matchLabel = MATCH_LEVEL_LABELS[est.match_level] || "";
    const detailsHtml =
      `<strong>Data Accuracy:</strong> ${matchLabel}\n` +
      `(Similar historical flights: ${est.n_matches})\n\n` +
      `<strong>Automatically Estimated Details:</strong>\n` +
      `Departure Hour: ${est.dep_hour.toFixed(1)}\n` +
      `Departure Temperature: ${est.dep_temp_max.toFixed(1)}°\n` +
      `Departure Wind Speed: ${est.dep_wind_speed.toFixed(1)}\n` +
      `Arrival Temperature: ${est.arr_temp_max.toFixed(1)}°\n` +
      `Arrival Wind Speed: ${est.arr_wind_speed.toFixed(1)}`;
    renderResult("a", data.pred, data.proba, detailsHtml);
  } catch (e) {
    renderError("a", e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Predict Now 🚀";
  }
}

// ---------------------------------------------------------------------
// تنبؤ يدوي
// ---------------------------------------------------------------------
async function predictManual() {
  const btn = el("predict-manual-btn");
  const payload = {
    airline: el("m-airline").value,
    dep: el("m-dep").value,
    arr: el("m-arr").value,
    day: el("m-day").value,
    dep_hour: parseFloat(el("m-hour").value),
    dep_temp_max: parseFloat(el("m-dep-temp").value),
    dep_wind_speed: parseFloat(el("m-dep-wind").value),
    arr_temp_max: parseFloat(el("m-arr-temp").value),
    arr_wind_speed: parseFloat(el("m-arr-wind").value),
  };

  if (payload.dep === payload.arr) {
    renderError("m", "Please select a different arrival airport.");
    return;
  }
  if (Object.values(payload).some(v => typeof v === "number" && isNaN(v))) {
    renderError("m", "Please enter valid numbers in all weather and departure time fields.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Predicting..";
  try {
    const data = await api("/api/predict/manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderResult("m", data.pred, data.proba, "");
  } catch (e) {
    renderError("m", e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Predict Now 🚀";
  }
}

// ---------------------------------------------------------------------
// إعادة التدريب
// ---------------------------------------------------------------------
async function retrain() {
  const btn = el("retrain-btn");
  const progress = el("retrain-progress");
  const log = el("retrain-log");

  btn.disabled = true;
  progress.classList.add("show");
  log.textContent = "Starting model retraining...";

  try {
    await api("/api/retrain", { method: "POST" });

    while (true) {
      await new Promise(r => setTimeout(r, 1200));
      const status = await api("/api/retrain/status");
      log.textContent = status.log || "Training...";
      if (status.done) {
        if (status.error) {
          log.textContent = "❌ " + status.error;
        }
        break;
      }
    }
  } catch (e) {
    log.textContent = "❌ " + e.message;
  } finally {
    btn.disabled = false;
    progress.classList.remove("show");
  }
}

// ---------------------------------------------------------------------
// نقطة الدخول
// ---------------------------------------------------------------------
bootSequence();