# trap_journal.py (with resolve_trap_outcome logic)

import os
import json
from datetime import datetime

TRAP_JOURNAL_FILE = "data/sniper_trap_log.json"

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
    snapshot["timestamp"] = datetime.utcnow().isoformat()
    snapshot["status"] = "open"
    journal = load_trap_journal()
    journal.append(snapshot)
    save_trap_journal(journal)
    print("[+] Sniper trap logged to journal.")

def resolve_trap_outcome(price_now: float, threshold: float = 0.0025):
    """
    Marks open trades as win/loss based on move from entry price.
    threshold is percentage move (0.25% by default).
    """
    journal = load_trap_journal()
    updated = False

    for trap in journal:
        if trap.get("status") != "open":
            continue

        entry_price = trap.get("price")
        direction = trap.get("direction")

        if not entry_price or not direction:
            continue

        move_pct = abs(price_now - entry_price) / entry_price

        if direction == "LONG" and price_now >= entry_price * (1 + threshold):
            trap["status"] = "win"
        elif direction == "SHORT" and price_now <= entry_price * (1 - threshold):
            trap["status"] = "win"
        elif move_pct >= threshold:
            trap["status"] = "loss"

        if trap["status"] != "open":
            trap["resolved_at"] = datetime.utcnow().isoformat()
            trap["exit_price"] = price_now
            updated = True

    if updated:
        save_trap_journal(journal)
        print("[~] Trap journal updated with outcome(s).")

if __name__ == "__main__":
    # Example usage:
    current_price = 29500.00
    resolve_trap_outcome(price_now=current_price)            trap["exit_price"] = price_now
            updated = True

    if updated:
        save_trap_journal(journal)
        print("[~] Trap journal updated with outcome(s).")

if __name__ == "__main__":
    # Example: mark outcomes manually for current BTC price
    resolve_trap_outcome(price_now=11550.00)
