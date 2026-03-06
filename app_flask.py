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
from core.bybit_trader import BybitDemoTrader
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
    'bybit_trader': None,
    'bybit_trading': False,
    'bybit_thread': None
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_market():
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
        
        if app_state['ai_prediction_logs']:
            _update_previous_log_accuracy(
                app_state['ai_prediction_logs'],
                current_candle['close']
            )
        
        app_state['ai_prediction_logs'].append(log_entry)
        
        if len(app_state['ai_prediction_logs']) > 20:
            app_state['ai_prediction_logs'] = app_state['ai_prediction_logs'][-20:]
        
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
    app_state['ai_prediction_logs'] = []
    socketio.emit('ai_log_cleared', {})
    return jsonify({'success': True})


@app.route('/api/ai-log/get', methods=['GET'])
def get_ai_logs():
    return jsonify({
        'logs': app_state['ai_prediction_logs']
    })


@app.route('/api/bybit/test', methods=['POST'])
def test_bybit_connection():
    try:
        data = request.json
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        symbol = data.get('symbol', 'BTCUSDT')
        
        trader = BybitDemoTrader(
            api_key=api_key,
            api_secret=api_secret,
            demo_mode='demo',
            symbol=symbol
        )
        
        balance = trader.get_balance()
        position = trader.get_position()
        
        app_state['bybit_trader'] = trader
        
        return jsonify({
            'success': True,
            'balance': balance,
            'position': position
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('start_bybit_trading')
def handle_start_bybit_trading(data):
    app_state['bybit_trading'] = True
    
    if app_state['bybit_thread'] is None or not app_state['bybit_thread'].is_alive():
        thread = threading.Thread(
            target=bybit_trading_worker,
            args=(data,),
            daemon=True
        )
        thread.start()
        app_state['bybit_thread'] = thread
    
    emit('bybit_trading_started', {})


@socketio.on('stop_bybit_trading')
def handle_stop_bybit_trading():
    app_state['bybit_trading'] = False
    emit('bybit_trading_stopped', {})


def bybit_trading_worker(config):
    while app_state['bybit_trading']:
        try:
            if not app_state['bybit_trader']:
                time.sleep(5)
                continue
            
            trader = app_state['bybit_trader']
            
            if not app_state['data_loader']:
                app_state['data_loader'] = DataLoader()
            
            if not app_state['ai_agent']:
                app_state['ai_agent'] = PositionAwareDeepSeekAgent()
            
            df = app_state['data_loader'].load_data(config['symbol'], '15m')
            
            if df is not None and len(df) > 200:
                market_data = prepare_market_features(df.iloc[-1], df)
                account_info = trader.get_account_info()
                position_info = trader.get_position()
                
                decision = app_state['ai_agent'].analyze_with_position(
                    market_data=market_data,
                    account_info=account_info,
                    position_info=position_info
                )
                
                result = trader.execute_ai_decision(decision, market_data)
                
                socketio.emit('bybit_trade_executed', {
                    'action': result['action'],
                    'message': result['message'],
                    'balance': trader.get_balance(),
                    'position': trader.get_position()
                })
            
            time.sleep(900)  # 15 分鐘
            
        except Exception as e:
            print(f"Bybit trading error: {e}")
            time.sleep(60)


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
    print("Flask Server Starting...")
    print("Access at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
