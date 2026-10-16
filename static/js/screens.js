/* Отрисовка экранов и модальных окон. Только представление: все данные берутся из G.st (ответы сервера). */
const Screens = (() => {
  const { esc, fmt } = UI;
  const st = () => G.st;
  const owned = (key) => st().heroes.find((h) => h.key === key);
  const costRow = (items) => '<span class="cost">' + items.map((i) => Art.coin(i[0], i[1], i[2])).join("") + "</span>";
  const statNames = { hp: "ЗДР", atk: "АТК", def: "ЗАЩ", spd: "СКР" };

  /* ============================================================ ГЛАВНАЯ */
  function goal() {
    const s = st(), p = s.player, idle = liveIdle();
    const ready = s.quests.some((q) => !q.claimed && q.progress >= q.target);
    const filled = s.squad.slots.filter(Boolean).length;
    if (p.tickets >= 1 && s.heroes.length < 8) return { t: "Призовите новых героев", s: "У вас " + p.tickets + " бил. призыва — расширьте коллекцию", act: 'data-act="nav" data-to="summon"', ic: "summon" };
    if (filled < 5 && s.heroes.length >= 5) return { t: "Заполните отряд", s: "Сейчас героев в отряде: " + filled + " из 5", act: 'data-act="nav" data-to="squad"', ic: "squad" };
    if (idle.seconds >= 600) return { t: "Заберите накопленные награды", s: "Вас не было " + UI.dur(idle.seconds), act: 'data-act="claim-idle"', ic: "clock" };
    const weak = s.squad.slots.filter(Boolean).map(owned).filter((h) => h && h.level_cost && p.gold >= h.level_cost.gold && p.exp >= h.level_cost.exp).sort((a, b) => a.level - b.level)[0];
    if (weak) return { t: "Усильте героя: " + Art.hero(weak.key).name.split(" ")[0], s: "Хватает золота и опыта на повышение уровня", act: 'data-act="open-hero" data-key="' + weak.key + '"', ic: "up" };
    if (ready) return { t: "Задания выполнены", s: "Заберите ежедневные награды", act: 'data-act="quests"', ic: "quest" };
    return { t: "Пройдите этап " + s.campaign.view.stage, s: "Откройте новые главы и получите самоцветы", act: 'data-act="fight"', ic: "power" };
  }

  function liveIdle() {
    const b = st().idle, extra = (Date.now() - G.stAt) / 1000;
    const sec = Math.min(b.seconds + extra, b.cap_seconds), h = sec / 3600;
    return { seconds: sec, cap: b.cap_seconds, gold: Math.floor(b.rates.gold * h), exp: Math.floor(b.rates.exp * h), gems: Math.floor(b.rates.gems * h), rates: b.rates };
  }

  function home() {
    const s = st(), v = s.campaign.view, ch = G.cat.chapters[v.chapter - 1], idle = liveIdle();
    const mine = s.squad.power, ratio = v.enemy_power ? mine / v.enemy_power : 2;
    const verdict = ratio >= 1.15 ? ["good", "Преимущество"] : ratio >= 0.85 ? ["mid", "Равный бой"] : ["bad", "Опасно"];
    const rw = v.rewards, g = goal();
    const chips = [["gold", rw.gold], ["exp", rw.exp], ["gems", rw.gems], ["tickets", rw.tickets]].filter((x) => x[1] > 0)
      .map((x) => '<span class="chip">' + Art.icon(x[0], 15) + UI.fmt(x[1]) + "</span>").join("");
    const strip = s.squad.slots.map((k) => k ? Art.card(Art.hero(k), { mini: true, level: owned(k).level, stars: owned(k).stars }) : '<div class="slot-empty">+</div>').join("");
    const readyQ = s.quests.some((q) => !q.claimed && q.progress >= q.target);
    return '<section class="home">' +
      '<div class="scene" style="--c1:' + ch.c1 + ";--c2:" + ch.c2 + '">' + sceneSky(ch) +
      '<div class="eyebrow">Глава ' + v.chapter + "</div><h2>" + esc(ch.name) + '</h2><div class="stage-line">Этап ' + v.sub + " из 10 · №" + v.stage + (v.boss ? '<span class="boss">БОСС</span>' : "") + (s.campaign.finished ? '<span class="chip txt">Кампания пройдена</span>' : "") + "</div>" +
      '<div class="foes">' + v.enemies.map(Art.enemyMini).join("") + "</div>" +
      '<div class="cmp"><div class="lbl"><span>Ваша сила <b>' + fmt(mine) + "</b></span><span class=\"verdict " + verdict[0] + '">' + verdict[1] + "</span><span>Враги <b>" + fmt(v.enemy_power) + '</b></span></div><div class="bar ' + (ratio >= 1 ? "" : "violet") + '"><i style="width:' + UI.clamp(ratio * 50, 4, 100) + '%"></i></div></div>' +
      '<div class="cta"><button class="btn big" data-act="fight">Сражение</button><div class="rewards">' + chips + "</div>" +
      '<button class="btn ghost sm" data-act="map">' + Art.icon("map", 16) + " Карта кампании</button></div></div>" +
      '<div class="panel goal" ' + g.act + '><div class="gi">' + Art.icon(g.ic, 22) + '</div><div><div class="gt">' + esc(g.t) + '</div><div class="gs">' + esc(g.s) + "</div></div></div>" +
      '<div class="panel" data-act="nav" data-to="squad" style="cursor:pointer"><div class="row" style="margin-bottom:8px"><h3 style="margin:0">Ваш отряд</h3><span class="sp"></span><span class="chip txt">' + Art.icon("power", 14, "#ffd36b") + " " + fmt(mine) + '</span></div><div class="strip">' + strip + "</div></div>" +
      '<div class="panel idle-box"><div class="row"><h3 style="margin:0">Награды за отсутствие</h3><span class="sp"></span><span class="chip txt" id="idle-time">' + UI.dur(idle.seconds) + '</span></div>' +
      '<div class="idle-grid"><span class="chip">' + Art.icon("gold", 16) + '<span id="idle-gold">' + fmt(idle.gold) + '</span></span><span class="chip">' + Art.icon("exp", 16) + '<span id="idle-exp">' + fmt(idle.exp) + '</span></span><span class="chip">' + Art.icon("gems", 16) + '<span id="idle-gems">' + fmt(idle.gems) + "</span></span></div>" +
      '<div class="bar gold"><i id="idle-bar" style="width:' + (idle.seconds / idle.cap) * 100 + '%"></i></div><div class="small muted" style="margin:6px 0 10px">Копится до ' + G.cat.idle_cap_hours + " ч · доход: " + fmt(idle.rates.gold) + " золота/ч</div>" +
      '<button class="btn block" data-act="claim-idle">Забрать награды</button></div>' +
      '<div class="modes">' +
      '<button class="mode" data-act="quests">' + Art.icon("quest", 30) + "Задания" + (readyQ ? '<i class="dot"></i>' : "") + "</button>" +
      '<button class="mode" data-act="nav" data-to="shop">' + Art.icon("gift", 30) + "Дар дня" + (s.gift_ready ? '<i class="dot"></i>' : "") + "</button>" +
      '<button class="mode" data-act="map">' + Art.icon("map", 30) + "Карта</button>" +
      '<button class="mode lock" data-act="soon">' + Art.icon("tower", 30) + "Башня<small>Скоро</small></button>" +
      '<button class="mode lock" data-act="soon">' + Art.icon("arena", 30) + "Арена<small>Скоро</small></button>" +
      '<button class="mode lock" data-act="soon">' + Art.icon("guild", 30) + "Гильдия<small>Скоро</small></button></div></section>";
  }

  function sceneSky(ch) {
    return '<svg class="sky" viewBox="0 0 400 330" preserveAspectRatio="xMidYMax slice"><circle cx="320" cy="70" r="30" fill="' + ch.accent + '" opacity=".35"/><circle cx="320" cy="70" r="20" fill="' + Art.lighten(ch.accent, 0.5) + '" opacity=".5"/>' +
      '<path d="M0 330V250l30-10 20-40 20 40 30 6 25-60 25 60 35-10 30-30 30 30 40 8 25-50 25 50 35-12 30-34 25 34 25 6V330z" fill="#05041a" opacity=".6"/>' +
      '<path d="M0 330V285l60-14 50-24 60 22 70-16 60 12 50-20 50 18V330z" fill="#05041a" opacity=".85"/></svg>';
  }

  /* ============================================================ ГЕРОИ */
  function filters() {
    const f = G.filter;
    const facs = '<button class="tab ' + (f.fac === "all" ? "on" : "") + '" data-act="filter" data-k="fac" data-v="all">Все фракции</button>' +
      Object.entries(G.cat.factions).map(([k, v]) => '<button class="tab ' + (f.fac === k ? "on" : "") + '" data-act="filter" data-k="fac" data-v="' + k + '" style="' + (f.fac === k ? "" : "color:" + v.color) + '">' + Art.sigil(k, 14) + v.short + "</button>").join("");
    const cls = '<button class="tab ' + (f.cls === "all" ? "on" : "") + '" data-act="filter" data-k="cls" data-v="all">Все классы</button>' +
      Object.entries(G.cat.classes).map(([k, v]) => '<button class="tab ' + (f.cls === k ? "on" : "") + '" data-act="filter" data-k="cls" data-v="' + k + '">' + Art.clsIcon(k, 14) + v.name + "</button>").join("");
    return '<div class="tab-row">' + facs + '</div><div class="tab-row">' + cls + "</div>";
  }

  function heroes() {
    const s = st(), f = G.filter;
    const pass = (t) => (f.fac === "all" || t.faction === f.fac) && (f.cls === "all" || t.cls === f.cls);
    const mine = s.heroes.filter((h) => pass(Art.hero(h.key))).sort((a, b) => b.power - a.power);
    const locked = G.cat.heroes.filter((t) => pass(t) && !owned(t.key));
    const grid = mine.map((h) => Art.card(Art.hero(h.key), { level: h.level, stars: h.stars, attrs: 'data-act="open-hero" data-key="' + h.key + '"', tag: s.squad.slots.includes(h.key) ? "ОТРЯД" : "" })).join("") +
      locked.map((t) => Art.card(t, { locked: true, attrs: 'data-act="open-hero" data-key="' + t.key + '"' })).join("");
    return '<section><div class="row" style="margin-bottom:6px"><h2 style="font-size:20px">Герои</h2><span class="sp"></span><span class="chip txt">Собрано ' + s.heroes.length + " / " + G.cat.heroes.length + "</span></div>" + filters() +
      (grid ? '<div class="hgrid">' + grid + "</div>" : '<div class="empty"><h3>Никого не найдено</h3>Измените фильтры или призовите новых героев.</div>') +
      (s.heroes.length === 0 ? '<div class="empty"><h3>Коллекция пуста</h3><button class="btn" data-act="nav" data-to="summon">К призыву</button></div>' : "") + "</section>";
  }

  function heroBody(key) {
    const t = Art.hero(key), hv = owned(key), p = st().player, r = Art.rar(t.rarity), f = Art.fac(t.faction);
    let h = '<div class="hero-top" style="--rc:' + r.color + '">' + Art.card(t, { level: hv && hv.level, stars: hv ? hv.stars : 0, locked: !hv }) +
      '<div class="hero-info"><h2>' + esc(t.name) + '</h2><div class="small muted" style="margin-bottom:6px">' + esc(t.title) + '</div><span class="rtag">' + r.name + '</span>' +
      '<div class="kv"><span class="muted">Фракция</span><span style="color:' + f.color + '">' + esc(f.name) + '</span><span class="muted">Класс</span><span>' + G.cat.classes[t.cls].name + "</span>" +
      (hv ? '<span class="muted">Уровень</span><span>' + hv.level + " / " + hv.cap + '</span><span class="muted">Сила</span><span style="color:var(--gold-l)">' + fmt(hv.power) + "</span>" : "") + "</div></div></div>" +
      '<p class="small muted" style="margin:0 0 4px;line-height:1.45">' + esc(t.desc) + "</p>";
    if (hv) {
      h += '<div class="sec">Характеристики</div>';
      ["hp", "atk", "def", "spd"].forEach((k) => {
        const cur = hv.stats[k], nx = hv.next_stats ? hv.next_stats[k] : null;
        h += '<div class="stat"><span class="muted">' + statNames[k] + '</span><span class="v">' + fmt(cur) + '</span><span class="nx">' + (nx !== null && nx > cur ? "→ " + fmt(nx) + " (+" + fmt(nx - cur) + ")" : "") + "</span></div>";
      });
      h += '<div class="stat"><span class="muted">КРИТ</span><span class="v">' + Math.round(hv.stats.crit * 100) + '%</span><span></span></div>';
    }
    h += '<div class="sec">Способности</div>' +
      '<div class="skill"><div class="si">' + Art.icon("warrior", 20) + "</div><div><b>" + esc(t.basic.name) + '</b> <span class="muted small">· обычная</span><p>' + esc(t.basic.desc) + "</p></div></div>" +
      '<div class="skill ult"><div class="si">' + Art.icon("ult", 20) + "</div><div><b>" + esc(t.ult.name) + '</b> <span class="muted small">· ультимейт (100 энергии)</span><p>' + esc(t.ult.desc) + "</p></div></div>";
    if (!hv) return h + '<div class="empty small">Герой ещё не получен.</div><button class="btn block" data-act="nav" data-to="summon">Призвать героев</button>';

    // прокачка уровня
    const lc = hv.level_cost, canLv = lc && p.gold >= lc.gold && p.exp >= lc.exp;
    h += '<div class="sec">Прокачка</div><div class="panel" style="margin:0"><div class="row"><span class="muted small">Ваш опыт: ' + fmt(p.exp) + " · золото: " + fmt(p.gold) + "</span></div>";
    if (lc) {
      h += '<div class="row" style="margin-top:8px"><button class="btn sp ' + (canLv ? "" : "off") + '" data-act="levelup" data-key="' + key + '" data-times="1">Повысить ' + costRow([["gold", lc.gold, p.gold < lc.gold], ["exp", lc.exp, p.exp < lc.exp]]) + '</button><button class="btn ghost ' + (canLv ? "" : "off") + '" data-act="levelup" data-key="' + key + '" data-times="5">×5</button></div>';
      if (!canLv) h += '<div class="small" style="color:var(--danger);margin-top:6px">Не хватает ' + [p.gold < lc.gold ? fmt(lc.gold - p.gold) + " золота" : "", p.exp < lc.exp ? fmt(lc.exp - p.exp) + " опыта" : ""].filter(Boolean).join(" и ") + ". Заберите idle-награды или пройдите бой.</div>";
    } else h += '<div class="small muted" style="margin-top:8px">Достигнут предел уровня для этого количества звёзд. Повысьте звёзды фрагментами.</div>';
    h += "</div>";

    // звёзды
    h += '<div class="sec">Звёзды и фрагменты</div><div class="panel" style="margin:0"><div class="row"><span class="stars" style="font-size:18px">' + Art.stars(hv.stars) + '</span><span class="sp"></span>' + (hv.star_cost ? '<span class="small">' + Art.icon("shards", 14) + " " + hv.shards + " / " + hv.star_cost.shards + "</span>" : '<span class="small muted">Максимум</span>') + "</div>";
    if (hv.star_cost) {
      const ok = hv.shards >= hv.star_cost.shards && p.gold >= hv.star_cost.gold;
      h += '<div class="bar violet" style="margin:8px 0"><i style="width:' + UI.clamp((hv.shards / hv.star_cost.shards) * 100, 0, 100) + '%"></i></div><button class="btn violet block ' + (ok ? "" : "off") + '" data-act="star" data-key="' + key + '">Повысить звезду ' + costRow([["gold", hv.star_cost.gold, p.gold < hv.star_cost.gold]]) + "</button>" +
        '<div class="small muted" style="margin-top:6px">Фрагменты выпадают при повторном призыве героя. +15% к характеристикам и +8 к пределу уровня за звезду.</div>';
    }
    h += "</div>";

    // экипировка
    h += '<div class="sec">Экипировка</div><div class="equip">';
    G.cat.equip_slots && Object.keys(G.cat.equip_slots).forEach((slot) => {
      const nm = slot === "relic" ? G.cat.equip_names.relic[t.faction] : G.cat.equip_names[slot][t.cls];
      const lvl = hv.eq[slot], nx = hv.equip_next[slot], can = nx && p.gold >= nx.cost;
      h += '<div class="eq"><div class="ei">' + Art.icon(slot === "weapon" ? "warrior" : slot === "armor" ? "tank" : "ult", 22) + '</div><div class="en">' + esc(nm) + '</div><div class="el">Ур. ' + lvl + " / " + G.cat.equip_max + '</div><div class="small muted" style="font-size:10.5px">' + G.cat.equip_slots[slot].desc + "</div>" +
        (nx ? '<button class="btn sm block ' + (can ? "" : "off") + '" data-act="equip" data-key="' + key + '" data-slot="' + slot + '">' + costRow([["gold", nx.cost, p.gold < nx.cost]]) + "</button>" : '<div class="small muted">Макс.</div>') + "</div>";
    });
    return h + "</div>";
  }

  /* ============================================================ ОТРЯД */
  function squad() {
    const s = st();
    const cells = s.squad.slots.map((k, i) => {
      const lab = i < 2 ? "Передний ряд" : i < 3 ? "Центр" : "Тыл";
      const inner = k ? Art.card(Art.hero(k), { level: owned(k).level, stars: owned(k).stars, attrs: 'data-act="pick-slot" data-slot="' + i + '"' }) : '<div class="slot-empty" data-act="pick-slot" data-slot="' + i + '">+</div>';
      return '<div class="cell"><div class="lab">' + lab + "</div>" + inner + "</div>";
    }).join("");
    const bonus = s.squad.bonuses.map((b) => {
      const f = Art.fac(b.faction);
      return '<div class="bonus" style="--fc:' + f.color + '"><span style="color:' + f.color + '">' + Art.sigil(b.faction, 18) + "</span><span><b>" + f.short + " ×" + b.count + "</b> — +" + Math.round(b.hp * 100) + "% ЗДР" + (b.atk ? ", +" + Math.round(b.atk * 100) + "% АТК" : "") + "</span></div>";
    }).join("");
    return '<section><div class="row"><h2 style="font-size:20px">Отряд</h2><span class="sp"></span><button class="btn ghost sm" data-act="auto-squad">Авто-сбор</button></div>' +
      '<div class="panel" style="margin-top:10px"><div class="power"><div>' + Art.icon("power", 28, "#ffd36b") + '</div><div><div class="eyebrow">Сила отряда</div><div class="pv">' + fmt(s.squad.power) + "</div></div></div></div>" +
      '<div class="formation">' + cells + "</div>" +
      '<div class="panel"><h3>Бонусы фракций</h3>' + (bonus || '<div class="small muted">Поставьте в отряд 2+ героев одной фракции: 2 — +5% ЗДР, 3 — +10% ЗДР и +5% АТК, 4 — +15%/+10%, 5 — +25%/+15%.</div>') + "</div>" +
      '<div class="small muted center">Передний ряд принимает основные удары: ставьте туда танков.</div></section>';
  }

  function pickerBody(slot) {
    const s = st(), cur = s.squad.slots[slot];
    const list = s.heroes.slice().sort((a, b) => b.power - a.power);
    return "<h2>Слот " + (slot + 1) + "</h2>" + (cur ? '<button class="btn ghost sm" data-act="clear-slot" data-slot="' + slot + '" style="margin-bottom:10px">Убрать героя из слота</button>' : "") +
      '<div class="hgrid">' + list.map((h) => Art.card(Art.hero(h.key), { level: h.level, stars: h.stars, sel: h.key === cur, tag: s.squad.slots.includes(h.key) && h.key !== cur ? "СЛОТ " + (s.squad.slots.indexOf(h.key) + 1) : "", attrs: 'data-act="set-slot" data-slot="' + slot + '" data-key="' + h.key + '"' })).join("") + "</div>";
  }

  /* ============================================================ ПРИЗЫВ */
  function summon() {
    const s = st(), sm = G.cat.summon, p = s.player, cur = G.summonCur;
    const c1 = cur === "tickets" ? sm.cost.tickets : sm.cost.gems, c10 = cur === "tickets" ? sm.cost.tickets * 10 : sm.x10_gems;
    const have = p[cur], ico = cur === "tickets" ? "tickets" : "gems";
    const pe = s.summon.pity_epic, pl = s.summon.pity_legend;
    return '<section><h2 style="font-size:20px;margin-bottom:10px">Призыв</h2>' +
      '<div class="portal"><div class="rune"></div><div class="rune r2"></div><div class="orb"></div></div>' +
      '<div class="cur-toggle"><button class="tab ' + (cur === "tickets" ? "on" : "") + '" data-act="cur" data-v="tickets">' + Art.icon("tickets", 16) + " Билеты: " + p.tickets + '</button><button class="tab ' + (cur === "gems" ? "on" : "") + '" data-act="cur" data-v="gems">' + Art.icon("gems", 16) + " Самоцветы: " + fmt(p.gems) + "</button></div>" +
      '<div class="sum-btns"><button class="btn teal ' + (have >= c1 ? "" : "off") + '" data-act="summon" data-n="1"><span class="t">Призыв ×1</span>' + costRow([[ico, c1, have < c1]]) + '</button><button class="btn ' + (have >= c10 ? "" : "off") + '" data-act="summon" data-n="10"><span class="t">Призыв ×10</span>' + costRow([[ico, c10, have < c10]]) + "</button></div>" +
      (have < c1 ? '<div class="small center" style="color:var(--danger);margin-top:8px">Не хватает ресурсов. Забирайте idle-награды и проходите кампанию — билеты и самоцветы выдаются за этапы и задания.</div>' : "") +
      '<div class="panel pity" style="margin-top:14px"><h3>Гарантии</h3>' +
      '<div class="row"><span>Эпический или выше</span><span class="sp"></span><b>' + pe + " / " + sm.pity_epic + '</b></div><div class="bar violet"><i style="width:' + (pe / sm.pity_epic) * 100 + '%"></i></div>' +
      '<div class="row" style="margin-top:10px"><span>Легендарный</span><span class="sp"></span><b>' + pl + " / " + sm.pity_legend + '</b></div><div class="bar gold"><i style="width:' + (pl / sm.pity_legend) * 100 + '%"></i></div>' +
      '<div class="small muted" style="margin-top:8px">Счётчики сбрасываются при выпадении. Повтор героя даёт фрагменты для звёзд.</div></div>' +
      '<button class="btn ghost block" data-act="rates">Вероятности призыва</button></section>';
  }

  function ratesBody() {
    const sm = G.cat.summon, now = st().summon.rates;
    const pct = (v) => (v * 100).toFixed(2).replace(/\.?0+$/, "") + "%";
    const rows = ["legendary", "epic", "rare", "common"].map((k) => {
      const r = Art.rar(k), n = G.cat.heroes.filter((h) => h.rarity === k).length;
      return '<div class="rate-row" style="--rc:' + r.color + ";--rg:" + r.glow + '"><span class="dotc"></span><span style="color:' + r.color + '">' + r.name + '</span><span class="sp"></span><span class="small muted" style="font-weight:500">' + n + ' героев</span><span style="min-width:62px;text-align:right">' + pct(sm.rates[k]) + "</span></div>";
    }).join("");
    return "<h2>Вероятности</h2>" + rows +
      '<div class="small muted" style="margin:12px 0;line-height:1.5">Результат призыва определяет только сервер. Внутри редкости герой выбирается равновероятно.<br>• Каждый ' + sm.pity_epic + "-й призыв без эпика гарантированно даёт эпического или легендарного героя.<br>• Начиная с " + (sm.soft_start + 1) + "-го призыва без легендарного его шанс растёт на " + Math.round(sm.soft_step * 100) + "% за каждый призыв; на " + sm.pity_legend + "-м — гарантия.</div>" +
      '<div class="panel" style="margin:0"><h3>Шансы следующего призыва</h3>' + ["legendary", "epic", "rare", "common"].map((k) => '<div class="row small"><span style="color:' + Art.rar(k).color + '">' + Art.rar(k).name + '</span><span class="sp"></span><b>' + pct(now[k]) + "</b></div>").join("") + "</div>" +
      '<div class="small muted" style="margin-top:10px">Призывы оплачиваются только игровыми билетами и самоцветами, заработанными в игре. Платных розыгрышей нет.</div>';
  }

  function summonFx(results) {
    return new Promise((resolve) => {
      const order = { common: 0, rare: 1, epic: 2, legendary: 3 };
      const best = results.reduce((a, r) => (order[r.rarity] > order[a] ? r.rarity : a), "common");
      const br = Art.rar(best);
      const ov = document.createElement("div");
      ov.className = "summon-fx";
      ov.innerHTML = '<div class="stage"><div class="vortex" style="--vc:' + br.color + ";--vg:" + br.glow + '"><div class="ring"></div><div class="ring"></div><div class="core"></div></div><div class="eyebrow">Врата открываются…</div></div>';
      document.body.appendChild(ov);
      UI.haptic("medium");
      let skipAll = false;
      setTimeout(() => {
        const one = results.length === 1;
        const tag = (r) => (r.new ? "НОВЫЙ" : "+" + r.shards + " ФР.");
        const cardOf = (r) => Art.card(Art.hero(r.key), { tag: tag(r), level: 1 });
        ov.innerHTML = '<div class="stage">' + (one ? '<div class="big-reveal">' + cardOf(results[0]) + '</div><div><h2 style="text-align:center">' + esc(Art.hero(results[0].key).name) + '</h2><div class="res-line" style="color:' + Art.rar(results[0].rarity).color + '">' + Art.rar(results[0].rarity).name + "</div></div>"
          : '<div class="rgrid">' + results.map((r, i) => '<div class="rcard" data-i="' + i + '"><div class="in"><div class="back"><i></i></div><div class="face">' + cardOf(r) + "</div></div></div>").join("") + '</div><div class="res-line" id="sfx-line">Касайтесь карт или ждите</div>') +
          '<div class="btns" style="display:flex;gap:8px;width:100%"><button class="btn ghost sp" id="sfx-skip">Показать все</button><button class="btn sp" id="sfx-done" style="display:none">Готово</button></div></div>';
        if (one) { if (results[0].rarity === "legendary") UI.flash(); UI.haptic(results[0].rarity === "legendary" ? "success" : "medium"); ov.querySelector("#sfx-skip").style.display = "none"; ov.querySelector("#sfx-done").style.display = ""; }
        else reveal();
        ov.querySelector("#sfx-done").onclick = () => { ov.remove(); resolve(); };
        ov.querySelector("#sfx-skip").onclick = () => { skipAll = true; ov.querySelectorAll(".rcard").forEach((c) => c.classList.add("flip")); finish(); };
      }, 1150);
      async function reveal() {
        const cards = [...ov.querySelectorAll(".rcard")];
        for (let i = 0; i < cards.length; i++) {
          if (skipAll) return;
          await UI.sleep(i === 0 ? 300 : 260);
          if (skipAll) return;
          const r = results[i], c = cards[i];
          c.classList.add("flip");
          if (r.rarity === "epic") { c.classList.add("glow-e"); UI.haptic("light"); }
          if (r.rarity === "legendary") { c.classList.add("glow-l"); UI.flash(); UI.haptic("success"); await UI.sleep(500); }
        }
        finish();
      }
      function finish() {
        const nw = results.filter((r) => r.new).length, sh = results.reduce((a, r) => a + r.shards, 0);
        const line = ov.querySelector("#sfx-line");
        if (line) line.textContent = "Новых героев: " + nw + " · фрагментов: " + sh;
        const sk = ov.querySelector("#sfx-skip"), dn = ov.querySelector("#sfx-done");
        if (sk) sk.style.display = "none";
        if (dn) dn.style.display = "";
      }
    });
  }

  /* ============================================================ МАГАЗИН */
  function shop() {
    const s = st(), p = s.player;
    const sect = { free: "Бесплатно", tickets: "Билеты призыва", gold: "Золото", supplies: "Расходные материалы", cosmetic: "Косметика", premium: "Премиум-наборы" };
    const iconOf = { free: "gift", tickets: "tickets", gold: "gold", supplies: "exp", cosmetic: "star", premium: "gems" };
    let h = '<section><h2 style="font-size:20px;margin-bottom:10px">Магазин</h2><div class="notice">Тестовый режим: оплата реальными деньгами и Telegram Stars отключена. Покупки за самоцветы используют только внутриигровую валюту.</div>';
    Object.keys(sect).forEach((cat) => {
      const items = G.cat.shop.filter((i) => i.cat === cat);
      if (!items.length) return;
      h += '<div class="sec">' + sect[cat] + '</div><div class="shop-grid">' + items.map((i) => {
        let btn;
        if (i.kind === "premium") btn = '<button class="btn ghost sm off" disabled>' + Art.icon("lock", 14) + " Недоступно</button>";
        else if (i.kind === "free") btn = '<button class="btn sm ' + (s.gift_ready ? "" : "off") + '" data-act="buy" data-id="' + i.id + '">' + (s.gift_ready ? "Забрать" : "Завтра") + "</button>";
        else if (i.frame) {
          const has = p.cosmetics.includes(i.frame);
          btn = has ? '<button class="btn ghost sm ' + (p.frame === i.frame ? "off" : "") + '" data-act="frame" data-frame="' + i.frame + '">' + (p.frame === i.frame ? "Надето" : "Надеть") + "</button>"
            : '<button class="btn sm ' + (p.gems >= i.price ? "" : "off") + '" data-act="buy" data-id="' + i.id + '">' + costRow([["gems", i.price, p.gems < i.price]]) + "</button>";
        } else btn = '<button class="btn sm ' + (p.gems >= i.price ? "" : "off") + '" data-act="buy" data-id="' + i.id + '">' + costRow([["gems", i.price, p.gems < i.price]]) + "</button>";
        return '<div class="item ' + (i.kind === "premium" ? "off" : "") + '"><div class="ic">' + Art.icon(iconOf[cat], 30) + "</div><b>" + esc(i.name) + "</b><p>" + esc(i.desc) + "</p>" + btn + "</div>";
      }).join("") + "</div>";
    });
    return h + "</section>";
  }

  /* ============================================================ ЗАДАНИЯ / КАРТА */
  function questsBody() {
    const rewardChips = (r) => Object.entries(r).map(([k, v]) => '<span class="chip">' + Art.icon(k, 14) + fmt(v) + "</span>").join("");
    return "<h2>Ежедневные задания</h2>" + st().quests.map((q) => {
      const done = q.progress >= q.target;
      return '<div class="quest"><div class="qb"><div class="qn">' + esc(q.name) + '</div><div class="bar"><i style="width:' + (q.progress / q.target) * 100 + '%"></i></div><div class="row small muted"><span>' + q.progress + " / " + q.target + '</span><span class="sp"></span>' + rewardChips(q.reward) + "</div></div>" +
        (q.claimed ? '<span class="chip txt" style="color:var(--ok)">Получено</span>' : '<button class="btn sm ' + (done ? "" : "off") + '" data-act="claim-quest" data-id="' + q.id + '">Забрать</button>') + "</div>";
    }).join("") + '<div class="small muted center">Задания обновляются каждый день в 00:00 UTC.</div>';
  }

  function mapBody() {
    const c = st().campaign, chIdx = G.mapCh == null ? Math.floor((c.next - 1) / 10) : G.mapCh, ch = G.cat.chapters[chIdx];
    const tabs = G.cat.chapters.map((x, i) => '<button class="tab ' + (i === chIdx ? "on" : "") + '" data-act="map-ch" data-i="' + i + '">' + x.id + "</button>").join("");
    let nodes = "";
    for (let i = 1; i <= 10; i++) {
      const n = chIdx * 10 + i, cls = n <= c.cleared ? "done" : n === c.cleared + 1 ? "cur" : "lock";
      nodes += '<button class="snode ' + cls + (i === 10 ? " boss" : "") + '" ' + (cls === "lock" ? "" : 'data-act="stage" data-n="' + n + '"') + ">" + (cls === "done" ? Art.icon("check", 18) : i) + "<small>" + (i === 10 ? "босс" : n) + "</small></button>";
    }
    return "<h2>Карта кампании</h2><div class=\"tab-row\">" + tabs + '</div><div class="eyebrow">Глава ' + ch.id + '</div><h3 style="color:' + ch.accent + '">' + esc(ch.name) + '</h3><div class="small muted">' + esc(ch.desc) + " Босс: " + esc(ch.boss.name) + '.</div><div class="stage-grid">' + nodes + "</div>";
  }

  function stageBody(v) {
    const ch = G.cat.chapters[v.chapter - 1], mine = st().squad.power, rw = v.rewards;
    const chips = [["gold", rw.gold], ["exp", rw.exp], ["gems", rw.gems], ["tickets", rw.tickets]].filter((x) => x[1] > 0).map((x) => '<span class="chip">' + Art.icon(x[0], 15) + fmt(x[1]) + "</span>").join("");
    return "<h2>" + esc(ch.name) + " · " + v.sub + (v.boss ? " (босс)" : "") + '</h2><div class="foes">' + v.enemies.map(Art.enemyMini).join("") + '</div><div class="row small" style="justify-content:space-between;margin-bottom:8px"><span>Ваша сила: <b>' + fmt(mine) + "</b></span><span>Враги: <b>" + fmt(v.enemy_power) + "</b></span></div>" +
      '<div class="eyebrow" style="margin-bottom:6px">' + (rw.gems || rw.tickets ? "Награда за первое прохождение" : "Награда за победу") + '</div><div class="rewards" style="justify-content:flex-start;margin-bottom:14px">' + chips + '</div><div class="small muted" style="margin-bottom:10px">Побед на этапе: ' + v.clears + '</div><button class="btn big block" data-act="fight-stage" data-n="' + v.stage + '">Сражение</button>';
  }

  return { home, heroes, heroBody, squad, pickerBody, summon, ratesBody, summonFx, shop, questsBody, mapBody, stageBody, liveIdle };
})();
