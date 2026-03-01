from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.bot import bot, dp
from app.config import settings
from app.models.category import Category
from app.models.listing import Listing, ListingStatus
from app.models.user import User

router = Router()
dp.include_router(router)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_telegram_ids


async def notify_admins_new_listing(
    listing_id: str, title: str, username: str | None
) -> None:
    """Send notification to all admins when a new listing is created."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить", callback_data=f"approve:{listing_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"reject:{listing_id}"
                ),
            ]
        ]
    )
    text = f"📦 Новое объявление: <b>{title}</b>\nОт: @{username or 'unknown'}"
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=keyboard)
        except Exception:
            pass  # Admin may have blocked the bot


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Stella",
                    web_app=WebAppInfo(url=settings.app_base_url),
                )
            ]
        ]
    )
    await message.answer(
        "Добро пожаловать в <b>Stella</b>! 🌟\n\nНажмите кнопку ниже, чтобы открыть маркетплейс.",
        reply_markup=keyboard,
    )


# ---------------------------------------------------------------------------
# /pending — list pending listings (admin only)
# ---------------------------------------------------------------------------


@router.message(Command("pending"))
async def cmd_pending(message: Message, sessionmaker: async_sessionmaker) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    async with sessionmaker() as session:
        result = await session.execute(
            select(Listing).where(Listing.status == ListingStatus.pending)
        )
        listings = result.scalars().all()

    if not listings:
        await message.answer("✅ Нет объявлений на проверке.")
        return

    lines = ["📦 Ожидают проверки:\n"]
    for i, listing in enumerate(listings, start=1):
        lines.append(f"{i}. {listing.title} (ID: {listing.id})")

    await message.answer("\n".join(lines))


# ---------------------------------------------------------------------------
# /approve <listing_id> — approve listing (admin only)
# ---------------------------------------------------------------------------


@router.message(Command("approve"))
async def cmd_approve(message: Message, sessionmaker: async_sessionmaker) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /approve <listing_id>")
        return

    listing_id = parts[1].strip()

    async with sessionmaker() as session:
        result = await session.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            await message.answer("❌ Объявление не найдено.")
            return

        listing.status = ListingStatus.approved

        # Fetch seller for notification
        seller_result = await session.execute(
            select(User).where(User.id == listing.seller_id)
        )
        seller = seller_result.scalar_one_or_none()

        await session.commit()

    # Notify seller
    if seller is not None:
        try:
            await bot.send_message(
                seller.telegram_id,
                f"✅ Ваше объявление '{listing.title}' одобрено!",
            )
        except Exception:
            pass

    await message.answer("✅ Объявление одобрено.")


# ---------------------------------------------------------------------------
# /reject <listing_id> [reason] — reject listing (admin only)
# ---------------------------------------------------------------------------


@router.message(Command("reject"))
async def cmd_reject(message: Message, sessionmaker: async_sessionmaker) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Использование: /reject <listing_id> [причина]")
        return

    listing_id = parts[1].strip()
    reason = parts[2].strip() if len(parts) > 2 else "Не указана"

    async with sessionmaker() as session:
        result = await session.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            await message.answer("❌ Объявление не найдено.")
            return

        listing.status = ListingStatus.rejected

        seller_result = await session.execute(
            select(User).where(User.id == listing.seller_id)
        )
        seller = seller_result.scalar_one_or_none()

        await session.commit()

    # Notify seller
    if seller is not None:
        try:
            await bot.send_message(
                seller.telegram_id,
                f"❌ Ваше объявление '{listing.title}' отклонено. Причина: {reason}",
            )
        except Exception:
            pass

    await message.answer("❌ Объявление отклонено.")


# ---------------------------------------------------------------------------
# /stats — basic stats (admin only)
# ---------------------------------------------------------------------------


@router.message(Command("stats"))
async def cmd_stats(message: Message, sessionmaker: async_sessionmaker) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    async with sessionmaker() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        total_categories = (
            await session.execute(select(func.count(Category.id)))
        ).scalar_one()

        pending_count = (
            await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.status == ListingStatus.pending
                )
            )
        ).scalar_one()
        approved_count = (
            await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.status == ListingStatus.approved
                )
            )
        ).scalar_one()
        rejected_count = (
            await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.status == ListingStatus.rejected
                )
            )
        ).scalar_one()

    total_listings = pending_count + approved_count + rejected_count
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👤 Пользователей: {total_users}\n"
        f"📦 Объявлений всего: {total_listings}\n"
        f"  ⏳ На проверке: {pending_count}\n"
        f"  ✅ Одобрено: {approved_count}\n"
        f"  ❌ Отклонено: {rejected_count}\n"
        f"📂 Категорий: {total_categories}"
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
# Inline callbacks — approve / reject from admin notification message
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("approve:"))
async def callback_approve(
    callback: CallbackQuery, sessionmaker: async_sessionmaker
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.")
        return

    listing_id = callback.data.split(":", 1)[1]

    async with sessionmaker() as session:
        result = await session.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            await callback.answer("❌ Объявление не найдено.")
            return

        listing.status = ListingStatus.approved

        seller_result = await session.execute(
            select(User).where(User.id == listing.seller_id)
        )
        seller = seller_result.scalar_one_or_none()

        await session.commit()

    if seller is not None:
        try:
            await bot.send_message(
                seller.telegram_id,
                f"✅ Ваше объявление '{listing.title}' одобрено!",
            )
        except Exception:
            pass

    await callback.answer("✅ Одобрено")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(
    callback: CallbackQuery, sessionmaker: async_sessionmaker
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.")
        return

    listing_id = callback.data.split(":", 1)[1]

    async with sessionmaker() as session:
        result = await session.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            await callback.answer("❌ Объявление не найдено.")
            return

        listing.status = ListingStatus.rejected

        seller_result = await session.execute(
            select(User).where(User.id == listing.seller_id)
        )
        seller = seller_result.scalar_one_or_none()

        await session.commit()

    if seller is not None:
        try:
            await bot.send_message(
                seller.telegram_id,
                f"❌ Ваше объявление '{listing.title}' отклонено.",
            )
        except Exception:
            pass

    await callback.answer("❌ Отклонено")
    await callback.message.edit_reply_markup(reply_markup=None)
