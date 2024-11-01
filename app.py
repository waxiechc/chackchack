from flask import Flask, render_template, request, jsonify
import os
import time
import psycopg2
import hashlib
import hmac
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен вашего бота Telegram

# Функция подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

# Верификация подлинности данных initData
def verify_telegram_auth(data_string, bot_token):
    check_hash = data_string.split('hash=')[-1]
    data_check = data_string.replace(f"&hash={check_hash}", "")
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_hex = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    return hash_hex == check_hash

# Создание таблицы users, если ее нет
def create_table():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id TEXT PRIMARY KEY,
                    username TEXT,
                    crops INTEGER,
                    last_played INTEGER,
                    level INTEGER
                );
            """)
            conn.commit()

# Загрузка данных пользователя
def load_user_data(telegram_id, username):
    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            user_data = cursor.fetchone()
            if user_data is None:
                cursor.execute(
                    "INSERT INTO users (telegram_id, username, crops, last_played, level) VALUES (%s, %s, %s, %s, %s)",
                    (telegram_id, username, 0, int(time.time()), 1)
                )
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

# Верификация initData
@app.route("/verify_user", methods=["GET"])
def verify_user():
    init_data = request.args.get("initData", "")
    if verify_telegram_auth(init_data, BOT_TOKEN):
        data_dict = dict(pair.split("=") for pair in init_data.split("&") if "=" in pair)
        telegram_id = data_dict.get("id")
        username = data_dict.get("username", "Игрок")
        return jsonify({"success": True, "telegram_id": telegram_id, "username": username})
    else:
        return jsonify({"success": False})

# Основной маршрут
@app.route("/", methods=["GET", "POST"])
def index():
    telegram_id = request.args.get("telegram_id")
    username = request.args.get("username", "Гость")

    if not telegram_id:
        return "Ошибка: Не удалось получить идентификатор Telegram пользователя."

    user_data = load_user_data(telegram_id, username)
    current_time = int(time.time())
    elapsed_time = current_time - user_data['last_played']
    new_crops = elapsed_time // 600  # 1 урожай каждые 10 минут
    total_crops = user_data['crops'] + new_crops
    user_data['last_played'] = current_time
    save_user_data(telegram_id, total_crops, current_time, user_data['level'])

    message = ""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "explore":
            crops_found = 2 * user_data['level']
            total_crops += crops_found
            message = f"Вы исследовали поле и нашли {crops_found} урожая!"
        elif action == "upgrade":
            if total_crops >= 10:
                total_crops -= 10
                user_data['level'] += 1
                message = f"Вы повысили уровень! Теперь вы на уровне {user_data['level']}."
            else:
                message = "У вас недостаточно урожая для повышения уровня!"
        save_user_data(telegram_id, total_crops, current_time, user_data['level'])

    return render_template("index.html", message=message, crops=total_crops, username=username, level=user_data['level'])

if __name__ == "__main__":
    create_table()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)