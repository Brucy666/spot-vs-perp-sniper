import os
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def log_sniper_alert(alert):
    url = f"{SUPABASE_URL}/rest/v1/sniper_alerts"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "signal": alert["signal"],
        "direction": alert["direction"],
        "confidence_score": alert["confidence"],
        "bias_label": alert["label"],
        "cb_cvd": alert["cb_cvd"],
        "bin_spot": alert["bin_spot"],
        "bin_perp": alert["bin_perp"],
        "triggered_price": alert["price"]
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code not in [200, 201, 204]:
            print("[X] Supabase insert failed:", res.text)
        else:
            print("[✓] Sniper alert saved to Supabase.")
    except Exception as e:
        print("[X] Error logging alert:", e)
