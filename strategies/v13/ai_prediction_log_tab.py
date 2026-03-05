"""
AI 預測記錄 Tab
記錄每次模型預測結果和實際表現
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time

from core.data_loader import DataLoader
from strategies.v13 import prepare_market_features
from core.llm_agent_position_aware import PositionAwareDeepSeekAgent


def render_ai_prediction_log_tab():
    """渲柔 AI 預測記錄頁面"""
    st.subheader("[AI] 預測記錄 & 準確度分析")
    
    st.info("""
    **功能說明**：
    - 記錄每根 K 棒的 AI 預測結果
    - 對比預測 vs 實際走勢，計算準確率
    - 支持自動/手動更新
    - 保留近 20 筆記錄
    """)
    
    # === 設定區 ===
    with st.expander("[SETUP] 設定", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol = st.selectbox(
                "交易對",
                ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
                key='ai_log_symbol'
            )
        
        with col2:
            timeframe = st.selectbox(
                "K 線周期",
                ['15m', '1h', '4h'],
                key='ai_log_timeframe'
            )
        
        with col3:
            auto_update = st.checkbox(
                "自動更新",
                value=False,
                help="每 5 秒更新一次",
                key='ai_log_auto_update'
            )
    
    # === 控制按鈕 ===
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("[更新] 獲取最新預測", type="primary", key='ai_log_update_btn'):
            st.session_state['ai_log_trigger_update'] = True
    
    with col_btn2:
        if st.button("[清除] 清除所有記錄", type="secondary", key='ai_log_clear_btn'):
            st.session_state['ai_prediction_logs'] = []
            st.success("✅ 記錄已清除")
            st.rerun()
    
    with col_btn3:
        if st.button("[導出] 下載 CSV", type="secondary", key='ai_log_export_btn'):
            if 'ai_prediction_logs' in st.session_state and st.session_state['ai_prediction_logs']:
                df = pd.DataFrame(st.session_state['ai_prediction_logs'])
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 下載 CSV",
                    data=csv,
                    file_name=f"ai_predictions_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ 無記錄可導出")
    
    st.divider()
    
    # === 初始化 AI Agent ===
    if 'ai_log_agent' not in st.session_state:
        st.session_state['ai_log_agent'] = PositionAwareDeepSeekAgent()
    
    if 'ai_prediction_logs' not in st.session_state:
        st.session_state['ai_prediction_logs'] = []
    
    # === 更新邏輯 ===
    should_update = (
        st.session_state.get('ai_log_trigger_update', False) or 
        auto_update
    )
    
    if should_update:
        st.session_state['ai_log_trigger_update'] = False
        
        with st.spinner("🤖 AI 分析中..."):
            try:
                data_loader = DataLoader()
                ai_agent = st.session_state['ai_log_agent']
                
                # 獲取最新數據
                df = data_loader.load_data(symbol, timeframe)
                
                if df is not None and len(df) > 200:
                    current_candle = df.iloc[-1]
                    market_data = prepare_market_features(current_candle, df)
                    
                    # 獲取 AI 預測
                    account_info = {
                        'total_equity': 10000,
                        'available_balance': 10000,
                        'unrealized_pnl': 0,
                        'max_leverage': 10
                    }
                    
                    decision = ai_agent.analyze_with_position(
                        market_data=market_data,
                        account_info=account_info,
                        position_info=None
                    )
                    
                    # 記錄預測
                    log_entry = {
                        'timestamp': current_candle['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'close_price': float(current_candle['close']),
                        'action': decision.get('action', 'HOLD'),
                        'confidence': decision.get('confidence', 0),
                        'leverage': decision.get('leverage', 1),
                        'position_size_usdt': decision.get('position_size_usdt', 0),
                        'stop_loss': decision.get('stop_loss'),
                        'take_profit': decision.get('take_profit'),
                        'reasoning': decision.get('reasoning', '')[:200],
                        'risk_assessment': decision.get('risk_assessment', '')[:100],
                        # 用於後續驗證
                        'predicted_direction': _get_direction_from_action(decision.get('action', 'HOLD')),
                        'actual_direction': None,  # 下次更新時填入
                        'is_correct': None
                    }
                    
                    # 更新上一筆記錄的實際走勢
                    if st.session_state['ai_prediction_logs']:
                        _update_previous_log_accuracy(
                            st.session_state['ai_prediction_logs'],
                            current_candle['close']
                        )
                    
                    # 新增記錄
                    st.session_state['ai_prediction_logs'].append(log_entry)
                    
                    # 保留最近 20 筆
                    if len(st.session_state['ai_prediction_logs']) > 20:
                        st.session_state['ai_prediction_logs'] = st.session_state['ai_prediction_logs'][-20:]
                    
                    st.success(f"✅ 更新成功! AI 判斷: {decision.get('action', 'HOLD')} (信心度: {decision.get('confidence', 0)}%)")
                else:
                    st.error("❌ 數據不足，至少需要 200 根 K 棒")
                    
            except Exception as e:
                st.error(f"❌ 更新失敗: {e}")
    
    # === 顯示記錄 ===
    if st.session_state.get('ai_prediction_logs'):
        logs = st.session_state['ai_prediction_logs']
        
        # 計算準確率
        total_predictions = len([log for log in logs if log['is_correct'] is not None])
        correct_predictions = len([log for log in logs if log['is_correct'] == True])
        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # 顯示統計信息
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        col_stat1.metric(
            "總預測次數",
            f"{len(logs)}"
        )
        
        col_stat2.metric(
            "已驗證次數",
            f"{total_predictions}"
        )
        
        col_stat3.metric(
            "準確率",
            f"{accuracy:.1f}%",
            delta=f"{correct_predictions}/{total_predictions}"
        )
        
        # 動作分布
        action_counts = pd.Series([log['action'] for log in logs]).value_counts()
        col_stat4.metric(
            "最常動作",
            action_counts.index[0] if len(action_counts) > 0 else "N/A"
        )
        
        st.divider()
        
        # 詳細記錄表格
        st.markdown("### [記錄] 預測詳情")
        
        df_logs = pd.DataFrame(logs)
        
        # 選擇顯示欄位
        display_columns = [
            'timestamp', 'action', 'confidence', 'close_price',
            'leverage', 'predicted_direction', 'actual_direction', 'is_correct'
        ]
        
        # 處理顯示
        df_display = df_logs[display_columns].copy()
        df_display['is_correct'] = df_display['is_correct'].apply(
            lambda x: '✅' if x == True else ('❌' if x == False else '⏳')
        )
        
        st.dataframe(
            df_display,
            width='stretch',
            height=400
        )
        
        # 展開查看詳細推理
        with st.expander("[詳細] 查看 AI 推理過程"):
            for i, log in enumerate(reversed(logs[-5:])):
                idx = len(logs) - i - 1
                with st.container():
                    st.markdown(f"**⭐ 第 {idx+1} 筆記錄** - {log['timestamp']}")
                    
                    col_detail1, col_detail2 = st.columns([2, 3])
                    
                    with col_detail1:
                        st.caption(f"🎯 **動作**: {log['action']} ({log['confidence']}%)")
                        st.caption(f"💰 **價格**: ${log['close_price']:,.2f}")
                        st.caption(f"📈 **預測方向**: {log['predicted_direction']}")
                        st.caption(f"✅ **實際結果**: {log.get('actual_direction', '待驗證')}")
                    
                    with col_detail2:
                        st.caption(f"🧠 **AI 推理**: {log['reasoning']}")
                        st.caption(f"⚠️ **風險評估**: {log['risk_assessment']}")
                    
                    st.divider()
    
    else:
        st.info("📊 尚無預測記錄，點擊 [更新] 開始記錄")
    
    # === 自動更新迴圈 ===
    if auto_update:
        time.sleep(5)
        st.rerun()


def _get_direction_from_action(action: str) -> str:
    """從動作推斷預測方向"""
    if action in ['OPEN_LONG', 'ADD_POSITION']:
        return 'UP'
    elif action in ['OPEN_SHORT']:
        return 'DOWN'
    elif action == 'CLOSE':
        return 'CLOSE'
    else:
        return 'NEUTRAL'


def _update_previous_log_accuracy(logs: list, current_price: float):
    """更新上一筆記錄的準確度"""
    if len(logs) < 2:
        return
    
    prev_log = logs[-1]
    
    # 如果已經驗證過，不重複處理
    if prev_log['is_correct'] is not None:
        return
    
    prev_price = prev_log['close_price']
    predicted_direction = prev_log['predicted_direction']
    
    # 判斷實際方向
    if current_price > prev_price * 1.001:  # 上漲超過 0.1%
        actual_direction = 'UP'
    elif current_price < prev_price * 0.999:  # 下跌超過 0.1%
        actual_direction = 'DOWN'
    else:
        actual_direction = 'NEUTRAL'
    
    prev_log['actual_direction'] = actual_direction
    
    # 判斷是否正確
    if predicted_direction == 'NEUTRAL' or predicted_direction == 'CLOSE':
        prev_log['is_correct'] = None  # 不計算準確率
    else:
        prev_log['is_correct'] = (predicted_direction == actual_direction)
