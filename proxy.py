from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import requests
import time

app = Flask(__name__)
CORS(app)

TOKENS_FILE = "tokens_raw.json"
MIN_LIQUIDITY = 500
MIN_VOLUME = 500
MIN_HOLDERS = 10
MIN_AGE_SECONDS = 120

BIRDEYE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImQzZGRhYTcwLWExNzMtNGFmYy04ZTAwLTU0MzUxNWMxNTgyNiIsIm9yZ0lkIjoiNDUwNzAyIiwidXNlcklkIjoiNDYzNzM2IiwidHlwZUlkIjoiOTQwZjcxYTgtZGNjYS00NDNkLWI5NjUtNTdkN2NlYzUyNmZiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDg5NDEzMDMsImV4cCI6NDkwNDcwMTMwM30._2Vmv1XHEFt9LSQExca-i1YsFK0eEkc0pI14NHFn4Ec"
MORALIS_API_KEY = "ddf072bbd0b643f3b2d4b7d9e4dafb2c"

HEADERS_BIRDEYE = {"X-API-KEY": BIRDEYE_API_KEY}
HEADERS_MORALIS = {"accept": "application/json", "X-API-Key": MORALIS_API_KEY}

SEEN = set()

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

def save_tokens():
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(list(SEEN), f, indent=2)
    except Exception as e:
        print(f"❌ Ошибка при сохранении tokens_raw.json: {e}")

def is_token_valid(address):
    try:
        birdeye = requests.get(
            f"https://public-api.birdeye.so/public/token/{address}",
            headers=HEADERS_BIRDEYE,
            timeout=5
        ).json()

        data = birdeye.get("data", {})
        liquidity = data.get("liquidity", 0)
        volume = data.get("volume_24h_quote", 0)
        created_unix = data.get("created_at")
        price = data.get("value", 0)

        if not all([liquidity, volume, created_unix, price]):
            return False, None

        age = time.time() - int(created_unix)
        if age < MIN_AGE_SECONDS:
            return False, None

        moralis = requests.get(
            f"https://solana-gateway.moralis.io/token/mainnet/{address}/holders?limit=1",
            headers=HEADERS_MORALIS,
            timeout=5
        ).json()
        holders = moralis.get("total", 0)

        if liquidity >= MIN_LIQUIDITY and volume >= MIN_VOLUME and holders >= MIN_HOLDERS:
            # Получим имя токена
            meta = requests.get(
                f"https://solana-gateway.moralis.io/token/mainnet/{address}/metadata",
                headers=HEADERS_MORALIS,
                timeout=5
            ).json()
            name = meta.get("name", address)
            return True, {
                "baseToken": {"name": name},
                "priceUsd": price,
                "liquidity": {"usd": liquidity},
                "volume": {"h24": volume},
                "holders": holders
            }
        return False, None
    except Exception as e:
        print(f"❌ Ошибка фильтрации токена {address}: {e}")
        return False, None

@app.route("/tokens")
def get_tokens():
    result = []
    for token in SEEN:
        is_valid, data = is_token_valid(token)
        if is_valid:
            result.append(data)
    return jsonify(result), 200

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

@app.route("/raw-tokens")
def raw_tokens():
    return jsonify(list(SEEN)), 200

@app.route("/filtered-addresses")
def filtered_tokens():
    result = []
    for token in SEEN:
        is_valid, _ = is_token_valid(token)
        if is_valid:
            result.append(token)
    return jsonify(result), 200

if __name__ == "__main__":
    load_tokens()
    app.run(host="0.0.0.0", port=8000)
