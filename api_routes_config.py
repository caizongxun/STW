"""
Flask API 路由 - 配置管理
"""
from flask import Blueprint, request, jsonify
from core.config_manager import ConfigManager
from core.multi_api_manager import MultiAPIManager
import os

config_bp = Blueprint('config', __name__)
config_manager = ConfigManager()


@config_bp.route('/api/config/get', methods=['GET'])
def get_config():
    """獲取配置（不包含 API Keys）"""
    try:
        config = config_manager.get_for_display()
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@config_bp.route('/api/config/save', methods=['POST'])
def save_config():
    """保存配置"""
    try:
        config = request.get_json()
        
        if config_manager.save(config):
            # 匯出到環境變量
            config_manager.export_to_env()
            return jsonify({'success': True, 'message': '配置已保存'})
        else:
            return jsonify({'success': False, 'message': '保存失敗'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@config_bp.route('/api/config/reset', methods=['POST'])
def reset_config():
    """重設配置"""
    try:
        config_manager.reset()
        return jsonify({'success': True, 'message': '配置已重設'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@config_bp.route('/api/config/api-stats', methods=['GET'])
def get_api_stats():
    """獲取 API 使用統計"""
    try:
        # 确保環境變量是最新的
        config_manager.export_to_env()
        
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


@config_bp.route('/api/config/test-apis', methods=['POST'])
def test_apis():
    """測試所有 API 連接"""
    try:
        config_manager.export_to_env()
        api_manager = MultiAPIManager()
        
        available = 0
        failed = []
        
        for provider in api_manager.providers:
            if provider.is_available:
                available += 1
            else:
                failed.append(provider.name)
        
        return jsonify({
            'total': len(api_manager.providers),
            'available': available,
            'failed': failed
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
