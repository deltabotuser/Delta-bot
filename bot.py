import time
import requests

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "9057984357:AAFBz96JKKTaDQKVlSGNCC09NI YOA-FznmU"
TELEGRAM_CHAT_ID = "5573743290"  # Apni chat ID yahan daalein
DELTA_API_BASE = "https://api.delta.exchange"

# Delta Exchange ke sabhi main aur popular USDT perpetuals ki direct list (0-200$ aur baaki sabhi coins)
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", 
    "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "PEPEUSDT", 
    "SHIBUSDT", "WIFUSDT", "RENDERUSDT", "FETUSDT", "INJUSDT", "TIAUSDT", "ATOMUSDT", 
    "FTMUSDT", "ICPUSDT", "BCHUSDT", "LTCUSDT", "ETCUSDT", "ALGOUSDT", "SANDUSDT", 
    "MANAUSDT", "AXSUSDT", "GALAUSDT", "GMTUSDT", "IMXUSDT", "CRVUSDT", "AAVEUSDT", 
    "UNIUSDT", "MKRUSDT", "SNXUSDT", "RUNEUSDT", "KASUSDT", "BONKUSDT", "FLOKIUSDT", 
    "JUPUSDT", "DYMUSDT", "STRKUSDT", "SEIUSDT", "BLURUSDT", "ORDIUSDT", "POLUSDT",
    "1000PEPEUSDT", "1000SHIBUSDT", "1000BONKUSDT", "1000FLOKIUSDT", "ENAUSDT", "PENDLEUSDT"
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_delta_symbols():
    """Direct list + API se extra coins merge karke return karega"""
    symbols = set(DEFAULT_SYMBOLS)
    try:
        url = f"{DELTA_API_BASE}/v2/products"
        response = requests.get(url)
        data = response.json()
        if data.get("success"):
            for prod in data["result"]:
                symbol = prod.get("symbol", "")
                if "USDT" in symbol and prod.get("contract_type") == "perpetual_futures":
                    symbols.add(symbol)
    except Exception as e:
        print(f"API fetch notice: {e}")
    
    return list(symbols)

def get_ohlcv(symbol, resolution="15m"):
    try:
        url = f"{DELTA_API_BASE}/v2/history/candles"
        params = {"symbol": symbol, "resolution": resolution, "limit": 30}
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("success") and data.get("result"):
            return data["result"]
    except Exception as e:
        pass
    return None

def check_liquidity_sweep_and_smc(symbol, candles):
    if candles is None or len(candles) < 20:
        return None

    current = candles[-1]
    prev = candles[-2]
    
    curr_open, curr_high, curr_low, curr_close = current[1], current[2], current[3], current[4]
    prev_open, prev_high, prev_low, prev_close = prev[1], prev[2], prev[3], prev[4]
    
    historical = candles[-22:-2]
    swing_high = max([c[2] for c in historical])
    swing_low = min([c[3] for c in historical])
    
    setup = None
    
    # Bullish Liquidity Sweep
    if prev_low < swing_low and curr_close > curr_open and curr_close > prev_high:
        entry = curr_close
        sl = swing_low - (entry * 0.003)
        tp = entry + ((entry - sl) * 3)
        setup = {
            "type": "BULLISH (Buy / Long)",
            "reason": "Liquidity Sweep below recent swing low + Structure Shift",
            "entry": entry,
            "sl": sl,
            "tp": tp
        }
        
    # Bearish Liquidity Sweep
    elif prev_high > swing_high and curr_close < curr_open and curr_close < prev_low:
        entry = curr_close
        sl = swing_high + (entry * 0.003)
        tp = entry - ((sl - entry) * 3)
        setup = {
            "type": "BEARISH (Sell / Short)",
            "reason": "Liquidity Sweep above recent swing high + Structure Shift",
            "entry": entry,
            "sl": sl,
            "tp": tp
        }
        
    return setup

def scan_market():
    print("--- Scanning Delta Exchange markets ---")
    symbols = get_delta_symbols()
    print(f"Total coins loaded for scanning: {len(symbols)}")

    for symbol in symbols:
        print(f"Checking coin: {symbol}...")
        candles = get_ohlcv(symbol, resolution="15m")
        setup = check_liquidity_sweep_and_smc(symbol, candles)
        
        if setup:
            print(f">>> SETUP FOUND ON {symbol}! Sending alert...")
            msg = (
                f"🚨 *SMC & LIQUIDITY SWEEP ALERT* 🚨\n\n"
                f"🪙 *Asset:* `{symbol}`\n"
                f"📊 *Setup:* {setup['type']}\n"
                f"💡 *Logic:* {setup['reason']}\n\n"
                f"🎯 *Entry Price:* `{setup['entry']:.4f}`\n"
                f"🛑 *Stop Loss (SL):* `{setup['sl']:.4f}`\n"
                f"✅ *Take Profit (TP 1:3):* `{setup['tp']:.4f}`\n\n"
                f"⚡ *Pydroid Python Bot*"
            )
            send_telegram_alert(msg)
        time.sleep(0.1) # Fast scanning ke liye chota delay
    print("Scan complete. Waiting for next cycle...\n")

if __name__ == "__main__":
    while True:
        try:
            scan_market()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)
