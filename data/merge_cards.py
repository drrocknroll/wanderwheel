#!/usr/bin/env python3
import json
import sys
from jsonschema import validate, ValidationError

CARDS_MAIN = "cards.json"
CARDS_NEW = "new_cards.json"
SCHEMA_FILE = "card_schema.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("Попытка открыть основной файл:", CARDS_MAIN)
try:
    main_cards = load_json(CARDS_MAIN)
    print(f"Загружено {len(main_cards)} карточек из {CARDS_MAIN}.")
except:
    print(f"Файл {CARDS_MAIN} не найден или повреждён. Начинаем с пустого массива.")
    main_cards = []

print("Попытка открыть файл с новыми карточками:", CARDS_NEW)
try:
    new_cards = load_json(CARDS_NEW)
except:
    print(f"Не удалось прочитать {CARDS_NEW}. Проверьте, что там валидный JSON (массив).")
    sys.exit(1)

if not isinstance(new_cards, list):
    print(f"Ошибка: {CARDS_NEW} должен содержать массив ([{{...}}, {{...}}]).")
    sys.exit(1)

print("Пытаемся открыть схему:", SCHEMA_FILE)
try:
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = json.load(f)
except:
    print(f"Ошибка: не удалось загрузить схему {SCHEMA_FILE}.")
    sys.exit(1)

existing_ids = {card.get("id") for card in main_cards if "id" in card}

for card in new_cards:
    try:
        validate(instance=card, schema=schema)
    except ValidationError as e:
        print(f"\nОшибка валидации для карточки id={card.get('id','???')}:\n{e}")

