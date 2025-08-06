# feeds/binance_feed.py

import asyncio
import websockets
import json

class BinanceCVDTracker:
    def __init__(self):
        self.spot_cvd = 0
        self.perp_cvd = 0
        self.price = 0

    async def connect(self):
        asyncio.create_task(self._track_spot())
        asyncio.create_task(self._track_perp())

    async def _track_spot(self):
        uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        async for ws in websockets.connect(uri, ping_interval=None):
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    qty = float(data["q"])
                    is_buyer_maker = data["m"]
                    self.spot_cvd += -qty if is_buyer_maker else qty
                    self.price = float(data["p"])
            except Exception as e:
                print("[X] Binance Spot error:", e)
                await asyncio.sleep(3)

    async def _track_perp(self):
        uri = "wss://fstream.binance.com/ws/btcusdt@trade"
        async for ws in websockets.connect(uri, ping_interval=None):
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    qty = float(data["q"])
                    is_buyer_maker = data["m"]
                    self.perp_cvd += -qty if is_buyer_maker else qty
            except Exception as e:
                print("[X] Binance Perp error:", e)
                await asyncio.sleep(3)

    def get_cvd(self):
        return {
            "spot": round(self.spot_cvd, 2),
            "perp": round(self.perp_cvd, 2),
            "price": self.price
        }
