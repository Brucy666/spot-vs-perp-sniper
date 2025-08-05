# scorer_reversal.py

def score_reversal_confluence(deltas):
    """
    Reversal bot logic: detects counter-trend divergences.
    Looks for spot strength while perps weaken (potential trap), or vice versa.
    Uses: 5m, 15m, 1h
    Returns dict with score and label: spot_dominant / perp_dominant / neutral
    """

    try:
        tf_weights = {
            "5m": 1,
            "15m": 2,
            "1h": 2.5
        }

        score = 0
        total_weight = 0

        for tf, weight in tf_weights.items():
            tf_delta = deltas.get(tf)
            if not tf_delta:
                continue

            cb, spot, perp = tf_delta["cb_cvd"], tf_delta["bin_spot"], tf_delta["bin_perp"]

            # Trap logic — reversal opportunities
            if cb > 0 and spot > 0 and perp < 0:
                # Spot strength but perps selling = short trap forming
                score += 1.5 * weight
            elif cb < 0 and spot < 0 and perp > 0:
                # Spot weakness but perps buying = long trap forming
                score -= 1.5 * weight
            elif cb > 0 and spot < 0:
                # Coinbase divergence
                score += 0.5 * weight
            elif cb < 0 and spot > 0:
                # Coinbase weakness but spot holding
                score -= 0.5 * weight

            total_weight += weight

        final_score = round(score / total_weight * 10, 2) if total_weight else 0

        if final_score > 3:
            label = "spot_dominant"  # Reversal long trap
        elif final_score < -3:
            label = "perp_dominant"  # Reversal short trap
        else:
            label = "neutral"

        return {"score": final_score, "label": label}

    except Exception as e:
        print("[X] Error in score_reversal_confluence:", e)
        return {"score": 0, "label": "neutral"}
