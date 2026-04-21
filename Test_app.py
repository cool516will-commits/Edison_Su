import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 台股資金流簡化版")

TICKERS = [
    "2330.TW","2454.TW","2317.TW",
    "2603.TW","2609.TW",
    "2881.TW","2882.TW"
]

SECTOR = {
    "2330":"半導體","2454":"IC設計","2317":"電子代工",
    "2603":"航運","2609":"航運",
    "2881":"金融","2882":"金融"
}

@st.cache_data(ttl=600)
def get_data():

    df = yf.download(
        TICKERS,
        period="5d",
        interval="1d",
        group_by="ticker",
        progress=False
    )

    result = []

    for t in TICKERS:
        try:
            data = df[t].dropna()

            if len(data) < 2:
                continue

            close = data["Close"]
            vol = data["Volume"]

            # 📈 漲跌
            change = (close.iloc[-1] / close.iloc[-2] - 1) * 100

            # 📊 量能強度
            vol_ratio = vol.iloc[-1] / (vol.mean() + 1)

            # 💰 簡化資金流
            flow = change * (vol_ratio ** 0.3)

            result.append({
                "股票": t,
                "族群": SECTOR.get(t,"其他"),
                "漲跌%": round(change,2),
                "資金強度": round(flow,2)
            })

        except:
            continue

    return pd.DataFrame(result)

df = get_data()

if not df.empty:

    st.subheader("🔥 資金強度排行")

    df = df.sort_values("資金強度", ascending=False)
    st.dataframe(df, use_container_width=True)

    st.subheader("📊 題材資金分布")

    sector = df.groupby("族群")["資金強度"].sum()

    st.bar_chart(sector)

    st.subheader("🚀 強勢股")

    strong = df[df["資金強度"] > 1]

    for _, row in strong.iterrows():
        st.success(f"{row['股票']} | {row['族群']} | {row['資金強度']}")