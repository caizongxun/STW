import streamlit as st
from .config import V4Config
from .backtester import V4Backtester
from .features import V4FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V4 - SMC 爆發模式 (月化 30% 挑戰)")
    st.info("在擁有 50% 勝率與 1:2 盈虧比的基礎上，開啟「資金複利 (Compounding)」與「交易時間過濾 (Kill Zones)」來達到爆發性收益。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("利潤放大器")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### 資金管理 (核心)")
        use_compounding = st.checkbox("開啟滾雪球複利 (Compounding)", value=True, help="將賺到的錢投入下一次交易的保證金中。這是達成 30% 月化的關鍵。")
        risk_per_trade = st.slider("單筆止損風險 (Risk %)", 1.0, 5.0, 3.0, 0.5, help="因為勝率已經過半，可以將風險從 1.5% 提高到 3% 來放大收益。") / 100.0
        
        st.markdown("### 交易品質優化")
        use_killzones = st.checkbox("啟用活躍時間過濾 (Kill Zones)", value=True, help="自動避開盤整無聊的垃圾時間，只在紐約與倫敦開盤時做單。")
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
                    
                    st.success(f"回測完成！ ({symbol} {timeframe}) - 測試天數: {bt_results.get('days_tested', 'N/A')} 天")
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("嚴格月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_actual = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_actual:.2f}")
                    
                    # 判斷是否達標
                    if bt_results['monthly_return'] >= 30:
                        st.success("🎉 恭喜！策略已達到每月 30% 以上的回報目標！")
                        st.balloons()
                    elif bt_results['return_pct'] > 0:
                        st.info("💡 穩定盈利中！可嘗試提高「單筆風險 %」來逼近 30% 月化目標。")
                        
                else:
                    st.error("無法加載數據")