from flask import Flask, render_template, request
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
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    crops INTEGER,
                    last_played INTEGER,
                    level INTEGER
                );
            """)
            conn.commit()
    print("Table created successfully.")

# Загрузка данных пользователя
def load_user_data(telegram_id, username):
    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            user_data = cursor.fetchone()
            if user_data is None:
                cursor.execute("INSERT INTO users (telegram_id, username, crops, last_played, level) VALUES (%s, %s, %s, %s, %s)",
                               (telegram_id, username, 0, int(time.time()), 1))
                conn.commit()
                user_data = {"telegram_id": telegram_id, "username": username, "crops": 0, "last_played": int(time.time()), "level": 1}
            return user_data

# Сохранение данных пользователя
def save_user_data(telegram_id, crops, last_played, level):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET crops = %s, last_played = %s, level = %s WHERE telegram_id = %s",
                           (crops, last_played, level, telegram_id))
            conn.commit()

@app.route("/", methods=["GET", "POST"])
def index():
    telegram_id = request.args.get("telegram_id")
    username = request.args.get("username", "Игрок")

    if not telegram_id:
        return "Ошибка: Не удалось получить идентификатор Telegram пользователя."

    # Преобразуем telegram_id в число
    try:
        telegram_id = int(telegram_id)
    except ValueError:
        return "Ошибка: Неверный идентификатор Telegram пользователя."

    user_data = load_user_data(telegram_id, username)

    # Проверяем время последней игры
    current_time = int(time.time())
    elapsed_time = current_time - user_data['last_played']

    # Обновляем ресурсы
    new_crops = elapsed_time // 600  # 1 урожай каждые 10 минут
    total_crops = user_data['crops'] + new_crops

    # Обновляем информацию о пользователе
    user_data['last_played'] = current_time

    # Сохраняем обновленные данные пользователя
    save_user_data(telegram_id, total_crops, current_time, user_data['level'])

    message = ""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "explore":
            crops_found = 2 * user_data['level']  # Найденный урожай зависит от уровня
            total_crops += crops_found
            message = f"Вы исследовали поле и нашли {crops_found} урожая!"
        elif action == "upgrade":
            if total_crops >= 10:  # Сброс уровня при 10 урожаях
                total_crops -= 10
                user_data['level'] += 1
                message = f"Вы повысили уровень! Теперь вы на уровне {user_data['level']}."
            else:
                message = "У вас недостаточно урожая для повышения уровня!"

        # Сохраняем обновленные данные пользователя
        save_user_data(telegram_id, total_crops, current_time, user_data['level'])

    crops = total_crops
    level = user_data['level']

    return render_template("index.html", message=message, crops=crops, username=username, level=level)

if __name__ == "__main__":
    create_table()  # Создание таблицы при запуске
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)