import asyncio
import logging
import google.generativeai as genai
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

# ─── НАСТРОЙКИ ───────────────────────────────────────────────
TELEGRAM_TOKEN  = "5613436098:AAF86T1nQHVWKaCz3pppZXcldsUd0GH9h5A"
TARGET_CHAT_ID  = -5196872792     # ID чата куда слать переводы
ALLOWED_USER_ID = 93372553         # Твой Telegram user_id
GEMINI_API_KEY  = "AIzaSyA2kRqDpYGKBQYLyOcK-Yn_VHHgMSATw1w"
# ─────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp  = Dispatcher()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "Sen bir çeviri asistanısın. "
        "Kullanıcının gönderdiği metni Türkçeye çevir. "
        "Resmi ve profesyonel bir iş dili kullan. "
        "Sadece çeviriyi döndür, başka hiçbir şey ekleme."
    ),
)

# Счётчик задач (сбрасывается каждый день)
task_counter = {"count": 0, "date": datetime.now().date()}


def get_next_number() -> int:
    today = datetime.now().date()
    if task_counter["date"] != today:
        task_counter["count"] = 0
        task_counter["date"] = today
    task_counter["count"] += 1
    return task_counter["count"]


async def translate_to_turkish(text: str) -> str:
    response = await model.generate_content_async(text)
    return response.text.strip()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    await message.answer(
        "Привет! Пиши задачи — переведу на турецкий и отправлю в рабочий чат.\n\n"
        "/status — задач за сегодня\n"
        "/reset — сбросить счётчик вручную"
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    today = datetime.now().date()
    count = task_counter["count"] if task_counter["date"] == today else 0
    await message.answer(f"Сегодня отправлено задач: {count}")


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    task_counter["count"] = 0
    task_counter["date"] = datetime.now().date()
    await message.answer("✅ Счётчик сброшен.")


@dp.message(F.text)
async def handle_task(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return

    original_text = message.text
    number = get_next_number()

    await message.answer("⏳ Перевожу...")

    try:
        translated = await translate_to_turkish(original_text)
    except Exception as e:
        task_counter["count"] -= 1  # откатываем счётчик при ошибке
        await message.answer(f"❌ Ошибка перевода: {e}")
        return

    formatted = f"{number}. {translated}"

    try:
        await bot.send_message(TARGET_CHAT_ID, formatted)
        await message.answer(f"✅ Отправлено:\n\n{formatted}")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки в чат: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
