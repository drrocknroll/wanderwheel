import csv
import json
from pathlib import Path

CSV_FILE = Path(__file__).parent / "data" / "new_cards.csv"
JSON_FILE = Path(__file__).parent / "data" / "cards.json"

def import_cards():
    # Считываем существующие карточки
    if JSON_FILE.exists() and JSON_FILE.stat().st_size > 0:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try:
                existing_cards = json.load(f)
            except json.JSONDecodeError:
                existing_cards = []
    else:
        existing_cards = []
    
    # Собираем карточки в словарь по id
    cards_dict = {card["id"]: card for card in existing_cards if "id" in card}
    
    # Чтение CSV (используя нужный delimiter, например, ;)
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader, None)
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 16:
                print(f"⚠️ Строка {row_num}: недостаточно столбцов. Пропускаем")
                continue
            # Распаковка столбцов в переменные (пример для 16 или 17 столбцов)
            # ... (здесь вставить существующий код импорта)
            # После обработки создаём структуру card_data и сохраняем:
            cards_dict[card_data["id"]] = card_data
    
    # Записываем итоговый список карточек обратно в JSON_FILE
    final_cards = list(cards_dict.values())
    with open(JSON_FILE, "w", encoding="utf-8") as wf:
        json.dump(final_cards, wf, ensure_ascii=False, indent=2)
    print(f"✅ Импортировано карточек: {len(final_cards)}")

if __name__ == "__main__":
    import_cards()
