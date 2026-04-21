import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 設定監控清單
WATCHLIST = {
    "權值指標": ["2330.TW", "2454.TW", "2317.TW"],
    "AI/ASIC": ["3661.TW", "3443.TW", "6526.TW", "2388.TW"],
    "半導體設備": ["8028.TW", "3167.TW", "3055.TW"],
    "匯率指標": ["TWD=X"]
}

st.set_page_config(page_title="外資資金流向雷達", layout="wide")

# 頁面標題與最後更新時間
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🏹 外資資金流向即時監控儀表板")
with col_t2:
    st.write(f"最後更新：{datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=300) # 快取 5 分鐘，避免頻繁請求被 yfinance 封鎖
def get_data():
    all_tickers = [item for sublist in WATCHLIST.values() for item in sublist]
    # 使用 auto_adjust 確保獲取正確收盤價
    data = yf.download(all_tickers, period="1d", interval="5m", auto_adjust=True)
    return data['Close']

try:
    df = get_data()
    
    # 檢查資料是否完整
    if df.empty:
        st.warning("目前非交易時段或無法取得即時數據。")
    else:
        # 1. 匯率邏輯
        twd_price = df["TWD=X"].dropna()
        latest_twd = twd_price.iloc[-1]
        open_twd = twd_price.iloc[0]
        twd_change = latest_twd - open_twd
        # 升值 (數值下降) 為利多
        is_twd_strong = twd_change < 0 

        # 2. 族群漲幅計算
        group_stats = {}
        for group, tickers in WATCHLIST.items():
            if group != "匯率指標":
                # 剔除 NaN 避免計算錯誤
                group_data = df[tickers].dropna(how='all')
                if not group_data.empty:
                    # 計算今日區間漲幅
                    move = (group_data.iloc[-1] / group_data.iloc[0] - 1).mean() * 100
                    group_stats[group] = move

        # 3. 核心指標呈現
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # 匯率：delta 顯示負數（升值）時呈現綠色(利多)
            st.metric("美金/台幣 (USD/TWD)", 
                      f"{latest_twd:.3f}", 
                      f"{twd_change:.3f} {'(升值)' if is_twd_strong else '(貶值)'}",
                      delta_color="inverse") 

        with c2:
            avg_heavy = group_stats.get("權值指標", 0)
            st.metric("權值指標平均漲跌", f"{avg_heavy:.2f}%", delta_color="normal")

        with c3:
            # 信心分數算法優化
            score = 0
            if is_twd_strong: score += 40
            if group_stats.get("權值指標", 0) > 0.5: score += 30
            if group_stats.get("AI/ASIC", 0) > 1.5: score += 30
            
            # 使用進度條顯示信心
            st.write(f"**外資進場信心分數：{score} / 100**")
            st.progress(score / 100)

        st.divider()

        # 4. 視覺化圖表
        chart_col, info_col = st.columns([2, 1])
        
        with chart_col:
            st.subheader("📊 關鍵族群今日漲幅排行")
            chart_df = pd.DataFrame.from_dict(group_stats, orient='index', columns=['漲幅(%)'])
            st.bar_chart(chart_df)

        with info_col:
            st.subheader("💡 盤勢分析")
            if score >= 70:
                st.success("🔥 **強力偏多**：匯率助攻且大型股帶頭，適合尋找強勢股切入。")
            elif score <= 30:
                st.error("⚠️ **資金退潮**：台幣貶值且權值股疲軟，建議保留現金或避險。")
            else:
                st.info("🔎 **震盪整理**：資金無明顯方向，以個股表現為主。")

except Exception as e:
    st.error(f"系統錯誤：{e}")

st.caption("數據來源：Yahoo Finance (延遲約 15 分鐘)。請勿將此作為唯一投資依據。")
