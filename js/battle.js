/* Проигрыватель боя. Весь исход рассчитан сервером; здесь только воспроизведение лога. */
const Battle = (() => {
  const BADGE = { shield: ["Щ", "#3fe0d0"], burn: ["О", "#ff9d4a"], stun: ["С", "#ffe066"], atk_up: ["↑", "#ff6b86"], def_up: ["+", "#6aa8ff"], def_down: ["−", "#b57bff"] };
  const getSpeed = () => { try { return +localStorage.getItem("eld_speed") || 1; } catch (e) { return 1; } };
  const setSpeed = (v) => { try { localStorage.setItem("eld_speed", v); } catch (e) { /* ignore */ } };

  function play(resp, meta) {
    return new Promise((resolve) => {
      const root = UI.$("#battle-root");
      const ch = G.cat.chapters[(meta.chapter || 1) - 1];
      const units = {};
      resp.units.forEach((u) => { units[u.id] = u; });
      let speed = getSpeed(), skipped = false, done = false;

      const unitHtml = (u) => {
        const r = u.mon ? { color: "#8a7aa8", glow: "#c0455a" } : Art.rar(u.rarity);
        return '<div class="bu ' + (u.side === "a" ? "ally" : "foe") + (u.boss ? " boss" : "") + '" id="u-' + u.id + '" style="--rc:' + r.color + ";--rg:" + r.glow + '">' +
          '<div class="face">' + Art.unitFace(u) + '<span class="lv">Ур.' + u.level + '</span><div class="st"></div></div>' +
          '<div class="hp"><u style="width:100%"></u><i style="width:100%"></i></div><div class="en"><i></i></div><div class="nm">' + UI.esc(u.name.split(" ")[0]) + "</div></div>";
      };
      const row = (side) => {
        const list = resp.units.filter((u) => u.side === side);
        let h = list.map(unitHtml).join("");
        for (let i = list.length; i < 5; i++) h += "<div></div>";
        return h;
      };

      root.innerHTML = '<div class="battle" style="--c1:' + ch.c1 + ";--c2:" + ch.c2 + '">' +
        '<div class="b-top"><div class="t">Глава ' + meta.chapter + " · Этап " + meta.sub + '</div><button class="btn ghost" id="b-speed">×' + speed + '</button><button class="btn ghost" id="b-skip">Пропустить</button></div>' +
        '<div class="b-field"><div class="b-row" id="b-foes">' + row("b") + '</div><div class="b-mid"><div class="b-round" id="b-round">Бой</div><div class="b-banner" id="b-banner"></div></div><div class="b-row" id="b-allies">' + row("a") + "</div></div></div>";
      const bt = root.querySelector(".battle");
      const el = (id) => root.querySelector("#u-" + id);
      const wait = (ms) => (skipped ? Promise.resolve() : UI.sleep(ms / speed));

      root.querySelector("#b-speed").onclick = () => { speed = speed === 1 ? 2 : speed === 2 ? 3 : 1; setSpeed(speed); root.querySelector("#b-speed").textContent = "×" + speed; };
      root.querySelector("#b-skip").onclick = () => { skipped = true; };

      function applyState(st) {
        for (const id in st) {
          const u = units[id], e = el(id), s = st[id];
          if (!e) continue;
          const pct = UI.clamp((s[0] / u.maxhp) * 100, 0, 100);
          e.querySelector(".hp i").style.width = pct + "%";
          e.querySelector(".hp u").style.width = UI.clamp(((s[0] + s[2]) / u.maxhp) * 100, 0, 100) + "%";
          e.querySelector(".en i").style.width = s[1] + "%";
          e.classList.toggle("dead", s[0] <= 0);
          e.querySelector(".st").innerHTML = s[0] > 0 ? s[3].map((t) => BADGE[t] ? '<b style="background:' + BADGE[t][1] + '">' + BADGE[t][0] + "</b>" : "").join("") : "";
        }
      }
      function float(id, text, cls) {
        if (skipped) return;
        const e = el(id); if (!e) return;
        const n = document.createElement("div");
        n.className = "fnum " + cls; n.textContent = text; n.style.marginLeft = (Math.random() * 24 - 12) + "px";
        e.appendChild(n); setTimeout(() => n.remove(), 1000);
      }
      function hitFx(id) {
        if (skipped) return;
        const e = el(id); if (!e) return;
        e.classList.remove("hit"); void e.offsetWidth; e.classList.add("hit");
        const s = document.createElement("div"); s.className = "slash"; e.querySelector(".face").appendChild(s); setTimeout(() => s.remove(), 320);
        setTimeout(() => e.classList.remove("hit"), 400);
      }
      async function banner(text) {
        const b = root.querySelector("#b-banner"); b.textContent = text; b.classList.add("on");
        bt.classList.add("ultfx"); UI.haptic("medium");
        await wait(650);
        b.classList.remove("on"); bt.classList.remove("ultfx");
      }

      async function run() {
        await wait(700);
        for (const ev of resp.log) {
          if (done) return;
          if (ev.k === "round") { root.querySelector("#b-round").textContent = "Раунд " + ev.n; await wait(250); }
          else if (ev.k === "dot") { float(ev.id, "−" + ev.d, "dot"); applyState(ev.st); await wait(320); }
          else if (ev.k === "stun") { float(ev.id, "Оглушён", "abs"); applyState(ev.st); await wait(380); }
          else if (ev.k === "act") {
            const a = el(ev.a), ult = ev.sk === "ult";
            if (ult) { a.classList.add("glow"); await banner(ev.n); }
            const dmgT = ev.tg.filter((t) => t.d !== undefined);
            if (!skipped && dmgT.length === 1 && !ult) {
              const t = el(dmgT[0].id);
              if (t) { const ar = a.getBoundingClientRect(), tr = t.getBoundingClientRect(); a.style.setProperty("--dx", (tr.left - ar.left) * 0.4 + "px"); a.style.setProperty("--dy", (tr.top - ar.top) * 0.45 + "px"); }
            } else { a.style.setProperty("--dx", "0px"); a.style.setProperty("--dy", "0px"); }
            a.classList.add("acting");
            await wait(260);
            for (const t of ev.tg) {
              if (t.d !== undefined) {
                hitFx(t.id);
                if (t.a) float(t.id, "щит −" + t.a, "abs");
                if (t.d > 0 || !t.a) float(t.id, (t.c ? "★" : "") + "−" + t.d, t.c ? "crit" : "dmg");
              }
              if (t.h) float(t.id, "+" + t.h, "heal");
            }
            ev.fx.forEach((f) => { if (f.t === "resist") float(f.id, "Иммунитет", "abs"); });
            applyState(ev.st);
            UI.haptic("light");
            await wait(420);
            a.classList.remove("acting", "glow");
          }
        }
        const end = resp.log[resp.log.length - 1];
        applyState(end.st);
        await wait(700);
        showResult();
      }

      function showResult() {
        if (done) return;
        const r = resp.result, rw = r.rewards;
        const chips = [["gold", rw.gold], ["exp", rw.exp], ["gems", rw.gems], ["tickets", rw.tickets]].filter((x) => x[1] > 0)
          .map((x) => '<span class="chip">' + Art.icon(x[0], 16) + "+" + UI.fmt(x[1]) + "</span>").join("");
        const s = G.st.campaign;
        const hasNext = r.win && r.first_clear && r.stage < s.max_stage;
        const div = document.createElement("div");
        div.className = "b-result";
        div.innerHTML = '<div class="res-card ' + (r.win ? "win" : "lose") + '"><div class="eyebrow">' + (r.win ? (r.first_clear ? "Этап пройден впервые" : "Повторное прохождение") : "Раундов: " + r.rounds) + "</div>" +
          "<h2>" + (r.win ? "ПОБЕДА" : "ПОРАЖЕНИЕ") + "</h2>" +
          (r.win ? '<div class="rewards">' + chips + "</div>" + (r.reduced ? '<div class="small muted">Дневной лимит повторных наград: награда снижена.</div>' : "") + (r.first_clear ? '<div class="small" style="color:var(--ok)">Открыт следующий этап кампании</div>' : "")
            : '<p class="muted small" style="margin:12px 0">Отряд слабее врагов. Улучшите героев, оденьте экипировку или соберите сочетание фракций.</p>') +
          '<div class="btns">' +
          (hasNext ? '<button class="btn block" data-b="next">Следующий этап</button>' : "") +
          (r.win ? '<button class="btn ' + (hasNext ? "ghost" : "") + ' block" data-b="retry">Повторить бой</button>' : '<button class="btn block" data-b="heroes">Усилить героев</button><button class="btn ghost block" data-b="retry">Попробовать снова</button>') +
          '<button class="btn ghost block" data-b="close">Продолжить</button></div></div>';
        bt.appendChild(div);
        if (r.win) { UI.haptic("success"); UI.flash(); } else UI.haptic("error");
        div.addEventListener("click", (e) => {
          const b = e.target.closest("[data-b]"); if (!b) return;
          done = true; root.innerHTML = ""; resolve(b.dataset.b);
        });
      }
      applyState(resp.log[0] && resp.log[0].st ? resp.log[0].st : {});
      run();
    });
  }
  return { play };
})();
