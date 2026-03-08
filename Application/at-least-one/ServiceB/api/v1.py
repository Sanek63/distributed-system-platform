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
async def receive_message(payload: Message):
    logger.info("got request from service-a")

    time.sleep(0.3)  # some operations
    
    logger.info("send ok to service-a")

    return {"result": "ok"}
