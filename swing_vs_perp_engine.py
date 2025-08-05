# swing_vs_perp_engine.py

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
from utils.spot_perp_scorer import score_spot_perp_confluence_multi
from utils.sniper_alert_logger import log_sniper_alert
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher
from sniper_executor import SniperExecutor

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
        self.cooldown_seconds = 1800  # 30 minutes

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

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_spot_perp_confluence_multi(deltas)
                confidence = scored["score"]
                bias_label = scored["label"]

                spot_price = bin_price or cb_price or bybit_price or okx_price
                now = time.time()

                signal = f"SWING BIAS | Confidence {confidence}/10 → {bias_label}"

                # Only alert when 15m, 1h, and 4h all align
                if all(tf in deltas for tf in ["15m", "1h", "4h"]):
                    if bias_label != "neutral" and confidence >= 6:
                        key = f"{bias_label}-{confidence}-{int(spot_price)}"
                        hash_sig = hashlib.sha256(key.encode()).hexdigest()

                        if hash_sig != self.last_signal_hash and (now - self.last_signal_time > self.cooldown_seconds):
                            log_sniper_alert({
                                "signal": signal,
                                "direction": "LONG" if bias_label == "spot_dominant" else "SHORT",
                                "confidence": confidence,
                                "label": bias_label,
                                "cb_cvd": deltas["15m"]["cb_cvd"],
                                "bin_spot": deltas["15m"]["bin_spot"],
                                "bin_perp": deltas["15m"]["bin_perp"],
                                "price": spot_price
                            })

                            await self.alert_dispatcher.maybe_alert(
                                signal, confidence, bias_label, deltas["15m"]
                            )

                            self.last_signal_hash = hash_sig
                            self.last_signal_time = now

                            if self.executor.should_execute(confidence, bias_label):
                                self.executor.execute(signal, confidence, spot_price, bias_label)

            except Exception as e:
                print(f"[ERROR] Swing loop failed: {e}")

            await asyncio.sleep(30)


if __name__ == "__main__":
    engine = SwingVsPerpEngine()
    asyncio.run(engine.run())
