import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = '8009127930:AAHS2c6qWF_Z-xUqfuQOpwZ-Dox5up-PUJc'  # ← ВСТАВЬ СВОЙ ТОКЕН
ADMIN_ID = 6396493619  # ← ВСТАВЬ СВОЙ Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === FSM для рассылки ===
class Broadcast(StatesGroup):
    waiting_for_message = State()

# === БАЗА ДАННЫХ ===
DATA_FILE = 'database.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# === /start ===
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"language": None}
        save_data(data)
    await message.answer(f"👋 Hello, {message.from_user.first_name}!\nPlease choose your language:")
    await show_language_menu(message)

# === /language ===
@dp.message(Command("language"))
async def show_language_menu(message: Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇺🇸 English")],
            [KeyboardButton(text="🇺🇿 O‘zbek")]
        ]
    )
    await message.answer("🌐 Выберите язык / Choose language / Tilni tanlang:", reply_markup=keyboard)

@dp.message(F.text.in_({"🇷🇺 Русский", "🇺🇸 English", "🇺🇿 O‘zbek"}))
async def set_language(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    lang = message.text
    data[user_id]["language"] = lang
    save_data(data)

    await message.answer(f"✅ Язык установлен: {lang}", reply_markup=ReplyKeyboardRemove())
    await message.answer("🔔 Для настройки подключите бота с помощью /activate")

# === /activate ===
@dp.message(Command("activate"))
async def activate_handler(message: Message):
    text = (
        "📌 *Для полноценной работы необходимо подключить бота к бизнес-аккаунту в Telegram.*\n\n"
        "Как это сделать?\n"
        "1. ⚙️ Откройте *Настройки Telegram*.\n"
        "2. 💼 Найдите пункт *Telegram для бизнеса* и нажмите на него.\n"
        "3. 🤖 Перейдите в раздел *Чат-боты*.\n"
        "4. ✍️ Введите: `sherlockmsg_bot`, и добавьте его.\n\n"
        "ℹ️ Бот сам поймёт, когда вы сделали все действия, и начнёт отслеживать все сообщения!\n"
        "_Вы получите уведомление._"
    )
    await message.answer(text, parse_mode="Markdown")

# === /function ===
@dp.message(Command("function"))
async def show_functions(message: Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📦 Товары"), KeyboardButton(text="📋 Заказы")],
            [KeyboardButton(text="⬅ Назад")]
        ]
    )
    await message.answer("🔧 Выберите функцию:", reply_markup=keyboard)

@dp.message(F.text == "📦 Товары")
async def handle_products(message: Message):
    await message.answer("🛒 Здесь будут товары...")

@dp.message(F.text == "📋 Заказы")
async def handle_orders(message: Message):
    await message.answer("📑 Здесь будут заказы...")

@dp.message(F.text == "⬅ Назад")
async def handle_back(message: Message):
    await message.answer("↩️ Назад", reply_markup=ReplyKeyboardRemove())

# === /broadcast с FSM ===
@dp.message(Command("broadcast"))
async def broadcast_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа.")
        return
    await message.answer("✉️ Введи текст рассылки:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Broadcast.waiting_for_message)

@dp.message(Broadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    users = load_data()
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 Сообщение от администратора:\n\n{message.text}")
            count += 1
        except:
            continue
    await message.answer(f"✅ Рассылка завершена. Отправлено {count} пользователям.")
    await state.clear()
# === /profile ===
@dp.message(Command("profile"))
async def profile_handler(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    lang = data.get(user_id, {}).get("language", "❓ Не выбран")

    text = (
        f"👤 Профиль:\n"
        f"🆔 ID: {user_id}\n"
        f"👨‍💼 Имя: {message.from_user.first_name}\n"
        f"🌐 Язык: {lang}"
    )
    await message.answer(text)

# === /stats (для админа) ===
@dp.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа.")
        return

    data = load_data()
    total_users = len(data)

    langs = {"🇷🇺 Русский": 0, "🇺🇸 English": 0, "🇺🇿 O‘zbek": 0, "❓": 0}
    for user in data.values():
        lang = user.get("language", "❓")
        langs[lang] = langs.get(lang, 0) + 1

    text = (
        f"📊 Статистика:\n"
        f"👥 Всего пользователей: {total_users}\n\n"
        f"🇷🇺 Русский: {langs['🇷🇺 Русский']}\n"
        f"🇺🇸 English: {langs['🇺🇸 English']}\n"
        f"🇺🇿 O‘zbek: {langs['🇺🇿 O‘zbek']}\n"
        f"❓ Без языка: {langs['❓']}"
    )
    await message.answer(text)

# === /help ===
@dp.message(Command("help"))
async def help_handler(message: Message):
    text = (
        "🆘 *Помощь*\n\n"
        "Доступные команды:\n"
        "/start — Запуск бота\n"
        "/language — Выбор языка\n"
        "/function — Меню функций\n"
        "/activate — Подключение к Telegram бизнес\n"
        "/profile — Мой профиль\n"
        "/help — Помощь\n"
    )

    # Только для админа
    if message.from_user.id == ADMIN_ID:
        text += (
            "\n*Админ-команды:*\n"
            "/broadcast — Рассылка\n"
            "/stats — Статистика пользователей"
        )

    await message.answer(text, parse_mode="Markdown")

# === ЗАПУСК ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
