import streamlit as st
from .config import V8Config
from .backtester import V8Backtester
from .features import V8FeatureEngine
from .lstm_model import V8LSTMModel
from core.data_loader import DataLoader
import pandas as pd

def render():
    st.header("V8 - LSTM 反轉預測 + 雙時間框架確認")
    
    st.info("""
    **V8 核心特性**：
    - 🧠 **真正的 LSTM 模型**：使用 TensorFlow 訓練序列預測模型
    - 🔄 **雙時間框架**：15m 尋找反轉 + 1h 確認趨勢
    - 🎯 **反轉形態量化**：RSI 背離、Pin Bar、Z-Score 超賣
    - 🛡️ **動態止損**：基於 ATR 自適應 + 移動止盈
    - 📈 **高勝率過濾**：只在模型信心度 >65% 時進場
    
    **適用場景**：
    - 捕捉大波動中的短期反轉機會
    - 適合波動性高的幣種（BTC/ETH/SOL）
    - 目標月化 20-30%，勝率 60%+
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("V8 設定")
        
        st.markdown("### 基本設定")
        symbol = st.selectbox(
            "交易對",
            ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            help="建議選擇波動性高的主流幣種"
        )
        
        col_cap, col_days = st.columns(2)
        with col_cap:
            capital = st.number_input("起投本金 (U)", min_value=1000, max_value=100000, value=10000, step=1000)
        with col_days:
            simulation_days = st.number_input("回測天數", min_value=30, max_value=180, value=60, 
                                            help="建議 60 天以上以充分測試 LSTM 模型")
        
        st.markdown("### LSTM 模型設定")
        train_model = st.checkbox(
            "🧠 訓練 LSTM 模型",
            value=True,
            help="首次使用必須啟用，大約需要 2-5 分鐘"
        )
        
        if train_model:
            train_size_pct = st.slider(
                "訓練集比例 (%)",
                50, 80, 70,
                help="前 70% 用於訓練，後 30% 用於回測"
            ) / 100.0
        else:
            train_size_pct = 0.7
        
        lstm_confidence = st.slider(
            "LSTM 信心度閾值 (%)",
            50, 90, 65, 5,
            help="只有當模型預測信心度高於此值才進場。降低可增加交易機會。"
        ) / 100.0
        
        st.markdown("### 策略參數")
        enable_dual_timeframe = st.checkbox(
            "✅ 啟用雙時間框架確認",
            value=True,
            help="同時檢查 15m 和 1h，提高勝率但減少交易機會"
        )
        
        enable_pattern_filter = st.checkbox(
            "✅ 啟用反轉形態過濾",
            value=False,
            help="檢測 RSI 背離、Pin Bar 等形態。可能過度限制交易。"
        )
        
        st.markdown("### 風險管理")
        base_risk = st.slider("基礎風險 (%)", 1.0, 5.0, 2.5, 0.5) / 100.0
        max_leverage = st.slider("最大槓桿", 1, 5, 3, 1)
        atr_multiplier = st.slider("止損 ATR 倍數", 0.5, 3.0, 1.2, 0.1)
        tp_ratio = st.slider("止盈倍數 (R)", 1.5, 4.0, 2.5, 0.5)
        
        test_btn = st.button("🚀 開始 V8 回測", type="primary", use_container_width=True)
        
    with col2:
        if test_btn:
            with st.spinner(f"正在加載 {symbol} 數據..."):
                config = V8Config(
                    symbol=symbol,
                    capital=capital,
                    simulation_days=simulation_days,
                    train_model=train_model,
                    train_size_pct=train_size_pct,
                    lstm_confidence=lstm_confidence,
                    enable_dual_timeframe=enable_dual_timeframe,
                    enable_pattern_filter=enable_pattern_filter,
                    base_risk=base_risk,
                    max_leverage=max_leverage,
                    atr_multiplier=atr_multiplier,
                    tp_ratio=tp_ratio
                )
                
                loader = DataLoader()
                df_15m = loader.load_data(symbol, '15m')
                df_1h = loader.load_data(symbol, '1h')
                
                if df_15m is not None and not df_15m.empty and df_1h is not None and not df_1h.empty:
                    # 生成特徵
                    fe = V8FeatureEngine(config)
                    df_15m = fe.generate(df_15m, timeframe='15m')
                    df_1h = fe.generate(df_1h, timeframe='1h')
                    
                    # 訓練 LSTM 模型
                    lstm_model = V8LSTMModel(config)
                    if train_model:
                        st.info("🧠 正在訓練 LSTM 模型，預計 2-5 分鐘...")
                        train_history = lstm_model.train(df_15m)
                        st.success(f"✅ LSTM 訓練完成！準確率: {train_history['accuracy']:.2f}%")
                    
                    # 開始回測
                    st.info("📋 正在回測 V8 策略...")
                    bt = V8Backtester(config, lstm_model)
                    bt_results = bt.run(df_15m, df_1h, fe)
                    
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
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    col_b1.metric("總報酬 (%)", f"{bt_results['return_pct']:.2f}%")
                    monthly_return = bt_results['monthly_return']
                    col_b2.metric("月化報酬", f"{monthly_return:.2f}%")
                    col_b3.metric("最大回撤", f"{bt_results['max_drawdown']:.2f}%")
                    col_b4.metric("夏普比率", f"{bt_results.get('sharpe_ratio', 0):.2f}")
                    
                    # 交易統計
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    col_c1.metric("勝率", f"{bt_results['win_rate']:.2f}%")
                    col_c2.metric("總交易", bt_results['total_trades'])
                    col_c3.metric("平均持倉(h)", f"{bt_results.get('avg_holding_hours', 0):.1f}")
                    col_c4.metric("盈虧比", f"{bt_results.get('profit_factor', 0):.2f}")
                    
                    st.markdown("---")
                    st.markdown("### 🧠 LSTM 模型表現")
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    col_d1.metric("訓練準確率", f"{bt_results.get('lstm_train_acc', 0):.1f}%")
                    col_d2.metric("測試準確率", f"{bt_results.get('lstm_test_acc', 0):.1f}%")
                    col_d3.metric("實際勝率提升", f"+{bt_results.get('winrate_improvement', 0):.1f}%")
                    
                    # 顯示過濾統計
                    if 'filter_stats' in bt_results:
                        st.markdown("---")
                        st.markdown("### 🔍 過濾器統計（為何沒交易？）")
                        stats = bt_results['filter_stats']
                        
                        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                        col_e1.metric("LSTM 信號數", stats.get('lstm_signals', 0))
                        col_e2.metric("通過信心度", stats.get('pass_confidence', 0))
                        col_e3.metric("通過趨勢", stats.get('pass_trend', 0))
                        col_e4.metric("最終交易", stats.get('final_trades', 0))
                        
                        st.info(f"""
                        **過濾漏斗分析**：
                        - LSTM 產生了 {stats.get('lstm_signals', 0)} 個看漲信號
                        - 其中 {stats.get('pass_confidence', 0)} 個通過信心度 ≥ {lstm_confidence*100:.0f}%
                        - 其中 {stats.get('pass_trend', 0)} 個通過趨勢確認
                        - 最終執行了 {stats.get('final_trades', 0)} 筆交易
                        
                        **建議**：
                        {'- 降低 LSTM 信心度到 60%' if stats.get('pass_confidence', 0) < 10 else ''}
                        {'- 關閉雙時間框架確認' if stats.get('pass_trend', 0) < 5 else ''}
                        {'- 關閉反轉形態過濾' if enable_pattern_filter and stats.get('final_trades', 0) == 0 else ''}
                        """)
                    
                    # 結果評估
                    if bt_results['total_trades'] == 0:
                        st.error("""
                        ❌ **沒有產生任何交易！**
                        
                        **可能原因**：
                        1. LSTM 信心度閾值太高（當前 {:.0f}%）→ 降低到 60%
                        2. 雙時間框架過濾太嚴格 → 嘗試關閉
                        3. 反轉形態過濾太嚴格 → 嘗試關閉
                        4. 回測期間市場持續單邊，沒有反轉機會
                        
                        **立即行動**：
                        - 將「LSTM 信心度閾值」降到 **60%**
                        - 取消勾選「啟用反轉形態過濾」
                        - 重新回測
                        """.format(lstm_confidence * 100))
                    elif monthly_return >= 20 and bt_results['win_rate'] >= 60:
                        st.success(f"🎉 **優秀表現！** 月化 {monthly_return:.1f}%，勝率 {bt_results['win_rate']:.1f}%")
                        if bt_results['max_drawdown'] < 15:
                            st.success("✅ 回撤控制良好，可以考慮實盤。")
                            st.balloons()
                    elif monthly_return >= 10:
                        st.info(f"📊 月化報酬 {monthly_return:.1f}%，表現尚可。建議：\n- 降低 LSTM 信心度閾值到 60%\n- 測試不同的幣種")
                    else:
                        st.warning(f"⚠️ 月化報酬 {monthly_return:.1f}% 未達預期。可能原因：\n- 訓練數據不足\n- 市場特性變化\n- 過濾條件過於嚴格")
                    
                    st.info("""
                    **V8 使用建議**：
                    - ✅ 首次使用必須訓練 LSTM 模型（大約 2-5 分鐘）
                    - ✅ 建議每月重新訓練一次以適應市場
                    - ✅ 實盤前先用小資金測試 2 週
                    - ✅ 只在波動性高的時段交易（避免盤整）
                    - ⚠️ LSTM 預測只是輔助，不能完全依賴
                    """)
                    
                else:
                    st.error("無法載入數據")