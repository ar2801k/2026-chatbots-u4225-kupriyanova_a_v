
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MENU = ReplyKeyboardMarkup(
    [
        ["🛍 Каталог", "🔎 Поиск"],
        ["⭐ Избранное", "🛒 Корзина"],
        ["💬 Обратная связь", "ℹ️ Помощь"],
    ],
    resize_keyboard=True,
)

PRODUCTS = [
    ("Футболка", 1500),
    ("Худи", 3500),
    ("Кроссовки", 5900),
    ("Рюкзак", 2500),
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в SmartShop Assistant!\n\n"
        "Я помогу вам найти товары и узнать цены.\n"
        "Выберите действие в меню ниже.",
        reply_markup=MENU,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Доступные функции:\n\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/catalog — каталог товаров\n"
        "/about — информация о проекте\n\n"
        "Остальные функции будут добавлены в следующих версиях.",
        reply_markup=MENU,
    )


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🛍 Каталог SmartShop:\n"]
    for name, price in PRODUCTS:
        lines.append(f"• {name} — {price} ₽")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=MENU,
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 SmartShop Assistant\n\n"
        "Учебный проект по дисциплине "
        "«Vibe Coding for Business».\n"
        "Университет ИТМО.\n"
        "Студент: Куприянова Арина Владимировна.\n"
        "Группа: U4225.",
        reply_markup=MENU,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛍 Каталог":
        await catalog(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "🔎 Поиск":
        await update.message.reply_text(
            "🔎 Поиск товаров появится в следующей версии."
        )
    elif text == "⭐ Избранное":
        await update.message.reply_text(
            "⭐ Избранное появится в следующей версии."
        )
    elif text == "🛒 Корзина":
        await update.message.reply_text(
            "🛒 Корзина появится в следующей версии."
        )
    elif text == "💬 Обратная связь":
        await update.message.reply_text(
            "💬 Сбор обратной связи будет добавлен позже."
        )
    else:
        await update.message.reply_text(
            "Неизвестная команда. Используйте /help.",
            reply_markup=MENU,
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не найден. Проверьте файл lab1/.env"
        )

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("catalog", catalog))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("SmartShop Assistant запущен!")
    application.run_polling()


if __name__ == "__main__":
    main()
