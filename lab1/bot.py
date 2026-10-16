
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

# Не выводим URL запросов с секретным токеном в логи
logging.basicConfig(level=logging.WARNING)

PRODUCTS = {
    1: {
        "name": "Футболка Basic",
        "category": "Одежда",
        "price": 1500,
        "stock": 15,
        "description": "Хлопковая футболка на каждый день.",
    },
    2: {
        "name": "Худи Comfort",
        "category": "Одежда",
        "price": 3500,
        "stock": 8,
        "description": "Тёплое худи свободного кроя.",
    },
    3: {
        "name": "Кроссовки Active",
        "category": "Обувь",
        "price": 5900,
        "stock": 12,
        "description": "Удобные кроссовки для прогулок.",
    },
    4: {
        "name": "Рюкзак City",
        "category": "Аксессуары",
        "price": 2500,
        "stock": 6,
        "description": "Городской рюкзак на 20 литров.",
    },
    5: {
        "name": "Кепка Sport",
        "category": "Аксессуары",
        "price": 900,
        "stock": 20,
        "description": "Лёгкая регулируемая кепка.",
    },
    6: {
        "name": "Ботинки Winter",
        "category": "Обувь",
        "price": 7200,
        "stock": 4,
        "description": "Утеплённые зимние ботинки.",
    },
}

MENU = ReplyKeyboardMarkup(
    [
        ["🛍 Каталог", "📂 Категории"],
        ["🔎 Поиск", "⭐ Избранное"],
        ["🛒 Корзина", "ℹ️ Помощь"],
        ["🔙 Главное меню"],
    ],
    resize_keyboard=True,
)

CATEGORIES = ReplyKeyboardMarkup(
    [
        ["👕 Одежда", "👟 Обувь"],
        ["🎒 Аксессуары", "🔙 Главное меню"],
    ],
    resize_keyboard=True,
)


def format_product(product_id):
    p = PRODUCTS[product_id]
    return (
        f"📦 {p['name']} (ID: {product_id})\n"
        f"📂 Категория: {p['category']}\n"
        f"💰 Цена: {p['price']} ₽\n"
        f"✅ В наличии: {p['stock']} шт.\n"
        f"📝 {p['description']}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "👋 Добро пожаловать в SmartShop Assistant!\n\n"
        "Здесь можно найти товары, узнать цены, "
        "добавить товары в избранное и корзину.\n\n"
        "Выберите действие в меню.",
        reply_markup=MENU,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "ℹ️ Возможности SmartShop:\n\n"
        "/start — главное меню\n"
        "/catalog — каталог\n"
        "/categories — категории\n"
        "/search — поиск\n"
        "/favorites — избранное\n"
        "/cart — корзина\n"
        "/about — информация о проекте\n\n"
        "Чтобы добавить товар в избранное, "
        "напишите: избранное 1\n"
        "Чтобы добавить товар в корзину: купить 1\n"
        "Чтобы удалить товар из корзины: удалить 1\n"
        "Чтобы очистить корзину: очистить\n\n"
        "Цифра — ID товара из каталога.",
        reply_markup=MENU,
    )


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "🛍 Каталог товаров:\n\n"
        + "\n\n".join(format_product(i) for i in PRODUCTS)
        + "\n\nДля добавления товара напишите «купить 1», "
        "где 1 — ID товара.",
        reply_markup=MENU,
    )


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "📂 Выберите категорию:",
        reply_markup=CATEGORIES,
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "search"
    await update.message.reply_text(
        "🔎 Введите название товара или его часть.\n"
        "Например: худи, кроссовки, кепка."
    )


async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    items = context.user_data.setdefault("favorites", [])

    if not items:
        await update.message.reply_text(
            "⭐ Избранное пока пустое.\n"
            "Добавьте товар командой «избранное 1».",
            reply_markup=MENU,
        )
        return

    await update.message.reply_text(
        "⭐ Избранные товары:\n\n"
        + "\n\n".join(format_product(i) for i in items),
        reply_markup=MENU,
    )


async def cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    items = context.user_data.setdefault("cart", [])

    if not items:
        await update.message.reply_text(
            "🛒 Корзина пуста.\n"
            "Добавьте товар командой «купить 1».",
            reply_markup=MENU,
        )
        return

    total = sum(PRODUCTS[i]["price"] for i in items)
    lines = [
        f"• {PRODUCTS[i]['name']} — {PRODUCTS[i]['price']} ₽"
        for i in items
    ]

    await update.message.reply_text(
        "🛒 Ваша корзина:\n\n"
        + "\n".join(lines)
        + f"\n\n💰 Итого: {total} ₽\n\n"
        "«удалить 1» — убрать одну единицу товара.\n"
        "«очистить» — очистить корзину.\n\n"
        "Оплата в учебном боте не предусмотрена.",
        reply_markup=MENU,
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "🎓 SmartShop Assistant\n\n"
        "Учебный проект ИТМО.\n"
        "Дисциплина: Vibe Coding for Business.\n"
        "Студент: Куприянова Арина Владимировна.\n"
        "Группа: U4225.\n\n"
        "Версия: MVP 2.0",
        reply_markup=MENU,
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()
    lower = text.lower()

    menu_actions = {
        "🛍 Каталог": catalog,
        "📂 Категории": categories,
        "🔎 Поиск": search,
        "⭐ Избранное": favorites,
        "🛒 Корзина": cart,
        "ℹ️ Помощь": help_command,
        "🔙 Главное меню": start,
    }

    if text in menu_actions:
        await menu_actions[text](update, context)
        return

    category_names = {
        "👕 Одежда": "Одежда",
        "👟 Обувь": "Обувь",
        "🎒 Аксессуары": "Аксессуары",
    }

    if text in category_names:
        context.user_data["mode"] = None
        category = category_names[text]
        matching = [
            i for i, p in PRODUCTS.items()
            if p["category"] == category
        ]
        await update.message.reply_text(
            f"📂 {category}:\n\n"
            + "\n\n".join(format_product(i) for i in matching),
            reply_markup=CATEGORIES,
        )
        return

    parts = lower.split()

    if len(parts) == 2 and parts[0] in {
        "купить", "избранное", "удалить"
    }:
        if not parts[1].isdigit():
            await update.message.reply_text("Укажите числовой ID товара.")
            return

        product_id = int(parts[1])
        if product_id not in PRODUCTS:
            await update.message.reply_text("Товар с таким ID не найден.")
            return

        if parts[0] == "купить":
            items = context.user_data.setdefault("cart", [])
            quantity = items.count(product_id)

            if quantity >= PRODUCTS[product_id]["stock"]:
                await update.message.reply_text(
                    "Недостаточно товара в наличии."
                )
                return

            items.append(product_id)
            message = "✅ Товар добавлен в корзину!"

        elif parts[0] == "избранное":
            items = context.user_data.setdefault("favorites", [])
            if product_id in items:
                items.remove(product_id)
                message = "⭐ Товар удалён из избранного."
            else:
                items.append(product_id)
                message = "⭐ Товар добавлен в избранное!"

        else:
            items = context.user_data.setdefault("cart", [])
            if product_id in items:
                items.remove(product_id)
                message = "✅ Товар удалён из корзины."
            else:
                message = "Такого товара нет в корзине."

        context.user_data["mode"] = None
        await update.message.reply_text(message, reply_markup=MENU)
        return

    if lower == "очистить":
        context.user_data["cart"] = []
        context.user_data["mode"] = None
        await update.message.reply_text(
            "🗑 Корзина очищена.",
            reply_markup=MENU,
        )
        return

    if context.user_data.get("mode") == "search":
        matching = [
            i for i, p in PRODUCTS.items()
            if lower in p["name"].lower()
            or lower in p["description"].lower()
        ]
        context.user_data["mode"] = None

        if matching:
            response = (
                "🔎 Результаты поиска:\n\n"
                + "\n\n".join(format_product(i) for i in matching)
            )
        else:
            response = "😔 По вашему запросу товары не найдены."

        await update.message.reply_text(response, reply_markup=MENU)
        return

    await update.message.reply_text(
        "Не понял запрос. Выберите действие в меню или /help.",
        reply_markup=MENU,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден в lab1/.env")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    commands = {
        "start": start,
        "help": help_command,
        "catalog": catalog,
        "categories": categories,
        "search": search,
        "favorites": favorites,
        "cart": cart,
        "about": about,
    }

    for command, handler in commands.items():
        application.add_handler(CommandHandler(command, handler))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print("SmartShop Assistant 2.0 запущен!", flush=True)
    application.run_polling()


if __name__ == "__main__":
    main()
