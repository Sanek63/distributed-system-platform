import httpx
import logging

from fastapi import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from core.config import config


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    attempt_number = 0
    attempt_count = 0

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempt_count),
        wait=wait_fixed(0.2),
        reraise=True,
    ):
        with attempt:
            attempt_number += 1

            logger.info(f"[{attempt_number}/{attempt_count}] send request to service-b")

            async with httpx.AsyncClient(timeout=1) as client:
                resp = await client.post(
                    f"{config.SERVICE_B_URL}/api/message-b",
                    json=payload.model_dump(),
                )
                resp.raise_for_status()

            logger.info("got response from service-b: %s", resp.text)

    return {"result": "ok"}
