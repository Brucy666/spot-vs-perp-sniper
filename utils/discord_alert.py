import aiohttp
import os

# Fallback default
DEFAULT_WEBHOOK = os.getenv("DISCORD_WEBHOOK_SPOT_PERP")

# Optional webhooks for different bot modes
WEBHOOKS = {
    "sniper": os.getenv("DISCORD_WEBHOOK_SPOT_SNIPER", DEFAULT_WEBHOOK),
    "swing": os.getenv("DISCORD_WEBHOOK_SWING", DEFAULT_WEBHOOK),
    "reversal": os.getenv("DISCORD_WEBHOOK_REVERSAL", DEFAULT_WEBHOOK),
}


async def send_discord_alert(message: str, mode: str = "sniper"):
    """
    Sends a formatted alert message to the appropriate Discord channel based on mode.
    """
    webhook = WEBHOOKS.get(mode, DEFAULT_WEBHOOK)

    if not webhook:
        print(f"❌ No Discord webhook found for mode: {mode}")
        return

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"content": message}
            async with session.post(webhook, json=payload) as resp:
                if resp.status != 204:
                    print(f"❌ Discord webhook failed [{mode}] → Status: {resp.status}")
    except Exception as e:
        print(f"[X] Discord alert error [{mode}]:", e)
