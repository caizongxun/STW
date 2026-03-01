import streamlit as st
from .config import V3Config
from .trainer import V3Trainer
from .backtester import V3Backtester
from .features import V3FeatureEngine
from core.data_loader import DataLoader

def render():
    st.header("V3 - 激進高收益模型 (Target: 30%/Month)")
    st.info("透過提高資金利用率、拉高盈虧比 (保本推移策略) 與動態高槓桿，追求高額報酬。高報酬伴隨高回撤。")
    
    tab1, tab2 = st.tabs(["模型訓練", "策略回測"])
    
    with tab1:
        render_training()
        
    with tab2:
        st.info("請先進行訓練，回測結果會在訓練後自動展示。")

def render_training():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("進攻型參數設定")
        symbol = st.selectbox("交易對 (V3)", ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT'])
        timeframe = '15m'
        
        st.markdown("### 資金與槓桿")
        leverage = st.slider("合約槓桿倍數", 1, 50, 10, 1)
        position_pct = st.slider("單筆開倉比例 (%)", 10, 100, 50, 10) / 100.0
        
        st.markdown("### 策略敏銳度")
        signal_threshold = st.slider("AI 進場概率閾值", 0.50, 0.80, 0.58, 0.02)
        cooldown = st.slider("冷卻期 (抓連勝不休息)", 0, 10, 2, 1)
        
        st.markdown("### 盈虧比設定 (大賺小賠)")
        atr_sl = st.slider("止損乘數 (ATR)", 0.5, 3.0, 1.2, 0.1)
        atr_tp = st.slider("止盈乘數 (ATR)", 1.0, 5.0, 3.5, 0.1)
        
        train_btn = st.button("開始訓練 V3", type="primary", use_container_width=True)
        
    with col2:
        if train_btn:
            with st.spinner("加載數據與訓練中 (高參數量)..."):
                config = V3Config(
                    symbol=symbol,
                    signal_threshold=signal_threshold,
                    cooldown_bars=cooldown,
                    leverage=leverage,
                    position_pct=position_pct,
                    atr_sl_multiplier=atr_sl,
                    atr_tp_multiplier=atr_tp
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, timeframe)
                
                if df is not None and not df.empty:
                    trainer = V3Trainer(config)
                    results = trainer.train(df)
                    
                    st.success("V3 訓練完成！")
                    st.json(results)
                    
                    st.subheader("樣本外回測 (Out of Sample)")
                    bt = V3Backtester(config)
                    test_df = df.iloc[int(len(df)*0.8):].reset_index(drop=True)
                    bt_results = bt.run(test_df, trainer.long_model, trainer.short_model, V3FeatureEngine(config))
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    
                    # 判斷是否有月化報酬
                    if 'monthly_return' in bt_results and bt_results['monthly_return'] != 0:
                        col_b.metric("預估月化報酬", f"{bt_results['monthly_return']:.2f}%")
                    else:
                        col_b.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                        
                    col_c.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    
                    col_d, col_e = st.columns(2)
                    col_d.metric("總交易次數", bt_results['total_trades'])
                    if 'monthly_return' in bt_results and bt_results['monthly_return'] != 0:
                        col_e.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                    
                    st.json(bt_results)
                else:
                    st.error("無法加載數據")