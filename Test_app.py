import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 配置 ---
st.set_page_config(page_title="智能股市分析工具", layout="wide")

st.title("🤖 智能股市分類與資金流向工具")
st.markdown("我是你的中間分析人：自動抓取市場熱門股，並依據產業題材進行即時分類。")

# 擴大抓取池
SEED_TICKERS = [
    "2330.TW", "2454.TW", "2317.TW", "3661.TW", "3443.TW", "3017.TW", "3324.TW", "6669.TW",
    "1513.TW", "1519.TW", "1503.TW", "6806.TW", "2603.TW", "2609.TW", "2615.TW", "2002.TW", 
    "1301.TW", "2881.TW", "2882.TW", "1760.TW", "6446.TW", "4147.TW", "2308.TW", "2382.TW", "3231.TW"
]

@st.cache_data(ttl=600)
def analyze_and_classify():
    results = []
    # 抓取 5 天數據以確保計算穩定
    data = yf.download(SEED_TICKERS, period="5d", interval="15m", progress=False)
    
    if data.empty:
        return pd.DataFrame()

    for t in SEED_TICKERS:
        try:
            # 獲取個股基本資料
            t_obj = yf.Ticker(t)
            info = t_obj.info
            sector = info.get('sector', '其他題材')
            
            # 產業分類翻譯
            sector_map = {
                "Technology": "💻 科技大熱門",
                "Financial Services": "🏦 金融/保險",
                "Industrials": "⚙️ 工業/重電/航運",
                "Basic Materials": "🧱 基礎原物料",
                "Healthcare": "🧬 生技醫療",
                "Consumer Cyclical": "🛍️ 消費零售"
            }
            theme = sector_map.get(sector, "📁 " + sector)
            
            # 取得價格與成交量 (確保資料長度足夠)
            closes = data['Close'][t].dropna()
            vols = data['Volume'][t].dropna()
            
            if len(closes) > 1:
                change = (closes.iloc[-1] / closes.iloc[-2] - 1) * 100
                # 計算資金強度：漲跌幅度 x 成交量放大率 (當前量 / 平均量)
                vol_ratio = vols.iloc[-1] / vols.mean() if vols.mean() != 0 else 1
                flow_strength = change * vol_ratio
                
                results.append({
                    "題材分類": theme,
                    "股票名稱": info.get('shortName', t),
                    "代碼": t,
                    "今日漲跌(%)": round(change, 2),
                    "資金流向強度": round(flow_strength, 2)
                })
        except:
            continue
    return pd.DataFrame(results)

try:
    with st.spinner("中間人正在分析市場並重新分類..."):
        df_analysis = analyze_and_classify()

    if not df_analysis.empty and '資金流向強度' in df_analysis.columns:
        c1, c2 = st.columns([7, 3])

        with c1:
            st.subheader("📊 市場題材熱度分布")
            # 加上防護：取絕對值來決定區塊大小
            df_analysis['abs_flow'] = df_analysis['資金流向強度'].abs() + 0.1 
            fig = px.treemap(df_analysis, 
                             path=['題材分類', '股票名稱'], 
                             values='abs_flow',
                             color='今日漲跌(%)',
                             color_continuous_scale='RdBu_r',
                             range_color=[-5, 5],
                             hover_data=['代碼', '資金流向強度'])
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("🔥 資金流入排行")
            top_5 = df_analysis.sort_values(by="資金流向強度", ascending=False).head(5)
            for _, row in top_5.iterrows():
                st.success(f"**{row['股票名稱']}** \n\n {row['題材分類']} | 強度: {row['資金流向強度']}")
    else:
        st.info("目前抓取數據不足，請稍候片刻重新整理。")

except Exception as e:
    st.error(f"分析過程遇到突發狀況: {e}")

st.caption