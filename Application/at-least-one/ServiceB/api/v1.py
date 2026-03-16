import logging
import time
import random
import asyncio

from fastapi import APIRouter, Request, HTTPException
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
async def receive_message(payload: Message, request: Request):
    _stats["total_requests"] += 1
    logger.info("got request from service-a")

    r = random.random()

    if r < 0.2:
        delay_s = random.uniform(1.2, 3.5)
        _stats["delayed_requests"] += 1
        logger.info("random delay %.2fs", delay_s)
        await asyncio.sleep(delay_s)

    elif r < 0.3:
        _stats["failed_requests"] += 1
        logger.info(
            "[scenario-2][service-b] total_requests=%d successful_requests=%d failed_requests=%d delayed_requests=%d",
            _stats["total_requests"],
            _stats["successful_requests"],
            _stats["failed_requests"],
            _stats["delayed_requests"],
        )
        raise HTTPException(status_code=500, detail="Random failure")

    _stats["successful_requests"] += 1
    logger.info("send ok to service-a")
    logger.info(
        "[scenario-2][service-b] total_requests=%d successful_requests=%d failed_requests=%d delayed_requests=%d",
        _stats["total_requests"],
        _stats["successful_requests"],
        _stats["failed_requests"],
        _stats["delayed_requests"],
    )

    return {"result": "ok"}
