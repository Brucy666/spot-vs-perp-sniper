# feeds/bybit_feed.py (patched with reconnect logic)

import asyncio
import websockets
import json

class BybitCVDTracker:
    def __init__(self):
        self.ws_url = "wss://stream.bybit.com/realtime_public"
        self.symbol = "BTCUSDT"
        self.cvd = 0
        self.last_price = None

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    sub_msg = {
                        "op": "subscribe",
                        "args": [f"trade.{self.symbol}"]
                    }
                    await ws.send(json.dumps(sub_msg))

                    async for msg in ws:
                        await self._process(msg)
            except Exception as e:
                print("[X] Bybit reconnecting:", e)
                await asyncio.sleep(5)

    async def _process(self, msg):
        try:
            data = json.loads(msg)
            if data.get("topic", "").startswith("trade."):
                trades = data.get("data", [])
                for t in trades:
                    side = t.get("S")
                    price = float(t.get("p"))
                    qty = float(t.get("v"))

                    self.last_price = price
                    self.cvd += qty if side == "Buy" else -qty

        except Exception as e:
            print("[X] Bybit parse error:", e)

    def get_cvd(self):
        return round(self.cvd, 2)

    def get_price(self):
        return self.last_price
