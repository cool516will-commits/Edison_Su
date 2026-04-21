import streamlit as st
import pandas as pd

st.title("📱 Streamlit 正常測試")

df = pd.DataFrame({
    "股票": ["2330", "2454", "2317"],
    "漲跌%": [1.2, -0.5, 2.3]
})

st.dataframe(df)

st.success("✅ Streamlit 已正常運作")