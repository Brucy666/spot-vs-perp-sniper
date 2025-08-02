# feeds/binance_feed.py

import asyncio
import websockets
import json

class BinanceCVDTracker:
    def __init__(self, symbol="btcusdt"):
        self.symbol = symbol
        self.spot_cvd = 0.0
        self.perp_cvd = 0.0
        self.price = None

    async def connect(self):
        uri = (
            "wss://stream.binance.com:9443/stream?streams="
            f"{self.symbol}@aggTrade/{self.symbol}usdt@aggTrade"
        )
        async with websockets.connect(uri) as ws:
            async for message in ws:
                await self.handle_message(json.loads(message))

    async def handle_message(self, msg):
        stream = msg.get("stream", "")
        data = msg.get("data", {})

        if not data:
            return

        price = float(data["p"])
        qty = float(data["q"])
        side = data["m"]  # market maker: True = sell, False = buy
        self.price = price

        if "@aggTrade" in stream and "usdt@aggTrade" in stream:
            # Spot stream
            if side:
                self.spot_cvd -= qty
            else:
                self.spot_cvd += qty
        elif "usdt" not in stream:
            # Perp stream (futures default)
            if side:
                self.perp_cvd -= qty
            else:
                self.perp_cvd += qty

    def get_cvd(self):
        return {
            "spot": round(self.spot_cvd, 2),
            "perp": round(self.perp_cvd, 2),
            "price": self.price
        }
