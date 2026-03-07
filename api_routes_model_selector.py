"""
模型選擇器 API 路由
支持熱更新(不用重啟伺服器)
"""
from flask import jsonify, request
from core.model_config_manager import ModelConfigManager

# 初始化模型配置管理器
model_config_manager = None

def init_model_config_manager():
    global model_config_manager
    if model_config_manager is None:
        model_config_manager = ModelConfigManager()
    return model_config_manager

def register_model_selector_routes(app, app_state):
    """
    註冊模型選擇器的 API 路由
    在 app_flask.py 中呼叫這個函數
    
    Args:
        app: Flask app
        app_state: 全局狀態字典 (用於熱更新 AI agents)
    """
    
    def _reload_agents():
        """重新載入所有 AI agents (熱更新)"""
        print("\n" + "="*60)
        print("⚡ 熱更新：重新載入 AI 模型...")
        print("="*60)
        
        try:
            # 清除舊的 agents
            app_state['ai_agent'] = None
            app_state['dual_agent'] = None
            app_state['arbitrator_agent'] = None
            
            # 強制 Python 釋放記憶體
            import gc
            gc.collect()
            
            print("✅ 舊模型已清除")
            print("✅ 下次 AI 分析時會自動使用新模型")
            print("="*60 + "\n")
            return True
            
        except Exception as e:
            print(f"❌ 熱更新失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @app.route('/api/models/available', methods=['GET'])
    def get_available_models():
        """獲取可用模型列表"""
        try:
            manager = init_model_config_manager()
            models = manager.get_available_models()
            return jsonify({
                'success': True,
                'models': models
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/models/config', methods=['GET'])
    def get_model_config():
        """獲取當前模型配置"""
        try:
            manager = init_model_config_manager()
            config = manager.get_config()
            summary = manager.get_config_summary()
            return jsonify({
                'success': True,
                'config': config,
                'summary': summary
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/models/config', methods=['POST'])
    def save_model_config():
        """保存模型配置並熱更新"""
        try:
            manager = init_model_config_manager()
            config = request.json
            
            # 驗證配置
            is_valid, error_msg = manager.validate_config(config)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            # 保存
            if manager.save_config(config):
                # 熱更新 agents
                reload_success = _reload_agents()
                
                return jsonify({
                    'success': True,
                    'message': '✅ 配置已保存並立即生效！',
                    'hot_reload': reload_success
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '保存失敗'
                }), 500
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/models/reset', methods=['POST'])
    def reset_model_config():
        """重置為預設配置並熱更新"""
        try:
            manager = init_model_config_manager()
            if manager.reset_to_default():
                # 熱更新 agents
                reload_success = _reload_agents()
                
                return jsonify({
                    'success': True,
                    'message': '✅ 已重置為預設配置並立即生效！',
                    'hot_reload': reload_success
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '重置失敗'
                }), 500
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/models/hot-reload', methods=['POST'])
    def hot_reload_models():
        """手動觸發熱更新"""
        try:
            reload_success = _reload_agents()
            return jsonify({
                'success': reload_success,
                'message': '✅ 模型已重新載入' if reload_success else '❌ 重新載入失敗'
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    print("✅ 模型選擇器 API 路由已註冊 (支持熱更新)")
