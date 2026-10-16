/* Ядро приложения: инициализация, Telegram, навигация, действия игрока. Состояние хранится только на сервере. */
const App = (() => {
  const $ = UI.$, tg = UI.tg;
  const NAV = [["home", "Кампания", "home"], ["heroes", "Герои", "heroes"], ["squad", "Отряд", "squad"], ["summon", "Призыв", "summon"], ["shop", "Магазин", "shop"]];
  const M = { hero: null, quests: null, map: null };
  let ticker = null, fighting = false, prevRes = null;

  /* ---------------------------------------------------------------- Telegram */
  function setupTelegram() {
    if (!tg) return;
    try {
      tg.ready(); tg.expand();
      if (tg.disableVerticalSwipes) tg.disableVerticalSwipes();
      if (tg.setHeaderColor) tg.setHeaderColor("#06051a");
      if (tg.setBackgroundColor) tg.setBackgroundColor("#06051a");
      if (tg.setBottomBarColor) tg.setBottomBarColor("#06051a");
    } catch (e) { /* старые клиенты */ }
    const apply = () => {
      const r = document.documentElement.style;
      r.setProperty("--app-h", (tg.viewportStableHeight || window.innerHeight) + "px");
      const a = tg.safeAreaInset || {}, c = tg.contentSafeAreaInset || {};
      r.setProperty("--tg-top", ((a.top || 0) + (c.top || 0)) + "px");
      r.setProperty("--tg-bottom", (a.bottom || 0) + "px");
    };
    apply();
    ["viewportChanged", "safeAreaChanged", "contentSafeAreaChanged"].forEach((ev) => { try { tg.onEvent(ev, apply); } catch (e) { /* нет события */ } });
  }

  /* ---------------------------------------------------------------- состояние и отрисовка */
  function setState(s) { G.st = s; G.stAt = Date.now(); renderTop(); renderNav(); }

  function renderTop() {
    const p = G.st.player, pct = UI.clamp((p.xp / p.xp_next) * 100, 0, 100);
    const pill = (k, v) => '<div class="pill" data-res="' + k + '">' + Art.icon(k, 20) + "<span>" + UI.fmt(v) + "</span></div>";
    $("#topbar").innerHTML = '<div class="me"><div class="avatar f-' + p.frame + '">' + UI.esc((p.name || "?").trim().charAt(0).toUpperCase()) + '<span class="lvl">' + p.level + '</span></div><div style="min-width:0"><div class="me-name">' + UI.esc(p.name) + '</div><div class="xpbar"><i style="width:' + pct + '%"></i></div></div></div>' +
      '<div class="pills">' + pill("gold", p.gold) + pill("gems", p.gems) + pill("tickets", p.tickets) + "</div>";
    if (prevRes) ["gold", "gems", "tickets"].forEach((k) => { if (prevRes[k] !== p[k]) { const e = $('[data-res="' + k + '"]'); if (e) e.classList.add("bump"); } });
    prevRes = { gold: p.gold, gems: p.gems, tickets: p.tickets };
  }

  function renderNav() {
    const s = G.st, idle = Screens.liveIdle();
    const dots = { home: idle.seconds >= 600 || s.gift_ready || s.quests.some((q) => !q.claimed && q.progress >= q.target), summon: s.player.tickets >= 1 };
    $("#nav").innerHTML = NAV.map((n) => '<button class="nav-btn ' + (G.screen === n[0] ? "on" : "") + '" data-act="nav" data-to="' + n[0] + '">' + Art.icon(n[2], 26) + "<span>" + n[1] + "</span>" + (dots[n[0]] && G.screen !== n[0] ? '<i class="dot"></i>' : "") + "</button>").join("");
  }

  function render(resetScroll) {
    const scr = $("#screen"), top = scr.scrollTop;
    scr.innerHTML = Screens[G.screen]();
    scr.scrollTop = resetScroll ? 0 : top;
    renderNav();
    clearInterval(ticker);
    if (G.screen === "home") ticker = setInterval(tick, 1000);
  }

  function tick() {
    const e = $("#idle-time"); if (!e) return;
    const i = Screens.liveIdle();
    e.textContent = UI.dur(i.seconds);
    $("#idle-gold").textContent = UI.fmt(i.gold); $("#idle-exp").textContent = UI.fmt(i.exp); $("#idle-gems").textContent = UI.fmt(i.gems);
    $("#idle-bar").style.width = (i.seconds / i.cap) * 100 + "%";
  }

  function refreshOpen() {
    if (M.hero && G.heroKey) UI.setModal(M.hero, Screens.heroBody(G.heroKey));
    if (M.quests) UI.setModal(M.quests, Screens.questsBody());
    if (M.map) UI.setModal(M.map, Screens.mapBody());
  }
  function commit(state) { setState(state); render(); refreshOpen(); }

  function go(to) { UI.closeAll(); G.screen = to; render(true); renderNav(); }

  function handleErr(err) {
    if (err && (err.code === "unauthorized" || err.code === "session_expired" || err.code === "server_misconfigured")) return fatal(err);
    UI.toast(err && err.message ? err.message : "Что-то пошло не так.", "err");
    UI.haptic("error");
    if (err && ["conflict", "db_busy"].includes(err.code)) silentRefresh();
  }
  async function silentRefresh() { try { commit(await Api.get("/state")); } catch (e) { /* ignore */ } }

  function fatal(err) {
    const b = $("#boot");
    b.classList.remove("hide");
    const auth = err && ["unauthorized", "session_expired", "server_misconfigured"].includes(err.code);
    b.innerHTML = "<h1>Эльдрания</h1><div class=\"sub\">Сумрачные Врата</div><p style=\"max-width:300px;line-height:1.5\">" + UI.esc(err && err.message ? err.message : "Не удалось загрузить игру.") + "</p>" +
      (auth ? '<p class="small muted" style="max-width:300px">Игра работает как Telegram Mini App. Откройте её из бота. Для локальной проверки включите DEV_MODE=1 на сервере.</p>' : "") +
      '<button class="btn" data-act="retry-boot">Повторить</button>';
  }

  /* ---------------------------------------------------------------- действия */
  const rewardText = (r) => Object.entries(r).filter((x) => x[1] > 0).map(([k, v]) => ({ gold: "золото", exp: "опыт", gems: "самоцветы", tickets: "билеты" }[k] ? "+" + UI.fmt(v) + " " + { gold: "золота", exp: "опыта", gems: "самоцветов", tickets: "бил." }[k] : "")).join(", ");

  async function startBattle(stage) {
    if (fighting) return;
    fighting = true;
    try {
      const res = await Api.post("/battle", { stage, request_id: Api.uuid() });
      UI.closeAll();
      Object.keys(M).forEach((k) => { M[k] = null; });
      const meta = { chapter: Math.ceil(stage / 10), sub: ((stage - 1) % 10) + 1 };
      const act = await Battle.play(res, meta);
      commit(res.state);
      fighting = false;
      if (act === "next") return startBattle(stage + 1);
      if (act === "retry") return startBattle(stage);
      if (act === "heroes") go("heroes");
    } catch (e) { handleErr(e); }
    finally { fighting = false; }
  }

  const Actions = {
    "nav": (d) => go(d.to),
    "close-modal": () => UI.close(),
    "retry-boot": () => boot(),
    "soon": () => UI.toast("Этот режим появится в одном из следующих обновлений."),
    "filter": (d) => { G.filter[d.k] = d.v; render(); },
    "cur": (d) => { G.summonCur = d.v; render(); },

    "claim-idle": async () => {
      const r = await Api.post("/idle/claim");
      commit(r.state); UI.haptic("success");
      UI.toast("Получено: " + rewardText(r.claimed), "ok");
    },
    "fight": () => startBattle(G.st.campaign.next),
    "fight-stage": (d) => startBattle(+d.n),
    "map": () => { G.mapCh = null; M.map = UI.modal(Screens.mapBody(), { onClose: () => { M.map = null; } }); },
    "map-ch": (d) => { G.mapCh = +d.i; UI.setModal(M.map, Screens.mapBody()); },
    "stage": async (d) => { const v = await Api.get("/stage/" + d.n); UI.modal(Screens.stageBody(v)); },
    "quests": () => { M.quests = UI.modal(Screens.questsBody(), { onClose: () => { M.quests = null; } }); },
    "claim-quest": async (d) => { const r = await Api.post("/quests/" + d.id + "/claim"); commit(r.state); UI.haptic("success"); UI.toast("Награда: " + rewardText(r.reward), "ok"); },

    "open-hero": (d) => { G.heroKey = d.key; M.hero = UI.modal(Screens.heroBody(d.key), { onClose: () => { M.hero = null; G.heroKey = null; } }); },
    "levelup": async (d) => {
      const r = await Api.post("/heroes/" + d.key + "/levelup", { times: +d.times });
      commit(r.state); UI.haptic("success"); UI.toast("Уровень повышен: " + r.level, "ok");
    },
    "equip": async (d) => { const r = await Api.post("/heroes/" + d.key + "/equip", { slot: d.slot }); commit(r.state); UI.haptic("success"); UI.toast("Предмет улучшен до ур. " + r.level, "ok"); },
    "star": async (d) => { const r = await Api.post("/heroes/" + d.key + "/star"); commit(r.state); UI.haptic("success"); UI.flash(); UI.toast("Звёзд: " + r.stars, "ok"); },

    "pick-slot": (d) => { UI.modal(Screens.pickerBody(+d.slot), {}); },
    "set-slot": async (d) => {
      const slots = G.st.squad.slots.slice(), slot = +d.slot, j = slots.indexOf(d.key);
      if (j === slot) return UI.close();
      if (j >= 0) slots[j] = slots[slot];
      slots[slot] = d.key;
      const r = await Api.put("/squad", { slots }); UI.close(); commit(r.state); UI.haptic("light");
    },
    "clear-slot": async (d) => { const slots = G.st.squad.slots.slice(); slots[+d.slot] = null; const r = await Api.put("/squad", { slots }); UI.close(); commit(r.state); },
    "auto-squad": async () => {
      const top = G.st.heroes.slice().sort((a, b) => b.power - a.power).slice(0, 5).map((h) => h.key);
      while (top.length < 5) top.push(null);
      const r = await Api.put("/squad", { slots: top }); commit(r.state); UI.toast("Отряд собран из сильнейших героев.", "ok");
    },

    "summon": async (d) => {
      const n = +d.n, cur = G.summonCur;
      const r = await Api.post("/summon", { count: n, currency: cur, request_id: Api.uuid() });
      UI.closeAll();
      await Screens.summonFx(r.results);
      commit(r.state);
    },
    "rates": () => { UI.modal(Screens.ratesBody()); },

    "buy": async (d) => {
      const r = await Api.post("/shop/buy", { item_id: d.id });
      commit(r.state); UI.haptic("success"); UI.toast(r.gave ? "Получено: " + rewardText(r.gave) : "Покупка выполнена.", "ok");
    },
    "frame": async (d) => { const r = await Api.post("/cosmetics/frame", { frame: d.frame }); commit(r.state); },
  };

  document.addEventListener("click", async (e) => {
    const el = e.target.closest("[data-act]");
    if (!el) return;
    if (el.classList.contains("off") || el.disabled) { if (el.dataset.act !== "nav") UI.toast("Недостаточно ресурсов или действие недоступно."); return; }
    const fn = Actions[el.dataset.act];
    if (!fn || el.classList.contains("loading")) return;
    el.classList.add("loading");
    try { await fn(el.dataset, el); } catch (err) { handleErr(err); } finally { el.classList.remove("loading"); }
  });

  /* ---------------------------------------------------------------- запуск */
  async function boot() {
    const b = $("#boot");
    b.classList.remove("hide");
    b.innerHTML = '<h1>Эльдрания</h1><div class="sub">Сумрачные Врата</div><div class="spinner"></div>';
    try {
      if (!G.cat) { G.cat = await Api.get("/catalog"); Art.index(); }
      setState(await Api.get("/state"));
      render(true);
      b.classList.add("hide");
      if (G.cat.dev_mode && !Api.hasTelegram) UI.toast("Тестовый режим (DEV_MODE): вход без Telegram.");
    } catch (e) { fatal(e); }
  }

  function init() {
    setupTelegram();
    UI.initFx();
    document.addEventListener("visibilitychange", () => { if (!document.hidden && G.st && !fighting) silentRefresh(); });
    boot();
  }
  return { init, boot };
})();

App.init();
