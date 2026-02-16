import logging
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    logger.info(
        f"from={request.client.host}:{request.client.port} message={payload.message!r}"
    )
    return {"status": "ok", "received": payload.message}
