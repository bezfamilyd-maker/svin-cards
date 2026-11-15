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
COOLDOWN = 14400

# Время по МСК (ровно 1 минута: с 14:48 до 14:49)
TIME_WINDOW_HOUR = 14
TIME_WINDOW_MINUTE_START = 48
TIME_WINDOW_MINUTE_END = 49

MSK = ZoneInfo("Europe/Moscow")
CODEWORDS = {"свинья", "свинота", "хряк", "жир"}

# ==================== КАРТОЧКИ ====================
cards_nothing = [
    {"photo": "AgACAgIAAxkBAAMCavjOkT35v2AoMbS23FY3YFDlg00AAmshaxt5CMlL6JsNIfTs94YBAAMCAAN5AAM9BA", "name": "Кабан обыкновенный жирный", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMEavjOmJsplG8HrkuTK0lMlQpCrhoAAmwhaxt5CMlL6hBVPmgtszQBAAMCAAN5AAM9BA", "name": "Милый кабанчик", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMGavjOnceIKo-spJU7ENVBBWcH_JwAAm0haxt5CMlL1rRC0ZsyLnABAAMCAAN5AAM9BA", "name": "Нестриженная свинья (стрижка в 6)", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMIavjOojiWvaZHfa2K_qML4MCsQdYAAm4haxt5CMlLtNpfcghLloABAAMCAAN5AAM9BA", "name": "Исхудавшая свинья не ела 3 минуты", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMKavjOp9Xnjo60_mAUhSVlC1j4FmIAAnIhaxt5CMlL7jdJ3SeAU8wBAAMCAAN4AAM9BA", "name": "Свиноматка обыкновенная", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMMavjOrjxg9vArNTFyUQ1_tNFraPMAAnUhaxt5CMlLfuaAf-5sfGUBAAMCAAN4AAM9BA", "name": "Базовый выводок", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMOavjOs8zcSKUj5BHzrwFleaQSwPoAAnYhaxt5CMlLyeIW1IRsxlEBAAMCAAN4AAM9BA", "name": "Негры свиноты", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMaavjOyRGbLwGsJs72VMi8waBAdfAAAnwhaxt5CMlLSXOCFt2iFFkBAAMCAAN4AAM9BA", "name": "Свинья и сладкий хлеб", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMkavjO29ImRfZnRePBnEVzWOHbT8sAAoEhaxt5CMlLHyK6o_TKGScBAAMCAAN4AAM9BA", "name": "Свин М.Джексон", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMeavjO0c-YTB71lkkfA1F8WXwShr0AAn4haxt5CMlL8IdZvaAnAT0BAAMCAAN4AAM9BA", "name": "Культурная хрюшка", "rarity": "Ничего не стоит"},
]

cards_common = [
    {"photo": "AgACAgIAAxkBAAMgavjO1bcDIGSiWO0TwMWSzoiGFL8AAn8haxt5CMlLhTvHqmT1AcYBAAMCAAN4AAM9BA", "name": "Ебаный ландрас", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMcavjOzX9PqIy-qOL0JHW5UQzKN58AAn0haxt5CMlLbJhjAAGL1RydAQADAgADeAADPQQ", "name": "Свинья с большим достоинством", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMYavjOxPr9xrvZLG_6t6n_pAAB6K-BAAJ7IWsbeQjJS-PMPDBncPVmAQADAgADeAADPQQ", "name": "Свиньи эне эне завтракают", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMWavjOwc6J5AIBQfGsOzDMiXYFLyoAAnohaxt5CMlLL5k8YAEi0ggBAAMCAAN4AAM9BA", "name": "Свиньи эне эне", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMQavjOt9xKQ5mcavzuBqJLEzskVssAAnchaxt5CMlLLoAd6ALi7JcBAAMCAAN4AAM9BA", "name": "Милый поросёнок", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMSavjOukPhHblsthFFlaSif2cTTWIAAnghaxt5CMlL1z5YPLf6njABAAMCAAN4AAM9BA", "name": "Свиньи ищут мины в Боснии", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMUavjOvuIcttjlcUTIXFIxOGiOvLQAAnkhaxt5CMlLa3RZHgHg0jEBAAMCAAN4AAM9BA", "name": "Пять бутылок водки", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMmavjO3yJULY0QcdDq4xM1I31ROXMAAoIhaxt5CMlL1a2rM88anF0BAAMCAAN4AAM9BA", "name": "Украинская степная", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMoavjO4_Lgous1QJl-G85_gDmTSkYAAoMhaxt5CMlLzux53J21gbUBAAMCAAN4AAM9BA", "name": "Свиноматка до изнасилования", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMqavjO5uSkWe7f73ow8yMajra3uEsAAoQhaxt5CMlLH9Rji0UNjv0BAAMCAAN4AAM9BA", "name": "Бибизян и свин дружат", "rarity": "Обычная"},
]

cards_unusual = [
    {"photo": "AgACAgIAAxkBAAMsavjO6tOwTsdpIDAeoo4LxQfwPkUAAoUhaxt5CMlLzja90czcWvoBAAMCAAN4AAM9BA", "name": "Бибизян на свине", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAMuavjO7gLbo4HALLTMWGHB-gjYPZYAAoYhaxt5CMlLW8mLJAWP7q4BAAMCAAN4AAM9BA", "name": "Бибизян на кабане", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM2avjO_BCn14F7QpfJxWZBimMsFWAAAoohaxt5CMlL7-A2OZkEbn4BAAMCAAN4AAM9BA", "name": "Очередь в газовую камеру", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM4avjO_nRTZjXkksOEX1HooBfOhkEAAoshaxt5CMlLGey1g3RpRXEBAAMCAAN4AAM9BA", "name": "По факту админ и свин", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM6avjPAYmaozjfzt-8sUdy6lYb4zkAAowhaxt5CMlLJkUfcqbdigMBAAMCAAN4AAM9BA", "name": "Ландрасы ебутся", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM8avjPBKzjxhhEvCTbXIvxn_AQQNIAAo0haxt5CMlLacqXYQgfZm0BAAMCAAN4AAM9BA", "name": "Жирные белые свиньи ебутся", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM0avjO-GISAx5C-r-h1k1NDI4lDzMAAokhaxt5CMlLgl-9mcKiFEgBAAMCAAN4AAM9BA", "name": "свиноматка 200", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAMyavjO9Xs8Xxxyl7EtFZf2NI_GtB4AAoghaxt5CMlL9mH81-nxqJgBAAMCAAN4AAM9BA", "name": "БИБИЗЯН АДМИН ЖЕЛАЕТ ВСЕМ МИРА", "rarity": "Необычная"},
]

cards_heroic = [
    {"photo": "AgACAgIAAxkBAAMwavjO8ZrRJtSh__E0TLo3GeeOkCoAAochaxt5CMlLac4ztm0nTTwBAAMCAAN4AAM9BA", "name": "Админ и свин", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAAN8avjTRKLFqAQGCVDCDWXTi2uiwNsAArYhaxt5CMlLJP4q6H6W64gBAAMCAAN5AAM9BA", "name": "Аватарка бота", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANAavjQWANzQWXDPycZgvrMChNpzFoAApQhaxt5CMlL26TUxpctcN0BAAMCAAN5AAM9BA", "name": "Украïньский стэповiй свiн", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAAM-avjPCIbd9072br_A9YRxU41ALUgAAo4haxt5CMlLt2NsveiWQmMBAAMCAAN3AAM9BA", "name": "Дырочка свиная", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANWavjRJSeiEw0BBw07PmYWHY9ciMEAAp8haxt5CMlLRVzHBDKNZTEBAAMCAAN5AAM9BA", "name": "Я моггаю?", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANUavjQ-Y4HaEd3V9x5srr0puvkbegAAp4haxt5CMlLiRmuUh7lhkgBAAMCAAN4AAM9BA", "name": "Тайный гость", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANeavjR3hSEE4XBBBU7hZ8STZ15tUkAAqQhaxt5CMlLrq_qckKywJ4BAAMCAAN4AAM9BA", "name": "Админ тупой и ничего придумать сам не может?", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANwavjSka2AyTyb_hcm99jTjm7dWs4AAq0haxt5CMlL5LC4aVmtXQUBAAMCAAN5AAM9BA", "name": "Ваня и ...", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANyavjSptwyby7SbaQQNKOb96OHBacAAq8haxt5CMlLVAdN6T45u_oBAAMCAAN5AAM9BA", "name": "... и Балтика", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANqavjSSP9EFH6FV2iW9sSh0DglXpAAAqohaxt5CMlLC4t_0L3tSgwBAAMCAAN5AAM9BA", "name": "Ваня фюрер", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANsavjSYAj84t5y6XhQj9ms51G8X7MAAqshaxt5CMlLaycxPNzJAqEBAAMCAAN5AAM9BA", "name": "Странность", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANuavjSeSov6NSfLBOoyg14LneVeAEAAqwhaxt5CMlLJ7z1Ul_K6WEBAAMCAAN5AAM9BA", "name": "Сажает лёгкие", "rarity": "Героизм"},
]

cards_legendary = [
    {"photo": "AgACAgIAAxkBAAMiavjO2PbsSVO0XBv-dERzqWMfzNgAAoAhaxt5CMlLd3pByCqHzFsBAAMCAAN4AAM9BA", "name": "Некая тётя Н.", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANEavjQd2mOrjtdqggsDfXFAoXWG1AAApYhaxt5CMlLsjMXEe38Vy0BAAMCAAN5AAM9BA", "name": "Воцап", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANCavjQapK-gtzjlkXo4o3pi7R0QRYAApUhaxt5CMlLGtmjHnAEYyABAAMCAAN5AAM9BA", "name": "Свин на хате", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAAN2avjS1PtCC-cBlAbHflmyoqM8p3MAArIhaxt5CMlLqOTN9fM_C-kBAAMCAAN5AAM9BA", "name": "С квасом", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAAN0avjSwk2Z6cQa1wABQvnI9uw9i3hrAAKwIWsbeQjJS6jjjuXCWcsiAQADAgADeQADPQQ", "name": "Цундере танец", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAAN6avjS7-tEr19OT74FG0yr91wfNIMAArUhaxt5CMlLYyXEaPZUb7gBAAMCAAN3AAM9BA", "name": "Ищет парня", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANiavjR_67xI1kdnQrlu3P-23QS0MEAAqYhaxt5CMlL8QIwNlIMgb0BAAMCAAN3AAM9BA", "name": "Бомжа ебучая", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANkavjSD8dfQqskbsXE-Ue35oTX9e8AAqchaxt5CMlLsqzt2nZPLtgBAAMCAAN5AAM9BA", "name": "I love gay porn", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANmavjSG8F6_40v7yvI3bzfZbUoOg4AAqghaxt5CMlL1SvqZClJ1FoBAAMCAAN3AAM9BA", "name": "Свин не считает себя свином", "rarity": "Легендарная"},
]

cards_impossible = [
    {"photo": "AgACAgIAAxkBAAN4avjS4GsX7ZLriQipGhDP5NZyPUkAArQhaxt5CMlLbxr-EmkbsDwBAAMCAAN3AAM9BA", "name": "За что мой дед воровал?", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANoavjSI527BtiF3QG1KNGpc1wfSNIAAqkhaxt5CMlLVKf3Wgf1afYBAAMCAAN3AAM9BA", "name": "Син шьюхи", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANaavjRjFoHjZEGSJNFegU4yYqa_kYAAqIhaxt5CMlL2v240F2UUV4BAAMCAAN4AAM9BA", "name": "Lite версия", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANYavjRX3FrE5_lxBNmgsYc57e8Z_sAAqEhaxt5CMlL1QM1ILs5xcsBAAMCAAN3AAM9BA", "name": "Зельц из свиней", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANOavjQsniUFXlopBF21aFb2POq8wMAApshaxt5CMlL9u7QysHgMXYBAAMCAAN3AAM9BA", "name": "Нормальный мальчик", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANQavjQuZUBCn0UKlatj_PQKIsE29AAApwhaxt5CMlLRh-fofqDAQwBAAMCAAN5AAM9BA", "name": "Свинота", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANSavjQxTGtk0Hjp5hPwmI74Pne_KkAAp0haxt5CMlLG8IXDgkWP0IBAAMCAAN5AAM9BA", "name": "Это кто нахуй?", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANgavjR772Xpia8MMBSNkF7q2HsYdoAAqUhaxt5CMlL8S2acKanOCgBAAMCAAN5AAM9BA", "name": "Смешно шо пэзда", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANIavjQmVB0yK-ftQX38qEAAfwPAqubAAKYIWsbeQjJS4WsgmRL9PkwAQADAgADdwADPQQ", "name": "Питушачьи корни", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANGavjQkWJ-Vcw24peWDmPrwHErlSAAApchaxt5CMlL27i_0ybcBQkBAAMCAAN3AAM9BA", "name": "Свинья небритая+нестриженная (добрый)", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANKavjQoCkx3rFsEg80Jy3Tzk3zcXIAApkhaxt5CMlL7hb_-f9eFAsBAAMCAAN4AAM9BA", "name": "Добрый Ваня немного свин", "rarity": "Невозможно"},
    {"photo": "AgACAgIAAxkBAANMavjQpfELBxbh6vrEgjoyF70Xb1oAApohaxt5CMlLj8T3PcKn_AsBAAMCAAN5AAM9BA", "name": "Депутат", "rarity": "Невозможно"},
]

# Особая карточка по времени (14:48 МСК)
TIME_CARD = {"photo": "AgACAgIAAxkBAANcavjRnfWN8rpI8i9gXtBf2pm7jowAAqMhaxt5CMlLUKlcBbpadbgBAAMCAAN4AAM9BA", "name": "Самая редкая карточка в мире (посхалко)", "rarity": "Секретная"}

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
            weights=[30, 25, 23, 10, 7, 5], 
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
        #f"🌙 С {TIME_WINDOW_HOUR}:{TIME_WINDOW_MINUTE_START:02d} до {TIME_WINDOW_HOUR}:{TIME_WINDOW_MINUTE_END:02d} МСК — секретная карточка по времени."
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
  
