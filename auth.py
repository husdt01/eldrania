"""Проверка Telegram Mini App initData по официальному алгоритму.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

import config
from services import GameError

DEV_USER_BASE = 1_000_000


def validate_init_data(init_data: str, bot_token: str, max_age: int, now: float | None = None) -> dict:
    """Возвращает данные пользователя Telegram или бросает GameError(401)."""
    if not init_data:
        raise GameError("unauthorized", "Откройте игру через Telegram.", 401)
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise GameError("unauthorized", "Данные Telegram повреждены.", 401)
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise GameError("unauthorized", "Подпись Telegram недействительна.", 401)
    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        auth_date = 0
    if (now if now is not None else time.time()) - auth_date > max_age:
        raise GameError("session_expired", "Сессия устарела. Закройте и снова откройте игру.", 401)
    try:
        user = json.loads(pairs.get("user", ""))
        uid = int(user["id"])
    except (ValueError, KeyError, TypeError):
        raise GameError("unauthorized", "В данных Telegram нет пользователя.", 401)
    name = " ".join(x for x in (user.get("first_name"), user.get("last_name")) if x) or user.get("username") or f"Игрок {uid}"
    return {"id": uid, "name": name[:40], "username": user.get("username")}


def authenticate(init_data: str | None, dev_user: str | None = None) -> dict:
    """Определяет игрока запроса. Тестовый профиль работает ТОЛЬКО при DEV_MODE=1."""
    if config.DEV_MODE and not init_data:
        n = 1
        if dev_user and dev_user.isdigit() and 0 < int(dev_user) < 1000:
            n = int(dev_user)
        return {"id": DEV_USER_BASE + n, "name": f"Тестовый игрок {n}", "username": f"dev{n}"}
    if not config.BOT_TOKEN:
        if config.DEV_MODE:  # initData есть, но проверить нечем — в DEV используем тестовый профиль
            return {"id": DEV_USER_BASE + 1, "name": "Тестовый игрок 1", "username": "dev1"}
        raise GameError("server_misconfigured", "На сервере не задан BOT_TOKEN.", 503)
    return validate_init_data(init_data or "", config.BOT_TOKEN, config.INITDATA_MAX_AGE)
