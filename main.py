"""
main.py

Версия 1.2.01

- Единая база карточек в data/cards.json.
- Выбор языка (/start, /lang) и города.
- Кнопка "Go!" с анимацией колеса.
- 80% факт, 20% квиз (если есть квиз).
- Фильтрация карточек по языку (ru/en/cn) и городу (moscow/spb/all).
- Inline-кнопки для викторин.
- Команда "Return / Вернуться" для смены настроек.
- Отключён предпросмотр ссылок Google Maps (disable_web_page_preview=True).
"""

import logging
import random
import json
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
import os

# Чтение токена из переменной окружения (на Railway установишь API_TOKEN)
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("Не задан API_TOKEN. Установите его в переменной окружения.")

logging.basicConfig(level=logging.INFO)
logging.info("=== BOT STARTED: 'WanderWheel' VERSION 1.2.01 (Single cards.json) ===")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---------------------------
# 1. Настройки: язык, город
# ---------------------------
USER_LANGS = {}
LANG_OPTIONS = ["ru", "en", "cn"]
CITY_OPTIONS = {
    "ru": ["Москва", "Санкт-Петербург", "Все"],
    "en": ["Moscow", "Saint Petersburg", "All"],
    "cn": ["莫斯科", "圣彼得堡", "全部"]
}
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
# 2. Функции загрузки карточек
# ---------------------------
def load_cards() -> list:
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
# 3. Команды и логика
# ---------------------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    USER_LANGS[user_id] = {"language": "ru", "city": "all"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Start / Старт")
    await message.reply("Добро пожаловать в WanderWheel!\nНажмите 'Start / Старт' для выбора языка.", reply_markup=kb)

@dp.message_handler(commands=['lang'])
async def cmd_change_lang(message: types.Message):
    await change_language(message)

@dp.message_handler(lambda msg: msg.text == "Start / Старт")
async def choose_language(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lang in LANG_OPTIONS:
        kb.add(lang.upper())
    await message.reply("Выберите язык / Select language / 选择语言:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text and msg.text.lower() in LANG_OPTIONS)
async def language_selection(message: types.Message):
    user_id = message.from_user.id
    chosen_lang = message.text.lower()
    USER_LANGS[user_id]["language"] = chosen_lang
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[chosen_lang]:
        kb.add(city_name)
    await message.reply("Выберите город:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text and msg.text.lower() in CITY_MAP.keys())
async def city_selection(message: types.Message):
    user_id = message.from_user.id
    city_raw = message.text.lower()
    city_key = CITY_MAP.get(city_raw, "all")
    USER_LANGS[user_id]["city"] = city_key
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    await message.reply(f"Вы выбрали город: {message.text}. Нажмите 'Go!' для продолжения.", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text == "Go!")
async def spin_wheel(message: types.Message):
    user_id = message.from_user.id
    if user_id not in USER_LANGS:
        await cmd_start(message)
        return
    await message.answer("🎡 Крутится колесо фортуны...")
    await asyncio.sleep(1.5)
    roll = random.randint(1, 100)
    logging.info(f"User {user_id} pressed Go! -> Random roll = {roll}")
    lang = USER_LANGS[user_id]["language"]
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
    await message.answer("Нажмите Go! или Return / Вернуться", reply_markup=kb)

async def send_quiz_card(message: types.Message, card: dict):
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
        answer_text = "Верно!"
    else:
        answer_text = f"Неверно. Правильный ответ: {correct_idx+1}"
    await callback_query.message.answer(answer_text)
    await callback_query.answer()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    await callback_query.message.answer("Нажмите Go! или Return / Вернуться", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text == "Return / Вернуться")
async def return_handler(message: types.Message):
    user_id = message.from_user.id
    curr_lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    if curr_lang == "ru":
        text_ = "Что хотите изменить: язык или город?"
        opt_lang = "Изменить язык"
        opt_city = "Изменить город"
    elif curr_lang == "en":
        text_ = "What do you want to change: language or city?"
        opt_lang = "Change language"
        opt_city = "Change city"
    else:
        text_ = "您想更改什么：语言还是城市？"
        opt_lang = "更改语言"
        opt_city = "更改城市"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(opt_lang, opt_city)
    await message.answer(text_, reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in ["Изменить язык", "Change language", "更改语言"])
async def change_language(message: types.Message):
    user_id = message.from_user.id
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lang in LANG_OPTIONS:
        kb.add(lang.upper())
    curr_lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    if curr_lang == "ru":
        txt = "Выберите язык:"
    elif curr_lang == "en":
        txt = "Select language:"
    else:
        txt = "选择语言:"
    await message.answer(txt, reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in ["Изменить город", "Change city", "更改城市"])
async def change_city(message: types.Message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, {}).get("language", "ru")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[lang]:
        kb.add(city_name)
    if lang == "ru":
        txt = "Выберите город:"
    elif lang == "en":
        txt = "Choose city:"
    else:
        txt = "请选择城市："
    await message.answer(txt, reply_markup=kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
