"""
分析相關路由模塊
負責 AI 分析、回測、預測日誌等
修復: 所有 prepare_market_features 調用都添加 symbol 參數
"""
from flask import jsonify, request
from datetime import datetime
from strategies.v13.market_features import prepare_market_features
from strategies.v13.config import V13Config
from strategies.v13.backtester import V13Backtester
from core.realtime_data_loader import RealtimeDataLoader
import pandas as pd
from typing import Dict, List, Optional


def _prepare_historical_candles(df: pd.DataFrame, symbol: str, num_candles: int = 20) -> List[Dict]:
    """
    準備歷史 K 棒數據 (包含完整的40種技術指標)
    讓 AI 能看到每根 K 棒的完整市場狀態
    修復: 添加 symbol 參數
    """
    if len(df) < num_candles:
        num_candles = len(df)
    
    result = []
    
    # 從倒數 num_candles 根開始處理
    for i in range(-num_candles, 0):
        # 對每一根 K 棒使用 prepare_market_features 計算完整指標
        # 使用直至當前 K 棒的資料
        df_slice = df.iloc[:len(df) + i + 1].copy()
        row = df.iloc[i]
        
        # 修復: 添加 symbol 參數
        features = prepare_market_features(row, df_slice, symbol=symbol)
        
        # 加入時間戳和基本 OHLCV
        candle_info = {
            'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume']),
            
            # 全部 40 種技術指標
            'features': features
        }
        
        result.append(candle_info)
    
    return result


def _get_ai_decision(
    app_state: Dict,
    market_data: Dict,
    account_info: Dict,
    position_info: Optional[Dict],
    historical_candles: Optional[List[Dict]] = None,
    successful_cases: Optional[List[Dict]] = None,
    multi_timeframe_data: Optional[Dict] = None
):
    """獲取 AI 決策（單模型/雙模型/三階段仲裁）"""
    
    # 優先檢查三階段仲裁（雙模型 + 仲裁者 + 執行審核）
    if app_state['use_arbitrator_consensus'] and app_state.get('HAS_ARBITRATOR'):
        if not app_state['arbitrator_agent']:
            from core.arbitrator_consensus_agent import ArbitratorConsensusAgent
            app_state['arbitrator_agent'] = ArbitratorConsensusAgent()
        
        print("[DECISION] Using Arbitrator Consensus (3-stage: A/B -> Arbitrator -> Executor)")
        result = app_state['arbitrator_agent'].analyze_with_arbitration(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info,
            historical_candles=historical_candles,
            successful_cases=successful_cases,
            multi_timeframe_data=multi_timeframe_data
        )
        result['model_type'] = 'arbitrator'
        return result
    
    # 雙模型
    elif app_state['use_dual_model'] and app_state.get('HAS_DUAL_MODEL'):
        if not app_state['dual_agent']:
            from core.dual_model_agent import DualModelDecisionAgent
            app_state['dual_agent'] = DualModelDecisionAgent()
        
        print("[DECISION] Using Dual Model")
        decision = app_state['dual_agent'].analyze_with_dual_models(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info
        )
        decision['model_type'] = 'dual'
        return decision
    
    # 單模型
    else:
        if not app_state['ai_agent']:
            from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
            app_state['ai_agent'] = PositionAwareDeepSeekAgent()
        
        print("[DECISION] Using Single Model")
        decision = app_state['ai_agent'].analyze_with_position(
            market_data=market_data,
            account_info=account_info,
            position_info=position_info
        )
        decision['model_type'] = 'single'
        return decision


def register_analysis_routes(app, app_state):
    """註冊分析相關路由"""
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze_market():
        try:
            data = request.json
            symbol = data.get('symbol', 'BTCUSDT')
            timeframe = data.get('timeframe', '15m')
            auto_log = data.get('auto_log', False)
            
            if not app_state['data_loader']:
                app_state['data_loader'] = RealtimeDataLoader()
            
            # 初始化多時間框架分析器
            if app_state.get('HAS_MULTI_TIMEFRAME') and not app_state['mt_analyzer']:
                from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer
                app_state['mt_analyzer'] = MultiTimeframeAnalyzer(app_state['data_loader'])
                print("[OK] 多時間框架分析器已初始化")
            
            df = app_state['data_loader'].load_data(symbol, timeframe)
            
            if df is None or len(df) < 200:
                return jsonify({'error': '數據不足，至少需要 200 根 K 線'}), 400
            
            # 修復: 添加 symbol 參數
            latest_data = prepare_market_features(df.iloc[-1], df, symbol=symbol)
            historical_candles = _prepare_historical_candles(df, symbol=symbol, num_candles=20)
            
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
                    print(f"[OK] 多時間框架數據已準備: {list(multi_timeframe_data.keys())}")
                    
                    # 檢查逆勢機會
                    counter_signal = app_state['mt_analyzer'].get_counter_trend_signal(multi_timeframe_data)
                    if counter_signal['has_signal']:
                        print(f"[ALERT] 高信心逆勢機會: {counter_signal['direction']} (信心度 {counter_signal['confidence']}%)")
                        print(f"   {counter_signal['reasoning']}")
                except Exception as e:
                    print(f"[WARNING] 多時間框架分析失敗: {e}")
                    multi_timeframe_data = None
            
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
            
            decision = _get_ai_decision(
                app_state=app_state,
                market_data=latest_data,
                account_info=account_info,
                position_info=position_info,
                historical_candles=historical_candles,
                successful_cases=app_state['cases'][:10],
                multi_timeframe_data=multi_timeframe_data
            )
            
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
                from core.ai_log_utils import save_ai_prediction_log
                save_ai_prediction_log(
                    app_state=app_state,
                    timestamp=timestamp,
                    symbol=symbol,
                    timeframe=timeframe,
                    price=latest_price,
                    decision=decision,
                    market_data=latest_data
                )
            
            print(f"[ANALYZE] Latest price: ${latest_price:,.2f}")
            print(f"[ANALYZE] Model type: {decision.get('model_type', 'unknown')}")
            print(f"[ANALYZE] Provided {len(historical_candles)} historical candles (15m) with 40+ features each")
            if multi_timeframe_data:
                print(f"[ANALYZE] Multi-timeframe: {list(multi_timeframe_data.keys())}")
            print(f"[ANALYZE] Provided {len(app_state['cases'][:10])} successful cases")
            
            if decision.get('is_counter_trend'):
                print("[ANALYZE] Counter-trend operation detected!")
            
            if 'execution_decision' in decision:
                print(f"[ANALYZE] Executor decision: {decision['execution_decision']}")
            
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
            # 修復: 添加 symbol 參數
            market_data = prepare_market_features(current_candle, df, symbol=symbol)
            historical_candles = _prepare_historical_candles(df, symbol=symbol, num_candles=20)
            
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
        return jsonify({'success': True})
    
    @app.route('/api/ai-log/get', methods=['GET'])
    def get_ai_logs():
        return jsonify({
            'logs': app_state['ai_prediction_logs']
        })
    
    @app.route('/api/arbitrator/stats', methods=['GET'])
    def get_arbitrator_stats():
        """獲取三階段仲裁系統統計"""
        try:
            if not app_state.get('arbitrator_agent'):
                return jsonify({
                    'enabled': False,
                    'stats': None
                })
            
            stats = app_state['arbitrator_agent'].get_statistics()
            
            return jsonify({
                'enabled': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
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
