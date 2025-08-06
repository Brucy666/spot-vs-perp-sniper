# spot_vs_perp_engine.py (AI-enhanced, volume-patched, typo-fixed)

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
from utils.global_volume_fetcher import fetch_all_volume
from utils.ai_volume_scoring import score_volume_bias
from scorer_sniper import score_sniper_confluence

load_dotenv()


class SpotVsPerpEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

        self.memory = MultiTFMemory()
        self.alert_dispatcher = SpotPerpAlertDispatcher(cooldown_seconds=300)

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

                bybit_cvd = self.bybit.get_cvd()
                okx_cvd = self.okx.get_cvd()

                spot_price = bin_price or cb_price
                if not spot_price:
                    print("[SNIPER ERROR] No valid price found, skipping...")
                    await asyncio.sleep(5)
                    continue

                # CVD-based memory and scoring
                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_sniper_confluence(deltas)
                confidence = scored["score"]
                label = scored["label"]

                # Volume snapshot and scoring
                volume_data = fetch_all_volume()
                vol_score, vol_label = score_volume_bias(volume_data)

                # Console output
                print("\n==================== SPOT SNIPER REPORT ====================")
                print(f"🟩 Coinbase Spot CVD: {cb_cvd} | Price: {cb_price}")
                print(f"🟦 Binance Spot CVD: {bin_spot}")
                print(f"🟥 Binance Perp CVD: {bin_perp} | Price: {bin_price}")
                print(f"🟧 Bybit Perp CVD: {bybit_cvd}")
                print(f"🟪 OKX Futures CVD: {okx_cvd}")
                for tf in ["1m", "3m", "5m"]:
                    d = deltas.get(tf)
                    if d:
                        print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"🔊 Volume Bias: {vol_label.upper()} | Score: {vol_score}/10")
                print(f"💡 Confidence Score: {confidence}/10 → {label.upper()}")
                print("===========================================================")

                snapshot = {
                    "exchange": "multi",
                    "spot_cvd": bin_spot,
                    "perp_cvd": bin_perp,
                    "price": spot_price,
                    "signal": f"{label.upper()}"
                }

                now = time.time()
                sig_key = f"{label}-{confidence}-{int(spot_price)}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                if sig_hash != self.last_signal_hash and (now - self.last_signal_time > 300):
                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

                    signal_text = (
                        f"Brucy Bonus💥 SPOT SIGNAL | Confidence {confidence}/10 → {label} | "
                        f"Volume {vol_score}/10 → {vol_label}"
                    )

                    log_sniper_alert({
                        "signal": signal_text,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": confidence,
                        "label": label,
                        "cb_cvd": deltas["3m"]["cb_cvd"],
                        "bin_spot": deltas["3m"]["bin_spot"],
                        "bin_perp": deltas["3m"]["bin_perp"],
                        "price": spot_price
                    })

                    await self.alert_dispatcher.maybe_alert(
                        signal_text=signal_text,
                        confidence=confidence,
                        label=label,
                        deltas=deltas["3m"]
                    )

            except Exception as e:
                print(f"[ERROR] Spot Sniper Engine Error: {e}")

            await asyncio.sleep(5)


if __name__ == "__main__":
    engine = SpotVsPerpEngine()
    asyncio.run(engine.run())
