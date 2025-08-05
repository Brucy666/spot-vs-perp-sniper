# swing_vs_perp_engine.py (wired with scorer_swing.py)

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
from scorer_swing import score_swing_tf

load_dotenv()

class SwingVsPerpEngine:
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
        self.cooldown = 1800  # 30 minutes

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

                # Require alignment of 15m, 1h, 4h
                required_tfs = ["15m", "1h", "4h"]
                if not all(tf in deltas for tf in required_tfs):
                    await asyncio.sleep(30)
                    continue

                scored = score_swing_tf(deltas)
                confidence = scored["score"]
                label = scored["label"]
                signal = f"SWING ALIGNMENT | Confidence {confidence}/10 → {label.upper()}"

                print("\n==================== SWING BIAS REPORT ====================")
                for tf in required_tfs:
                    d = deltas[tf]
                    print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"💡 Swing Bias: {label.upper()} | Confidence: {confidence}/10")
                print("===========================================================")

                now = time.time()
                sig_key = f"{signal}-{label}-{int(spot_price)}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                if label != "neutral" and confidence >= 6 and (now - self.last_signal_time > self.cooldown) and sig_hash != self.last_signal_hash:
                    log_sniper_alert({
                        "signal": signal,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": confidence,
                        "label": label,
                        "cb_cvd": deltas["15m"]["cb_cvd"],
                        "bin_spot": deltas["15m"]["bin_spot"],
                        "bin_perp": deltas["15m"]["bin_perp"],
                        "price": spot_price
                    })

                    await self.alert_dispatcher.maybe_alert(
                        signal, confidence, label, deltas["15m"]
                    )

                    if self.executor.should_execute(confidence, label):
                        self.executor.execute(signal, confidence, spot_price, label)

                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

            except Exception as e:
                print(f"[ERROR] Swing Engine Error: {e}")

            await asyncio.sleep(30)


if __name__ == "__main__":
    engine = SwingVsPerpEngine()
    asyncio.run(engine.run())
