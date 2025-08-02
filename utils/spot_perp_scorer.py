# utils/spot_perp_scorer.py

def score_spot_perp_confluence(deltas):
    cb = deltas.get("cb_cvd", 0)
    spot = deltas.get("bin_spot", 0)
    perp = deltas.get("bin_perp", 0)

    score = 0
    label = "neutral"

    # === Base Scoring Rules ===

    # Real spot strength
    if cb > 2 and spot > 1:
        score += 4
    elif cb > 0.5 and spot > 0.5:
        score += 2

    # Perp weakness
    if perp < -2:
        score += 3
    elif perp < -0.5:
        score += 1

    # Trap detection: spot strong, perps fading
    if cb > 1 and spot > 1 and perp < -1:
        score += 2

    # Conflict: if perp rising while spot flat/down
    if perp > 1 and spot < 0:
        score -= 2

    # Slight penalty for noise
    if abs(cb) < 0.3 and abs(spot) < 0.3 and abs(perp) < 0.3:
        score -= 1

    # === Label Assignment ===
    if score >= 7:
        label = "spot_dominant"
    elif score >= 4:
        label = "spot_advantage"
    elif score <= 0 and perp > 2:
        label = "perp_dominant"
    elif score <= 2:
        label = "perp_advantage"

    return {
        "score": round(score, 1),
        "label": label
    }
