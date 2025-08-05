# scorer_sniper.py (updated for 1m, 3m, 5m only)

def score_spot_perp_confluence_sniper(deltas):
    tf_weights = {
        "1m":  0.4,
        "3m":  0.35,
        "5m":  0.25
    }

    total_score = 0
    total_weight = 0
    spot_dominant = 0
    perp_dominant = 0

    for tf, weight in tf_weights.items():
        if tf not in deltas:
            continue

        cb = deltas[tf]["cb_cvd"]
        spot = deltas[tf]["bin_spot"]
        perp = deltas[tf]["bin_perp"]

        total_weight += weight
        signal_strength = 0

        if cb > 0 and spot > 0 and perp < 0:
            signal_strength = 10
            spot_dominant += 1
        elif perp > 0 and spot <= 0 and cb <= 0:
            signal_strength = -10
            perp_dominant += 1

        total_score += signal_strength * weight

    normalized_score = round(abs(total_score) / total_weight, 1) if total_weight > 0 else 0

    if spot_dominant >= 2:
        label = "spot_dominant"
    elif perp_dominant >= 2:
        label = "perp_dominant"
    else:
        label = "neutral"

    return {
        "score": normalized_score,
        "label": label
    }
