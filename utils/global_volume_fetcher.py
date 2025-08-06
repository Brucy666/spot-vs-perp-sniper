# utils/global_volume_fetcher.py

import requests
import os

CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")

# --- REST Endpoints ---
BINANCE_REST = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
BYBIT_V5_REST = "https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT"
OKX_REST = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
CMC_REST = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC"

# --- Individual Fetchers ---
def fetch_binance_volume():
    try:
        res = requests.get(BINANCE_REST, timeout=5)
        data = res.json()
        return {
            "binance_spot_volume": float(data.get("quoteVolume", 0)),
            "binance_base_volume": float(data.get("volume", 0))
        }
    except Exception as e:
        print("[X] Binance volume fetch failed:", e)
        return {}

def fetch_bybit_v5_volume():
    try:
        res = requests.get(BYBIT_V5_REST, timeout=5)
        data = res.json()
        if data.get("retCode") == 0 and "result" in data:
            ticker = data["result"]["list"][0]
            return {
                "bybit_perp_volume": float(ticker.get("turnover24h", 0))
            }
    except Exception as e:
        print("[X] Bybit V5 volume fetch failed:", e)
    return {}

def fetch_okx_volume():
    try:
        res = requests.get(OKX_REST, timeout=5)
        data = res.json()
        ticker = data["data"][0]
        return {
            "okx_volume": float(ticker.get("volCcy24h", 0))
        }
    except Exception as e:
        print("[X] OKX volume fetch failed:", e)
        return {}

def fetch_coinmarketcap_volume():
    try:
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        res = requests.get(CMC_REST, headers=headers, timeout=5)
        data = res.json()
        quote = data["data"]["BTC"]["quote"]["USD"]
        return {
            "cmc_volume": float(quote.get("volume_24h", 0))
        }
    except Exception as e:
        print("[X] CoinMarketCap volume fetch failed:", e)
        return {}

# --- Combined Fetcher ---
def fetch_all_volume():
    result = {}
    result.update(fetch_binance_volume())
    result.update(fetch_bybit_v5_volume())
    result.update(fetch_okx_volume())
    result.update(fetch_coinmarketcap_volume())
    return result
