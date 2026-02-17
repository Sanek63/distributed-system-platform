import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message():
    logger.info("got request from service-a")
    ...

    raise HTTPException(status_code=502, detail="some error")
