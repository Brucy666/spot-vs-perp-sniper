# reversal_vs_trend_engine.py

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

from scorer_reversal import score_reversal_confluence
from utils.volume_fetcher import fetch_all_volume
from utils.ai_volume_scoring import score_volume_bias

load_dotenv()


class ReversalVsTrendEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

        self.memory = MultiTFMemory()
        self.alert_dispatcher = SpotPerpAlertDispatcher(cooldown_seconds=900)

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
                    print("[REVERSAL ERROR] No valid spot price found, skipping...")
                    await asyncio.sleep(15)
                    continue

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_reversal_confluence(deltas)
                cvd_score = scored["score"]
                label = scored["label"]

                volume_data = fetch_all_volume()
                volume_score, volume_label = score_volume_bias(volume_data)

                final_score = round((cvd_score * 0.7) + (volume_score * 0.3), 2)

                print("\n==================== REVERSAL BIAS REPORT ====================")
                for tf in ["5m", "15m", "30m"]:
                    d = deltas.get(tf)
                    if d:
                        print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"🔄 Reversal Bias: {label.upper()} | CVD: {cvd_score}/10 | Volume: {volume_score}/10 | Final: {final_score}/10")
                print("🔊 Volume Snapshot:", volume_data)
                print("==============================================================")

                core_tf = deltas.get("15m")
                if not core_tf:
                    await asyncio.sleep(15)
                    continue

                now = time.time()
                sig_key = f"{label}-{final_score}-{int(spot_price)}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                if sig_hash != self.last_signal_hash and (now - self.last_signal_time > self.alert_dispatcher.cooldown_seconds):
                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

                    signal_text = f"Brucy Bonus💥 REVERSAL BIAS | Confidence {final_score}/10 → {label}"

                    log_sniper_alert({
                        "signal": signal_text,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": final_score,
                        "label": label,
                        "cb_cvd": core_tf["cb_cvd"],
                        "bin_spot": core_tf["bin_spot"],
                        "bin_perp": core_tf["bin_perp"],
                        "price": spot_price
                    })

                    await self.alert_dispatcher.maybe_alert(
                        signal_text=signal_text,
                        confidence=final_score,
                        label=label,
                        deltas=core_tf,
                        cvd_score=cvd_score,
                        volume_score=volume_score
                    )

            except Exception as e:
                print(f"[ERROR] Reversal Engine Error: {e}")

            await asyncio.sleep(15)


if __name__ == "__main__":
    engine = ReversalVsTrendEngine()
    asyncio.run(engine.run())
