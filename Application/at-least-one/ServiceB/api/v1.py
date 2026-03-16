import logging
import random
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()
_stats = {
    "total_requests": 0,
    "delayed_requests": 0,
    "failed_requests": 0,
    "successful_requests": 0,
}


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(payload: Message):
    _stats["total_requests"] += 1

    r = random.random()

    if r < 0.2:
        delay_s = random.uniform(1.2, 3.5)
        _stats["delayed_requests"] += 1
        await asyncio.sleep(delay_s)

    elif r < 0.3:
        _stats["failed_requests"] += 1
        logger.info("%s", _stats)
        raise HTTPException(status_code=500, detail="Random failure")

    _stats["successful_requests"] += 1
    logger.info("%s", _stats)

    return {"result": "ok"}
