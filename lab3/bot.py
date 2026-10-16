"""SmartShop Assistant 3.0 — SQLite-backed Telegram bot."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import database as db

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / '.env')
load_dotenv(PROJECT_DIR.parent / 'lab1' / '.env')  # local fallback; never commit the token
TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.WARNING)

MENU = ReplyKeyboardMarkup([
    ['🛍 Каталог', '📂 Категории'],
    ['🔎 Поиск', '⭐ Избранное'],
    ['🛒 Корзина', '📋 Мои заявки'],
    ['ℹ️ Помощь', '🔙 Главное меню'],
], resize_keyboard=True)
CATEGORIES = ReplyKeyboardMarkup([
    ['👕 Одежда', '👟 Обувь'],
    ['🎒 Аксессуары', '🔙 Главное меню'],
], resize_keyboard=True)
CATEGORY_BUTTONS = {'👕 Одежда': 'Одежда', '👟 Обувь': 'Обувь', '🎒 Аксессуары': 'Аксессуары'}


def describe(p):
    return (f"📦 {p['name']} (ID: {p['id']})\n"
            f"📂 Категория: {p['category']}\n"
            f"💰 Цена: {p['price']} ₽\n"
            f"✅ В наличии: {p['stock']} шт.\n"
            f"📝 {p['description']}")


def user_id(update):
    person = update.effective_user
    db.ensure_user(person.id, person.first_name or '')
    return person.id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = None
    await update.message.reply_text('👋 Добро пожаловать в SmartShop Assistant 3.0!\nДанные сохраняются в SQLite. Выберите действие:', reply_markup=MENU)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = None
    await update.message.reply_text(
        'ℹ️ Команды: /start /help /catalog /categories /search /favorites /cart /orders /about\n\n'
        '«избранное 2» — добавить/убрать избранное\n'
        '«купить 2» — добавить в корзину\n'
        '«удалить 2» — убрать 1 шт.\n'
        '«очистить» — очистить корзину\n'
        '«заказать» — оформить заявку без оплаты.', reply_markup=MENU)


async def send_product_cards(update, rows, heading):
    """Show each product with one-tap cart and favorites actions."""
    await update.message.reply_text(heading)
    if not rows:
        await update.message.reply_text('😔 Товары не найдены.', reply_markup=MENU)
        return
    for product in rows:
        product_id = product['id']
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('🛒 В корзину', callback_data=f'cart_add:{product_id}'),
            InlineKeyboardButton('⭐ Избранное', callback_data=f'fav_toggle:{product_id}'),
        ]])
        await update.message.reply_text(describe(product), reply_markup=keyboard)


async def product_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = user_id(update)
    try:
        action, raw_id = query.data.split(':', 1)
        pid = int(raw_id)
    except (ValueError, AttributeError):
        await query.message.reply_text('Некорректная кнопка.')
        return
    if db.product(pid) is None:
        await query.message.reply_text('Товар больше не найден.')
        return
    if action == 'cart_add':
        result = db.add_to_cart(uid, pid)
        response = {'ok': '✅ Товар добавлен в корзину. Откройте «🛒 Корзина» в меню.',
                    'stock': 'Недостаточно товара на складе.',
                    'missing': 'Товар не найден.'}[result]
    elif action == 'fav_toggle':
        added = db.toggle_favorite(uid, pid)
        response = '⭐ Добавлено в избранное.' if added else '⭐ Удалено из избранного.'
    else:
        response = 'Неизвестное действие.'
    await query.message.reply_text(response, reply_markup=MENU)


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = None
    await send_product_cards(update, db.products(), '🛍 Каталог из базы данных:')


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = None
    await update.message.reply_text('📂 Выберите категорию:', reply_markup=CATEGORIES)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = 'search'
    await update.message.reply_text('🔎 Введите часть названия или описания товара:')


async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = user_id(update)
    context.user_data['mode'] = None
    items = db.favorites(uid)
    await update.message.reply_text('⭐ Избранное:\n\n' + '\n\n'.join(map(describe, items)) if items else '⭐ Избранное пока пустое.', reply_markup=MENU)


async def cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = user_id(update)
    context.user_data['mode'] = None
    items = db.cart_items(uid)
    if not items:
        await update.message.reply_text('🛒 Корзина пуста.', reply_markup=MENU)
        return
    total = sum(p['price'] * p['quantity'] for p in items)
    lines = [f"• {p['name']} × {p['quantity']} — {p['price']*p['quantity']} ₽" for p in items]
    await update.message.reply_text('🛒 Корзина:\n\n' + '\n'.join(lines) + f'\n\n💰 Итого: {total} ₽\nЧтобы оформить заявку, напишите «заказать».', reply_markup=MENU)


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = user_id(update)
    context.user_data['mode'] = None
    items = db.orders(uid)
    await update.message.reply_text('📋 Мои заявки:\n' + '\n'.join(f"№{o['id']} — {o['total']} ₽ ({o['created_at']})" for o in items) if items else '📋 Заявок пока нет.', reply_markup=MENU)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id(update)
    context.user_data['mode'] = None
    await update.message.reply_text('🎓 SmartShop Assistant 3.1 — лабораторная №3, Railway + SQLite.\nКуприянова Арина Владимировна, U4225, ИТМО.', reply_markup=MENU)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = user_id(update)
    raw = update.message.text.strip()
    lower = raw.lower()
    actions = {
        '🛍 Каталог': catalog, '📂 Категории': categories,
        '🔎 Поиск': search, '⭐ Избранное': favorites,
        '🛒 Корзина': cart, '📋 Мои заявки': orders,
        'ℹ️ Помощь': help_command, '🔙 Главное меню': start,
    }
    if raw in actions:
        await actions[raw](update, context)
        return
    if raw in CATEGORY_BUTTONS:
        context.user_data['mode'] = None
        category = CATEGORY_BUTTONS[raw]
        rows = db.products(category=category)
        await send_product_cards(update, rows, f'📂 {category}:')
        return
    parts = lower.split()
    if len(parts) == 2 and parts[0] in ('купить', 'избранное', 'удалить'):
        context.user_data['mode'] = None
        if not parts[1].isdigit():
            await update.message.reply_text('Укажите числовой ID товара.')
            return
        pid = int(parts[1])
        if db.product(pid) is None:
            await update.message.reply_text('Товар с таким ID не найден.')
            return
        if parts[0] == 'купить':
            result = db.add_to_cart(uid, pid)
            msg = {'ok': '✅ Товар добавлен в корзину.', 'stock': 'Недостаточно товара на складе.', 'missing': 'Товар не найден.'}[result]
        elif parts[0] == 'избранное':
            added = db.toggle_favorite(uid, pid)
            msg = '⭐ Добавлено в избранное.' if added else '⭐ Удалено из избранного.'
        else:
            msg = '✅ Удалена одна единица товара.' if db.remove_from_cart(uid, pid) else 'Такого товара нет в корзине.'
        await update.message.reply_text(msg, reply_markup=MENU)
        return
    if lower == 'очистить':
        db.clear_cart(uid)
        context.user_data['mode'] = None
        await update.message.reply_text('🗑 Корзина очищена.', reply_markup=MENU)
        return
    if lower == 'заказать':
        context.user_data['mode'] = None
        try:
            result = db.place_order(uid)
        except ValueError as error:
            await update.message.reply_text(str(error), reply_markup=MENU)
            return
        await update.message.reply_text(f'✅ Заявка №{result[0]} создана. Сумма {result[1]} ₽. Оплата не проводится.' if result else 'Сначала добавьте товары в корзину.', reply_markup=MENU)
        return
    if context.user_data.get('mode') == 'search':
        context.user_data['mode'] = None
        rows = db.products(term=raw)
        await send_product_cards(update, rows, '🔎 Результаты поиска:')
        return
    await update.message.reply_text('Не понял запрос. Нажмите /help.', reply_markup=MENU)


def main():
    if not TOKEN:
        raise RuntimeError('BOT_TOKEN отсутствует в lab1/.env или lab2/.env')
    db.init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    handlers = {
        'start': start, 'help': help_command, 'catalog': catalog,
        'categories': categories, 'search': search, 'favorites': favorites,
        'cart': cart, 'orders': orders, 'about': about,
    }
    for name, handler in handlers.items():
        app.add_handler(CommandHandler(name, handler))
    app.add_handler(CallbackQueryHandler(product_button, pattern=r'^(cart_add|fav_toggle):[0-9]+$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('SmartShop Assistant 3.0 (SQLite) запущен!', flush=True)
    app.run_polling()


if __name__ == '__main__':
    main()
