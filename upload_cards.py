import csv
import json
from pathlib import Path

# Константы с путями к файлам
CSV_FILE = "data/new_cards.csv"
JSON_FILE = "data/cards.json"

def upload_cards():
    """
    Читает CSV_FILE (разделитель ';') и обновляет JSON_FILE (cards.json),
    добавляя новые карточки и заменяя существующие дубли по id.
    """
    # 1. Чтение существующего JSON-файла (если есть)
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
    
    # Преобразуем существующие карточки в словарь по id для удобства обновления
    cards_dict = {}
    for card in existing_cards:
        if isinstance(card, dict) and "id" in card:
            cards_dict[card["id"]] = card
    
    # Множество существующих ID для отслеживания обновлений
    existing_ids = set(cards_dict.keys())
    
    # 2. Открытие CSV-файла
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"❌ Не найден CSV-файл: {CSV_FILE}")
        return
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        header = next(reader, None)  # чтение заголовка
        if header is None:
            print("❌ CSV-файл пустой или отсутствуют заголовки.")
            return
        
        # Инициализация счетчиков
        new_count = 0
        updated_count = 0
        
        # 3. Обработка строк CSV
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 16:
                print(f"⚠️ Строка {row_num}: недостаточно столбцов. Пропущено: {row}")
                continue
            
            # Распаковка полей из строки (с учетом наличия 'tags')
            if len(row) == 16:
                (card_id, interactive_str, language, city, address,
                 gps_lat_str, gps_lng_str, title, text, question,
                 options_str, correct_index_str, reality_str, explanation,
                 routes_str, persons_str) = row
                tags_str = ""
            else:
                (card_id, interactive_str, language, city, address,
                 gps_lat_str, gps_lng_str, title, text, question,
                 options_str, correct_index_str, reality_str, explanation,
                 routes_str, persons_str, tags_str) = row
            
            # Удаление лишних пробелов и подготовка значений
            card_id = card_id.strip()
            interactive = interactive_str.strip().lower() == "true"
            lang_val = language.strip().lower()
            city_val = city.strip().lower()
            
            # Проверка дубликатов для подсчета статистики
            if card_id in existing_ids:
                updated_count += 1
            else:
                new_count += 1
            
            # Преобразование координат в float (если не пустые)
            gps_lat = None
            gps_lng = None
            if gps_lat_str.strip():
                try:
                    gps_lat = float(gps_lat_str.strip())
                except ValueError:
                    gps_lat = None
            if gps_lng_str.strip():
                try:
                    gps_lng = float(gps_lng_str.strip())
                except ValueError:
                    gps_lng = None
            
            # Разбиение списка вариантов (options) по ';'
            options_list = []
            if options_str.strip():
                options_list = [opt.strip() for opt in options_str.split(';')]
            
            # Индекс правильного ответа в целое число
            correct_idx = None
            if correct_index_str.strip():
                try:
                    correct_idx = int(correct_index_str.strip())
                except ValueError:
                    correct_idx = None
            
            # Определение иконки по типу (reality)
            reality_val = reality_str.strip().lower()
            if reality_val == "legend":
                icon_val = "🧙🏻‍♂️"
            else:
                icon_val = "📖"
            
            # Разбиение маршрутов, персон и тегов на списки
            routes_list = [route.strip() for route in routes_str.split(';') if route.strip()]
            persons_list = [person.strip() for person in persons_str.split(';') if person.strip()]
            tags_list = [tag.strip() for tag in tags_str.split(';') if tag.strip()]
            
            # Формирование словаря данных карточки
            card_data = {
                "id": card_id,
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
            
            # Заполнение поля location при наличии данных
            loc_obj = {}
            if address.strip():
                loc_obj["address"] = address.strip().strip('"')
            if gps_lat is not None and gps_lng is not None:
                loc_obj["gps"] = {"lat": gps_lat, "lng": gps_lng}
            if loc_obj:
                card_data["location"] = loc_obj
            
            # Добавление/обновление карточки в словарь по id
            cards_dict[card_id] = card_data
        
    # 4. Сохранение объединенного списка карточек обратно в JSON
    final_cards = list(cards_dict.values())
    with open(cards_path, "w", encoding="utf-8") as json_file:
        json.dump(final_cards, json_file, ensure_ascii=False, indent=2)
    
    # 5. Вывод статистики обновления
    print(f"✅ Добавлено карточек: {new_count}, Обновлено: {updated_count}")

# Запуск функции при вызове скрипта напрямую
if __name__ == "__main__":
    upload_cards()
