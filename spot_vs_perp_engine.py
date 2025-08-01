# spot_vs_perp_engine.py

import asyncio
from feeds.coinbase_feed import CoinbaseSpotCVD
from feeds.binance_feed import BinanceCVDTracker
from feeds.bybit_feed import BybitCVDTracker
from feeds.okx_feed import OKXCVDTracker


class SpotVsPerpEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

    async def run(self):
        await asyncio.gather(
            self.coinbase.connect(),
            self.binance.connect(),
            self.bybit.connect(),
            self.okx.connect(),
            self.monitor()
        )

    async def monitor(self):
        while True:
            # Get CVD data
            cb_cvd = self.coinbase.get_cvd()
            cb_price = self.coinbase.get_last_price()

            bin_data = self.binance.get_cvd()
            bin_spot = bin_data["spot"]
            bin_perp = bin_data["perp"]
            bin_price = bin_data["price"]

            bybit_cvd = self.bybit.get_cvd()
            bybit_price = self.bybit.get_price()

            okx_cvd = self.okx.get_cvd()
            okx_price = self.okx.get_price()

            # Signal Logic
            signal = "📊 No clear bias"
            if cb_cvd > 0 and bin_spot > 0 and bin_perp < 0:
                signal = "✅ Spot-led move — real demand (Coinbase & Binance Spot rising)"
            elif bin_perp > 0 and cb_cvd < 0 and bin_spot <= 0:
                signal = "🚨 Perp-led pump — potential trap (Spot not participating)"
            elif bybit_cvd > 0 and bin_perp < 0:
                signal = "⚠️ Bybit retail buying while Binance is fading — watch for fakeout"
            elif okx_cvd < 0 and bin_perp > 0:
                signal = "🟡 OKX futures selling while Binance perps buying — Asia dump risk"
            elif cb_cvd > 0 and bin_spot < 0:
                signal = "🟣 US Spot buying (Coinbase) while Binance Spot is weak — divergence"

            # Display Output
            print("\n==================== SPOT vs PERP REPORT ====================")
            print(f"🟩 Coinbase Spot CVD: {cb_cvd} | Price: {cb_price}")
            print(f"🟦 Binance Spot CVD: {bin_spot}")
            print(f"🟥 Binance Perp CVD: {bin_perp} | Price: {bin_price}")
            print(f"🟧 Bybit Perp CVD: {bybit_cvd} | Price: {bybit_price}")
            print(f"🟪 OKX Futures CVD: {okx_cvd} | Price: {okx_price}")
            print(f"\n🧠 Signal: {signal}")
            print("=============================================================")

            await asyncio.sleep(5)


if __name__ == "__main__":
    engine = SpotVsPerpEngine()
    asyncio.run(engine.run())
