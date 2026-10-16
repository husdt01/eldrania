/* Общее состояние и UI-утилиты: форматирование, модальные окна, тосты, частицы. */
const G = { cat: null, st: null, stAt: 0, screen: "home", filter: { fac: "all", cls: "all" }, summonCur: "tickets", modals: [] };

const UI = (() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (n) => Math.round(n).toLocaleString("ru-RU");
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  function dur(sec) {
    sec = Math.max(0, Math.floor(sec));
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
    if (h > 0) return h + "ч " + String(m).padStart(2, "0") + "м";
    if (m > 0) return m + "м " + String(s).padStart(2, "0") + "с";
    return s + "с";
  }

  function haptic(kind) {
    try {
      const h = tg && tg.HapticFeedback;
      if (!h) return;
      if (kind === "success" || kind === "error" || kind === "warning") h.notificationOccurred(kind);
      else h.impactOccurred(kind || "light");
    } catch (e) { /* нет haptic */ }
  }

  function toast(msg, kind) {
    const root = $("#toast-root");
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.textContent = msg;
    root.appendChild(el);
    setTimeout(() => { el.style.transition = "opacity .3s"; el.style.opacity = "0"; setTimeout(() => el.remove(), 320); }, 2600);
  }

  /* ---------- модальные окна ---------- */
  function syncBack() {
    if (!tg || !tg.BackButton) return;
    try {
      if (G.modals.length) { tg.BackButton.show(); } else { tg.BackButton.hide(); }
    } catch (e) { /* старая версия клиента */ }
  }

  function modal(html, opts) {
    opts = opts || {};
    const root = $("#modal-root");
    const ov = document.createElement("div");
    ov.className = "overlay" + (opts.mid ? " mid" : "");
    ov.innerHTML = '<div class="sheet' + (opts.mid ? " center-sheet" : "") + '"><button class="close" data-act="close-modal" aria-label="Закрыть">×</button><div class="mbody">' + html + "</div></div>";
    ov.addEventListener("click", (e) => { if (e.target === ov) close(ov); });
    root.appendChild(ov);
    ov._onClose = opts.onClose;
    G.modals.push(ov);
    syncBack();
    return ov;
  }
  function setModal(ov, html) { const b = ov.querySelector(".mbody"); const top = ov.querySelector(".sheet").scrollTop; b.innerHTML = html; ov.querySelector(".sheet").scrollTop = top; }
  function close(ov) {
    ov = ov || G.modals[G.modals.length - 1];
    if (!ov) return;
    G.modals = G.modals.filter((m) => m !== ov);
    ov.remove();
    syncBack();
    if (ov._onClose) ov._onClose();
  }
  function closeAll() { while (G.modals.length) close(); }
  if (tg && tg.BackButton) { try { tg.BackButton.onClick(() => close()); } catch (e) { /* ignore */ } }

  /* ---------- фоновые частицы (угольки) ---------- */
  const fxc = { cvs: null, ctx: null, parts: [], w: 0, h: 0, run: true };
  function initFx() {
    const c = $("#fx"); if (!c) return;
    fxc.cvs = c; fxc.ctx = c.getContext("2d");
    const resize = () => { const d = Math.min(window.devicePixelRatio || 1, 2); fxc.w = c.width = innerWidth * d; fxc.h = c.height = innerHeight * d; fxc.d = d; };
    resize(); addEventListener("resize", resize);
    const count = innerWidth < 500 ? 34 : 60;
    for (let i = 0; i < count; i++) fxc.parts.push(spawn(true));
    document.addEventListener("visibilitychange", () => { fxc.run = !document.hidden; if (fxc.run) loop(); });
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches) loop();
  }
  function spawn(init) {
    const teal = Math.random() < 0.55;
    return { x: Math.random() * fxc.w, y: init ? Math.random() * fxc.h : fxc.h + 10, r: (Math.random() * 1.8 + 0.6) * (fxc.d || 1),
      vy: -(Math.random() * 0.35 + 0.12) * (fxc.d || 1), vx: (Math.random() - 0.5) * 0.2, a: Math.random() * 0.5 + 0.2, t: Math.random() * 6, col: teal ? "63,224,208" : "232,196,123" };
  }
  function loop() {
    if (!fxc.run) return;
    const { ctx } = fxc; ctx.clearRect(0, 0, fxc.w, fxc.h);
    fxc.parts.forEach((p, i) => {
      p.t += 0.02; p.x += p.vx + Math.sin(p.t) * 0.15; p.y += p.vy;
      if (p.y < -10) fxc.parts[i] = spawn(false);
      ctx.beginPath(); ctx.fillStyle = "rgba(" + p.col + "," + (p.a * (0.6 + 0.4 * Math.sin(p.t * 2))) + ")";
      ctx.shadowColor = "rgba(" + p.col + ",.8)"; ctx.shadowBlur = 8; ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
    });
    requestAnimationFrame(loop);
  }

  function flash() { const f = document.createElement("div"); f.className = "flash"; document.body.appendChild(f); setTimeout(() => f.remove(), 950); }

  return { $, esc, fmt, sleep, clamp, dur, haptic, toast, modal, setModal, close, closeAll, initFx, flash, tg };
})();
