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

from utils.memory_logger import log_snapshot
from utils.multi_tf_memory import MultiTFMemory
from utils.spot_perp_scorer import score_spot_perp_confluence_multi
from utils.spot_perp_alert_dispatcher import SpotPerpAlertDispatcher
from utils.cvd_snapshot_writer import write_snapshot_to_supabase
from utils.sniper_alert_logger import log_sniper_alert
from sniper_executor import SniperExecutor

load_dotenv()

class SpotVsPerpEngine:
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
        self.signal_cooldown = 900  # 15m

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
                # === Collect
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

                # === Score and classify
                self.memory.update(cb_cvd, bin_spot, bin_perp)
                deltas = self.memory.get_all_deltas()
                scored = score_spot_perp_confluence_multi(deltas)
                confidence = scored["score"]
                label = scored["label"]

                # === Signal logic
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

                # === Console Output
                print("\n==================== SPOT vs PERP REPORT ====================")
                print(f"🟩 Coinbase Spot CVD: {cb_cvd} | Price: {cb_price}")
                print(f"🟦 Binance Spot CVD: {bin_spot}")
                print(f"🟥 Binance Perp CVD: {bin_perp} | Price: {bin_price}")
                print(f"🟧 Bybit Perp CVD: {bybit_cvd} | Price: {bybit_price}")
                print(f"🟪 OKX Futures CVD: {okx_cvd} | Price: {okx_price}")
                print(f"\n🧠 Signal: {signal}")
                for tf, vals in deltas.items():
                    print(f"🕒 {tf} CVD Δ → CB: {vals['cb_cvd']}% | Spot: {vals['bin_spot']}% | Perp: {vals['bin_perp']}%")
                print(f"💡 Confidence Score: {confidence}/10 → {label.upper()}")
                print("=============================================================")

                # === Logging
                snapshot = {
                    "exchange": "multi",
                    "spot_cvd": bin_spot,
                    "perp_cvd": bin_perp,
                    "price": bin_price or cb_price or bybit_price or okx_price,
                    "signal": signal
                }

                log_snapshot(snapshot)

                # === Supabase Snapshot
                now = time.time()
                signature = f"{signal}-{bin_spot}-{cb_cvd}-{bin_perp}"
                hash_ = hashlib.sha256(signature.encode()).hexdigest()

                is_unique = hash_ != self.last_signal_hash
                is_cooldown_ok = now - self.last_signal_time > self.signal_cooldown
                is_signal = any(t in signal for t in ["✅", "🚨", "⚠️", "🟡", "🟣"])

                if is_unique and is_cooldown_ok and is_signal:
                    write_snapshot_to_supabase(snapshot)
                    self.last_signal_time = now
                    self.last_signal_hash = hash_

                    # === Log sniper entry
                    log_sniper_alert({
                        "signal": signal,
                        "direction": "LONG" if label == "spot_dominant" else "SHORT",
                        "confidence": confidence,
                        "label": label,
                        "cb_cvd": deltas["15m"]["cb_cvd"],
                        "bin_spot": deltas["15m"]["bin_spot"],
                        "bin_perp": deltas["15m"]["bin_perp"],
                        "price": snapshot["price"]
                    })

                    # === Discord alert
                    await self.alert_dispatcher.maybe_alert(
                        signal, confidence, label, deltas["15m"]
                    )

                    # === Execution
                    if self.executor.should_execute(confidence, label):
                        self.executor.execute(signal, confidence, snapshot["price"], label)

            except Exception as e:
                print(f"[ERROR] Spot Monitor Failed: {e}")

            await asyncio.sleep(5)


if __name__ == "__main__":
    engine = SpotVsPerpEngine()
    asyncio.run(engine.run())
