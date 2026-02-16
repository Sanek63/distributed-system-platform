import httpx
import logging
import uuid

from fastapi import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel, Field
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from core.config import config


logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    message: str
    messageId: str | None = Field(default=None)


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    attempt_no = 0

    if not payload.messageId:
        payload.messageId = str(uuid.uuid4())

    async with httpx.AsyncClient(timeout=2) as client:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_fixed(0.2),
                reraise=True,
            ):
                with attempt:
                    attempt_no += 1

                    logger.info(f"[service-a] attempt={attempt_no} call service-b messageId={payload.messageId}")

                    try:
                        resp = await client.post(
                            f"{config.SERVICE_B_URL}/api/message-b",
                            json=payload.model_dump(),
                            headers={"Idempotency-Key": payload.messageId},
                        )
                    except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                        logger.info(f"[service-a] timeout -> connection aborted: {type(e).__name__}")
                        raise HTTPException(status_code=504, detail="Timeout calling service-b")

        except Exception as e:
            logger.info(f"[service-a] forward failed after retries: {type(e).__name__}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward to ServiceB after retries: {type(e).__name__}",
            )

    logger.info(f"[service-a] forwarded OK status={resp.status_code} messageId={payload.messageId}")

    return {"result": "ok"}
