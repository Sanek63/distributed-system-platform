import logging
import asyncio
import random

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()

_idempotency_store: dict[str, dict] = {}
_idempotency_lock = asyncio.Lock()
_stats = {
    "total_requests": 0,
    "unique_processed": 0,
    "duplicate_hits": 0,
    "failed_requests": 0,
}


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(
    payload: Message,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    logger.info(
        "[scenario-3] got request from service-a key=%s message=%r",
        idempotency_key,
        payload.message,
    )

    async with _idempotency_lock:
        _stats["total_requests"] += 1
        if (cached := _idempotency_store.get(idempotency_key)) is not None:
            _stats["duplicate_hits"] += 1
            logger.info("[service-b] idempotent request with key=%s", idempotency_key)
            logger.info(
                "[scenario-3][service-b] total_requests=%d unique_processed=%d duplicate_hits=%d failed_requests=%d",
                _stats["total_requests"],
                _stats["unique_processed"],
                _stats["duplicate_hits"],
                _stats["failed_requests"],
            )
            return cached

    r = random.random()

    if r < 0.20:
        delay_s = random.uniform(1.2, 3.5)
        logger.info(f"[service-b] random delay {delay_s:.2f}s")
        await asyncio.sleep(delay_s)

    elif r < 0.30:
        async with _idempotency_lock:
            _stats["failed_requests"] += 1
            logger.info(
                "[scenario-3][service-b] total_requests=%d unique_processed=%d duplicate_hits=%d failed_requests=%d",
                _stats["total_requests"],
                _stats["unique_processed"],
                _stats["duplicate_hits"],
                _stats["failed_requests"],
            )
        raise HTTPException(status_code=500, detail="Random failure")

    result = {"status": "ok"}

    async with _idempotency_lock:
        _idempotency_store[idempotency_key] = result
        _stats["unique_processed"] += 1

    logger.info("send ok to service-a")
    logger.info(
        "[scenario-3][service-b] total_requests=%d unique_processed=%d duplicate_hits=%d failed_requests=%d",
        _stats["total_requests"],
        _stats["unique_processed"],
        _stats["duplicate_hits"],
        _stats["failed_requests"],
    )

    return result
