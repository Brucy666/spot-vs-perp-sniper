# swing_vs_perp_engine.py

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
                # === Collect Feed Data ===
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

                # === Update Memory + Score ===
                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_spot_perp_confluence_multi(deltas)

                confidence = scored["score"]
                bias_label = scored["label"]

                signal_text = f"SWING BIAS | Confidence {confidence}/10 → {bias_label.upper()}"

                # === Print Snapshot to Terminal ===
                print("\n==================== SWING vs PERP SNAPSHOT ====================")
                for tf in ["15m", "1h", "4h"]:
                    if tf in deltas:
                        d = deltas[tf]
                        print(f"🕒 {tf.upper()} Δ → CB: {d['cb_cvd']}% | SPOT: {d['bin_spot']}% | PERP: {d['bin_perp']}%")
                print(f"💡 Final Score: {confidence}/10 → {bias_label}")
                print("===============================================================\n")

                # === Confirm Multi-TF Alignment ===
                if all(tf in deltas for tf in ["15m", "1h", "4h"]) and confidence >= 6 and bias_label != "neutral":
                    signal_key = f"{bias_label}-{confidence}-{int(spot_price)}"
                    signal_hash = hashlib.sha256(signal_key.encode()).hexdigest()

                    if signal_hash != self.last_signal_hash and (now - self.last_signal_time > self.cooldown_seconds):
                        direction = "LONG" if bias_label == "spot_dominant" else "SHORT"

                        alert_data = {
                            "signal": signal_text,
                            "direction": direction,
                            "confidence": confidence,
                            "label": bias_label,
                            "cb_cvd": deltas["15m"]["cb_cvd"],
                            "bin_spot": deltas["15m"]["bin_spot"],
                            "bin_perp": deltas["15m"]["bin_perp"],
                            "price": spot_price
                        }

                        log_sniper_alert(alert_data)
                        await self.alert_dispatcher.maybe_alert(
                            signal_text,
                            confidence,
                            bias_label,
                            deltas["15m"]
                        )

                        if self.executor.should_execute(confidence, bias_label):
                            self.executor.execute(signal_text, confidence, spot_price, bias_label)

                        self.last_signal_hash = signal_hash
                        self.last_signal_time = now

            except Exception as e:
                print(f"[ERROR] Swing Monitor Failed: {e}")

            await asyncio.sleep(30)


if __name__ == "__main__":
    engine = SwingVsPerpEngine()
    asyncio.run(engine.run())
