# ai_volume_scoring.py (Sharpened Short Bias Detection)

def score_volume_bias(volume_data):
    """
    Enhanced volume bias logic: adds sharper SHORT detection
    Returns:
        score (float): 0 to 10 confidence score
        label (str): spot_dominant | perp_dominant | neutral
    """
    try:
        spot = float(volume_data.get("binance_spot_volume", 0))
        perp = float(volume_data.get("binance_base_volume", 0))

        if spot == 0 or perp == 0:
            return 0, "neutral"

        ratio = spot / perp
        imbalance = round((spot - perp) / max(spot, perp) * 100, 2)

        liquidity_factor = min(spot + perp, 50000000) / 50000000

        if ratio >= 1.2:
            score = min(10, (ratio * 5 + imbalance / 10) * liquidity_factor)
            return round(score, 2), "spot_dominant"

        elif ratio <= 0.85:
            strength = (1 / ratio) * 6 + abs(imbalance) / 8  # stronger SHORT weighting
            score = min(10, strength * liquidity_factor)
            return round(score, 2), "perp_dominant"

        return 0, "neutral"

    except Exception as e:
        print("[X] AI Volume Scoring Error:", e)
        return 0, "neutral"
