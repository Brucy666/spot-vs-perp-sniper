# utils/spot_perp_scorer.py

def score_spot_perp_confluence_multi(deltas):
    """
    Accepts multi-timeframe delta dictionary with keys:
    '5m', '15m', '1h' etc, each with:
      - cb_cvd
      - bin_spot
      - bin_perp

    Returns:
        score: float
        label: 'spot_dominant', 'perp_dominant', or 'neutral'
    """
    tf_weights = {
        "5m": 1,
        "15m": 2,
        "1h": 3
    }

    score = 0
    spot_bias = 0
    perp_bias = 0

    for tf, weight in tf_weights.items():
        delta = deltas.get(tf)
        if not delta:
            continue

        cb = delta["cb_cvd"]
        spot = delta["bin_spot"]
        perp = delta["bin_perp"]

        # === Spot Bias ===
        if cb > 0 and spot > 0 and perp < 0:
            score += 1.5 * weight
            spot_bias += weight
        elif cb > 0 and spot > 0:
            score += 1.0 * weight
            spot_bias += weight
        elif cb > 0 or spot > 0:
            score += 0.5 * weight
            spot_bias += weight / 2

        # === Perp Bias ===
        if perp > 0 and cb < 0 and spot <= 0:
            score -= 1.5 * weight
            perp_bias += weight
        elif perp > 0 and cb < 0:
            score -= 1.0 * weight
            perp_bias += weight
        elif perp > 0:
            score -= 0.5 * weight
            perp_bias += weight / 2

    final_score = round(score / sum(tf_weights.values()), 1)

    # === Label ===
    if final_score >= 2:
        label = "spot_dominant"
    elif final_score <= -2:
        label = "perp_dominant"
    else:
        label = "neutral"

    return {
        "score": final_score,
        "label": label
    }
