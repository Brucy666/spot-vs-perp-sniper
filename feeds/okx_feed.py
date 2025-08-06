# okx_feed.py (patched with resilient reconnect loop)

import asyncio
import websockets
import json

class OKXCVDTracker:
    def __init__(self):
        self.cvd = 0
        self.price = 0
        self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"

    async def connect(self):
        while True:
            try:
                print("[OKX] Connecting to WebSocket...")
                async with websockets.connect(self.ws_url, ping_interval=20) as ws:
                    await self.subscribe(ws)
                    await self.listen(ws)
            except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
                print("[OKX] Connection lost. Reconnecting in 5s...", e)
                await asyncio.sleep(5)
            except Exception as e:
                print("[OKX] Unexpected error:", e)
                await asyncio.sleep(5)

    async def subscribe(self, ws):
        payload = {
            "op": "subscribe",
            "args": [{"channel": "open_interest", "instId": "BTC-USD-SWAP"}]
        }
        await ws.send(json.dumps(payload))

    async def listen(self, ws):
        async for msg in ws:
            data = json.loads(msg)
            if "data" in data:
                self.handle_data(data["data"])

    def handle_data(self, payload):
        try:
            # Example: grab OI or price for fallback
            item = payload[0]
            self.cvd = float(item.get("oi", 0))
            self.price = float(item.get("last", 0))
        except Exception as e:
            print("[OKX] Failed to parse data:", e)

    def get_cvd(self):
        return self.cvd

    def get_price(self):
        return self.price
