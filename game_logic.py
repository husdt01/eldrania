"""Чистая игровая логика без доступа к БД и сети: формулы, симулятор боя, призыв, idle.

Всё, что влияет на экономику и исход боя, считается здесь, на сервере.
"""
from __future__ import annotations

import math
import random

from game_data import (
    CHAPTERS, CLASSES, FACTION_BONUS, HEROES, MAX_STAGE, MONSTERS, PITY_EPIC_EVERY, PITY_LEGEND_HARD,
    PITY_SOFT_START, PITY_SOFT_STEP, STAGES_PER_CHAPTER, STAR_GOLD, STAR_SHARDS, SUMMON_RATES,
)

MAX_ROUNDS = 30
ENERGY_ACT = 35     # энергия за собственное действие
ENERGY_HIT = 10     # энергия за полученный удар
CRIT_MULT = 1.5


def round10(x: float) -> int:
    return int(round(x / 10.0)) * 10


# ======================================================================= прокачка
def level_cap(stars: int) -> int:
    return 20 + 8 * stars


def level_cost(level: int) -> dict:
    """Стоимость перехода с уровня level на level+1."""
    return {"gold": max(50, round10(50 * 1.12 ** (level - 1))),
            "exp": max(30, round10(30 * 1.115 ** (level - 1)))}


def equip_cost(level: int) -> int:
    """Золото за повышение предмета с уровня level на level+1."""
    return max(300, round10(300 * 1.45 ** level))


def star_cost(stars: int) -> dict:
    return {"shards": STAR_SHARDS[stars], "gold": STAR_GOLD[stars]}


def hero_stats(base: dict, level: int, stars: int, eq: dict) -> dict:
    m = (1 + 0.09 * (level - 1)) * (1 + 0.15 * stars)
    armor = 1 + 0.05 * eq.get("armor", 0)
    weapon = 1 + 0.05 * eq.get("weapon", 0)
    relic = eq.get("relic", 0)
    return {
        "hp": int(base["hp"] * m * armor),
        "atk": int(base["atk"] * m * weapon),
        "def": int(base["def"] * m * armor),
        "spd": int(base["spd"] + relic + stars),
        "crit": round(0.10 + 0.02 * relic, 2),
    }


def stats_power(s: dict) -> int:
    return int(s["hp"] * 0.12 + s["atk"] + s["def"] + s["spd"] * 1.5)


# ======================================================================= фракционные бонусы
def squad_bonuses(factions: list[str]) -> dict:
    """{фракция: {count, hp, atk}} для фракций с >= 2 героями в отряде."""
    counts: dict[str, int] = {}
    for f in factions:
        counts[f] = counts.get(f, 0) + 1
    out = {}
    for f, c in counts.items():
        if c >= 2:
            hp, atk = FACTION_BONUS[min(c, 5)]
            out[f] = {"count": c, "hp": hp, "atk": atk}
    return out


def apply_bonuses(units: list[dict]) -> dict:
    bonuses = squad_bonuses([u["fac"] for u in units])
    for u in units:
        b = bonuses.get(u["fac"])
        if b:
            u["hp"] = int(u["hp"] * (1 + b["hp"]))
            u["atk"] = int(u["atk"] * (1 + b["atk"]))
    return bonuses


# ======================================================================= аккаунт
def xp_for_level(level: int) -> int:
    return 40 * (level - 1) ** 2


def account_level(xp: int) -> int:
    return 1 + int(math.sqrt(max(0, xp) / 40))


# ======================================================================= idle
def idle_rates(stage_cleared: int) -> dict:
    return {"gold": 900 + 120 * stage_cleared, "exp": 500 + 70 * stage_cleared, "gems": 4}


def idle_calc(stage_cleared: int, elapsed: float, cap_hours: float) -> dict:
    cap = cap_hours * 3600
    sec = max(0.0, min(float(elapsed), cap))
    h = sec / 3600
    r = idle_rates(stage_cleared)
    return {"seconds": int(sec), "cap_seconds": int(cap), "capped": elapsed >= cap,
            "gold": int(r["gold"] * h), "exp": int(r["exp"] * h), "gems": int(r["gems"] * h), "rates": r}


# ======================================================================= призыв
def summon_rates(pity_epic: int, pity_legend: int) -> dict:
    """Вероятности СЛЕДУЮЩЕГО призыва с учётом pity. Эти же числа показывает UI."""
    base = SUMMON_RATES
    n = pity_legend + 1
    leg = base["legendary"]
    if n >= PITY_LEGEND_HARD:
        leg = 1.0
    elif n > PITY_SOFT_START:
        leg = min(1.0, leg + (n - PITY_SOFT_START) * PITY_SOFT_STEP)
    rest = 1.0 - leg
    base_rest = 1.0 - base["legendary"]
    rates = {k: base[k] * rest / base_rest for k in ("common", "rare", "epic")}
    rates["legendary"] = leg
    if pity_epic + 1 >= PITY_EPIC_EVERY:
        rates = {"common": 0.0, "rare": 0.0, "epic": 1.0 - leg, "legendary": leg}
    return rates


def roll_rarity(rng: random.Random, pity_epic: int, pity_legend: int) -> str:
    rates = summon_rates(pity_epic, pity_legend)
    u = rng.random()
    acc = 0.0
    for r in ("legendary", "epic", "rare", "common"):
        acc += rates[r]
        if u < acc:
            return r
    return "legendary" if rates["legendary"] >= 1.0 else "common"


def pick_hero(rng: random.Random, rarity: str) -> str:
    pool = sorted(k for k, h in HEROES.items() if h["rarity"] == rarity)
    return rng.choice(pool)


def advance_pity(pity_epic: int, pity_legend: int, rarity: str) -> tuple[int, int]:
    pity_epic += 1
    pity_legend += 1
    if rarity == "legendary":
        return 0, 0
    if rarity == "epic":
        return 0, pity_legend
    return pity_epic, pity_legend


# ======================================================================= кампания
def stage_chapter(n: int) -> tuple[dict, int, bool]:
    idx = (n - 1) // STAGES_PER_CHAPTER
    sub = (n - 1) % STAGES_PER_CHAPTER + 1
    return CHAPTERS[idx], sub, sub == STAGES_PER_CHAPTER


def stage_multiplier(n: int) -> float:
    return 0.50 + 0.13 * (n - 1) + 0.0022 * (n - 1) ** 2


def enemy_team(n: int) -> list[dict]:
    chapter, sub, is_boss = stage_chapter(n)
    rng = random.Random(n * 7919 + 13)
    keys = [rng.choice(["bonewarden", "cavebrute"]), rng.choice(["cavebrute", "bonewarden"]),
            rng.choice(["whisperwitch", "rotarcher"]), rng.choice(["rotarcher", "whisperwitch"]),
            rng.choice(["decaypriest", "whisperwitch", "rotarcher"])]
    mult = stage_multiplier(n)
    team = []
    for slot, mk in enumerate(keys):
        boss = is_boss and slot == 2
        tpl = chapter["boss"] if boss else MONSTERS[mk]
        hp, atk, df, spd = CLASSES[tpl["cls"]]["base"]
        hmod = amod = dmod = 1.0
        if boss:
            hmod, amod, dmod = 3.2, 1.15, 1.2
        team.append({
            "key": tpl["key"], "name": tpl["name"], "cls": tpl["cls"], "fac": "void", "rarity": "common",
            "level": int(n * 1.4) + 1, "mon": True, "boss": boss, "chapter": chapter["id"],
            "hp": int(hp * mult * hmod), "atk": int(atk * mult * amod), "def": int(df * (1 + (mult - 1) * 0.6) * dmod),
            "spd": spd, "crit": 0.08, "basic": tpl["basic"], "ult": tpl["ult"],
        })
    return team


def stage_rewards(n: int, first_clear: bool) -> dict:
    """Награда за победу. first_clear — первое прохождение этапа."""
    _, _, boss = stage_chapter(n)
    k = 2.5 if first_clear else 1.0
    r = {"gold": int((120 + 40 * n) * k), "exp": int((80 + 25 * n) * k), "xp": 20 + 3 * n, "gems": 0, "tickets": 0}
    if first_clear:
        r["gems"] = 20 + (40 if boss else 0)
        r["tickets"] = 2 if boss else (1 if n % 5 == 0 else 0)
    return r


# ======================================================================= симулятор боя
class Unit:
    def __init__(self, uid: str, side: str, slot: int, d: dict):
        self.id, self.side, self.slot, self.d = uid, side, slot, d
        self.maxhp = max(1, int(d["hp"]))
        self.hp = self.maxhp
        self.atk, self.df, self.spd = d["atk"], d["def"], d["spd"]
        self.crit = d.get("crit", 0.1)
        self.en = 0
        self.fx: list[dict] = []
        self.boss = bool(d.get("boss"))

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def atk_eff(self) -> float:
        return self.atk * (1 + sum(e["v"] for e in self.fx if e["t"] == "atk_up"))

    def def_eff(self) -> float:
        m = 1 + sum(e["v"] for e in self.fx if e["t"] == "def_up") - sum(e["v"] for e in self.fx if e["t"] == "def_down")
        return self.df * max(0.2, m)

    def shield(self) -> int:
        return int(sum(e["amt"] for e in self.fx if e["t"] == "shield"))

    def snap(self) -> list:
        return [max(0, self.hp), self.en, self.shield(), sorted({e["t"] for e in self.fx})]


FALLBACK = {"name": "Удар", "tgt": "front", "n": 1, "dmg": 0.8, "heal": 0.0, "fx": []}


def simulate(team_a: list[dict], team_b: list[dict], seed: int, max_rounds: int = MAX_ROUNDS) -> dict:
    """Автобой. team_a — отряд игрока, team_b — враги. Возвращает units, log, win, rounds.
    Результат полностью определяется характеристиками, навыками и seed."""
    rng = random.Random(seed)
    units = [Unit(f"a{i}", "a", i, d) for i, d in enumerate(team_a)] + \
            [Unit(f"b{i}", "b", i, d) for i, d in enumerate(team_b)]
    log: list[dict] = []

    def snap() -> dict:
        return {u.id: u.snap() for u in units}

    def alive(side: str) -> list[Unit]:
        return [u for u in units if u.side == side and u.alive]

    def pick(u: Unit, s: dict, enemies: list[Unit], allies: list[Unit]) -> list[Unit]:
        t, n = s["tgt"], s["n"]
        if t == "front":
            return sorted(enemies, key=lambda x: x.slot)[:n]
        if t == "lowest":
            return sorted(enemies, key=lambda x: (x.hp, x.slot))[:n]
        if t == "random":
            return rng.sample(enemies, min(n, len(enemies)))
        if t == "all_enemies":
            return list(enemies)
        if t == "allies_lowest":
            return sorted(allies, key=lambda x: (x.hp / x.maxhp, x.slot))[:n]
        if t == "all_allies":
            return list(allies)
        return [u]

    def apply_fx(src: Unit, tgt: Unit, f: dict):
        if not tgt.alive:
            return None
        t = f["type"]
        if t == "stun":
            if tgt.boss:
                return {"id": tgt.id, "t": "resist"}
            if not any(e["t"] == "stun" for e in tgt.fx):
                tgt.fx.append({"t": "stun", "turns": 1, "v": 0})
        elif t == "shield":
            amt = int(src.maxhp * f["value"])
            ex = next((e for e in tgt.fx if e["t"] == "shield"), None)
            if ex:
                ex["amt"] += amt
                ex["turns"] = max(ex["turns"], f["turns"])
            else:
                tgt.fx.append({"t": "shield", "turns": f["turns"], "amt": amt, "v": 0})
        elif t == "burn":
            tgt.fx = [e for e in tgt.fx if e["t"] != "burn"]
            tgt.fx.append({"t": "burn", "turns": f["turns"], "amt": src.atk_eff() * f["value"], "v": 0})
        elif t in ("atk_up", "def_up", "def_down"):
            tgt.fx = [e for e in tgt.fx if e["t"] != t]
            tgt.fx.append({"t": t, "turns": f["turns"], "v": f["value"]})
        elif t == "energy":
            tgt.en = min(100, tgt.en + int(f["value"]))
        return {"id": tgt.id, "t": t}

    def deal(attacker: Unit, tgt: Unit, mult: float) -> dict:
        crit = rng.random() < attacker.crit
        raw = attacker.atk_eff() * mult * (CRIT_MULT if crit else 1.0) * rng.uniform(0.95, 1.05)
        dmg = max(1, int(raw * 500.0 / (500.0 + tgt.def_eff())))
        absorbed = 0
        for e in tgt.fx:
            if e["t"] == "shield" and dmg > 0:
                take = min(e["amt"], dmg)
                e["amt"] -= take
                dmg -= take
                absorbed += take
        tgt.fx = [e for e in tgt.fx if not (e["t"] == "shield" and e["amt"] <= 0)]
        tgt.hp -= dmg
        rec = {"id": tgt.id, "d": dmg, "c": crit, "a": absorbed, "x": not tgt.alive}
        if tgt.alive:
            tgt.en = min(100, tgt.en + ENERGY_HIT)
        else:
            tgt.fx = []
        return rec

    def cast(u: Unit, s: dict, kind: str) -> None:
        enemies, allies = alive("b" if u.side == "a" else "a"), alive(u.side)
        if s["heal"] > 0 and s["dmg"] == 0 and s["tgt"] == "allies_lowest" and all(a.hp >= a.maxhp for a in allies):
            s = FALLBACK
        targets = pick(u, s, enemies, allies)
        recs, fx_events = [], []
        for t in targets:
            rec = {"id": t.id}
            if s["dmg"] > 0:
                rec.update(deal(u, t, s["dmg"]))
            if s["heal"] > 0 and t.alive:
                amount = int(u.atk_eff() * s["heal"])
                healed = max(0, min(t.maxhp - t.hp, amount))
                t.hp += healed
                rec["h"] = healed
            recs.append(rec)
        for f in s["fx"]:
            if f["to"] == "hit":
                recipients = [t for t in targets]
            elif f["to"] == "self":
                recipients = [u]
            else:
                recipients = alive(u.side)
            for r in recipients:
                if f["chance"] < 1.0 and rng.random() > f["chance"]:
                    continue
                ev = apply_fx(u, r, f)
                if ev:
                    fx_events.append(ev)
        log.append({"k": "act", "a": u.id, "sk": kind, "n": s["name"], "tg": recs, "fx": fx_events, "st": snap()})

    def end_turn(u: Unit) -> None:
        for e in u.fx:
            e["turns"] -= 1
        u.fx = [e for e in u.fx if e["turns"] > 0]

    def take_turn(u: Unit) -> None:
        for e in [e for e in u.fx if e["t"] == "burn"]:
            dmg = max(1, int(e["amt"]))
            u.hp -= dmg
            if not u.alive:
                u.fx = []
            log.append({"k": "dot", "id": u.id, "d": dmg, "x": not u.alive, "st": snap()})
            if not u.alive:
                return
        if any(e["t"] == "stun" for e in u.fx):
            u.fx = [e for e in u.fx if e["t"] != "stun"]
            log.append({"k": "stun", "id": u.id, "st": snap()})
            end_turn(u)
            return
        if u.en >= 100:
            u.en = 0
            cast(u, u.d["ult"], "ult")
        else:
            u.en = min(100, u.en + ENERGY_ACT)
            cast(u, u.d["basic"], "basic")
        end_turn(u)

    rounds = 0
    for rnd in range(1, max_rounds + 1):
        rounds = rnd
        log.append({"k": "round", "n": rnd})
        order = sorted([x for x in units if x.alive], key=lambda x: (-x.spd, 0 if x.side == "a" else 1, x.slot))
        for u in order:
            if not u.alive:
                continue
            if not alive("a") or not alive("b"):
                break
            take_turn(u)
        if not alive("a") or not alive("b"):
            break
    win = bool(alive("a")) and not alive("b")
    log.append({"k": "end", "win": win, "rounds": rounds, "st": snap()})

    init = []
    for u in units:
        init.append({"id": u.id, "side": u.side, "slot": u.slot, "key": u.d["key"], "name": u.d["name"],
                     "cls": u.d["cls"], "fac": u.d["fac"], "rarity": u.d["rarity"], "level": u.d["level"],
                     "mon": bool(u.d.get("mon")), "boss": u.boss, "chapter": u.d.get("chapter"),
                     "maxhp": u.maxhp, "atk": u.atk, "def": u.df, "spd": u.spd})
    return {"units": init, "log": log, "win": win, "rounds": rounds}
