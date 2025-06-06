from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)
TOKENS_FILE = "tokens_raw.json"
SEEN = set()

# Загрузка токенов
if os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, "r") as f:
        try:
            SEEN.update(json.load(f))
        except:
            pass

@app.route("/tokens")
def get_tokens():
    return jsonify(list(SEEN))

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
