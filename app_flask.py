"""
Flask 主伺服器 - 取代 Streamlit
支持即時更新、多 Tab 同時操作、無閃爍
新增: 兩階段仲裁決策系統
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
from datetime import datetime
import json
import os
from typing import Dict, Optional
import uuid

from core.realtime_data_loader import RealtimeDataLoader
from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
from core.bybit_trader import BybitDemoTrader
from strategies.v13.market_features import prepare_market_features
from strategies.v13.config import V13Config
from strategies.v13.backtester import V13Backtester

try:
    from core.config_manager import ConfigManager
    from core.multi_api_manager import MultiAPIManager
    from core.dual_model_agent import DualModelDecisionAgent
    from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
    HAS_CONFIG_MANAGER = True
    HAS_DUAL_MODEL = True
    HAS_ARBITRATOR = True
except ImportError as e:
    HAS_CONFIG_MANAGER = False
    HAS_DUAL_MODEL = False
    HAS_ARBITRATOR = False
    print(f"警告: 部分功能不可用 - {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

CONFIG_FILE = 'config.json'
CASES_FILE = 'cases.json'

app_state = {
    'ai_agent': None,
    'dual_agent': None,
    'arbitrator_agent': None,
    'use_dual_model': False,
    'use_arbitrator_consensus': False,
    'dual_model_mode': 'consensus',
    'data_loader': None,
    'auto_update_enabled': False,
    'auto_update_thread': None,
    'ai_prediction_logs': [],
    'latest_signal': None,
    'bybit_trader': None,
    'bybit_trading': False,
    'bybit_thread': None,
    'user_config': {},
    'cases': [],
    'config_manager': None
}

if HAS_CONFIG_MANAGER:
    app_state['config_manager'] = ConfigManager()


def load_config():
    if HAS_CONFIG_MANAGER and app_state['config_manager']:
        try:
            config = app_state['config_manager'].load()
            app_state['user_config'] = config
            
            app_state['use_dual_model'] = config.get('use_dual_model', False)
            app_state['use_arbitrator_consensus'] = config.get('use_arbitrator_consensus', False)
            app_state['dual_model_mode'] = config.get('dual_model_mode', 'consensus')
            
            print(f"配置已載入: {CONFIG_FILE}")
            return config
        except Exception as e:
            print(f"載入配置失敗: {e}")
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                app_state['user_config'] = config
                app_state['use_dual_model'] = config.get('use_dual_model', False)
                app_state['use_arbitrator_consensus'] = config.get('use_arbitrator_consensus', False)
                app_state['dual_model_mode'] = config.get('dual_model_mode', 'consensus')
                print(f"配置已載入: {CONFIG_FILE}")
                return config
        except Exception as e:
            print(f"載入配置失敗: {e}")
    return {}


def save_config(config: Dict):
    try:
        app_state['user_config'] = config
        
        if 'use_dual_model' in config:
            app_state['use_dual_model'] = config['use_dual_model']
        if 'use_arbitrator_consensus' in config:
            app_state['use_arbitrator_consensus'] = config['use_arbitrator_consensus']
        if 'dual_model_mode' in config:
            app_state['dual_model_mode'] = config['dual_model_mode']
        
        if HAS_CONFIG_MANAGER and app_state['config_manager']:
            app_state['config_manager'].save(config)
            app_state['config_manager'].export_to_env()
        else:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"配置已保存: {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"保存配置失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_cases():
    if os.path.exists(CASES_FILE):
        try:
            with open(CASES_FILE, 'r', encoding='utf-8') as f:
                cases = json.load(f)
                app_state['cases'] = cases
                print(f"案例已載入: {len(cases)} 筆")
                return cases
        except Exception as e:
            print(f"載入案例失敗: {e}")
    return []


def save_cases():
    try:
        with open(CASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_state['cases'], f, indent=2, ensure_ascii=False)
        print(f"案例已保存: {len(app_state['cases'])} 筆")
        return True
    except Exception as e:
        print(f"保存案例失敗: {e}")
        return False


def _get_ai_decision(market_data: Dict, account_info: Dict, position_info: Optional[Dict]):
    """獲取 AI 決策（單模型/雙模型/兩階段仲裁）"""
    
    # 優先檢查兩階段仲裁
    if app_state['use_arbitrator_consensus'] and HAS_ARBITRATOR:
        if not app_state['arbitrator_agent']:
            app_state['arbitrator_agent'] = ArbitratorConsensusAgent()
        
        print("[DECISION] Using Arbitrator Consensus (2-stage)")
        result = app_state['arbitrator_agent'].analyze_with_arbitration(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info
        )
        result['model_type'] = 'arbitrator'
        return result
    
    # 雙模型
    elif app_state['use_dual_model'] and HAS_DUAL_MODEL:
        if not app_state['dual_agent']:
            app_state['dual_agent'] = DualModelDecisionAgent()
        
        print("[DECISION] Using Dual Model")
        decision = app_state['dual_agent'].analyze_with_dual_models(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info,
            mode=app_state['dual_model_mode']
        )
        decision['model_type'] = 'dual'
        return decision
    
    # 單模型
    else:
        if not app_state['ai_agent']:
            app_state['ai_agent'] = PositionAwareDeepSeekAgent()
        
        print("[DECISION] Using Single Model")
        decision = app_state['ai_agent'].analyze_with_position(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info
        )
        decision['model_type'] = 'single'
        return decision


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/config/get', methods=['GET'])
def get_config():
    try:
        if HAS_CONFIG_MANAGER and app_state['config_manager']:
            config = app_state['config_manager'].get_for_display()
        else:
            config = app_state['user_config']
        
        config['use_dual_model'] = app_state['use_dual_model']
        config['use_arbitrator_consensus'] = app_state['use_arbitrator_consensus']
        config['dual_model_mode'] = app_state['dual_model_mode']
        config['has_dual_model'] = HAS_DUAL_MODEL
        config['has_arbitrator'] = HAS_ARBITRATOR
        
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/save', methods=['POST'])
def save_user_config():
    try:
        config = request.json
        
        if save_config(config):
            return jsonify({'success': True, 'message': '配置已保存'})
        else:
            return jsonify({'success': False, 'message': '保存失敗'}), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    try:
        if HAS_CONFIG_MANAGER and app_state['config_manager']:
            app_state['config_manager'].reset()
        
        app_state['user_config'] = {}
        app_state['use_dual_model'] = False
        app_state['use_arbitrator_consensus'] = False
        app_state['dual_model_mode'] = 'consensus'
        
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        
        return jsonify({'success': True, 'message': '配置已重設'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/test-apis', methods=['POST'])
def test_apis():
    try:
        if not HAS_CONFIG_MANAGER:
            return jsonify({
                'error': '未安裝配置管理器，請安裝: pip install cryptography google-generativeai'
            }), 500
        
        if not app_state['config_manager']:
            return jsonify({'error': '配置管理器未初始化'}), 500
        
        app_state['config_manager'].export_to_env()
        
        api_manager = MultiAPIManager()
        
        available = 0
        failed = []
        providers = []
        
        for provider in api_manager.providers:
            provider_info = {
                'name': provider.name,
                'model': provider.model,
                'available': provider.is_available,
                'priority': provider.priority,
                'daily_usage': f"{provider.daily_count}/{provider.daily_limit}"
            }
            providers.append(provider_info)
            
            if provider.is_available:
                available += 1
            else:
                failed.append(provider.name)
        
        return jsonify({
            'success': True,
            'total': len(api_manager.providers),
            'available': available,
            'failed': failed,
            'providers': providers
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/api-stats', methods=['GET'])
def get_api_stats():
    try:
        if not HAS_CONFIG_MANAGER:
            return jsonify({
                'total_providers': 0,
                'available_providers': 0,
                'providers': []
            })
        
        if app_state['config_manager']:
            app_state['config_manager'].export_to_env()
        
        api_manager = MultiAPIManager()
        stats = api_manager.get_stats()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'total_providers': 0,
            'available_providers': 0,
            'providers': [],
            'error': str(e)
        })


@app.route('/api/dual-model/stats', methods=['GET'])
def get_dual_model_stats():
    """獲取雙模型統計"""
    try:
        if not app_state.get('dual_agent'):
            return jsonify({
                'enabled': False,
                'performance': None
            })
        
        performance = app_state['dual_agent'].get_model_performance()
        agreement_rate = app_state['dual_agent'].get_agreement_rate(last_n=10)
        
        return jsonify({
            'enabled': True,
            'mode': app_state['dual_model_mode'],
            'performance': performance,
            'recent_agreement_rate': agreement_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cases/list', methods=['GET'])
def list_cases():
    return jsonify({'cases': app_state['cases']})


@app.route('/api/cases/add', methods=['POST'])
def add_case():
    try:
        case = request.json
        case['id'] = str(uuid.uuid4())
        case['created_at'] = datetime.now().isoformat()
        
        app_state['cases'].append(case)
        save_cases()
        
        return jsonify({'success': True, 'case': case})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cases/delete/<case_id>', methods=['DELETE'])
def delete_case(case_id):
    try:
        app_state['cases'] = [c for c in app_state['cases'] if c['id'] != case_id]
        save_cases()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        auto_log = data.get('auto_log', False)
        
        if not app_state['data_loader']:
            app_state['data_loader'] = RealtimeDataLoader()
        
        df = app_state['data_loader'].load_data(symbol, timeframe)
        
        if df is None or len(df) < 200:
            return jsonify({'error': '數據不足，至少需要 200 根 K 線'}), 400
        
        latest_data = prepare_market_features(df.iloc[-1], df)
        
        if app_state['bybit_trader']:
            account_info = app_state['bybit_trader'].get_account_info()
            position_info = app_state['bybit_trader'].get_position()
        else:
            account_info = {
                'total_equity': 10000,
                'available_balance': 10000,
                'unrealized_pnl': 0,
                'max_leverage': 10
            }
            position_info = None
        
        decision = _get_ai_decision(latest_data, account_info, position_info)
        
        latest_price = float(df['close'].iloc[-1])
        timestamp = df['timestamp'].iloc[-1]
        
        app_state['latest_signal'] = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': timestamp.isoformat(),
            'price': latest_price,
            'decision': decision
        }
        
        if auto_log:
            _save_ai_prediction_log(
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                price=latest_price,
                decision=decision,
                market_data=latest_data
            )
        
        print(f"[ANALYZE] Latest price: ${latest_price:,.2f}")
        print(f"[ANALYZE] Model type: {decision.get('model_type', 'unknown')}")
        
        return jsonify(app_state['latest_signal'])
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            app_state['data_loader'] = RealtimeDataLoader()
        
        df = app_state['data_loader'].load_data(symbol, timeframe, limit=1000)
        
        if df is None or df.empty:
            return jsonify({'error': '無法載入數據'}), 400
        
        bt = V13Backtester(config)
        results = bt.run(df)
        
        return jsonify(results)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-log/update', methods=['POST'])
def update_ai_log():
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '15m')
        
        if not app_state['data_loader']:
            app_state['data_loader'] = RealtimeDataLoader()
        
        df = app_state['data_loader'].load_data(symbol, timeframe)
        
        if df is None or len(df) < 200:
            return jsonify({'error': '數據不足'}), 400
        
        current_candle = df.iloc[-1]
        market_data = prepare_market_features(current_candle, df)
        
        if app_state['bybit_trader']:
            account_info = app_state['bybit_trader'].get_account_info()
            position_info = app_state['bybit_trader'].get_position()
        else:
            account_info = {
                'total_equity': 10000,
                'available_balance': 10000,
                'unrealized_pnl': 0,
                'max_leverage': 10
            }
            position_info = None
        
        decision = _get_ai_decision(market_data, account_info, position_info)
        
        _save_ai_prediction_log(
            timestamp=current_candle['timestamp'],
            symbol=symbol,
            timeframe=timeframe,
            price=float(current_candle['close']),
            decision=decision,
            market_data=market_data
        )
        
        return jsonify({
            'success': True,
            'logs': app_state['ai_prediction_logs']
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
    print("\n" + "=" * 50)
    print("Bybit 自動交易已啟動")
    print("=" * 50)
    
    while app_state['bybit_trading']:
        try:
            if not app_state['bybit_trader']:
                print("等待 Bybit 連接...")
                time.sleep(5)
                continue
            
            trader = app_state['bybit_trader']
            symbol = config.get('symbol', 'BTCUSDT')
            timeframe = '15m'
            
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 執行 AI 分析...")
            
            if not app_state['data_loader']:
                app_state['data_loader'] = RealtimeDataLoader()
            
            df = app_state['data_loader'].load_data(symbol, timeframe)
            
            if df is not None and len(df) > 200:
                current_candle = df.iloc[-1]
                market_data = prepare_market_features(current_candle, df)
                account_info = trader.get_account_info()
                position_info = trader.get_position()
                
                decision = _get_ai_decision(market_data, account_info, position_info)
                
                _save_ai_prediction_log(
                    timestamp=current_candle['timestamp'],
                    symbol=symbol,
                    timeframe=timeframe,
                    price=float(current_candle['close']),
                    decision=decision,
                    market_data=market_data
                )
                
                result = trader.execute_ai_decision(decision, market_data)
                
                print(f"\n交易執行: {result['action']} - {result['message']}")
                
                socketio.emit('bybit_trade_executed', {
                    'action': result['action'],
                    'message': result['message'],
                    'balance': trader.get_balance(),
                    'position': trader.get_position(),
                    'timestamp': datetime.now().isoformat()
                })
                
                socketio.emit('ai_log_updated', {
                    'logs': app_state['ai_prediction_logs']
                })
            
            print(f"\n等待下次執行 (15 分鐘後)...")
            time.sleep(900)
            
        except Exception as e:
            print(f"\nBybit trading error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)
    
    print("\n" + "=" * 50)
    print("Bybit 自動交易已停止")
    print("=" * 50)


def _save_ai_prediction_log(
    timestamp,
    symbol: str,
    timeframe: str,
    price: float,
    decision: Dict,
    market_data: Dict
):
    log_entry = {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp),
        'symbol': symbol,
        'timeframe': timeframe,
        'close_price': float(price),
        'action': decision.get('action', 'HOLD'),
        'confidence': decision.get('confidence', 0),
        'leverage': decision.get('leverage', 1),
        'position_size_usdt': decision.get('position_size_usdt', 0),
        'stop_loss': decision.get('stop_loss'),
        'take_profit': decision.get('take_profit'),
        'reasoning': decision.get('reasoning', '')[:200],
        'risk_assessment': decision.get('risk_assessment', 'MEDIUM'),
        'model_type': decision.get('model_type', 'single'),
        'agreement': decision.get('agreement'),
        'predicted_direction': _get_direction_from_action(decision.get('action', 'HOLD')),
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
    print(f"\nAI 預測已記錄: {log_entry['action']} (信心度 {log_entry['confidence']}%){model_info}")
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


if __name__ == '__main__':
    load_config()
    load_cases()
    
    print("")
    print("=" * 60)
    print("  Flask Server Starting - STW AI Trading System")
    print("=" * 60)
    print("  Access at: http://localhost:5000")
    print("  Features:")
    print("    - Real-time market data from Binance API")
    print("    - WebSocket live updates")
    print("    - Auto AI prediction logging")
    print("    - Config auto-save & restore")
    print("    - Encrypted API keys storage")
    print("    - Multi-API management")
    print("    - Learning cases library")
    print("    - Module-level loading (no page refresh)")
    print("    - Multi-tab simultaneous operation")
    
    if HAS_ARBITRATOR:
        print("    - Two-stage Arbitrator Consensus")
        print(f"      Enabled: {app_state['use_arbitrator_consensus']}")
    
    if HAS_DUAL_MODEL:
        print("    - Dual-model decision system")
        print(f"      Mode: {app_state['dual_model_mode']}")
        print(f"      Enabled: {app_state['use_dual_model']}")
    
    print("=" * 60)
    
    if HAS_CONFIG_MANAGER:
        print("  Config Manager: Enabled")
    else:
        print("  Config Manager: Disabled")
    
    if HAS_ARBITRATOR:
        print("  Arbitrator: Enabled")
    else:
        print("  Arbitrator: Disabled")
    
    if HAS_DUAL_MODEL:
        print("  Dual Model: Enabled")
    else:
        print("  Dual Model: Disabled")
    
    print("=" * 60)
    print("")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
