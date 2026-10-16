"""Сервисный слой: все изменения экономики и прогресса.

Каждая функция вызывается внутри транзакции BEGIN IMMEDIATE (см. database.transaction),
получает соединение и id игрока, проверяет правила на сервере и пишет в БД.
Модуль не зависит от FastAPI, поэтому его можно тестировать напрямую.
"""
from __future__ import annotations

import json
import random
import secrets
import sqlite3
import time
from datetime import datetime, timezone

import config
import game_data as D
import game_logic as L


class GameError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


# ------------------------------------------------------------------ время
_clock = time.time   # подменяется в тестах


def now() -> int:
    return int(_clock())


def today() -> str:
    return datetime.fromtimestamp(now(), tz=timezone.utc).strftime("%Y-%m-%d")


RES_GEN = {"gold": "золота", "exp": "опыта", "gems": "самоцветов", "tickets": "билетов", "shards": "фрагментов"}


# ------------------------------------------------------------------ базовые операции
def log_event(conn, pid: int, kind: str, payload: dict, idem: str | None = None) -> None:
    conn.execute("INSERT INTO events (player_id, kind, idem_key, payload, created_at) VALUES (?,?,?,?,?)",
                 (pid, kind, idem, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), now()))


def idem_get(conn, pid: int, kind: str, key: str | None):
    if not key:
        return None
    r = conn.execute("SELECT payload FROM events WHERE player_id=? AND kind=? AND idem_key=?", (pid, kind, key)).fetchone()
    return json.loads(r["payload"]) if r else None


def prune_events(conn, pid: int, kind: str, keep: int = 20) -> None:
    conn.execute("DELETE FROM events WHERE player_id=? AND kind=? AND id NOT IN "
                 "(SELECT id FROM events WHERE player_id=? AND kind=? ORDER BY id DESC LIMIT ?)",
                 (pid, kind, pid, kind, keep))


def get_player(conn, pid: int) -> dict:
    return dict(conn.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone())


def need(p: dict, **cost) -> None:
    missing = [f"{v - p[k]} {RES_GEN[k]}" for k, v in cost.items() if v and p[k] < v]
    if missing:
        raise GameError("insufficient", "Не хватает: " + ", ".join(missing) + ".")


def add_res(conn, pid: int, gold: int = 0, exp: int = 0, gems: int = 0, tickets: int = 0) -> None:
    try:
        conn.execute("UPDATE players SET gold=gold+?, exp=exp+?, gems=gems+?, tickets=tickets+? WHERE id=?",
                     (gold, exp, gems, tickets, pid))
    except sqlite3.IntegrityError:
        raise GameError("insufficient", "Недостаточно ресурсов.")


def bump_quest(conn, pid: int, qid: str, n: int = 1) -> None:
    conn.execute("INSERT INTO daily_quests (player_id, day, quest_id, progress) VALUES (?,?,?,?) "
                 "ON CONFLICT(player_id, day, quest_id) DO UPDATE SET progress = progress + ?",
                 (pid, today(), qid, n, n))


def quest_progress(conn, pid: int, qid: str) -> int:
    r = conn.execute("SELECT progress FROM daily_quests WHERE player_id=? AND day=? AND quest_id=?",
                     (pid, today(), qid)).fetchone()
    return r["progress"] if r else 0


# ------------------------------------------------------------------ игрок
def get_or_create_player(conn, tg: dict) -> int:
    row = conn.execute("SELECT id, name, username FROM players WHERE tg_id=?", (tg["id"],)).fetchone()
    if row:
        if row["name"] != tg["name"] or row["username"] != tg.get("username"):
            conn.execute("UPDATE players SET name=?, username=? WHERE id=?", (tg["name"], tg.get("username"), row["id"]))
        return row["id"]
    t, s = now(), D.STARTER
    cur = conn.execute(
        "INSERT INTO players (tg_id, name, username, gold, exp, gems, tickets, last_idle_claim, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (tg["id"], tg["name"], tg.get("username"), s["gold"], s["exp"], s["gems"], s["tickets"],
         t - s["idle_head_start"], t))
    pid = cur.lastrowid
    for slot, key in enumerate(D.STARTER_HEROES):
        conn.execute("INSERT INTO heroes (player_id, hero_key, created_at) VALUES (?,?,?)", (pid, key, t))
        conn.execute("INSERT INTO squad (player_id, slot, hero_key) VALUES (?,?,?)", (pid, slot, key))
    log_event(conn, pid, "player_created", {"tg_id": tg["id"]})
    return pid


# ------------------------------------------------------------------ герои
def _eq(r) -> dict:
    return {"weapon": r["eq_weapon"], "armor": r["eq_armor"], "relic": r["eq_relic"]}


def hero_row(conn, pid: int, key: str):
    r = conn.execute("SELECT * FROM heroes WHERE player_id=? AND hero_key=?", (pid, key)).fetchone()
    if not r:
        raise GameError("not_owned", "У вас нет этого героя.", 404)
    return r


def hero_view(r) -> dict:
    tpl = D.HEROES[r["hero_key"]]
    eq, lvl, stars = _eq(r), r["level"], r["stars"]
    cap = L.level_cap(stars)
    stats = L.hero_stats(tpl["base"], lvl, stars, eq)
    equip_next = {}
    for slot in D.EQUIP_SLOTS:
        if eq[slot] >= D.EQUIP_MAX:
            equip_next[slot] = None
        else:
            e2 = dict(eq, **{slot: eq[slot] + 1})
            equip_next[slot] = {"cost": L.equip_cost(eq[slot]), "stats": L.hero_stats(tpl["base"], lvl, stars, e2)}
    return {
        "key": r["hero_key"], "level": lvl, "stars": stars, "shards": r["shards"], "eq": eq, "cap": cap,
        "stats": stats, "power": L.stats_power(stats),
        "next_stats": L.hero_stats(tpl["base"], lvl + 1, stars, eq) if lvl < cap else None,
        "level_cost": L.level_cost(lvl) if lvl < cap else None,
        "star_cost": L.star_cost(stars) if stars < D.MAX_STARS else None,
        "star_next": L.hero_stats(tpl["base"], lvl, stars + 1, eq) if stars < D.MAX_STARS else None,
        "equip_next": equip_next,
    }


def level_up(conn, pid: int, key: str, times: int = 1) -> dict:
    r = hero_row(conn, pid, key)
    lvl, gained, reason, code = r["level"], 0, None, "cannot_upgrade"
    for _ in range(max(1, min(int(times), 10))):
        if lvl >= L.level_cap(r["stars"]):
            reason = "Достигнут предел уровня. Повысьте звёзды героя."
            break
        cost = L.level_cost(lvl)
        p = get_player(conn, pid)
        if p["gold"] < cost["gold"] or p["exp"] < cost["exp"]:
            try:
                need(p, gold=cost["gold"], exp=cost["exp"])
            except GameError as e:
                reason, code = e.message, e.code
            break
        add_res(conn, pid, gold=-cost["gold"], exp=-cost["exp"])
        lvl += 1
        gained += 1
    if gained == 0:
        raise GameError(code, reason or "Улучшение недоступно.")
    conn.execute("UPDATE heroes SET level=? WHERE id=?", (lvl, r["id"]))
    bump_quest(conn, pid, "q_upgrade", gained)
    return {"hero": key, "gained": gained, "level": lvl}


def equip_up(conn, pid: int, key: str, slot: str) -> dict:
    if slot not in D.EQUIP_SLOTS:
        raise GameError("bad_slot", "Неизвестный слот экипировки.")
    r = hero_row(conn, pid, key)
    col = "eq_" + slot
    cur = r[col]
    if cur >= D.EQUIP_MAX:
        raise GameError("cannot_upgrade", "Предмет уже улучшен до максимума.")
    cost = L.equip_cost(cur)
    need(get_player(conn, pid), gold=cost)
    add_res(conn, pid, gold=-cost)
    conn.execute(f"UPDATE heroes SET {col}=? WHERE id=?", (cur + 1, r["id"]))
    bump_quest(conn, pid, "q_upgrade", 1)
    return {"hero": key, "slot": slot, "level": cur + 1}


def star_up(conn, pid: int, key: str) -> dict:
    r = hero_row(conn, pid, key)
    if r["stars"] >= D.MAX_STARS:
        raise GameError("cannot_upgrade", "Максимум звёзд.")
    cost = L.star_cost(r["stars"])
    if r["shards"] < cost["shards"]:
        raise GameError("insufficient", f"Не хватает {cost['shards'] - r['shards']} фрагментов героя.")
    need(get_player(conn, pid), gold=cost["gold"])
    add_res(conn, pid, gold=-cost["gold"])
    conn.execute("UPDATE heroes SET stars=stars+1, shards=shards-? WHERE id=?", (cost["shards"], r["id"]))
    bump_quest(conn, pid, "q_upgrade", 1)
    return {"hero": key, "stars": r["stars"] + 1}


# ------------------------------------------------------------------ отряд
def squad_slots(conn, pid: int) -> list:
    slots = [None] * 5
    for r in conn.execute("SELECT slot, hero_key FROM squad WHERE player_id=?", (pid,)):
        slots[r["slot"]] = r["hero_key"]
    return slots


def set_squad(conn, pid: int, slots: list) -> dict:
    if not isinstance(slots, list) or len(slots) != 5:
        raise GameError("bad_squad", "Отряд состоит из пяти слотов.")
    keys = [k for k in slots if k]
    if any(not isinstance(k, str) for k in keys):
        raise GameError("bad_squad", "Некорректный состав отряда.")
    if not keys:
        raise GameError("bad_squad", "В отряде должен быть хотя бы один герой.")
    if len(set(keys)) != len(keys):
        raise GameError("duplicate_hero", "Один герой не может занимать два слота.")
    owned = {r["hero_key"] for r in conn.execute("SELECT hero_key FROM heroes WHERE player_id=?", (pid,))}
    for k in keys:
        if k not in owned:
            raise GameError("not_owned", "В отряд можно ставить только героев из вашей коллекции.", 404)
    conn.execute("DELETE FROM squad WHERE player_id=?", (pid,))
    for i, k in enumerate(slots):
        if k:
            conn.execute("INSERT INTO squad (player_id, slot, hero_key) VALUES (?,?,?)", (pid, i, k))
    return {"slots": slots}


def auto_fill_squad(conn, pid: int) -> None:
    """Заполняет ПУСТЫЕ слоты сильнейшими героями (занятые слоты не трогает)."""
    slots = squad_slots(conn, pid)
    empty = [i for i, k in enumerate(slots) if k is None]
    if not empty:
        return
    rows = [r for r in conn.execute("SELECT * FROM heroes WHERE player_id=?", (pid,)) if r["hero_key"] not in slots]
    rows.sort(key=lambda r: -hero_view(r)["power"])
    for slot, r in zip(empty, rows):
        conn.execute("INSERT INTO squad (player_id, slot, hero_key) VALUES (?,?,?)", (pid, slot, r["hero_key"]))


def player_units(conn, pid: int) -> tuple[list[dict], dict]:
    q = ("SELECT h.*, s.slot FROM squad s JOIN heroes h ON h.player_id=s.player_id AND h.hero_key=s.hero_key "
         "WHERE s.player_id=? ORDER BY s.slot")
    units = []
    for r in conn.execute(q, (pid,)):
        tpl = D.HEROES[r["hero_key"]]
        st = L.hero_stats(tpl["base"], r["level"], r["stars"], _eq(r))
        units.append({"key": tpl["key"], "name": tpl["name"], "cls": tpl["cls"], "fac": tpl["faction"],
                      "rarity": tpl["rarity"], "level": r["level"], "basic": tpl["basic"], "ult": tpl["ult"], **st})
    bonuses = L.apply_bonuses(units)
    return units, bonuses


# ------------------------------------------------------------------ призыв
def summon_cost(count: int, currency: str) -> int:
    if currency == "tickets":
        return count * D.SUMMON_COST["tickets"]
    return D.SUMMON_COST["gems"] if count == 1 else D.SUMMON_X10_DISCOUNT_GEMS


def summon(conn, pid: int, count: int, currency: str, request_id: str | None = None,
           rng: random.Random | None = None) -> dict:
    if count not in (1, 10):
        raise GameError("bad_request", "Можно призвать 1 или 10 героев.")
    if currency not in ("tickets", "gems"):
        raise GameError("bad_request", "Неизвестная валюта призыва.")
    prev = idem_get(conn, pid, "summon", request_id)
    if prev:
        prev["replayed"] = True
        return prev
    p = get_player(conn, pid)
    cost = summon_cost(count, currency)
    need(p, **{currency: cost})
    add_res(conn, pid, **{currency: -cost})
    rng = rng or random.SystemRandom()
    pe, pl = p["pity_epic"], p["pity_legend"]
    results = []
    for _ in range(count):
        rarity = L.roll_rarity(rng, pe, pl)
        key = L.pick_hero(rng, rarity)
        pe, pl = L.advance_pity(pe, pl, rarity)
        if conn.execute("SELECT 1 FROM heroes WHERE player_id=? AND hero_key=?", (pid, key)).fetchone():
            shards = D.RARITIES[rarity]["dupe_shards"]
            conn.execute("UPDATE heroes SET shards=shards+? WHERE player_id=? AND hero_key=?", (shards, pid, key))
            results.append({"key": key, "rarity": rarity, "new": False, "shards": shards})
        else:
            conn.execute("INSERT INTO heroes (player_id, hero_key, created_at) VALUES (?,?,?)", (pid, key, now()))
            results.append({"key": key, "rarity": rarity, "new": True, "shards": 0})
    conn.execute("UPDATE players SET pity_epic=?, pity_legend=?, summons_total=summons_total+? WHERE id=?",
                 (pe, pl, count, pid))
    auto_fill_squad(conn, pid)
    bump_quest(conn, pid, "q_summon", 1)
    payload = {"results": results, "spent": {currency: cost}, "count": count}
    log_event(conn, pid, "summon", payload, request_id)
    prune_events(conn, pid, "summon", 20)
    return payload


# ------------------------------------------------------------------ кампания и бой
def enemy_brief(e: dict) -> dict:
    return {"key": e["key"], "name": e["name"], "cls": e["cls"], "boss": e["boss"], "level": e["level"],
            "chapter": e["chapter"], "power": L.stats_power(e)}


def stage_view(conn, pid: int, n: int) -> dict:
    if not isinstance(n, int) or n < 1 or n > D.MAX_STAGE:
        raise GameError("bad_stage", "Такого этапа нет.", 404)
    p = get_player(conn, pid)
    chapter, sub, boss = L.stage_chapter(n)
    enemies = L.enemy_team(n)
    r = conn.execute("SELECT clears FROM stage_clears WHERE player_id=? AND stage=?", (pid, n)).fetchone()
    return {"stage": n, "chapter": chapter["id"], "sub": sub, "boss": boss,
            "enemies": [enemy_brief(e) for e in enemies], "enemy_power": sum(L.stats_power(e) for e in enemies),
            "rewards": L.stage_rewards(n, first_clear=n > p["stage_cleared"]),
            "clears": r["clears"] if r else 0, "locked": n > p["stage_cleared"] + 1}


def battle(conn, pid: int, stage: int, request_id: str | None = None) -> dict:
    prev = idem_get(conn, pid, "battle", request_id)
    if prev:
        prev["replayed"] = True
        return prev
    p = get_player(conn, pid)
    if not isinstance(stage, int) or stage < 1 or stage > D.MAX_STAGE:
        raise GameError("bad_stage", "Такого этапа нет.", 404)
    if stage > p["stage_cleared"] + 1:
        raise GameError("stage_locked", "Сначала пройдите предыдущий этап.")
    units, bonuses = player_units(conn, pid)
    if not units:
        raise GameError("empty_squad", "Соберите отряд перед боем.")
    sim = L.simulate(units, L.enemy_team(stage), secrets.randbits(62))
    first = stage == p["stage_cleared"] + 1
    rewards = {"gold": 0, "exp": 0, "gems": 0, "tickets": 0, "xp": 0}
    reduced = False
    if sim["win"]:
        rewards = L.stage_rewards(stage, first)
        if not first and quest_progress(conn, pid, "q_win") >= D.DAILY_FULL_REWARD_WINS:
            rewards["gold"] //= 4
            rewards["exp"] //= 4
            reduced = True
        add_res(conn, pid, gold=rewards["gold"], exp=rewards["exp"], gems=rewards["gems"], tickets=rewards["tickets"])
        conn.execute("UPDATE players SET account_xp=account_xp+? WHERE id=?", (rewards["xp"], pid))
        if first:
            conn.execute("UPDATE players SET stage_cleared=? WHERE id=?", (stage, pid))
        conn.execute("INSERT INTO stage_clears (player_id, stage, clears) VALUES (?,?,1) "
                     "ON CONFLICT(player_id, stage) DO UPDATE SET clears = clears + 1", (pid, stage))
        bump_quest(conn, pid, "q_win", 1)
    payload = {"result": {"win": sim["win"], "stage": stage, "rounds": sim["rounds"], "rewards": rewards,
                          "first_clear": bool(first and sim["win"]), "reduced": reduced,
                          "bonuses": bonuses},
               "units": sim["units"], "log": sim["log"]}
    log_event(conn, pid, "battle", payload, request_id)
    prune_events(conn, pid, "battle", 20)
    return payload


# ------------------------------------------------------------------ idle, подарки, задания
def idle_preview(p: dict) -> dict:
    elapsed = max(0, now() - p["last_idle_claim"])
    return L.idle_calc(p["stage_cleared"], elapsed, config.IDLE_CAP_HOURS)


def idle_claim(conn, pid: int) -> dict:
    p = get_player(conn, pid)
    t = now()
    calc = idle_preview(p)
    if calc["seconds"] < 60 or calc["gold"] + calc["exp"] + calc["gems"] <= 0:
        raise GameError("idle_empty", "Пока нечего забирать — награды ещё копятся.")
    # compare-and-swap: повторный запрос не пройдёт, потому что время уже сдвинуто
    cur = conn.execute("UPDATE players SET last_idle_claim=? WHERE id=? AND last_idle_claim=?",
                       (t, pid, p["last_idle_claim"]))
    if cur.rowcount != 1:
        raise GameError("conflict", "Награда уже получена.")
    add_res(conn, pid, gold=calc["gold"], exp=calc["exp"], gems=calc["gems"])
    bump_quest(conn, pid, "q_idle", 1)
    log_event(conn, pid, "idle_claim", {k: calc[k] for k in ("seconds", "gold", "exp", "gems")})
    return {"claimed": {"gold": calc["gold"], "exp": calc["exp"], "gems": calc["gems"]}, "seconds": calc["seconds"]}


def claim_daily_gift(conn, pid: int) -> dict:
    cur = conn.execute("UPDATE players SET last_gift_day=? WHERE id=? AND (last_gift_day IS NULL OR last_gift_day<>?)",
                       (today(), pid, today()))
    if cur.rowcount != 1:
        raise GameError("already_claimed", "Сегодняшний дар уже получен. Возвращайтесь завтра!")
    add_res(conn, pid, **D.DAILY_GIFT)
    log_event(conn, pid, "daily_gift", D.DAILY_GIFT)
    return {"gave": D.DAILY_GIFT}


def quests_view(conn, pid: int) -> list:
    rows = {r["quest_id"]: r for r in conn.execute(
        "SELECT * FROM daily_quests WHERE player_id=? AND day=?", (pid, today()))}
    out = []
    for q in D.QUESTS:
        r = rows.get(q["id"])
        out.append({"id": q["id"], "name": q["name"], "target": q["target"], "reward": q["reward"],
                    "progress": min(r["progress"], q["target"]) if r else 0, "claimed": bool(r and r["claimed"])})
    return out


def claim_quest(conn, pid: int, qid: str) -> dict:
    q = next((x for x in D.QUESTS if x["id"] == qid), None)
    if not q:
        raise GameError("bad_quest", "Неизвестное задание.", 404)
    cur = conn.execute("UPDATE daily_quests SET claimed=1 WHERE player_id=? AND day=? AND quest_id=? "
                       "AND claimed=0 AND progress>=?", (pid, today(), qid, q["target"]))
    if cur.rowcount != 1:
        raise GameError("cannot_claim", "Задание не выполнено или награда уже получена.")
    add_res(conn, pid, **q["reward"])
    log_event(conn, pid, "quest_claim", {"quest": qid, "reward": q["reward"]})
    return {"quest": qid, "reward": q["reward"]}


# ------------------------------------------------------------------ магазин
def shop_buy(conn, pid: int, item_id: str) -> dict:
    item = next((i for i in D.SHOP if i["id"] == item_id), None)
    if not item:
        raise GameError("bad_item", "Такого товара нет.", 404)
    if item["kind"] == "premium":
        # Реальные платежи отключены. Будущая интеграция Telegram Stars: счёт создаёт сервер (createInvoiceLink),
        # а выдача происходит только после successful_payment, подтверждённого ботом (см. README).
        raise GameError("payments_disabled", "Покупки за Telegram Stars отключены в тестовом режиме.", 403)
    if item["kind"] == "free":
        return claim_daily_gift(conn, pid)
    p = get_player(conn, pid)
    need(p, gems=item["price"])
    if "frame" in item:
        owned = json.loads(p["cosmetics"])
        if item["frame"] in owned:
            raise GameError("already_owned", "Эта рамка уже куплена.")
        add_res(conn, pid, gems=-item["price"])
        owned.append(item["frame"])
        conn.execute("UPDATE players SET cosmetics=?, frame=? WHERE id=?", (json.dumps(owned), item["frame"], pid))
    else:
        add_res(conn, pid, gems=-item["price"], **item["give"])
    log_event(conn, pid, "shop_buy", {"item": item_id, "price": item["price"]})
    return {"item": item_id, "gave": item.get("give"), "frame": item.get("frame")}


def set_frame(conn, pid: int, frame: str) -> dict:
    p = get_player(conn, pid)
    if frame not in D.FRAMES or (frame != "none" and frame not in json.loads(p["cosmetics"])):
        raise GameError("not_owned", "Эта рамка вам не принадлежит.")
    conn.execute("UPDATE players SET frame=? WHERE id=?", (frame, pid))
    return {"frame": frame}


# ------------------------------------------------------------------ состояние для клиента
def catalog() -> dict:
    heroes = []
    static_dir = config.BASE_DIR / "static" / "assets" / "heroes"
    for k in D.HERO_ORDER:
        h = D.HEROES[k]
        url = None
        for ext in ("webp", "png", "jpg"):
            if (static_dir / f"{k}.{ext}").exists():
                url = f"/static/assets/heroes/{k}.{ext}"
                break
        heroes.append({"key": k, "name": h["name"], "title": h["title"], "rarity": h["rarity"],
                       "faction": h["faction"], "cls": h["cls"], "desc": h["desc"], "look": h["look"],
                       "base": h["base"], "portrait_url": url,
                       "basic": {x: h["basic"][x] for x in ("name", "desc")},
                       "ult": {x: h["ult"][x] for x in ("name", "desc")}})
    chapters = [{"id": c["id"], "name": c["name"], "desc": c["desc"], "c1": c["c1"], "c2": c["c2"],
                 "accent": c["accent"], "boss": {"key": c["boss"]["key"], "name": c["boss"]["name"]}}
                for c in D.CHAPTERS]
    return {
        "title": D.GAME_TITLE, "subtitle": D.GAME_SUBTITLE, "heroes": heroes, "factions": D.FACTIONS,
        "classes": {k: {"name": v["name"], "desc": v["desc"]} for k, v in D.CLASSES.items()},
        "rarities": D.RARITIES, "chapters": chapters, "stages_per_chapter": D.STAGES_PER_CHAPTER,
        "max_stage": D.MAX_STAGE, "faction_bonus": {str(k): v for k, v in D.FACTION_BONUS.items()},
        "equip_slots": D.EQUIP_SLOT_INFO, "equip_names": D.EQUIP_NAMES, "equip_max": D.EQUIP_MAX,
        "max_stars": D.MAX_STARS, "shop": D.SHOP, "frames": D.FRAMES,
        "summon": {"rates": D.SUMMON_RATES, "cost": D.SUMMON_COST, "x10_gems": D.SUMMON_X10_DISCOUNT_GEMS,
                   "pity_epic": D.PITY_EPIC_EVERY, "pity_legend": D.PITY_LEGEND_HARD,
                   "soft_start": D.PITY_SOFT_START, "soft_step": D.PITY_SOFT_STEP},
        "idle_cap_hours": config.IDLE_CAP_HOURS, "dev_mode": config.DEV_MODE,
    }


def build_state(conn, pid: int) -> dict:
    p = get_player(conn, pid)
    heroes = [hero_view(r) for r in conn.execute("SELECT * FROM heroes WHERE player_id=? ORDER BY id", (pid,))]
    slots = squad_slots(conn, pid)
    units, bonuses = player_units(conn, pid)
    squad_power = sum(L.stats_power(u) for u in units)
    lvl = L.account_level(p["account_xp"])
    base_xp = L.xp_for_level(lvl)
    nxt = min(p["stage_cleared"] + 1, D.MAX_STAGE)
    clears = {str(r["stage"]): r["clears"] for r in conn.execute(
        "SELECT stage, clears FROM stage_clears WHERE player_id=?", (pid,))}
    pe, pl = p["pity_epic"], p["pity_legend"]
    return {
        "server_time": now(),
        "player": {"id": pid, "name": p["name"], "level": lvl, "xp": p["account_xp"] - base_xp,
                   "xp_next": L.xp_for_level(lvl + 1) - base_xp, "frame": p["frame"],
                   "cosmetics": json.loads(p["cosmetics"]), "gold": p["gold"], "exp": p["exp"],
                   "gems": p["gems"], "tickets": p["tickets"], "summons_total": p["summons_total"]},
        "heroes": heroes,
        "squad": {"slots": slots, "power": squad_power,
                  "bonuses": [{"faction": f, **b} for f, b in bonuses.items()]},
        "campaign": {"cleared": p["stage_cleared"], "max_stage": D.MAX_STAGE, "next": nxt,
                     "finished": p["stage_cleared"] >= D.MAX_STAGE, "view": stage_view(conn, pid, nxt),
                     "clears": clears},
        "idle": idle_preview(p),
        "summon": {"pity_epic": pe, "pity_legend": pl, "rates": L.summon_rates(pe, pl)},
        "quests": quests_view(conn, pid),
        "gift_ready": p["last_gift_day"] != today(),
    }
