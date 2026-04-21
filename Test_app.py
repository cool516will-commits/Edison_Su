import streamlit as st
from FinMind.data import DataLoader
import pandas as pd

st.title("簡化版資金流")

api = DataLoader()
api.login_by_token(api_token="你的token")

stocks = ["2330","2454","2317"]

rows = []

for s in stocks:
    try:
        df = api.taiwan_stock_daily(
            stock_id=s,
            start_date="2025-01-01"
        )

        df = df.sort_values("date")

        close = df["close"]

        change = (close.iloc[-1] / close.iloc[-2] - 1) * 100

        rows.append({
            "股票": s,
            "漲跌%": round(change,2)
        })

    except:
        st.write(f"{s} error")

st.dataframe(pd.DataFrame(rows))