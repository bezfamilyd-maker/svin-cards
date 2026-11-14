import os
import sqlite3
import random
import time
import datetime
import threading
from zoneinfo import ZoneInfo
from flask import Flask
import telebot

# ==================== НАСТРОЙКИ ====================
TOKEN = os.environ.get('TELEGRAM_TOKEN', '9010306241:AAH49OSX-q6U1DLjTeDshgLCJrEWrEYExfs')

# Кулдаун между карточками (1 час = 3600 секунд)
COOLDOWN = 3600

# Время по МСК (ровно 1 минута: с 14:48 до 14:49)
TIME_WINDOW_HOUR = 14
TIME_WINDOW_MINUTE_START = 48
TIME_WINDOW_MINUTE_END = 49

MSK = ZoneInfo("Europe/Moscow")
CODEWORDS = {"свинья", "свинота", "хряк", "жир"}

# ==================== КАРТОЧКИ ====================
cards_nothing = [
    {"photo": "ID_1", "name": "Карточка 1", "rarity": "Ничего не стоит"},
    {"photo": "ID_2", "name": "Карточка 2", "rarity": "Ничего не стоит"},
    {"photo": "ID_3", "name": "Карточка 3", "rarity": "Ничего не стоит"},
    {"photo": "ID_4", "name": "Карточка 4", "rarity": "Ничего не стоит"},
    {"photo": "ID_5", "name": "Карточка 5", "rarity": "Ничего не стоит"},
    {"photo": "ID_6", "name": "Карточка 6", "rarity": "Ничего не стоит"},
    {"photo": "ID_7", "name": "Карточка 7", "rarity": "Ничего не стоит"},
    {"photo": "ID_8", "name": "Карточка 8", "rarity": "Ничего не стоит"},
    {"photo": "ID_9", "name": "Карточка 9", "rarity": "Ничего не стоит"},
    {"photo": "ID_10", "name": "Карточка 10", "rarity": "Ничего не стоит"},
]

cards_common = [
    {"photo": "ID_11", "name": "Карточка 11", "rarity": "Обычная"},
    {"photo": "ID_12", "name": "Карточка 12", "rarity": "Обычная"},
    {"photo": "ID_13", "name": "Карточка 13", "rarity": "Обычная"},
    {"photo": "ID_14", "name": "Карточка 14", "rarity": "Обычная"},
    {"photo": "ID_15", "name": "Карточка 15", "rarity": "Обычная"},
    {"photo": "ID_16", "name": "Карточка 16", "rarity": "Обычная"},
    {"photo": "ID_17", "name": "Карточка 17", "rarity": "Обычная"},
    {"photo": "ID_18", "name": "Карточка 18", "rarity": "Обычная"},
    {"photo": "ID_19", "name": "Карточка 19", "rarity": "Обычная"},
    {"photo": "ID_20", "name": "Карточка 20", "rarity": "Обычная"},
]

cards_unusual = [
    {"photo": "ID_21", "name": "Карточка 21", "rarity": "Необычная"},
    {"photo": "ID_22", "name": "Карточка 22", "rarity": "Необычная"},
    {"photo": "ID_23", "name": "Карточка 23", "rarity": "Необычная"},
    {"photo": "ID_24", "name": "Карточка 24", "rarity": "Необычная"},
    {"photo": "ID_25", "name": "Карточка 25", "rarity": "Необычная"},
    {"photo": "ID_26", "name": "Карточка 26", "rarity": "Необычная"},
    {"photo": "ID_27", "name": "Карточка 27", "rarity": "Необычная"},
    {"photo": "ID_28", "name": "Карточка 28", "rarity": "Необычная"},
]

cards_heroic = [
    {"photo": "ID_29", "name": "Карточка 29", "rarity": "Героизм"},
    {"photo": "ID_30", "name": "Карточка 30", "rarity": "Героизм"},
    {"photo": "ID_31", "name": "Карточка 31", "rarity": "Героизм"},
    {"photo": "ID_32", "name": "Карточка 32", "rarity": "Героизм"},
    {"photo": "ID_33", "name": "Карточка 33", "rarity": "Героизм"},
    {"photo": "ID_34", "name": "Карточка 34", "rarity": "Героизм"},
    {"photo": "ID_35", "name": "Карточка 35", "rarity": "Героизм"},
    {"photo": "ID_36", "name": "Карточка 36", "rarity": "Героизм"},
    {"photo": "ID_37", "name": "Карточка 37", "rarity": "Героизм"},
    {"photo": "ID_38", "name": "Карточка 38", "rarity": "Героизм"},
    {"photo": "ID_39", "name": "Карточка 39", "rarity": "Героизм"},
    {"photo": "ID_40", "name": "Карточка 40", "rarity": "Героизм"},
]

cards_legendary = [
    {"photo": "ID_41", "name": "Карточка 41", "rarity": "Легендарная"},
    {"photo": "ID_42", "name": "Карточка 42", "rarity": "Легендарная"},
    {"photo": "ID_43", "name": "Карточка 43", "rarity": "Легендарная"},
    {"photo": "ID_44", "name": "Карточка 44", "rarity": "Легендарная"},
    {"photo": "ID_45", "name": "Карточка 45", "rarity": "Легендарная"},
    {"photo": "ID_46", "name": "Карточка 46", "rarity": "Легендарная"},
    {"photo": "ID_47", "name": "Карточка 47", "rarity": "Легендарная"},
    {"photo": "ID_48", "name": "Карточка 48", "rarity": "Легендарная"},
    {"photo": "ID_49", "name": "Карточка 49", "rarity": "Легендарная"},
]

cards_impossible = [
    {"photo": "ID_50", "name": "Карточка 50", "rarity": "Невозможно"},
    {"photo": "ID_51", "name": "Карточка 51", "rarity": "Невозможно"},
    {"photo": "ID_52", "name": "Карточка 52", "rarity": "Невозможно"},
    {"photo": "ID_53", "name": "Карточка 53", "rarity": "Невозможно"},
    {"photo": "ID_54", "name": "Карточка 54", "rarity": "Невозможно"},
    {"photo": "ID_55", "name": "Карточка 55", "rarity": "Невозможно"},
    {"photo": "ID_56", "name": "Карточка 56", "rarity": "Невозможно"},
    {"photo": "ID_57", "name": "Карточка 57", "rarity": "Невозможно"},
    {"photo": "ID_58", "name": "Карточка 58", "rarity": "Невозможно"},
    {"photo": "ID_59", "name": "Карточка 59", "rarity": "Невозможно"},
    {"photo": "ID_60", "name": "Карточка 60", "rarity": "Невозможно"},
    {"photo": "ID_61", "name": "Карточка 61", "rarity": "Невозможно"},
    {"photo": "ID_62", "name": "Карточка 62", "rarity": "Невозможно"},
]

# Особая карточка по времени (14:48 МСК)
TIME_CARD = {"photo": "ID_TIME", "name": "Особая по времени", "rarity": "Секретная"}

# ==================== БОТ И БД ====================
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    last_draw_time REAL DEFAULT 0
)
""")
conn.commit()

# ==================== FLASK ДЛЯ RENDER ====================
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== ЛОГИКА ====================
def in_time_window():
    now = datetime.datetime.now(MSK)
    return (now.hour == TIME_WINDOW_HOUR and 
            TIME_WINDOW_MINUTE_START <= now.minute < TIME_WINDOW_MINUTE_END)

def get_card_and_update(uid):
    now_ts = time.time()
    cur.execute("SELECT last_draw_time FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    
    if row is None:
        cur.execute("INSERT INTO users (user_id, last_draw_time) VALUES (?, ?)", (uid, 0))
        conn.commit()
        last_time = 0
    else:
        last_time = row[0]

    if now_ts - last_time < COOLDOWN:
        return None, "cooldown", int(COOLDOWN - (now_ts - last_time))

    if in_time_window():
        card, reason = TIME_CARD, "time"
    else:
        rarity_choice = random.choices(
            ["nothing", "common", "unusual", "heroic", "legendary", "impossible"], 
            weights=[45, 25, 15, 9, 5, 1], 
            k=1
        )[0]

        if rarity_choice == "nothing":
            card = random.choice(cards_nothing)
        elif rarity_choice == "common":
            card = random.choice(cards_common)
        elif rarity_choice == "unusual":
            card = random.choice(cards_unusual)
        elif rarity_choice == "heroic":
            card = random.choice(cards_heroic)
        elif rarity_choice == "legendary":
            card = random.choice(cards_legendary)
        else:
            card = random.choice(cards_impossible)
            
        reason = "random"

    cur.execute("UPDATE users SET last_draw_time=? WHERE user_id=?", (now_ts, uid))
    conn.commit()
    return card, reason, 0

def format_remaining(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h: return f"{h} ч {m} мин"
    if m: return f"{m} мин"
    return f"{s} сек"

# ==================== ОБРАБОТЧИКИ ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    text = (
        "🐷 <b>Svin Cards</b>\n\n"
        "Кодовые слова: свинья, свинота, хряк, жир\n"
        f"⏳ Кулдаун: {COOLDOWN // 60} мин.\n"
        f"🌙 С {TIME_WINDOW_HOUR}:{TIME_WINDOW_MINUTE_START:02d} до {TIME_WINDOW_HOUR}:{TIME_WINDOW_MINUTE_END:02d} МСК — секретная карточка по времени."
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uid = message.from_user.id
    cur.execute("SELECT last_draw_time FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if row is None:
        bot.reply_to(message, "Напиши «свинья», чтобы начать!")
        return
    last_time = row[0]
    cooldown_left = max(0, int(COOLDOWN - (time.time() - last_time)))
    
    text = "📊 <b>Твоя статистика</b>\n\n"
    if cooldown_left > 0:
        text += f"⏳ Кулдаун: {format_remaining(cooldown_left)}"
    else:
        text += "✅ Можно тянуть карточку!"
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.lower().strip() not in CODEWORDS:
        return
    uid = message.from_user.id
    card, reason, cooldown_left = get_card_and_update(uid)
    
    if card is None:
        bot.reply_to(message, f"⏳ Рано! Ждать: <b>{format_remaining(cooldown_left)}</b>.", parse_mode='HTML')
        return
        
    caption = f"<b>{card['name']}</b>\nРедкость: {card['rarity']}"
    if reason == "time":
        caption = "🌙 <b>Секретная карточка по времени!</b>\n\n" + caption
    
    bot.send_photo(message.chat.id, card["photo"], caption=caption, parse_mode='HTML')

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🐷 Svin Cards запущен...")
    bot.infinity_polling()
  
