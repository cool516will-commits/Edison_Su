import streamlit as st
import yfinance as yf
import pandas as pd

st.title("🧠 穩定資金流（防炸版）")

TICKERS = ["2330.TW","2454.TW","2317.TW","2603.TW"]

def safe_get(data, key):
    try:
        return data[key].dropna()
    except:
        return None

@st.cache_data(ttl=300)
def load():

    df = yf.download(
        TICKERS,
        period="5d",
        interval="1d",
        group_by="ticker",
        progress=False
    )

    rows = []

    for t in TICKERS:
        try:
            d = safe_get(df, t)

            if d is None or len(d) < 2:
                continue

            close = d["Close"]
            vol = d["Volume"]

            if close.isna().any() or vol.isna().any():
                continue

            change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
            vol_ratio = vol.iloc[-1] / (vol.mean() + 1)

            rows.append({
                "股票": t,
                "漲跌%": round(change,2),
                "量比": round(vol_ratio,2)
            })

        except Exception as e:
            st.write(f"{t} skipped")

    return pd.DataFrame(rows)

df = load()