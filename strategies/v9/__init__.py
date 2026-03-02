import streamlit as st
from .config import V9Config
from .backtester import V9Backtester
from core.data_loader import DataLoader

def render():
    st.header("V9 - 趨勢回調狙擊手 (Partial TP)")
    
    st.info("""
    **V9 核心特性**：
    - 🎯 **分批止盈**：達到 1R 時平倉 50%，止損移到保本
    - 📈 **趨勢回調進場**：只在多頭趨勢的回調時進場
    - 🛡️ **保本止損**：首次止盈後，剩餘倉位永不虧損
    - 💰 **高勝率設計**：目標勝率 60%+，盈虧比 1.5+
    
    **適用場景**：
    - 趨勢明確的市場環境
    - 波動率適中的主流幣種
    - 目標月化 20-40%
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V9 設定")
        
        symbol = st.selectbox("交易對", ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", 1000, 100000, 10000, 1000)
        with col_days:
            simulation_days = st.number_input("回測天數", 30, 180, 60)
        
        st.markdown("### 進場設定")
        rsi_threshold = st.slider("RSI 超賣閾值", 25, 40, 35, 5)
        pullback_to_ema = st.selectbox("回調目標", ['EMA20', 'EMA50'], index=1)
        
        st.markdown("### 出場設定")
        tp1_r = st.slider("第一止盈 (R)", 0.5, 2.0, 1.0, 0.1)
        tp2_r = st.slider("第二止盈 (R)", 1.5, 4.0, 2.5, 0.5)
        partial_tp_pct = st.slider("首次止盈平倉比例 (%)", 30, 70, 50, 10) / 100.0
        
        st.markdown("### 風險管理")
        base_risk = st.slider("基礎風險 (%)", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 5, 3, 1)
        atr_multiplier = st.slider("止損 ATR 倍數", 0.5, 3.0, 1.5, 0.1)
        
        test_btn = st.button("🚀 開始 V9 回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在加載 {symbol} 數據..."):
                config = V9Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    rsi_threshold=rsi_threshold,
                    pullback_to_ema=pullback_to_ema,
                    tp1_r=tp1_r,
                    tp2_r=tp2_r,
                    partial_tp_pct=partial_tp_pct,
                    base_risk=base_risk,
                    max_leverage=max_leverage,
                    atr_multiplier=atr_multiplier
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '15m')
                
                if df is not None and not df.empty:
                    st.info("📋 正在回測 V9 策略...")
                    bt = V9Backtester(config)
                    results = bt.run(df)
                    
                    st.success(f"✅ 回測完成！({symbol}) - 測試天數: {results.get('days_tested', 0)} 天")
                    
                    # 資金變化
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("起始本金", f"{capital:.2f} U")
                    col_a2.metric("最終資金", f"{results['final_capital']:.2f} U",
                                  delta=f"+{(results['final_capital']/capital - 1)*100:.1f}%")
                    profit_usd = results['final_capital'] - capital
                    col_a3.metric("淨利潤", f"{profit_usd:+.2f} U")
                    
                    st.markdown("---")
                    
                    # 績效指標
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    col_b1.metric("總報酬 (%)", f"{results['return_pct']:.2f}%")
                    monthly_return = results['monthly_return']
                    col_b2.metric("月化報酬", f"{monthly_return:.2f}%")
                    col_b3.metric("最大回撤", f"{results['max_drawdown']:.2f}%")
                    col_b4.metric("夏普比率", f"{results.get('sharpe_ratio', 0):.2f}")
                    
                    # 交易統計
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    col_c1.metric("勝率", f"{results['win_rate']:.2f}%")
                    col_c2.metric("總交易", results['total_trades'])
                    col_c3.metric("平均持倉(h)", f"{results.get('avg_holding_hours', 0):.1f}")
                    col_c4.metric("盈虧比", f"{results.get('profit_factor', 0):.2f}")
                    
                    # 分批止盈統計
                    if 'partial_tp_stats' in results:
                        st.markdown("---")
                        st.markdown("### 📊 分批止盈統計")
                        stats = results['partial_tp_stats']
                        
                        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                        col_d1.metric("觸發 TP1 次數", stats.get('tp1_count', 0))
                        col_d2.metric("觸發 TP2 次數", stats.get('tp2_count', 0))
                        col_d3.metric("保本出場次數", stats.get('breakeven_count', 0))
                        col_d4.metric("止損次數", stats.get('sl_count', 0))
                        
                        st.info(f"""
                        **分批止盈效果分析**：
                        - {stats.get('tp1_count', 0)} 筆交易達到了 TP1 ({tp1_r}R)，鎖定了 {partial_tp_pct*100:.0f}% 倉位的利潤
                        - 其中 {stats.get('tp2_count', 0)} 筆交易讓剩餘倉位達到了 TP2 ({tp2_r}R)
                        - {stats.get('breakeven_count', 0)} 筆交易在 TP1 後觸發保本止損（不賺不賠）
                        - 只有 {stats.get('sl_count', 0)} 筆交易直接止損（未達到 TP1）
                        """)
                    
                    # 結果評估
                    if monthly_return >= 20 and results['win_rate'] >= 55:
                        st.success(f"🎉 **優秀表現！** 月化 {monthly_return:.1f}%，勝率 {results['win_rate']:.1f}%")
                        if results['max_drawdown'] < 15:
                            st.success("✅ 回撤控制良好，可以考慮實盤。")
                            st.balloons()
                    elif monthly_return >= 10:
                        st.info(f"📊 月化報酬 {monthly_return:.1f}%，表現尚可。")
                    else:
                        st.warning(f"⚠️ 月化報酬 {monthly_return:.1f}% 未達預期。")
                    
                else:
                    st.error("無法載入數據")