import streamlit as st
from .config import V4Config
from .backtester import V4Backtester
from .features import V4FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V4 - SMC 爆發模式 (月化 30% 挑戰)")
    st.info("在擁有 50% 勝率與 1:2 盈虧比的基礎上，開啟「資金複利」與「交易時間過濾」來達到爆發性收益。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("利潤放大器")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### 資金管理 (核心)")
        use_compounding = st.checkbox("開啟滾雪球複利 (Compounding)", value=True)
        risk_per_trade = st.slider("單筆止損風險 (Risk %)", 1.0, 10.0, 3.0, 0.5, help="這決定了你每次開單的槓桿大小") / 100.0
        
        st.markdown("### 交易品質優化")
        use_killzones = st.checkbox("啟用活躍時間過濾 (Kill Zones)", value=True)
        fvg_min_size = st.slider("FVG 最小缺口 (ATR 倍數)", 0.1, 2.0, 0.5, 0.1)
        require_sweep = st.checkbox("必須有流動性掠奪", value=True)
        
        st.markdown("### 盈虧比設定")
        rr_ratio = st.number_input("目標盈虧比 (R)", value=2.5, step=0.5)
        be_ratio = st.number_input("保本推移 (R)", value=1.0, step=0.1)
            
        test_btn = st.button("開始回測 爆發模式", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner("執行複利回測與時區過濾中..."):
                config = V4Config(
                    symbol=symbol,
                    use_compounding=use_compounding,
                    risk_per_trade=risk_per_trade,
                    use_killzones=use_killzones,
                    fvg_min_size_atr=fvg_min_size,
                    require_sweep=require_sweep,
                    risk_reward_ratio=rr_ratio,
                    breakeven_r=be_ratio
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    bt = V4Backtester(config)
                    fe = V4FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"回測完成！ ({symbol} {timeframe}) - 測試總天數: {bt_results.get('days_tested', 0)} 天")
                    
                    # 第一排數據
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("平均月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    # 第二排數據
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_actual = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_actual:.2f}")
                    
                    # 第三排：實盤參考數據
                    st.markdown("---")
                    st.markdown("### 🔍 實盤可行性評估")
                    col_g, col_h = st.columns(2)
                    col_g.metric("平均使用槓桿", f"{bt_results.get('avg_leverage', 0):.1f}x")
                    
                    # 分析實盤落差風險
                    if bt_results.get('avg_leverage', 0) > 20:
                        st.warning("⚠️ **警告：平均槓桿過高**。在實盤中，超過 20 倍的槓桿遇到極端插針時，交易所的強制平倉引擎（Liquidation Engine）可能會在打到你的止損價之前，就先把你強平。")
                    elif bt_results['max_drawdown'] > 50:
                        st.warning("⚠️ **警告：回撤過大**。高達 65% 的回撤在實盤中會對心態造成極大考驗，散戶極高機率會在回撤期手動關閉機器人。")
                    else:
                        st.success("✅ **實盤可行性高**。槓桿與回撤都在可控範圍內，此策略具備上線實盤的潛力。")
                    
                    st.info("""
                    **關於實盤與回測的落差（Slippage & Fill Rate）：**
                    1. **滑點與手續費**：回測已扣除萬分之四手續費與萬分之二滑點（Maker+Taker混合）。但遇到非農或CPI數據發布的瞬間，真實滑點可能高達千分之一，會吃掉部分利潤。
                    2. **FVG 限價單成交率**：回測假設「只要價格碰到 FVG 邊緣就 100% 成交」。但在實盤中，FVG 邊緣是流動性密集區，你的限價單（Limit Order）可能因為排隊太後面而錯失行情（Missed Fill）。
                    3. **建議**：如果要上實盤，建議先把 `Risk %` 降回 1.5%，跑兩週測試實盤成交率與滑點誤差。
                    """)
                    
                else:
                    st.error("無法加載數據")