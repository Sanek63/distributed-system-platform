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

    if random.random() < 0.35:
        _stats["failed_requests"] += 1
        logger.info("%s", _stats)
        raise HTTPException(status_code=502, detail="some error")

    _stats["accepted_requests"] += 1
    logger.info("%s", _stats)
    return {"result": "ok"}
