"""
交易相關路由模塊
負責 Bybit 交易、案例管理等
修復: 所有 prepare_market_features 調用都添加 symbol 參數
"""
from flask import jsonify, request
import uuid
from datetime import datetime
from core.bybit_trader import BybitDemoTrader


def register_trading_routes(app, app_state):
    """註冊交易相關路由"""
    
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
            
            from core.config_utils import save_cases
            save_cases(app_state)
            
            return jsonify({'success': True, 'case': case})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/cases/delete/<case_id>', methods=['DELETE'])
    def delete_case(case_id):
        try:
            app_state['cases'] = [c for c in app_state['cases'] if c['id'] != case_id]
            
            from core.config_utils import save_cases
            save_cases(app_state)
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
