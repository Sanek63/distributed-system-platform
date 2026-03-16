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

    logger.info(
        "[scenario-1][request-%d] send request to service-b (no retry)",
        _stats["total_requests"],
    )

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(
                f"{config.SERVICE_B_URL}/api/message-b",
                json=payload.model_dump(),
            )
            logger.info(
                "[scenario-1][request-%d] service-b status=%d (status is logged, but no retries/checks are applied)",
                _stats["total_requests"],
                resp.status_code,
            )
    except httpx.HTTPError as exc:
        _stats["delivery_failures"] += 1
        logger.warning(
            "[scenario-1][request-%d] fire-and-forget delivery failed: %s",
            _stats["total_requests"],
            exc,
        )

    logger.info(
        "[scenario-1][at-most-once] total_requests=%d total_outbound_requests=%d retries=0 delivery_failures=%d",
        _stats["total_requests"],
        _stats["total_outbound_requests"],
        _stats["delivery_failures"],
    )

    return {"result": "ok"}
