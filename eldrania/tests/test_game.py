"""Тесты игровой логики и сервисного слоя (только стандартная библиотека).
Запуск из корня проекта:  python -m unittest discover -s tests -v
"""
import hashlib
import hmac
import json
import os
import random
import sys
import tempfile
import time
import unittest
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config  # noqa: E402

_tmp = tempfile.mkdtemp()
config.DB_PATH = os.path.join(_tmp, "test.db")

import auth  # noqa: E402
import database  # noqa: E402
import game_data as D  # noqa: E402
import game_logic as L  # noqa: E402
import services as S  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        if os.path.exists(config.DB_PATH):
            os.remove(config.DB_PATH)
        database.init_db()
        S._clock = time.time
        self.tg = {"id": 777, "name": "Тест", "username": "t"}
        with database.transaction() as c:
            self.pid = S.get_or_create_player(c, self.tg)

    def tx(self, fn, *a, **kw):
        with database.transaction() as c:
            return fn(c, self.pid, *a, **kw)

    def player(self):
        with database.transaction() as c:
            return S.get_player(c, self.pid)

    def set_player(self, **cols):
        with database.transaction() as c:
            c.execute("UPDATE players SET " + ",".join(f"{k}=?" for k in cols) + " WHERE id=?", (*cols.values(), self.pid))

    def grant_hero(self, key, level=1):
        with database.transaction() as c:
            c.execute("INSERT OR IGNORE INTO heroes (player_id,hero_key,level,created_at) VALUES (?,?,?,?)",
                      (self.pid, key, level, S.now()))


class TestStart(Base):
    def test_new_player(self):
        with database.transaction() as c:
            st = S.build_state(c, self.pid)
        self.assertEqual(len(st["heroes"]), 3)
        self.assertEqual([k for k in st["squad"]["slots"] if k], D.STARTER_HEROES)
        self.assertEqual(st["player"]["tickets"], 10)
        self.assertGreater(st["idle"]["gold"], 0)  # стартовый запас idle доступен сразу
        with database.transaction() as c:  # повторный вход не создаёт второго игрока
            self.assertEqual(S.get_or_create_player(c, self.tg), self.pid)
            self.assertEqual(c.execute("SELECT COUNT(*) n FROM players").fetchone()["n"], 1)


class TestIdle(Base):
    def test_claim_once(self):
        r = self.tx(S.idle_claim)
        self.assertGreater(r["claimed"]["gold"], 0)
        with self.assertRaises(S.GameError) as cm:
            self.tx(S.idle_claim)
        self.assertEqual(cm.exception.code, "idle_empty")

    def test_cap(self):
        self.set_player(last_idle_claim=S.now() - 100 * 3600)
        r = self.tx(S.idle_claim)
        self.assertEqual(r["seconds"], 12 * 3600)
        self.assertEqual(r["claimed"]["gold"], 900 * 12)

    def test_time_passes_via_server_clock(self):
        self.tx(S.idle_claim)
        base = time.time()
        S._clock = lambda: base + 3600
        r = self.tx(S.idle_claim)
        self.assertAlmostEqual(r["claimed"]["gold"], 900, delta=5)


class TestSummon(Base):
    def test_x10_spends_and_grants(self):
        r = self.tx(S.summon, 10, "tickets", "rq1")
        self.assertEqual(len(r["results"]), 10)
        p = self.player()
        self.assertEqual(p["tickets"], 0)
        self.assertEqual(p["summons_total"], 10)
        with database.transaction() as c:
            self.assertEqual(S.build_state(c, self.pid)["squad"]["slots"].count(None), 0)  # отряд автозаполнен

    def test_insufficient_changes_nothing(self):
        self.tx(S.summon, 10, "tickets", "a")
        before = self.player()
        with self.assertRaises(S.GameError):
            self.tx(S.summon, 1, "tickets", "b")
        self.assertEqual(before, self.player())

    def test_idempotent(self):
        self.tx(S.summon, 1, "gems", "same")
        gems = self.player()["gems"]
        r = self.tx(S.summon, 1, "gems", "same")
        self.assertTrue(r.get("replayed"))
        self.assertEqual(self.player()["gems"], gems)

    def test_duplicates_give_shards(self):
        rng = random.Random(1)
        total = 0
        for i in range(30):
            self.set_player(tickets=5, pity_epic=0, pity_legend=0)
            r = self.tx(S.summon, 1, "tickets", f"r{i}", rng)
            total += r["results"][0]["shards"]
        self.assertGreater(total, 0)
        with database.transaction() as c:
            self.assertGreater(c.execute("SELECT SUM(shards) s FROM heroes").fetchone()["s"], 0)

    def test_hard_pity(self):
        self.set_player(tickets=5, pity_legend=D.PITY_LEGEND_HARD - 1)
        r = self.tx(S.summon, 1, "tickets", "p")
        self.assertEqual(r["results"][0]["rarity"], "legendary")
        self.assertEqual(self.player()["pity_legend"], 0)

    def test_epic_pity(self):
        self.set_player(tickets=5, pity_epic=D.PITY_EPIC_EVERY - 1, pity_legend=0)
        r = self.tx(S.summon, 1, "tickets", "p")
        self.assertIn(r["results"][0]["rarity"], ("epic", "legendary"))

    def test_rates_sum_and_distribution(self):
        for pe in range(0, 12):
            for pl in range(0, 52, 5):
                self.assertAlmostEqual(sum(L.summon_rates(pe, pl).values()), 1.0, places=9)
        self.assertEqual(L.summon_rates(0, 0), {k: v for k, v in L.summon_rates(0, 0).items()})
        base = L.summon_rates(0, 0)
        for k, v in D.SUMMON_RATES.items():
            self.assertAlmostEqual(base[k], v, places=9)
        rng = random.Random(5)
        pe = pl = 0
        counts = {"common": 0, "rare": 0, "epic": 0, "legendary": 0}
        gap = worst = 0
        N = 200000
        for _ in range(N):
            r = L.roll_rarity(rng, pe, pl)
            pe, pl = L.advance_pity(pe, pl, r)
            counts[r] += 1
            gap = 0 if r == "legendary" else gap + 1
            worst = max(worst, gap)
        self.assertLess(worst, D.PITY_LEGEND_HARD)
        self.assertTrue(0.025 <= counts["legendary"] / N <= 0.045, counts)
        self.assertGreater(counts["common"] / N, 0.25)


class TestUpgrades(Base):
    def test_level_up_and_block(self):
        before = self.player()
        r = self.tx(S.level_up, "brann", 1)
        self.assertEqual(r["level"], 2)
        cost = L.level_cost(1)
        after = self.player()
        self.assertEqual(before["gold"] - after["gold"], cost["gold"])
        self.assertEqual(before["exp"] - after["exp"], cost["exp"])
        self.set_player(gold=0)
        with self.assertRaises(S.GameError) as cm:
            self.tx(S.level_up, "brann", 1)
        self.assertEqual(cm.exception.code, "insufficient")

    def test_level_cap_and_stars(self):
        self.set_player(gold=10**7, exp=10**7)
        with database.transaction() as c:
            c.execute("UPDATE heroes SET level=20 WHERE hero_key='brann' AND player_id=?", (self.pid,))
        with self.assertRaises(S.GameError):
            self.tx(S.level_up, "brann", 1)
        with self.assertRaises(S.GameError):
            self.tx(S.star_up, "brann")  # нет фрагментов
        with database.transaction() as c:
            c.execute("UPDATE heroes SET shards=50 WHERE hero_key='brann' AND player_id=?", (self.pid,))
        self.tx(S.star_up, "brann")
        self.assertEqual(self.tx(S.level_up, "brann", 1)["level"], 21)

    def test_equipment(self):
        gold = self.player()["gold"]
        self.tx(S.equip_up, "brann", "weapon")
        self.assertEqual(gold - self.player()["gold"], L.equip_cost(0))
        with self.assertRaises(S.GameError):
            self.tx(S.equip_up, "brann", "banana")
        with self.assertRaises(S.GameError):
            self.tx(S.level_up, "mage_not_owned", 1)

    def test_stats_grow(self):
        b = D.HEROES["brann"]["base"]
        s1 = L.hero_stats(b, 1, 0, {})
        self.assertGreater(L.hero_stats(b, 5, 0, {})["atk"], s1["atk"])
        self.assertGreater(L.hero_stats(b, 1, 0, {"weapon": 3})["atk"], s1["atk"])
        self.assertGreater(L.hero_stats(b, 1, 2, {})["hp"], s1["hp"])


class TestSquad(Base):
    def test_rules(self):
        self.grant_hero("tarn")
        with self.assertRaises(S.GameError) as cm:
            self.tx(S.set_squad, ["tarn", "tarn", None, None, None])
        self.assertEqual(cm.exception.code, "duplicate_hero")
        with self.assertRaises(S.GameError):
            self.tx(S.set_squad, ["nox", None, None, None, None])  # не в коллекции
        with self.assertRaises(S.GameError):
            self.tx(S.set_squad, [None] * 5)
        self.tx(S.set_squad, ["tarn", None, "brann", "lyra", "mira"])
        with database.transaction() as c:
            self.assertEqual(S.squad_slots(c, self.pid), ["tarn", None, "brann", "lyra", "mira"])

    def test_faction_bonus(self):
        b = L.squad_bonuses(["dawn", "dawn", "dawn", "dusk", "tide"])
        self.assertEqual(set(b), {"dawn"})
        self.assertEqual(b["dawn"]["hp"], 0.10)
        self.assertEqual(L.squad_bonuses(["dawn", "dusk", "tide"]), {})


class TestBattle(Base):
    def test_win_progress_and_rewards(self):
        before = self.player()
        r = self.tx(S.battle, 1, "b1")
        self.assertTrue(r["result"]["win"])
        self.assertEqual(r["log"][-1]["k"], "end")
        p = self.player()
        self.assertEqual(p["stage_cleared"], 1)
        self.assertEqual(p["gold"] - before["gold"], r["result"]["rewards"]["gold"])
        self.assertGreater(r["result"]["rewards"]["gems"], 0)

    def test_locked_stage(self):
        with self.assertRaises(S.GameError) as cm:
            self.tx(S.battle, 3, "x")
        self.assertEqual(cm.exception.code, "stage_locked")
        with self.assertRaises(S.GameError):
            self.tx(S.battle, 9999, "x")

    def test_idempotent_battle(self):
        self.tx(S.battle, 1, "same")
        gold = self.player()["gold"]
        r = self.tx(S.battle, 1, "same")
        self.assertTrue(r.get("replayed"))
        self.assertEqual(self.player()["gold"], gold)

    def test_repeat_gives_less_than_first(self):
        first = self.tx(S.battle, 1, "a")["result"]["rewards"]
        again = self.tx(S.battle, 1, "b")["result"]["rewards"]
        self.assertLess(again["gold"], first["gold"])
        self.assertEqual(again["gems"], 0)

    def test_loss_gives_nothing_and_no_progress(self):
        self.set_player(stage_cleared=29)
        before = self.player()
        r = self.tx(S.battle, 30, "l")
        self.assertFalse(r["result"]["win"])
        p = self.player()
        self.assertEqual((p["gold"], p["stage_cleared"]), (before["gold"], 29))

    def test_outcome_depends_on_strength_and_is_deterministic(self):
        def team(lvl):
            out = []
            for k in ["brann", "tarn", "lyra", "seraphine", "kaera"]:
                t = D.HEROES[k]
                out.append({"key": k, "name": t["name"], "cls": t["cls"], "fac": t["faction"], "rarity": t["rarity"],
                            "level": lvl, "basic": t["basic"], "ult": t["ult"],
                            **L.hero_stats(t["base"], lvl, 0, {})})
            return out
        a = L.simulate(team(10), L.enemy_team(15), 42)
        b = L.simulate(team(10), L.enemy_team(15), 42)
        self.assertEqual(a["log"], b["log"])
        wins = lambda lvl: sum(L.simulate(team(lvl), L.enemy_team(15), s)["win"] for s in range(20))
        self.assertLess(wins(2), wins(25))
        self.assertEqual(wins(2), 0)
        self.assertEqual(wins(25), 20)

    def test_battle_has_ults_heals_and_ends(self):
        self.tx(S.summon, 10, "tickets", "s")
        r = self.tx(S.battle, 1, "z")
        kinds = {e["sk"] for e in r["log"] if e["k"] == "act"}
        self.assertIn("basic", kinds)
        self.assertLessEqual(r["result"]["rounds"], L.MAX_ROUNDS)
        r2 = L.simulate(S.player_units  and [], [], 1)
        self.assertFalse(r2["win"])

    def test_sim_log_contains_ult_and_heal(self):
        def u(key, lvl=30):
            t = D.HEROES[key]
            return {"key": key, "name": t["name"], "cls": t["cls"], "fac": t["faction"], "rarity": t["rarity"],
                    "level": lvl, "basic": t["basic"], "ult": t["ult"], **L.hero_stats(t["base"], lvl, 0, {})}
        res = L.simulate([u("brann"), u("seraphine"), u("morvena"), u("kaera"), u("alaric")], L.enemy_team(30), 3)
        acts = [e for e in res["log"] if e["k"] == "act"]
        self.assertTrue(any(e["sk"] == "ult" for e in acts))
        self.assertTrue(any(t.get("h") for e in acts for t in e["tg"]))
        self.assertTrue(any(t.get("d") for e in acts for t in e["tg"]))


class TestEconomyMisc(Base):
    def test_daily_gift_once(self):
        g = self.player()["gems"]
        self.tx(S.claim_daily_gift)
        self.assertEqual(self.player()["gems"], g + D.DAILY_GIFT["gems"])
        with self.assertRaises(S.GameError):
            self.tx(S.claim_daily_gift)

    def test_quests(self):
        with self.assertRaises(S.GameError):
            self.tx(S.claim_quest, "q_idle")
        self.tx(S.idle_claim)
        e = self.player()["exp"]
        self.tx(S.claim_quest, "q_idle")
        self.assertEqual(self.player()["exp"], e + 1500)
        with self.assertRaises(S.GameError):
            self.tx(S.claim_quest, "q_idle")

    def test_shop(self):
        with self.assertRaises(S.GameError) as cm:
            self.tx(S.shop_buy, "stars_gems")
        self.assertEqual(cm.exception.code, "payments_disabled")
        p = self.player()
        self.tx(S.shop_buy, "tickets_1")
        q = self.player()
        self.assertEqual((q["gems"], q["tickets"]), (p["gems"] - 150, p["tickets"] + 1))
        self.set_player(gems=10)
        with self.assertRaises(S.GameError):
            self.tx(S.shop_buy, "gold_s")
        self.set_player(gems=1000)
        self.tx(S.shop_buy, "frame_gold")
        with self.assertRaises(S.GameError):
            self.tx(S.shop_buy, "frame_gold")
        self.assertEqual(self.player()["frame"], "gold")

    def test_db_blocks_negative_balance(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            with database.transaction() as c:
                c.execute("UPDATE players SET gold=-5 WHERE id=?", (self.pid,))

    def test_catalog_and_state_json(self):
        json.dumps(S.catalog())
        with database.transaction() as c:
            json.dumps(S.build_state(c, self.pid))
        self.assertGreaterEqual(len(D.HEROES), 12)
        for rar in D.RARITIES:
            self.assertTrue(any(h["rarity"] == rar for h in D.HEROES.values()))


class TestAuth(unittest.TestCase):
    TOKEN = "123456:TEST-TOKEN"

    def make(self, user, auth_date=None, tamper=False):
        data = {"auth_date": str(auth_date or int(time.time())), "query_id": "AAH", "user": json.dumps(user)}
        check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret = hmac.new(b"WebAppData", self.TOKEN.encode(), hashlib.sha256).digest()
        data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if tamper:
            data["user"] = json.dumps({**user, "id": 1})
        return urlencode(data)

    def test_valid(self):
        u = auth.validate_init_data(self.make({"id": 42, "first_name": "Аня"}), self.TOKEN, 3600)
        self.assertEqual(u["id"], 42)

    def test_tampered_expired_empty(self):
        for bad in (self.make({"id": 42}, tamper=True), self.make({"id": 42}, auth_date=1000), "", "a=b"):
            with self.assertRaises(S.GameError):
                auth.validate_init_data(bad, self.TOKEN, 3600)

    def test_dev_mode_gate(self):
        old = (config.DEV_MODE, config.BOT_TOKEN)
        try:
            config.DEV_MODE, config.BOT_TOKEN = False, self.TOKEN
            with self.assertRaises(S.GameError):
                auth.authenticate(None, "1")  # без DEV_MODE тестовый вход невозможен
            config.DEV_MODE = True
            self.assertEqual(auth.authenticate(None, "2")["id"], auth.DEV_USER_BASE + 2)
            config.DEV_MODE, config.BOT_TOKEN = False, ""
            with self.assertRaises(S.GameError):
                auth.authenticate("x=y")
        finally:
            config.DEV_MODE, config.BOT_TOKEN = old


if __name__ == "__main__":
    unittest.main()
