from FinMind.data import DataLoader
import pandas as pd
import requests
import schedule
import time

# ================================
# 🔧 設定
# ================================
LINE_TOKEN = "你的LINE_TOKEN"   # ←改這裡
START_DATE = "2026-03-01"

api = DataLoader()

# ================================
# 🔔 LINE通知
# ================================
def send_line(msg):
    try:
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
        data = {"message": msg}
        requests.post(url, headers=headers, data=data)
    except Exception as e:
        print("LINE 發送失敗:", e)

# ================================
# 📊 股票清單
# ================================
def get_all_stocks():
    df = api.taiwan_stock_info()
    return df[df["industry_category"].notnull()][
        ["stock_id", "stock_name", "industry_category"]
    ]

# ================================
# 📈 價格資料
# ================================
def get_price(stock_id):
    try:
        df = api.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=START_DATE
        )
        return df.tail(30)
    except:
        return None

# ================================
# 💰 三大法人
# ================================
def get_flow(stock_id):
    try:
        data = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date="2026-04-01"
        )
        if data.empty:
            return 0

        latest = data.iloc[-1]
        return (
            latest["Foreign_Investor"] +
            latest["Investment_Trust"] +
            latest["Dealer"]
        )
    except:
        return 0

# ================================
# 🧠 題材分類
# ================================
def classify_theme(name):
    name = str(name)

    if any(x in name for x in ["廣達", "緯創", "緯穎", "英業達"]):
        return "AI"
    elif any(x in name for x in ["台積", "聯電"]):
        return "半導體"
    elif "光" in name:
        return "矽光子"
    elif any(x in name for x in ["國巨", "電容"]):
        return "被動元件"
    elif any(x in name for x in ["散熱", "風扇"]):
        return "散熱"
    else:
        return "其他"

# ================================
# 🔥 爆量突破
# ================================
def detect_breakout(df):
    if df is None or len(df) < 10:
        return False

    latest = df.iloc[-1]
    avg_vol = df["Trading_Volume"].mean()
    max_price = df["close"].max()

    return (
        latest["Trading_Volume"] > 2 * avg_vol and
        latest["close"] > 0.95 * max_price
    )

# ================================
# 🧠 主力行為（模擬）
# ================================
def detect_main_force(df):
    if df is None or len(df) < 15:
        return False

    df = df.sort_values("date")

    early = df.iloc[:10]
    late = df.iloc[-5:]

    return (
        late["Trading_Volume"].mean() >
        early["Trading_Volume"].mean() * 1.5 and
        late["close"].mean() > early["close"].mean()
    )

# ================================
# ⚠️ 假突破
# ================================
def is_fake_breakout(df):
    if df is None or len(df) < 1:
        return True

    latest = df.iloc[-1]

    upper_shadow = latest["max"] - max(latest["open"], latest["close"])
    body = abs(latest["close"] - latest["open"])

    return upper_shadow > body * 1.5 or latest["close"] < latest["open"]

# ================================
# 🎯 交易策略
# ================================
def trading_signal(df):
    if df is None or len(df) < 20:
        return "NO"

    ma5 = df["close"].rolling(5).mean().iloc[-1]
    ma20 = df["close"].rolling(20).mean().iloc[-1]
    latest = df.iloc[-1]

    if latest["close"] > ma5 > ma20:
        return "BUY"
    elif latest["close"] < ma5:
        return "SELL"
    return "HOLD"

# ================================
# 🚀 主掃描
# ================================
def scan_market():
    print("🚀 掃描市場中...")

    stocks = get_all_stocks()
    signals = []

    for _, row in stocks.iterrows():
        sid = row["stock_id"]
        name = row["stock_name"]

        df = get_price(sid)
        if df is None:
            continue

        if not detect_breakout(df):
            continue

        if not detect_main_force(df):
            continue

        if is_fake_breakout(df):
            continue

        flow = get_flow(sid)
        if flow < 0:
            continue

        signal = trading_signal(df)
        theme = classify_theme(name)

        signals.append({
            "stock": sid,
            "name": name,
            "theme": theme,
            "flow": flow,
            "signal": signal
        })

    result = pd.DataFrame(signals)

    if result.empty:
        print("❌ 無強勢股")
        return

    result = result.sort_values(by="flow", ascending=False)

    print("\n🔥 強勢股：")
    print(result.head(10))

    theme_rank = result.groupby("theme")["flow"].sum()

    msg = "🔥 主力訊號\n\n"
    msg += result.head(5).to_string(index=False) + "\n\n"
    msg += "🔥 題材排行\n" + theme_rank.to_string()

    send_line(msg)

    result.to_csv("hot_stocks.csv", index=False)

# ================================
# ⏰ 排程（盤中用）
# ================================
def run_realtime():
    schedule.every(5).minutes.do(scan_market)

    while True:
        schedule.run_pending()
        time.sleep(1)

# ================================
# ▶️ 執行
# ================================
if __name__ == "__main__":
    scan_market()        # 單次跑
    # run_realtime()     # 開盤用（打開這行）
