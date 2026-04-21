import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🔥 市場資金流 + 題材雷達 (穩定版)")

TICKERS = [
    "2330.TW","2454.TW","2317.TW","2308.TW","2382.TW",
    "2603.TW","2609.TW","2615.TW",
    "2881.TW","2882.TW"
]

SECTOR = {
    "2330.TW":"半導體","2454.TW":"IC設計","2317.TW":"電子代工",
    "2308.TW":"半導體","2382.TW":"電子代工",
    "2603.TW":"航運","2609.TW":"航運","2615.TW":"航運",
    "2881.TW":"金融","2882.TW":"金融"
}

@st.cache_data(ttl=300)
def get_data():
    df = yf.download(TICKERS, period="2d", interval="5m", progress=False)
    return df

def analyze(df):
    results = []

    for t in TICKERS:
        try:
            close = df['Close'][t].dropna()
            vol = df['Volume'][t].dropna()

            if len(close) < 20:
                continue

            # 🔹 漲跌動能（避免太短）
            change = (close.iloc[-1] / close.iloc[-10] - 1) * 100

            # 🔹 均量比（平滑）
            vol_ratio = vol.iloc[-1] / (vol.rolling(20).mean().iloc[-1] + 1)

            # 🔹 短期趨勢（5MA vs 20MA）
            ma5 = close.rolling(5).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]

            trend_score = 1 if ma5 > ma20 else -1

            # 🔥 主力資金強度（穩定版）
            flow = change * (vol_ratio ** 0.5) * trend_score

            # 🚀 飆股雷達條件
            breakout = (
                change > 1.5 and
                vol_ratio > 1.2 and
                close.iloc[-1] > close.rolling(20).max().iloc[-2]
            )

            results.append({
                "股票": t,
                "族群": SECTOR.get(t,"其他"),
                "漲跌%": round(change,2),
                "量比": round(vol_ratio,2),
                "資金強度": round(flow,2),
                "飆股": "🚀" if breakout else ""
            })

        except Exception as e:
            continue

    return pd.DataFrame(results)

df_raw = get_data()
df = analyze(df_raw)

# =========================
# 📊 題材資金群聚（重點）
# =========================
if not df.empty:

    st.subheader("📊 題材資金集中度")

    sector_flow = df.groupby("族群")["資金強度"].sum().reset_index()

    fig = px.bar(sector_flow, x="族群", y="資金強度")
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # 🔥 飆股雷達
    # =========================
    st.subheader("🚀 飆股雷達")

    hot = df[df["飆股"]=="🚀"].sort_values(by="資金強度", ascending=False)

    if not hot.empty:
        for _, row in hot.iterrows():
            st.success(f"{row['股票']} | {row['族群']} | 強度 {row['資金強度']}")
    else:
        st.info("目前沒有明顯飆股訊號")

    # =========================
    # 💰 資金排行
    # =========================
    st.subheader("💰 主力資金排行")

    top = df.sort_values(by="資金強度", ascending=False).head(5)

    for _, row in top.iterrows():
        st.write(f"{row['股票']} | {row['族群']} | {row['資金強度']}")
