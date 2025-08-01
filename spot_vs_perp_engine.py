# spot_vs_perp_engine.py

import asyncio
from feeds.coinbase_feed import CoinbaseSpotCVD
from feeds.binance_feed import BinanceCVDTracker

class SpotVsPerpEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()

    async def run(self):
        await asyncio.gather(
            self.coinbase.connect(),
            self.binance.connect(),
            self.monitor()
        )

    async def monitor(self):
        while True:
            cb_cvd = self.coinbase.get_cvd()
            cb_price = self.coinbase.get_last_price()
            bin_data = self.binance.get_cvd()

            spot = bin_data["spot"]
            perp = bin_data["perp"]
            price = bin_data["price"]

            # Scoring logic
            if spot > 0 and perp < 0 and cb_cvd > 0:
                signal = "✅ Spot-led move — real demand"
            elif perp > 0 and spot <= 0 and cb_cvd <= 0:
                signal = "🚨 Perp-led pump — potential trap"
            elif cb_cvd > 0 and spot < 0:
                signal = "🟡 U.S. Spot buying (Coinbase), Binance lagging"
            else:
                signal = "📊 Mixed flow — no clear bias"

            print(f"\n📈 Price: {price or cb_price}")
            print(f"💧 Coinbase Spot CVD: {cb_cvd}")
            print(f"🟢 Binance Spot CVD: {spot}")
            print(f"🔴 Binance Perp CVD: {perp}")
            print(f"🧠 Signal: {signal}")

            await asyncio.sleep(5)

if __name__ == "__main__":
    engine = SpotVsPerpEngine()
    asyncio.run(engine.run())
