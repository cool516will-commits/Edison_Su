import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 詳細監控清單 (你可以隨時在這裡增加股票) ---
WATCHLIST = {
    "👑 權值指標 (大盤風向)": ["2330.TW", "2454.TW", "2317.TW"],
    "💻 AI/ASIC (領頭羊)": ["3661.TW", "3443.TW", "6526.TW", "2388.TW", "6669.TW"],
    "🛠️ 半導體設備 (擴產題材)": ["8028.TW", "3167.TW", "3055.TW", "3583.TW"],
    "🔗 散熱/伺服器 (AI硬體)": ["3017.TW", "3324.TW", "2382.TW", "2301.TW"],
    "💵 匯率指標": ["TWD=X"]
}

st.set_page_config(page_title="外資資金流向雷達 2.0", layout="wide")

# 顯示最後更新時間
st.sidebar.write(f"🕒 數據最後更新：{datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=300)
def get_data():
    all_tickers = [item for sublist in WATCHLIST.values() for item in sublist]
    data = yf.download(all_tickers, period="1d", interval="5m", auto_adjust=True)
    return data['Close']

try:
    df = get_data()
    if df.empty:
        st.warning("目前非交易時段或無法取得數據。")
    else:
        # --- 計算匯率 ---
        twd_s = df["TWD=X"].dropna()
        latest_twd = twd_s.iloc[-1]
        twd_change = latest_twd - twd_s.iloc[0]
        is_twd_strong = twd_change < 0

        # --- 計算所有個股漲幅並分類 ---
        all_results = []
        group_avg = {}
        
        for group, tickers in WATCHLIST.items():
            if group == "💵 匯率指標": continue
            
            group_data = df[tickers].dropna(axis=1, how='all')
            if not group_data.empty:
                # 計算該組每支股票的漲幅
                individual_changes = (group_data.iloc[-1] / group_data.iloc[0] - 1) * 100
                for ticker, change in individual_changes.items():
                    all_results.append({"分類": group, "股票代碼": ticker, "今日漲幅(%)": round(change, 2)})
                
                # 計算該組平均
                group_avg[group] = individual_changes.mean()

        # --- UI 呈現：頂部卡片 ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("美金/台幣 (USD/TWD)", f"{latest_twd:.3f}", 
                      f"{twd_change:.3f} ({'升值' if is_twd_strong else '貶值'})", delta_color="inverse")
        with c2:
            st.metric("權值股平均表現", f"{group_avg.get('👑 權值指標 (大盤風向)', 0):.2f}%")
        with c3:
            score = 0
            if is_twd_strong: score += 40
            if group_avg.get('👑 權值指標 (大盤風向)', 0) > 0.5: score += 30
            if any(v > 1.5 for v in group_avg.values()): score += 30
            st.write(f"### 外資進場信心：**{score}** / 100")
            st.progress(score / 100)

        st.divider()

        # --- 詳細圖表分析 ---
        st.subheader("🔍 個股題材詳細漲幅對照圖")
        
        # 整理成 DataFrame 方便畫圖
        plot_df = pd.DataFrame(all_results)
        
        # 使用顏色區分分類，畫出橫向條形圖
        import plotly.express as px # Streamlit 內建支援 plotly
        fig = px.bar(plot_df, 
                     x="今日漲幅(%)", 
                     y="股票代碼", 
                     color="分類",
                     text="今日漲幅(%)",
                     orientation='h',
                     title="各題材成分股即時漲跌狀況",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

        # --- 表格清單 ---
        with st.expander("看詳細數據表格"):
            st.table(plot_df.sort_values(by="今日漲幅(%)", ascending=False))

except Exception as e:
    st.error(f"錯誤報告：{e}")