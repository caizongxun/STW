"""
WebSocket 事件處理模塊
負責 Bybit 自動交易的 WebSocket 事件
修復: 所有 prepare_market_features 調用都添加 symbol 參數
"""
import time
from datetime import datetime
from strategies.v13.market_features import prepare_market_features
from core.realtime_data_loader import RealtimeDataLoader


def register_websocket_handlers(socketio, app_state):
    """註冊 WebSocket 事件處理器"""
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        socketio.emit('connected', {'message': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('start_bybit_trading')
    def handle_start_bybit_trading(data):
        app_state['bybit_trading'] = True
        
        if app_state['bybit_thread'] is None or not app_state['bybit_thread'].is_alive():
            import threading
            thread = threading.Thread(
                target=bybit_trading_worker,
                args=(socketio, app_state, data),
                daemon=True
            )
            thread.start()
            app_state['bybit_thread'] = thread
        
        socketio.emit('bybit_trading_started', {})
    
    @socketio.on('stop_bybit_trading')
    def handle_stop_bybit_trading():
        app_state['bybit_trading'] = False
        socketio.emit('bybit_trading_stopped', {})


def bybit_trading_worker(socketio, app_state, config):
    """
    Bybit 自動交易工作線程
    修復: 所有 prepare_market_features 調用都添加 symbol 參數
    """
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
                # 修復: 添加 symbol 參數
                market_data = prepare_market_features(current_candle, df, symbol=symbol)
                
                from routes.analysis_routes import _prepare_historical_candles, _get_ai_decision
                historical_candles = _prepare_historical_candles(df, symbol=symbol, num_candles=20)
                account_info = trader.get_account_info()
                position_info = trader.get_position()
                
                # 獲取多時間框架數據
                multi_timeframe_data = None
                if app_state.get('HAS_MULTI_TIMEFRAME') and app_state['mt_analyzer']:
                    try:
                        multi_timeframe_data = app_state['mt_analyzer'].prepare_multi_timeframe_data(
                            symbol=symbol,
                            primary_timeframe=timeframe,
                            secondary_timeframes=['1h', '4h'],
                            num_candles=20
                        )
                    except Exception as e:
                        print(f"[WARNING] 多時間框架分析失敗: {e}")
                
                decision = _get_ai_decision(
                    app_state=app_state,
                    market_data=market_data,
                    account_info=account_info,
                    position_info=position_info,
                    historical_candles=historical_candles,
                    successful_cases=app_state['cases'][:10],
                    multi_timeframe_data=multi_timeframe_data
                )
                
                from core.ai_log_utils import save_ai_prediction_log
                save_ai_prediction_log(
                    app_state=app_state,
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
