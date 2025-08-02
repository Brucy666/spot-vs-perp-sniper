# utils/spot_perp_scorer.py

def score_spot_perp_confluence_multi(deltas: dict):
    """
    Accepts deltas for 5m, 15m, and 1h, returns confidence score and bias label.
    """

    score = 0
    notes = []

    # === Timeframe Weights ===
    tf_weights = {
        "5m": 1.0,
        "15m": 1.5,
        "1h": 1.0
    }

    for tf, delta in deltas.items():
        weight = tf_weights.get(tf, 1.0)

        cb = delta["cb_cvd"]
        spot = delta["bin_spot"]
        perp = delta["bin_perp"]

        # SPOT-LED (bullish) scoring
        if cb > 1 and spot > 1:
            score += 2 * weight
            notes.append(f"{tf} spot flow rising")

        # PERP DUMP scoring
        if perp < -1:
            score += 1 * weight
            notes.append(f"{tf} perp fading")

        # CONFLICT signal (perp rising while spot falls)
        if perp > 1 and spot < -1:
            score -= 2 * weight
            notes.append(f"{tf} perp vs spot conflict")

        # FLAT: no movement = minor penalty
        if abs(cb) < 0.3 and abs(spot) < 0.3 and abs(perp) < 0.3:
            score -= 0.5 * weight
            notes.append(f"{tf} flat market")

    # === Bias Label Logic ===
    label = "neutral"
    if score >= 6:
        label = "spot_dominant"
    elif score >= 3:
        label = "spot_advantage"
    elif score <= 0:
        label = "perp_dominant"
    elif score <= 2:
        label = "perp_advantage"

    return {
        "score": round(score, 1),
        "label": label,
        "notes": notes
    }
