"""
多 API 管理器
支持多個免費 API 輪換使用，自動故障轉移
2026 年 3 月更新 - 使用正確的 OpenRouter 模型 ID
"""
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class APIProvider:
    """一個 API 提供商配置"""
    name: str
    api_key: str
    base_url: str
    model: str
    rpm_limit: int  # 每分鐘請求數限制
    daily_limit: int  # 每日請求數限制
    priority: int = 1  # 優先級 (1-5, 5最高)
    
    # 運行時狀態
    request_count: int = 0
    daily_count: int = 0
    last_request_time: Optional[datetime] = None
    last_reset_date: Optional[str] = None
    is_available: bool = True
    failure_count: int = 0
    
    def can_request(self) -> bool:
        """檢查是否可以發起請求"""
        if not self.is_available:
            return False
        
        # 檢查每日限制
        today = datetime.now().strftime('%Y-%m-%d')
        if self.last_reset_date != today:
            self.daily_count = 0
            self.last_reset_date = today
        
        if self.daily_count >= self.daily_limit:
            return False
        
        # 檢查 RPM 限制
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < 60:
                if self.request_count >= self.rpm_limit:
                    return False
            else:
                self.request_count = 0
        
        return True
    
    def record_request(self):
        """記錄請求"""
        now = datetime.now()
        if self.last_request_time and (now - self.last_request_time).total_seconds() >= 60:
            self.request_count = 0
        
        self.request_count += 1
        self.daily_count += 1
        self.last_request_time = now
    
    def record_success(self):
        """記錄成功請求"""
        self.failure_count = 0
        self.is_available = True
    
    def record_failure(self):
        """記錄失敗請求"""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.is_available = False
            print(f"[WARN] {self.name} 連續失敗 3 次，暫時停用")
    
    def reset_availability(self):
        """重置可用性"""
        self.failure_count = 0
        self.is_available = True


class MultiAPIManager:
    """多 API 管理器"""
    
    def __init__(self, config_file: str = 'api_config.json'):
        self.config_file = config_file
        self.providers: List[APIProvider] = []
        self.load_config()
        
        # 如果沒有配置，使用預設配置
        if not self.providers:
            self._setup_default_providers()
    
    def _setup_default_providers(self):
        """
        設置預設 API 提供商
        2026 年 3 月正確的模型 ID
        """
        
        # 1. Groq - 最快且最穩定的免費 API (優先使用)
        if os.getenv('GROQ_API_KEY'):
            self.providers.append(APIProvider(
                name='Groq_Llama_3_3_70B',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile',
                rpm_limit=30,
                daily_limit=14400,
                priority=5  # 最高優先級
            ))
            
            self.providers.append(APIProvider(
                name='Groq_Mixtral_8x7B',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='mixtral-8x7b-32768',
                rpm_limit=30,
                daily_limit=14400,
                priority=4
            ))
        
        # 2. Google Gemini - 官方 API，非常穩定
        if os.getenv('GOOGLE_API_KEY'):
            self.providers.append(APIProvider(
                name='Google_Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='https://generativelanguage.googleapis.com/v1beta',
                model='gemini-2.0-flash',
                rpm_limit=15,
                daily_limit=1500,
                priority=5  # 提高優先級
            ))
        
        # 3. OpenRouter - 作為備用 (免費模型經常變動)
        if os.getenv('OPENROUTER_API_KEY'):
            # Llama 3.3 70B
            self.providers.append(APIProvider(
                name='OpenRouter_Llama_3_3_70B',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='meta-llama/llama-3.3-70b-instruct:free',
                rpm_limit=20,
                daily_limit=200,
                priority=3  # 作為備用
            ))
            
            # Gemini 2.0 Flash Exp
            self.providers.append(APIProvider(
                name='OpenRouter_Gemini_2_Flash',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='google/gemini-2.0-flash-exp:free',
                rpm_limit=20,
                daily_limit=200,
                priority=3
            ))
            
            # Mistral Small 3.1
            self.providers.append(APIProvider(
                name='OpenRouter_Mistral_Small',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='mistralai/mistral-small-3.1:free',
                rpm_limit=20,
                daily_limit=200,
                priority=3
            ))
            
            # Qwen 2.5 Coder
            self.providers.append(APIProvider(
                name='OpenRouter_Qwen_Coder',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='qwen/qwen-2.5-coder-32b-instruct:free',
                rpm_limit=20,
                daily_limit=200,
                priority=3
            ))
        
        # 4. GitHub Models
        if os.getenv('GITHUB_TOKEN'):
            self.providers.append(APIProvider(
                name='GitHub_GPT4o_mini',
                api_key=os.getenv('GITHUB_TOKEN'),
                base_url='https://models.inference.ai.azure.com',
                model='gpt-4o-mini',
                rpm_limit=10,
                daily_limit=1000,
                priority=4
            ))
        
        # 5. DeepSeek 官方 API (付費但極便宜)
        if os.getenv('DEEPSEEK_API_KEY'):
            self.providers.append(APIProvider(
                name='DeepSeek_Chat',
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url='https://api.deepseek.com/v1',
                model='deepseek-chat',
                rpm_limit=60,
                daily_limit=50000,
                priority=4
            ))
        
        # 6. Cloudflare Workers AI
        cf_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        cf_api_key = os.getenv('CLOUDFLARE_API_KEY')
        if cf_account_id and cf_api_key:
            self.providers.append(APIProvider(
                name='Cloudflare_Llama_3_1',
                api_key=cf_api_key,
                base_url=f'https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1',
                model='@cf/meta/llama-3.1-8b-instruct',
                rpm_limit=100,
                daily_limit=10000,
                priority=3
            ))
        
        print(f"\n[OK] 已配置 {len(self.providers)} 個 API 提供商 (2026 年 3 月正確模型)")
        for p in self.providers:
            status = "[HIGH]" if p.priority == 5 else "[OK]"
            print(f"  {status} {p.name}: {p.model} (優先級 {p.priority})")
    
    def get_available_provider(self, purpose: str = 'general') -> Optional[APIProvider]:
        """
        獲取可用的 API 提供商
        
        Args:
            purpose: 用途 ('fast', 'reasoning', 'position', 'general')
        """
        # 根據用途選擇優先級
        priority_map = {
            'fast': ['Groq_Llama_3_3_70B', 'Cloudflare_Llama_3_1'],
            'reasoning': ['Google_Gemini_2_Flash', 'Groq_Llama_3_3_70B'],
            'position': ['Groq_Llama_3_3_70B', 'Google_Gemini_2_Flash'],
            'general': None
        }
        
        preferred_names = priority_map.get(purpose)
        
        # 按優先級排序
        sorted_providers = sorted(
            self.providers,
            key=lambda p: p.priority,
            reverse=True
        )
        
        # 如果有指定優先提供商，先嘗試它們
        if preferred_names:
            for name in preferred_names:
                for provider in sorted_providers:
                    if provider.name == name and provider.can_request():
                        return provider
        
        # 否則按優先級返回第一個可用的
        for provider in sorted_providers:
            if provider.can_request():
                return provider
        
        print("[WARN] 所有 API 提供商都不可用")
        return None
    
    def save_config(self):
        """保存配置到文件"""
        config = {
            'providers': [
                {
                    'name': p.name,
                    'api_key': p.api_key,
                    'base_url': p.base_url,
                    'model': p.model,
                    'rpm_limit': p.rpm_limit,
                    'daily_limit': p.daily_limit,
                    'priority': p.priority,
                    'daily_count': p.daily_count,
                    'last_reset_date': p.last_reset_date,
                    'is_available': p.is_available
                }
                for p in self.providers
            ]
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def load_config(self):
        """從文件載入配置"""
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for p_config in config.get('providers', []):
                provider = APIProvider(**{
                    k: v for k, v in p_config.items()
                    if k in APIProvider.__dataclass_fields__
                })
                self.providers.append(provider)
            
            print(f"[OK] 從 {self.config_file} 載入配置")
        except Exception as e:
            print(f"[WARN] 載入配置失敗: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        return {
            'total_providers': len(self.providers),
            'available_providers': sum(1 for p in self.providers if p.is_available),
            'providers': [
                {
                    'name': p.name,
                    'model': p.model,
                    'daily_usage': f"{p.daily_count}/{p.daily_limit}",
                    'is_available': p.is_available,
                    'priority': p.priority
                }
                for p in self.providers
            ]
        }
