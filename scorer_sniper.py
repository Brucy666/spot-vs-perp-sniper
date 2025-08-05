# scorer_sniper.py

def score_sniper_confluence(deltas):
    """
    Sniper scoring engine.
    Evaluates short-term timeframes (1m, 3m, 5m) for aggressive confluence.
    Returns:
        {
            "score": float,
            "label": "spot_dominant" | "perp_dominant" | "neutral"
        }
    """
    try:
        tf_weights = {
            "1m": 1.5,
            "3m": 2.0,
            "5m": 2.5
        }

        score = 0
        total_weight = 0

        for tf, weight in tf_weights.items():
            tf_delta = deltas.get(tf)
            if not tf_delta:
                continue

            cb = tf_delta["cb_cvd"]
            spot = tf_delta["bin_spot"]
            perp = tf_delta["bin_perp"]

            # Spot-led sniper
            if cb > 0 and spot > 0 and perp < 0:
                score += 1.5 * weight
            elif cb > 0 and spot > 0:
                score += 1.0 * weight
            elif cb < 0 and spot < 0:
                score -= 1.0 * weight
            elif perp > 0 and cb < 0 and spot <= 0:
                score -= 1.5 * weight

            total_weight += weight

        final_score = round(score / total_weight * 10, 2) if total_weight else 0

        if final_score > 3:
            label = "spot_dominant"
        elif final_score < -3:
            label = "perp_dominant"
        else:
            label = "neutral"

        return {
            "score": final_score,
            "label": label
        }

    except Exception as e:
        print("[X] Error in score_sniper_confluence:", e)
        return {
            "score": 0,
            "label": "neutral"
        }
