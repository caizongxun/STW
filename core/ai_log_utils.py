"""
AI 預測日誌工具模塊
負責保存和更新 AI 預測日誌
"""
from typing import Dict
from datetime import datetime


def save_ai_prediction_log(
    app_state: Dict,
    timestamp,
    symbol: str,
    timeframe: str,
    price: float,
    decision: Dict,
    market_data: Dict
):
    # 處理執行審核員調整後的決策
    final_action = decision.get('final_action', decision.get('action', 'HOLD'))
    final_confidence = decision.get('adjusted_confidence', decision.get('confidence', 0))
    
    log_entry = {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp),
        'symbol': symbol,
        'timeframe': timeframe,
        'close_price': float(price),
        'action': final_action,
        'confidence': final_confidence,
        'leverage': decision.get('adjusted_leverage', decision.get('leverage', 1)),
        'position_size_usdt': decision.get('adjusted_position_size', decision.get('position_size_usdt', 0)),
        'stop_loss': decision.get('stop_loss'),
        'take_profit': decision.get('take_profit'),
        'reasoning': decision.get('executor_reasoning', decision.get('reasoning', ''))[:200],
        'risk_assessment': decision.get('risk_assessment', 'MEDIUM'),
        'model_type': decision.get('model_type', 'single'),
        'is_counter_trend': decision.get('is_counter_trend', False),
        'execution_decision': decision.get('execution_decision'),  # EXECUTE/REJECT/REDUCE_SIZE
        'agreement': decision.get('agreement'),
        'predicted_direction': _get_direction_from_action(final_action),
        'actual_direction': None,
        'is_correct': None,
        'rsi': market_data.get('rsi'),
        'macd_hist': market_data.get('macd_hist'),
        'bb_position': market_data.get('bb_position'),
        'adx': market_data.get('adx')
    }
    
    if app_state['ai_prediction_logs']:
        _update_previous_log_accuracy(
            app_state['ai_prediction_logs'],
            price
        )
    
    app_state['ai_prediction_logs'].append(log_entry)
    
    if len(app_state['ai_prediction_logs']) > 100:
        app_state['ai_prediction_logs'] = app_state['ai_prediction_logs'][-100:]
    
    model_info = f" ({log_entry['model_type']} model)" if log_entry['model_type'] in ['dual', 'arbitrator'] else ""
    counter_info = " [Counter-trend]" if log_entry['is_counter_trend'] else ""
    executor_info = f" [{log_entry['execution_decision']}]" if log_entry.get('execution_decision') else ""
    print(f"\nAI 預測已記錄: {log_entry['action']} (信心度 {log_entry['confidence']}%){model_info}{counter_info}{executor_info}")
    print(f"總記錄數: {len(app_state['ai_prediction_logs'])}")


def _get_direction_from_action(action: str) -> str:
    if action in ['OPEN_LONG', 'ADD_POSITION']:
        return 'UP'
    elif action in ['OPEN_SHORT']:
        return 'DOWN'
    elif action == 'CLOSE':
        return 'CLOSE'
    else:
        return 'NEUTRAL'


def _update_previous_log_accuracy(logs: list, current_price: float):
    if len(logs) < 1:
        return
    
    prev_log = logs[-1]
    
    if prev_log['is_correct'] is not None:
        return
    
    prev_price = prev_log['close_price']
    predicted_direction = prev_log['predicted_direction']
    
    if current_price > prev_price * 1.001:
        actual_direction = 'UP'
    elif current_price < prev_price * 0.999:
        actual_direction = 'DOWN'
    else:
        actual_direction = 'NEUTRAL'
    
    prev_log['actual_direction'] = actual_direction
    
    if predicted_direction in ['NEUTRAL', 'CLOSE']:
        prev_log['is_correct'] = None
    else:
        prev_log['is_correct'] = (predicted_direction == actual_direction)
    
    if prev_log['is_correct'] is not None:
        result_text = "[OK] 準確" if prev_log['is_correct'] else "[FAIL] 錯誤"
        print(f"\n上次預測結果: {result_text}")
        print(f"  預測: {predicted_direction}, 實際: {actual_direction}")
