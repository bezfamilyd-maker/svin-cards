import os
import random
import time
import datetime
import threading
from zoneinfo import ZoneInfo
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client

# ==================== НАСТРОЙКИ ====================
TOKEN = os.environ.get('TELEGRAM_TOKEN', '9010306241:AAH49OSX-q6U1DLjTeDshgLCJrEWrEYExfs')

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

COOLDOWN = 7200  # 2 часа

TIME_WINDOW_HOUR = 14
TIME_WINDOW_MINUTE_START = 48
TIME_WINDOW_MINUTE_END = 49

MSK = ZoneInfo("Europe/Moscow")
CODEWORDS = {"свинья", "свин", "ваня", "@vvan_darkholme", "свинота", "хряк", "жир"}

RARITY_LIMITS = {
    "Ничего не стоит": 20,
    "Обычная": 40,
    "Необычная": 60,
    "Героизм": 70,
    "Легендарная": 90,
    "Невозможно": 100,
    "Секретная": 100
}

# ==================== КАРТОЧКИ С ХАРАКТЕРИСТИКАМИ ====================
cards_nothing = [
    {"photo": "AgACAgIAAxkBAAMCavjOkT35v2AoMbS23FY3YFDlg00AAmshaxt5CMlL6JsNIfTs94YBAAMCAAN5AAM9BA", "name": "Кабан обыкновенный жирный", "rarity": "Ничего не стоит", "fat": 8, "profit": 1, "culture": 1},
    {"photo": "AgACAgIAAxkBAAMEavjOmJsplG8HrkuTK0lMlQpCrhoAAmwhaxt5CMlL6hBVPmgtszQBAAMCAAN5AAM9BA", "name": "Милый кабанчик", "rarity": "Ничего не стоит", "fat": 2, "profit": 3, "culture": 5},
    {"photo": "AgACAgIAAxkBAAMGavjOnceIKo-spJU7ENVBBWcH_JwAAm0haxt5CMlL1rRC0ZsyLnABAAMCAAN5AAM9BA", "name": "Нестриженная свинья (стрижка в 6)", "rarity": "Ничего не стоит", "fat": 5, "profit": 1, "culture": 0},
    {"photo": "AgACAgIAAxkBAAMIavjOojiWvaZHfa2K_qML4MCsQdYAAm4haxt5CMlLtNpfcghLloABAAMCAAN5AAM9BA", "name": "Исхудавшая свинья не ела 3 минуты", "rarity": "Ничего не стоит", "fat": 0, "profit": 2, "culture": 1},
    {"photo": "AgACAgIAAxkBAAMKavjOp9Xnjo60_mAUhSVlC1j4FmIAAnIhaxt5CMlL7jdJ3SeAU8wBAAMCAAN4AAM9BA", "name": "Свиноматка обыкновенная", "rarity": "Ничего не стоит", "fat": 6, "profit": 2, "culture": 2},
    {"photo": "AgACAgIAAxkBAAMMavjOrjxg9vArNTFyUQ1_tNFraPMAAnUhaxt5CMlLfuaAf-5sfGUBAAMCAAN4AAM9BA", "name": "Базовый выводок", "rarity": "Ничего не стоит", "fat": 4, "profit": 3, "culture": 3},
    {"photo": "AgACAgIAAxkBAAMOavjOs8zcSKUj5BHzrwFleaQSwPoAAnYhaxt5CMlLyeIW1IRsxlEBAAMCAAN4AAM9BA", "name": "Негры свиноты", "rarity": "Ничего не стоит", "fat": 3, "profit": 1, "culture": 0},
    {"photo": "AgACAgIAAxkBAAMaavjOyRGbLwGsJs72VMi8waBAdfAAAnwhaxt5CMlLSXOCFt2iFFkBAAMCAAN4AAM9BA", "name": "Свинья и сладкий хлеб", "rarity": "Ничего не стоит", "fat": 7, "profit": 2, "culture": 1},
    {"photo": "AgACAgIAAxkBAAMkavjO29ImRfZnRePBnEVzWOHbT8sAAoEhaxt5CMlLHyK6o_TKGScBAAMCAAN4AAM9BA", "name": "Свин М.Джексон", "rarity": "Ничего не стоит", "fat": 2, "profit": 3, "culture": 4},
    {"photo": "AgACAgIAAxkBAAMeavjO0c-YTB71lkkfA1F8WXwShr0AAn4haxt5CMlL8IdZvaAnAT0BAAMCAAN4AAM9BA", "name": "Культурная хрюшка", "rarity": "Ничего не стоит", "fat": 1, "profit": 1, "culture": 8},
    {"photo": "AgACAgIAAxkBAAMgavjO1bcDIGSiWO0TwMWSzoiGFL8AAn8haxt5CMlLhTvHqmT1AcYBAAMCAAN4AAM9BA", "name": "Ебаный ландрас", "rarity": "Ничего не стоит", "fat": 5, "profit": 2, "culture": 0},
    {"photo": "AgACAgIAAxkBAAMcavjOzX9PqIy-qOL0JHW5UQzKN58AAn0haxt5CMlLbJhjAAGL1RydAQADAgADeAADPQQ", "name": "Свинья с большим достоинством", "rarity": "Ничего не стоит", "fat": 3, "profit": 4, "culture": 2},
    {"photo": "AgACAgIAAxkBAAMYavjOxPr9xrvZLG_6t6n_pAAB6K-BAAJ7IWsbeQjJS-PMPDBncPVmAQADAgADeAADPQQ", "name": "Свиньи эне эне завтракают", "rarity": "Ничего не стоит", "fat": 4, "profit": 2, "culture": 3},
    {"photo": "AgACAgIAAxkBAAMWavjOwc6J5AIBQfGsOzDMiXYFLyoAAnohaxt5CMlLL5k8YAEi0ggBAAMCAAN4AAM9BA", "name": "Свиньи эне эне", "rarity": "Ничего не стоит", "fat": 3, "profit": 3, "culture": 2},
    {"photo": "AgACAgIAAxkBAAMQavjOt9xKQ5mcavzuBqJLEzskVssAAnchaxt5CMlLLoAd6ALi7JcBAAMCAAN4AAM9BA", "name": "Милый поросёнок", "rarity": "Ничего не стоит", "fat": 2, "profit": 4, "culture": 4},
    {"photo": "AgACAgIAAxkBAAMSavjOukPhHblsthFFlaSif2cTTWIAAnghaxt5CMlL1z5YPLf6njABAAMCAAN4AAM9BA", "name": "Свиньи ищут мины в Боснии", "rarity": "Ничего не стоит", "fat": 4, "profit": 1, "culture": 2},
    {"photo": "AgACAgIAAxkBAAMUavjOvuIcttjlcUTIXFIxOGiOvLQAAnkhaxt5CMlLa3RZHgHg0jEBAAMCAAN4AAM9BA", "name": "Пять бутылок водки", "rarity": "Ничего не стоит", "fat": 1, "profit": 1, "culture": 0},
    {"photo": "AgACAgIAAxkBAAMmavjO3yJULY0QcdDq4xM1I31ROXMAAoIhaxt5CMlL1a2rM88anF0BAAMCAAN4AAM9BA", "name": "Украинская степная", "rarity": "Ничего не стоит", "fat": 5, "profit": 3, "culture": 2},
    {"photo": "AgACAgIAAxkBAAMoavjO4_Lgous1QJl-G85_gDmTSkYAAoMhaxt5CMlLzux53J21gbUBAAMCAAN4AAM9BA", "name": "Свиноматка до изнасилования", "rarity": "Ничего не стоит", "fat": 3, "profit": 1, "culture": 1},
    {"photo": "AgACAgIAAxkBAAMqavjO5uSkWe7f73ow8yMajra3uEsAAoQhaxt5CMlLH9Rji0UNjv0BAAMCAAN4AAM9BA", "name": "Бибизян и свин дружат", "rarity": "Ничего не стоит", "fat": 2, "profit": 2, "culture": 5},
]

cards_common = [
    {"photo": "AgACAgIAAxkBAAMsavjO6tOwTsdpIDAeoo4LxQfwPkUAAoUhaxt5CMlLzja90czcWvoBAAMCAAN4AAM9BA", "name": "Бибизян на свине", "rarity": "Обычная", "fat": 15, "profit": 10, "culture": 10},
    {"photo": "AgACAgIAAxkBAAMuavjO7gLbo4HALLTMWGHB-gjYPZYAAoYhaxt5CMlLW8mLJAWP7q4BAAMCAAN4AAM9BA", "name": "Бибизян на кабане", "rarity": "Обычная", "fat": 18, "profit": 8, "culture": 12},
    {"photo": "AgACAgIAAxkBAAM2avjO_BCn14F7QpfJxWZBimMsFWAAAoohaxt5CMlL7-A2OZkEbn4BAAMCAAN4AAM9BA", "name": "Очередь в газовую камеру", "rarity": "Обычная", "fat": 10, "profit": 15, "culture": 5},
    {"photo": "AgACAgIAAxkBAAM4avjO_nRTZjXkksOEX1HooBfOhkEAAoshaxt5CMlLGey1g3RpRXEBAAMCAAN4AAM9BA", "name": "По факту админ и свин", "rarity": "Обычная", "fat": 12, "profit": 12, "culture": 15},
    {"photo": "AgACAgIAAxkBAAM6avjPAYmaozjfzt-8sUdy6lYb4zkAAowhaxt5CMlLJkUfcqbdigMBAAMCAAN4AAM9BA", "name": "Ландрасы ебутся", "rarity": "Обычная", "fat": 20, "profit": 5, "culture": 0},
    {"photo": "AgACAgIAAxkBAAM8avjPBKzjxhhEvCTbXIvxn_AQQNIAAo0haxt5CMlLacqXYQgfZm0BAAMCAAN4AAM9BA", "name": "Жирные белые свиньи ебутся", "rarity": "Обычная", "fat": 25, "profit": 5, "culture": 0},
    {"photo": "AgACAgIAAxkBAAM0avjO-GISAx5C-r-h1k1NDI4lDzMAAokhaxt5CMlLgl-9mcKiFEgBAAMCAAN4AAM9BA", "name": "свиноматка 200", "rarity": "Обычная", "fat": 15, "profit": 15, "culture": 10},
    {"photo": "AgACAgIAAxkBAAMyavjO9Xs8Xxxyl7EtFZf2NI_GtB4AAoghaxt5CMlL9mH81-nxqJgBAAMCAAN4AAM9BA", "name": "БИБИЗЯН АДМИН ЖЕЛАЕТ ВСЕМ МИРА", "rarity": "Обычная", "fat": 5, "profit": 20, "culture": 20},
    {"photo": "AgACAgIAAxkBAAPRavmcj79fZopz5rKfI0e6aYmSXusAAr0iaxt5CNFLO07zZV_H8DIBAAMCAAN3AAM9BA", "name": "Но никто не пришёл", "rarity": "Обычная", "fat": 5, "profit": 10, "culture": 20},
]

cards_unusual = [
    {"photo": "AgACAgIAAxkBAAMwavjO8ZrRJtSh__E0TLo3GeeOkCoAAochaxt5CMlLac4ztm0nTTwBAAMCAAN4AAM9BA", "name": "Админ и свин", "rarity": "Необычная", "fat": 40, "profit": 15, "culture": 15},
    {"photo": "AgACAgIAAxkBAAN8avjTRKLFqAQGCVDCDWXTi2uiwNsAArYhaxt5CMlLJP4q6H6W64gBAAMCAAN5AAM9BA", "name": "Аватарка бота", "rarity": "Необычная", "fat": 20, "profit": 20, "culture": 35},
    {"photo": "AgACAgIAAxkBAANAavjQWANzQWXDPycZgvrMChNpzFoAApQhaxt5CMlL26TUxpctcN0BAAMCAAN5AAM9BA", "name": "Украïньский стэповiй свiн", "rarity": "Необычная", "fat": 35, "profit": 35, "culture": 15},
    {"photo": "AgACAgIAAxkBAAM-avjPCIbd9072br_A9YRxU41ALUgAAo4haxt5CMlLt2NsveiWQmMBAAMCAAN3AAM9BA", "name": "Дырочка свиная", "rarity": "Необычная", "fat": 25, "profit": 25, "culture": 10},
    {"photo": "AgACAgIAAxkBAANWavjRJSeiEw0BBw07PmYWHY9ciMEAAp8haxt5CMlLRVzHBDKNZTEBAAMCAAN5AAM9BA", "name": "Я моггаю?", "rarity": "Необычная", "fat": 15, "profit": 40, "culture": 20},
    {"photo": "AgACAgIAAxkBAANUavjQ-Y4HaEd3V9x5srr0puvkbegAAp4haxt5CMlLiRmuUh7lhkgBAAMCAAN4AAM9BA", "name": "Тайный гость", "rarity": "Необычная", "fat": 20, "profit": 45, "culture": 30},
    {"photo": "AgACAgIAAxkBAANeavjR3hSEE4XBBBU7hZ8STZ15tUkAAqQhaxt5CMlLrq_qckKywJ4BAAMCAAN4AAM9BA", "name": "Админ тупой и ничего придумать сам не может?", "rarity": "Необычная", "fat": 10, "profit": 20, "culture": 50},
    {"photo": "AgACAgIAAxkBAANwavjSka2AyTyb_hcm99jTjm7dWs4AAq0haxt5CMlL5LC4aVmtXQUBAAMCAAN5AAM9BA", "name": "Ваня и ...", "rarity": "Необычная", "fat": 30, "profit": 30, "culture": 20},
    {"photo": "AgACAgIAAxkBAANyavjSptwyby7SbaQQNKOb96OHBacAAq8haxt5CMlLVAdN6T45u_oBAAMCAAN5AAM9BA", "name": "... и Балтика", "rarity": "Необычная", "fat": 20, "profit": 15, "culture": 15},
    {"photo": "AgACAgIAAxkBAANqavjSSP9EFH6FV2iW9sSh0DglXpAAAqohaxt5CMlLC4t_0L3tSgwBAAMCAAN5AAM9BA", "name": "Ваня фюрер", "rarity": "Необычная", "fat": 25, "profit": 35, "culture": 10},
    {"photo": "AgACAgIAAxkBAANsavjSYAj84t5y6XhQj9ms51G8X7MAAqshaxt5CMlLaycxPNzJAqEBAAMCAAN5AAM9BA", "name": "Странность", "rarity": "Необычная", "fat": 15, "profit": 15, "culture": 45},
    {"photo": "AgACAgIAAxkBAANuavjSeSov6NSfLBOoyg14LneVeAEAAqwhaxt5CMlLJ7z1Ul_K6WEBAAMCAAN5AAM9BA", "name": "Сажает лёгкие", "rarity": "Необычная", "fat": 15, "profit": 25, "culture": 25},
    {"photo": "AgACAgIAAxkBAAPVavmeMjMEqUQXq9YC0VNZX6gNFCgAAskiaxt5CNFLm0fmn-5igj8BAAMCAAN5AAM9BA", "name": "Рейх свин", "rarity": "Необычная", "fat": 35, "profit": 30, "culture": 10},
    {"photo": "AgACAgIAAxkBAAPNavmbjAp9cp4VwLawCeuEC1BO6gYAArAiaxt5CNFLXXXbsE65ej4BAAMCAAN3AAM9BA", "name": "Свин следит", "rarity": "Необычная", "fat": 20, "profit": 35, "culture": 25},
]

cards_heroic = [
    {"photo": "AgACAgIAAxkBAAMiavjO2PbsSVO0XBv-dERzqWMfzNgAAoAhaxt5CMlLd3pByCqHzFsBAAMCAAN4AAM9BA", "name": "Некая тётя Н.", "rarity": "Героизм", "fat": 55, "profit": 25, "culture": 10},
    {"photo": "AgACAgIAAxkBAANEavjQd2mOrjtdqggsDfXFAoXWG1AAApYhaxt5CMlLsjMXEe38Vy0BAAMCAAN5AAM9BA", "name": "Воцап", "rarity": "Героизм", "fat": 20, "profit": 55, "culture": 30},
    {"photo": "AgACAgIAAxkBAANCavjQapK-gtzjlkXo4o3pi7R0QRYAApUhaxt5CMlLGtmjHnAEYyABAAMCAAN5AAM9BA", "name": "Свин на хате", "rarity": "Героизм", "fat": 50, "profit": 50, "culture": 25},
    {"photo": "AgACAgIAAxkBAAN2avjS1PtCC-cBlAbHflmyoqM8p3MAArIhaxt5CMlLqOTN9fM_C-kBAAMCAAN5AAM9BA", "name": "С квасом", "rarity": "Героизм", "fat": 40, "profit": 30, "culture": 40},
    {"photo": "AgACAgIAAxkBAAN0avjSwk2Z6cQa1wABQvnI9uw9i3hrAAKwIWsbeQjJS6jjjuXCWcsiAQADAgADeQADPQQ", "name": "Цундере танец", "rarity": "Героизм", "fat": 15, "profit": 20, "culture": 60},
    {"photo": "AgACAgIAAxkBAAN6avjS7-tEr19OT74FG0yr91wfNIMAArUhaxt5CMlLYyXEaPZUb7gBAAMCAAN3AAM9BA", "name": "Ищет парня", "rarity": "Героизм", "fat": 20, "profit": 50, "culture": 50},
    {"photo": "AgACAgIAAxkBAANiavjR_67xI1kdnQrlu3P-23QS0MEAAqYhaxt5CMlL8QIwNlIMgb0BAAMCAAN3AAM9BA", "name": "Бомжа ебучая", "rarity": "Героизм", "fat": 35, "profit": 15, "culture": 20},
    {"photo": "AgACAgIAAxkBAANkavjSD8dfQqskbsXE-Ue35oTX9e8AAqchaxt5CMlLsqzt2nZPLtgBAAMCAAN5AAM9BA", "name": "I love gay porn", "rarity": "Героизм", "fat": 10, "profit": 25, "culture": 60},
    {"photo": "AgACAgIAAxkBAANmavjSG8F6_40v7yvI3bzfZbUoOg4AAqghaxt5CMlL1SvqZClJ1FoBAAMCAAN3AAM9BA", "name": "Свин не считает себя свином", "rarity": "Героизм", "fat": 20, "profit": 20, "culture": 55},
    {"photo": "AgACAgIAAxkBAAPPavmcf3TUYa2Y4PMHVf5YpupdAAH3AAK7ImsbeQjRS9B_ktnpeS2BAQADAgADdwADPQQ", "name": "Идите работайте (до избиения)", "rarity": "Героизм", "fat": 30, "profit": 55, "culture": 20},
]

cards_legendary = [
    {"photo": "AgACAgIAAxkBAAN4avjS4GsX7ZLriQipGhDP5NZyPUkAArQhaxt5CMlLbxr-EmkbsDwBAAMCAAN3AAM9BA", "name": "За что мой дед воровал?", "rarity": "Легендарная", "fat": 20, "profit": 20, "culture": 70},
    {"photo": "AgACAgIAAxkBAANoavjSI527BtiF3QG1KNGpc1wfSNIAAqkhaxt5CMlLVKf3Wgf1afYBAAMCAAN3AAM9BA", "name": "Син шьюхи", "rarity": "Легендарная", "fat": 30, "profit": 30, "culture": 45},
    {"photo": "AgACAgIAAxkBAANaavjRjFoHjZEGSJNFegU4yYqa_kYAAqIhaxt5CMlL2v240F2UUV4BAAMCAAN4AAM9BA", "name": "Lite версия", "rarity": "Легендарная", "fat": 35, "profit": 60, "culture": 25},
    {"photo": "AgACAgIAAxkBAANYavjRX3FrE5_lxBNmgsYc57e8Z_sAAqEhaxt5CMlL1QM1ILs5xcsBAAMCAAN3AAM9BA", "name": "Зельц из свиней", "rarity": "Легендарная", "fat": 70, "profit": 30, "culture": 15},
    {"photo": "AgACAgIAAxkBAANOavjQsniUFXlopBF21aFb2POq8wMAApshaxt5CMlL9u7QysHgMXYBAAMCAAN3AAM9BA", "name": "Нормальный мальчик", "rarity": "Легендарная", "fat": 25, "profit": 25, "culture": 30},
    {"photo": "AgACAgIAAxkBAANQavjQuZUBCn0UKlatj_PQKIsE29AAApwhaxt5CMlLRh-fofqDAQwBAAMCAAN5AAM9BA", "name": "Свинота", "rarity": "Легендарная", "fat": 30, "profit": 50, "culture": 40},
    {"photo": "AgACAgIAAxkBAANSavjQxTGtk0Hjp5hPwmI74Pne_KkAAp0haxt5CMlLG8IXDgkWP0IBAAMCAAN5AAM9BA", "name": "Это кто нахуй?", "rarity": "Легендарная", "fat": 40, "profit": 20, "culture": 65},
    {"photo": "AgACAgIAAxkBAANgavjR772Xpia8MMBSNkF7q2HsYdoAAqUhaxt5CMlL8S2acKanOCgBAAMCAAN5AAM9BA", "name": "Смешно шо пэзда", "rarity": "Легендарная", "fat": 10, "profit": 10, "culture": 68},
    {"photo": "AgACAgIAAxkBAANIavjQmVB0yK-ftQX38qEAAfwPAqubAAKYIWsbeQjJS4WsgmRL9PkwAQADAgADdwADPQQ", "name": "Питушачьи корни", "rarity": "Легендарная", "fat": 15, "profit": 45, "culture": 55},
    {"photo": "AgACAgIAAxkBAANGavjQkWJ-Vcw24peWDmPrwHErlSAAApchaxt5CMlL27i_0ybcBQkBAAMCAAN3AAM9BA", "name": "Свинья небритая+нестриженная (добрый)", "rarity": "Легендарная", "fat": 65, "profit": 25, "culture": 35},
    {"photo": "AgACAgIAAxkBAANKavjQoCkx3rFsEg80Jy3Tzk3zcXIAApkhaxt5CMlL7hb_-f9eFAsBAAMCAAN4AAM9BA", "name": "Добрый Ваня немного свин", "rarity": "Легендарная", "fat": 10, "profit": 35, "culture": 65},
]

cards_impossible = [
    {"photo": "AgACAgIAAxkBAANMavjQpfELBxbh6vrEgjoyF70Xb1oAApohaxt5CMlLj8T3PcKn_AsBAAMCAAN5AAM9BA", "name": "Депутат", "rarity": "Невозможно", "fat": 81, "profit": 82, "culture": 83},
    {"photo": "AgACAgIAAxkBAAPbavmfsQ5XwxxjeipLpUKKTq09OgsAAuAiaxt5CNFLL97hIve2HYoBAAMCAAN4AAM9BA", "name": "Хрюшка на пляже", "rarity": "Невозможно", "fat": 80, "profit": 80, "culture": 82},
    {"photo": "AgACAgIAAxkBAAPZavmfqonJn164bOhWLe0MlLVItP8AAt8iaxt5CNFLs8Ap64cMlpwBAAMCAAN3AAM9BA", "name": "Баронесса пулемётчица", "rarity": "Невозможно", "fat": 88, "profit": 87, "culture": 80},
    {"photo": "AgACAgIAAxkBAAPXavmfpDqph8RJeYwuyEQd_u-7IJcAAt4iaxt5CNFLuHhstpuHYwkBAAMCAAN5AAM9BA", "name": "ЗАГРОЗА БАЛiСТИКИ У УКРАÏНİ", "rarity": "Невозможно", "fat": 82, "profit": 80, "culture": 80},
    {"photo": "AgACAgIAAxkBAAPTavmeMBTFbW8AAdOoUtQVYH-Mh5iTAALIImsbeQjRS_F0gvpSiQH9AQADAgADeQADPQQ", "name": "Терпила и его ёбырь", "rarity": "Невозможно", "fat": 83, "profit": 80, "culture": 86},
]

TIME_CARD = {"photo": "AgACAgIAAxkBAANcavjRnfWN8rpI8i9gXtBf2pm7jowAAqMhaxt5CMlLUKlcBbpadbgBAAMCAAN4AAM9BA", "name": "Самая редкая карточка в мире (посхалко)", "rarity": "Секретная", "fat": 100, "profit": 100, "culture": 100}

# ==================== БОТ И БАЗА ====================
bot = telebot.TeleBot(TOKEN)
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
        rarity_choice = random.choices(
            ["nothing", "common", "unusual", "heroic", "legendary", "impossible"], 
            weights=[50, 29, 10, 5, 4, 2], 
            k=1
        )[0]

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
            if stat == 'fat':
                fat_b += points
                upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Жирность повышена на +{points}."
            elif stat == 'profit':
                profit_b += points
                upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Выгодность повышена на +{points}."
            else:
                culture_b += points
                upgrade_msg = f"\n\n📈 <b>Дубликат!</b> Культурность повышена на +{points}."
                
            supabase.table('inventory').update({
                'fat_bonus': fat_b, 'profit_bonus': profit_b, 'culture_bonus': culture_b
            }).eq('id', existing['id']).execute()
        else:
            upgrade_msg = "\n\n🚫 <b>Дубликат!</b> Но твоя карточка уже полностью прокачана."
    else:
        supabase.table('inventory').insert({
            'user_id': uid, 'card_name': card['name'], 'card_rarity': card['rarity'],
            'card_photo': card['photo'], 'fat_bonus': 0, 'profit_bonus': 0, 'culture_bonus': 0
        }).execute()
        
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
    text = (
        "🐷 <b>Прiвiт! Цэ я, свинота, карточный бот для твоего чата</b>\n\n"
        "Напиши 'свинья', чтобы подрочить меня\n\n"
        "P.s. Для связи с разработчиком отправь команду /help и иди нахуй"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ==================== СИСТЕМА PVP БОЕВ (ЭТАП 1) ====================
ALLOWED_CHAT_ID = -1002541291432

@bot.message_handler(commands=['battle'])
def cmd_battle(message):
    # Проверка, что команда вызвана именно в нужном чате
    if message.chat.id != ALLOWED_CHAT_ID:
        bot.reply_to(message, "Свинобойня проводится только в специально отведенной бане! Иди нахуй, пидрила")
        return

    # Проверка, что игрок отметил соперника
    if len(message.entities) < 2 or message.entities[1].type != 'mention':
        bot.reply_to(message, "Чтобы вызвать на свинобой, напиши: `/battle @username`", parse_mode='Markdown')
        return

    # Получаем username соперника (без символа @)
    enemy_username = message.entities[1].extract_from(message.text)[1:]
    
    # Получаем информацию о вызывающем
    challenger_id = message.from_user.id
    challenger_name = message.from_user.first_name

    # Проверяем, есть ли у вызывающего карточки
    inv_resp = supabase.table('inventory').select('card_name').eq('user_id', challenger_id).execute()
    if not inv_resp.data:
        bot.reply_to(message, f"{challenger_name}, Хахаха, ты ебаная нищета! Напиши «свин», чтобы получить пизды, или иди нахуй.")
        return

    # Отправляем сообщение с кнопками
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="✅ Газ ехала", callback_data=f"accept_battle_{challenger_id}_{enemy_username}"),
        InlineKeyboardButton(text="❌ Я питух", callback_data=f"decline_battle_{challenger_id}")
    )
    
    text = f"⚔️ <b>{challenger_name}</b> вызывает на смертельный бой <b>@{enemy_username}</b>!\n\nНа кону стоит твоё очко. Согласен?"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_battle_'))
def callback_accept_battle(call):
    # Парсим данные: accept_battle_ID_username
    parts = call.data.split('_')
    challenger_id = int(parts[2])
    enemy_username = parts[3]
    
    # Проверяем, что на кнопку нажал именно тот, кого вызвали
    if call.from_user.username.lower() != enemy_username.lower():
        bot.answer_callback_query(call.id, "Убери свои ебаные сардельки!", show_alert=True)
        return

    # Проверяем, есть ли у того, кого вызвали, карточки
    inv_resp = supabase.table('inventory').select('card_name').eq('user_id', call.from_user.id).execute()
    if not inv_resp.data:
        bot.answer_callback_query(call.id, "Нищета без карточек, пошла нахуй отсюда!", show_alert=True)
        return

    # Меняем сообщение
    bot.edit_message_text(
        f"⚔️ <b>Чмо не зассало, газ!</b>\n\nПидорас {challenger_id} и Пидорас {call.from_user.id} готовы к свинобойне.\n\nСейчас лудка раздаст вам свиней.",
        call.message.chat.id, call.message.message_id, parse_mode='HTML'
    )
    # Здесь в будущем (Этап 2) мы вызовем функцию старта боя

@bot.callback_query_handler(func=lambda call: call.data.startswith('decline_battle_'))
def callback_decline_battle(call):
    bot.edit_message_text(
        "❌ ПИТУШАРА. Этот хуеглот зассал играть, позор ему!.",
        call.message.chat.id, call.message.message_id, parse_mode='HTML'
    )

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uid = message.from_user.id
    first_name = message.from_user.first_name
    
    inv_resp = supabase.table('inventory').select('card_rarity').eq('user_id', uid).execute()
    if not inv_resp.data:
        bot.reply_to(message, f"Ты ебаная нищета, {first_name}. Напиши «свин» и иди нахуй!")
        return
        
    rarities = set(item['card_rarity'] for item in inv_resp.data)
    total_cards = len(inv_resp.data)
    
    text = f"📊 <b>Инвентарь {first_name}</b>\nСобрано карточек: {total_cards}\n\nВыбери свиноредкость:"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for r in rarities:
        if r == "Ничего не стоит": icon = "🗑"
        elif r == "Обычная": icon = "⚪"
        elif r == "Необычная": icon = "🔵"
        elif r == "Героизм": icon = "🟣"
        elif r == "Легендарная": icon = "🟡"
        elif r == "Невозможно": icon = "⚫️"
        else: icon = "🌟"
        markup.add(InlineKeyboardButton(text=f"{icon} {r}", callback_data=f"rarity_{r}"))
        
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('rarity_'))
def callback_rarity(call):
    uid = call.from_user.id
    rarity = call.data.split('_', 1)[1] 
    
    inv_resp = supabase.table('inventory').select('card_name').eq('user_id', uid).eq('card_rarity', rarity).execute()
    if not inv_resp.data:
        bot.answer_callback_query(call.id, "Ты нищета без карточек этой свиноредкости.")
        return
        
    markup = InlineKeyboardMarkup(row_width=2)
    for item in inv_resp.data:
        markup.add(InlineKeyboardButton(text=item['card_name'], callback_data=f"card_{item['card_name']}"))
    markup.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_rarities"))
    
    bot.edit_message_text(f"Карточки редкости <b>{rarity}</b>:\nВыбери карточку:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('card_'))
def callback_card(call):
    uid = call.from_user.id
    card_name = call.data.replace('card_', '')
    
    inv_resp = supabase.table('inventory').select('*').eq('user_id', uid).eq('card_name', card_name).execute()
    if not inv_resp.data:
        bot.answer_callback_query(call.id, "Ошибка.")
        return
        
    data = inv_resp.data[0]
    
    all_cards = cards_nothing + cards_common + cards_unusual + cards_heroic + cards_legendary + cards_impossible + [TIME_CARD]
    base_card = next((c for c in all_cards if c['name'] == card_name), None)
    
    caption = (
        f"🎴 <b>{data['card_name']}</b>\n"
        f"Редкость: {data['card_rarity']}\n\n"
        f"🐷 Жирность: {base_card['fat']} (+{data['fat_bonus']})\n"
        f"💰 Выгодность: {base_card['profit']} (+{data['profit_bonus']})\n"
        f"🎩 Культурность: {base_card['culture']} (+{data['culture_bonus']})"
    )
    
    bot.send_photo(call.message.chat.id, data['card_photo'], caption=caption, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_rarities')
def callback_back_list(call):
    uid = call.from_user.id
    first_name = call.from_user.first_name
    
    inv_resp = supabase.table('inventory').select('card_rarity').eq('user_id', uid).execute()
    rarities = set(item['card_rarity'] for item in inv_resp.data)
    total_cards = len(inv_resp.data)
    
    text = f"📊 <b>Инвентарь {first_name}</b>\nСобрано карточек: {total_cards}\n\nВыбери свиноредкость:"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for r in rarities:
        if r == "Ничего не стоит": icon = "🗑"
        elif r == "Обычная": icon = "⚪"
        elif r == "Необычная": icon = "🔵"
        elif r == "Героизм": icon = "🟣"
        elif r == "Легендарная": icon = "🟡"
        elif r == "Невозможно": icon = "⚫️"
        else: icon = "🌟"
        markup.add(InlineKeyboardButton(text=f"{icon} {r}", callback_data=f"rarity_{r}"))
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.lower().strip() not in CODEWORDS:
        return
    uid = message.from_user.id
    card, reason, extra_msg = get_card_and_update(uid)
    
    if card is None:
        if random.choice([True, False]):
            msg_text = f"⏳ Еще рано, хуйня. Жди: <b>{format_remaining(extra_msg)}</b>."
        else:
            msg_text = f"Ты не голоден, тебе просто скучно. Жди: <b>{format_remaining(extra_msg)}</b>."
        bot.reply_to(message, msg_text, parse_mode='HTML')
        return
        
    rarity = card['rarity']
    if rarity == "Ничего не стоит": icon = "🗑"
    elif rarity == "Обычная": icon = "⚪"
    elif rarity == "Необычная": icon = "🔵"
    elif rarity == "Героизм": icon = "🟣"
    elif rarity == "Легендарная": icon = "🟡"
    elif rarity == "Невозможно": icon = "⚫️"
    else: icon = "🌟"

    caption = (
        f"{icon} <b>{card['name']}</b>\n"
        f"Редкость: {card['rarity']}\n\n"
        f"🐷 Жирность: {card['fat']}\n"
        f"💰 Выгодность: {card['profit']}\n"
        f"🎩 Культурность: {card['culture']}"
        f"{extra_msg}"
    )
    
    if reason == "time":
        caption = "🌙 <b>Секретная карточка по времени!</b>\n\n" + caption
    
    bot.send_photo(message.chat.id, card["photo"], caption=caption, parse_mode='HTML')

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🐷 Svin Cards запущен...")
    bot.infinity_polling()
