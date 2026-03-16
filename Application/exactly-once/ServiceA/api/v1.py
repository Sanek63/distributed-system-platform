import httpx
import logging
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from core.config import config


logger = logging.getLogger(__name__)
router = APIRouter()
_stats = {
    "total_requests": 0,
    "total_http_attempts": 0,
    "total_retries": 0,
    "succeeded_requests": 0,
    "failed_requests": 0,
}


class Message(BaseModel):
    message: str


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    _stats["total_requests"] += 1
    attempt_number = 0
    attempt_count = 3

    idempotency_key = str(uuid.uuid4())

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempt_count),
            wait=wait_fixed(0.2),
            reraise=True,
        ):
            attempt_number += 1
            _stats["total_http_attempts"] += 1

            with attempt:
                async with httpx.AsyncClient(timeout=2) as client:
                    response = await client.post(
                        f"{config.SERVICE_B_URL}/api/message-b",
                        json=payload.model_dump(),
                        headers={"Idempotency-Key": idempotency_key},
                    )
                    response.raise_for_status()
        _stats["succeeded_requests"] += 1
    except Exception:
        _stats["failed_requests"] += 1
        raise
    finally:
        retries_made = max(attempt_number - 1, 0)
        _stats["total_retries"] += retries_made
        logger.info("%s", _stats)

    return {"result": "ok"}
