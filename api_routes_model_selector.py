"""
模型選擇器 API 路由
在 app_flask.py 中 import 這個檔案來使用
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

def register_model_selector_routes(app):
    """
    註冊模型選擇器的 API 路由
    在 app_flask.py 中呼叫這個函數
    """
    
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
        """保存模型配置"""
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
                return jsonify({
                    'success': True,
                    'message': '配置已保存，請重新啟動伺服器以生效'
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
        """重置為預設配置"""
        try:
            manager = init_model_config_manager()
            if manager.reset_to_default():
                return jsonify({
                    'success': True,
                    'message': '已重置為預設配置（方案 B）'
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
    
    print("✅ 模型選擇器 API 路由已註冊")
