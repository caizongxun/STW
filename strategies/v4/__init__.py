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
        st.subheader("基本設定")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", min_value=10, max_value=100000, value=10000, step=100)
        with col_days:
            simulation_days = st.number_input("回測天數", min_value=0, max_value=1000, value=0, help="0 表示測試所有歷史資料，30 表示只測試最近 30 天")
        
        st.markdown("### 資金管理與槓桿")
        use_compounding = st.checkbox("開啟滾雪球複利 (Compounding)", value=True)
        risk_per_trade = st.slider("單筆止損風險 (Risk %)", 0.5, 10.0, 3.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿倍數", 1, 100, 30, 1, help="限制單筆交易的最大槓桿，避免被提早強平")
        
        st.markdown("### 交易品質優化")
        use_killzones = st.checkbox("啟用活躍時間過濾 (Kill Zones)", value=True)
        fvg_min_size = st.slider("FVG 最小缺口 (ATR 倍數)", 0.1, 2.0, 0.5, 0.1)
        require_sweep = st.checkbox("必須有流動性掠奪", value=True)
        
        st.markdown("### 盈虧比設定")
        rr_ratio = st.number_input("目標盈虧比 (R)", value=2.5, step=0.5)
        be_ratio = st.number_input("保本推移 (R)", value=1.0, step=0.1)
            
        test_btn = st.button("開始回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在回測 {'所有' if simulation_days == 0 else str(simulation_days)} 天的數據..."):
                config = V4Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    use_compounding=use_compounding,
                    risk_per_trade=risk_per_trade,
                    max_leverage=max_leverage,
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
                    
                    st.success(f"回測完成！ ({symbol} {timeframe}) - 實際測試天數: {bt_results.get('days_tested', 0)} 天")
                    
                    # 第一排：資金變化
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("起始本金", f"{capital:.2f} U")
                    col_a2.metric("最終資金", f"{bt_results['final_capital']:.2f} U")
                    profit_usd = bt_results['final_capital'] - capital
                    col_a3.metric("淨利潤", f"{profit_usd:+.2f} U")
                    
                    st.markdown("---")
                    
                    # 第二排：績效指標
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("平均月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    # 第三排：交易統計
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_actual = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_actual:.2f}")
                    
                    # 實盤評估
                    st.markdown("---")
                    st.markdown("### 🔍 實盤可行性評估")
                    col_g, col_h = st.columns(2)
                    col_g.metric("平均使用槓桿", f"{bt_results.get('avg_leverage', 0):.1f}x")
                    col_h.metric("最大允許槓桿", f"{max_leverage}x")
                    
                    if bt_results.get('avg_leverage', 0) > max_leverage * 0.8:
                        st.warning(f"⚠️ 警告：平均槓桿 ({bt_results.get('avg_leverage', 0):.1f}x) 已經非常接近你設定的上限 ({max_leverage}x)，實盤中遇到插針極易被強平。")
                    elif bt_results['max_drawdown'] > 50:
                        st.warning("⚠️ 警告：回撤過大。實盤中會對心態造成極大考驗。")
                    else:
                        st.success("✅ 實盤可行性高，槓桿與回撤都在可控範圍內。")
                        
                else:
                    st.error("無法加載數據")