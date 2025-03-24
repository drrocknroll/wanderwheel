"""
main.py

Версия 1.1 (пример, переходим на единый cards.json без regions_config).
Сохраняем кнопки 'Start / Старт', 'Go!', 'Return / Вернуться' и логику выбора языка и города.
Файлы фактов/квизов берём из cards.json (общий).

В cards.json у карточек есть поля:
  "language": "ru"/"en"/"cn"
  "city": "moscow"/"spb" (иногда в location)
  "interactive": true/false
  ...и т.д.

80% -> факт, 20% -> квиз (если есть).
"""

import logging
import random
import json
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
import config  # Файл с API_TOKEN

logging.basicConfig(level=logging.INFO)
logging.info("=== BOT STARTED: "WanderWheel" VERSION 1.2 (Single cards.json) ===")

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# ---------------------------
# 1. Настройки: язык, город
# ---------------------------
USER_LANGS = {}  # { user_id: {"language": "RU"/"EN"/"CN", "city": "moscow"/"spb"/"all"} }

LANG_OPTIONS = ["RU", "EN", "CN"]

CITY_OPTIONS = {
    "RU": ["Москва", "Санкт-Петербург", "Все"],
    "EN": ["Moscow", "Saint Petersburg", "All"],
    "CN": ["莫斯科", "圣彼得堡", "全部"]
}

# Сопоставляем пользовательский ввод с ключами в JSON
# Предполагается, что в cards.json city может храниться "moscow"/"spb"/"all"
CITY_MAP = {
    "Москва": "moscow",
    "Moscow": "moscow",
    "Санкт-Петербург": "spb",
    "Saint Petersburg": "spb",
    "莫斯科": "moscow",
    "圣彼得堡": "spb",
    "Все": "all",
    "All": "all",
    "全部": "all"
}


# ---------------------------
# 2. Функции загрузки карточек
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
                logging.error("cards.json: должен быть массивом JSON-объектов!")
                return []
    except Exception as e:
        logging.error(f"Ошибка чтения cards.json: {e}")
        return []


def get_filtered_cards(lang: str, city: str) -> (list, list):
    """
    Загружает все карточки из cards.json, отфильтровывает по языку (lang) и городу (city),
    и делит их на обычные (facts) и интерактивные (quizzes).
    
    'city' может быть "moscow", "spb" или "all".
    'lang' может быть "RU"/"EN"/"CN".
    
    У некоторых карточек location может быть строкой, у других — словарём:
      - Если словарь, то location.get("city") используется для города.
      - Если строка, сравниваем напрямую.
    """
    all_cards = load_cards()
    facts = []
    quizzes = []

    # Приводим параметры к нижнему регистру для сравнения
    lang = lang.lower()   # "ru", "en", "cn"
    city = city.lower()   # "moscow", "spb", "all"

    for c in all_cards:
        # Язык карточки
        card_lang = c.get("language", "").lower()
        if card_lang != lang:
            # Не совпадает язык — пропускаем
            continue

        # Определяем город из location, который может быть str или dict
        loc = c.get("location", {})
        if isinstance(loc, dict):
            # location – это словарь
            card_city = loc.get("city", "").lower()
        elif isinstance(loc, str):
            # location – это строка
            card_city = loc.lower()
        else:
            card_city = ""

        # Если city == "all", подойдёт любая карточка
        if city != "all" and card_city != city:
            continue

        # Проверяем интерактив
        if c.get("interactive", False) is True:
            quizzes.append(c)
        else:
            facts.append(c)

        logging.info(f"CARD_ID={c.get('id')} card_lang={card_lang} card_city={card_city}")

    logging.info(f"Found {len(facts)} facts, {len(quizzes)} quizzes for language={lang} city={city}")
    return (facts, quizzes)


# ---------------------------
# 3. Команды и логика
# ---------------------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # По умолчанию RU + all
    USER_LANGS[user_id] = {"language": "RU", "city": "all"}

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Start / Старт")
    await message.reply("Добро пожаловать в WanderWheel!\nНажмите 'Start / Старт' для выбора языка.", reply_markup=kb)


@dp.message_handler(lambda msg: msg.text == "Start / Старт")
async def choose_language(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lang in LANG_OPTIONS:
        kb.add(lang)
    await message.reply("Выберите язык / Select language / 选择语言:", reply_markup=kb)


@dp.message_handler(lambda msg: msg.text in LANG_OPTIONS)
async def language_selection(message: types.Message):
    user_id = message.from_user.id
    chosen_lang = message.text  # "RU"/"EN"/"CN"
    USER_LANGS[user_id]["language"] = chosen_lang

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[chosen_lang]:
        kb.add(city_name)
    await message.reply("Выберите город:", reply_markup=kb)


@dp.message_handler(lambda msg: msg.text in sum(CITY_OPTIONS.values(), []))
async def city_selection(message: types.Message):
    user_id = message.from_user.id
    city_raw = message.text  # e.g. "Москва", "All", ...
    city_key = CITY_MAP.get(city_raw, "all")  # "moscow"/"spb"/"all"
    USER_LANGS[user_id]["city"] = city_key

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    await message.reply(f"Вы выбрали город: {city_raw}. Нажмите 'Go!' для продолжения.", reply_markup=kb)


@dp.message_handler(lambda msg: msg.text == "Go!")
async def spin_wheel(message: types.Message):
    """При нажатии Go! 80% -> факт, 20% -> квиз."""
    user_id = message.from_user.id
    if user_id not in USER_LANGS:
        await cmd_start(message)
        return

    roll = random.randint(1, 100)
    logging.info(f"User {user_id} pressed Go! -> Random roll = {roll}")

    # Получаем списки
    lang = USER_LANGS[user_id]["language"]
    city = USER_LANGS[user_id]["city"]
    facts, quizzes = get_filtered_cards(lang, city)

    # Если нет фактов и нет квизов
    if not facts and not quizzes:
        await message.reply("⚠️ Нет карточек для выбранного языка/города.")
        return

    # 20% -> квиз (если есть), иначе факт
    if roll <= 20 and quizzes:
        quiz_card = random.choice(quizzes)
        await send_quiz_card(message, quiz_card)
    else:
        # Если факт есть, берём факт, иначе квиз
        if facts:
            fact_card = random.choice(facts)
            await send_fact_card(message, fact_card)
        else:
            # Фактов нет, но есть квизы
            quiz_card = random.choice(quizzes)
            await send_quiz_card(message, quiz_card)


async def send_fact_card(message: types.Message, card: dict):
    """
    Выводим обычную карточку (fact).
    card["title"], card["text"], ...
    """
    # title, text могут быть строковыми полями
    text_msg = (
        f"{card.get('icon','')} {card.get('title','')}\n"
        f"{card.get('text','')}"
    )

    # Если есть location и оно словарь -> добавим адрес
    loc = card.get("location", {})
    if isinstance(loc, dict):
        addr = loc.get("address", "")
        if addr:
            text_msg += f"\n📍 {addr}"
        # При наличии GPS -> ссылка
        gps = loc.get("gps", {})
        if "lat" in gps and "lng" in gps:
            lat, lng = gps["lat"], gps["lng"]
            maps_link = f"https://maps.google.com/?q={lat},{lng}"
            text_msg += f"\n[Открыть на карте]({maps_link})"
    elif isinstance(loc, str):
        # location – строка, просто выводим
        text_msg += f"\n📍 {loc}"

    await message.answer(text_msg, parse_mode="Markdown")

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Go!", "Return / Вернуться")
    await message.answer("Нажмите Go! или Вернуться", reply_markup=kb)


async def send_quiz_card(message: types.Message, card: dict):
    """
    Выводим карточку-квиз. Предполагаем, что в card есть поля:
      "question", "options" (array), "correct_index" (число)
    """
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
    # Формат quiz:<card_id>:<user_choice>:<correct_idx>
    parts = callback_query.data.split(":")
    if len(parts) != 4:
        await callback_query.answer("Ошибка формата квиза", show_alert=True)
        return

    quiz_id = parts[1]
    user_choice_str = parts[2]
    correct_idx_str = parts[3]

    try:
        user_choice = int(user_choice_str)
        correct_idx = int(correct_idx_str)
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
    await callback_query.message.answer("Нажмите Go! или Вернуться", reply_markup=kb)


@dp.message_handler(lambda msg: msg.text == "Return / Вернуться")
async def return_handler(message: types.Message):
    """
    Пользователь нажал 'Return / Вернуться' — спросим, что менять: язык или город.
    """
    user_id = message.from_user.id
    curr_lang = USER_LANGS.get(user_id, {}).get("language", "RU")

    if curr_lang == "RU":
        text_ = "Что хотите изменить: язык или город?"
        opt_lang = "Изменить язык"
        opt_city = "Изменить город"
    elif curr_lang == "EN":
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
        kb.add(lang)

    if USER_LANGS[user_id]["language"] == "RU":
        txt = "Выберите язык:"
    elif USER_LANGS[user_id]["language"] == "EN":
        txt = "Select language:"
    else:
        txt = "选择语言:"

    await message.answer(txt, reply_markup=kb)


@dp.message_handler(lambda msg: msg.text in ["Изменить город", "Change city", "更改城市"])
async def change_city(message: types.Message):
    user_id = message.from_user.id
    lang = USER_LANGS[user_id]["language"]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city_name in CITY_OPTIONS[lang]:
        kb.add(city_name)

    if lang == "RU":
        txt = "Выберите город:"
    elif lang == "EN":
        txt = "Choose city:"
    else:
        txt = "请选择城市："

    await message.answer(txt, reply_markup=kb)


# -----------------------
# Запуск бота
# -----------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
