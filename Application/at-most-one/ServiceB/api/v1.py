import logging

from fastapi import APIRouter
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-b")
async def receive_message():
    logger.info("got request from service-a")
    ...
    logger.info("send ok to service-a")

    return {"result": "ok"}
