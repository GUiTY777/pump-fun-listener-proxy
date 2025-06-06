from flask import Flask, jsonify, request
import json
import os

print("🚀 Flask proxy.py запущен")

app = Flask(__name__)

TOKENS_FILE = "tokens_raw.json"
SEEN = set()

# Загружаем токены, безопасно
def load_tokens():
    global SEEN
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    SEEN.update(data)
                    print(f"✅ Загружено {len(data)} токенов из файла")
                else:
                    print("⚠️ tokens_raw.json не содержит список")
        except Exception as e:
            print(f"❌ Ошибка при загрузке tokens_raw.json: {e}")
    else:
        print("ℹ️ Файл tokens_raw.json не найден — стартуем с пустого списка")

# Сохраняем токены
def save_tokens():
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(list(SEEN), f, indent=2)
        print(f"💾 Сохранено {len(SEEN)} токенов")
    except Exception as e:
        print(f"❌ Ошибка при сохранении tokens_raw.json: {e}")

# Загружаем при запуске
load_tokens()

@app.route("/tokens")
def get_tokens():
    print("📥 Запрос: /tokens")
    return jsonify(list(SEEN)), 200

@app.route("/add-token", methods=["POST"])
def add_token():
    print("📥 Запрос: /add-token")
    try:
        data = request.get_json()
        token = data.get("token")
        if token and token not in SEEN:
            SEEN.add(token)
            save_tokens()
            print(f"✅ Новый токен сохранён: {token}")
            return {"status": "saved"}, 200
        print("ℹ️ Токен уже существует или пустой")
        return {"status": "ignored"}, 200
    except Exception as e:
        print(f"❌ Ошибка в /add-token: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
