"""
交易執行審核員 (Trading Executor Agent)

三階段決策系統的第三階段：
  階段1: Model A + Model B 快速分析
  階段2: 仲裁者決策 (意見分歧時)
  階段3: 交易執行審核 (最終把關) ← 這裡

審核員的職責：
  1. 評估仲裁者決策的可行性
  2. 檢查市場狀況是否適合交易
  3. 考量風險控制 (信心度門檻)
  4. 避免危險操作 (如低流動性、高波動)
  5. 最終決定 EXECUTE (執行) 或 REJECT (拒絕)

基本規則：
  - 信心度 >= 60%: 自動執行
  - 信心度 50-59%: 謹慎執行 (減少倉位)
  - 信心度 < 50%: 拒絕執行
  - HOLD 行動：一律通過 (不需審核)
  - 持倉狀況：檢查是否重複下單
  - 市場波動：超過 5% 短期波動降低信心
  - 逆勢操作：需要更高信心度 (>70%)

輸出：
  {
    "execution_decision": "EXECUTE" | "REJECT" | "REDUCE_SIZE",
    "final_action": "最終行動",
    "adjusted_confidence": 調整後信心度,
    "adjusted_position_size": 調整後倉位,
    "executor_reasoning": "審核員理由",
    "risk_factors": []
  }
"""
import json
import os
from typing import Dict, Optional, List
import requests
import time

# 導入強健 JSON 解析器
try:
    from core.json_parser_robust import parse_executor_review
    HAS_ROBUST_PARSER = True
except ImportError:
    HAS_ROBUST_PARSER = False
    print("[WARNING] 強健 JSON 解析器不可用，使用基礎解析")


class TradingExecutorAgent:
    """
    交易執行審核員 - 最終把關
    使用獨立模型作為「交易員」角色
    """
    
    def __init__(self):
        self.confidence_threshold_high = 60
        self.confidence_threshold_medium = 50
        self.confidence_threshold_counter_trend = 70
        self.max_volatility_percent = 5.0
        
        self.execution_history: List[Dict] = []
        
        # 使用 Gemini Flash 作為審核員 (快速且穩定)
        self.executor_model = self._init_executor_model()
        
        if HAS_ROBUST_PARSER:
            print("[OK] 執行審核員使用強健 JSON 解析器")
    
    def _init_executor_model(self):
        """初始化審核員模型"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            # 備用: Groq Llama
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                return {
                    'provider': 'groq',
                    'api_key': api_key,
                    'model': 'llama-3.3-70b-versatile',
                    'base_url': 'https://api.groq.com/openai/v1'
                }
            return None
        
        return {
            'provider': 'google',
            'api_key': api_key,
            'model': 'gemini-2.5-flash',
            'base_url': ''
        }
    
    def review_trading_decision(
        self,
        arbitrator_decision: Dict,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None,
        multi_timeframe_data: Optional[Dict] = None
    ) -> Dict:
        """
        審核仲裁者的決策，決定是否執行
        
        Returns:
            {
                "execution_decision": "EXECUTE" | "REJECT" | "REDUCE_SIZE",
                "final_action": 最終行動,
                "adjusted_confidence": 調整後信心度,
                "adjusted_position_size": 調整後倉位,
                "executor_reasoning": 審核員理由
            }
        """
        print("\n" + "="*70)
        print("[STAGE 3] 交易執行審核 - 最終把關")
        print("="*70)
        
        action = arbitrator_decision.get('action', 'HOLD')
        confidence = arbitrator_decision.get('confidence', 0)
        is_counter_trend = arbitrator_decision.get('is_counter_trend', False)
        
        # HOLD 一律通過
        if action == 'HOLD':
            print("[OK] HOLD 行動，直接通過")
            return self._approve_decision(arbitrator_decision, "HOLD 不需審核")
        
        # 快速規則檢查
        quick_check = self._quick_rule_check(
            action, confidence, is_counter_trend, position_info, market_data
        )
        
        if quick_check['status'] == 'REJECT':
            print(f"[REJECT] {quick_check['reason']}")
            return self._reject_decision(arbitrator_decision, quick_check['reason'])
        
        if quick_check['status'] == 'REDUCE_SIZE':
            print(f"[WARNING] {quick_check['reason']}")
            reduced_size = arbitrator_decision['position_size_usdt'] * 0.5
            return self._reduce_position_size(
                arbitrator_decision, reduced_size, quick_check['reason']
            )
        
        # AI 審核員深度分析
        if self.executor_model:
            ai_review = self._ai_deep_review(
                arbitrator_decision, market_data, account_info, 
                position_info, multi_timeframe_data
            )
            
            if ai_review:
                print(f"[AI REVIEW] {ai_review['execution_decision']}")
                print(f"            {ai_review['executor_reasoning'][:100]}...")
                return ai_review
        
        # 備用: 基於信心度的預設策略
        print("[INFO] AI 審核員不可用，使用預設策略")
        return self._default_confidence_strategy(arbitrator_decision)
    
    def _quick_rule_check(
        self, 
        action: str, 
        confidence: int, 
        is_counter_trend: bool,
        position_info: Optional[Dict],
        market_data: Dict
    ) -> Dict:
        """快速規則檢查"""
        
        # 1. 重複下單檢查
        if position_info:
            current_side = position_info.get('side', '')
            if current_side == 'Long' and action == 'OPEN_LONG':
                return {'status': 'REJECT', 'reason': '已有多單，拒絕重複 OPEN_LONG'}
            if current_side == 'Short' and action == 'OPEN_SHORT':
                return {'status': 'REJECT', 'reason': '已有空單，拒絕重複 OPEN_SHORT'}
            if not current_side and action == 'CLOSE':
                return {'status': 'REJECT', 'reason': '無持倉，無法 CLOSE'}
        
        # 2. 信心度檢查
        if is_counter_trend:
            if confidence < self.confidence_threshold_counter_trend:
                return {
                    'status': 'REJECT',
                    'reason': f'逆勢操作信心度不足 ({confidence}% < {self.confidence_threshold_counter_trend}%)'
                }
        else:
            if confidence < self.confidence_threshold_medium:
                return {
                    'status': 'REJECT',
                    'reason': f'信心度不足 ({confidence}% < {self.confidence_threshold_medium}%)'
                }
            elif confidence < self.confidence_threshold_high:
                return {
                    'status': 'REDUCE_SIZE',
                    'reason': f'信心度中等 ({confidence}%)，減少倉位 50%'
                }
        
        # 3. 波動性檢查
        volatility = self._calculate_volatility(market_data)
        if volatility and volatility > self.max_volatility_percent:
            return {
                'status': 'REDUCE_SIZE',
                'reason': f'市場波動過大 ({volatility:.2f}%)，減少倉位'
            }
        
        return {'status': 'PASS', 'reason': 'OK'}
    
    def _calculate_volatility(self, market_data: Dict) -> Optional[float]:
        """計算短期波動率"""
        try:
            atr = market_data.get('atr', 0)
            close = market_data.get('close', 0)
            if close > 0:
                return (atr / close) * 100
        except:
            pass
        return None
    
    def _ai_deep_review(
        self,
        arbitrator_decision: Dict,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict],
        multi_timeframe_data: Optional[Dict]
    ) -> Optional[Dict]:
        """使用 AI 模型進行深度審核"""
        
        if not self.executor_model:
            return None
        
        system_prompt = """你是一名經驗豐富的加密貨幣交易員，負責最終審核交易決策。

你的職責：
1. 審查 AI 仲裁者的交易決策
2. 評估市場狀況是否適合執行
3. 檢查風險控制是否完善
4. 決定 EXECUTE (執行) / REJECT (拒絕) / REDUCE_SIZE (減少倉位)

審核原則：
- 信心度 >= 60%: 可以執行
- 信心度 50-59%: 減少倉位 50%
- 信心度 < 50%: 拒絕執行
- 逆勢操作需要 >= 70% 信心度
- 避免重複下單
- 波動過大時減少倉位
- 流動性不足時謹慎

輸出 JSON 格式：
{
  "execution_decision": "EXECUTE" | "REJECT" | "REDUCE_SIZE",
  "confidence_adjustment": -20 到 +20 (信心度調整),
  "position_size_ratio": 0.5-1.0 (倉位比例),
  "reasoning": "審核理由",
  "risk_factors": ["風險因素清單"]
}"""
        
        user_prompt_parts = [
            "=== 仲裁者決策 ===",
            json.dumps(arbitrator_decision, indent=2, ensure_ascii=False),
            "\n=== 當前市場 ===",
            json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n=== 賬戶狀況 ===",
            json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n=== 持倉狀況 ===",
            json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'
        ]
        
        if multi_timeframe_data:
            simplified_mt = {}
            for tf in ['15m', '1h', '4h']:
                if tf in multi_timeframe_data:
                    data = multi_timeframe_data[tf]
                    simplified_mt[tf] = {
                        'trend': data.get('trend_analysis', {}),
                        'rsi': data.get('current', {}).get('rsi')
                    }
            user_prompt_parts.extend([
                "\n=== 多時間框架趨勢 ===",
                json.dumps(simplified_mt, indent=2, ensure_ascii=False)
            ])
        
        user_prompt_parts.append("\n請作為交易員審核這個決策，決定是否執行。")
        user_prompt = "\n".join(user_prompt_parts)
        
        try:
            print("\n[AI EXECUTOR] 正在審核...")
            
            if self.executor_model['provider'] == 'google':
                result = self._call_gemini(system_prompt, user_prompt)
            else:
                result = self._call_openai_compatible(system_prompt, user_prompt)
            
            if result['success']:
                review = self._parse_review(result['content'])
                
                # 應用審核結果
                if review['execution_decision'] == 'EXECUTE':
                    adjusted_confidence = arbitrator_decision['confidence'] + review.get('confidence_adjustment', 0)
                    return self._approve_decision(
                        arbitrator_decision, 
                        review['reasoning'],
                        adjusted_confidence
                    )
                elif review['execution_decision'] == 'REJECT':
                    return self._reject_decision(arbitrator_decision, review['reasoning'])
                else:  # REDUCE_SIZE
                    ratio = review.get('position_size_ratio', 0.5)
                    reduced_size = arbitrator_decision['position_size_usdt'] * ratio
                    return self._reduce_position_size(
                        arbitrator_decision, reduced_size, review['reasoning']
                    )
            else:
                print(f"[WARNING] AI 審核失敗: {result.get('error', 'Unknown')}")
                return None
                
        except Exception as e:
            print(f"[ERROR] AI 審核異常: {e}")
            return None
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> Dict:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.executor_model['api_key'])
            model = genai.GenerativeModel(self.executor_model['model'])
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            start_time = time.time()
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2000
                )
            )
            elapsed = time.time() - start_time
            
            return {'success': True, 'content': response.text, 'elapsed': elapsed}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> Dict:
        try:
            headers = {
                'Authorization': f'Bearer {self.executor_model["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.executor_model['model'],
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.1,
                'max_tokens': 2000
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.executor_model['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {'success': True, 'content': content, 'elapsed': elapsed}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_review(self, content: str) -> Dict:
        """解析審核員回應"""
        if HAS_ROBUST_PARSER:
            # 使用強健解析器
            return parse_executor_review(content)
        else:
            # 備用: 基礎解析
            try:
                if '{' in content and '}' in content:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    return json.loads(content[start:end])
            except:
                pass
            
            return {
                'execution_decision': 'REJECT',
                'confidence_adjustment': 0,
                'position_size_ratio': 1.0,
                'reasoning': '解析失敗，預設拒絕',
                'risk_factors': ['解析錯誤']
            }
    
    def _approve_decision(self, decision: Dict, reason: str, adjusted_confidence: Optional[int] = None) -> Dict:
        return {
            'execution_decision': 'EXECUTE',
            'final_action': decision['action'],
            'adjusted_confidence': adjusted_confidence or decision['confidence'],
            'adjusted_position_size': decision['position_size_usdt'],
            'adjusted_leverage': decision['leverage'],
            'entry_price': decision['entry_price'],
            'stop_loss': decision['stop_loss'],
            'take_profit': decision['take_profit'],
            'executor_reasoning': reason,
            'risk_assessment': decision['risk_assessment'],
            'is_counter_trend': decision.get('is_counter_trend', False)
        }
    
    def _reject_decision(self, decision: Dict, reason: str) -> Dict:
        return {
            'execution_decision': 'REJECT',
            'final_action': 'HOLD',
            'adjusted_confidence': 0,
            'adjusted_position_size': 0,
            'adjusted_leverage': 1,
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'executor_reasoning': f'拒絕執行: {reason}',
            'risk_assessment': 'HIGH',
            'original_action': decision['action']
        }
    
    def _reduce_position_size(self, decision: Dict, reduced_size: float, reason: str) -> Dict:
        return {
            'execution_decision': 'REDUCE_SIZE',
            'final_action': decision['action'],
            'adjusted_confidence': max(decision['confidence'] - 10, 40),
            'adjusted_position_size': reduced_size,
            'adjusted_leverage': min(decision['leverage'], 3),
            'entry_price': decision['entry_price'],
            'stop_loss': decision['stop_loss'],
            'take_profit': decision['take_profit'],
            'executor_reasoning': f'減少倉位: {reason}',
            'risk_assessment': decision['risk_assessment'],
            'is_counter_trend': decision.get('is_counter_trend', False),
            'original_size': decision['position_size_usdt']
        }
    
    def _default_confidence_strategy(self, decision: Dict) -> Dict:
        """預設基於信心度的策略"""
        confidence = decision['confidence']
        is_counter_trend = decision.get('is_counter_trend', False)
        
        if is_counter_trend:
            if confidence >= 70:
                return self._approve_decision(decision, f"逆勢操作信心度達標 ({confidence}%)")
            else:
                return self._reject_decision(decision, f"逆勢操作信心度不足 ({confidence}% < 70%)")
        else:
            if confidence >= 60:
                return self._approve_decision(decision, f"信心度達標 ({confidence}%)")
            elif confidence >= 50:
                reduced = decision['position_size_usdt'] * 0.5
                return self._reduce_position_size(decision, reduced, f"信心度中等 ({confidence}%)")
            else:
                return self._reject_decision(decision, f"信心度不足 ({confidence}% < 50%)")
    
    def get_statistics(self) -> Dict:
        if not self.execution_history:
            return {'total': 0}
        
        total = len(self.execution_history)
        executed = sum(1 for x in self.execution_history if x['execution_decision'] == 'EXECUTE')
        rejected = sum(1 for x in self.execution_history if x['execution_decision'] == 'REJECT')
        reduced = sum(1 for x in self.execution_history if x['execution_decision'] == 'REDUCE_SIZE')
        
        return {
            'total_reviews': total,
            'executed': executed,
            'rejected': rejected,
            'reduced_size': reduced,
            'execution_rate': (executed / total) * 100 if total > 0 else 0,
            'rejection_rate': (rejected / total) * 100 if total > 0 else 0
        }
