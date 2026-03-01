import streamlit as st
from .config import V4Config
from .backtester import V4Backtester
from .features import V4FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V4 - SMC (流動性掠奪 + FVG 狙擊)")
    st.info("解決低勝率問題：加入 ICT 的靈魂「Liquidity Sweep (流動性掠奪)」。只有在掃掉散戶止損後形成的真空區，才是真正的高勝率進場點。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("SMC 進階參數")
        symbol = st.selectbox("交易對 (V4)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### FVG 品質過濾")
        fvg_min_size = st.slider("FVG 最小缺口 (ATR 倍數)", 0.1, 2.0, 0.5, 0.1, help="過濾掉太小的無意義缺口")
        
        st.markdown("### 流動性掠奪 (Liquidity Sweep)")
        require_sweep = st.checkbox("必須有流動性掠奪 (強烈建議)", value=True, help="FVG 發生前，必須先跌破前低/突破前高")
        sweep_lookback = st.slider("尋找前高低點的區間 (K線數)", 5, 50, 15, 5)
        
        st.markdown("### 風控與盈虧比")
        risk_per_trade = st.slider("單筆止損風險 (Risk %)", 0.5, 5.0, 1.5, 0.5) / 100.0
        
        col_rr1, col_rr2 = st.columns(2)
        with col_rr1:
            rr_ratio = st.number_input("目標盈虧比 (R)", value=2.5, step=0.5)
        with col_rr2:
            be_ratio = st.number_input("保本推移 (R)", value=1.0, step=0.1, help="提早保本提升勝率")
            
        test_btn = st.button("開始回測 高勝率 SMC", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner("計算流動性矩陣與 FVG..."):
                config = V4Config(
                    symbol=symbol,
                    fvg_min_size_atr=fvg_min_size,
                    require_sweep=require_sweep,
                    sweep_lookback=sweep_lookback,
                    risk_per_trade=risk_per_trade,
                    risk_reward_ratio=rr_ratio,
                    breakeven_r=be_ratio
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    bt = V4Backtester(config)
                    fe = V4FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"回測完成！ ({symbol} {timeframe})")
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    col_b.metric("預估月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    col_c.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    col_d, col_e, col_f = st.columns(3)
                    col_d.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_e.metric("總交易次數", bt_results['total_trades'])
                    
                    avg_w = bt_results['avg_win_pct']
                    avg_l = abs(bt_results['avg_loss_pct'])
                    rr_actual = (avg_w / avg_l) if avg_l > 0 else 0
                    col_f.metric("實際盈虧比", f"1 : {rr_actual:.2f}")
                    
                    st.json(bt_results)
                    
                    if bt_results['return_pct'] > 0:
                        st.balloons()
                else:
                    st.error("無法加載數據")