"""
main.py

Версия 1.3.0

- Единая база карточек в data/cards.json.
- Выбор языка (/start, /lang) и города.
- Кнопка "Go!" с анимацией "Колесо крутится...", вывод которой ограничен (не чаще 1 раза из 5).
- 80% факт, 20% квиз (если есть квиз).
- Фильтрация карточек по языку (ru/en/cn) и городу (moscow/spb/all).
- Inline-кнопки для викторин.
- Локализация всех стандартных сообщений через localization.py.
- Пользовательские настройки хранятся в памяти.
"""

import logging
import random
import json
import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from localization import translations  # Импорт локализации

logging.basicConfig(level=logging.INFO)
logging.info("=== BOT STARTED: 'WanderWheel' VERSION 1.3.0 (Single cards.json) ===")

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN не задан. Установите его в переменной окружения.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---------------------------
# Глобальные переменные для настроек пользователя и счетчики сообщений
# ---------------------------
USER_LANGS = {}  # { user_id: {"language": "ru", "city": "moscow"} }
MESSAGE_COUNTERS = {}  # для ограничения повторений стандартных сообщений

# Языковые опции (храним в нижнем регистре, но отображаем в верхнем)
LANG_OPTIONS = ["ru", "en", "cn"]

# Города для каждого языка
CITY_OPTIONS = {
    "ru": ["Москва", "Санкт-Петербург", "Все"],
    "en": ["Moscow", "Saint Petersburg", "All"],
    "cn": ["莫斯科", "圣彼得堡", "全部"]
}

# Сопоставление ввода города (в любом регистре) к ключу "moscow"/"spb"/"all"
CITY_MAP = {
    "москва": "moscow",
    "moscow": "moscow",
    "санкт-петербург": "spb",
    "saint petersburg": "spb",
    "spb": "spb",
    "莫斯科": "moscow",
    "圣彼得堡": "spb",
    "все": "all",
    "all": "all",
    "全部": "all"
}

# ---------------------------
# Функция контроля частоты повторения стандартных сообщений
# ---------------------------
def should_send_message(user_id, msg_key):
    """
    Возвращает True, если сообщение msg_key для данного пользователя должно быть отправлено
    (не чаще 1 раза из 5 вызовов). Первое появление – отправляется.
    """
    global MESSAGE_COUNTERS
    if user_id not in MESSAGE_COUNTERS:
        MESSAGE_COUNTERS[user_id] = {}
    if msg_key not in MESSAGE_COUNTERS[user_id]:
        MESSAGE_COUNTERS[user_id][msg_key] = 0
    MESSAGE_COUNTERS[user_id][msg_key] += 1
    # Отправляем, если вызов в позиции, когда (count % 5) == 1
    return (MESSAGE_COUNTERS[user_id][msg_key] % 5) == 1

# ---------------------------
# Функции загрузки карточек
# ---------------------------
def load_cards() -> list:
    """
    Считываем ВСЕ карточки из data/cards.json.
    """
    path = Path(__file__).parent / "data" / "cards.json"
    if not path.exists():
        logging.error(f"cards.json not found: {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                logging.error("cards.json должен быть массивом JSON-объектов!")
                return []
    except Exception as e:
        logging.error(f"Ошибка чтения cards.json: {e}")
        return []

def get_filtered_cards(lang: str, city: str) -> (list, list):
    """
    Загружает карточки из cards.json, фильтрует по языку (lang) и городу (city),
    разделяя их на факты и квизы.
    """
    all_cards = load_cards()
    facts = []
    quizzes = []
    lang = lang.lower()
    city = city.lower()
    for c in all_cards:
        card_lang = c.get("language", "").lower()
        if card_lang != lang:
            continue
        card_city = c.get("city", "").lower()
        if not card_city:
            loc = c.get("location", {})
            if isinstance(loc, dict):
                card_city = loc.get("city", "").lower()
            elif isinstance(loc, str):
                card_city = loc.lower()
            else:
                card_city = ""
        if city != "all" and card_city != city:
            continue
        if c.get("interactive", False) is True:
            quizzes.append(c)
        else:
            facts.append(c)
        logging.info(f"CARD_ID={c.get('id')} card_lang={card_lang} card_city={card_city}")
    logging.info(f"Найдено {len(facts)} фактов, {len(quizzes)} квизов для lang={lang} city={city}")
    return (facts, quizzes)

# ---------------------------
# Команды и логика
# ---------------------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    USER_LANGS[user_id] = {"language": "ru", "city": "all"}
    lang = USER_LANGS[user_id]["language"]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Start / Старт")
    welcome_text = translations[lang]["welcome"] + "\n" + translations[lang]["start_prompt"]
    await message.reply(welcome_text, reply_markup=kb)

@dp.message_handler(commands=['lang'])
async def cmd_change_lang(message: types.Message):
    await change_language(message)

@dp.message_handler(lambda msg: msg.text == "Start / Старт")
async def choose_language(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lang_opt in LANG_OPTIONS:
        kb.add(lang_opt.upper())
    # Пока устанавливаем язык по умолчанию "ru"
    await message.reply(translations["ru"]["choose_language"], reply_markup=kb)

@dp.message_handler(lambda msg: msg.text and msg.text.lower() in LANG_OPTIONS)
async def language_selection(message: types.Message):
    user_id = message.from_user.id
    chosen_lang = message.text.lower()
    USER_LANGS[user_id]["language"] = chosen_lang
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[chosen_lang]:
        kb.add(city_name)
    await message.reply(translations[chosen_lang]["choose_city"], reply_markup=kb)

@dp.message_handler(lambda msg: msg.text and msg.text.lower() in CITY_MAP.keys())
async def city_selection(message: types.Message):
    user_id = message.from_user.id
    lang = USER_LANGS[user_id]["language"]
    city_raw = message.text
    city_key = CITY_MAP.get(city_raw.lower(), "all")
    USER_LANGS[user_id]["city"] = city_key
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    city_selected_text = translations[lang]["city_selected"].format(city=city_raw)
    await message.reply(city_selected_text, reply_markup=kb)

@dp.message_handler(lambda msg: msg.text == "Go!")
async def spin_wheel(message: types.Message):
    user_id = message.from_user.id
    if user_id not in USER_LANGS:
        await cmd_start(message)
        return
    lang = USER_LANGS[user_id]["language"]
    if should_send_message(user_id, "wheel_spinning"):
        await message.answer(translations[lang]["wheel_spinning"])
    await asyncio.sleep(1.5)
    roll = random.randint(1, 100)
    logging.info(f"User {user_id} pressed Go! -> Random roll = {roll}")
    city = USER_LANGS[user_id]["city"]
    facts, quizzes = get_filtered_cards(lang, city)
    if not facts and not quizzes:
        await message.reply("⚠️ Нет карточек для выбранного языка/города.")
        return
    if roll <= 20 and quizzes:
        quiz_card = random.choice(quizzes)
        await send_quiz_card(message, quiz_card)
    else:
        if facts:
            fact_card = random.choice(facts)
            await send_fact_card(message, fact_card)
        else:
            quiz_card = random.choice(quizzes)
            await send_quiz_card(message, quiz_card)

async def send_fact_card(message: types.Message, card: dict):
    user_id = message.from_user.id
    lang = USER_LANGS[user_id]["language"]
    text_msg = (
        f"{card.get('icon','')} {card.get('title','')}\n"
        f"{card.get('text','')}"
    )
    loc = card.get("location", {})
    if isinstance(loc, dict):
        addr = loc.get("address", "")
        if addr:
            text_msg += f"\n📍 {addr}"
        gps = loc.get("gps", {})
        if "lat" in gps and "lng" in gps:
            lat, lng = gps["lat"], gps["lng"]
            text_msg += f"\n[{lat},{lng}](https://maps.google.com/?q={lat},{lng})"
    elif isinstance(loc, str):
        text_msg += f"\n📍 {loc}"
    await message.answer(text_msg, parse_mode="Markdown", disable_web_page_preview=True)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    # Отправляем стандартное сообщение не чаще 1 раза из 5
    if should_send_message(user_id, "go_or_return"):
        await message.answer(translations[lang]["go_or_return"], reply_markup=kb)

async def send_quiz_card(message: types.Message, card: dict):
    lang = USER_LANGS[message.from_user.id]["language"]
    question = card.get("question", "Вопрос не задан.")
    options = card.get("options", [])
    correct_idx = card.get("correct_index", 0)
    kb = types.InlineKeyboardMarkup()
    for i, opt in enumerate(options):
        callback_data = f"quiz:{card.get('id','')}:{i}:{correct_idx}"
        kb.add(types.InlineKeyboardButton(f"{i+1}) {opt}", callback_data=callback_data))
    await message.answer(question, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("quiz:"))
async def process_quiz_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = USER_LANGS[user_id]["language"]
    parts = callback_query.data.split(":")
    if len(parts) != 4:
        await callback_query.answer("Ошибка формата квиза", show_alert=True)
        return
    try:
        user_choice = int(parts[2])
        correct_idx = int(parts[3])
    except ValueError:
        await callback_query.answer("Ошибка индексов", show_alert=True)
        return
    if user_choice == correct_idx:
        answer_text = translations[lang]["quiz_correct"]
    else:
        answer_text = translations[lang]["quiz_wrong"].format(correct=correct_idx+1)
    await callback_query.message.answer(answer_text)
    await callback_query.answer()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    await callback_query.message.answer(translations[lang]["go_or_return"], reply_markup=kb)

@dp.message_handler(lambda msg: msg.text == "Return / Вернуться")
async def return_handler(message: types.Message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    text_ = translations[lang]["what_change"]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(translations[lang]["change_language"], translations[lang]["change_city"])
    await message.answer(text_, reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in [translations["ru"]["change_language"], translations["en"]["change_language"], translations["cn"]["change_language"]])
async def change_language(message: types.Message):
    user_id = message.from_user.id
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lang_opt in LANG_OPTIONS:
        kb.add(lang_opt.upper())
    curr_lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    await message.answer(translations[curr_lang]["choose_language"], reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in [translations["ru"]["change_city"], translations["en"]["change_city"], translations["cn"]["change_city"]])
async def change_city(message: types.Message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[lang]:
        kb.add(city_name)
    await message.answer(translations[lang]["choose_city"], reply_markup=kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
