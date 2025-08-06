# feeds/bybit_feed.py (updated for V5 WebSocket API)

import asyncio
import json
import websockets

class BybitCVDTracker:
    def __init__(self):
        self.price = 0.0
        self.cvd = 0.0
        self.symbol = "BTCUSDT"
        self.endpoint = "wss://stream.bybit.com/v5/public/linear"

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.endpoint) as ws:
                    # Subscribe to trades
                    await ws.send(json.dumps({
                        "op": "subscribe",
                        "args": [f"publicTrade.{self.symbol}"]
                    }))

                    async for message in ws:
                        data = json.loads(message)

                        if data.get("topic") == f"publicTrade.{self.symbol}" and "data" in data:
                            for trade in data["data"]:
                                price = float(trade["p"])
                                size = float(trade["v"])
                                side = trade["S"]  # Buy or Sell

                                self.price = price
                                if side == "Buy":
                                    self.cvd += size
                                else:
                                    self.cvd -= size

            except Exception as e:
                print("[X] Bybit feed error:", e)
                await asyncio.sleep(5)  # brief delay before reconnect

    def get_price(self):
        return self.price

    def get_cvd(self):
        return round(self.cvd, 2)
