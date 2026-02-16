import httpx

from fastapi import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from core.config import config


router = APIRouter()


class Message(BaseModel):
    message: str


@router.post("/api/message-a")
async def accept_and_forward(payload: Message):
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            await client.post(
                f"{config.SERVICE_B_URL}/api/message-b",
                json=payload.model_dump(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward to ServiceB: {type(e).__name__}",
            )

    return {"result": "ok"}
