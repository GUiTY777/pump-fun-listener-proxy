from flask import Flask, jsonify, request
import json
import os

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
                else:
                    print("⚠️ tokens_raw.json не содержит список")
        except Exception as e:
            print(f"❌ Ошибка при загрузке tokens_raw.json: {e}")

# Сохраняем токены
def save_tokens():
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(list(SEEN), f, indent=2)
    except Exception as e:
        print(f"❌ Ошибка при сохранении tokens_raw.json: {e}")

# Загружаем при запуске
load_tokens()

@app.route("/tokens")
def get_tokens():
    return jsonify(list(SEEN)), 200

@app.route("/add-token", methods=["POST"])
def add_token():
    try:
        data = request.get_json()
        token = data.get("token")
        if token and token not in SEEN:
            SEEN.add(token)
            save_tokens()
            print(f"✅ Новый токен сохранён: {token}")
            return {"status": "saved"}, 200
        return {"status": "ignored"}, 200
    except Exception as e:
        print(f"❌ Ошибка в /add-token: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
