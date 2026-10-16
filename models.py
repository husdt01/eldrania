"""Схема базы данных SQLite.

Баланс защищён CHECK-ограничениями: даже при ошибке в коде валюта не уйдёт в минус.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id           INTEGER NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    username        TEXT,
    gold            INTEGER NOT NULL DEFAULT 0 CHECK (gold    >= 0),
    exp             INTEGER NOT NULL DEFAULT 0 CHECK (exp     >= 0),
    gems            INTEGER NOT NULL DEFAULT 0 CHECK (gems    >= 0),
    tickets         INTEGER NOT NULL DEFAULT 0 CHECK (tickets >= 0),
    account_xp      INTEGER NOT NULL DEFAULT 0,
    stage_cleared   INTEGER NOT NULL DEFAULT 0,
    pity_epic       INTEGER NOT NULL DEFAULT 0,
    pity_legend     INTEGER NOT NULL DEFAULT 0,
    summons_total   INTEGER NOT NULL DEFAULT 0,
    last_idle_claim INTEGER NOT NULL,
    last_gift_day   TEXT,
    frame           TEXT    NOT NULL DEFAULT 'none',
    cosmetics       TEXT    NOT NULL DEFAULT '[]',
    created_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS heroes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    hero_key   TEXT    NOT NULL,
    level      INTEGER NOT NULL DEFAULT 1,
    stars      INTEGER NOT NULL DEFAULT 0,
    shards     INTEGER NOT NULL DEFAULT 0 CHECK (shards >= 0),
    eq_weapon  INTEGER NOT NULL DEFAULT 0,
    eq_armor   INTEGER NOT NULL DEFAULT 0,
    eq_relic   INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    UNIQUE (player_id, hero_key)
);

CREATE TABLE IF NOT EXISTS squad (
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    slot      INTEGER NOT NULL CHECK (slot BETWEEN 0 AND 4),
    hero_key  TEXT    NOT NULL,
    PRIMARY KEY (player_id, slot),
    UNIQUE (player_id, hero_key)
);

CREATE TABLE IF NOT EXISTS stage_clears (
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    stage     INTEGER NOT NULL,
    clears    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, stage)
);

CREATE TABLE IF NOT EXISTS daily_quests (
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    day       TEXT    NOT NULL,
    quest_id  TEXT    NOT NULL,
    progress  INTEGER NOT NULL DEFAULT 0,
    claimed   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, day, quest_id)
);

-- Журнал игровых событий + хранилище результатов для идемпотентных запросов.
-- idem_key: повтор запроса с тем же request_id вернёт сохранённый результат, а не выдаст награду заново.
-- Здесь же в будущем хранятся charge_id платежей Telegram Stars (уникальность защитит от двойной выдачи).
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    kind       TEXT    NOT NULL,
    idem_key   TEXT,
    payload    TEXT    NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE (player_id, kind, idem_key)
);
CREATE INDEX IF NOT EXISTS idx_events_player ON events(player_id, id);
"""
