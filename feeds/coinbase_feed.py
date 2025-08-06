# feeds/coinbase_feed.py (patched with reconnect logic)

import asyncio
import websockets
import json

class CoinbaseSpotCVD:
    def __init__(self):
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.product_id = "BTC-USD"
        self.cvd = 0
        self.last_price = None

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    sub_msg = {
                        "type": "subscribe",
                        "product_ids": [self.product_id],
                        "channels": ["matches"]
                    }
                    await ws.send(json.dumps(sub_msg))

                    async for msg in ws:
                        await self._process(msg)
            except Exception as e:
                print("[X] Coinbase reconnecting:", e)
                await asyncio.sleep(5)

    async def _process(self, msg):
        try:
            data = json.loads(msg)
            if data.get("type") == "match":
                price = float(data["price"])
                size = float(data["size"])
                side = data["side"]

                self.last_price = price
                self.cvd += size if side == "buy" else -size
        except Exception as e:
            print("[X] Coinbase parse error:", e)

    def get_cvd(self):
        return round(self.cvd, 2)

    def get_last_price(self):
        return self.last_price
