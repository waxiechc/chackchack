from flask import Flask, render_template, request, redirect, url_for
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env
app = Flask(__name__)
app.secret_key = "secret_key"

# Подключение к базе данных PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

# Создание таблицы users, если ее нет
def create_table():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id TEXT PRIMARY KEY,
                    crops INTEGER,
                    last_harvest_time INTEGER,
                    level INTEGER
                );
            """)
            conn.commit()
    print("Table created successfully.")

# Загрузка данных пользователя
def load_user_data(telegram_id):
    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            user_data = cursor.fetchone()
            if user_data is None:
                cursor.execute("INSERT INTO users (telegram_id, crops, last_harvest_time, level) VALUES (%s, %s, %s, %s)",
                               (telegram_id, 0, int(time.time()), 1))
                conn.commit()
                user_data = {"telegram_id": telegram_id, "crops": 0, "last_harvest_time": int(time.time()), "level": 1}
            return user_data

# Сохранение данных пользователя
def save_user_data(telegram_id, crops, last_harvest_time, level):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET crops = %s, last_harvest_time = %s, level = %s WHERE telegram_id = %s",
                           (crops, last_harvest_time, level, telegram_id))
            conn.commit()

# Функция для автоматического сбора урожая
def calculate_harvest(user_data):
    current_time = int(time.time())
    elapsed_time = current_time - user_data['last_harvest_time']
    # Проверка времени сбора урожая каждые 8 часов
    if elapsed_time >= 8 * 3600:  # 8 часов в секундах
        user_data['last_harvest_time'] = current_time
        user_data['crops'] = 0  # Урожай сбрасывается каждые 8 часов
    else:
        user_data['crops'] += (elapsed_time // 3600) * 125  # Добавляем урожай в зависимости от прошедших часов
        user_data['last_harvest_time'] += (elapsed_time // 3600) * 3600  # Обновляем время на полные часы

@app.route("/", methods=["GET", "POST"])
def index():
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        return "Ошибка: Не удалось получить идентификатор Telegram пользователя."

    user_data = load_user_data(telegram_id)

    # Обновляем прогресс сбора урожая
    calculate_harvest(user_data)

    message = ""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "explore":
            crops_found = 2 * user_data['level']  # Найденный урожай зависит от уровня
            user_data['crops'] += crops_found
            message = f"Вы исследовали поле и нашли {crops_found} урожая!"
        elif action == "upgrade":
            if user_data['crops'] >= 10:  # Стоимость улучшения уровня
                user_data['crops'] -= 10
                user_data['level'] += 1
                message = f"Вы повысили уровень! Теперь вы на уровне {user_data['level']}."
            else:
                message = "У вас недостаточно урожая для повышения уровня!"

        # Сохраняем обновленные данные пользователя
        save_user_data(telegram_id, user_data['crops'], user_data['last_harvest_time'], user_data['level'])

    crops = user_data['crops']
    level = user_data['level']

    return render_template("index.html", message=message, crops=crops, username=telegram_id, level=level)

if __name__ == "__main__":
    create_table()  # Создание таблицы при запуске
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)