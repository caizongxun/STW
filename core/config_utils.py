"""
配置工具模塊
負責載入、保存配置和案例
"""
import json
import os
from typing import Dict

CONFIG_FILE = 'config.json'
CASES_FILE = 'cases.json'


def load_config(app_state, config_manager=None, HAS_CONFIG_MANAGER=False):
    """載入配置並自動設定環境變數"""
    if HAS_CONFIG_MANAGER and config_manager:
        try:
            config = config_manager.load()
            app_state['user_config'] = config
            
            # 自動設定環境變數
            config_manager.export_to_env()
            print("[OK] 已自動設定環境變數")
            
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


def save_config(app_state, config_manager, config: Dict, HAS_CONFIG_MANAGER=False):
    try:
        app_state['user_config'] = config
        
        if 'use_dual_model' in config:
            app_state['use_dual_model'] = config['use_dual_model']
        if 'use_arbitrator_consensus' in config:
            app_state['use_arbitrator_consensus'] = config['use_arbitrator_consensus']
        if 'dual_model_mode' in config:
            app_state['dual_model_mode'] = config['dual_model_mode']
        
        if HAS_CONFIG_MANAGER and config_manager:
            config_manager.save(config)
            config_manager.export_to_env()
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


def load_cases(app_state):
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


def save_cases(app_state):
    try:
        with open(CASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_state['cases'], f, indent=2, ensure_ascii=False)
        print(f"案例已保存: {len(app_state['cases'])} 筆")
        return True
    except Exception as e:
        print(f"保存案例失敗: {e}")
        return False
