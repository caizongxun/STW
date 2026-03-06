"""
Flask 主伺服器 - 取代 Streamlit
支持即時更新、多 Tab 同時操作、無閃爍
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
from datetime import datetime
import json

from core.data_loader import DataLoader
from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
from strategies.v13.market_features import prepare_market_features
from strategies.v13.config import V13Config
from strategies.v13.backtester import V13Backtester

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局狀態管理
app_state = {
    'ai_agent': None,
    'data_loader': None,
    'auto_update_enabled': False,
    'auto_update_thread': None,
    'ai_prediction_logs': [],
    'latest_signal': None,
    'bybit_positions': []
}


# ============= 路由 =============

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    """獲取實時 AI 訊號"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        
        if not app_state['data_loader']:
            app_state['data_loader'] = DataLoader()
        
        df = app_state['data_loader'].load_data(symbol, timeframe)
        
        if df is None or len(df) < 200:
            return jsonify({'error': '數據不足，至少需要 200 根 K 線'}), 400
        
        latest_data = prepare_market_features(df.iloc[-1], df)
        
        if not app_state['ai_agent']:
            app_state['ai_agent'] = PositionAwareDeepSeekAgent()
        
        account_info = {
            'total_equity': 10000,
            'available_balance': 10000,
            'unrealized_pnl': 0,
            'max_leverage': 10
        }
        
        decision = app_state['ai_agent'].analyze_with_position(
            market_data=latest_data,
            account_info=account_info,
            position_info=None
        )
        
        app_state['latest_signal'] = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'price': latest_data['close'],
            'decision': decision
        }
        
        return jsonify(app_state['latest_signal'])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """執行回測"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        capital = data.get('capital', 10000)
        simulation_days = data.get('simulation_days', 30)
        ai_confidence_threshold = data.get('ai_confidence_threshold', 0.7)
        
        config = V13Config(
            symbol=symbol,
            timeframe=timeframe,
            capital=capital,
            simulation_days=simulation_days,
            ai_confidence_threshold=ai_confidence_threshold
        )
        
        if not app_state['data_loader']:
            app_state['data_loader'] = DataLoader()
        
        df = app_state['data_loader'].load_data(symbol, timeframe)
        
        if df is None or df.empty:
            return jsonify({'error': '無法載入數據'}), 400
        
        bt = V13Backtester(config)
        results = bt.run(df)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-log/update', methods=['POST'])
def update_ai_log():
    """更新 AI 預測記錄"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        
        if not app_state['data_loader']:
            app_state['data_loader'] = DataLoader()
        
        if not app_state['ai_agent']:
            app_state['ai_agent'] = PositionAwareDeepSeekAgent()
        
        df = app_state['data_loader'].load_data(symbol, timeframe)
        
        if df is None or len(df) < 200:
            return jsonify({'error': '數據不足'}), 400
        
        current_candle = df.iloc[-1]
        market_data = prepare_market_features(current_candle, df)
        
        account_info = {
            'total_equity': 10000,
            'available_balance': 10000,
            'unrealized_pnl': 0,
            'max_leverage': 10
        }
        
        decision = app_state['ai_agent'].analyze_with_position(
            market_data=market_data,
            account_info=account_info,
            position_info=None
        )
        
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
            'predicted_direction': _get_direction_from_action(decision.get('action', 'HOLD')),
            'actual_direction': None,
            'is_correct': None
        }
        
        # 更新上一筆記錄的準確度
        if app_state['ai_prediction_logs']:
            _update_previous_log_accuracy(
                app_state['ai_prediction_logs'],
                current_candle['close']
            )
        
        app_state['ai_prediction_logs'].append(log_entry)
        
        # 保留最近 20 筆
        if len(app_state['ai_prediction_logs']) > 20:
            app_state['ai_prediction_logs'] = app_state['ai_prediction_logs'][-20:]
        
        # 透過 WebSocket 推送更新
        socketio.emit('ai_log_updated', {
            'logs': app_state['ai_prediction_logs'],
            'new_entry': log_entry
        })
        
        return jsonify({
            'success': True,
            'logs': app_state['ai_prediction_logs']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-log/clear', methods=['POST'])
def clear_ai_logs():
    """清除所有 AI 預測記錄"""
    app_state['ai_prediction_logs'] = []
    socketio.emit('ai_log_cleared', {})
    return jsonify({'success': True})


@app.route('/api/ai-log/get', methods=['GET'])
def get_ai_logs():
    """獲取所有 AI 預測記錄"""
    return jsonify({
        'logs': app_state['ai_prediction_logs']
    })


# ============= WebSocket 事件 =============

@socketio.on('connect')
def handle_connect():
    """客戶端連接"""
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """客戶端斷開"""
    print('Client disconnected')


@socketio.on('start_auto_update')
def handle_start_auto_update(data):
    """啟動自動更新"""
    symbol = data.get('symbol', 'BTCUSDT')
    timeframe = data.get('timeframe', '15m')
    interval = data.get('interval', 900)  # 預設 15 分鐘
    
    app_state['auto_update_enabled'] = True
    
    if app_state['auto_update_thread'] is None or not app_state['auto_update_thread'].is_alive():
        thread = threading.Thread(
            target=auto_update_worker,
            args=(symbol, timeframe, interval),
            daemon=True
        )
        thread.start()
        app_state['auto_update_thread'] = thread
    
    emit('auto_update_started', {'symbol': symbol, 'timeframe': timeframe})


@socketio.on('stop_auto_update')
def handle_stop_auto_update():
    """停止自動更新"""
    app_state['auto_update_enabled'] = False
    emit('auto_update_stopped', {})


# ============= 背景任務 =============

def auto_update_worker(symbol, timeframe, interval):
    """自動更新背景任務"""
    while app_state['auto_update_enabled']:
        try:
            if not app_state['data_loader']:
                app_state['data_loader'] = DataLoader()
            
            if not app_state['ai_agent']:
                app_state['ai_agent'] = PositionAwareDeepSeekAgent()
            
            df = app_state['data_loader'].load_data(symbol, timeframe)
            
            if df is not None and len(df) > 200:
                current_candle = df.iloc[-1]
                market_data = prepare_market_features(current_candle, df)
                
                account_info = {
                    'total_equity': 10000,
                    'available_balance': 10000,
                    'unrealized_pnl': 0,
                    'max_leverage': 10
                }
                
                decision = app_state['ai_agent'].analyze_with_position(
                    market_data=market_data,
                    account_info=account_info,
                    position_info=None
                )
                
                # 透過 WebSocket 推送即時訊號
                socketio.emit('signal_updated', {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat(),
                    'price': market_data['close'],
                    'decision': decision
                })
            
        except Exception as e:
            print(f"Auto update error: {e}")
        
        time.sleep(interval)


# ============= 輔助函數 =============

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


if __name__ == '__main__':
    print("🚀 Flask Server Starting...")
    print("📡 Access at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
