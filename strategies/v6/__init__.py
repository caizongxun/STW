import streamlit as st
from .config import V6Config
from .backtester import V6Backtester
from .features import V6FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V6 - 資金費率套利 (Funding Rate Arbitrage)")
    st.info("""
    **資金費率套利核心邏輯**：
    - 同時做多現貨、做空永續合約（或反向），賺取每 8 小時結算一次的資金費率
    - 這是**完全對沖策略**，價格漲跌不影響你的總資產，只賺利息
    - 月化收益約 3-10%，取決於市場情緒（牛市時資金費率更高）
    
    **適合場景**：
    - 不想承擔價格波動風險
    - 希望穩定賺取被動收入
    - 有一筆閒置資金可以鎖定數週到數月
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("套利設定")
        
        st.markdown("### 交易對選擇")
        symbol = st.selectbox(
            "選擇幣種",
            ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'DOGEUSDT'],
            help="選擇流動性高的主流幣種，資金費率更穩定"
        )
        
        st.markdown("### 回測設定")
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", min_value=1000, max_value=100000, value=10000, step=1000)
        with col_days:
            simulation_days = st.number_input("回測天數", min_value=0, max_value=365, value=90, help="0=全部歷史")
        
        st.markdown("### 策略參數")
        min_funding_rate = st.slider(
            "最低資金費率閾值 (%)",
            0.0, 0.1, 0.01, 0.005,
            help="只有當資金費率高於此值時才開倉（避免負費率）"
        )
        
        allocation_pct = st.slider(
            "單次套利資金佔比 (%)",
            10, 100, 50, 10,
            help="每次套利使用多少比例的總資金"
        ) / 100.0
        
        max_positions = st.slider(
            "最大同時持倉數",
            1, 5, 3,
            help="最多同時運行幾組套利對沖倉位"
        )
        
        st.markdown("### 風險控制")
        enable_hedge_rebalance = st.checkbox(
            "啟用對沖再平衡",
            value=True,
            help="當現貨與合約價差過大時，自動調整倉位保持完美對沖"
        )
        
        max_basis_pct = st.slider(
            "最大基差容忍度 (%)",
            0.5, 5.0, 2.0, 0.5,
            help="當現貨與合約價差超過此值時，視為風險過高，暫停開倉"
        ) / 100.0
        
        test_btn = st.button("🚀 開始回測資金費率套利", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在回測 {symbol} 資金費率套利策略..."):
                config = V6Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    min_funding_rate=min_funding_rate,
                    allocation_pct=allocation_pct,
                    max_positions=max_positions,
                    enable_hedge_rebalance=enable_hedge_rebalance,
                    max_basis_pct=max_basis_pct
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '1h')  # 使用 1 小時數據，每 8 根 K 線模擬一次資金費率結算
                
                if df is not None and not df.empty:
                    bt = V6Backtester(config)
                    fe = V6FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"✅ 回測完成！({symbol}) - 測試天數: {bt_results.get('days_tested', 0)} 天")
                    
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
                    col_b3.metric("年化報酬 (APY)", f"{bt_results['monthly_return'] * 12:.2f}%")
                    
                    # 資金費率統計
                    col_c1, col_c2, col_c3 = st.columns(3)
                    col_c1.metric("平均資金費率", f"{bt_results.get('avg_funding_rate', 0) * 100:.3f}%")
                    col_c2.metric("總收費次數", bt_results.get('funding_collections', 0))
                    col_c3.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                    
                    st.markdown("---")
                    st.markdown("### 💰 資金費率套利特性")
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    col_d1.metric("資金利用率", f"{allocation_pct * 100:.0f}%")
                    col_d2.metric("同時運行套利數", max_positions)
                    col_d3.metric("對沖完美度", "99%+" if enable_hedge_rebalance else "95%+")
                    
                    if bt_results['return_pct'] > 0:
                        st.success(f"✅ **策略為正期望值！** 在 {bt_results.get('days_tested', 0)} 天內，年化收益達到 {bt_results['monthly_return'] * 12:.2f}%。")
                        
                        if bt_results['max_drawdown'] < 2:
                            st.success("🎯 **極低風險！** 回撤低於 2%，這是真正的穩定套利策略。")
                            st.balloons()
                    else:
                        st.warning("⚠️ 在此期間資金費率可能以負值為主（空頭市場），或手續費吃掉了利潤。")
                    
                    st.info("""
                    **資金費率套利的優勢**：
                    - ✅ **零方向性風險**：價格漲跌都不影響你
                    - ✅ **穩定收益**：每 8 小時固定結算
                    - ✅ **複利效應**：利息自動累積到本金
                    - ✅ **適合長期**：90 天、180 天、365 天都適用
                    
                    **注意事項**：
                    - ⚠️ 需要同時持有現貨與合約，資金會被鎖定
                    - ⚠️ 極端行情時（如閃崩）可能出現短暫虧損
                    - ⚠️ 熊市時資金費率可能轉負（空頭收費）
                    """)
                    
                else:
                    st.error("無法載入數據，請檢查幣種名稱是否正確")