"""
倉位感知版 DeepSeek-R1 交易決策引擎
- 能讀取當前倉位和本金
- 自動調整槓桿
- 智能風控決策
- 重試機制
- 波段交易策略
- 多 API 輪轉支持
"""
import json
import re
import time
import os
from typing import Dict, Optional, List

try:
    from core.multi_api_manager import MultiAPIManager
    HAS_MULTI_API = True
except ImportError:
    HAS_MULTI_API = False
    print("警告: 未找到 MultiAPIManager，將使用 Ollama")

try:
    from langchain_ollama import OllamaLLM
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class PositionAwareDeepSeekAgent:
    """
    倉位感知版 DeepSeek 引擎
    支持波段交易和趨勢追蹤
    支持多 API 輪轉 (Gemini, Groq, OpenRouter, Ollama)
    """
    
    def __init__(self, model_name: str = "deepseek-r1:14b", max_retries: int = 3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.position_history: List[Dict] = []  # 持倉歷史
        self.last_signal: Optional[str] = None  # 上次訊號
        self.trend_direction: Optional[str] = None  # 當前趨勢
        
        # 初始化 API 管理器
        self.api_manager = None
        self.ollama_model = None
        
        if HAS_MULTI_API:
            try:
                self.api_manager = MultiAPIManager()
                if len(self.api_manager.providers) > 0:
                    print(f"✅ 多 API 管理器已启用: {len(self.api_manager.providers)} 個 API")
                else:
                    print("⚠️ 沒有可用的免費 API，嘗試使用 Ollama...")
                    self.api_manager = None
            except Exception as e:
                print(f"⚠️ 多 API 初始化失敗: {e}，嘗試使用 Ollama...")
                self.api_manager = None
        
        # 如果沒有多 API，使用 Ollama
        if not self.api_manager and HAS_OLLAMA:
            try:
                self.ollama_model = OllamaLLM(
                    model=model_name,
                    temperature=0.1,
                    num_predict=2048
                )
                print(f"✅ 使用 Ollama 本地模型: {model_name}")
            except Exception as e:
                print(f"❌ Ollama 初始化失敗: {e}")
        
        # 檢查是否有任何可用的 AI
        if not self.api_manager and not self.ollama_model:
            print("❌ 警告: 沒有可用的 AI 模型！")
            print("請至少配置一個：")
            print("  1. 免費 API (設定頁面)")
            print("  2. Ollama (pip install langchain-ollama && ollama pull deepseek-r1:14b)")
    
    def _call_llm(self, prompt: str, purpose: str = 'position') -> str:
        """調用 LLM（多 API 或 Ollama）"""
        
        # 優先使用多 API 管理器
        if self.api_manager:
            provider = self.api_manager.get_available_provider(purpose=purpose)
            
            if provider:
                try:
                    print(f"🤖 使用 API: {provider.name} ({provider.model})")
                    
                    provider.record_request()
                    
                    # Google Gemini
                    if provider.name.startswith('Google') and HAS_GEMINI:
                        response = self._call_gemini(prompt, provider)
                    
                    # 其他 OpenAI 相容 API (Groq, OpenRouter, GitHub)
                    else:
                        response = self._call_openai_compatible(prompt, provider)
                    
                    provider.record_success()
                    print(f"✅ {provider.name} 請求成功")
                    return response
                    
                except Exception as e:
                    print(f"❌ {provider.name} 請求失敗: {e}")
                    provider.record_failure()
                    # 嘗試下一個 API
                    return self._call_llm_fallback(prompt)
        
        # 備用: 使用 Ollama
        if self.ollama_model:
            print(f"🤖 使用 Ollama: {self.model_name}")
            try:
                response = self.ollama_model.invoke(prompt)
                print("✅ Ollama 請求成功")
                return response
            except Exception as e:
                print(f"❌ Ollama 請求失敗: {e}")
                raise
        
        raise RuntimeError("所有 API 都不可用，且沒有安裝 Ollama")
    
    def _call_llm_fallback(self, prompt: str) -> str:
        """備用 LLM 調用（當首選 API 失敗）"""
        if self.api_manager:
            # 嘗試下一個可用的 API
            for provider in self.api_manager.providers:
                if provider.can_request():
                    try:
                        print(f"🔄 嘗試備用 API: {provider.name}")
                        provider.record_request()
                        
                        if provider.name.startswith('Google') and HAS_GEMINI:
                            response = self._call_gemini(prompt, provider)
                        else:
                            response = self._call_openai_compatible(prompt, provider)
                        
                        provider.record_success()
                        print(f"✅ {provider.name} 備用成功")
                        return response
                    except Exception as e:
                        print(f"❌ {provider.name} 備用失敗: {e}")
                        provider.record_failure()
                        continue
        
        # 最後嘗試 Ollama
        if self.ollama_model:
            print("🔄 所有免費 API 失敗，使用 Ollama")
            return self.ollama_model.invoke(prompt)
        
        raise RuntimeError("所有 API 都失敗，且沒有 Ollama")
    
    def _call_gemini(self, prompt: str, provider) -> str:
        """調用 Google Gemini API"""
        genai.configure(api_key=provider.api_key)
        model = genai.GenerativeModel(provider.model)
        response = model.generate_content(prompt)
        return response.text
    
    def _call_openai_compatible(self, prompt: str, provider) -> str:
        """調用 OpenAI 相容 API (Groq, OpenRouter, GitHub)"""
        import requests
        
        headers = {
            'Authorization': f'Bearer {provider.api_key}',
            'Content-Type': 'application/json'
        }
        
        # GitHub Models 特殊處理
        if provider.name.startswith('GitHub'):
            headers['Authorization'] = f'token {provider.api_key}'
        
        data = {
            'model': provider.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.1,
            'max_tokens': 2048
        }
        
        # OpenRouter 特殊處理
        if provider.name.startswith('OpenRouter'):
            data['route'] = 'fallback'
        
        url = f"{provider.base_url}/chat/completions"
        
        print(f"  請求 URL: {url}")
        print(f"  模型: {provider.model}")
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        # 詳細錯誤資訊
        if response.status_code != 200:
            print(f"  狀態碼: {response.status_code}")
            print(f"  回應: {response.text[:500]}")
        
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def analyze_with_position(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """
        結合帳戶資訊的 AI 分析 (帶重試 + 波段策略)
        """
        for attempt in range(self.max_retries):
            try:
                print(f"AI 分析嘗試 {attempt + 1}/{self.max_retries}...")
                
                prompt = self._build_prompt(market_data, account_info, position_info)
                response = self._call_llm(prompt, purpose='position')
                
                # 清理回應
                response = self._clean_response(response)
                
                # 解析
                decision = self._parse_response(response)
                
                # 應用波段策略過濾
                decision = self._apply_swing_strategy(decision, market_data, position_info)
                
                # 驗證成功
                if decision['action'] != 'HOLD' or decision.get('error') is None:
                    print(f"✅ AI 分析成功: {decision['action']} (信心度 {decision['confidence']}%)")
                    
                    # 更新狀態
                    self.last_signal = decision['action']
                    if decision['action'] in ['OPEN_LONG', 'OPEN_SHORT']:
                        self.trend_direction = 'LONG' if decision['action'] == 'OPEN_LONG' else 'SHORT'
                    
                    return decision
                
                print(f"嘗試 {attempt + 1} 失敗: {decision.get('error')}")
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 嘗試 {attempt + 1} 失敗: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
        
        # 所有嘗試都失敗
        print("❌ 所有 AI 分析嘗試都失敗")
        return self._get_safe_default()
    
    def _apply_swing_strategy(
        self,
        decision: Dict,
        market_data: Dict,
        position_info: Optional[Dict]
    ) -> Dict:
        """
        應用波段交易策略過濾
        
        策略規則:
        1. 有持倉時，不輕易反向開倉
        2. 趨勢未確認反轉前，保持原趨勢
        3. 需要高信心度 + 技術指標確認才能反向
        """
        action = decision['action']
        confidence = decision['confidence']
        
        # 如果當前有持倉
        if position_info and position_info.get('size', 0) > 0:
            current_side = position_info['side']  # 'Buy' or 'Sell'
            unrealized_pnl = position_info.get('unrealized_pnl', 0)
            entry_price = position_info.get('entry_price', 0)
            current_price = market_data.get('close', 0)
            
            # 計算持倉盈虧百分比
            pnl_pct = (unrealized_pnl / (entry_price * position_info['size'])) * 100 if entry_price > 0 else 0
            
            print(f"\n當前持倉: {current_side}, 盈虧: {pnl_pct:.2f}%")
            
            # 規則 1: 有盈利持倉，不輕易平倉
            if pnl_pct > 2.0 and action == 'CLOSE':
                if confidence < 80:
                    print("過濾: 盈利持倉，且信心度不足，繼續持有")
                    decision['action'] = 'HOLD'
                    decision['reasoning'] = '盈利持倉中，等待更強訊號'
            
            # 規則 2: 有持倉時，不允許直接反向開倉
            is_reverse_signal = (
                (current_side == 'Buy' and action == 'OPEN_SHORT') or
                (current_side == 'Sell' and action == 'OPEN_LONG')
            )
            
            if is_reverse_signal:
                # 需要高信心度 + 技術指標確認
                rsi = market_data.get('rsi', 50)
                adx = market_data.get('adx', 0)
                
                # 反轉條件: 信心度 > 75 且 RSI 過熟/超賣 且 ADX > 25
                reverse_confirmed = (
                    confidence > 75 and
                    adx > 25 and
                    ((action == 'OPEN_SHORT' and rsi > 70) or (action == 'OPEN_LONG' and rsi < 30))
                )
                
                if not reverse_confirmed:
                    print(f"過濾: 反向訊號未確認 (信心度 {confidence}%, RSI {rsi:.1f}, ADX {adx:.1f})")
                    # 不反向，但可以平倉
                    decision['action'] = 'CLOSE'
                    decision['reasoning'] = '趨勢可能反轉，先平倉觀望'
                else:
                    print("反轉訊號確認，允許反向開倉")
            
            # 規則 3: 止損保護 (虧損 > 5%)
            if pnl_pct < -5.0:
                print(f"觸發止損: 虧損 {pnl_pct:.2f}%")
                decision['action'] = 'CLOSE'
                decision['reasoning'] = f'止損出場 (虧損 {pnl_pct:.2f}%)'
        
        # 規則 4: 無持倉時，避免頻繁交易
        else:
            # 如果上次訊號和這次相反，且時間過短，避免開倉
            if self.last_signal in ['OPEN_LONG', 'OPEN_SHORT']:
                is_opposite = (
                    (self.last_signal == 'OPEN_LONG' and action == 'OPEN_SHORT') or
                    (self.last_signal == 'OPEN_SHORT' and action == 'OPEN_LONG')
                )
                
                if is_opposite and confidence < 80:
                    print(f"過濾: 與上次訊號 ({self.last_signal}) 相反，且信心度不足")
                    decision['action'] = 'HOLD'
                    decision['reasoning'] = '等待趨勢明朗'
        
        return decision
    
    def _clean_response(self, response: str) -> str:
        """清理 AI 回應中的常見問題"""
        # 移除 null
        response = response.replace(': null', ': 0.0')
        response = response.replace(':null', ':0.0')
        
        # 移除所有數學運算式 (e.g. "70359.7 - (2 * 267.93)")
        # 匹配: 數字 + 任何運算符 + 任何內容 + = + 數字
        response = re.sub(r'("\w+"\s*:\s*)([\d.]+)\s*[-+*/()].*?=\s*([\d.]+)', r'\1\3', response)
        
        # 移除簡單的運算式 (e.g. "65505.24 - 100")
        response = re.sub(r'("\w+"\s*:\s*)([\d.]+)\s*[-+*/]\s*[\d.()]+', r'\1\2', response)
        
        # 移除 JSON 中的註釋
        response = re.sub(r'//.*?\n', '\n', response)
        response = re.sub(r'/\*.*?\*/', '', response, flags=re.DOTALL)
        
        return response
    
    def _build_prompt(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> str:
        """構建完整 Prompt (波段交易版)"""
        
        prompt = f"""You are a professional swing trader focusing on trend-following strategies.

[ACCOUNT STATUS]
Total Assets: ${account_info['total_equity']:,.2f} USDT
Available Balance: ${account_info['available_balance']:,.2f} USDT
Unrealized PnL: ${account_info.get('unrealized_pnl', 0):+,.2f} USDT
Max Leverage: {account_info.get('max_leverage', 10)}x
"""
        
        if position_info:
            side_text = 'Long' if position_info['side'] == 'Buy' else 'Short'
            pnl_pct = (position_info['unrealized_pnl'] / (position_info['entry_price'] * position_info['size'])) * 100
            
            prompt += f"""
[CURRENT POSITION]
Direction: {side_text}
Size: {position_info['size']:.4f} BTC
Entry Price: ${position_info['entry_price']:,.2f}
Current Price: ${position_info['current_price']:,.2f}
Unrealized PnL: ${position_info['unrealized_pnl']:+,.2f} ({pnl_pct:+.2f}%)
Leverage: {position_info.get('leverage', 1)}x
"""
        else:
            prompt += "\n[CURRENT POSITION]\nNo position\n"
        
        # 添加上次訊號資訊
        if self.last_signal:
            prompt += f"\n[LAST SIGNAL]\n{self.last_signal}\n"
        
        prompt += f"""

[MARKET INDICATORS]
Symbol: {market_data.get('symbol', 'UNKNOWN')}
Price: ${market_data.get('close', 0):,.2f}

RSI: {market_data.get('rsi', 50):.2f}
BB Position: {market_data.get('bb_position', 0.5):.2f}
ATR: ${market_data.get('atr', 0):,.2f}
MACD Hist: {market_data.get('macd_hist', 0):.4f}
ADX: {market_data.get('adx', 0):.2f}
Volume Ratio: {market_data.get('volume_ratio', 1.0):.2f}

[SWING TRADING RULES]
1. If you have a profitable position (>2%), DO NOT close unless very strong reversal signal
2. If you have a position, DO NOT reverse direction unless confidence >75% AND clear technical confirmation
3. Avoid frequent trading - wait for clear trend confirmation
4. Stop loss at -5% unrealized PnL
5. Focus on trend-following, not short-term noise

[CRITICAL JSON REQUIREMENTS]
1. NEVER use calculations like "70359.7 - (2 * 267.93)"
2. ONLY use final numbers: "stop_loss": 69823.84
3. NEVER use null - always use 0 or 0.0
4. NO comments in JSON
5. Wrap JSON in ```json and ``` tags

[TASK]
Provide swing trading decision:

```json
{{
  "action": "HOLD",
  "confidence": 60,
  "leverage": 1,
  "position_size_usdt": 100.0,
  "entry_price": {market_data.get('close', 0)},
  "stop_loss": {market_data.get('close', 0) * 0.95},
  "take_profit": {market_data.get('close', 0) * 1.05},
  "reasoning": "Brief reason for decision",
  "risk_assessment": "LOW"
}}
```

Valid actions: OPEN_LONG, OPEN_SHORT, CLOSE, ADD_POSITION, REDUCE_POSITION, HOLD
Valid risk: LOW, MEDIUM, HIGH
"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析 DeepSeek 回答"""
        try:
            json_str = self._extract_json(response)
            
            if not json_str:
                raise ValueError("No JSON found in response")
            
            decision = json.loads(json_str)
            decision = self._normalize_decision(decision)
            
            return decision
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Problematic JSON: {json_str[:200]}...")
            return self._get_safe_default(f'JSON 解析失敗: {str(e)}')
            
        except Exception as e:
            print(f"Parse error: {e}")
            return self._get_safe_default(f'解析錯誤: {str(e)}')
    
    def _extract_json(self, response: str) -> str:
        """從回應中提取 JSON"""
        if '```json' in response:
            json_start = response.find('```json') + 7
            json_end = response.find('```', json_start)
            if json_end > json_start:
                return response[json_start:json_end].strip()
        
        if '```' in response:
            json_start = response.find('```') + 3
            json_end = response.find('```', json_start)
            if json_end > json_start:
                return response[json_start:json_end].strip()
        
        first_brace = response.find('{')
        last_brace = response.rfind('}')
        if first_brace >= 0 and last_brace > first_brace:
            return response[first_brace:last_brace+1].strip()
        
        return ""
    
    def _normalize_decision(self, decision: Dict) -> Dict:
        """標準化和驗證決策"""
        normalized = {
            'action': str(decision.get('action', 'HOLD')).upper(),
            'confidence': int(float(decision.get('confidence', 0) or 0)),
            'leverage': int(float(decision.get('leverage', 1) or 1)),
            'position_size_usdt': float(decision.get('position_size_usdt', 0) or 0),
            'entry_price': float(decision.get('entry_price', 0) or 0),
            'stop_loss': float(decision.get('stop_loss', 0) or 0),
            'take_profit': float(decision.get('take_profit', 0) or 0),
            'reasoning': str(decision.get('reasoning', 'No reasoning provided')),
            'risk_assessment': str(decision.get('risk_assessment', 'MEDIUM')).upper()
        }
        
        valid_actions = ['OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'ADD_POSITION', 'REDUCE_POSITION', 'HOLD']
        if normalized['action'] not in valid_actions:
            normalized['action'] = 'HOLD'
        
        valid_risks = ['LOW', 'MEDIUM', 'HIGH']
        if normalized['risk_assessment'] not in valid_risks:
            normalized['risk_assessment'] = 'MEDIUM'
        
        normalized['confidence'] = max(0, min(100, normalized['confidence']))
        normalized['leverage'] = max(1, min(10, normalized['leverage']))
        
        return normalized
    
    def _get_safe_default(self, error_msg: str = "AI analysis failed") -> Dict:
        """返回安全預設值"""
        return {
            'action': 'HOLD',
            'confidence': 0,
            'leverage': 1,
            'position_size_usdt': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'reasoning': error_msg,
            'risk_assessment': 'HIGH',
            'error': error_msg
        }
