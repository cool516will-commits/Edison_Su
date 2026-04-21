import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 配置 ---
st.set_page_config(page_title="AI 股市分類工具", layout="wide")

st.title("🤖 智能股市分類與資金流向工具")
st.markdown("我是你的中間分析人：自動抓取市場熱門股，並依據產業題材進行即時分類。")

# 1. 建立一個較大的「自動抓取池」(涵蓋台灣各產業指標股)
# 這樣你不用手動管 50 強，我會自動從這裡面挑選「有資金流進」的出來
SEED_TICKERS = [
    # AI/半導體
    "2330.TW", "2454.TW", "2317.TW", "3661.TW", "3443.TW", "3017.TW", "3324.TW", "6669.TW",
    # 綠能/重電
    "1513.TW", "1519.TW", "1503.TW", "6806.TW",
    # 航運/傳統
    "2603.TW", "2609.TW", "2615.TW", "2002.TW", "1301.TW",
    # 金融/生技
    "2881.TW", "2882.TW", "1760.TW", "6446.TW", "4147.TW"
]

@st.cache_data(ttl=600)
def analyze_and_classify():
    results = []
    # 抓取數據
    data = yf.download(SEED_TICKERS, period="2d", interval="15m")
    
    for t in SEED_TICKERS:
        try:
            ticker_info = yf.Ticker(t)
            # 中間人分析：取得產業資訊 (Sector)
            sector = ticker_info.info.get('sector', '其他題材')
            # 翻譯產業類別
            sector_map = {
                "Technology": "💻 科技大熱門",
                "Financial Services": "🏦 金融/保險",
                "Industrials": "⚙️ 工業/重電/航運",
                "Basic Materials": "🧱 基礎原物料",
                "Healthcare": "🧬 生技醫療"
            }
            theme = sector_map.get(sector, sector)
            
            close = data['Close'][t].dropna()
            vol = data['Volume'][t].dropna()
            
            if not close.empty:
                change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
                # 資金流向強度 = 漲幅 * 當前量能對比平均量的倍數
                flow_strength = change * (vol.iloc[-1] / vol.mean())
                
                results.append({
                    "題材分類": theme,
                    "股票名稱": ticker_info.info.get('shortName', t),
                    "代碼": t,
                    "今日漲跌(%)": round(change, 2),
                    "資金流向強度": round(flow_strength, 2)
                })
        except:
            continue
    return pd.DataFrame(results)

try:
    with st.spinner("中間人正在分析市場數據並進行分類..."):
        df_analysis = analyze_and_classify()

    # --- UI 呈現 ---
    c1, c2 = st.columns([7, 3])

    with c1:
        st.subheader("📊 市場題材熱度分布")
        # 使用 Treemap (樹狀圖) 呈現分類，面積越大代表資金流入越多
        fig = px.treemap(df_analysis, 
                         path=['題材分類', '股票名稱'], 
                         values=df_analysis['資金流向強度'].abs(),
                         color='今日漲跌(%)',
                         color_continuous_scale='RdBu_r',
                         hover_data=['代碼', '資金流向強度'])
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🔥 資金流入前五名")
        top_5 = df_analysis.sort_values(by="資金流向強度", ascending=False).head(5)
        for _, row in top_5.iterrows():
            st.success(f"**{row['股票名稱']}** ({row['題材分類']}) \n\n 強度：{row['資金流向強度']}")

    st.divider()

    # --- 分類工具區 ---
    st.subheader("📂 依產業題材過濾")
    selected_sector = st.multiselect("選擇你想關注的分類：", df_analysis['題材分類'].unique())
    if selected_sector:
        st.dataframe(df_analysis[df_analysis['題材分類'].isin(selected_sector)], use_container_width=True)
    else:
        st.dataframe(df_analysis, use_container_width=True)

except Exception as e:
    st.error(f"分析過程中發生錯誤: {e}")

st.caption