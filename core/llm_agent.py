from langchain_ollama import OllamaLLM
import json
import re
import pandas as pd
from pathlib import Path

class DeepSeekTradingAgent:
    """DeepSeek-R1 14B 精確交易決策引擎 with Prompt Learning"""
    
    def __init__(self):
        self.model = OllamaLLM(
            model="deepseek-r1:14b",
            temperature=0.2,
            num_predict=3072
        )
        self.success_cases = []
        self.load_historical_cases()
    
    def load_historical_cases(self):
        """從歷史數據中加載成功交易案例"""
        cases_file = Path("data/success_cases.json")
        if cases_file.exists():
            try:
                with open(cases_file, 'r', encoding='utf-8') as f:
                    self.success_cases = json.load(f)
                print(f"[V13] 已載入 {len(self.success_cases)} 個歷史成功案例")
            except:
                self.success_cases = []
    
    def save_success_case(self, market_data, decision, actual_result):
        """保存成功的交易案例供未來學習"""
        if actual_result.get('profit', 0) > 0:
            case = {
                'market_data': market_data,
                'decision': decision,
                'result': actual_result
            }
            self.success_cases.append(case)
            
            # 只保留最近 50 個成功案例
            self.success_cases = self.success_cases[-50:]
            
            cases_file = Path("data/success_cases.json")
            cases_file.parent.mkdir(exist_ok=True)
            with open(cases_file, 'w', encoding='utf-8') as f:
                json.dump(self.success_cases, f, ensure_ascii=False, indent=2)
    
    def _generate_learning_context(self):
        """將歷史成功案例轉換為學習上下文"""
        if not self.success_cases:
            return ""
        
        # 選取最相關的 3 個案例
        recent_cases = self.success_cases[-3:]
        
        context = "\n## 📚 歷史成功案例參考（從過往盈利交易中學習）\n\n"
        for i, case in enumerate(recent_cases, 1):
            md = case['market_data']
            dec = case['decision']
            res = case['result']
            
            context += f"""
案例 {i}:
- 市場狀況: RSI={md.get('rsi', 0):.1f}, MACD={md.get('macd_hist', 0):.4f}, 成交量比={md.get('volume_ratio', 1):.1f}x
- AI 決策: {dec['signal']} @ ${dec['entry_price']:,.0f}, 止損 ${dec['stop_loss']:,.0f}, 止盈 ${dec['take_profit']:,.0f}
- 實際結果: 獲利 {res.get('profit_percent', 0):.2f}%, 持倉 {res.get('hold_hours', 0):.1f} 小時
- 關鍵因素: {dec.get('reasoning', '')[:100]}...

"""
        return context
    
    def analyze_market(self, market_data: dict) -> dict:
        """
        分析市場並給出精確的交易計劃
        
        Args:
            market_data: {
                'symbol': 'BTCUSDT',
                'close': 65000,
                'rsi': 72,
                'macd_hist': 0.0035,
                'bb_position': 0.88,
                'volume_ratio': 0.9,
                'ema50': 64500,
                'ema200': 63000,
                'atr': 800
            }
        
        Returns:
            {
                'signal': 'LONG/SHORT/HOLD',
                'entry_price': 64500.0,
                'stop_loss': 63800.0,
                'take_profit': 66100.0,
                'confidence': 75,
                'position_size_percent': 30,
                'risk_reward_ratio': 2.5,
                'reasoning': '...',
                'key_risks': [...],
                'wait_conditions': [...]
            }
        """
        
        bb_upper = market_data['close'] * (1 + 0.005)
        bb_lower = market_data['close'] * (1 - 0.005)
        
        learning_context = self._generate_learning_context()
        
        prompt = f"""你是專業加密貨幣量化交易員。請根據以下市場數據給出精確的交易計劃。

{learning_context}

## 當前市場數據（{market_data['symbol']}）
- 當前價格：${market_data['close']:,.2f}
- RSI(14)：{market_data.get('rsi', 50):.1f}
- MACD 柱狀圖：{market_data.get('macd_hist', 0):.4f}
- 布林帶位置：{market_data.get('bb_position', 0.5):.2f}（上軌=${bb_upper:,.2f}，下軌=${bb_lower:,.2f}）
- 成交量比率：{market_data.get('volume_ratio', 1):.1f}x
- EMA50：${market_data.get('ema50', market_data['close']):,.2f}
- EMA200：${market_data.get('ema200', market_data['close']):,.2f}
- ATR(14)：${market_data.get('atr', market_data['close']*0.02):,.2f}

## 分析要求
1. 參考上述歷史成功案例，學習在類似市場條件下的最佳決策
2. 判斷真突破或假突破
3. 給出交易決策：LONG、SHORT 或 HOLD
4. **重要**：
   - 如果是 HOLD，entry_price 是「建議等待的進場價」（例如回調至支撐位）
   - 如果是 LONG/SHORT，entry_price 是「立即進場價」
   - 止損必須基於 ATR 或關鍵支撐/阻力位
   - 盈虧比至少 1:2

## 輸出格式（嚴格 JSON，不要有任何額外文字）
{{
  "signal": "LONG/SHORT/HOLD",
  "confidence": 75,
  "entry_price": {market_data.get('ema50', market_data['close'])},
  "stop_loss": {market_data.get('ema50', market_data['close']) - market_data.get('atr', 800)},
  "take_profit": {market_data.get('ema50', market_data['close']) + market_data.get('atr', 800) * 2},
  "position_size_percent": 30,
  "risk_reward_ratio": 2.0,
  "reasoning": "詳細推理，說明如何參考歷史案例...",
  "key_risks": ["風險1", "風險2"],
  "wait_conditions": ["等待條件1", "等待條件2"]
}}
"""
        
        try:
            response = self.model.invoke(prompt)
            
            # 移除 Thinking 部分
            response = response.split('...done thinking.')[-1].strip()
            
            # 提取 JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                result = json.loads(json_str)
                
                # 計算實際盈虧比
                if result['signal'] != 'HOLD':
                    risk = abs(result['entry_price'] - result['stop_loss'])
                    reward = abs(result['take_profit'] - result['entry_price'])
                    result['risk_reward_ratio'] = round(reward / risk, 2) if risk > 0 else 0
                
                return result
            
            return self._fallback_decision(market_data, response)
            
        except Exception as e:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'entry_price': market_data['close'],
                'stop_loss': market_data['close'] * 0.98,
                'take_profit': market_data['close'] * 1.02,
                'position_size_percent': 0,
                'error': str(e)
            }
    
    def _fallback_decision(self, market_data, raw_response):
        """當 JSON 解析失敗時的備用決策"""
        return {
            'signal': 'HOLD',
            'confidence': 50,
            'entry_price': market_data.get('ema50', market_data['close']),
            'stop_loss': market_data.get('ema50', market_data['close']) - market_data.get('atr', 800),
            'take_profit': market_data.get('ema50', market_data['close']) + market_data.get('atr', 800) * 2,
            'position_size_percent': 0,
            'reasoning': raw_response[:500],
            'key_risks': ['AI 回答解析失敗'],
            'parse_error': True
        }
    
    def format_trade_plan(self, decision: dict) -> str:
        """格式化交易計劃為易讀文本"""
        
        if decision['signal'] == 'HOLD':
            wait_cond = decision.get('wait_conditions', [])
            wait_text = '\n'.join(f'  • {cond}' for cond in wait_cond) if wait_cond else '  • 等待更明確的信號'
            
            return f"""
⏸️ 交易信號：觀望 (HOLD)
🎯 信心指數：{decision.get('confidence', 0)}%

💡 AI 判斷：{decision.get('reasoning', 'N/A')}

📍 建議進場價：${decision['entry_price']:,.2f}
⏳ 等待條件：
{wait_text}

如果在建議價格進場：
├─ 止損：${decision['stop_loss']:,.2f}
├─ 止盈：${decision['take_profit']:,.2f}
└─ 盈虧比：1:{decision.get('risk_reward_ratio', 0):.1f}

⚠️ 關鍵風險：
{chr(10).join('  • ' + risk for risk in decision.get('key_risks', ['未知風險']))}
"""
        
        # LONG/SHORT 格式
        entry = decision['entry_price']
        sl = decision['stop_loss']
        tp = decision['take_profit']
        
        risk_usd = abs(entry - sl)
        reward_usd = abs(tp - entry)
        risk_pct = (risk_usd / entry) * 100
        reward_pct = (reward_usd / entry) * 100
        
        signal_icon = "📈" if decision['signal'] == "LONG" else "📉"
        
        return f"""
{signal_icon} 交易信號：{decision['signal']}
🎯 信心指數：{decision.get('confidence', 0)}%

📊 精確交易計劃：
├─ 進場價：${entry:,.2f}
├─ 止損價：${sl:,.2f} （-{risk_pct:.2f}%, ${risk_usd:,.2f}）
├─ 止盈價：${tp:,.2f} （+{reward_pct:.2f}%, ${reward_usd:,.2f}）
└─ 盈虧比：1:{decision.get('risk_reward_ratio', 0):.2f}

💰 倉位建議：{decision.get('position_size_percent', 0)}% 總資金
   （假設 $10,000，開倉 ${10000 * decision.get('position_size_percent', 0) / 100:,.2f}）

💡 AI 推理：
{decision.get('reasoning', 'N/A')}

⚠️ 關鍵風險：
{chr(10).join('  • ' + risk for risk in decision.get('key_risks', ['未知風險']))}
"""