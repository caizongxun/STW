"""
倉位感知版 DeepSeek-R1 交易決策引擎
- 能讀取當前倉位和本金
- 自動調整槓杆
- 智能風控決策
"""
import json
import re
from typing import Dict, Optional
from langchain_ollama import OllamaLLM


class PositionAwareDeepSeekAgent:
    """
    倉位感知版 DeepSeek 引擎
    能根據當前倉位、本金、風險做智能決策
    """
    
    def __init__(self, model_name: str = "deepseek-r1:14b"):
        self.model = OllamaLLM(
            model=model_name,
            temperature=0.1,
            num_predict=2048
        )
    
    def analyze_with_position(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """
        結合帳戶資訊的 AI 分析
        
        Args:
            market_data: 市場數據
                {
                    'symbol': 'BTCUSDT',
                    'close': 65505.24,
                    'rsi': 31.48,
                    'bb_position': 0.15,
                    'atr': 284.12,
                    ...
                }
            
            account_info: 帳戶資訊
                {
                    'total_equity': 100000.0,
                    'available_balance': 95000.0,
                    'unrealized_pnl': 250.0,
                    'max_leverage': 10
                }
            
            position_info: 當前持倉 (可選)
                {
                    'side': 'Buy'/'Sell',
                    'size': 0.001,
                    'entry_price': 65000.0,
                    'current_price': 65505.24,
                    'unrealized_pnl': 50.52,
                    'leverage': 1
                }
        
        Returns:
            {
                'action': 'OPEN_LONG'/'OPEN_SHORT'/'CLOSE'/'ADD_POSITION'/'REDUCE_POSITION'/'HOLD',
                'confidence': 75,
                'leverage': 2,  # 建議槓杆
                'position_size_usdt': 200.0,  # 建議下單金額
                'entry_price': 65505.24,
                'stop_loss': 65221.12,
                'take_profit': 66073.48,
                'reasoning': 'str',
                'risk_assessment': 'LOW'/'MEDIUM'/'HIGH'
            }
        """
        # 構建 Prompt
        prompt = self._build_prompt(market_data, account_info, position_info)
        
        try:
            # 調用 DeepSeek
            response = self.model.invoke(prompt)
            
            # 清理 null 和計算式
            response = response.replace(': null', ': 0.0')
            response = re.sub(r'("\w+"\s*:\s*[\d.]+)\s*[-+*/]\s*[\d.]+', r'\1', response)
            
            # 解析回答
            decision = self._parse_response(response)
            
            return decision
            
        except Exception as e:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'reasoning': f'AI 分析失敗: {str(e)}',
                'risk_assessment': 'HIGH',
                'error': str(e)
            }
    
    def _build_prompt(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> str:
        """構建完整 Prompt"""
        
        prompt = f"""你是專業的加密貨幣量化交易員，擁有完整的帳戶和倉位資訊。

【當前帳戶狀況】
總資產：${account_info['total_equity']:,.2f} USDT
可用餘額：${account_info['available_balance']:,.2f} USDT
未實現盈虧：${account_info.get('unrealized_pnl', 0):+,.2f} USDT
最大槓杆：{account_info.get('max_leverage', 10)}x
"""
        
        # 如果有持倉
        if position_info:
            side_cn = '多單' if position_info['side'] == 'Buy' else '空單'
            pnl_pct = (position_info['unrealized_pnl'] / (position_info['entry_price'] * position_info['size'])) * 100
            
            prompt += f"""
【當前持倉】
方向：{side_cn} ({position_info['side']})
數量：{position_info['size']:.4f} BTC
進場價：${position_info['entry_price']:,.2f}
當前價：${position_info['current_price']:,.2f}
浮盈浮虧：${position_info['unrealized_pnl']:+,.2f} USDT ({pnl_pct:+.2f}%)
槓杆：{position_info.get('leverage', 1)}x
倉位價值：${position_info['entry_price'] * position_info['size']:,.2f} USDT
"""
        else:
            prompt += "\n【當前持倉】\n無持倉\n"
        
        # 市場數據
        prompt += f"""

【市場技術指標】
幣種：{market_data.get('symbol', 'UNKNOWN')}
當前價：${market_data.get('close', 0):,.2f}

RSI：{market_data.get('rsi', 50):.2f}
BB Position：{market_data.get('bb_position', 0.5):.2f} (布林帶位置: 0=下軌, 1=上軌)
ATR：${market_data.get('atr', 0):,.2f} (波動度)
MACD Hist：{market_data.get('macd_hist', 0):.4f}
ADX：{market_data.get('adx', 0):.2f} (趋勢強度)
Volume Ratio：{market_data.get('volume_ratio', 1.0):.2f}
EMA 9/21/50: ${market_data.get('ema9', 0):,.0f} / ${market_data.get('ema21', 0):,.0f} / ${market_data.get('ema50', 0):,.0f}
"""
        
        # 決策要求
        prompt += f"""

【任務要求】
請根據以上資訊，給出智能交易決策。

決策框架：

1. **如果無持倉**：
   - 評估是否開倉（OPEN_LONG / OPEN_SHORT / HOLD）
   - 計算合理的槓杆（1-{account_info.get('max_leverage', 10)}x）
   - 根據 ATR 計算止損止盈
   - 建議下單金額（不超過可用餘額的 30%）

2. **如果有持倉**：
   a. 如果浮盈 > 5%：
      - 考慮加倉（ADD_POSITION）或減倉（REDUCE_POSITION）
   
   b. 如果浮虧 < -3%：
      - 考慮止損（CLOSE）或繼續持有（HOLD）
   
   c. 如果方向與當前訊號相反：
      - 先平倉（CLOSE），再考慮反向開倉

3. **槓杆選擇原則**：
   - 信心度 > 80%：ATR < 300 → 可用 2-3x
   - 信心度 70-80%：ATR < 500 → 用 1-2x
   - 信心度 < 70% 或 ATR > 500 → 只用 1x

4. **風險評估**：
   - LOW: RSI 在 30-70，ADX > 25，成交量正常
   - MEDIUM: RSI 超賣/超買，或 ADX < 25
   - HIGH: 極端 RSI (<20 or >80)，或 ATR 異常大

⚠️ CRITICAL JSON RULES:
- NEVER use null - use 0 or 0.0
- NEVER write math expressions - only final numbers
- NEVER include comments in JSON

必須以 JSON 格式回答：
```json
{{
  "action": "OPEN_LONG",
  "confidence": 75,
  "leverage": 2,
  "position_size_usdt": 200.0,
  "entry_price": 65505.24,
  "stop_loss": 65221.12,
  "take_profit": 66073.48,
  "reasoning": "簡潔說明決策理由，包含倉位管理逻輯",
  "risk_assessment": "LOW"
}}
```

注意：
- action 可選項：OPEN_LONG, OPEN_SHORT, CLOSE, ADD_POSITION, REDUCE_POSITION, HOLD
- leverage 範圍：1-{account_info.get('max_leverage', 10)}
- position_size_usdt 不能超過可用餘額的 30%（約 ${account_info['available_balance'] * 0.3:,.0f} USDT）
- risk_assessment 只能是 LOW, MEDIUM, HIGH
"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析 DeepSeek 回答"""
        try:
            # 提取 JSON
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '```' in response:
                json_start = response.find('```') + 3
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            # 清理 null 和計算式
            json_str = json_str.replace(': null', ': 0.0')
            json_str = re.sub(r'("\w+"\s*:\s*[\d.]+)\s*[-+*/]\s*[\d.]+', r'\1', json_str)
            
            decision = json.loads(json_str)
            
            # 驗證和標準化
            decision['action'] = decision.get('action', 'HOLD').upper()
            decision['confidence'] = int(decision.get('confidence', 0) or 0)
            decision['leverage'] = int(decision.get('leverage', 1) or 1)
            decision['position_size_usdt'] = float(decision.get('position_size_usdt', 0) or 0)
            decision['entry_price'] = float(decision.get('entry_price', 0) or 0)
            decision['stop_loss'] = float(decision.get('stop_loss', 0) or 0)
            decision['take_profit'] = float(decision.get('take_profit', 0) or 0)
            decision['risk_assessment'] = decision.get('risk_assessment', 'MEDIUM').upper()
            
            # 驗證值範圍
            if decision['action'] not in ['OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'ADD_POSITION', 'REDUCE_POSITION', 'HOLD']:
                decision['action'] = 'HOLD'
            
            if decision['risk_assessment'] not in ['LOW', 'MEDIUM', 'HIGH']:
                decision['risk_assessment'] = 'MEDIUM'
            
            return decision
            
        except Exception as e:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'reasoning': f'JSON 解析失敗: {str(e)}',
                'risk_assessment': 'HIGH',
                'error': str(e)
            }
