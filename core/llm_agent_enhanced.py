"""
升級版 DeepSeek-R1 交易決策引擎
支援從詳細成功案例中學習，注入40+技術指標到Prompt
"""
import json
import re
from pathlib import Path
from typing import Dict, List
from langchain_ollama import OllamaLLM
import pandas as pd


class EnhancedDeepSeekAgent:
    """強化版DeepSeek交易引擎，注入完整技術特徵的成功案例"""
    
    def __init__(self, model_name: str = "deepseek-r1:14b", cases_path: str = "data/detailed_success_cases.json"):
        self.model = OllamaLLM(
            model=model_name,
            temperature=0.1,  # 低溫度，提高一致性
            num_predict=2048
        )
        self.cases_path = Path(cases_path)
        self.success_cases = self._load_cases()
        
    def _load_cases(self) -> List[Dict]:
        """載入成功案例庫"""
        if not self.cases_path.exists():
            return []
        
        try:
            with open(self.cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cases = data.get('cases', [])
                print(f"✅ 已載入 {len(cases)} 個成功案例")
                return cases
        except Exception as e:
            print(f"⚠️ 載入案例失敗: {e}")
            return []
    
    def analyze_market(self, current_market: Dict, max_cases: int = 5) -> Dict:
        """
        分析市場並給出交易決策
        
        Args:
            current_market: 當前市場數據（包含40+技術指標）
            max_cases: 最多注入00b6個案例到Prompt
        
        Returns:
            {
                'signal': 'LONG'/'SHORT'/'HOLD',
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'confidence': int (0-100),
                'reasoning': str,
                'matched_cases': List[str]  # 匹配到的相似案例
            }
        """
        # 筛選相似案例
        similar_cases = self._find_similar_cases(current_market, max_cases)
        
        # 構建強化Prompt
        prompt = self._build_enhanced_prompt(current_market, similar_cases)
        
        try:
            # 調Ollama
            response = self.model.invoke(prompt)
            
            # ★★★ 關鍵修改：在接收 AI 輸出後立即暴力替換 null ★★★
            response = response.replace(': null', ': 0.0')
            response = response.replace(':null', ': 0.0')
            response = re.sub(r'"(entry_price|stop_loss|take_profit|position_size_pct)"\s*:\s*null', r'"\1": 0.0', response, flags=re.IGNORECASE)
            
            # 解析JSON回答
            decision = self._parse_response(response)
            
            # 添加匹配案例資訊
            decision['matched_cases'] = [c['trade_id'] for c in similar_cases]
            decision['reasoning'] = response  # 保留完整推理過程
            
            return decision
            
        except Exception as e:
            return {
                'signal': 'HOLD',
                'entry_price': current_market.get('close', 0),
                'stop_loss': current_market.get('close', 0) * 0.98,
                'take_profit': current_market.get('close', 0) * 1.02,
                'confidence': 0,
                'reasoning': f"AI分析失敗: {str(e)}",
                'error': str(e)
            }
    
    def _find_similar_cases(self, current_market: Dict, max_cases: int) -> List[Dict]:
        """
        找到與當前市場相似的成功案例
        相似度計算：比較RSI/BB_position/volume_ratio/macd_hist/adx
        """
        if not self.success_cases:
            return []
        
        similarities = []
        
        for case in self.success_cases:
            # 取得案例進場時刻的指標
            entry_candle = next((c for c in case['candles'] if c['position'] == 'entry'), None)
            if not entry_candle:
                continue
            
            case_indicators = entry_candle['indicators']
            
            # 計算相似度（欧氏距離）
            score = 0
            weights = {
                'rsi': 2.0,
                'bb_position': 2.0,
                'volume_ratio': 1.5,
                'macd_hist': 1.5,
                'adx': 1.0
            }
            
            for key, weight in weights.items():
                current_val = current_market.get(key, 0)
                case_val = case_indicators.get(key, 0)
                
                if current_val == 0 and case_val == 0:
                    continue
                
                # 正規化後計算差異
                if key == 'rsi':
                    diff = abs(current_val - case_val) / 100.0
                elif key == 'bb_position':
                    diff = abs(current_val - case_val)
                elif key == 'volume_ratio':
                    diff = abs(current_val - case_val) / max(current_val, case_val, 1.0)
                elif key == 'macd_hist':
                    diff = min(abs(current_val - case_val) * 100, 1.0)
                elif key == 'adx':
                    diff = abs(current_val - case_val) / 100.0
                else:
                    diff = 0
                
                score += weight * (1 - diff)
            
            similarities.append({
                'case': case,
                'score': score
            })
        
        # 排序並返回最相似的
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return [s['case'] for s in similarities[:max_cases]]
    
    def _build_enhanced_prompt(self, current_market: Dict, similar_cases: List[Dict]) -> str:
        """構建強化版Prompt，注入完整案例特徵"""
        
        prompt = f"""你是專業的加密貨幣量化交易員。以下是{len(similar_cases)}個真實獲利交易的完整技術指標數據：

"""
        
        # 注入成功案例
        for idx, case in enumerate(similar_cases, 1):
            prompt += f"\n【案例{idx}：{case['symbol']} {case['direction']} {case['outcome']}】\n"
            prompt += f"進場時間：{case['entry_time']}\n"
            prompt += f"進場價：${case['entry_price']:,.2f}\n"
            prompt += f"出場價：${case['exit_price']:,.2f}\n"
            prompt += f"持倉：{case['holding_bars']}根K棒\n"
            
            # 顯示指標趋勢
            if case.get('indicator_trends'):
                prompt += "\n關鍵指標變化趋勢：\n"
                for indicator, trend_data in case['indicator_trends'].items():
                    values_str = " → ".join([str(v) for v in trend_data['values']])
                    prompt += f"- {indicator}: [{values_str}] ({trend_data['trend']})\n"
            
            # 進場邏輯
            prompt += f"\n進場決策邏輯：{case['entry_logic']}\n"
            prompt += f"實際表現：持倉{case['holding_bars']}根K棒，{case['outcome']}\n"
            prompt += "-" * 60 + "\n"
        
        # 當前市場數據
        prompt += f"\n\n【當前市場狀態】\n"
        prompt += f"幣種：{current_market.get('symbol', 'UNKNOWN')}\n"
        prompt += f"當前價：${current_market.get('close', 0):,.2f}\n\n"
        
        prompt += "技術指標：\n"
        
        # 按類別顯示指標
        categories = {
            '趋勢': ['ema9', 'ema21', 'ema50', 'ema200', 'macd', 'macd_signal', 'macd_hist', 'adx'],
            '動能': ['rsi', 'stoch_k', 'stoch_d', 'cci', 'mfi', 'willr'],
            '波動': ['atr', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_position'],
            '成交量': ['volume_ratio', 'obv', 'ad'],
            '支撐壓力': ['dist_to_support', 'dist_to_resistance']
        }
        
        for category, indicators in categories.items():
            prompt += f"\n{category}：\n"
            for indicator in indicators:
                value = current_market.get(indicator)
                if value is not None:
                    prompt += f"  - {indicator}: {value:.4f}\n"
        
        # 決策要求
        prompt += f"""

【任務要求】
請比對上述成功案例，分析當前市場是否符合高勝率進場條件。

分析步驟：
1. 比較當前RSI/BB_position/volume_ratio與成功案例的相似度
2. 檢查MACD/ADX是否顯示相同的動能特徵
3. 評估支撐/壓力位置是否合理
4. 給出明確的交易計劃

⚠️ CRITICAL: NEVER use null - ALWAYS use 0.0 for numeric fields

必須以JSON格式回答：
```json
{{
  "signal": "LONG" | "SHORT" | "HOLD",
  "confidence": 65,
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "reasoning": "簡潔說明決策理由與匹配的案例特徵",
  "key_risks": ["風險1", "風險2"]
}}
```

⚠️ 注意：
- 只有當confidence > 70且與成功案例高度相似時才建議開倉
- 止損必須基於ATR（當前ATR={current_market.get('atr', 0):.2f}）
- 盈虧比至少1:2，最好1:3
"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析DeepSeek的JSON回答"""
        try:
            # 提取JSON區塊
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '```' in response:
                json_start = response.find('```') + 3
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # 嘗試直接解析
                json_str = response.strip()
            
            # ★★★ 暴力替換null（防萬一）★★★
            json_str = json_str.replace(': null', ': 0.0')
            json_str = json_str.replace(':null', ': 0.0')
            json_str = re.sub(r'"(entry_price|stop_loss|take_profit)"\s*:\s*null', r'"\1": 0.0', json_str, flags=re.IGNORECASE)
            
            decision = json.loads(json_str)
            
            # 驗證必要欄位
            required_fields = ['signal', 'entry_price', 'stop_loss', 'take_profit', 'confidence']
            for field in required_fields:
                if field not in decision:
                    decision[field] = 0.0 if field != 'signal' else 'HOLD'
            
            # 標準化signal
            decision['signal'] = decision['signal'].upper()
            if decision['signal'] not in ['LONG', 'SHORT', 'HOLD']:
                decision['signal'] = 'HOLD'
            
            # 確保數值類型（強制轉型，允許None）
            decision['confidence'] = int(decision.get('confidence', 0) or 0)
            decision['entry_price'] = float(decision.get('entry_price', 0) or 0)
            decision['stop_loss'] = float(decision.get('stop_loss', 0) or 0)
            decision['take_profit'] = float(decision.get('take_profit', 0) or 0)
            
            return decision
            
        except Exception as e:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'entry_price': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'reasoning': f"JSON解析失敗: {str(e)}",
                'error': str(e),
                'parse_error': True
            }
    
    def reload_cases(self):
        """重新載入案例庫（當添加新案例後）"""
        self.success_cases = self._load_cases()
