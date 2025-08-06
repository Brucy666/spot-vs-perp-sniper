# feeds/bybit_feed.py

import asyncio
import websockets
import json

class BybitCVDTracker:
    def __init__(self):
        self.cvd = 0
        self.price = 0

    async def connect(self):
        uri = "wss://stream.bybit.com/v5/public/linear"
        async for ws in websockets.connect(uri, ping_interval=None):
            try:
                await ws.send(json.dumps({
                    "op": "subscribe",
                    "args": ["publicTrade.BTCUSDT"]
                }))
                async for msg in ws:
                    data = json.loads(msg)
                    if "data" in data:
                        for trade in data["data"]:
                            qty = float(trade["v"])
                            side = trade["S"]
                            self.cvd += qty if side == "Buy" else -qty
                            self.price = float(trade["p"])
            except Exception as e:
                print("[X] Bybit Perp error:", e)
                await asyncio.sleep(3)

    def get_cvd(self):
        return round(self.cvd, 2)

    def get_price(self):
        return self.price
