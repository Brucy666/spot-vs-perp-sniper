# volume_fetcher.py

import requests

# REST API endpoints for volume
BINANCE_REST = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
BYBIT_REST = "https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT"
COINBASE_REST = "https://api.pro.coinbase.com/products/BTC-USD/stats"

def fetch_binance_volume():
    try:
        res = requests.get(BINANCE_REST, timeout=5)
        data = res.json()
        return {
            "binance_spot_volume": float(data["quoteVolume"]),
            "binance_base_volume": float(data["volume"])
        }
    except Exception as e:
        print("[X] Binance volume fetch failed:", e)
        return {}

def fetch_bybit_volume():
    try:
        res = requests.get(BYBIT_REST, timeout=5)
        data = res.json()["result"][0]
        return {
            "bybit_perp_volume": float(data["turnover_24h"])  # quote volume
        }
    except Exception as e:
        print("[X] Bybit volume fetch failed:", e)
        return {}

def fetch_coinbase_volume():
    try:
        res = requests.get(COINBASE_REST, timeout=5)
        data = res.json()
        return {
            "coinbase_spot_volume": float(data["volume"])
        }
    except Exception as e:
        print("[X] Coinbase volume fetch failed:", e)
        return {}

def fetch_all_volume():
    result = {}
    result.update(fetch_binance_volume())
    result.update(fetch_bybit_volume())
    result.update(fetch_coinbase_volume())
    return result
