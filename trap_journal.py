# trap_journal.py
# Logs sniper signals and outcomes for reinforcement learning / feedback loop

import os
import json
from datetime import datetime

TRAP_JOURNAL_FILE = "data/sniper_trap_log.json"

# Ensure folder exists
os.makedirs(os.path.dirname(TRAP_JOURNAL_FILE), exist_ok=True)

def load_trap_journal():
    if os.path.exists(TRAP_JOURNAL_FILE):
        with open(TRAP_JOURNAL_FILE, "r") as f:
            return json.load(f)
    return []

def save_trap_journal(data):
    with open(TRAP_JOURNAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_trap_signal(snapshot):
    """
    Save sniper signal snapshot:
    {
        'timestamp': ISO,
        'direction': LONG / SHORT,
        'confidence': float,
        'label': spot_dominant / perp_dominant / neutral,
        'price': float,
        'cb_cvd': float,
        'bin_spot': float,
        'bin_perp': float
    }
    """
    journal = load_trap_journal()
    snapshot["timestamp"] = datetime.utcnow().isoformat()
    snapshot["status"] = "open"  # marked until resolved
    journal.append(snapshot)
    save_trap_journal(journal)
    print("[+] Sniper trap logged to journal.")

def resolve_trap_outcome(price_now: float, threshold=0.0025):
    """
    Check journal for unresolved trades and mark outcomes.
    A price move of >= 0.25% is used as resolution.
    """
    journal = load_trap_journal()
    updated = False

    for trap in journal:
        if trap.get("status") != "open":
            continue

        entry_price = trap["price"]
        direction = trap["direction"]

        if direction == "LONG" and price_now >= entry_price * (1 + threshold):
            trap["status"] = "win"
        elif direction == "SHORT" and price_now <= entry_price * (1 - threshold):
            trap["status"] = "win"
        elif abs(price_now - entry_price) / entry_price >= threshold:
            trap["status"] = "loss"

        if trap["status"] != "open":
            trap["resolved_at"] = datetime.utcnow().isoformat()
            trap["exit_price"] = price_now
            updated = True

    if updated:
        save_trap_journal(journal)
        print("[~] Trap journal updated with outcome(s).")

if __name__ == "__main__":
    # Example: mark outcomes manually for current BTC price
    resolve_trap_outcome(price_now=11550.00)
