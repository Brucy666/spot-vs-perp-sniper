# ai_volume_scoring.py (Upgraded Volume & Short Detection Logic)

import math

def score_volume_bias(volume_data):
    """
    Enhanced AI scoring logic for volume confluence.
    Dynamically scales score based on volume ratio, size, and delta.
    Returns a volume_score (0-10) and directional label.
    """
    try:
        spot = float(volume_data.get("binance_spot_volume", 0))
        perp = float(volume_data.get("binance_base_volume", 0))

        if spot == 0 or perp == 0:
            return 0, "neutral"

        ratio = spot / perp
        imbalance = round((spot - perp) / max(spot, perp) * 100, 2)

        # Penalty for low liquidity
        liquidity_factor = min(spot + perp, 50000000) / 50000000  # scale to 1

        # Score scale
        if ratio >= 1.2:
            score = min(10, (ratio * 5 + imbalance / 10) * liquidity_factor)
            return round(score, 2), "spot_dominant"
        elif ratio <= 0.8:
            score = min(10, ((1 / ratio) * 5 + abs(imbalance) / 10) * liquidity_factor)
            return round(score, 2), "perp_dominant"
        else:
            return 0, "neutral"

    except Exception as e:
        print("[X] AI Volume Scoring Error:", e)
        return 0, "neutral"
