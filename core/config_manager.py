"""
配置管理器
負責保存/載入/管理系統配置，支持本地持久化存儲
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config.json', key_file: str = '.config_key'):
        self.config_file = Path(config_file)
        self.key_file = Path(key_file)
        self.config: Dict[str, Any] = {}
        self.cipher = None
        
        # 初始化加密密鑰
        self._init_encryption()
        
        # 載入配置
        self.load()
    
    def _init_encryption(self):
        """初始化加密密鑰"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # 生成新密鑰
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # 設置權限（僅擁有者可讀）
            os.chmod(self.key_file, 0o600)
        
        self.cipher = Fernet(key)
    
    def _encrypt(self, value: str) -> str:
        """加密字串"""
        if not value:
            return ''
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        """解密字串"""
        if not encrypted_value:
            return ''
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return ''
    
    def load(self) -> Dict[str, Any]:
        """載入配置"""
        if not self.config_file.exists():
            self.config = self._get_default_config()
            return self.config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print(f"✅ 已載入配置: {self.config_file}")
        except Exception as e:
            print(f"⚠️ 載入配置失敗: {e}")
            self.config = self._get_default_config()
        
        return self.config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置"""
        if config:
            # 加密 API Keys
            encrypted_config = config.copy()
            
            # 多 API Keys
            for key in ['groq_api_key', 'google_api_key', 'openrouter_api_key', 
                       'github_token', 'cloudflare_api_key', 'deepseek_api_key', 
                       'binance_api_key', 'binance_api_secret', 'bybit_api_key', 
                       'bybit_api_secret']:
                if key in config and config[key]:
                    encrypted_config[key] = self._encrypt(config[key])
            
            self.config.update(encrypted_config)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 已保存配置: {self.config_file}")
            return True
        except Exception as e:
            print(f"⚠️ 保存配置失敗: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置項"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """設置配置項"""
        self.config[key] = value
    
    def get_api_key(self, key: str) -> str:
        """獲取解密後的 API Key"""
        encrypted = self.config.get(key, '')
        return self._decrypt(encrypted) if encrypted else ''
    
    def has_api_key(self, key: str) -> bool:
        """檢查是否有某個 API Key"""
        return bool(self.config.get(key))
    
    def get_for_display(self) -> Dict[str, Any]:
        """獲取用於顯示的配置（不包含實際 API Key）"""
        display_config = self.config.copy()
        
        # 移除加密的 API Keys，只顯示是否已保存
        api_keys = ['groq_api_key', 'google_api_key', 'openrouter_api_key', 
                   'github_token', 'cloudflare_api_key', 'deepseek_api_key', 
                   'binance_api_key', 'binance_api_secret', 'bybit_api_key', 
                   'bybit_api_secret']
        
        for key in api_keys:
            if key in display_config:
                display_config.pop(key)
                display_config[f"{key}_saved"] = True
        
        return display_config
    
    def reset(self):
        """重設配置為預設值"""
        self.config = self._get_default_config()
        self.save()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            # AI 設定
            'ai_model': 'deepseek-r1:14b',
            'ai_temperature': 0.1,
            'ai_max_tokens': 2048,
            'ai_confidence_threshold': 70,
            
            # 集成設定
            'enable_ensemble': False,
            'min_models': 2,
            'max_models': 3,
            
            # 通知設定
            'enable_notifications': False,
            'notification_email': '',
            'notify_on_trade': False,
            'notify_on_error': False
        }
    
    def export_to_env(self):
        """匯出 API Keys 到環境變量（用於使用）"""
        mappings = {
            'groq_api_key': 'GROQ_API_KEY',
            'google_api_key': 'GOOGLE_API_KEY',
            'openrouter_api_key': 'OPENROUTER_API_KEY',
            'github_token': 'GITHUB_TOKEN',
            'cloudflare_api_key': 'CLOUDFLARE_API_KEY',
            'deepseek_api_key': 'DEEPSEEK_API_KEY',
            'binance_api_key': 'BINANCE_API_KEY',
            'binance_api_secret': 'BINANCE_API_SECRET',
            'bybit_api_key': 'BYBIT_API_KEY',
            'bybit_api_secret': 'BYBIT_API_SECRET'
        }
        
        for config_key, env_key in mappings.items():
            api_key = self.get_api_key(config_key)
            if api_key:
                os.environ[env_key] = api_key
