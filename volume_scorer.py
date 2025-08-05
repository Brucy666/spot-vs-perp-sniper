# volume_scorer.py

def score_volume_bias(volume_data):
    """
    Scores directional volume behavior from spot vs perp.
    Returns:
        score (float): Confidence boost from volume context
        label (str): 'spot_dominant', 'perp_dominant', or 'neutral'
    """
    try:
        spot_volume = float(volume_data.get("binance_spot_volume", 0))
        perp_volume = float(volume_data.get("binance_base_volume", 0))

        if spot_volume == 0 or perp_volume == 0:
            return 0, "neutral"

        ratio = spot_volume / perp_volume

        if ratio > 1.25:
            return 8, "spot_dominant"
        elif ratio < 0.75:
            return 8, "perp_dominant"
        else:
            return 0, "neutral"

    except Exception as e:
        print("[X] Volume scoring failed:", e)
        return 0, "neutral"
