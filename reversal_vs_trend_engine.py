# reversal_vs_trend_engine.py

import asyncio
import time
import hashlib
from dotenv import load_dotenv

from feeds.coinbase_feed import CoinbaseSpotCVD
from feeds.binance_feed import BinanceCVDTracker
from feeds.bybit_feed import BybitCVDTracker
from feeds.okx_feed import OKXCVDTracker

from utils.memory_logger import log_snapshot
from utils.multi_tf_memory import MultiTFMemory
from utils.spot_perp_scorer import score_spot_perp_confluence_multi
from utils.sniper_alert_logger import log_sniper_alert
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher
from sniper_executor import SniperExecutor

load_dotenv()

class ReversalVsTrendEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

        self.memory = MultiTFMemory()
        self.alert_dispatcher = SpotPerpAlertDispatcher()
        self.executor = SniperExecutor()

        self.last_signal_time = 0
        self.last_signal_hash = ""
        self.cooldown_seconds = 300  # 5 min for reversals

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
            try:
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

                spot_price = bin_price or cb_price or bybit_price or okx_price
                now = time.time()

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_spot_perp_confluence_multi(deltas)

                short_tf = deltas.get("1m") or deltas.get("3m")
                long_tf = deltas.get("15m") or deltas.get("1h")

                if not short_tf or not long_tf:
                    await asyncio.sleep(10)
                    continue

                direction = None
                reason = ""

                # Long trap? Short TF bearish, but macro bullish
                if scored["label"] == "spot_dominant" and short_tf["bin_perp"] > 0 and short_tf["cb_cvd"] < 0:
                    direction = "LONG"
                    reason = "🐍 Spot macro strong, but perps shorting into it (trap long setup)"

                # Short trap? Short TF bullish, but macro bearish
                elif scored["label"] == "perp_dominant" and short_tf["bin_spot"] > 0 and short_tf["cb_cvd"] > 0:
                    direction = "SHORT"
                    reason = "🧨 Macro weak, but short-term buyers piling in (short trap)"

                if direction and scored["score"] >= 6:
                    key = f"{direction}-{scored['score']}-{int(spot_price)}"
                    signal_hash = hashlib.sha256(key.encode()).hexdigest()

                    if signal_hash != self.last_signal_hash and (now - self.last_signal_time > self.cooldown_seconds):
                        signal_text = f"REVERSAL TRAP | {reason}"

                        log_sniper_alert({
                            "signal": signal_text,
                            "direction": direction,
                            "confidence": scored["score"],
                            "label": scored["label"],
                            "cb_cvd": short_tf["cb_cvd"],
                            "bin_spot": short_tf["bin_spot"],
                            "bin_perp": short_tf["bin_perp"],
                            "price": spot_price
                        })

                        await self.alert_dispatcher.maybe_alert(
                            signal_text,
                            scored["score"],
                            scored["label"],
                            short_tf
                        )

                        if self.executor.should_execute(scored["score"], scored["label"]):
                            self.executor.execute(signal_text, scored["score"], spot_price, scored["label"])

                        self.last_signal_time = now
                        self.last_signal_hash = signal_hash

            except Exception as e:
                print(f"[ERROR] Reversal Engine Error: {e}")

            await asyncio.sleep(10)


if __name__ == "__main__":
    engine = ReversalVsTrendEngine()
    asyncio.run(engine.run())
