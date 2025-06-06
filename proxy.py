from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

TOKENS_FILE = "tokens_raw.json"
SEEN = set()

# Безопасно загружаем токены из файла
if os.path.exists(TOKENS_FILE):
    try:
        with open(TOKENS_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                SEEN.update(data)
    except Exception as e:
        print(f"Failed to load tokens file: {e}")

# Получить список всех токенов
@app.route("/tokens")
def get_tokens():
    return jsonify(list(SEEN))

# Добавить новый токен
@app.route("/add-token", methods=["POST"])
def add_token():
    data = request.json
    token = data.get("token")
    if token and token not in SEEN:
        SEEN.add(token)
        with open(TOKENS_FILE, "w") as f:
            json.dump(list(SEEN), f, indent=2)
        print(f"Saved token from listener: {token}")
        return {"status": "saved"}, 200
    return {"status": "ignored"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
