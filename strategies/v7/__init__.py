import streamlit as st
from .config import V7Config
from .backtester import V7Backtester
from .features import V7FeatureEngine
from .ml_models import V7MLEngine
from core.data_loader import DataLoader
import pandas as pd

def render():
    st.header("V7 - AI 驅動多策略引擎 (目標月化 30%)")
    st.info("""
    **V7 核心特性**：
    - 🤖 **LSTM 價格預測**：預測未來 1 小時價格方向，信心度 >75% 才開倉
    - 🎯 **XGBoost 插針分類器**：區分「假插針」與「真崩盤」，捕捉反轉機會
    - ⚡ **動量突破剝頭皮**：15 分鐘級別高頻交易，單筆目標 1-3%
    - 📈 **複利加速器**：盈利越多風險越高，虧損時自動降低風險
    - 🔄 **動態策略選擇**：AI 自動判斷當前最適合的策略
    
    **風險提示**：
    月化 30% 屬於高風險高報酬策略，最大回撤可能達到 15-25%。
    建議先用小資金（100-1000U）測試 2 週再放大。
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V7 設定")
        
        st.markdown("### 基本設定")
        symbol = st.selectbox(
            "交易對",
            ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            help="建議選擇波動性高的幣種以提高報酬"
        )
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", min_value=100, max_value=100000, value=1000, step=100)
        with col_days:
            simulation_days = st.number_input("回測天數", min_value=30, max_value=365, value=30, help="建議至少 30 天以測試複利效果")
        
        st.markdown("### 策略啟用")
        enable_momentum = st.checkbox("✅ 動量突破剝頭皮", value=True, help="目標月化 15-25%")
        enable_liquidity_hunt = st.checkbox("✅ 流動性掃蕩反轉", value=True, help="目標月化 10-20%")
        enable_ml_filter = st.checkbox("🤖 啟用 AI 過濾器", value=True, help="LSTM + XGBoost 提高勝率")
        
        st.markdown("### 風險管理")
        base_risk = st.slider("基礎風險 (%)", 1.0, 5.0, 2.0, 0.5, help="單筆止損風險") / 100.0
        max_leverage = st.slider("最大槓桿", 1, 10, 3, 1, help="用於放大報酬")
        enable_compound = st.checkbox("💰 啟用複利加速器", value=True, help="盈利時自動提高風險")
        
        st.markdown("### ML 模型設定")
        ml_confidence_threshold = st.slider(
            "AI 信心度閾值 (%)",
            50, 90, 75, 5,
            help="只有當 AI 預測信心度高於此值才開倉"
        ) / 100.0
        
        test_btn = st.button("🚀 開始回測 V7", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在訓練 AI 模型並回測 {symbol} 過去 {simulation_days} 天..."):
                config = V7Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    enable_momentum=enable_momentum,
                    enable_liquidity_hunt=enable_liquidity_hunt,
                    enable_ml_filter=enable_ml_filter,
                    base_risk=base_risk,
                    max_leverage=max_leverage,
                    enable_compound=enable_compound,
                    ml_confidence_threshold=ml_confidence_threshold
                )
                
                loader = DataLoader()
                df = loader.load_data(symbol, '15m')  # 15 分鐘級別高頻交易
                
                if df is not None and not df.empty:
                    # 訓練 ML 模型
                    ml_engine = V7MLEngine(config)
                    st.info("🤖 正在訓練 LSTM 價格預測模型...")
                    ml_engine.train(df)
                    
                    # 開始回測
                    bt = V7Backtester(config, ml_engine)
                    fe = V7FeatureEngine(config)
                    bt_results = bt.run(df, fe)
                    
                    st.success(f"✅ 回測完成！({symbol}) - 測試天數: {bt_results.get('days_tested', 0)} 天")
                    
                    # 資金變化
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("起始本金", f"{capital:.2f} U")
                    col_a2.metric("最終資金", f"{bt_results['final_capital']:.2f} U", 
                                  delta=f"+{(bt_results['final_capital']/capital - 1)*100:.1f}%")
                    profit_usd = bt_results['final_capital'] - capital
                    col_a3.metric("淨利潤", f"{profit_usd:+.2f} U")
                    
                    st.markdown("---")
                    
                    # 績效指標
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    monthly_return = bt_results['monthly_return']
                    col_b2.metric(
                        "平均月化報酬", 
                        f"{monthly_return:.2f}%",
                        delta="🎯 達標！" if monthly_return >= 30 else "⚠️ 未達標"
                    )
                    col_b3.metric("最大回撤 (%)", f"{bt_results['max_drawdown']:.2f}%")
                    
                    # 交易統計
                    col_c1, col_c2, col_c3 = st.columns(3)
                    col_c1.metric("勝率 (%)", f"{bt_results['win_rate']:.2f}%")
                    col_c2.metric("總交易次數", bt_results['total_trades'])
                    col_c3.metric("平均槓桿", f"{bt_results.get('avg_leverage', 0):.1f}x")
                    
                    st.markdown("---")
                    st.markdown("### 🤖 AI 模型表現")
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    col_d1.metric("LSTM 預測準確率", f"{bt_results.get('lstm_accuracy', 0):.1f}%")
                    col_d2.metric("XGBoost 準確率", f"{bt_results.get('xgb_accuracy', 0):.1f}%")
                    col_d3.metric("AI 過濾後勝率", f"{bt_results.get('ml_filtered_winrate', 0):.1f}%")
                    
                    # 評估結果
                    if monthly_return >= 30:
                        st.success(f"🎉 **目標達成！** 月化報酬 {monthly_return:.2f}% 已超過 30% 目標。")
                        if bt_results['max_drawdown'] < 20:
                            st.success("✅ 回撤控制良好（<20%），風險可接受。")
                            st.balloons()
                        else:
                            st.warning(f"⚠️ 最大回撤 {bt_results['max_drawdown']:.1f}% 偏高，實盤需謹慎。")
                    elif monthly_return >= 20:
                        st.info(f"📊 月化報酬 {monthly_return:.2f}%，接近目標。可嘗試：\n1. 提高基礎風險到 3%\n2. 提高槓桿到 5 倍")
                    else:
                        st.warning(f"⚠️ 月化報酬 {monthly_return:.2f}% 未達標。建議：\n1. 啟用複利加速器\n2. 降低 AI 信心度閾值到 65%\n3. 增加交易頻率")
                    
                    st.info("""
                    **V7 使用建議**：
                    - ✅ 先用 100-500U 小資金實盤測試 2 週
                    - ✅ 確認月化報酬穩定在 20%+ 後再放大本金
                    - ✅ 每週監控回撤，超過 15% 立即降低風險
                    - ✅ 每月重新訓練 AI 模型以適應市場變化
                    - ⚠️ 不要在單一策略上押注所有資金
                    """)
                    
                else:
                    st.error("無法載入數據")