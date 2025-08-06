import json
import os
import time
import uuid
from openai import OpenAI

TRAP_LOG_FILE = "trap_log.json"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt_commentary(snapshot):
    """
    Asks GPT to comment on the trap signal snapshot.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a professional BTC sniper trade analyst."},
                {"role": "user", "content": f"Analyze this trap:\n{snapshot}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[X] GPT trap commentary failed:", e)
        return "GPT unavailable"

def log_trap_signal(snapshot):
    """
    Logs new trap signal with GPT commentary into local JSON file.
    """
    snapshot["timestamp"] = time.time()
    snapshot["uuid"] = str(uuid.uuid4())
    snapshot["gpt_comment"] = get_gpt_commentary(snapshot)

    try:
        if os.path.exists(TRAP_LOG_FILE):
            with open(TRAP_LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(snapshot)

        with open(TRAP_LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"🪤 Trap logged: {snapshot['signal']} at {snapshot['price']}")
        print(f"🧠 GPT says: {snapshot['gpt_comment']}")
    except Exception as e:
        print("[X] Failed to write trap log:", e)


def resolve_trap_outcome(current_price):
    """
    Adds 'exit_price' and win/loss result to each trap without outcome.
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
                entry = trap.get("price")
                trap["exit_price"] = current_price
                trap["exit_time"] = time.time()

                if direction == "LONG":
                    trap["outcome"] = "win" if current_price > entry else "loss"
                elif direction == "SHORT":
                    trap["outcome"] = "win" if current_price < entry else "loss"
                else:
                    trap["outcome"] = "unknown"

                updated = True

        if updated:
            with open(TRAP_LOG_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print("📈 Trap outcomes resolved and saved.")

    except Exception as e:
        print("[X] Trap outcome resolution failed:", e)
