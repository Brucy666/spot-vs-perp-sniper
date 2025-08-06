# feeds/binance_feed.py (patched with reconnect logic)

import asyncio
import websockets
import json

class BinanceCVDTracker:
    def __init__(self):
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.symbol_spot = "btcusdt"
        self.symbol_perp = "btcusdt@aggTrade"

        self.spot_cvd = 0
        self.perp_cvd = 0
        self.last_price = None

    async def connect(self):
        while True:
            try:
                streams = f"{self.symbol_spot}@aggTrade/{self.symbol_perp}"
                full_url = f"{self.ws_url}/{streams}"
                async with websockets.connect(full_url) as ws:
                    async for msg in ws:
                        await self._process(msg)
            except Exception as e:
                print("[X] Binance reconnecting:", e)
                await asyncio.sleep(5)

    async def _process(self, msg):
        try:
            data = json.loads(msg)
            stream = data.get("s") or data.get("stream", "").split("@")[0]
            payload = data.get("data", data)
            price = float(payload["p"])
            qty = float(payload["q"])
            is_buyer_maker = payload["m"]

            self.last_price = price
            delta = -qty if is_buyer_maker else qty

            if stream.lower() == self.symbol_spot:
                self.spot_cvd += delta
            elif stream.lower() == self.symbol_perp:
                self.perp_cvd += delta

        except Exception as e:
            print("[X] Binance parse error:", e)

    def get_cvd(self):
        return {
            "spot": round(self.spot_cvd, 2),
            "perp": round(self.perp_cvd, 2),
            "price": self.last_price
        }
