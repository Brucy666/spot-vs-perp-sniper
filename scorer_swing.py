# scorer_swing.py (polished + production ready)

def score_swing_confluence(deltas):
    """
    Swing scoring engine: Evaluates higher timeframes for directional bias.
    Uses: 15m, 30m, 1h, 4h
    Returns: { score: float, label: "spot_dominant" | "perp_dominant" | "neutral" }
    """
    try:
        tf_weights = {
            "15m": 1,
            "30m": 1.5,
            "1h":  2,
            "4h":  2.5
        }

        score = 0
        total_weight = 0

        for tf, weight in tf_weights.items():
            tf_delta = deltas.get(tf)
            if not tf_delta:
                continue

            cb     = tf_delta["cb_cvd"]
            spot   = tf_delta["bin_spot"]
            perp   = tf_delta["bin_perp"]

            if cb > 0 and spot > 0 and perp < 0:
                score += 1.5 * weight  # Strong spot-led trend
            elif perp > 0 and cb < 0 and spot <= 0:
                score -= 1.5 * weight  # Strong perp-led trap
            elif cb > 0 and spot < 0:
                score += 0.5 * weight  # Divergence (possible absorption)
            elif cb < 0 and spot > 0:
                score -= 0.5 * weight  # Inverse divergence

            total_weight += weight

        final_score = round((score / total_weight) * 10, 2) if total_weight else 0

        if final_score > 3:
            label = "spot_dominant"
        elif final_score < -3:
            label = "perp_dominant"
        else:
            label = "neutral"

        return {"score": final_score, "label": label}

    except Exception as e:
        print("[X] Error in score_swing_confluence:", e)
        return {"score": 0, "label": "neutral"}
