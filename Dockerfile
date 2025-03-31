# Используем официальный базовый образ Python 3.10 (можно 3.9, 3.11 - на твой вкус)
FROM python:3.10-slim

# Указываем рабочую директорию
WORKDIR /app

# Копируем все файлы в контейнер
COPY . /app

# Обновим pip (на всякий случай)
RUN pip install --upgrade pip

# Установим зависимости из setup.py (aiogram и т.д.)
RUN pip install .

# Запускаем нашего бота
CMD ["python", "main.py"]
