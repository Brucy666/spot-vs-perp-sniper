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
from scoring.scorer_reversal import score_reversal_confluence

load_dotenv()

class ReversalVsTrendEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()

        self.memory = MultiTFMemory()
        self.alert_dispatcher = SpotPerpAlertDispatcher(cooldown_seconds=1800)

        self.last_signal_time = 0
        self.last_signal_hash = ""
        self.cooldown_seconds = 1800

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

                spot_price = bin_price or cb_price or 0

                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_reversal_confluence(deltas)
                confidence = scored["score"]
                label = scored["label"]

                signal = f"Brucy Bonus💥 REVERSAL BIAS | Confidence {confidence}/10 → {label}"

                print("\n==================== REVERSAL CHECK ====================")
                print(f"🟩 Coinbase Spot CVD: {cb_cvd} | Price: {cb_price}")
                print(f"🟦 Binance Spot CVD: {bin_spot}")
                print(f"🟥 Binance Perp CVD: {bin_perp} | Price: {bin_price}")
                print(f"🟧 Bybit Perp CVD: {bybit_cvd}")
                print(f"🟪 OKX Futures CVD: {okx_cvd}")
                print(f"\n🧠 Signal: {signal}")
                for tf in ["1m", "5m", "15m", "1h"]:
                    d = deltas.get(tf)
                    if d:
                        print(f"🕒 {tf} CVD Δ → CB: {d['cb_cvd']}% | Spot: {d['bin_spot']}% | Perp: {d['bin_perp']}%")
                print(f"💡 Confidence Score: {confidence}/10 → {label.upper()}")
                print("=======================================================")

                snapshot = {
                    "exchange": "multi",
                    "spot_cvd": bin_spot,
                    "perp_cvd": bin_perp,
                    "price": spot_price,
                    "signal": signal
                }

                log_snapshot(snapshot)

                now = time.time()
                sig_key = f"{signal}-{bin_spot}-{cb_cvd}-{bin_perp}"
                sig_hash = hashlib.sha256(sig_key.encode()).hexdigest()

                if sig_hash != self.last_signal_hash and (now - self.last_signal_time > self.cooldown_seconds):
                    self.last_signal_time = now
                    self.last_signal_hash = sig_hash

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

            except Exception as e:
                print(f"[ERROR] Reversal Engine Error: {e}")

            await asyncio.sleep(10)


if __name__ == "__main__":
    engine = ReversalVsTrendEngine()
    asyncio.run(engine.run())
