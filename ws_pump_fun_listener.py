import asyncio
import websockets
import json
import os
import aiohttp

WS_URL = "wss://pumpportal.fun/api/data"
PROXY_URL = "https://pump-fun-proxy-production-594d.up.railway.app/add-token"
TOKENS_FILE = "tokens_raw.json"
SEEN = set()

# Загружаем сохранённые токены
def load_existing_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, "r") as f:
                data = json.load(f)
                for addr in data:
                    SEEN.add(addr)
            print(f"✅ Загружено токенов: {len(SEEN)}")
        except Exception as e:
            print(f"❌ Ошибка чтения tokens_raw.json: {e}")
    else:
        print("🟦 Файл tokens_raw.json не найден — стартуем с нуля")

# Сохраняем локально и шлём в прокси
def save_token(address):
    SEEN.add(address)
    with open(TOKENS_FILE, "w") as f:
        json.dump(list(SEEN), f, indent=2)
    print(f"💾 Сохранено {len(SEEN)} токенов локально")

    # Отправляем в proxy
    asyncio.create_task(send_to_proxy(address))

async def send_to_proxy(address):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(PROXY_URL, json={"token": address}) as resp:
                if resp.status == 200:
                    print(f"📤 Токен отправлен в прокси: {address}")
                else:
                    print(f"⚠️ Не удалось отправить токен в прокси: {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка отправки в прокси: {e}")

async def listen():
    print("🔌 Подключаемся к WebSocket pumpportal.fun...")
    async with websockets.connect(WS_URL) as ws:
        print("✅ Подключено. Подписываемся на новые токены...")

        await ws.send(json.dumps({"method": "subscribeNewToken"}))

        while True:
            try:
                msg = await ws.recv()
                print(f"📩 Получено сообщение: {msg}")

                data = json.loads(msg)
                if isinstance(data, dict) and data.get("txType") == "create" and "mint" in data:
                    address = data["mint"]
                    if address not in SEEN:
                        print(f"🆕 Новый токен: {address}")
                        save_token(address)
                else:
                    print("⚠️ Нет поля tokenAddress в сообщении")

            except Exception as e:
                print(f"❌ Ошибка при обработке сообщения: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    load_existing_tokens()
    asyncio.run(listen())
