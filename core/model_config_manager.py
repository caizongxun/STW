"""
模型配置管理器
讓用戶在 Web UI 自由選擇 Model A, Model B, 仲裁者
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class ModelConfigManager:
    def __init__(self, config_file: str = 'model_config.json'):
        self.config_file = Path(config_file)
        self.available_models = self._init_available_models()
        self.config = self._load_config()
    
    def _init_available_models(self) -> List[Dict]:
        """初始化可用模型列表 (2026年2月最新)"""
        return [
            # ===== Groq 模型 (14,400/day) =====
            {
                'id': 'groq_llama_70b',
                'name': 'Llama 3.3 70B',
                'platform': 'Groq',
                'model_name': 'llama-3.3-70b-versatile',
                'api_base': 'https://api.groq.com/openai/v1',
                'api_key_env': 'GROQ_API_KEY',
                'category': 'fast',
                'speed': '1-3s',
                'quota': '14,400/day',
                'quality': 5,
                'available': bool(os.getenv('GROQ_API_KEY'))
            },
            {
                'id': 'groq_mixtral',
                'name': 'Mixtral 8x7B',
                'platform': 'Groq',
                'model_name': 'mixtral-8x7b-32768',
                'api_base': 'https://api.groq.com/openai/v1',
                'api_key_env': 'GROQ_API_KEY',
                'category': 'fast',
                'speed': '1-3s',
                'quota': '14,400/day',
                'quality': 4,
                'available': bool(os.getenv('GROQ_API_KEY'))
            },
            {
                'id': 'groq_qwen3_32b',
                'name': 'Qwen3 32B',
                'platform': 'Groq',
                'model_name': 'qwen-2.5-32b',
                'api_base': 'https://api.groq.com/openai/v1',
                'api_key_env': 'GROQ_API_KEY',
                'category': 'fast',
                'speed': '1-3s',
                'quota': '14,400/day',
                'quality': 4,
                'available': bool(os.getenv('GROQ_API_KEY'))
            },
            
            # ===== Google 模型 (250-1,000/day) =====
            {
                'id': 'google_gemini_flash',
                'name': 'Gemini 2.0 Flash',
                'platform': 'Google',
                'model_name': 'gemini-2.0-flash',
                'api_base': '',
                'api_key_env': 'GOOGLE_API_KEY',
                'category': 'fast',
                'speed': '2-5s',
                'quota': '250/day',
                'quality': 5,
                'available': bool(os.getenv('GOOGLE_API_KEY'))
            },
            
            # ===== OpenRouter 免費模型 =====
            {
                'id': 'openrouter_llama_70b',
                'name': 'Llama 3.3 70B',
                'platform': 'OpenRouter',
                'model_name': 'meta-llama/llama-3.3-70b-instruct:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '3-6s',
                'quota': '無限',
                'quality': 5,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_llama_405b',
                'name': 'Llama 3.1 405B',
                'platform': 'OpenRouter',
                'model_name': 'meta-llama/llama-3.1-405b-instruct:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'arbitrator',
                'speed': '10-20s',
                'quota': '無限',
                'quality': 6,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_deepseek_r1',
                'name': 'DeepSeek R1 (Reasoning)',
                'platform': 'OpenRouter',
                'model_name': 'deepseek/deepseek-r1:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'arbitrator',
                'speed': '10-20s',
                'quota': '無限',
                'quality': 6,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_gemini_flash',
                'name': 'Gemini 2.0 Flash Exp',
                'platform': 'OpenRouter',
                'model_name': 'google/gemini-2.0-flash-exp:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '3-6s',
                'quota': '無限',
                'quality': 5,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_mistral_small',
                'name': 'Mistral Small 3.1',
                'platform': 'OpenRouter',
                'model_name': 'mistralai/mistral-small-3.1:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '3-6s',
                'quota': '無限',
                'quality': 4,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_qwen3_coder',
                'name': 'Qwen3 Coder 480B',
                'platform': 'OpenRouter',
                'model_name': 'qwen/qwen-3-coder-480b:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '5-10s',
                'quota': '無限',
                'quality': 5,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_devstral_2',
                'name': 'Devstral 2 (Coding)',
                'platform': 'OpenRouter',
                'model_name': 'mistralai/devstral-2512:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '5-10s',
                'quota': '無限',
                'quality': 5,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            {
                'id': 'openrouter_nemotron_nano',
                'name': 'Nemotron 3 Nano 30B',
                'platform': 'OpenRouter',
                'model_name': 'nvidia/nemotron-3-nano-30b:free',
                'api_base': 'https://openrouter.ai/api/v1',
                'api_key_env': 'OPENROUTER_API_KEY',
                'category': 'fast',
                'speed': '3-6s',
                'quota': '無限',
                'quality': 4,
                'available': bool(os.getenv('OPENROUTER_API_KEY'))
            },
        ]
    
    def _load_config(self) -> Dict:
        """讀取模型配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"讀取模型配置失敗: {e}")
        
        # 預設配置
        return {
            'model_a': 'groq_llama_70b',
            'model_b': 'openrouter_llama_70b',
            'arbitrator': 'openrouter_llama_405b'
        }
    
    def save_config(self, config: Dict) -> bool:
        """保存模型配置"""
        try:
            self.config = config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ 模型配置已保存: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ 保存模型配置失敗: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """重置為預設配置"""
        default_config = {
            'model_a': 'groq_llama_70b',
            'model_b': 'openrouter_llama_70b',
            'arbitrator': 'openrouter_llama_405b'
        }
        return self.save_config(default_config)
    
    def get_available_models(self) -> List[Dict]:
        """獲取可用模型列表"""
        # 重新檢查可用性
        for model in self.available_models:
            api_key_env = model['api_key_env']
            model['available'] = bool(os.getenv(api_key_env))
        
        return self.available_models
    
    def get_config(self) -> Dict:
        """獲取當前配置"""
        return self.config
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict]:
        """根據 ID 獲取模型資訊"""
        for model in self.available_models:
            if model['id'] == model_id:
                return model
        return None
    
    def validate_config(self, config: Dict) -> tuple:
        """
        驗證配置是否有效
        返回 (is_valid: bool, error_message: str)
        """
        required_keys = ['model_a', 'model_b', 'arbitrator']
        
        for key in required_keys:
            if key not in config:
                return False, f"缺少必要的欄位: {key}"
            
            model_id = config[key]
            model = self.get_model_by_id(model_id)
            
            if not model:
                return False, f"無效的模型 ID: {model_id}"
            
            if not model['available']:
                return False, f"模型 {model['name']} ({model['platform']}) 未配置 API Key"
        
        # 檢查 Model A 和 Model B 不能相同
        if config['model_a'] == config['model_b']:
            return False, "Model A 和 Model B 不能相同"
        
        return True, ""
    
    def get_config_summary(self) -> Dict:
        """獲取配置摘要"""
        model_a = self.get_model_by_id(self.config['model_a'])
        model_b = self.get_model_by_id(self.config['model_b'])
        arbitrator = self.get_model_by_id(self.config['arbitrator'])
        
        return {
            'model_a': {
                'id': self.config['model_a'],
                'name': model_a['name'] if model_a else 'Unknown',
                'platform': model_a['platform'] if model_a else 'Unknown'
            },
            'model_b': {
                'id': self.config['model_b'],
                'name': model_b['name'] if model_b else 'Unknown',
                'platform': model_b['platform'] if model_b else 'Unknown'
            },
            'arbitrator': {
                'id': self.config['arbitrator'],
                'name': arbitrator['name'] if arbitrator else 'Unknown',
                'platform': arbitrator['platform'] if arbitrator else 'Unknown'
            }
        }
