import logging
import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()
_stats = {
    "total_requests": 0,
    "accepted_requests": 0,
    "failed_requests": 0,
}


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(payload: Message):
    _stats["total_requests"] += 1
    logger.info(
        "[scenario-1] got request from service-a message=%r",
        payload.message,
    )

    if random.random() < 0.35:
        _stats["failed_requests"] += 1
        logger.info(
            "[scenario-1][at-most-once] total_requests=%d accepted_requests=%d failed_requests=%d",
            _stats["total_requests"],
            _stats["accepted_requests"],
            _stats["failed_requests"],
        )
        raise HTTPException(status_code=502, detail="some error")

    _stats["accepted_requests"] += 1
    logger.info("[scenario-1] accepted request")
    logger.info(
        "[scenario-1][at-most-once] total_requests=%d accepted_requests=%d failed_requests=%d",
        _stats["total_requests"],
        _stats["accepted_requests"],
        _stats["failed_requests"],
    )
    return {"result": "ok"}
