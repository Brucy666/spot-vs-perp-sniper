# scorer_sniper.py (AI-enhanced directional scoring logic)

def score_sniper_confluence(deltas, volume_bias=None):
    """
    Multi-timeframe CVD scoring logic with volume bias integration.
    Returns score (float) and label (str).
    """
    try:
        tf_weights = {
            "1m": 1,
            "3m": 1.5,
            "5m": 2
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

            if cb > 0 and spot > 0 and perp < 0:
                score += 1.5 * weight
            elif perp > 0 and cb < 0 and spot <= 0:
                score -= 1.5 * weight
            elif cb > 0 and spot < 0:
                score += 0.5 * weight
            elif cb < 0 and spot > 0:
                score -= 0.5 * weight

            total_weight += weight

        if total_weight == 0:
            return {"score": 0, "label": "neutral"}

        cvd_score = round(score / total_weight * 10, 2)

        # Blend with volume bias
        final_score = cvd_score
        if volume_bias:
            vol_score, vol_label = volume_bias
            blend_ratio = 0.7 if vol_label == "neutral" else 0.5
            final_score = round((cvd_score * blend_ratio) + (vol_score * (1 - blend_ratio)), 2)

        # Label
        if final_score > 2:
            label = "spot_dominant"
        elif final_score < -2:
            label = "perp_dominant"
        else:
            label = "neutral"

        return {
            "score": final_score,
            "label": label
        }

    except Exception as e:
        print("[X] Sniper scoring error:", e)
        return {"score": 0, "label": "neutral"}
