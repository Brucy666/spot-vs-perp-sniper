# trap_journal.py

import json
import os
import time

TRAP_LOG_FILE = "trap_log.json"

def log_trap_signal(snapshot):
    """
    Stores trap signal snapshot with timestamp into trap_log.json
    """
    snapshot["timestamp"] = time.time()
    try:
        if os.path.exists(TRAP_LOG_FILE):
            with open(TRAP_LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(snapshot)

        with open(TRAP_LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"[🪤] Trap logged: {snapshot['signal']} at {snapshot['price']}")

    except Exception as e:
        print("[X] Failed to write trap log:", e)


def resolve_trap_outcome(current_price):
    """
    Reads open traps and checks outcome based on exit price.
    Updates log with win/loss tags and outcome info.
    """
    try:
        if not os.path.exists(TRAP_LOG_FILE):
            return

        with open(TRAP_LOG_FILE, "r") as f:
            data = json.load(f)

        updated = False
        for trap in data:
            if "exit_price" not in trap:
                direction = trap.get("direction")
                entry_price = trap.get("price")

                trap["exit_price"] = current_price
                trap["exit_time"] = time.time()

                # Determine result
                if direction == "LONG":
                    trap["outcome"] = "win" if current_price > entry_price else "loss"
                elif direction == "SHORT":
                    trap["outcome"] = "win" if current_price < entry_price else "loss"
                else:
                    trap["outcome"] = "unknown"

                updated = True

        if updated:
            with open(TRAP_LOG_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print("[✓] Trap outcomes updated")

    except Exception as e:
        print("[X] Trap outcome resolution failed:", e)
