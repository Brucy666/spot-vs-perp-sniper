# feeds/okx_feed.py

import asyncio
import websockets
import json

class OKXCVDTracker:
    def __init__(self):
        self.cvd = 0
        self.price = 0

    async def connect(self):
        uri = "wss://ws.okx.com:8443/ws/v5/public"
        async for ws in websockets.connect(uri, ping_interval=None):
            try:
                await ws.send(json.dumps({
                    "op": "subscribe",
                    "args": [{"channel": "trades", "instId": "BTC-USDT-SWAP"}]
                }))
                async for msg in ws:
                    data = json.loads(msg)
                    if "data" in data:
                        for trade in data["data"]:
                            qty = float(trade["sz"])
                            side = trade["side"]
                            self.cvd += qty if side == "buy" else -qty
                            self.price = float(trade["px"])
            except Exception as e:
                print("[X] OKX error:", e)
                await asyncio.sleep(3)

    def get_cvd(self):
        return round(self.cvd, 2)

    def get_price(self):
        return self.price
