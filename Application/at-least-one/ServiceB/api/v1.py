import logging
import time
import random
import asyncio

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

r = random.random()
logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    logger.info(
        f"[service-b][in] {request.method} {request.url.path} "
        f"traceparent={request.headers.get('traceparent')} baggage={request.headers.get('baggage')}"
    )

    if r < 0.20:
        delay_s = random.uniform(1.2, 3.5)
        logger.info(f"[service-b] random delay {delay_s:.2f}s")
        await asyncio.sleep(delay_s)
    elif r < 0.30:
        logger.info("[service-b] random failure 500")
        raise HTTPException(status_code=500, detail="Random failure")

    logger.info(f"[service-b] received message={payload.message!r} at={time.strftime('%Y-%m-%d %H:%M:%S')}")

    return {"status": "ok", "received": payload.message}
