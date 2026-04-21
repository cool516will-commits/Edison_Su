import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="資金流App",
    layout="wide"
)

# 🔄 每60秒自動刷新
st.markdown(
    """
    <meta http-equiv="refresh" content="60">
    """,
    unsafe_allow_html=True
)

st.title("📱 台股資金流雷達")

api = DataLoader()
api.login_by_token(api_token="你的token")

TICKERS = ["2330","2454","2317","2603","2609","2881","2882"]

SECTOR = {
    "2330":"半導體","2454":"IC設計","2317":"電子代工",
    "2603":"航運","2609":"航運",
    "2881":"金融","2882":"金融"
}

@st.cache_data(ttl=300)
def fetch_data():
    rows = []

    for t in TICKERS:
        try:
            df = api.taiwan_stock_daily(
                stock_id=t,
                start_date="2026-01-01"
            )

            if df.empty or len(df) < 5:
                continue

            df = df.sort_values("date")

            close = df["close"]
            vol = df["Trading_Volume"]

            change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
            vol_ratio = vol.iloc[-1] / (vol.tail(5).mean() + 1)
            flow = change * (vol_ratio ** 0.4)

            rows.append({
                "股票": t,
                "族群": SECTOR.get(t,"其他"),
                "漲跌%": round(change,2),
                "資金強度": round(flow,2)
            })

        except:
            continue

    return pd.DataFrame(rows)

df = fetch_data()

# ========================
# 📊 UI 手機優化
# ========================
if not df.empty:

    df = df.sort_values(by="資金強度", ascending=False)

    # 🔥 TOP3（像 App 首頁）
    st.subheader("🔥 今日最強")
    top3 = df.head(3)

    for _, row in top3.iterrows():
        st.markdown(f"""
        ### {row['股票']} ({row['族群']})
        漲跌：**{row['漲跌%']}%**  
        資金：**{row['資金強度']}**
        ---
        """)

    # 📊 題材資金
    st.subheader("📊 題材熱度")
    sector_flow = df.groupby("族群")["資金強度"].sum()
    st.bar_chart(sector_flow)

    # 📋 全部排行（可滑）
    st.subheader("📋 全市場排行")
    st.dataframe(df, use_container_width=True)

else:
    st.error("抓不到資料")

st.caption(f"更新時間：{datetime.now().strftime('%H:%M:%S')}")