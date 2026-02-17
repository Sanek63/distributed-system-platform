import httpx
import logging

from fastapi import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from core.config import config


router = APIRouter()
logger = logging.getLogger(__name__)


class Message(BaseModel):
    message: str


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    logger.info('send request to service-b')

    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            resp = await client.post(
                f"{config.SERVICE_B_URL}/api/message-b",
                json=payload.model_dump(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward to ServiceB: {type(e).__name__}",
            )

    logger.info("got response from service-b: %s", resp.text)

    return {"result": "ok"}
