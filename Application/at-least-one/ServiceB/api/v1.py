import logging
import time
import random
import asyncio

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    logger.info("got request from service-a")

    r = random.random()

    if r < 0.2:
        delay_s = random.uniform(1.2, 3.5)
        logger.info("random delay %.2fs", delay_s)
        await asyncio.sleep(delay_s)

    elif r < 0.3:
        logger.info("[service-b] random failure 500")
        raise HTTPException(status_code=500, detail="Random failure")

    logger.info("send ok to service-a")

    return {"result": "ok"}
