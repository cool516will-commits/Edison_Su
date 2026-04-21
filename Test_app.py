import streamlit as st
import yfinance as yf
import pandas as pd

st.title("🧠 動態資金流中間智能層")

TICKERS = [
    "2330.TW","2454.TW","2317.TW",
    "2603.TW","2609.TW",
    "2881.TW","2882.TW"
]

def behavior_label(change, vol_ratio):
    if change > 2 and vol_ratio > 1.5:
        return "🚀 爆量強攻"
    elif change > 1:
        return "📈 上攻"
    elif vol_ratio > 1.5:
        return "💰 放量盤整"
    elif change < -1:
        return "📉 走弱"
    else:
        return "➖ 無明顯趨勢"

def cluster_tag(change, vol_ratio):
    score = change * vol_ratio
    if score > 3:
        return "🔥 主流資金族群"
    elif score > 1:
        return "🟡 溫和資金族群"
    elif score > 0:
        return "⚪ 中性族群"
    else:
        return "🔻 被拋售族群"

def market_role(change, vol_ratio):
    if change > 1 and vol_ratio > 1:
        return "領漲股"
    elif vol_ratio > 2:
        return "量先行股"
    elif change > 1:
        return "價格推動股"
    else:
        return "觀望股"

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
            d = df[t].dropna()

            if len(d) < 2:
                continue

            close = d["Close"]
            vol = d["Volume"]

            change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
            vol_ratio = vol.iloc[-1] / (vol.mean() + 1)

            rows.append({
                "股票": t,
                "動能": behavior_label(change, vol_ratio),
                "資金族群": cluster_tag(change, vol_ratio),
                "市場角色": market_role(change, vol_ratio),
                "漲跌%": round(change,2),
                "量比": round(vol_ratio,2)
            })

        except:
            continue

    return pd.DataFrame(rows)

df = load()

st.dataframe(df, use_container_width=True)

st.subheader("🧠 解讀結果")

for _, r in df.iterrows():
    st.markdown(f"""
### {r['股票']}
- 動能：{r['動能']}
- 資金：{r['資金族群']}
- 角色：{r['市場角色']}
- 漲跌：{r['漲跌%']}%
""")