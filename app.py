from flask import Flask, render_template, request
import os
import json
import time

app = Flask(__name__)
app.secret_key = "secret_key"
USER_DATA_FILE = "user_data.json"

# Загрузка данных пользователя из файла
def load_user_data(username):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            user_data = data.get(username, {"crops": 0, "last_played": int(time.time()), "level": 1})
            user_data.setdefault("level", 1)
            return user_data
    return {"crops": 0, "last_played": int(time.time()), "level": 1}

# Сохранение данных пользователя в файл
def save_user_data(username, crops, last_played, level):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[username] = {"crops": crops, "last_played": last_played, "level": level}

    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/", methods=["GET", "POST"])
def index():
    username = request.args.get("username", "Гость")
    user_data = load_user_data(username)

    # Проверяем время последней игры
    current_time = int(time.time())
    elapsed_time = current_time - user_data['last_played']

    # Обновляем ресурсы
    new_crops = elapsed_time // 600  # 1 урожай каждые 10 минут
    total_crops = user_data['crops'] + new_crops

    # Обновляем информацию о пользователе
    user_data['last_played'] = current_time

    # Сохраняем обновленные данные пользователя
    save_user_data(username, total_crops, current_time, user_data['level'])

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
        save_user_data(username, total_crops, current_time, user_data['level'])

    crops = total_crops
    level = user_data['level']

    return render_template("index.html", message=message, crops=crops, username=username, level=level)

if __name__ == "__main__":
    # Используйте переменную окружения PORT, если она существует, иначе используйте 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)