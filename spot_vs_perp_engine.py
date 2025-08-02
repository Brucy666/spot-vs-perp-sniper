# spot_vs_perp_engine.py

import asyncio
import os
import time
import hashlib
from dotenv import load_dotenv

from feeds.coinbase_feed import CoinbaseSpotCVD
from feeds.binance_feed import BinanceCVDTracker
from feeds.bybit_feed import BybitCVDTracker
from feeds.okx_feed import OKXCVDTracker

from utils.discord_alert import send_discord_alert
from utils.memory_logger import log_snapshot
from utils.cvd_snapshot_writer import write_snapshot_to_supabase
from utils.spot_perp_memory_tracker import SpotPerpMemoryTracker
from utils.spot_perp_scorer import score_spot_perp_confluence
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher

load_dotenv()

class SpotVsPerpEngine:
    def __init__(self):
        self.coinbase = CoinbaseSpotCVD()
        self.binance = BinanceCVDTracker()
        self.bybit = BybitCVDTracker()
        self.okx = OKXCVDTracker()
        self.memory_tracker = SpotPerpMemoryTracker()
        self.alert_dispatcher = SpotPerpAlertDispatcher()

        self.last_signal = None
        self.last_signal_time = 0
        self.last_signal_hash = ""
        self.signal_cooldown_seconds = 900  # 15 minutes

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
            # === Collect Live CVD ===
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

            # === Update Memory & Score ===
            self.memory_tracker.update(cb_cvd, bin_spot, bin_perp)
            deltas = self.memory_tracker.get_rolling_deltas()
            scored = score_spot_perp_confluence(deltas["15m"])
            confidence = scored["score"]
            bias_label = scored["label"]

            # === Signal Detection ===
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

            # === Terminal Output ===
            print("\n==================== SPOT vs PERP REPORT ====================")
            print(f"🟩 Coinbase Spot CVD: {cb_cvd} | Price: {cb_price}")
            print(f"🟦 Binance Spot CVD: {bin_spot}")
            print(f"🟥 Binance Perp CVD: {bin_perp} | Price: {bin_price}")
            print(f"🟧 Bybit Perp CVD: {bybit_cvd} | Price: {bybit_price}")
            print(f"🟪 OKX Futures CVD: {okx_cvd} | Price: {okx_price}")
            print(f"\n🧠 Signal: {signal}")
            print(f"📉 15m CVD Δ → CB: {deltas['15m']['cb_cvd']}% | Spot: {deltas['15m']['bin_spot']}% | Perp: {deltas['15m']['bin_perp']}%")
            print(f"💡 Confidence Score: {confidence}/10 → {bias_label.upper()}")
            print("=============================================================")

            # === Snapshot Construction ===
            snapshot = {
                "exchange": "multi",
                "spot_cvd": bin_spot,
                "perp_cvd": bin_perp,
                "price": bin_price or cb_price or bybit_price or okx_price,
                "signal": signal
            }

            log_snapshot(snapshot)

            # === Optional: Base Alert Logic (for historical logging/Supabase)
            now = time.time()
            signal_signature = f"{signal}-{bin_spot}-{cb_cvd}-{bin_perp}"
            signal_hash = hashlib.sha256(signal_signature.encode()).hexdigest()

            is_unique = signal_hash != self.last_signal_hash
            is_cooldown_passed = now - self.last_signal_time > self.signal_cooldown_seconds
            is_meaningful = any(k in signal for k in ["✅", "🚨", "⚠️", "🟡", "🟣"])

            if is_unique and is_cooldown_passed and is_meaningful:
                write_snapshot_to_supabase(snapshot)
                self.last_signal = signal
                self.last_signal_time = now
                self.last_signal_hash = signal_hash

            # === High-Confluence Alert Dispatcher ===
            await self.alert_dispatcher.maybe_alert(
                signal=signal,
                confidence=confidence,
                label=bias_label,
                deltas=deltas["15m"]
            )

            await asyncio.sleep(5)


if __name__ == "__main__":
    engine = SpotVsPerpEngine()
    asyncio.run(engine.run())
