# sniper_console_status.py

import asyncio
import os
from dotenv import load_dotenv
from utils.multi_tf_memory import MultiTFMemory
from scorer_sniper import score_spot_perp_confluence_sniper
from scorer_swing import score_swing_tf
from scorer_reversal import score_reversal_trap
from utils.discord_alert import send_discord_alert

load_dotenv()

memory = MultiTFMemory()

async def update_console_status():
    while True:
        deltas = memory.get_all_deltas()

        sniper_score = score_spot_perp_confluence_sniper({k: deltas[k] for k in ["1m", "3m", "5m"] if k in deltas})
        swing_score = score_swing_tf({k: deltas[k] for k in ["15m", "30m", "1h", "4h"] if k in deltas})
        reversal_score = score_reversal_trap({k: deltas[k] for k in ["1h", "4h", "8h", "12h", "1d"] if k in deltas})

        def format_delta(tf):
            if tf not in deltas:
                return "(waiting)"
            d = deltas[tf]
            return f"CB `{d['cb_cvd']}%` | Spot `{d['bin_spot']}%` | Perp `{d['bin_perp']}%`"

        message = (
            "**🧠 Brucy AI System Console**\n"
            f"🔫 Sniper: `{sniper_score['label']}` | {sniper_score['score']}/10 → {format_delta('3m')}\n"
            f"📈 Swing: `{swing_score['label']}` | {swing_score['score']}/10 → {format_delta('30m')}\n"
            f"🧨 Reversal: `{reversal_score['label']}` | {reversal_score['score']}/10 → {format_delta('1h')}\n"
        )

        await send_discord_alert(message)
        await asyncio.sleep(300)  # every 5 minutes

if __name__ == "__main__":
    asyncio.run(update_console_status())
