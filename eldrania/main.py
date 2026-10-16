"""Эльдрания — idle RPG для Telegram Mini App. REST API на FastAPI.

Запуск:  python -m uvicorn main:app --reload --host 127.0.0.1 --port 8765
Вся игровая логика живёт в services.py / game_logic.py; здесь только HTTP-слой.
"""
import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import auth
import config
import database
import services as S

log = logging.getLogger("eldrania")
STATIC_DIR = config.BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    if config.DEV_MODE:
        log.warning("DEV_MODE включён: вход без Telegram разрешён (тестовый профиль). Не используйте в production!")
    elif not config.BOT_TOKEN:
        log.error("BOT_TOKEN не задан и DEV_MODE выключен — авторизация работать не будет.")
    yield


app = FastAPI(title="Эльдрания", lifespan=lifespan,
              docs_url="/docs" if config.DEV_MODE else None, redoc_url=None,
              openapi_url="/openapi.json" if config.DEV_MODE else None)
app.add_middleware(GZipMiddleware, minimum_size=1024)


class NoCacheStatic(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


app.mount("/static", NoCacheStatic(directory=str(STATIC_DIR)), name="static")


# ------------------------------------------------------------ ошибки
def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(S.GameError)
async def game_error_handler(_: Request, exc: S.GameError):
    return _err(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return _err(422, "bad_request", "Некорректный запрос.")


@app.exception_handler(sqlite3.OperationalError)
async def db_busy_handler(_: Request, exc: sqlite3.OperationalError):
    log.exception("sqlite error")
    return _err(503, "db_busy", "База данных занята. Повторите через секунду.")


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    log.exception("unhandled error")
    return _err(500, "server_error", "Внутренняя ошибка сервера.")


# ------------------------------------------------------------ авторизация и транзакции
def current_tg(request: Request) -> dict:
    return auth.authenticate(request.headers.get("X-Telegram-Init-Data"), request.headers.get("X-Dev-User"))


def act(tg: dict, fn, *args, **kwargs) -> dict:
    """Одна транзакция: создать игрока при необходимости -> выполнить действие -> вернуть свежее состояние."""
    with database.transaction() as conn:
        pid = S.get_or_create_player(conn, tg)
        result = dict(fn(conn, pid, *args, **kwargs))
        result["state"] = S.build_state(conn, pid)
        return result


# ------------------------------------------------------------ схемы запросов
class SummonIn(BaseModel):
    count: Literal[1, 10]
    currency: Literal["tickets", "gems"]
    request_id: Optional[str] = Field(None, max_length=64)


class BattleIn(BaseModel):
    stage: int = Field(ge=1, le=1000)
    request_id: Optional[str] = Field(None, max_length=64)


class LevelIn(BaseModel):
    times: int = Field(1, ge=1, le=10)


class EquipIn(BaseModel):
    slot: Literal["weapon", "armor", "relic"]


class SquadIn(BaseModel):
    slots: list[Optional[str]] = Field(min_length=5, max_length=5)


class BuyIn(BaseModel):
    item_id: str = Field(max_length=40)


class FrameIn(BaseModel):
    frame: str = Field(max_length=20)


# ------------------------------------------------------------ маршруты
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/health")
def health():
    return {"ok": True, "dev_mode": config.DEV_MODE}


@app.get("/api/catalog")
def api_catalog():
    return S.catalog()


@app.get("/api/state")
def api_state(tg: dict = Depends(current_tg)):
    with database.transaction() as conn:
        pid = S.get_or_create_player(conn, tg)
        return S.build_state(conn, pid)


@app.post("/api/idle/claim")
def api_idle_claim(tg: dict = Depends(current_tg)):
    return act(tg, S.idle_claim)


@app.post("/api/summon")
def api_summon(body: SummonIn, tg: dict = Depends(current_tg)):
    return act(tg, S.summon, body.count, body.currency, body.request_id)


@app.post("/api/heroes/{key}/levelup")
def api_levelup(key: str, body: LevelIn, tg: dict = Depends(current_tg)):
    return act(tg, S.level_up, key, body.times)


@app.post("/api/heroes/{key}/equip")
def api_equip(key: str, body: EquipIn, tg: dict = Depends(current_tg)):
    return act(tg, S.equip_up, key, body.slot)


@app.post("/api/heroes/{key}/star")
def api_star(key: str, tg: dict = Depends(current_tg)):
    return act(tg, S.star_up, key)


@app.put("/api/squad")
def api_squad(body: SquadIn, tg: dict = Depends(current_tg)):
    return act(tg, S.set_squad, body.slots)


@app.get("/api/stage/{n}")
def api_stage(n: int, tg: dict = Depends(current_tg)):
    with database.transaction() as conn:
        pid = S.get_or_create_player(conn, tg)
        return S.stage_view(conn, pid, n)


@app.post("/api/battle")
def api_battle(body: BattleIn, tg: dict = Depends(current_tg)):
    return act(tg, S.battle, body.stage, body.request_id)


@app.post("/api/gift/claim")
def api_gift(tg: dict = Depends(current_tg)):
    return act(tg, S.claim_daily_gift)


@app.post("/api/quests/{qid}/claim")
def api_quest_claim(qid: str, tg: dict = Depends(current_tg)):
    return act(tg, S.claim_quest, qid)


@app.post("/api/shop/buy")
def api_shop_buy(body: BuyIn, tg: dict = Depends(current_tg)):
    return act(tg, S.shop_buy, body.item_id)


@app.post("/api/cosmetics/frame")
def api_frame(body: FrameIn, tg: dict = Depends(current_tg)):
    return act(tg, S.set_frame, body.frame)
