"""
多 API 管理器
统一使用 DeepSeek-R1 类推理模型，但从不同 API 提供商輪转
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
            print(f"⚠️ {self.name} 連續失敗 3 次，暫時停用")
    
    def reset_availability(self):
        """重置可用性"""
        self.failure_count = 0
        self.is_available = True


class MultiAPIManager:
    """
    多 API 管理器
    统一使用 DeepSeek-R1 或类似的推理模型
    """
    
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
        统一使用 DeepSeek-R1 类模型
        """
        
        # 1. OpenRouter - DeepSeek-R1 原生版 (免費，推理最強)
        if os.getenv('OPENROUTER_API_KEY'):
            self.providers.append(APIProvider(
                name='OpenRouter_R1',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-r1:free',  # DeepSeek-R1 原生
                rpm_limit=20,
                daily_limit=1000,
                priority=5  # 最高優先級
            ))
            
            # OpenRouter - R1 Distill Llama 70B (免費，速度快)
            self.providers.append(APIProvider(
                name='OpenRouter_R1_Distill',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-r1-distill-llama-70b:free',  # R1 蒸駏版
                rpm_limit=20,
                daily_limit=1000,
                priority=4
            ))
            
            # OpenRouter - R1 Distill Qwen (免費)
            self.providers.append(APIProvider(
                name='OpenRouter_R1_Qwen',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-r1-distill-qwen-32b:free',  # R1 蒸駏 Qwen
                rpm_limit=20,
                daily_limit=1000,
                priority=4
            ))
        
        # 2. Groq - DeepSeek-R1 Distill Llama (速度超快)
        if os.getenv('GROQ_API_KEY'):
            self.providers.append(APIProvider(
                name='Groq_R1_Distill',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='deepseek-r1-distill-llama-70b',  # Groq 版 R1
                rpm_limit=30,
                daily_limit=14400,
                priority=5  # 速度快
            ))
        
        # 3. GitHub Models - GPT-4o-mini (備用，非 R1 但質量好)
        if os.getenv('GITHUB_TOKEN'):
            self.providers.append(APIProvider(
                name='GitHub_GPT4o_mini',
                api_key=os.getenv('GITHUB_TOKEN'),
                base_url='https://models.inference.ai.azure.com',
                model='gpt-4o-mini',
                rpm_limit=10,
                daily_limit=1000,
                priority=3  # 備用
            ))
        
        # 4. Cloudflare - Llama 3.1 (備用，高額度)
        cf_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        cf_api_key = os.getenv('CLOUDFLARE_API_KEY')
        if cf_account_id and cf_api_key:
            self.providers.append(APIProvider(
                name='Cloudflare_Llama',
                api_key=cf_api_key,
                base_url=f'https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1',
                model='@cf/meta/llama-3.1-8b-instruct',
                rpm_limit=100,
                daily_limit=10000,
                priority=2  # 備用
            ))
        
        # 5. Google Gemini - Gemini 2.0 Flash (備用，非 R1 但質量極佳)
        if os.getenv('GOOGLE_API_KEY'):
            self.providers.append(APIProvider(
                name='Google_Gemini_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='https://generativelanguage.googleapis.com/v1beta',
                model='gemini-2.0-flash-exp',
                rpm_limit=15,
                daily_limit=1500,
                priority=3  # 備用
            ))
        
        print(f"\n✅ 已配置 {len(self.providers)} 個 API 提供商 (主要使用 DeepSeek-R1 系列)")
        for p in self.providers:
            print(f"  - {p.name}: {p.model} (優先級 {p.priority})")
    
    def get_available_provider(self, purpose: str = 'general') -> Optional[APIProvider]:
        """
        獲取可用的 API 提供商
        優先使用 DeepSeek-R1 类模型
        
        Args:
            purpose: 用途 ('fast', 'reasoning', 'position', 'general')
        """
        # 根據用途選擇優先級
        priority_map = {
            'fast': ['Groq_R1_Distill', 'OpenRouter_R1_Distill'],  # 速度優先
            'reasoning': ['OpenRouter_R1', 'OpenRouter_R1_Distill'],  # 推理優先
            'position': ['Groq_R1_Distill', 'OpenRouter_R1'],  # 倉位控制：快速+準確
            'general': None  # 按優先級排序
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
        
        print("⚠️ 所有 API 提供商都不可用")
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
            
            print(f"✅ 從 {self.config_file} 載入配置")
        except Exception as e:
            print(f"⚠️ 載入配置失敗: {e}")
    
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
