# scorer_reversal.py (updated for deep macro TFs)

def score_reversal_trap(deltas):
    """
    Detects macro trap signals by comparing short-term pressure vs long-term trend.
    Uses: short = 1h, long = 4h, 8h, 12h, 1d
    """
    try:
        short_tf = deltas.get("1h")
        macro_tfs = ["4h", "8h", "12h", "1d"]
        macro_bias = 0

        for tf in macro_tfs:
            tf_delta = deltas.get(tf)
            if not tf_delta:
                continue

            cb, spot, perp = tf_delta["cb_cvd"], tf_delta["bin_spot"], tf_delta["bin_perp"]

            if cb > 0 and spot > 0 and perp < 0:
                macro_bias += 1
            elif cb < 0 and spot < 0 and perp > 0:
                macro_bias -= 1

        if not short_tf or macro_bias == 0:
            return {"score": 0, "label": "neutral"}

        cb_short = short_tf["cb_cvd"]
        spot_short = short_tf["bin_spot"]
        perp_short = short_tf["bin_perp"]

        # If macro bullish but short-term is selling → trap LONG
        if macro_bias > 1 and (cb_short < 0 and perp_short > 0):
            return {"score": 8.5, "label": "spot_dominant"}

        # If macro bearish but short-term is buying → trap SHORT
        if macro_bias < -1 and (cb_short > 0 and spot_short > 0):
            return {"score": 8.5, "label": "perp_dominant"}

        return {"score": 4.0, "label": "neutral"}

    except Exception as e:
        print("[X] Reversal scoring error:", e)
        return {"score": 0, "label": "neutral"}
