import streamlit as st
from .config import V11Config
from .backtester import V11Backtester
from core.data_loader import DataLoader

def render():
    st.header("V11 - AI 神經預測系統 (XGBoost Quant)")
    
    st.info("""
    **V11 核心理念 (機器學習量化)**：
    單純依賴技術指標 (V8~V10) 容易被假突破和假回調騙。V11 引入了 **機器學習 (XGBoost/LightGBM 邏輯)**。
    
    **AI 運作邏輯**：
    1. 🧠 **特徵工程**：系統會計算 20+ 種市場特徵 (RSI, MACD, 布林帶偏離度, 波動率, K線形態)。
    2. 🤖 **模型訓練**：在回測時，模型會先拿前 30% 的數據進行訓練，學習「什麼樣的特徵組合會導致未來 10 根 K 線上漲」。
    3. 🎯 **機率預測**：在正式交易時，只有當 AI 模型預測「上漲機率 > 設定閾值」時才允許開倉。
    4. ⚡ **動態適應**：打破固定指標的死板，AI 會自動發現隱藏的市場規律，從而大幅提高勝率與交易次數。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V11 AI 設定")
        
        symbol = st.selectbox("交易對", ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'], index=0)
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", 1000, 100000, 10000, 1000)
        with col_days:
            simulation_days = st.number_input("回測天數", 30, 365, 90, help="天數越長，AI 訓練數據越多，建議 90 天以上")
            
        st.markdown("### 🤖 機器學習參數")
        ai_confidence = st.slider("AI 預測信心閾值 (%)", 50, 90, 65, 5, help="只交易 AI 認為勝率大於此數值的信號。太高會沒交易，太低會虧損。")
        look_forward = st.slider("預測未來 K 線數", 3, 20, 10, 1, help="AI 預測未來幾根 K 線內會上漲")
        
        st.markdown("### 🛡️ 交易與風險管理")
        tp_r = st.slider("止盈目標 (R)", 1.0, 5.0, 2.0, 0.5)
        base_risk = st.slider("單筆風險 (%)", 1.0, 5.0, 2.0, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 10, 3, 1)
        
        test_btn = st.button("🚀 開始 V11 AI 訓練與回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在加載 {symbol} 數據，並訓練 AI 模型 (這可能需要 10-20 秒)..."):
                config = V11Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    ai_confidence_threshold=ai_confidence / 100.0,
                    look_forward_bars=look_forward,
                    tp_r=tp_r,
                    base_risk=base_risk,
                    max_leverage=max_leverage
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '15m')
                
                if df is not None and not df.empty:
                    bt = V11Backtester(config)
                    results = bt.run(df)
                    
                    st.success(f"✅ AI 訓練與回測完成！({symbol}) - 測試天數: {results.get('days_tested', 0)} 天")
                    
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
                    col_c3.metric("模型 AUC 分數", f"{results.get('model_auc', 0):.2f}", help=">0.5代表比瞎猜好，>0.6算不錯")
                    col_c4.metric("盈虧比", f"{results.get('profit_factor', 0):.2f}")
                    
                    st.markdown("### 🧠 AI 模型特徵重要性 (Top 5)")
                    st.write("AI 發現以下指標對預測未來走勢最關鍵：")
                    importance = results.get('feature_importance', {})
                    for feat, score in list(importance.items())[:5]:
                        st.progress(score, text=f"{feat} ({score*100:.1f}%)")
                    
                else:
                    st.error("無法載入數據")