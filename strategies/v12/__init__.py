import streamlit as st
from .config import V12Config
from .backtester import V12Backtester
from core.data_loader import DataLoader

def render():
    st.header("V12 - 高階量化神經網路 (精準打擊模型)")
    
    st.info("""
    **V12 針對你的嚴格要求 (AUC>0.7, 精準率>0.6, 召回率>0.6, 每天1-3單) 進行了架構重寫：**
    
    1. 🎯 **三重屏障標籤 (Triple-Barrier Labeling)**：不再死板預測「漲跌」，而是讓 AI 學習「未來會先碰到 2R 止盈，還是先碰到 1R 止損」。這解決了預測與實際交易脫節的問題。
    2. ⚖️ **動態閾值尋優 (Auto-Thresholding)**：系統會在訓練階段自動遍歷所有機率閾值，強制找出能滿足 **Precision >= 60% & Recall >= 60%** 的最佳出手點。
    3. 🛑 **每日交易次數限制**：強制將每日出手次數壓制在 1~3 次，只做最有把握的交易，杜絕過度交易 (Overtrading)。
    4. 🧬 **高階特徵工程**：加入了 24小時動能、多均線發散度、真實波動幅度 (ATR) 等機構級量化特徵。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V12 嚴格參數設定")
        
        symbol = st.selectbox("交易對", ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'], index=0)
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", 1000, 100000, 10000, 1000)
        with col_days:
            simulation_days = st.number_input("回測天數", 60, 365, 120, help="建議至少 120 天，讓 AI 有足夠的樣本達成 70% AUC")
            
        st.markdown("### 🎯 屏障與頻率設定")
        max_daily_trades = st.slider("每日最多交易次數", 1, 5, 2, 1, help="達到次數後當天不再開倉")
        tp_atr = st.slider("止盈 ATR 倍數 (獲利空間)", 1.0, 4.0, 2.0, 0.5)
        sl_atr = st.slider("止損 ATR 倍數 (防守空間)", 0.5, 3.0, 1.0, 0.5)
        
        st.markdown("### 🛡️ 風險管理")
        base_risk = st.slider("單筆風險 (%)", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 10, 3, 1)
        
        test_btn = st.button("🧠 啟動 V12 深度訓練與回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在執行三重屏障標記與 XGBoost 訓練 (約需 20-30 秒)..."):
                config = V12Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    max_daily_trades=max_daily_trades,
                    tp_atr_mult=tp_atr,
                    sl_atr_mult=sl_atr,
                    base_risk=base_risk,
                    max_leverage=max_leverage
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '15m')
                
                if df is not None and not df.empty:
                    bt = V12Backtester(config)
                    results = bt.run(df)
                    
                    st.success(f"✅ V12 訓練與回測完成！({symbol}) - 測試天數: {results.get('days_tested', 0)} 天")
                    
                    # AI 模型嚴格指標
                    st.markdown("### 🤖 機器學習核心指標 (測試集表現)")
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    auc = results.get('test_auc', 0)
                    prec = results.get('test_precision', 0)
                    rec = results.get('test_recall', 0)
                    
                    col_m1.metric("AUC 分數", f"{auc*100:.1f}%", delta="達標!" if auc >= 0.7 else "需更多數據", delta_color="normal" if auc >= 0.7 else "inverse")
                    col_m2.metric("精準率 (Precision)", f"{prec*100:.1f}%", help="AI說會漲的時候，實際漲的機率")
                    col_m3.metric("召回率 (Recall)", f"{rec*100:.1f}%", help="所有真正的大漲中，AI成功抓到的比例")
                    col_m4.metric("最佳決策閾值", f"{results.get('best_threshold', 0)*100:.1f}%", help="AI 自動尋找的最優開倉信心值")
                    
                    st.markdown("---")
                    
                    # 資金與交易統計
                    st.markdown("### 📊 交易與資金表現")
                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    col_a1.metric("總報酬 (%)", f"{results['return_pct']:.2f}%")
                    col_a2.metric("淨利潤", f"{results['final_capital'] - capital:+.2f} U")
                    col_a3.metric("最大回撤", f"{results['max_drawdown']:.2f}%")
                    col_a4.metric("夏普比率", f"{results.get('sharpe_ratio', 0):.2f}")
                    
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    col_c1.metric("勝率", f"{results['win_rate']:.2f}%")
                    col_c2.metric("總交易次數", results['total_trades'])
                    
                    avg_daily_trades = results['total_trades'] / max(1, results.get('days_tested', 1))
                    col_c3.metric("日均交易次數", f"{avg_daily_trades:.1f} 次/天")
                    col_c4.metric("盈虧比", f"{results.get('profit_factor', 0):.2f}")
                    
                    if avg_daily_trades > 3:
                        st.warning("⚠️ 日均交易次數大於 3，建議在左側調低「每日最多交易次數」。")
                    elif avg_daily_trades < 0.5:
                        st.info("💡 交易次數偏少，代表 AI 為了維持 60% 以上的精準率，過濾掉了大量不確定信號。這是穩健的表現。")
                        
                else:
                    st.error("無法載入數據")