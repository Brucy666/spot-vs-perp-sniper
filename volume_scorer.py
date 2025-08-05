# volume_scorer.py

def score_volume_confluence(volume_data):
    """
    Takes a volume snapshot and returns a volume score and label.
    Expects:
        volume_data = {
            "binance_spot_volume": float,
            "binance_base_volume": float
        }
    """
    try:
        spot = volume_data.get("binance_spot_volume", 0)
        perp = volume_data.get("binance_base_volume", 0)

        if spot == 0 or perp == 0:
            return {"volume_score": 0, "volume_label": "neutral"}

        ratio = spot / perp
        delta = round((spot - perp) / max(spot, perp) * 100, 2)

        if ratio >= 1.25:
            label = "spot_dominant"
            score = min(round(ratio * 3), 10)
        elif ratio <= 0.75:
            label = "perp_dominant"
            score = min(round((1 / ratio) * 3), 10)
        else:
            label = "neutral"
            score = 0

        return {
            "volume_score": score,
            "volume_label": label,
            "spot_vs_perp_ratio": ratio,
            "percent_diff": delta
        }

    except Exception as e:
        print("[X] Volume scoring error:", e)
        return {"volume_score": 0, "volume_label": "neutral"}
