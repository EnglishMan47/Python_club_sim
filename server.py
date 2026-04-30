"""
L3 - Сервер
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import core

# Логирование в файл
ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "simulation.log"

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
_file_handler.setLevel(logging.DEBUG)

logger = logging.getLogger("cyberzone")
logger.setLevel(logging.DEBUG)
logger.addHandler(_file_handler)
logger.propagate = False

# Изменяемое состояние мира — только здесь, на L3
# Core видит эти значения как аргументы чистых функций
STATE: core.World = core.initial_state(seed=42)
SPEED: int        = 1
SPEED_OPTIONS     = (1, 2, 5, 10, 20, 60)
CLIENTS: Set[WebSocket] = set()

WEB = ROOT

logger.info("CYBER ZONE сервер инициализирован. Log: %s", LOG_FILE)

# Валидация входящих сообщений
def _validate_command(msg: object) -> tuple[bool, str]:
    """Возвращает (ok, reason). Проверяет структуру команды перед применением."""
    if not isinstance(msg, dict):
        return False, f"ожидался dict, получен {type(msg).__name__}"
    action = msg.get("action")
    if not isinstance(action, str):
        return False, f"поле 'action' должно быть строкой, получено {type(action).__name__}"
    if action not in core.VALID_ACTIONS:
        return False, f"неизвестная команда '{action}'"
    if action == "speed":
        value = msg.get("value")
        try:
            value = int(value)
        except (TypeError, ValueError):
            return False, f"поле 'value' для speed должно быть числом, получено {value!r}"
        if value not in SPEED_OPTIONS:
            return False, f"недопустимая скорость {value}, допустимые: {SPEED_OPTIONS}"
    return True, ""

# Жизненный цикл приложения — симуляционный цикл как фоновая задача
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI lifespan: запуск симуляционного цикла")
    task = asyncio.create_task(_simulation_loop())
    try:
        yield
    finally:
        task.cancel()
        logger.info("FastAPI lifespan: симуляционный цикл остановлен")


app = FastAPI(lifespan=lifespan)

if WEB.exists():
    app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
async def index():
    return FileResponse(WEB / "index.html")


@app.get("/style.css")
async def stylesheet():
    return FileResponse(WEB / "style.css", media_type="text/css")


# WebSocket
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    CLIENTS.add(ws)
    client_id = id(ws)
    logger.info("WS подключён: client#%d (всего: %d)", client_id, len(CLIENTS))
    await _safe_send(ws, _snapshot_payload())
    try:
        while True:
            text = await ws.receive_text()
            msg = _parse_message(text, client_id)
            if msg is None:
                continue
            ok, reason = _validate_command(msg)
            if not ok:
                logger.warning("WS client#%d: невалидная команда — %s | raw=%r", client_id, reason, text[:200])
                continue
            _handle_command(msg)
            await _broadcast(_snapshot_payload())
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("WS client#%d: необработанная ошибка — %s", client_id, exc, exc_info=True)
    finally:
        CLIENTS.discard(ws)
        logger.info("WS отключён: client#%d (всего: %d)", client_id, len(CLIENTS))


def _parse_message(text: str, client_id: int) -> dict | None:
    """Парсит JSON; логирует и возвращает None при ошибке."""
    if not isinstance(text, str) or not text.strip():
        logger.warning("WS client#%d: пустое сообщение", client_id)
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("WS client#%d: невалидный JSON — %s | raw=%r", client_id, exc, text[:200])
        return None

# Обработка команд
def _handle_command(msg: dict) -> None:
    """Применяет команду пользователя. Единственное место мутации STATE."""
    global STATE, SPEED
    action = msg.get("action")

    if action == "speed":
        value = int(msg.get("value", 1))
        if value in SPEED_OPTIONS:
            SPEED = value
            logger.info("Скорость изменена: %d×", SPEED)
        return

    prev_running = STATE.running
    prev_day = STATE.day
    STATE = core.apply_command(STATE, msg)

    # Логируем значимые события симуляции
    if action == "start" and STATE.running and not prev_running:
        logger.info("Симуляция запущена. День %d", STATE.day)
    elif action == "pause":
        logger.info("Симуляция: %s", "пауза" if STATE.paused else "продолжение")
    elif action == "reset":
        logger.info("Симуляция сброшена")
    elif action == "new_day":
        if STATE.day != prev_day:
            logger.info("Новый день: %d", STATE.day)


# Симуляционный цикл — каждую итерацию = 1 минута симуляции
async def _simulation_loop() -> None:
    global STATE
    prev_running = False
    while True:
        interval = max(0.016, 1.0 / SPEED)
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return

        if STATE.running and not STATE.paused:
            STATE = core.tick(STATE)
            await _broadcast(_snapshot_payload())

            # Логируем закрытие дня
            if prev_running and not STATE.running:
                logger.info(
                    "День %d завершён. Выручка: %.0f₽, Расходы: %.0f₽",
                    STATE.day,
                    STATE.revenue + STATE.food_revenue,
                    (core.CONFIG["rent"] + core.CONFIG["electric"] +
                     core.CONFIG["wage_admin"] + 2*core.CONFIG["wage_worker"] +
                     STATE.expenses + STATE.food_stock.purchase_cost),
                )
        prev_running = STATE.running


def _snapshot_payload() -> str:
    d = core.world_to_dict(STATE, log_tail=200, chat_tail=150)
    d["speed"]         = SPEED
    d["speed_options"] = list(SPEED_OPTIONS)
    return json.dumps(d, ensure_ascii=False)


async def _safe_send(ws: WebSocket, data: str) -> None:
    try:
        await ws.send_text(data)
    except Exception:
        CLIENTS.discard(ws)


async def _broadcast(data: str) -> None:
    if not CLIENTS:
        return
    await asyncio.gather(
        *(_safe_send(ws, data) for ws in list(CLIENTS)),
        return_exceptions=True,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
