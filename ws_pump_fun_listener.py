import asyncio
import websockets
import json
import requests

WS_URL = "wss://pumpportal.fun/api/data"
SEEN = set()

def save_token(address):
    try:
        response = requests.post("https://pump-fun-proxy-production-594d.up.railway.app/add-token", json={"token": address})
        print(f"Sent token to proxy: {address} — status: {response.status_code}")
    except Exception as e:
        print(f"Error sending token to proxy: {e}")

async def listen():
    print("Connecting to pumpportal.fun WebSocket...")
    async with websockets.connect(WS_URL) as ws:
        print("Connected. Subscribing to new token events...")
        await ws.send(json.dumps({"method": "subscribeNewToken"}))

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if isinstance(data, dict) and "tokenAddress" in data:
                    address = data["tokenAddress"]
                    if address not in SEEN:
                        print(f"New token: {address}")
                        save_token(address)
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(listen())
