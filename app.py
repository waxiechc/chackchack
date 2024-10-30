from flask import Flask, render_template, request, session
import random

app = Flask(__name__)
app.secret_key = "secret_key"

@app.route("/", methods=["GET", "POST"])
def index():
    # Проверяем и инициализируем переменные сессии, если они отсутствуют
    if "target_number" not in session:
        session["target_number"] = random.randint(1, 100)
    if "attempts" not in session:
        session["attempts"] = 0
    if "history" not in session:
        session["history"] = []

    target_number = session["target_number"]
    attempts = session["attempts"]
    history = session["history"]

    message = ""
    guessed = False

    if request.method == "POST":
        user_guess = int(request.form.get("guess"))
        session["attempts"] += 1

        if user_guess < target_number:
            message = "Ваше число меньше загаданного!"
        elif user_guess > target_number:
            message = "Ваше число больше загаданного!"
        else:
            message = "Поздравляем! Вы угадали число!"
            guessed = True
            session.pop("target_number", None)  # Сброс игры после угадывания

        # Сохраняем историю попыток
        history.append(f"Попытка {session['attempts']}: {user_guess} - {message}")

    return render_template("index.html", message=message, guessed=guessed, attempts=session["attempts"], history=history)

if __name__ == "__main__":
    app.run(debug=True)