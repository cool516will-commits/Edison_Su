import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 設定監控清單 ---
WATCHLIST = {
    "權值指標": ["2330.TW", "2454.TW", "2317.TW"],
    "AI/ASIC": ["3661.TW", "3443.TW", "6526.TW", "2388.TW"],
    "半導體設備": ["8028.TW", "3167.TW", "3055.TW"],
    "匯率指標": ["TWD=X"]
}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="外資資金流向雷達", layout="wide")

# 標題與更新時間顯示
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🏹 外資資金流向即時監控儀表板")
with col_t2:
    st.write(f"🕒 最後更新：{datetime.now().strftime('%H:%M:%S')}")

# --- 3. 資料擷取函數 (加入快取避免被封鎖) ---
@st.cache_data(ttl=300)  # 快取 5 分鐘
def get_data():
    all_tickers = [item for sublist in WATCHLIST.values() for item in sublist]
    # 下載今日 5 分鐘 K 線
    data = yf.download(all_tickers, period="1d", interval="5m", auto_adjust=True)
    # yfinance 下載多個標的會產生 Multi-Index，這裡只取收盤價
    return data['Close']

# --- 4. 主程式邏輯 ---
try:
    df = get_data()

    if df.empty:
        st.warning("目前暫無即時交易數據，請確認是否為開盤時段。")
    else:
        # --- 數據計算 ---
        # 1. 匯率計算：台幣升值 (數值變小) = 資金流入 (綠色利多)
        twd_series = df["TWD=X"].dropna()
        latest_twd = twd_series.iloc[-1]
        twd_change = latest_twd - twd_series.iloc[0]
        is_twd_strong = twd_change < 0

        # 2. 族群漲幅計算
        group_stats = {}
        for group, tickers in WATCHLIST.items():
            if group != "匯率指標":
                # 過濾掉該族群中可能存在的空值，計算今日漲幅
                group_data = df[tickers].dropna(how='all')
                if not group_data.empty:
                    # 計算公式：(現價 / 開盤價 - 1)
                    move = (group_data.iloc[-1] / group_data.iloc[0] - 1).mean() * 100
                    group_stats[group] = move

        # --- UI 呈現 ---
        # 第一排：核心數據卡片
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric(
                label="美金/台幣 (USD/TWD)", 
                value=f"{latest_twd:.3f}", 
                delta=f"{twd_change:.3f} ({'升值' if is_twd_strong else '貶值'})",
                delta_color="inverse"  # 讓數值下降(升值)顯示為綠色
            )

        with c2:
            avg_heavy = group_stats.get("權值指標", 0)
            st.metric("權值股今日平均漲幅", f"{avg_heavy:.2f}%")

        with c3:
            # 信心分數邏輯 (可根據實戰自行調整權重)
            score = 0
            if is_twd_strong: score += 40
            if avg_heavy > 0.5: score += 30
            if group_stats.get("AI/ASIC", 0) > 1.5: score += 30
            
            st.write(f"### 外資進場信心分數：**{score}** / 100")
            st.progress(score / 100)

        st.divider()

        # 第二排：圖表與警報
        chart_col, info_col = st.columns([2, 1])
        
        with chart_col:
            st.subheader("📊 關鍵族群今日漲幅 (1D)")
            chart_df = pd.DataFrame.from_dict(group_stats, orient='index', columns=['漲幅(%)'])
            st.bar_chart(chart_df)

        with info_col:
            st.subheader("🚨 盤勢即時診斷")
            if score >= 70:
                st.success("🔥 **多頭共振**：台幣升值且權值股發力，外資進場意願高。")
            elif score <= 30:
                st.error("⚠️ **資金流出**：匯率承壓或權值股遭拋售，建議保守觀望。")
            else:
                st.info("🔎 **區間震盪**：市場無明顯單一方向，留意個股表現。")

except Exception as e:
    st.error(f"資料處理發生錯誤：{e}")

st.caption("註：本工具僅供參考，數據受 yfinance 延遲限制（約 15 分鐘）。")
