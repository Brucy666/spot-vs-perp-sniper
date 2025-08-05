# reversal_vs_trend_engine.py (updated with mode="reversal" for dispatcher)

import asyncio
import os
import time
import hashlib
from dotenv import load_dotenv

from feeds.coinbase_feed import CoinbaseSpotCVD
from feeds.binance_feed import BinanceCVDTracker
from feeds.bybit_feed import BybitCVDTracker
from feeds.okx_feed import OKXCVDTracker

from utils.memory_logger import log_snapshot
from utils.multi_tf_memory import MultiTFMemory
from utils.sniper_alert_logger import log_sniper_alert
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher
from sniper_executor import SniperExecutor
from scorer_reversal import score_reversal_trap

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
        self.cooldown_seconds = 300

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

                spot_price = bin_price or cb_price

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()

                scored = score_reversal_trap(deltas)
                confidence = scored["score"]
                label = scored["label"]
                signal = f"REVERSAL TRAP | Confidence {confidence}/10 → {label.upper()}"

                print("\n==================== REVERSAL TRAP REPORT ====================")
                for tf in ["1h", "4h", "8h", "12h", "1d"]:
                    d = deltas.get(tf)
                    if d:
                        print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"💡 Reversal Signal: {label.upper()} | Confidence: {confidence}/10")
                print("===============================================================")

                now = time.time()
                sig_key = f"{signal}-{label}-{int(spot_price)}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                if label != "neutral" and confidence >= 6 and sig_hash != self.last_signal_hash and (now - self.last_signal_time > self.cooldown_seconds):
                    log_sniper_alert({
                        "signal": signal,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": confidence,
                        "label": label,
                        "cb_cvd": deltas["1h"]["cb_cvd"],
                        "bin_spot": deltas["1h"]["bin_spot"],
                        "bin_perp": deltas["1h"]["bin_perp"],
                        "price": spot_price
                    })

                    await self.alert_dispatcher.maybe_alert(
                        signal, confidence, label, deltas["1h"], mode="reversal"
                    )

                    if self.executor.should_execute(confidence, label):
                        self.executor.execute(signal, confidence, spot_price, label)

                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

            except Exception as e:
                print(f"[ERROR] Reversal Engine Error: {e}")

            await asyncio.sleep(10)


if __name__ == "__main__":
    engine = ReversalVsTrendEngine()
    asyncio.run(engine.run())
