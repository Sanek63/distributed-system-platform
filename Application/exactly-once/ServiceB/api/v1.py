import logging
import asyncio
import random

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str
    messageId: str | None = Field(default=None)


_idempotency_store: dict[str, dict] = {}
_idempotency_lock = asyncio.Lock()


@router.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    message_id = payload.messageId or request.headers.get("Idempotency-Key")
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing messageId / Idempotency-Key")

    async with _idempotency_lock:
        cached = _idempotency_store.get(message_id)
        if cached is not None:
            logger.info(f"[service-b] idempotent hit messageId={message_id}")
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
        _idempotency_store[message_id] = result

    return result
