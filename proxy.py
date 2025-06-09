from flask import Flask, jsonify, request
import json
import os
import requests
import time

app = Flask(__name__)

TOKENS_FILE = "tokens_raw.json"
MIN_LIQUIDITY = 500
MIN_VOLUME = 500
MIN_HOLDERS = 10
MIN_AGE_SECONDS = 120  # минимум 2 минуты

BIRDEYE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImQzZGRhYTcwLWExNzMtNGFmYy04ZTAwLTU0MzUxNWMxNTgyNiIsIm9yZ0lkIjoiNDUwNzAyIiwidXNlcklkIjoiNDYzNzM2IiwidHlwZUlkIjoiOTQwZjcxYTgtZGNjYS00NDNkLWI5NjUtNTdkN2NlYzUyNmZiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDg5NDEzMDMsImV4cCI6NDkwNDcwMTMwM30._2Vmv1XHEFt9LSQExca-i1YsFK0eEkc0pI14NHFn4Ec"
MORALIS_API_KEY = "ddf072bbd0b643f3b2d4b7d9e4dafb2c"  # вставь сюда актуальный свой ключ

HEADERS_BIRDEYE = {"X-API-KEY": BIRDEYE_API_KEY}
HEADERS_MORALIS = {"accept": "application/json", "X-API-Key": MORALIS_API_KEY}

SEEN = set()

# Загрузка токенов при старте
def load_tokens():
    global SEEN
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    SEEN.update(data)
        except Exception as e:
            print(f"❌ Ошибка при загрузке tokens_raw.json: {e}")

# Сохранение токенов
def save_tokens():
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(list(SEEN), f, indent=2)
    except Exception as e:
        print(f"❌ Ошибка при сохранении tokens_raw.json: {e}")

# Проверка токена по фильтрам
def is_token_valid(address):
    try:
        # Birdeye: получаем ликвидность, объём, дату создания
        birdeye = requests.get(
            f"https://public-api.birdeye.so/public/token/{address}",
            headers=HEADERS_BIRDEYE,
            timeout=5
        ).json()

        data = birdeye.get("data", {})
        liquidity = data.get("liquidity", 0)
        volume = data.get("volume_24h_quote", 0)
        created_unix = data.get("created_at")

        if not all([liquidity, volume, created_unix]):
            return False

        age = time.time() - int(created_unix)
        if age < MIN_AGE_SECONDS:
            return False

        # Moralis: получаем количество холдеров
        moralis = requests.get(
            f"https://solana-gateway.moralis.io/token/mainnet/{address}/holders?limit=1",
            headers=HEADERS_MORALIS,
            timeout=5
        ).json()
        holders = moralis.get("total", 0)

        return liquidity >= MIN_LIQUIDITY and volume >= MIN_VOLUME and holders >= MIN_HOLDERS
    except Exception as e:
        print(f"❌ Ошибка фильтрации токена {address}: {e}")
        return False

# Эндпоинт: получить все сохранённые токены
@app.route("/tokens")
def get_tokens():
    return jsonify(list(SEEN)), 200

# Эндпоинт: добавить новый токен
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

# Эндпоинт: отфильтрованные токены
@app.route("/filtered-tokens")
def filtered_tokens():
    result = []
    for token in SEEN:
        if is_token_valid(token):
            result.append(token)
    return jsonify(result), 200

# Запуск сервера
if __name__ == "__main__":
    load_tokens()
    app.run(host="0.0.0.0", port=8000)
