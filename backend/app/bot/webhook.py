from fastapi import APIRouter, Request, Response
from aiogram.types import Update

from app.bot.bot import bot, dp
from app.config import settings

router = APIRouter()


@router.post("/bot/webhook")
async def bot_webhook(request: Request) -> Response:
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        return Response(status_code=403)
    body = await request.json()
    update = Update.model_validate(body, context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response()
