import os
import random
import time
import datetime
import threading
from zoneinfo import ZoneInfo
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client

# ==================== НАСТРОЙКИ ====================
TOKEN = os.environ.get('TELEGRAM_TOKEN', '9010306241:AAH49OSX-q6U1DLjTeDshgLCJrEWrEYExfs')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

COOLDOWN = 7200
TIME_WINDOW_HOUR = 14
TIME_WINDOW_MINUTE_START = 48
TIME_WINDOW_MINUTE_END = 49

MSK = ZoneInfo("Europe/Moscow")
CODEWORDS = {"свинья", "свин", "ваня", "@vvan_darkholme", "свинота", "хряк", "жир"}
ALLOWED_CHAT_ID = -1002541291432

RARITY_LIMITS = {
    "Ничего не стоит": 20, "Обычная": 40, "Необычная": 60,
    "Героизм": 70, "Легендарная": 90, "Невозможно": 100, "Секретная": 100
}

# (Списки карточек cards_nothing, cards_common и т.д. оставляем без изменений, я их сократил для примера)
cards_nothing = [
    {"photo": "AgACAgIAAxkBAAMCavjOkT35v2AoMbS23FY3YFDlg00AAmshaxt5CMlL6JsNIfTs94YBAAMCAAN5AAM9BA", "name": "Кабан обыкновенный жирный", "rarity": "Ничего не стоит", "fat": 8, "profit": 1, "culture": 1},
    # ... остальные карточки ...
]
# ВАЖНО: Скопируйте сюда ВСЕ ваши карточки из предыдущих версий!
cards_common = []
cards_unusual = []
cards_heroic = []
cards_legendary = []
cards_impossible = []
TIME_CARD = {"photo": "", "name": "Самая редкая карточка в мире (посхалко)", "rarity": "Секретная", "fat": 100, "profit": 100, "culture": 100}

# ==================== БОТ И БАЗА ====================
bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== FLASK ====================
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

# ==================== ЛОГИКА ВЫПАДЕНИЯ ====================
def in_time_window():
    now = datetime.datetime.now(MSK)
    return (now.hour == TIME_WINDOW_HOUR and 
            TIME_WINDOW_MINUTE_START <= now.minute < TIME_WINDOW_MINUTE_END)

def get_card_and_update(uid):
    now_ts = time.time()
    response = supabase.table('users').select('last_draw_time').eq('user_id', uid).execute()
    if not response.data:
        supabase.table('users').insert({'user_id': uid, 'last_draw_time': 0}).execute()
        last_time = 0
    else:
        last_time = response.data[0]['last_draw_time']

    if now_ts - last_time < COOLDOWN:
        return None, "cooldown", int(COOLDOWN - (now_ts - last_time))

    if in_time_window():
        card, reason = TIME_CARD, "time"
    else:
        rarity_choice = random.choices(["nothing", "common", "unusual", "heroic", "legendary", "impossible"], weights=[50, 29, 10, 5, 4, 2], k=1)[0]
        if rarity_choice == "nothing": card = random.choice(cards_nothing)
        elif rarity_choice == "common": card = random.choice(cards_common)
        elif rarity_choice == "unusual": card = random.choice(cards_unusual)
        elif rarity_choice == "heroic": card = random.choice(cards_heroic)
        elif rarity_choice == "legendary": card = random.choice(cards_legendary)
        else: card = random.choice(cards_impossible)
        reason = "random"

    supabase.table('users').update({'last_draw_time': now_ts}).eq('user_id', uid).execute()

    inv_resp = supabase.table('inventory').select('*').eq('user_id', uid).eq('card_name', card['name']).execute()
    upgrade_msg = ""
    if inv_resp.data:
        existing = inv_resp.data[0]
        fat_b, profit_b, culture_b = existing['fat_bonus'], existing['profit_bonus'], existing['culture_bonus']
        limit = RARITY_LIMITS[card['rarity']]
        upgradable = []
        if card['fat'] + fat_b < limit: upgradable.append('fat')
        if card['profit'] + profit_b < limit: upgradable.append('profit')
        if card['culture'] + culture_b < limit: upgradable.append('culture')
        
        if upgradable:
            stat = random.choice(upgradable)
            points = random.choice([2, 3])
            if stat == 'fat': fat_b += points; upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Жирность повышена на +{points}."
            elif stat == 'profit': profit_b += points; upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Выгодность повышена на +{points}."
            else: culture_b += points; upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Культурность повышена на +{points}."
            supabase.table('inventory').update({'fat_bonus': fat_b, 'profit_bonus': profit_b, 'culture_bonus': culture_b}).eq('id', existing['id']).execute()
        else:
            upgrade_msg = "\n\n🚫 <b>Дубликат!</b> Но твоя карточка уже полностью прокачана."
    else:
        supabase.table('inventory').insert({'user_id': uid, 'card_name': card['name'], 'card_rarity': card['rarity'], 'card_photo': card['photo'], 'fat_bonus': 0, 'profit_bonus': 0, 'culture_bonus': 0}).execute()
    return card, reason, upgrade_msg

def format_remaining(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h: return f"{h} ч {m} мин"
    if m: return f"{m} мин"
    return f"{s} сек"

# ==================== ОБРАБОТЧИКИ ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    text = "🐷 <b>Прiвiт! Цэ я, свинота, карточный бот</b>\n\nНапиши 'свинья', чтобы получить карточку\nДля инвентаря: /stats"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uid = message.from_user.id
    inv_resp = supabase.table('inventory').select('card_rarity').eq('user_id', uid).execute()
    if not inv_resp.data:
        bot.reply_to(message, "У тебя пока нет карточек!")
        return
    rarities = set(item['card_rarity'] for item in inv_resp.data)
    markup = InlineKeyboardMarkup(row_width=2)
    for r in rarities:
        icon = "🗑" if r == "Ничего не стоит" else "⚪" if r == "Обычная" else "🔵" if r == "Необычная" else "🟣" if r == "Героизм" else "🟡" if r == "Легендарная" else "⚫️" if r == "Невозможно" else "🌟"
        markup.add(InlineKeyboardButton(text=f"{icon} {r}", callback_data=f"rarity_{r}"))
    bot.send_message(message.chat.id, f"📊 <b>Инвентарь</b>\nСобрано: {len(inv_resp.data)}", reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('rarity_'))
def callback_rarity(call):
    uid = call.from_user.id
    rarity = call.data.split('_', 1)[1] 
    inv_resp = supabase.table('inventory').select('card_name').eq('user_id', uid).eq('card_rarity', rarity).execute()
    if not inv_resp.data:
        bot.answer_callback_query(call.id, "Нет карточек этой редкости.")
        return
    markup = InlineKeyboardMarkup(row_width=2)
    for item in inv_resp.data:
        markup.add(InlineKeyboardButton(text=item['card_name'], callback_data=f"card_{item['card_name']}"))
    markup.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_rarities"))
    bot.edit_message_text(f"Карточки <b>{rarity}</b>:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('card_'))
def callback_card(call):
    uid = call.from_user.id
    card_name = call.data.replace('card_', '')
    inv_resp = supabase.table('inventory').select('*').eq('user_id', uid).eq('card_name', card_name).execute()
    if not inv_resp.data: return
    data = inv_resp.data[0]
    all_cards = cards_nothing + cards_common + cards_unusual + cards_heroic + cards_legendary + cards_impossible + [TIME_CARD]
    base_card = next((c for c in all_cards if c['name'] == card_name), None)
    caption = f"🎴 <b>{data['card_name']}</b>\nРедкость: {data['card_rarity']}\n\n🐷 Жирность: {base_card['fat']} (+{data['fat_bonus']})\n💰 Выгодность: {base_card['profit']} (+{data['profit_bonus']})\n🎩 Культурность: {base_card['culture']} (+{data['culture_bonus']})"
    bot.send_photo(call.message.chat.id, data['card_photo'], caption=caption, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_rarities')
def callback_back_list(call):
    uid = call.from_user.id
    inv_resp = supabase.table('inventory').select('card_rarity').eq('user_id', uid).execute()
    rarities = set(item['card_rarity'] for item in inv_resp.data)
    markup = InlineKeyboardMarkup(row_width=2)
    for r in rarities:
        icon = "🗑" if r == "Ничего не стоит" else "⚪" if r == "Обычная" else "🔵" if r == "Необычная" else "🟣" if r == "Героизм" else "🟡" if r == "Легендарная" else "⚫️" if r == "Невозможно" else "🌟"
        markup.add(InlineKeyboardButton(text=f"{icon} {r}", callback_data=f"rarity_{r}"))
    bot.edit_message_text(f"📊 <b>Инвентарь</b>\nСобрано: {len(inv_resp.data)}", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

# ==================== ВЫДАЧА КАРТОЧЕК ====================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.lower().strip() not in CODEWORDS: return
    uid = message.from_user.id
    card, reason, extra_msg = get_card_and_update(uid)
    if card is None:
        msg_text = f"⏳ Еще рано, хуйня. Жди: <b>{format_remaining(extra_msg)}</b>." if random.choice([True, False]) else f"Ты не голоден, тебе просто скучно. Жди: <b>{format_remaining(extra_msg)}</b>."
        bot.reply_to(message, msg_text, parse_mode='HTML')
        return
    icon = "🗑" if card['rarity'] == "Ничего не стоит" else "⚪" if card['rarity'] == "Обычная" else "🔵" if card['rarity'] == "Необычная" else "🟣" if card['rarity'] == "Героизм" else "🟡" if card['rarity'] == "Легендарная" else "⚫️" if card['rarity'] == "Невозможно" else "🌟"
    caption = f"{icon} <b>{card['name']}</b>\nРедкость: {card['rarity']}\n\n🐷 Жирность: {card['fat']}\n💰 Выгодность: {card['profit']}\n🎩 Культурность: {card['culture']}{extra_msg}"
    if reason == "time": caption = "🌙 <b>Секретная карточка!</b>\n\n" + caption
    bot.send_photo(message.chat.id, card["photo"], caption=caption, parse_mode='HTML')

# ==================== PVP БОИ ====================
@bot.message_handler(commands=['battle'])
def cmd_battle(message):
    try:
        # Убрали проверку на message.text, так как мы точно знаем, что это команда
        if not message.reply_to_message:
            bot.reply_to(message, "Ответь на сообщение и напиши `/battle`.", parse_mode='Markdown')
            return
            
        if message.reply_to_message.from_user is None:
            bot.reply_to(message, "Вызывай конкретного человека, долбоёб.")
            return
            
        if message.reply_to_message.from_user.id == message.from_user.id:
            bot.reply_to(message, "Сам себе дрочить собрался, еблан?")
            return
        
        enemy_id = message.reply_to_message.from_user.id
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(text="✅ Газ ехала", callback_data=f"acc_{message.from_user.id}_{enemy_id}"), 
            InlineKeyboardButton(text="❌ Я питух", callback_data=f"dec_{message.from_user.id}")
        )
        bot.send_message(
            message.chat.id, 
            f"⚔️ <b>{message.from_user.first_name}</b> вызывает на бой <b>{message.reply_to_message.from_user.first_name}</b>!", 
            reply_markup=markup, 
            parse_mode='HTML'
        )
    except Exception as e:
        bot.reply_to(message, f"⚠️ ОШИБКА В КОДЕ:\n\n{e}", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('acc_'))
def callback_accept(call):
    _, p1, p2 = call.data.split('_')
    p1, p2 = int(p1), int(p2)
    if call.from_user.id != p2:
        bot.answer_callback_query(call.id, "Убери сардельки с чужих кнопок, хуйня.")
        return
    
    inv1 = supabase.table('inventory').select('card_name').eq('user_id', p1).execute()
    inv2 = supabase.table('inventory').select('card_name').eq('user_id', p2).execute()
    if len(inv1.data) < 3 or len(inv2.data) < 3:
        bot.answer_callback_query(call.id, "Нищета, иди нахуй! Нудно минимум 3 карточки", show_alert=True)
        return

    d1 = random.sample([c['card_name'] for c in inv1.data], min(10, len(inv1.data)))
    d2 = random.sample([c['card_name'] for c in inv2.data], min(10, len(inv2.data)))
    
    resp = supabase.table('battles').insert({"chat_id": call.message.chat.id, "player1_id": p1, "player2_id": p2, "p1_cards": d1, "p2_cards": d2, "status": "choosing"}).execute()
    b_id = resp.data[0]['battle_id']
    
    bot.edit_message_text("⚔️ <b>Бой начался!</b> Игроки получают карточки в личку.", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    send_hand(p1, d1, b_id, 1); send_hand(p2, d2, b_id, 2)

def send_hand(uid, deck, b_id, p_num):
    markup = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(deck):
        markup.add(InlineKeyboardButton(text=f"◻️ {c}", callback_data=f"pick_{b_id}_{p_num}_{i}"))
    try: bot.send_message(uid, "🃏♠️ Выбери 3 свиньи:", reply_markup=markup)
    except: bot.send_message(ALLOWED_CHAT_ID, f"Пидор {uid} нихуя не нажал в личке!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pick_'))
def callback_pick(call):
    _, b_id, p_num, c_idx = call.data.split('_')
    b_id, p_num, c_idx = int(b_id), int(p_num), int(c_idx)
    b = supabase.table('battles').select('*').eq('battle_id', b_id).execute().data[0]
    if (p_num == 1 and call.from_user.id != b['player1_id']) or (p_num == 2 and call.from_user.id != b['player2_id']):
        bot.answer_callback_query(call.id, "Убери сардельки с чужих свиней!")
        return
    hand_key, deck_key = f'p{p_num}_hand', f'p{p_num}_cards'
    hand, deck = b[hand_key], b[deck_key]
    card = deck[c_idx]
    if card in hand:
        hand.remove(card)
    else:
        if len(hand) >= 3:
            bot.answer_callback_query(call.id, "Уже 3 свиньи, еблан.")
            return
        hand.append(card)
    supabase.table('battles').update({hand_key: hand}).eq('battle_id', b_id).execute()
    
    markup = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(deck):
        markup.add(InlineKeyboardButton(text=f"{'✅' if c in hand else '◻️'} {c}", callback_data=f"pick_{b_id}_{p_num}_{i}"))
    if len(hand) == 3:
        markup.add(InlineKeyboardButton(text="🔥 В БОЙ", callback_data=f"rdy_{b_id}_{p_num}"))
    bot.edit_message_text("🃏 Выбери 3 карточки:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rdy_'))
def callback_ready(call):
    _, b_id, p_num = call.data.split('_')
    b_id, p_num = int(b_id), int(p_num)
    supabase.table('battles').update({f"p{p_num}_ready": True}).eq('battle_id', b_id).execute()
    b = supabase.table('battles').select('*').eq('battle_id', b_id).execute().data[0]
    bot.edit_message_text("⏳ Ждем соперника...", call.message.chat.id, call.message.message_id)
    if b['p1_ready'] and b['p2_ready']:
        start_round(b_id, b['chat_id'], 1, b['p1_hand'], b['p2_hand'])

def start_round(b_id, chat_id, r_num, hand1, hand2):
    stat = random.choice(["Жирность", "Выгодность", "Культурность"])
    supabase.table('battles').update({"current_round": r_num, "status": stat, "p1_choice": None, "p2_choice": None}).eq('battle_id', b_id).execute()
    bot.send_message(chat_id, f"⚔️ <b>Раунд {r_num}!</b>\nСравниваем: <b>{stat}</b>.\nЖдем выбор пидоров...", parse_mode='HTML')
    
    markup = InlineKeyboardMarkup()
    for c in hand1: markup.add(InlineKeyboardButton(text=c, callback_data=f"rch_{b_id}_1_{c}"))
    try: bot.send_message(supabase.table('battles').select('player1_id').eq('battle_id', b_id).execute().data[0]['player1_id'], f"Раунд {r_num}: выбери свинью ({stat})", reply_markup=markup)
    except: pass

    markup = InlineKeyboardMarkup()
    for c in hand2: markup.add(InlineKeyboardButton(text=c, callback_data=f"rch_{b_id}_2_{c}"))
    try: bot.send_message(supabase.table('battles').select('player2_id').eq('battle_id', b_id).execute().data[0]['player2_id'], f"Раунд {r_num}: выбери свинью ({stat})", reply_markup=markup)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('rch_'))
def callback_round_choice(call):
    _, b_id, p_num, card = call.data.split('_', 3)
    b_id, p_num = int(b_id), int(p_num)
    b = supabase.table('battles').select('*').eq('battle_id', b_id).execute().data[0]
    supabase.table('battles').update({f"p{p_num}_choice": card}).eq('battle_id', b_id).execute()
    bot.edit_message_text(f"Ты выбрал: <b>{card}</b>. Ждем...", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    if b[f"p{3-p_num}_choice"]:
        resolve_round(b_id, b['chat_id'])

def resolve_round(b_id, chat_id):
    b = supabase.table('battles').select('*').eq('battle_id', b_id).execute().data[0]
    stat = b['status'] 
    all_c = cards_nothing + cards_common + cards_unusual + cards_heroic + cards_legendary + cards_impossible + [TIME_CARD]
    
    def get_val(uid, c_name, stat):
        inv = supabase.table('inventory').select('*').eq('user_id', uid).eq('card_name', c_name).execute().data[0]
        base = next(c for c in all_c if c['name'] == c_name)
        key = 'fat' if stat == "Жирность" else 'profit' if stat == "Выгодность" else 'culture'
        return base[key] + inv[f'{key}_bonus']

    v1 = get_val(b['player1_id'], b['p1_choice'], stat)
    v2 = get_val(b['player2_id'], b['p2_choice'], stat)
    
    res = f"<b>Раунд {b['current_round']} ({stat}):</b>\nХуеглот 1: {v1} | Хуеглот 2: {v2}\n"
    w1, w2 = b['p1_wins'], b['p2_wins']
    if v1 > v2: w1 += 1; res += "🏆 Победило чмо номер 1!"
    elif v2 > v1: w2 += 1; res += "🏆 Победил чмо номер 2!"
    else: res += "🤝 Победила питушиная дружба!"
    
    supabase.table('battles').update({"p1_wins": w1, "p2_wins": w2}).eq('battle_id', b_id).execute()
    bot.send_message(chat_id, res, parse_mode='HTML')

    if w1 >= 2 or w2 >= 2 or b['current_round'] >= 3:
        finish_battle(b_id, chat_id, w1, w2)
    else:
        start_round(b_id, chat_id, b['current_round'] + 1, b['p1_hand'], b['p2_hand'])

# ==================== СМЕРТЕЛЬНЫЙ ИСХОД ====================
def finish_battle(b_id, chat_id, w1, w2):
    b = supabase.table('battles').select('*').eq('battle_id', b_id).execute().data[0]
    all_c = cards_nothing + cards_common + cards_unusual + cards_heroic + cards_legendary + cards_impossible + [TIME_CARD]
    
    if w1 == w2:
        bot.send_message(chat_id, f"🏁 <b>Бой окончен!</b> Счет {w1}:{w2}. Ничья! Никто не потерял свиней.", parse_mode='HTML')
    else:
        if w1 > w2:
            winner_id, loser_id, winner_hand = b['player1_id'], b['player2_id'], b['p1_hand']
        else:
            winner_id, loser_id, winner_hand = b['player2_id'], b['player1_id'], b['p2_hand']

        bot.send_message(chat_id, f"🏁 <b>Свинобойня окончена!</b> Счет {w1}:{w2}. Победил {winner_id}!", parse_mode='HTML')

        loser_hand = b['p1_hand'] if loser_id == b['player1_id'] else b['p2_hand']
        
        def calc_power(c_name):
            inv = supabase.table('inventory').select('*').eq('user_id', loser_id).eq('card_name', c_name).execute().data
            if not inv: return 0 # ЗАЩИТА ОТ ОШИБКИ
            inv = inv[0]
            base = next((c for c in all_c if c['name'] == c_name), None)
            return (base['fat'] + inv['fat_bonus']) + (base['profit'] + inv['profit_bonus']) + (base['culture'] + inv['culture_bonus'])

        strongest_card = max(loser_hand, key=calc_power)
        supabase.table('inventory').delete().eq('user_id', loser_id).eq('card_name', strongest_card).execute()
        
        bot.send_message(chat_id, f"💀 <b>СМЕРТЕЛЬНЫЙ ИСХОД:</b>\nПроигравший ({loser_id}) навсегда потерял свинью (лох ебаный) <b>«{strongest_card}»</b>!", parse_mode='HTML')

        def calc_power_win(c_name):
            inv = supabase.table('inventory').select('*').eq('user_id', winner_id).eq('card_name', c_name).execute().data
            if not inv: return 0 # ЗАЩИТА ОТ ОШИБКИ
            inv = inv[0]
            base = next((c for c in all_c if c['name'] == c_name), None)
            return (base['fat'] + inv['fat_bonus']) + (base['profit'] + inv['profit_bonus']) + (base['culture'] + inv['culture_bonus'])

        weakest_card_name = min(winner_hand, key=calc_power_win)
        
        inv_win = supabase.table('inventory').select('*').eq('user_id', winner_id).eq('card_name', weakest_card_name).execute().data[0]
        base_win = next(c for c in all_c if c['name'] == weakest_card_name)
        
        boost_msg = f"🎁 <b>Награда поебителю:</b> Твоя самая слабая свинья (<b>«{weakest_card_name}»</b>) прокачана:"
        new_fat, new_profit, new_culture = inv_win['fat_bonus'], inv_win['profit_bonus'], inv_win['culture_bonus']
        
        if random.choice([True, False]):
            points = random.choice([1, 2])
            new_fat += points
            boost_msg += f"\n🐷 +{points} к Жирности!"
        if random.choice([True, False]):
            points = random.choice([1, 2])
            new_profit += points
            boost_msg += f"\n💰 +{points} к Выгодности!"
        if random.choice([True, False]):
            points = random.choice([1, 2])
            new_culture += points
            boost_msg += f"\n🎩 +{points} к Культурности!"

        supabase.table('inventory').update({'fat_bonus': new_fat, 'profit_bonus': new_profit, 'culture_bonus': new_culture}).eq('id', inv_win['id']).execute()
        bot.send_message(chat_id, boost_msg, parse_mode='HTML')

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    RENDER_URL = "https://svin-cards.onrender.com" 
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

    @app.route(f'/{TOKEN}', methods=['POST'])
    def getMessage():
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200

    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
