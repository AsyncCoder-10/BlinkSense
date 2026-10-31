const $ = id => document.getElementById(id);
const faaa = new Audio("/static/faaa.mp3");
let last = "Focused", hist = [];

function playFaaa() { faaa.currentTime = 0; faaa.play().catch(() => {}); }

function beep(freq, ms) {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const o = ctx.createOscillator();
  o.frequency.value = freq; o.connect(ctx.destination);
  o.start(); setTimeout(() => { o.stop(); ctx.close(); }, ms);
}

const clamp = (v, m) => Math.max(-m, Math.min(m, v));
const setDot = (id, v, max) => $(id).style.left = (50 + clamp(v, max) / max * 50) + "%";

function headText(s) {
  if (!s.face) return "No face detected";
  const p = [];
  if (s.yaw > 12) p.push("turned right"); else if (s.yaw < -12) p.push("turned left");
  if (s.pitch > 12) p.push("looking down"); else if (s.pitch < -12) p.push("looking up");
  if (Math.abs(s.roll) > 12) p.push("tilted");
  return p.length ? p.join(", ") : "facing screen";
}

function drawChart() {
  const c = $("chart"), g = c.getContext("2d"), W = c.width, H = c.height;
  g.clearRect(0, 0, W, H);
  g.strokeStyle = "#dbeafe"; g.lineWidth = 1;
  [0, .5, 1].forEach(f => { g.beginPath(); g.moveTo(0, H * f); g.lineTo(W, H * f); g.stroke(); });
  if (hist.length < 2) return;
  const grad = g.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, "rgba(37,99,235,.35)"); grad.addColorStop(1, "rgba(37,99,235,0)");
  g.beginPath();
  hist.forEach((v, i) => {
    const x = i / 119 * W, y = H - v / 100 * H;
    i ? g.lineTo(x, y) : g.moveTo(x, y);
  });
  g.strokeStyle = "#2563eb"; g.lineWidth = 2.5; g.stroke();
  g.lineTo((hist.length - 1) / 119 * W, H); g.lineTo(0, H); g.fillStyle = grad; g.fill();
}

async function poll() {
  try {
    const s = await (await fetch("/api/status")).json();
    $("badge").textContent = s.state; $("badge").className = "badge " + s.state;
    $("score").textContent = s.score; $("ring").style.setProperty("--p", s.score);
    $("streak").textContent = s.streak_s; $("best").textContent = s.best_streak_min;
    $("dis").textContent = s.distracted_pct; $("dro").textContent = s.drowsy_pct;
    $("blinks").textContent = s.blinks; $("gaze").textContent = s.gaze;

    $("yv").textContent = s.yaw + "°"; $("pv").textContent = s.pitch + "°"; $("rv").textContent = s.roll + "°";
    setDot("yd", s.yaw, 45); setDot("pd", s.pitch, 45); setDot("rd", s.roll, 45);
    setHead(s.yaw, s.pitch, s.roll, s.face);
    $("htxt").textContent = headText(s);

    if (s.state !== last) {
      if (s.state === "Drowsy") beep(900, 600);
      if (s.state === "Distracted") playFaaa();
      last = s.state;
    }
  } catch (e) {}
}
setInterval(poll, 250);
setInterval(async () => {                       // chart: one point per second
  try { hist.push((await (await fetch("/api/status")).json()).score); } catch (e) {}
  if (hist.length > 120) hist.shift();
  drawChart();
}, 1000);

async function resetAll() { await fetch("/api/reset", { method: "POST" }); hist = []; drawChart(); }
async function getCoach() {
  $("coach").textContent = "Thinking...";
  try { $("coach").textContent = (await (await fetch("/api/feedback")).json()).feedback; }
  catch (e) { $("coach").textContent = "Coach unavailable. Check HF_TOKEN in .env."; }
}