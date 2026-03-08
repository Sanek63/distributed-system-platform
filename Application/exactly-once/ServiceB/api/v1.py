import logging
import asyncio
import time

from fastapi import APIRouter, Header
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()

_idempotency_store: dict[str, dict] = {}
_idempotency_lock = asyncio.Lock()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(idempotency_key: str = Header(alias="Idempotency-Key")):
    logger.info("got request from service-a")

    async with _idempotency_lock:
        if (cached := _idempotency_store.get(idempotency_key)) is not None:
            logger.info(f"[service-b] idempotent request with key={idempotency_key}")
            return cached

    time.sleep(0.3)  # some operations

    result = {"status": "ok"}
    async with _idempotency_lock:
        _idempotency_store[idempotency_key] = result

    logger.info("send ok to service-a")

    return result
