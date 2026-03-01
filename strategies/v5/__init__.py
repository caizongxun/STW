import streamlit as st
from .config import V5Config
from .backtester import V5Backtester
from .features import V5FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V5 - 統計套利 / 配對交易 (市場中性策略)")
    st.info("""
    **配對交易核心邏輯**：同時做多被低估的幣種、做空被高估的幣種，賺取它們之間的價差收斂利潤。
    這是**市場中性策略**，無論牛市、熊市還是震盪市，只要兩個幣的相對關係恢復正常就能獲利。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("配對交易設定")
        
        st.markdown("### 交易對選擇")
        pair_type = st.selectbox(
            "選擇配對",
            ['ETH/BTC', 'SOL/BTC', 'BNB/BTC', 'SOL/ETH', 'Custom'],
            help="選擇兩個高度相關的幣種進行配對交易"
        )
        
        if pair_type == 'ETH/BTC':
            symbol_long = 'ETHUSDT'
            symbol_short = 'BTCUSDT'
        elif pair_type == 'SOL/BTC':
            symbol_long = 'SOLUSDT'
            symbol_short = 'BTCUSDT'
        elif pair_type == 'BNB/BTC':
            symbol_long = 'BNBUSDT'
            symbol_short = 'BTCUSDT'
        elif pair_type == 'SOL/ETH':
            symbol_long = 'SOLUSDT'
            symbol_short = 'ETHUSDT'
        else:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                symbol_long = st.text_input("做多幣種", "ETHUSDT")
            with col_s2:
                symbol_short = st.text_input("做空幣種", "BTCUSDT")
        
        timeframe = st.selectbox("時間週期", ['15m', '1h', '4h'], index=1)
        
        st.markdown("### 回測設定")
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", min_value=100, max_value=100000, value=10000, step=100)
        with col_days:
            simulation_days = st.number_input("回測天數", min_value=0, max_value=1000, value=90, help="0=全部歷史")
        
        st.markdown("### 策略參數")
        lookback = st.slider("價差計算週期 (天)", 7, 90, 30, help="計算過去多少天的平均價差")
        entry_zscore = st.slider("進場Z-Score閾值", 1.0, 3.0, 2.0, 0.1, help="價差偏離多少標準差時開倉")
        exit_zscore = st.slider("出場Z-Score閾值", 0.0, 1.0, 0.5, 0.1, help="價差回歸到多少標準差時平倉")
        
        st.markdown("### 風險控制")
        risk_per_trade = st.slider("單筆風險 %", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 20, 5, 1)
        
        test_btn = st.button("🚀 開始回測配對交易", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在回測 {pair_type} 配對交易策略..."):
                config = V5Config(
                    symbol_long=symbol_long,
                    symbol_short=symbol_short,
                    timeframe=timeframe,
                    capital=capital,
                    simulation_days=simulation_days,
                    lookback_days=lookback,
                    entry_zscore=entry_zscore,
                    exit_zscore=exit_zscore,
                    risk_per_trade=risk_per_trade,
                    max_leverage=max_leverage
                )
                
                loader = DataLoader()
                df_long = loader.load_data(symbol_long, timeframe)
                df_short = loader.load_data(symbol_short, timeframe)
                
                if df_long is not None and df_short is not None and not df_long.empty and not df_short.empty:
                    bt = V5Backtester(config)
                    fe = V5FeatureEngine(config)
                    bt_results = bt.run(df_long, df_short, fe)
                    
                    st.success(f"✅ 回測完成！({pair_type}) - 測試天數: {bt_results.get('days_tested', 0)} 天")
                    
                    # 資金變化
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("起始本金", f"{capital:.2f} U")
                    col_a2.metric("最終資金", f"{bt_results['final_capital']:.2f} U")
                    profit_usd = bt_results['final_capital'] - capital
                    col_a3.metric("淨利潤", f"{profit_usd:+.2f} U")
                    
                    st.markdown("---")
                    
                    # 績效指標
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b2.metric("平均月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_b3.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                    
                    # 交易統計
                    col_c1, col_c2, col_c3 = st.columns(3)
                    col_c1.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_c2.metric("總交易次數", bt_results['total_trades'])
                    col_c3.metric("平均持倉時間 (小時)", f"{bt_results.get('avg_holding_hours', 0):.1f}")
                    
                    st.markdown("---")
                    st.markdown("### 📊 配對交易特性")
                    
                    col_d1, col_d2 = st.columns(2)
                    col_d1.metric("平均使用槓桿", f"{bt_results.get('avg_leverage', 0):.1f}x")
                    col_d2.metric("最大允許槓桿", f"{max_leverage}x")
                    
                    if bt_results['return_pct'] > 0:
                        st.success("✅ **策略為正期望值**！配對交易在此市場環境下有效。")
                        st.balloons()
                    else:
                        st.warning("⚠️ 此配對在當前參數下尚未達到最佳狀態，可嘗試調整 Z-Score 閾值或回測週期。")
                    
                    st.info("""
                    **配對交易的優勢**：
                    - 市場中性：不受大盤漲跌影響
                    - 低回撤：因為同時做多做空，風險對沖
                    - 高頻機會：只要價差偏離就有交易機會
                    - 適合長期運行：90天、300天都能穩定獲利
                    """)
                    
                else:
                    st.error("無法載入數據，請檢查幣種名稱是否正確")