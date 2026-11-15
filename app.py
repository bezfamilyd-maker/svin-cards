import os
import random
import time
import datetime
import threading
from zoneinfo import ZoneInfo
from flask import Flask
import telebot
from supabase import create_client, Client

# ==================== НАСТРОЙКИ ====================
TOKEN = os.environ.get('TELEGRAM_TOKEN', '9010306241:AAH49OSX-q6U1DLjTeDshgLCJrEWrEYExfs')

# Ключи Supabase (берутся из переменных окружения Render)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Кулдаун между карточками (2 часа = 7200 секунд)
COOLDOWN = 7200

# Время по МСК (ровно 1 минута: с 14:48 до 14:49)
TIME_WINDOW_HOUR = 14
TIME_WINDOW_MINUTE_START = 48
TIME_WINDOW_MINUTE_END = 49

MSK = ZoneInfo("Europe/Moscow")
CODEWORDS = {"свинья", "свин", "ваня", "@vvan_darkholme", "свинота", "хряк", "жир"}

# ==================== КАРТОЧКИ ====================
# 1. Те, что были "Ничего не стоит" + сдвинутые из "Обычных"
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
    # Сдвинутые из Обычных:
    {"photo": "AgACAgIAAxkBAAMgavjO1bcDIGSiWO0TwMWSzoiGFL8AAn8haxt5CMlLhTvHqmT1AcYBAAMCAAN4AAM9BA", "name": "Ебаный ландрас", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMcavjOzX9PqIy-qOL0JHW5UQzKN58AAn0haxt5CMlLbJhjAAGL1RydAQADAgADeAADPQQ", "name": "Свинья с большим достоинством", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMYavjOxPr9xrvZLG_6t6n_pAAB6K-BAAJ7IWsbeQjJS-PMPDBncPVmAQADAgADeAADPQQ", "name": "Свиньи эне эне завтракают", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMWavjOwc6J5AIBQfGsOzDMiXYFLyoAAnohaxt5CMlLL5k8YAEi0ggBAAMCAAN4AAM9BA", "name": "Свиньи эне эне", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMQavjOt9xKQ5mcavzuBqJLEzskVssAAnchaxt5CMlLLoAd6ALi7JcBAAMCAAN4AAM9BA", "name": "Милый поросёнок", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMSavjOukPhHblsthFFlaSif2cTTWIAAnghaxt5CMlL1z5YPLf6njABAAMCAAN4AAM9BA", "name": "Свиньи ищут мины в Боснии", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMUavjOvuIcttjlcUTIXFIxOGiOvLQAAnkhaxt5CMlLa3RZHgHg0jEBAAMCAAN4AAM9BA", "name": "Пять бутылок водки", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMmavjO3yJULY0QcdDq4xM1I31ROXMAAoIhaxt5CMlL1a2rM88anF0BAAMCAAN4AAM9BA", "name": "Украинская степная", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMoavjO4_Lgous1QJl-G85_gDmTSkYAAoMhaxt5CMlLzux53J21gbUBAAMCAAN4AAM9BA", "name": "Свиноматка до изнасилования", "rarity": "Ничего не стоит"},
    {"photo": "AgACAgIAAxkBAAMqavjO5uSkWe7f73ow8yMajra3uEsAAoQhaxt5CMlLH9Rji0UNjv0BAAMCAAN4AAM9BA", "name": "Бибизян и свин дружат", "rarity": "Ничего не стоит"},
]

# 2. Те, что были "Необычные" (теперь "Обычные")
cards_common = [
    {"photo": "AgACAgIAAxkBAAMsavjO6tOwTsdpIDAeoo4LxQfwPkUAAoUhaxt5CMlLzja90czcWvoBAAMCAAN4AAM9BA", "name": "Бибизян на свине", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMuavjO7gLbo4HALLTMWGHB-gjYPZYAAoYhaxt5CMlLW8mLJAWP7q4BAAMCAAN4AAM9BA", "name": "Бибизян на кабане", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAM2avjO_BCn14F7QpfJxWZBimMsFWAAAoohaxt5CMlL7-A2OZkEbn4BAAMCAAN4AAM9BA", "name": "Очередь в газовую камеру", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAM4avjO_nRTZjXkksOEX1HooBfOhkEAAoshaxt5CMlLGey1g3RpRXEBAAMCAAN4AAM9BA", "name": "По факту админ и свин", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAM6avjPAYmaozjfzt-8sUdy6lYb4zkAAowhaxt5CMlLJkUfcqbdigMBAAMCAAN4AAM9BA", "name": "Ландрасы ебутся", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAM8avjPBKzjxhhEvCTbXIvxn_AQQNIAAo0haxt5CMlLacqXYQgfZm0BAAMCAAN4AAM9BA", "name": "Жирные белые свиньи ебутся", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAM0avjO-GISAx5C-r-h1k1NDI4lDzMAAokhaxt5CMlLgl-9mcKiFEgBAAMCAAN4AAM9BA", "name": "свиноматка 200", "rarity": "Обычная"},
    {"photo": "AgACAgIAAxkBAAMyavjO9Xs8Xxxyl7EtFZf2NI_GtB4AAoghaxt5CMlL9mH81-nxqJgBAAMCAAN4AAM9BA", "name": "БИБИЗЯН АДМИН ЖЕЛАЕТ ВСЕМ МИРА", "rarity": "Обычная"},
]

# 3. Те, что были "Героизм" (теперь "Необычные")
cards_unusual = [
    {"photo": "AgACAgIAAxkBAAMwavjO8ZrRJtSh__E0TLo3GeeOkCoAAochaxt5CMlLac4ztm0nTTwBAAMCAAN4AAM9BA", "name": "Админ и свин", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAN8avjTRKLFqAQGCVDCDWXTi2uiwNsAArYhaxt5CMlLJP4q6H6W64gBAAMCAAN5AAM9BA", "name": "Аватарка бота", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANAavjQWANzQWXDPycZgvrMChNpzFoAApQhaxt5CMlL26TUxpctcN0BAAMCAAN5AAM9BA", "name": "Украïньский стэповiй свiн", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAAM-avjPCIbd9072br_A9YRxU41ALUgAAo4haxt5CMlLt2NsveiWQmMBAAMCAAN3AAM9BA", "name": "Дырочка свиная", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANWavjRJSeiEw0BBw07PmYWHY9ciMEAAp8haxt5CMlLRVzHBDKNZTEBAAMCAAN5AAM9BA", "name": "Я моггаю?", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANUavjQ-Y4HaEd3V9x5srr0puvkbegAAp4haxt5CMlLiRmuUh7lhkgBAAMCAAN4AAM9BA", "name": "Тайный гость", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANeavjR3hSEE4XBBBU7hZ8STZ15tUkAAqQhaxt5CMlLrq_qckKywJ4BAAMCAAN4AAM9BA", "name": "Админ тупой и ничего придумать сам не может?", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANwavjSka2AyTyb_hcm99jTjm7dWs4AAq0haxt5CMlL5LC4aVmtXQUBAAMCAAN5AAM9BA", "name": "Ваня и ...", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANyavjSptwyby7SbaQQNKOb96OHBacAAq8haxt5CMlLVAdN6T45u_oBAAMCAAN5AAM9BA", "name": "... и Балтика", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANqavjSSP9EFH6FV2iW9sSh0DglXpAAAqohaxt5CMlLC4t_0L3tSgwBAAMCAAN5AAM9BA", "name": "Ваня фюрер", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANsavjSYAj84t5y6XhQj9ms51G8X7MAAqshaxt5CMlLaycxPNzJAqEBAAMCAAN5AAM9BA", "name": "Странность", "rarity": "Необычная"},
    {"photo": "AgACAgIAAxkBAANuavjSeSov6NSfLBOoyg14LneVeAEAAqwhaxt5CMlLJ7z1Ul_K6WEBAAMCAAN5AAM9BA", "name": "Сажает лёгкие", "rarity": "Необычная"},
]

# 4. Те, что были "Легендарные" (теперь "Героизм")
cards_heroic = [
    {"photo": "AgACAgIAAxkBAAMiavjO2PbsSVO0XBv-dERzqWMfzNgAAoAhaxt5CMlLd3pByCqHzFsBAAMCAAN4AAM9BA", "name": "Некая тётя Н.", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANEavjQd2mOrjtdqggsDfXFAoXWG1AAApYhaxt5CMlLsjMXEe38Vy0BAAMCAAN5AAM9BA", "name": "Воцап", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANCavjQapK-gtzjlkXo4o3pi7R0QRYAApUhaxt5CMlLGtmjHnAEYyABAAMCAAN5AAM9BA", "name": "Свин на хате", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAAN2avjS1PtCC-cBlAbHflmyoqM8p3MAArIhaxt5CMlLqOTN9fM_C-kBAAMCAAN5AAM9BA", "name": "С квасом", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAAN0avjSwk2Z6cQa1wABQvnI9uw9i3hrAAKwIWsbeQjJS6jjjuXCWcsiAQADAgADeQADPQQ", "name": "Цундере танец", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAAN6avjS7-tEr19OT74FG0yr91wfNIMAArUhaxt5CMlLYyXEaPZUb7gBAAMCAAN3AAM9BA", "name": "Ищет парня", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANiavjR_67xI1kdnQrlu3P-23QS0MEAAqYhaxt5CMlL8QIwNlIMgb0BAAMCAAN3AAM9BA", "name": "Бомжа ебучая", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANkavjSD8dfQqskbsXE-Ue35oTX9e8AAqchaxt5CMlLsqzt2nZPLtgBAAMCAAN5AAM9BA", "name": "I love gay porn", "rarity": "Героизм"},
    {"photo": "AgACAgIAAxkBAANmavjSG8F6_40v7yvI3bzfZbUoOg4AAqghaxt5CMlL1SvqZClJ1FoBAAMCAAN3AAM9BA", "name": "Свин не считает себя свином", "rarity": "Героизм"},
]

# 5. Те, что были "Невозможно" (теперь "Легендарные")
cards_legendary = [
    {"photo": "AgACAgIAAxkBAAN4avjS4GsX7ZLriQipGhDP5NZyPUkAArQhaxt5CMlLbxr-EmkbsDwBAAMCAAN3AAM9BA", "name": "За что мой дед воровал?", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANoavjSI527BtiF3QG1KNGpc1wfSNIAAqkhaxt5CMlLVKf3Wgf1afYBAAMCAAN3AAM9BA", "name": "Син шьюхи", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANaavjRjFoHjZEGSJNFegU4yYqa_kYAAqIhaxt5CMlL2v240F2UUV4BAAMCAAN4AAM9BA", "name": "Lite версия", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANYavjRX3FrE5_lxBNmgsYc57e8Z_sAAqEhaxt5CMlL1QM1ILs5xcsBAAMCAAN3AAM9BA", "name": "Зельц из свиней", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANOavjQsniUFXlopBF21aFb2POq8wMAApshaxt5CMlL9u7QysHgMXYBAAMCAAN3AAM9BA", "name": "Нормальный мальчик", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANQavjQuZUBCn0UKlatj_PQKIsE29AAApwhaxt5CMlLRh-fofqDAQwBAAMCAAN5AAM9BA", "name": "Свинота", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANSavjQxTGtk0Hjp5hPwmI74Pne_KkAAp0haxt5CMlLG8IXDgkWP0IBAAMCAAN5AAM9BA", "name": "Это кто нахуй?", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANgavjR772Xpia8MMBSNkF7q2HsYdoAAqUhaxt5CMlL8S2acKanOCgBAAMCAAN5AAM9BA", "name": "Смешно шо пэзда", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANIavjQmVB0yK-ftQX38qEAAfwPAqubAAKYIWsbeQjJS4WsgmRL9PkwAQADAgADdwADPQQ", "name": "Питушачьи корни", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANGavjQkWJ-Vcw24peWDmPrwHErlSAAApchaxt5CMlL27i_0ybcBQkBAAMCAAN3AAM9BA", "name": "Свинья небритая+нестриженная (добрый)", "rarity": "Легендарная"},
    {"photo": "AgACAgIAAxkBAANKavjQoCkx3rFsEg80Jy3Tzk3zcXIAApkhaxt5CMlL7hb_-f9eFAsBAAMCAAN4AAM9BA", "name": "Добрый Ваня немного свин", "rarity": "Легендарная"},
]

# 6. Оставляем ОДНУ карточку в "Невозможно"
cards_impossible = [
    {"photo": "AgACAgIAAxkBAANMavjQpfELBxbh6vrEgjoyF70Xb1oAApohaxt5CMlLj8T3PcKn_AsBAAMCAAN5AAM9BA", "name": "Депутат", "rarity": "Невозможно"},
]

# Особая карточка по времени (14:48 МСК)
TIME_CARD = {"photo": "AgACAgIAAxkBAANcavjRnfWN8rpI8i9gXtBf2pm7jowAAqMhaxt5CMlLUKlcBbpadbgBAAMCAAN4AAM9BA", "name": "Самая редкая карточка в мире (посхалко)", "rarity": "Секретная"}

# ==================== БОТ И БАЗА ====================
bot = telebot.TeleBot(TOKEN)

# Подключение к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    
    # Ищем пользователя в Supabase
    response = supabase.table('users').select('last_draw_time').eq('user_id', uid).execute()
    
    if not response.data:
        # Если пользователя нет, добавляем
        supabase.table('users').insert({'user_id': uid, 'last_draw_time': 0}).execute()
        last_time = 0
    else:
        last_time = response.data[0]['last_draw_time']

    if now_ts - last_time < COOLDOWN:
        return None, "cooldown", int(COOLDOWN - (now_ts - last_time))

    if in_time_window():
        card, reason = TIME_CARD, "time"
    else:
        # Шансы не меняем (25, 24, 23, 15, 8, 5)
        rarity_choice = random.choices(
            ["nothing", "common", "unusual", "heroic", "legendary", "impossible"], 
            weights=[25, 24, 23, 15, 8, 5], 
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

    # Обновляем время в Supabase
    supabase.table('users').update({'last_draw_time': now_ts}).eq('user_id', uid).execute()
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
        "🐷 <b>Прiвiт! Цэ я, свинота, карточный бот для твоего чата</b>\n\n"
        "Напиши 'свинья', чтобы подрочить меня\n\n"
        "P.s. Для связи с разработчиком отправь команду /help и иди нахуй"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uid = message.from_user.id
    response = supabase.table('users').select('last_draw_time').eq('user_id', uid).execute()
    
    if not response.data:
        bot.reply_to(message, "Напиши «свинья», чтобы начать либо иди нахуй, чмо!")
        return
        
    last_time = response.data[0]['last_draw_time']
    cooldown_left = max(0, int(COOLDOWN - (time.time() - last_time)))
    
    text = "📊 <b>Твоя статистика</b>\n\n"
    if cooldown_left > 0:
        text += f"⏳ Кулдаун: {format_remaining(cooldown_left)}"
    else:
        text += "⚠️Нужно фармить свиней!"
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.lower().strip() not in CODEWORDS:
        return
    uid = message.from_user.id
    card, reason, cooldown_left = get_card_and_update(uid)
    
    if card is None:
        # Рандом 50/50 для выбора текста кулдауна
        if random.choice([True, False]):
            msg_text = f"⏳ Еще рано, хуйня. Жди: <b>{format_remaining(cooldown_left)}</b>."
        else:
            msg_text = f"Ты не голоден, тебе просто скучно. Жди: <b>{format_remaining(cooldown_left)}</b>."
            
        bot.reply_to(message, msg_text, parse_mode='HTML')
        return
        
    # Выбираем эмодзи для редкости
    rarity = card['rarity']
    if rarity == "Ничего не стоит":
        icon = "🗑"
    elif rarity == "Обычная":
        icon = "⚪"
    elif rarity == "Необычная":
        icon = "🔵"
    elif rarity == "Героизм":
        icon = "🟣"
    elif rarity == "Легендарная":
        icon = "🟡"
    elif rarity == "Невозможно":
        icon = "⚫️"
    else:
        icon = "🌟" # Секретная

    caption = f"{icon} <b>{card['name']}</b>\nРедкость: {card['rarity']}"
    
    if reason == "time":
        caption = "🌙 <b>Секретная карточка по времени!</b>\n\n" + caption
    
    bot.send_photo(message.chat.id, card["photo"], caption=caption, parse_mode='HTML')

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🐷 Svin Cards запущен...")
    bot.infinity_polling()
