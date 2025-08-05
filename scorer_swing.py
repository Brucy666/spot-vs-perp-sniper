# scorer_swing.py

def score_swing_tf(deltas):
    """
    Swing scoring engine: evaluates higher timeframes for bias.
    Uses: 15m, 1h, 4h
    Returns a dict with total score and bias label
    """
    try:
        tf_weights = {
            "15m": 1,
            "1h": 2,
            "4h": 3
        }

        score = 0
        total_weight = 0

        for tf, weight in tf_weights.items():
            tf_delta = deltas.get(tf)
            if not tf_delta:
                continue

            cb, spot, perp = tf_delta["cb_cvd"], tf_delta["bin_spot"], tf_delta["bin_perp"]

            if cb > 0 and spot > 0 and perp < 0:
                score += 1.5 * weight
            elif perp > 0 and cb < 0 and spot <= 0:
                score -= 1.5 * weight
            elif cb > 0 and spot < 0:
                score += 0.5 * weight
            elif cb < 0 and spot > 0:
                score -= 0.5 * weight

            total_weight += weight

        final_score = round(score / total_weight * 10, 2) if total_weight else 0

        if final_score > 3:
            label = "spot_dominant"
        elif final_score < -3:
            label = "perp_dominant"
        else:
            label = "neutral"

        return {"score": final_score, "label": label}

    except Exception as e:
        print("[X] Error in score_swing_tf:", e)
        return {"score": 0, "label": "neutral"}
