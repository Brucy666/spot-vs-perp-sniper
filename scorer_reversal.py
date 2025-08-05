# scorer_reversal.py

def score_reversal_trap(deltas):
    """
    Detects possible reversal trap setups based on mismatch between
    short-term and long-term CVD signals.
    Uses: short = 1m, 3m; long = 15m, 1h
    """
    try:
        short_tf = deltas.get("1m") or deltas.get("3m")
        long_tf = deltas.get("15m") or deltas.get("1h")

        if not short_tf or not long_tf:
            return {"score": 0, "label": "neutral"}

        cb_short = short_tf["cb_cvd"]
        spot_short = short_tf["bin_spot"]
        perp_short = short_tf["bin_perp"]

        cb_long = long_tf["cb_cvd"]
        spot_long = long_tf["bin_spot"]
        perp_long = long_tf["bin_perp"]

        # Trap LONG: macro bullish but perps shorting or spot dumping
        if cb_long > 0 and spot_long > 0 and perp_short > 0 and cb_short < 0:
            return {"score": 8.0, "label": "spot_dominant"}

        # Trap SHORT: macro bearish but spot or perps pushing up
        if cb_long < 0 and spot_long < 0 and spot_short > 0 and cb_short > 0:
            return {"score": 8.0, "label": "perp_dominant"}

        return {"score": 4.0, "label": "neutral"}

    except Exception as e:
        print("[X] Reversal scoring error:", e)
        return {"score": 0, "label": "neutral"}
