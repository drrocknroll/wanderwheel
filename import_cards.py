import csv
import json
from pathlib import Path

# Пусть у нас файлы:
CSV_FILE = "data/new_cards.csv"
JSON_FILE = "data/cards.json"

def import_cards():
    """
    Читает CSV_FILE (разделитель ';'), создает/обновляет JSON_FILE (cards.json).
    """
    # 1) Считываем (если есть) существующий cards.json
    cards_path = Path(JSON_FILE)
    if cards_path.exists() and cards_path.stat().st_size > 0:
        try:
            with open(cards_path, "r", encoding="utf-8") as f:
                existing_cards = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Файл cards.json повреждён или пуст. Будет перезаписан заново.")
            existing_cards = []
    else:
        existing_cards = []

    # Сохраним в dict по id, чтобы обновлять
    cards_dict = {}
    for c in existing_cards:
        if isinstance(c, dict) and "id" in c:
            cards_dict[c["id"]] = c

    # 2) Открываем CSV. delimiter=';'
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"❌ Не найден CSV-файл: {CSV_FILE}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        header = next(reader, None)  # первая строка
        if header is None:
            print("❌ CSV-файл пуст или некорректен (нет заголовков).")
            return

        # Ожидаем 16 или 17 столбцов
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 16:
                print(f"⚠️ Строка {row_num}: недостаточно столбцов. Пропускаем: {row}")
                continue

            # Если tags нет, len(row) == 16
            if len(row) == 16:
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
                tags_str = ""
            else:
                # len(row) == 17, значит есть tags
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

            interactive = (interactive_str.strip().lower() == "true")
            lang_val = language.strip().lower()
            city_val = city.strip().lower()

            # Преобразуем GPS
            gps_lat = None
            gps_lng = None
            if gps_lat_str.strip():
                try:
                    gps_lat = float(gps_lat_str.strip())
                except ValueError:
                    pass
            if gps_lng_str.strip():
                try:
                    gps_lng = float(gps_lng_str.strip())
                except ValueError:
                    pass

            # options (для квиза)
            options_list = []
            if options_str.strip():
                # внутри одной ячейки CSV, ответы разделены ;
                # но csv.reader уже разделил колонки,
                # так что здесь тоже ';'
                options_list = [o.strip() for o in options_str.split(';')]

            correct_idx = None
            if correct_index_str.strip():
                try:
                    correct_idx = int(correct_index_str.strip())
                except ValueError:
                    pass

            # reality -> icon
            reality_val = reality_str.strip().lower()
            if reality_val == "legend":
                icon_val = "🧙🏻‍♂️"
            else:
                icon_val = "📖"

            # routes
            routes_list = []
            if routes_str.strip():
                routes_list = [r.strip() for r in routes_str.split(';')]

            # persons
            persons_list = []
            if persons_str.strip():
                persons_list = [p.strip() for p in persons_str.split(';')]

            # tags
            tags_list = []
            if tags_str.strip():
                tags_list = [t.strip() for t in tags_str.split(';')]

            # Собираем структуру
            card_data = {
                "id": card_id.strip(),
                "interactive": interactive,
                "language": lang_val,
                "city": city_val,
                "icon": icon_val,
                "title": title.strip().strip('"'),
                "text": text.strip().strip('"'),
                "question": question.strip() if interactive else "",
                "options": options_list if interactive else [],
                "correct_index": correct_idx if interactive else None,
                "reality": reality_val,
                "explanation": explanation.strip() if interactive else "",
                "routes": routes_list,
                "persons": persons_list,
                "tags": tags_list,
                "location": {}
            }

            loc_obj = {}
            if address.strip():
                loc_obj["address"] = address.strip().strip('"')
            if gps_lat is not None and gps_lng is not None:
                loc_obj["gps"] = {"lat": gps_lat, "lng": gps_lng}
            if loc_obj:
                card_data["location"] = loc_obj

            cards_dict[ card_data["id"] ] = card_data

    # Превращаем в список и записываем
    final_cards = list(cards_dict.values())
    with open(cards_path, "w", encoding="utf-8") as wf:
        json.dump(final_cards, wf, ensure_ascii=False, indent=2)

    print(f"✅ Импортировано/обновлено карточек: {len(final_cards)}")

if __name__ == "__main__":
    import_cards()
