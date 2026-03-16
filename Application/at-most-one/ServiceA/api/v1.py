import httpx
import logging

from fastapi import APIRouter
from pydantic import BaseModel
from core.config import config


router = APIRouter()
logger = logging.getLogger(__name__)
_stats = {
    "total_requests": 0,
    "total_outbound_requests": 0,
    "delivery_failures": 0,
}


class Message(BaseModel):
    message: str


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    _stats["total_requests"] += 1
    _stats["total_outbound_requests"] += 1

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{config.SERVICE_B_URL}/api/message-b",
                json=payload.model_dump(),
            )
    except httpx.HTTPError:
        _stats["delivery_failures"] += 1

    logger.info("%s", _stats)

    return {"result": "ok"}
