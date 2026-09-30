import os, sqlite3, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID  = int(os.getenv("OWNER_ID", "0"))

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher()

DB = sqlite3.connect("leaks.db", check_same_thread=False)
DB.execute("""CREATE TABLE IF NOT EXISTS people(
    phone TEXT, fio TEXT, address TEXT, relatives TEXT, source TEXT)""")
DB.commit()

CONTACTS = {}

async def tg_data(uid):
    d = {"id": uid, "username": "—", "name": "—", "bio": "—",
         "photo_file_id": None}
    try:
        chat = await bot.get_chat(uid)
        d["username"] = chat.username or "—"
        d["name"]     = chat.full_name or "—"
        d["bio"]      = getattr(chat, "bio", None) or "—"
        ph = await bot.get_user_profile_photos(uid, limit=1)
        if ph.total_count:
            d["photo_file_id"] = ph.photos[0][-1].file_id
    except Exception as e
