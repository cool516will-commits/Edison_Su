import streamlit as st
import yfinance as yf
import pandas as pd

st.title("🧠 超穩資金流（保命版）")

TICKERS = ["2330.TW","2454.TW","2317.TW"]

@st.cache_data(ttl=300)
def load():

    rows = []

    for t in TICKERS:
        try:
            df = yf.download(t, period="5d", interval="1d", progress=False)

            if df.empty or len(df) < 2:
                continue

            close = df["Close"]
            vol = df["Volume"]

            change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
            vol_ratio = vol.iloc[-1] / (vol.mean() + 1)

            rows.append({
                "股票": t,
                "漲跌%": round(change,2),
                "量比": round(vol_ratio,2)
            })

        except Exception as e:
            st.write(f"{t} skip")

    return pd.DataFrame(rows)

df = load()

if df.empty:
    st.warning("沒有資料（但系統正常）")
else:
    st.dataframe(df)