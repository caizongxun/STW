"""
倉位感知版 DeepSeek-R1 交易決策引擎
- 能讀取當前倉位和本金
- 自動調整槓桿
- 智能風控決策
- 重試機制
"""
import json
import re
import time
from typing import Dict, Optional
from langchain_ollama import OllamaLLM


class PositionAwareDeepSeekAgent:
    """
    倉位感知版 DeepSeek 引擎
    能根據當前倉位、本金、風險做智能決策
    """
    
    def __init__(self, model_name: str = "deepseek-r1:14b", max_retries: int = 3):
        self.model = OllamaLLM(
            model=model_name,
            temperature=0.1,
            num_predict=2048
        )
        self.max_retries = max_retries
    
    def analyze_with_position(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """
        結合帳戶資訊的 AI 分析 (帶重試)
        """
        for attempt in range(self.max_retries):
            try:
                print(f"AI 分析嘗試 {attempt + 1}/{self.max_retries}...")
                
                prompt = self._build_prompt(market_data, account_info, position_info)
                response = self.model.invoke(prompt)
                
                # 清理回應
                response = self._clean_response(response)
                
                # 解析
                decision = self._parse_response(response)
                
                # 驗證成功
                if decision['action'] != 'HOLD' or decision.get('error') is None:
                    print(f"AI 分析成功: {decision['action']} (信心度 {decision['confidence']}%)")
                    return decision
                
                print(f"嘗試 {attempt + 1} 失敗: {decision.get('error')}")
                time.sleep(1)
                
            except Exception as e:
                print(f"嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
        
        # 所有嘗試都失敗，返回安全預設
        return self._get_safe_default()
    
    def _clean_response(self, response: str) -> str:
        """清理 AI 回應中的常見問題"""
        # 移除 null
        response = response.replace(': null', ': 0.0')
        response = response.replace(':null', ':0.0')
        
        # 移除計算式 (e.g. "entry_price": 65505.24 - 100)
        response = re.sub(r'("\w+"\s*:\s*[\d.]+)\s*[-+*/]\s*[\d.]+', r'\1', response)
        
        # 移除 JSON 中的註釋
        response = re.sub(r'//.*?\n', '\n', response)
        response = re.sub(r'/\*.*?\*/', '', response, flags=re.DOTALL)
        
        return response
    
    def _build_prompt(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> str:
        """構建完整 Prompt"""
        
        prompt = f"""You are a professional cryptocurrency quantitative trader with full account and position information.

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
        
        prompt += f"""

[MARKET INDICATORS]
Symbol: {market_data.get('symbol', 'UNKNOWN')}
Price: ${market_data.get('close', 0):,.2f}

RSI: {market_data.get('rsi', 50):.2f}
BB Position: {market_data.get('bb_position', 0.5):.2f} (0=lower, 1=upper)
ATR: ${market_data.get('atr', 0):,.2f}
MACD Hist: {market_data.get('macd_hist', 0):.4f}
ADX: {market_data.get('adx', 0):.2f}
Volume Ratio: {market_data.get('volume_ratio', 1.0):.2f}

[CRITICAL JSON REQUIREMENTS]
1. NEVER use null - always use 0 or 0.0
2. NEVER write calculations (65505.24 - 100) - only final numbers
3. NEVER add comments in JSON
4. ALL numeric fields must be valid numbers
5. Wrap JSON in ```json and ``` tags

[TASK]
Provide trading decision in STRICT JSON format:

```json
{{
  "action": "OPEN_LONG",
  "confidence": 75,
  "leverage": 2,
  "position_size_usdt": 200.0,
  "entry_price": {market_data.get('close', 0)},
  "stop_loss": {market_data.get('close', 0) * 0.98},
  "take_profit": {market_data.get('close', 0) * 1.02},
  "reasoning": "Brief decision reason",
  "risk_assessment": "LOW"
}}
```

Valid actions: OPEN_LONG, OPEN_SHORT, CLOSE, ADD_POSITION, REDUCE_POSITION, HOLD
Valid risk: LOW, MEDIUM, HIGH
Leverage: 1-{account_info.get('max_leverage', 10)}
Max position size: ${account_info['available_balance'] * 0.3:,.0f} USDT (30% of available)
"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析 DeepSeek 回答"""
        try:
            # 提取 JSON
            json_str = self._extract_json(response)
            
            if not json_str:
                raise ValueError("No JSON found in response")
            
            # 解析 JSON
            decision = json.loads(json_str)
            
            # 標準化和驗證
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
        # 嘗試 1: ```json ... ```
        if '```json' in response:
            json_start = response.find('```json') + 7
            json_end = response.find('```', json_start)
            if json_end > json_start:
                return response[json_start:json_end].strip()
        
        # 嘗試 2: ``` ... ```
        if '```' in response:
            json_start = response.find('```') + 3
            json_end = response.find('```', json_start)
            if json_end > json_start:
                return response[json_start:json_end].strip()
        
        # 嘗試 3: 尋找 { ... }
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
        
        # 驗證值範圍
        valid_actions = ['OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'ADD_POSITION', 'REDUCE_POSITION', 'HOLD']
        if normalized['action'] not in valid_actions:
            normalized['action'] = 'HOLD'
        
        valid_risks = ['LOW', 'MEDIUM', 'HIGH']
        if normalized['risk_assessment'] not in valid_risks:
            normalized['risk_assessment'] = 'MEDIUM'
        
        # 確保數値合理
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
