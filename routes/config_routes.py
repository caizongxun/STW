"""
配置管理路由模塊
負責 API Key 配置、模型選擇、API 測試等
"""
from flask import jsonify, request
import os


def register_config_routes(app, app_state, config_manager, HAS_CONFIG_MANAGER):
    """註冊配置相關路由"""
    
    @app.route('/api/config/get', methods=['GET'])
    def get_config():
        try:
            if HAS_CONFIG_MANAGER and config_manager:
                config = config_manager.get_for_display()
            else:
                config = app_state['user_config']
            
            config['use_dual_model'] = app_state['use_dual_model']
            config['use_arbitrator_consensus'] = app_state['use_arbitrator_consensus']
            config['dual_model_mode'] = app_state['dual_model_mode']
            config['has_dual_model'] = app_state.get('HAS_DUAL_MODEL', False)
            config['has_arbitrator'] = app_state.get('HAS_ARBITRATOR', False)
            config['has_multi_timeframe'] = app_state.get('HAS_MULTI_TIMEFRAME', False)
            
            return jsonify(config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/save', methods=['POST'])
    def save_user_config():
        try:
            from core.config_utils import save_config
            config = request.json
            
            if save_config(app_state, config_manager, config, HAS_CONFIG_MANAGER):
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
            if HAS_CONFIG_MANAGER and config_manager:
                config_manager.reset()
            
            app_state['user_config'] = {}
            app_state['use_dual_model'] = False
            app_state['use_arbitrator_consensus'] = False
            app_state['dual_model_mode'] = 'consensus'
            
            config_file = 'config.json'
            if os.path.exists(config_file):
                os.remove(config_file)
            
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
            
            if not config_manager:
                return jsonify({'error': '配置管理器未初始化'}), 500
            
            config_manager.export_to_env()
            
            from core.multi_api_manager import MultiAPIManager
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
            
            if config_manager:
                config_manager.export_to_env()
            
            from core.multi_api_manager import MultiAPIManager
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
