# scorer_sniper.py (AI-enhanced directional scoring logic)

def score_sniper_confluence(deltas, volume_bias=None):
    """
    Multi-timeframe CVD scoring logic with enhanced SHORT detection and volume confluence.
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

            # 🔴 Custom SHORT trigger: clear retail long trap
            if cb < -5 and perp > 5 and spot <= 0:
                return {"score": 9, "label": "perp_dominant"}

            # 🧠 Scoring logic
            if cb > 0 and spot > 0 and perp < 0:
                score += 1.5 * weight  # strong LONG
            elif perp > 0 and cb < 0 and spot <= 0:
                score -= 1.5 * weight  # strong SHORT
            elif cb > 0 and spot < 0:
                score += 0.5 * weight  # weak long
            elif cb < 0 and spot > 0:
                score -= 0.5 * weight  # weak short

            total_weight += weight

        if total_weight == 0:
            return {"score": 0, "label": "neutral"}

        cvd_score = round((score / total_weight) * 10, 2)

        # 🔄 Volume blending
        final_score = cvd_score
        if volume_bias:
            vol_score, vol_label = volume_bias
            blend_ratio = 0.7 if vol_label == "neutral" else 0.5
            final_score = round((cvd_score * blend_ratio) + (vol_score * (1 - blend_ratio)), 2)

        # 🧭 Final label
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
