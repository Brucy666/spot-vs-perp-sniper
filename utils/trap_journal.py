import json
import os
import time
import openai

TRAP_LOG_FILE = "trap_log.json"

openai.api_key = os.getenv("OPENAI_API_KEY")


def log_trap_signal(snapshot):
    """
    Logs trap signal locally and adds GPT commentary.
    """
    snapshot["timestamp"] = time.time()

    try:
        # Optional GPT tag
        snapshot["gpt_comment"] = get_gpt_comment(snapshot)

        # Load existing file
        if os.path.exists(TRAP_LOG_FILE):
            with open(TRAP_LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(snapshot)

        with open(TRAP_LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"[🪤] Trap logged: {snapshot['signal']} at {snapshot['price']}")
        print(f"[🤖] GPT says: {snapshot['gpt_comment']}")

    except Exception as e:
        print("[X] Failed to write trap log:", e)


def resolve_trap_outcome(current_price):
    """
    Updates all open traps with exit price and outcome result (win/loss).
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


def get_gpt_comment(trap):
    """
    Uses OpenAI GPT to add human-style trap commentary.
    """
    try:
        prompt = (
            f"You're a crypto sniper AI assistant. Given this trap setup:\n"
            f"- Signal: {trap['signal']}\n"
            f"- Direction: {trap['direction']}\n"
            f"- Confidence: {trap.get('confidence', '?')}/10\n"
            f"- CB CVD: {trap.get('cb_cvd', '?')}%\n"
            f"- Spot: {trap.get('bin_spot', '?')}%\n"
            f"- Perp: {trap.get('bin_perp', '?')}%\n"
            f"- Bias: {trap.get('label', '?')}\n"
            f"→ Give a 1-line summary assessing this trap quality."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("[X] GPT trap commentary failed:", e)
        return "GPT unavailable"
