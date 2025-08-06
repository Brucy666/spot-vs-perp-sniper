# volume_fetcher.py (AI-patched volume fetchers)
import requests

# REST API endpoints for volume
BINANCE_REST = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
BYBIT_REST = "https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT"
COINBASE_REST = "https://api.pro.coinbase.com/products/BTC-USD/stats"

def fetch_binance_volume():
    try:
        res = requests.get(BINANCE_REST, timeout=5)
        if not res.ok:
            raise ValueError(f"Invalid response: {res.status_code}")
        data = res.json()

        quote_vol = float(data.get("quoteVolume", 0))
        base_vol = float(data.get("volume", 0))

        if quote_vol == 0 or base_vol == 0:
            print("[!] Binance volume returned 0 — potential throttling or issue.")

        return {
            "binance_spot_volume": quote_vol,
            "binance_base_volume": base_vol
        }

    except Exception as e:
        print("[X] Binance volume fetch failed:", e)
        return {}

def fetch_bybit_volume():
    try:
        res = requests.get(BYBIT_REST, timeout=5)

        if not res.ok or not res.text.strip().startswith("{"):
            raise ValueError("Empty or invalid JSON response from Bybit")

        data = res.json()
        result = data.get("result", [])

        if isinstance(result, list) and result:
            turnover = float(result[0].get("turnover_24h", 0))
            return {
                "bybit_perp_volume": turnover
            }
        else:
            print("[!] Bybit returned no usable result")
            return {}

    except Exception as e:
        print("[X] Bybit volume fetch failed:", e)
        return {}

def fetch_coinbase_volume():
    try:
        res = requests.get(COINBASE_REST, timeout=5)

        if not res.ok:
            raise ValueError(f"Coinbase returned {res.status_code}")

        data = res.json()
        volume = data.get("volume")

        if volume:
            return {
                "coinbase_spot_volume": float(volume)
            }
        else:
            print("[!] Coinbase volume missing or zero")
            return {}

    except Exception as e:
        print("[X] Coinbase volume fetch failed:", e)
        return {}

def fetch_all_volume():
    """
    Fetches and combines volume data from Binance, Bybit, and Coinbase.
    Returns a unified dictionary.
    """
    volume_snapshot = {}
    volume_snapshot.update(fetch_binance_volume())
    volume_snapshot.update(fetch_bybit_volume())
    volume_snapshot.update(fetch_coinbase_volume())
    return volume_snapshot
