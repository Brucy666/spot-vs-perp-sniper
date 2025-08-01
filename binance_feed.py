# feeds/binance_feed.py

import asyncio
import websockets
import json

class BinanceCVDTracker:
    def __init__(self, symbol="btcusdt"):
        self.symbol = symbol
        self.spot_cvd = 0
        self.perp_cvd = 0
        self.price = None

    async def connect(self):
        uri = "wss://stream.binance.com:9443/stream?streams="
        uri += f"{self.symbol}@aggTrade/{self.symbol}perp@aggTrade"

        async with websockets.connect(uri) as ws:
            async for message in ws:
                await self.handle_message(json.loads(message))

    async def handle_message(self, msg):
        data = msg.get("data", {})
        stream = msg.get("stream", "")

        price = float(data["p"])
        qty = float(data["q"])
        side = data["m"]  # market maker: True = sell, False = buy

        if "perp" in stream:
            if side:
                self.perp_cvd -= qty
            else:
                self.perp_cvd += qty
        else:
            if side:
                self.spot_cvd -= qty
            else:
                self.spot_cvd += qty

        self.price = price

    def get_cvd(self):
        return {
            "spot": round(self.spot_cvd, 2),
            "perp": round(self.perp_cvd, 2),
            "price": self.price
        }


if __name__ == "__main__":
    tracker = BinanceCVDTracker()

    async def run():
        await tracker.connect()

    asyncio.run(run())
