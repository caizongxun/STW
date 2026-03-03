import streamlit as st
from .config import V10Config
from .backtester import V10Backtester
from core.data_loader import DataLoader

def render():
    st.header("V10 - 波動爆發狙擊手 (BB Squeeze Breakout)")
    
    st.info("""
    **V10 核心理念 (告別接飛刀)**：
    前幾個版本(V8, V9)都是「回調接刀」策略，在加密貨幣市場容易遇到連續下跌導致止損。
    V10 徹底改變思路，採用華爾街經典的 **Bollinger Band Squeeze (布林帶擠壓突破)** 策略。
    
    **策略邏輯**：
    1. 🛑 **等待平靜**：市場進入盤整，波動率降到最低（布林帶收斂/擠壓）。
    2. 🚀 **動能爆發**：價格帶量突破布林帶上軌，且 RSI 顯示強烈動能 (>60)。
    3. 📈 **順勢上車**：只在多頭趨勢中做多，絕不逆勢。
    4. 🛡️ **動態防守**：使用 EMA9 作為動態追蹤止損，讓利潤奔跑直到趨勢結束。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V10 設定")
        
        symbol = st.selectbox("交易對", ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'], index=0)
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", 1000, 100000, 10000, 1000)
        with col_days:
            simulation_days = st.number_input("回測天數", 30, 180, 60)
        
        st.markdown("### 爆發過濾條件")
        squeeze_length = st.slider("擠壓期長度 (K線數)", 10, 50, 20, 5, help="布林帶寬度低於過去N根K線的平均值")
        rsi_momentum = st.slider("RSI 動能要求", 50, 70, 60, 5, help="RSI必須大於此數值才算強勢突破")
        volume_surge = st.slider("成交量爆發倍數", 1.0, 3.0, 1.5, 0.1, help="突破時的成交量必須是均量的幾倍")
        
        st.markdown("### 出場與風險管理")
        exit_mode = st.radio("出場邏輯", ["ema_trailing", "fixed_rr"], 
                           format_func=lambda x: "📈 EMA9 跌破出場 (吃盡趨勢)" if x == "ema_trailing" else "🎯 固定盈虧比 (見好就收)")
        
        if exit_mode == "fixed_rr":
            tp_r = st.slider("止盈目標 (R)", 1.5, 5.0, 2.5, 0.5)
        else:
            tp_r = 0.0 # Not used
            
        base_risk = st.slider("單筆風險 (%)", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 10, 3, 1)
        
        test_btn = st.button("🚀 開始 V10 回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在加載 {symbol} 數據..."):
                config = V10Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    squeeze_length=squeeze_length,
                    rsi_momentum=rsi_momentum,
                    volume_surge=volume_surge,
                    exit_mode=exit_mode,
                    tp_r=tp_r,
                    base_risk=base_risk,
                    max_leverage=max_leverage
                )
                
                loader = DataLoader()
                # 爆發策略在 15m 或 1h 都很好，預設用 15m
                df = loader.load_data(symbol, '15m')
                
                if df is not None and not df.empty:
                    st.info("📋 正在回測 V10 波動爆發策略...")
                    bt = V10Backtester(config)
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
                    
                    st.markdown("---")
                    st.markdown("### 🔍 策略診斷與建議")
                    if monthly_return > 0:
                        st.success("🎉 **策略盈利！** 突破策略成功抓住了市場的強勢脈衝。")
                        if exit_mode == "ema_trailing" and results['win_rate'] < 40:
                            st.info("💡 **提示**：EMA追蹤出場的勝率通常在 35-45% 之間，這是正常的。因為我們在吃大趨勢，偶爾的假突破止損是可以接受的，關鍵是盈虧比（Profit Factor）是否大於 1.5。")
                    else:
                        st.warning("⚠️ **策略虧損**。可能原因：\n1. 該幣種近期處於無聊的震盪市，假突破太多。\n2. 要求太寬鬆，嘗試提高「成交量爆發倍數」到 2.0，過濾掉沒力的突破。")
                        
                else:
                    st.error("無法載入數據")