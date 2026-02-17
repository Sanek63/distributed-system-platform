import logging
import asyncio
import random

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()

_idempotency_store: dict[str, dict] = {}
_idempotency_lock = asyncio.Lock()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    logger.info("got request from service-a")

    async with _idempotency_lock:
        if (cached := _idempotency_store.get(idempotency_key)) is not None:
            logger.info(f"[service-b] idempotent request with key={idempotency_key}")
            return cached

    r = random.random()

    if r < 0.20:
        delay_s = random.uniform(1.2, 3.5)
        logger.info(f"[service-b] random delay {delay_s:.2f}s")
        await asyncio.sleep(delay_s)

    elif r < 0.30:
        logger.info("[service-b] random failure 500")
        raise HTTPException(status_code=500, detail="Random failure")

    result = {"status": "ok"}

    async with _idempotency_lock:
        _idempotency_store[idempotency_key] = result

    logger.info("send ok to service-a")

    return result
