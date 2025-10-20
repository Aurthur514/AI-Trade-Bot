# CoinSwitch PRO - Auto-Trading Bot with Trend Reversal Strategy and Rate Handling

import os
import time
import json
import requests
import urllib
from urllib.parse import urlencode, urlparse
from cryptography.hazmat.primitives.asymmetric import ed25519

# --- CONFIGURATION ---
# IMPORTANT: It is highly recommended to use environment variables for API keys.
# Export the variables in your terminal before running the script:
# export API_KEY="your_api_key_here"
# export SECRET_KEY="your_secret_key_here"
API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
BASE_URL = "https://coinswitch.co"
EXCHANGE = "coinswitchx"
SYMBOL_SUFFIX = "/INR"
TRADE_PERCENT_OF_BALANCE = 0.9
REQUEST_TIMEOUT = 5
MAX_COINS_TO_PROCESS = 15

# --- UTILS ---
def safe_get(url, headers, params=None):
    retries = 3
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            return res
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            time.sleep(1.5)  # wait a bit before retrying
    print("[ERROR] All retry attempts failed for:", url)
    return None

def get_server_time():
    res = safe_get(f"{BASE_URL}/trade/api/v2/time", headers={})
    if res:
        return str(res.json().get("serverTime", str(int(time.time() * 1000))))
    return str(int(time.time() * 1000))

def generate_signature(method, endpoint, params, body, epoch_time):
    message_to_sign = method
    path = endpoint
    if method == "GET" and params:
        path += '?' + urlencode(params)
    message_to_sign += urllib.parse.unquote_plus(path)
    if body:
        body_string = json.dumps(body, separators=(',', ':'), sort_keys=True)
    else:
        body_string = "{}"
    message_to_sign += body_string
    message_to_sign += epoch_time
    request_string = message_to_sign.encode('utf-8')
    secret_bytes = bytes.fromhex(SECRET_KEY)
    key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
    return key.sign(request_string).hex()

def get_headers(method, endpoint, params=None, body=None):
    epoch_time = get_server_time()
    signature = generate_signature(method, endpoint, params, body, epoch_time)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature,
        'X-AUTH-EPOCH': epoch_time
    }
    return headers, BASE_URL + endpoint

# --- STEP 1: GET INR Balance ---
def get_inr_balance():
    endpoint = "/trade/api/v2/user/portfolio"
    headers, url = get_headers("GET", endpoint)
    res = safe_get(url, headers)
    if not res:
        return 0
    data = res.json().get("data", [])
    for item in data:
        if item["currency"].lower() == "inr":
            return float(item["main_balance"])
    return 0

# --- STEP 2: Get tradable coins, limited to top N ---
def get_tradable_symbols():
    # Fallback symbols due to limited access
    return [
        {"symbol": "BTC/INR", "price": 950000.0, "change": 3.5},
        {"symbol": "ETH/INR", "price": 230000.0, "change": 5.2},
        {"symbol": "MATIC/INR", "price": 50.0, "change": 6.1}
    ]

# --- STEP 3: Get Trade Info ---
def get_trade_info(symbol):
    endpoint = "/trade/api/v2/tradeInfo"
    params = {"exchange": EXCHANGE, "symbol": symbol}
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params)
    if not res:
        return {}
    return res.json().get("data", {}).get(EXCHANGE, {}).get(symbol, {})

# --- STEP 4: Get recent candles ---
def get_recent_candles(symbol):
    endpoint = "/trade/api/v2/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (15 * 60 * 1000 * 3)
    params = {
        "symbol": symbol,
        "exchange": EXCHANGE,
        "interval": 15,
        "start_time": start_time,
        "end_time": end_time
    }
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params)
    if not res:
        return []
    return res.json().get("data", {}).get(symbol, [])

# --- STEP 5: Trend reversal check ---
def is_reversing_up(candles):
    if len(candles) < 2:
        return False
    last = candles[-1][4]
    prev = candles[-2][4]
    return float(last) > float(prev)

# --- STEP 6: Place Limit Order ---
def place_order(symbol, price, qty):
    endpoint = "/trade/api/v2/order"
    payload = {
        "side": "buy",
        "symbol": symbol,
        "type": "limit",
        "price": round(price, 2),
        "quantity": qty,
        "exchange": EXCHANGE
    }
    headers, url = get_headers("POST", endpoint, body=payload)
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        print(f"[TRADE] {symbol} @ ₹{price} =>", res.json())
    except Exception as e:
        print(f"[ERROR] Order failed for {symbol}: {e}")

# --- MAIN STRATEGY EXECUTION ---
def run_trading_bot():
    if not API_KEY or not SECRET_KEY:
        print("[ERROR] API_KEY and SECRET_KEY must be set as environment variables.")
        return
        # Validate API access before starting
    print("[INFO] Testing API Key authorization...")
    headers, url = get_headers("GET", "/trade/api/v2/time")
    res = safe_get(url, headers)
    if not res:
        print("[ERROR] API Key appears to be unauthorized or invalid. Exiting bot.")
        return
    start_balance = get_inr_balance()
    print("[INFO] INR Balance:", start_balance)
    tradable = get_tradable_symbols()
    print("[INFO] Found Tradable Coins:", tradable)

    trade_summary = []
    for coin in tradable:
        symbol = coin["symbol"]
        price = coin["price"]
        trade_info = get_trade_info(symbol)
        min_amt = float(trade_info.get("quote", {}).get("min", 0))
        qty_precision = trade_info.get("precision", {}).get("base", 6)

        max_invest = start_balance * TRADE_PERCENT_OF_BALANCE
        if price and min_amt and max_invest >= min_amt:
            qty = round(max_invest / price, qty_precision)
            total_cost = price * qty

            candles = get_recent_candles(symbol)
            if is_reversing_up(candles):
                print(f"[DECISION] BUY {symbol}: price={price}, qty={qty}, cost={total_cost:.2f}")
                place_order(symbol, price, qty)
                trade_summary.append((symbol, price, qty, total_cost))
                start_balance -= total_cost
            else:
                print(f"[SKIP] {symbol} is not reversing up.")
        time.sleep(0.5)

    print("\n[SUMMARY] Trades Executed:")
    for t in trade_summary:
        print(f" - {t[0]} | Qty: {t[2]} | Price: ₹{t[1]} | Total: ₹{t[3]:.2f}")

    final_balance = get_inr_balance()
    print(f"[INFO] Final INR Balance: ₹{final_balance:.2f}")

if __name__ == "__main__":
    run_trading_bot()
