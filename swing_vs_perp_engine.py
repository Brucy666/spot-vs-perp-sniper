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
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher
from utils.sniper_alert_logger import log_sniper_alert
from volume_fetcher import fetch_all_volume
from scorer_swing import score_swing_confluence

load_dotenv()

class SwingVsPerpEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

        self.memory = MultiTFMemory()
        self.alert_dispatcher = SpotPerpAlertDispatcher(cooldown_seconds=1800)

        self.last_signal_time = 0
        self.last_signal_hash = ""

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

                bybit_price = self.bybit.get_price()
                okx_price = self.okx.get_price()

                spot_price = bin_price or cb_price or bybit_price or okx_price
                if not spot_price:
                    print("[SWING ERROR] No valid spot price found, skipping...")
                    await asyncio.sleep(30)
                    continue

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_swing_confluence(deltas)
                confidence = scored["score"]
                label = scored["label"]

                # 🔊 Fetch and print live volume
                volume_data = fetch_all_volume()
                
                print("\n==================== SWING BIAS REPORT ====================")
                for tf in ["15m", "30m", "1h", "4h"]:
                    d = deltas.get(tf)
                    if d:
                        print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"💡 Swing Bias: {label.upper()} | Confidence: {confidence}/10")
                print(f"🔊 Volume Snapshot: {volume_data}")
                print("==========================================================")

                core_tf = deltas.get("30m")
                if not core_tf:
                    await asyncio.sleep(30)
                    continue

                now = time.time()
                sig_key = f"{label}-{confidence}-{int(spot_price)}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                is_unique = sig_hash != self.last_signal_hash
                is_cooldown_ok = (now - self.last_signal_time) > self.alert_dispatcher.cooldown_seconds

                if is_unique and is_cooldown_ok:
                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

                    signal_text = f"Brucy Bonus💥 SWING BIAS | Confidence {confidence}/10 → {label}"

                    log_sniper_alert({
                        "signal": signal_text,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": confidence,
                        "label": label,
                        "cb_cvd": core_tf["cb_cvd"],
                        "bin_spot": core_tf["bin_spot"],
                        "bin_perp": core_tf["bin_perp"],
                        "price": spot_price
                    })

                    await self.alert_dispatcher.maybe_alert(
                        signal_text, confidence, label, core_tf
                    )

            except Exception as e:
                print(f"[ERROR] Swing Engine Error: {e}")

            await asyncio.sleep(30)


if __name__ == "__main__":
    engine = SwingVsPerpEngine()
    asyncio.run(engine.run())
