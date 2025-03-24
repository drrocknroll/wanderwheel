import csv
import json
from pathlib import Path

# Пути к файлам:
CSV_FILE = "data/cards.csv"   # <-- входной CSV
JSON_FILE = "data/cards.json" # <-- итоговый JSON

def import_cards():
    """
    Читает CSV_FILE, формирует список словарей card[] и
    добавляет/обновляет их в JSON_FILE (cards.json).
    Предполагается, что CSV имеет столбцы (в порядке):
    
    1. id
    2. interactive       ("true"/"false")
    3. language          ("ru","en","cn")
    4. city              ("moscow","spb","all" или пусто)
    5. address
    6. gps_lat
    7. gps_lng
    8. title
    9. text
    10. question
    11. options
    12. correct_index
    13. reality          ("fact","legend","fantasy", etc.)
    14. explanation
    15. routes
    16. persons
    17. tags            (если нужно 17 столбцов)
    """

    # 1) Считываем существующий cards.json (если есть)
    cards_path = Path(JSON_FILE)
    if cards_path.exists():
        with open(cards_path, "r", encoding="utf-8") as f:
            existing_cards = json.load(f)
    else:
        existing_cards = []

    # Превратим existing_cards в dict по id, чтобы удобнее обновлять
    cards_dict = {}
    for c in existing_cards:
        if isinstance(c, dict) and "id" in c:
            cards_dict[c["id"]] = c

    # 2) Читаем CSV
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"Не найден CSV-файл: {CSV_FILE}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # считываем строку заголовков
        for row in reader:
            # Если у вас ровно 16 столбцов без tags, уберите "tags_str" из распаковки
            if len(row) < 16:
                print(f"⚠️ Пропущенные столбцы в строке: {row}")
                continue

            # Предположим, что у вас 17 столбцов (включая tags):
            # id,interactive,language,city,address,gps_lat,gps_lng,
            # title,text,question,options,correct_index,reality,
            # explanation,routes,persons,tags
            # Если tags нет, сократите распаковку на 1 переменную
            # или сделайте проверку len(row) == 16
            if len(row) == 16:
                # Без tags
                ( card_id,
                  interactive_str,
                  language,
                  city,
                  address,
                  gps_lat_str,
                  gps_lng_str,
                  title,
                  text,
                  question,
                  options_str,
                  correct_index_str,
                  reality_str,
                  explanation,
                  routes_str,
                  persons_str
                ) = row
                tags_str = ""  # пустая строка
            else:
                ( card_id,
                  interactive_str,
                  language,
                  city,
                  address,
                  gps_lat_str,
                  gps_lng_str,
                  title,
                  text,
                  question,
                  options_str,
                  correct_index_str,
                  reality_str,
                  explanation,
                  routes_str,
                  persons_str,
                  tags_str
                ) = row

            # Обрабатываем поля
            interactive = (interactive_str.strip().lower() == "true")
            # Преобразуем language/city к нижнему регистру
            lang_val = language.strip().lower()
            city_val = city.strip().lower()

            # Преобразуем GPS
            gps_lat = float(gps_lat_str) if gps_lat_str.strip() else None
            gps_lng = float(gps_lng_str) if gps_lng_str.strip() else None

            # Преобразуем options
            if options_str.strip():
                options_list = [o.strip() for o in options_str.split(";")]
            else:
                options_list = []

            correct_idx = None
            if correct_index_str.strip():
                correct_idx = int(correct_index_str.strip())

            # reality -> icon
            # e.g. "fact" -> 📖, "legend" -> 🧙🏻‍♂️, иначе любая ваша логика
            reality = reality_str.strip().lower()
            if reality == "legend":
                icon_val = "🧙🏻‍♂️"
            else:
                # Для прочих (fact, fantasy, etc.) используем 📖
                icon_val = "📖"

            # routes, persons, tags
            routes_list = []
            if routes_str.strip():
                routes_list = [r.strip() for r in routes_str.split(";")]

            persons_list = []
            if persons_str.strip():
                persons_list = [p.strip() for p in persons_str.split(";")]

            tags_list = []
            if tags_str.strip():
                tags_list = [t.strip() for t in tags_str.split(";")]

            # Создаём структуру карточки
            card_data = {
                "id": card_id.strip(),
                "interactive": interactive,
                "language": lang_val,
                "city": city_val,
                "icon": icon_val,
                "title": title.strip(),
                "text": text.strip(),
                "question": question.strip() if interactive else "",
                "options": options_list if interactive else [],
                "correct_index": correct_idx if interactive else None,
                "reality": reality,
                "explanation": explanation.strip() if interactive else "",
                "routes": routes_list,
                "persons": persons_list,
                "tags": tags_list,
                "location": {}
            }

            # Формируем location
            loc_dict = {}
            if address.strip():
                loc_dict["address"] = address.strip()
            if gps_lat is not None and gps_lng is not None:
                loc_dict["gps"] = {"lat": gps_lat, "lng": gps_lng}

            if loc_dict:
                card_data["location"] = loc_dict

            # Обновляем / создаём в cards_dict
            cards_dict[card_data["id"]] = card_data

    # 3) Превращаем cards_dict обратно в список
    final_cards = list(cards_dict.values())

    # 4) Сохраняем в cards.json
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(final_cards, f, indent=2, ensure_ascii=False)

    print(f"✅ Импортировано/обновлено карточек: {len(final_cards)}")

# Запуск
if __name__ == "__main__":
    import_cards()
