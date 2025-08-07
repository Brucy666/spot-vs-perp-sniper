import time
import hashlib
from utils.discord_alert import send_discord_alert
from utils.trap_journal import get_gpt_commentary


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

        if not (is_dominant and is_strong and is_cooldown_ok and is_new):
            return  # Skip alert

        direction = "🟢 LONG" if label == "spot_dominant" else "🔴 SHORT"

        tf_label = {
            "sniper": "3m",
            "swing": "30m",
            "reversal": "1h"
        }.get(mode, "15m")

        # === GPT Commentary ===
        try:
            gpt_comment = await get_gpt_commentary({
                "signal": signal,
                "direction": direction,
                "confidence": confidence,
                "cb_cvd": deltas.get("cb_cvd", 0),
                "bin_spot": deltas.get("bin_spot", 0),
                "bin_perp": deltas.get("bin_perp", 0),
                "label": label
            })
        except Exception as e:
            gpt_comment = f"[GPT error: {e}]"

        # === Final Alert Message ===
        alert = (
            f"**Brucy Bonus💥**\n"
            f"{signal}\n\n"
            f"🧠 Confidence: `{confidence}/10` → `{label}`\n"
            f"🎯 Suggested Trade: **{direction}**\n"
            f"📊 {tf_label} CVD Δ:\n"
            f"   • Coinbase: `{deltas.get('cb_cvd', '?')}%`\n"
            f"   • Binance Spot: `{deltas.get('bin_spot', '?')}%`\n"
            f"   • Binance Perp: `{deltas.get('bin_perp', '?')}%`\n\n"
            f"🤖 GPT says: _{gpt_comment}_"
        )

        await send_discord_alert(alert, mode=mode)
        self.last_signal_time = now
        self.last_signal_hash = signal_hash
