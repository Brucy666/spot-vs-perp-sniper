import time
import hashlib
from utils.discord_alert import send_discord_alert

class SpotPerpAlertDispatcher:
    def __init__(self, cooldown_seconds=900):
        self.last_signal_time = 0
        self.last_signal_hash = ""
        self.cooldown_seconds = cooldown_seconds

    async def maybe_alert(self, signal, confidence, label, deltas, mode="sniper"):
        now = time.time()
        signal_key = f"{signal}-{confidence}-{label}-{mode}"
        signal_hash = hashlib.sha256(signal_key.encode()).hexdigest()

        is_dominant = label in ["spot_dominant", "perp_dominant"]
        is_strong = confidence >= 6
        is_cooldown_ok = now - self.last_signal_time > self.cooldown_seconds
        is_new = signal_hash != self.last_signal_hash

        if is_dominant and is_strong and is_cooldown_ok and is_new:
            direction = "🟢 LONG" if label == "spot_dominant" else "🔴 SHORT"

            tf_label = {
                "sniper": "3m",
                "swing": "15m",
                "reversal": "1h"
            }.get(mode, "15m")

            alert = (
                f"**Brucy Bonus💥**\n"
                f"{signal}\n\n"
                f"🧠 Confidence: `{confidence}/10` → `{label}`\n"
                f"🎯 Suggested Trade: **{direction}**\n"
                f"📊 {tf_label} CVD Δ:\n"
                f"   • Coinbase: `{deltas['cb_cvd']}%`\n"
                f"   • Binance Spot: `{deltas['bin_spot']}%`\n"
                f"   • Binance Perp: `{deltas['bin_perp']}%`\n"
            )

            await send_discord_alert(alert)
            self.last_signal_time = now
            self.last_signal_hash = signal_hash
