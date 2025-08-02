# utils/spot_perp_alert_dispatcher.py

import time
import hashlib
from utils.discord_alert import send_discord_alert

class SpotPerpAlertDispatcher:
    def __init__(self):
        self.last_signal_time = 0
        self.last_signal_hash = ""
        self.cooldown_seconds = 900  # 15 minutes

    async def maybe_alert(self, signal, confidence, label, deltas):
        now = time.time()
        signal_key = f"{signal}-{confidence}-{label}"
        signal_hash = hashlib.sha256(signal_key.encode()).hexdigest()

        is_dominant = label in ["spot_dominant", "perp_dominant"]
        is_strong = confidence >= 7
        is_cooldown_ok = now - self.last_signal_time > self.cooldown_seconds
        is_new = signal_hash != self.last_signal_hash

        if is_dominant and is_strong and is_cooldown_ok and is_new:
            alert = (
                f"🚨 **HIGH-CONFLUENCE SNIPER SIGNAL**\n"
                f"{signal}\n\n"
                f"🧠 Confidence Score: `{confidence}/10` → `{label}`\n"
                f"📊 15m CVD Δ:\n"
                f"   • Coinbase: {deltas['cb_cvd']}%\n"
                f"   • Binance Spot: {deltas['bin_spot']}%\n"
                f"   • Binance Perp: {deltas['bin_perp']}%\n"
            )
            await send_discord_alert(alert)
            self.last_signal_time = now
            self.last_signal_hash = signal_hash
