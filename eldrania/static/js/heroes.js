/* Визуальный слой: процедурные SVG-портреты, иконки, символы фракций, карточки героев.
   Чтобы использовать настоящие арты, положите файл static/assets/heroes/<key>.webp (или .png/.jpg):
   сервер сам отдаст portrait_url в каталоге, и логика игры менять не нужно. */
const Art = (() => {
  let uid = 0;
  let HI = null;

  const hexToRgb = (h) => { h = h.replace("#", ""); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  const toHex = (a) => "#" + a.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
  const mix = (a, b, t) => { const x = hexToRgb(a), y = hexToRgb(b); return toHex(x.map((v, i) => v + (y[i] - v) * t)); };
  const lighten = (c, t) => mix(c, "#ffffff", t);
  const darken = (c, t) => mix(c, "#000000", t);
  const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };

  function index() { HI = {}; G.cat.heroes.forEach((h) => { HI[h.key] = h; }); }
  const hero = (key) => (HI || (index(), HI))[key];
  const rar = (k) => G.cat.rarities[k];
  const fac = (k) => G.cat.factions[k] || { name: "Порча", short: "Порча", color: "#c0455a", color2: "#2a0f1f" };

  /* ------------------------------------------------ иконки */
  const FILL = {
    gold: '<circle cx="12" cy="12" r="9.5" fill="#f2c46a" stroke="#8a5f1c" stroke-width="1.5"/><circle cx="12" cy="12" r="6" fill="none" stroke="#b8873a" stroke-width="1.3"/><path d="M12 8l3 4-3 4-3-4z" fill="#b8873a"/>',
    gems: '<path d="M12 2.5l7.5 6.5L12 21.5 4.5 9z" fill="#4fe3ff" stroke="#0b5a7a" stroke-width="1.3" stroke-linejoin="round"/><path d="M4.5 9h15M12 2.5L9 9l3 12.5L15 9z" fill="none" stroke="#fff" stroke-opacity=".65" stroke-width="1"/>',
    tickets: '<path d="M3 8a2 2 0 012-2h14a2 2 0 012 2v2a2 2 0 000 4v2a2 2 0 01-2 2H5a2 2 0 01-2-2v-2a2 2 0 000-4z" fill="#c78bff" stroke="#4a1fb0" stroke-width="1.3"/><path d="M12 8.2l1.2 2.6 2.8.4-2 2 .5 2.8-2.5-1.3-2.5 1.3.5-2.8-2-2 2.8-.4z" fill="#fff" fill-opacity=".9"/>',
    exp: '<path d="M5 4h11a3 3 0 013 3v13H8a3 3 0 01-3-3z" fill="#5ad1ff" stroke="#0b4f78" stroke-width="1.3" stroke-linejoin="round"/><path d="M12 8l1 2.2 2.4.3-1.8 1.6.5 2.4-2.1-1.2-2.1 1.2.5-2.4-1.8-1.6 2.4-.3z" fill="#fff"/>',
    shards: '<path d="M12 2l4.5 7.5L12 22 7.5 9.5z" fill="#ff6fa8" stroke="#8a1a4a" stroke-width="1.3" stroke-linejoin="round"/><path d="M7.5 9.5h9" stroke="#fff" stroke-opacity=".6"/>',
    star: '<path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.7 7L12 17.2 5.7 21l1.7-7L2 9.2l7.1-.6z" fill="#f2c46a"/>',
  };
  const STROKE = {
    home: '<path d="M4 20V9l3-2v3h2V6l3-3 3 3v4h2V7l3 2v11zM10 20v-5a2 2 0 014 0v5"/>',
    heroes: '<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z"/><circle cx="12" cy="10" r="2.2"/><path d="M8.5 16.5c.8-2 2-3 3.5-3s2.7 1 3.5 3"/>',
    squad: '<path d="M5 21V4M5 5h12l-2.5 4L17 13H5"/>',
    summon: '<circle cx="12" cy="12" r="8.5"/><path d="M12 6.5l1.6 3.9L17.5 12l-3.9 1.6L12 17.5l-1.6-3.9L6.5 12l3.9-1.6z"/>',
    shop: '<path d="M5 8h14l-1 12H6zM9 8V6a3 3 0 016 0v2"/>',
    quest: '<path d="M7 4h10a2 2 0 012 2v12a2 2 0 01-2 2H7zM7 4a2 2 0 00-2 2v12a2 2 0 002 2M10 9h6M10 13h6"/>',
    map: '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2zM9 4v14M15 6v14"/>',
    lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
    gift: '<rect x="4" y="9" width="16" height="11" rx="1"/><path d="M12 9v11M4 13h16M12 9c-3 0-5-4-2-4s2 4 2 4zm0 0c3 0 5-4 2-4s-2 4-2 4z"/>',
    tower: '<path d="M7 21V9L5 7V3h3v2h2V3h4v2h2V3h3v4l-2 2v12zM11 21v-4h2v4"/>',
    arena: '<path d="M5 19L17 7M14 4h5v5M19 19L7 7M10 4H5v5"/>',
    guild: '<path d="M6 3h12v10l-6 5-6-5zM12 18v3"/>',
    warrior: '<path d="M5 19L18 6M14 6h4v4M4 16l4 4M7 13l4 4"/>',
    tank: '<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z"/>',
    mage: '<circle cx="12" cy="9" r="4"/><path d="M12 13v8M9 21h6M10 7.5l4 3"/>',
    marksman: '<path d="M6 3c8 3 8 15 0 18M6 3v18M6 12h14M16 8l4 4-4 4"/>',
    support: '<path d="M12 20s-7-4.5-7-10a4 4 0 017-2.5A4 4 0 0119 10c0 5.5-7 10-7 10zM12 9v5M9.5 11.5h5"/>',
    ult: '<path d="M12 2l2.5 6.5L21 9l-5 4.5 1.5 7.5-5.5-4-5.5 4L8 13.5 3 9l6.5-.5z"/>',
    up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    power: '<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>',
  };
  function icon(name, size, color) {
    size = size || 18;
    if (FILL[name]) return '<svg viewBox="0 0 24 24" width="' + size + '" height="' + size + '">' + FILL[name] + "</svg>";
    return '<svg viewBox="0 0 24 24" width="' + size + '" height="' + size + '" fill="none" stroke="' + (color || "currentColor") + '" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + (STROKE[name] || "") + "</svg>";
  }
  const clsIcon = (cls, size) => icon(cls, size || 14);

  const SIGIL = {
    dawn: '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    grove: '<path d="M5 19C5 9 12 4 20 4c0 8-5 15-15 15zM5 19L14 10"/>',
    ember: '<path d="M12 3c1 4 5 5 5 10a5 5 0 01-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 1-9z"/>',
    tide: '<path d="M3 11c3-4 5-4 8 0s5 4 10-2M3 17c3-4 5-4 8 0s5 4 10-2"/>',
    dusk: '<path d="M16 3a9 9 0 100 18 7 7 0 010-18z"/>',
    void: '<path d="M12 5C6 5 3 12 3 12s3 7 9 7 9-7 9-7-3-7-9-7zM12 9a3 3 0 100 6 3 3 0 000-6z"/>',
  };
  function sigil(f, size, color) {
    return '<svg viewBox="0 0 24 24" width="' + (size || 16) + '" height="' + (size || 16) + '" fill="none" stroke="' + (color || "currentColor") + '" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">' + (SIGIL[f] || SIGIL.void) + "</svg>";
  }

  /* ------------------------------------------------ портреты героев */
  function heroSvg(h) {
    const id = "p" + (++uid), f = fac(h.faction), lk = h.look || {}, c = f.color, c2 = f.color2, r = rar(h.rarity);
    const skin = lk.skin || "#d9a77c", hair = lk.hair || "#553", style = lk.style || 0, extra = lk.extra;
    const body = darken(c2, 0.15);
    let s = '<svg viewBox="0 0 100 132" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">';
    s += '<defs><radialGradient id="g' + id + '" cx="50%" cy="36%" r="80%"><stop offset="0" stop-color="' + c + '" stop-opacity=".6"/><stop offset=".5" stop-color="' + c2 + '"/><stop offset="1" stop-color="#05041a"/></radialGradient>' +
      '<radialGradient id="a' + id + '" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="' + r.glow + '" stop-opacity=".7"/><stop offset="1" stop-color="' + r.glow + '" stop-opacity="0"/></radialGradient>' +
      '<linearGradient id="b' + id + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + lighten(body, 0.1) + '"/><stop offset="1" stop-color="' + darken(body, 0.5) + '"/></linearGradient></defs>';
    s += '<rect width="100" height="132" fill="url(#g' + id + ')"/>';
    s += '<g transform="translate(13 8) scale(3.1)" opacity=".13" fill="none" stroke="' + c + '" stroke-width="1.2" stroke-linecap="round">' + (SIGIL[h.faction] || "") + "</g>";
    if (h.rarity === "epic" || h.rarity === "legendary") s += '<circle cx="50" cy="54" r="46" fill="url(#a' + id + ')"/>';
    if (h.rarity === "legendary") {
      s += '<g fill="#fff" opacity=".85"><path d="M14 22l1.2 3 3 1.2-3 1.2L14 30.4l-1.2-3-3-1.2 3-1.2z"/><path d="M86 40l1 2.4 2.4 1-2.4 1L86 47l-1-2.6-2.4-1 2.4-1z"/><path d="M80 12l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></g>';
    }
    // задний план по классу
    if (h.cls === "warrior") s += '<g transform="rotate(20 78 70)"><rect x="75" y="30" width="6" height="64" rx="2" fill="#d5deee"/><rect x="69" y="84" width="18" height="5" rx="2" fill="' + c + '"/><rect x="76.5" y="89" width="3" height="11" fill="#6b4a2b"/></g>';
    if (h.cls === "marksman") s += '<path d="M85 34C101 68 101 98 85 130" fill="none" stroke="#b88a52" stroke-width="3" stroke-linecap="round"/><line x1="85" y1="34" x2="85" y2="130" stroke="#fff" opacity=".45" stroke-width=".8"/>';
    if (h.cls === "mage") s += '<rect x="80.8" y="84" width="2.4" height="48" fill="#6b4a2b"/><circle cx="82" cy="78" r="10" fill="' + c + '" opacity=".28"/><circle cx="82" cy="78" r="5.5" fill="' + lighten(c, 0.55) + '"/>';
    if (h.cls === "support") s += '<rect x="13.5" y="50" width="2.6" height="82" fill="#d8c08a"/><circle cx="14.8" cy="47" r="6" fill="' + c + '" opacity=".35"/><circle cx="14.8" cy="47" r="3.6" fill="' + lighten(c, 0.5) + '"/>';
    if (style === 1 && h.cls !== "tank") s += '<path d="M30 54C26 26 74 26 70 54L77 104L23 104Z" fill="' + darken(hair, 0.15) + '"/>';
    // тело
    s += '<path d="M10 134C10 104 28 92 50 92s40 12 40 42z" fill="url(#b' + id + ')"/>';
    s += '<path d="M33 96L50 114 67 96" fill="none" stroke="' + c + '" stroke-width="2.6" opacity=".95" stroke-linejoin="round"/>';
    s += '<circle cx="20" cy="104" r="8" fill="' + lighten(c2, 0.12) + '" stroke="' + c + '" stroke-width="1.6"/><circle cx="80" cy="104" r="8" fill="' + lighten(c2, 0.12) + '" stroke="' + c + '" stroke-width="1.6"/>';
    s += '<circle cx="50" cy="118" r="4" fill="' + c + '"/><circle cx="50" cy="118" r="1.8" fill="' + lighten(c, 0.7) + '"/>';
    // шея и голова
    s += '<rect x="44" y="70" width="12" height="26" rx="5" fill="' + darken(skin, 0.12) + '"/>';
    s += '<ellipse cx="50" cy="55" rx="16" ry="18.5" fill="' + skin + '"/><ellipse cx="50" cy="63" rx="14" ry="10" fill="' + darken(skin, 0.1) + '" opacity=".25"/>';
    // глаза
    s += '<circle cx="43" cy="56" r="4.6" fill="' + c + '" opacity=".22"/><circle cx="57" cy="56" r="4.6" fill="' + c + '" opacity=".22"/>' +
      '<ellipse cx="43" cy="56" rx="3" ry="2.1" fill="#fff"/><ellipse cx="57" cy="56" rx="3" ry="2.1" fill="#fff"/>' +
      '<circle cx="43.4" cy="56" r="1.7" fill="' + darken(c, 0.2) + '"/><circle cx="57.4" cy="56" r="1.7" fill="' + darken(c, 0.2) + '"/>' +
      '<path d="M38.5 51.5l8-1.5M61.5 51.5l-8-1.5" stroke="' + darken(hair, 0.3) + '" stroke-width="1.6" stroke-linecap="round"/>' +
      '<path d="M45.5 67q4.5 2.4 9 0" fill="none" stroke="' + darken(skin, 0.4) + '" stroke-width="1.3" stroke-linecap="round"/>';
    if (extra === "scar") s += '<path d="M60 47l-6 15" stroke="#7a2a2a" stroke-width="1.4" stroke-linecap="round" opacity=".8"/>';
    if (extra === "beard") s += '<path d="M35 58C36 80 64 80 65 58C60 70 40 70 35 58Z" fill="' + hair + '"/>';
    if (extra === "mask") s += '<path d="M34.5 58L65.5 58 63 68C57 73 43 73 37 68Z" fill="' + darken(c2, 0.45) + '" stroke="' + c + '" stroke-width=".8"/>';
    // волосы / головные уборы
    if (h.cls === "tank") {
      s += '<path d="M31 58C28 24 72 24 69 58L66.5 47C58 38 42 38 33.5 47Z" fill="#8c97ad" stroke="#d5deee" stroke-width="1"/><rect x="48.4" y="40" width="3.2" height="17" fill="#aab4c6"/><path d="M50 18l-5 12h10z" fill="' + c + '"/>';
      s += '<path d="M6 94h30v26c0 9-15 15-15 15S6 129 6 120z" fill="' + c2 + '" stroke="' + c + '" stroke-width="2"/><g transform="translate(12 100) scale(.75)" fill="none" stroke="' + c + '" stroke-width="2" stroke-linecap="round">' + (SIGIL[h.faction] || "") + "</g>";
    } else if (h.cls === "marksman") {
      s += '<path d="M26 60C20 20 80 20 74 60L67 47C58 36 42 36 33 47Z" fill="' + c2 + '" stroke="' + lighten(c2, 0.3) + '" stroke-width="1"/><path d="M33 47C40 40 60 40 67 47" fill="none" stroke="' + c + '" stroke-width="1.3" opacity=".8"/>';
    } else if (h.cls === "mage") {
      s += hairFront(style, hair) + '<path d="M26 47L52 2 74 47C63 41 37 41 26 47Z" fill="' + c2 + '" stroke="' + c + '" stroke-width="1.5" stroke-linejoin="round"/><rect x="27" y="42" width="46" height="5.5" rx="2.5" fill="' + c + '"/><circle cx="50" cy="44.7" r="2" fill="' + lighten(c, 0.7) + '"/>';
    } else {
      s += hairFront(style, hair);
      if (h.cls === "support") s += '<ellipse cx="50" cy="27" rx="16" ry="4.8" fill="none" stroke="' + lighten(c, 0.45) + '" stroke-width="2.4"/><ellipse cx="50" cy="27" rx="16" ry="4.8" fill="none" stroke="' + c + '" stroke-width="5" opacity=".25"/>';
    }
    if (extra === "crown") s += '<path d="M36 37l4-10 5 6 5-9 5 9 5-6 4 10z" fill="#f2c46a" stroke="#8a5f1c" stroke-width="1" stroke-linejoin="round"/><circle cx="50" cy="31" r="1.7" fill="#ff3d7f"/>';
    return s + "</svg>";
  }
  function hairFront(style, hair) {
    const d = {
      0: '<path d="M32 56C28 28 72 28 68 56C65 45 59 40 50 40C41 40 35 45 32 56Z" fill="' + hair + '"/>',
      1: '<path d="M32 54C34 34 66 34 68 54C60 44 42 44 32 54Z" fill="' + hair + '"/>',
      2: '<path d="M32 56C27 28 73 24 68 50C60 38 46 37 32 56Z" fill="' + hair + '"/><path d="M63 40L77 76 63 62Z" fill="' + hair + '"/>',
      3: '<path d="M32 56L29 33 40 41 42 24 50 38 58 24 60 41 71 33 68 56C62 45 38 45 32 56Z" fill="' + hair + '"/>',
    };
    return d[style] || d[0];
  }

  /* ------------------------------------------------ портреты монстров и боссов */
  function monsterSvg(u) {
    const id = "m" + (++uid), ch = G.cat.chapters[(u.chapter || 1) - 1] || G.cat.chapters[0];
    const acc = ch.accent, boss = u.boss, key = u.key;
    const skinTints = { bonewarden: "#d9d2c0", cavebrute: mix("#6f8a62", acc, 0.2), whisperwitch: "#2a2438", rotarcher: "#3a3a32", decaypriest: "#e8e0d0" };
    const skin = boss ? mix("#3a2a44", acc, 0.35) : (skinTints[key] || "#556");
    let s = '<svg viewBox="0 0 100 132" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<radialGradient id="g' + id + '" cx="50%" cy="40%" r="80%"><stop offset="0" stop-color="' + acc + '" stop-opacity="' + (boss ? ".7" : ".4") + '"/><stop offset=".55" stop-color="' + mix("#150f2a", acc, 0.18) + '"/><stop offset="1" stop-color="#05041a"/></radialGradient></defs>';
    s += '<rect width="100" height="132" fill="url(#g' + id + ')"/>';
    if (boss) s += '<circle cx="50" cy="55" r="44" fill="' + acc + '" opacity=".18"/><circle cx="50" cy="55" r="36" fill="none" stroke="' + acc + '" stroke-width="1" opacity=".5" stroke-dasharray="3 4"/>';
    if (key === "rotarcher") s += '<path d="M10 120L88 18" stroke="#8a6a3a" stroke-width="2.2"/><path d="M88 18l-7 2 5 5z" fill="#cfd8e8"/>';
    const horn = boss ? "#e8dcc0" : mix("#cfc6b0", acc, 0.25);
    if (boss || key === "cavebrute" || key === "decaypriest") {
      const sc = boss ? 1.25 : 0.85;
      s += '<g transform="translate(50 40) scale(' + sc + ') translate(-50 -40)"><path d="M34 44C24 40 20 28 26 14 28 28 36 34 40 36Z" fill="' + horn + '"/><path d="M66 44C76 40 80 28 74 14 72 28 64 34 60 36Z" fill="' + horn + '"/></g>';
    }
    s += '<path d="M6 134C6 100 26 90 50 90s44 10 44 44z" fill="' + darken(mix("#2a1f3d", acc, 0.2), 0.1) + '"/><path d="M26 98l24 20 24-20" fill="none" stroke="' + acc + '" stroke-width="2.4" opacity=".7"/>';
    if (key === "whisperwitch" || key === "rotarcher") {
      s += '<path d="M24 62C18 20 82 20 76 62L70 94H30Z" fill="' + darken(mix("#241a3a", acc, 0.2), 0.1) + '"/><ellipse cx="50" cy="58" rx="15" ry="17" fill="#07050f"/>';
    } else {
      const rx = key === "cavebrute" || boss ? 20 : 16;
      s += '<rect x="43" y="72" width="14" height="24" rx="5" fill="' + darken(skin, 0.25) + '"/><ellipse cx="50" cy="55" rx="' + rx + '" ry="18" fill="' + skin + '"/>';
    }
    const eye = boss ? "#ff3d3d" : acc;
    if (key === "whisperwitch") {
      s += [[41, 55], [59, 55], [50, 46]].map((p) => '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="4.5" fill="' + acc + '" opacity=".3"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="2" fill="#fff"/>').join("");
    } else if (key === "rotarcher") {
      s += '<circle cx="50" cy="56" r="8" fill="' + acc + '" opacity=".3"/><ellipse cx="50" cy="56" rx="5" ry="3.6" fill="#fff"/><circle cx="50" cy="56" r="2" fill="' + acc + '"/>';
    } else {
      s += '<ellipse cx="42" cy="54" rx="5" ry="4.5" fill="#0a0612"/><ellipse cx="58" cy="54" rx="5" ry="4.5" fill="#0a0612"/><circle cx="42" cy="54" r="2.2" fill="' + eye + '"/><circle cx="58" cy="54" r="2.2" fill="' + eye + '"/>' +
        '<path d="M37 47l10 4M63 47l-10 4" stroke="' + darken(skin, 0.5) + '" stroke-width="2" stroke-linecap="round"/>';
      if (key === "bonewarden" || boss) s += '<path d="M40 68h20M43 66v5M48 66v6M52 66v6M57 66v5" stroke="' + darken(skin, 0.5) + '" stroke-width="1.4"/>';
      if (key === "cavebrute") s += '<path d="M40 64l-3 10 6-5zM60 64l3 10-6-5z" fill="#f4efe0"/>';
      if (key === "decaypriest") s += '<path d="M30 40L20 22M30 40l-3-12M70 40l10-18M70 40l3-12" stroke="#cfc6b0" stroke-width="2.2" stroke-linecap="round"/>';
    }
    if (key === "bonewarden" && !boss) s += '<path d="M31 56C28 26 72 26 69 56L66 46C58 38 42 38 34 46Z" fill="#6c7488" stroke="#a9b2c6"/>';
    if (boss) s += '<path d="M30 38l5-14 6 8 5-13 4 13 5-13 5 13 6-8 5 14z" fill="' + acc + '" stroke="#fff" stroke-opacity=".5" stroke-width="1" stroke-linejoin="round"/>';
    return s + "</svg>";
  }

  /* ------------------------------------------------ публичные функции */
  function portrait(tpl) {
    if (tpl.portrait_url) return '<img src="' + tpl.portrait_url + '" alt="" loading="lazy" draggable="false">';
    return heroSvg(tpl);
  }
  function unitFace(u) {
    if (u.mon) return monsterSvg(u);
    const t = hero(u.key);
    return t ? portrait(t) : "";
  }
  function stars(n, max) {
    max = max || G.cat.max_stars;
    return "★".repeat(n) + '<span class="e">' + "★".repeat(Math.max(0, max - n)) + "</span>";
  }
  /* opts: level, stars, locked, mini, sel, tag, attrs */
  function card(tpl, opts) {
    opts = opts || {};
    const r = rar(tpl.rarity), f = fac(tpl.faction);
    return '<div class="hcard r-' + tpl.rarity + (opts.locked ? " locked" : "") + (opts.mini ? " mini" : "") + (opts.sel ? " sel" : "") + '" style="--rc:' + r.color + ";--rg:" + r.glow + '" ' + (opts.attrs || "") + ">" +
      '<div class="art">' + portrait(tpl) + '</div><div class="shade"></div>' +
      '<div class="top"><span class="badge" style="color:' + f.color + '">' + sigil(tpl.faction, 14) + '</span><span class="badge" style="color:var(--gold)">' + clsIcon(tpl.cls, 14) + "</span></div>" +
      (opts.tag ? '<span class="tag">' + opts.tag + "</span>" : "") +
      '<div class="bot"><div class="nm">' + UI.esc(tpl.name.split(" ")[0]) + '</div><div class="meta"><span>' + (opts.level ? "Ур. " + opts.level : "") + '</span><span class="stars">' + (opts.locked ? "" : stars(opts.stars || 0)) + "</span></div></div>" +
      (opts.locked ? '<div class="lock">' + icon("lock", 20) + "</div>" : "") + "</div>";
  }
  function enemyMini(u) {
    return '<div class="foe' + (u.boss ? " boss" : "") + '" title="' + UI.esc(u.name) + '">' + monsterSvg(u) + "</div>";
  }
  const coin = (kind, n, bad) => '<span class="c' + (bad ? " bad" : "") + '">' + icon(kind, 15) + UI.fmt(n) + "</span>";

  return { index, hero, rar, fac, icon, sigil, clsIcon, portrait, unitFace, card, enemyMini, stars, coin, lighten, mix };
})();
