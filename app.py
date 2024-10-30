from flask import Flask, render_template, request, session
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
            # Убедимся, что 'level' всегда присутствует
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

    if request.method == "POST":
        action = request.form.get("action")
        message = ""
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

    else:
        message = ""

    crops = total_crops
    level = user_data['level']

    return render_template("index.html", message=message, crops=crops, username=username, level=level)

if __name__ == "__main__":
    app.run(debug=True)

app = Flask(__name__)

# Начальные значения
users_data = {
    'username': 'Игрок',
    'level': 1,
    'crops': 0,
    'explorations': 0,
    'upgrade_cost': 10  # Начальная стоимость улучшения
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "explore":
            # Собираем урожай
            users_data['crops'] += 10  # Пример увеличения урожая
            users_data['explorations'] += 1
            message = "Урожай собран!"

        elif action == "upgrade":
            # Проверяем достаточно ли средств для улучшения
            if users_data['crops'] >= users_data['upgrade_cost']:
                users_data['crops'] -= users_data['upgrade_cost']
                users_data['level'] += 1
                users_data['upgrade_cost'] *= 2  # Увеличиваем стоимость улучшения
                message = "Уровень улучшен!"
            else:
                message = "Недостаточно урожая для улучшения!"

    else:
        message = ""

    # Сохраняем данные пользователя
    save_user_data()

    return render_template("index.html", username=users_data['username'],
                           level=users_data['level'],
                           crops=users_data['crops'],
                           explorations=users_data['explorations'],
                           upgrade_cost=users_data['upgrade_cost'],  # Передаем стоимость улучшения
                           message=message)

def save_user_data():
    # Сохранение данных в файл или другим способом
    with open('user_data.json', 'w') as f:
        json.dump(users_data, f)

if __name__ == "__main__":
    app.run(debug=True)
