"""
三模型共識決策系統 - AI 競賽專用
使用三個最強模型互相驗證，提高勝率
- Model A: Llama 3.1 405B (最強推理)
- Model B: Gemini 2.0 Flash Thinking (思維鏈)
- Model C: Llama 3.3 70B (速度 + 備份)
"""
import json
import time
import os
from typing import Dict, Optional, List, Tuple
import requests
from datetime import datetime


class ModelInterface:
    def __init__(self, name: str, api_key: str, base_url: str, model: str, weight: float = 1.0):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.weight = weight
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        raise NotImplementedError


class OpenAICompatibleModel(ModelInterface):
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.2,
            'max_tokens': 3000
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )
            elapsed = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {
                'success': True,
                'content': content,
                'model': self.model,
                'elapsed_time': elapsed
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': self.model,
                'elapsed_time': 0
            }


class GeminiModel(ModelInterface):
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            start_time = time.time()
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=3000
                )
            )
            elapsed = time.time() - start_time
            
            return {
                'success': True,
                'content': response.text,
                'model': self.model,
                'elapsed_time': elapsed
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': self.model,
                'elapsed_time': 0
            }


class TripleConsensusAgent:
    """
    三模型共識決策引擎
    用於 AI 競賽，追求最高準確性
    """
    
    def __init__(self):
        self.model_a = None  # Llama 3.1 405B
        self.model_b = None  # Gemini 2.0 Flash Thinking
        self.model_c = None  # Llama 3.3 70B (Groq)
        self.decision_history: List[Dict] = []
        
        self._init_models()
    
    def _init_models(self):
        print("\n" + "="*70)
        print("🏆 AI 競賽模式 - 三模型共識系統啟動")
        print("="*70)
        
        # Model A: Llama 3.1 405B (OpenRouter)
        if os.getenv('OPENROUTER_API_KEY'):
            self.model_a = OpenAICompatibleModel(
                name='Llama_405B',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='meta-llama/llama-3.1-405b-instruct:free',
                weight=0.45
            )
            print("✅ Model A: Llama 3.1 405B (最強推理) - 權重 45%")
        
        # Model B: Gemini 2.0 Flash Thinking (OpenRouter or Google)
        if os.getenv('OPENROUTER_API_KEY'):
            self.model_b = OpenAICompatibleModel(
                name='Gemini_2_Thinking',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='google/gemini-2.0-flash-thinking-exp:free',
                weight=0.35
            )
            print("✅ Model B: Gemini 2.0 Flash Thinking (思維鏈) - 權重 35%")
        elif os.getenv('GOOGLE_API_KEY'):
            self.model_b = GeminiModel(
                name='Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash',
                weight=0.35
            )
            print("✅ Model B: Gemini 2.0 Flash - 權重 35%")
        
        # Model C: Llama 3.3 70B (Groq)
        if os.getenv('GROQ_API_KEY'):
            self.model_c = OpenAICompatibleModel(
                name='Llama_70B_Fast',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile',
                weight=0.20
            )
            print("✅ Model C: Llama 3.3 70B (速度快) - 權重 20%")
        
        print("="*70 + "\n")
        
        if not all([self.model_a, self.model_b, self.model_c]):
            print("⚠️ 警告: 三模型未完全配置，請檢查 API Keys")
    
    def analyze_with_consensus(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """三模型共識分析"""
        
        if not all([self.model_a, self.model_b, self.model_c]):
            print("⚠️ 三模型未完全配置，降級為雙模型")
            from core.dual_model_agent import DualModelDecisionAgent
            agent = DualModelDecisionAgent()
            return agent.analyze_with_dual_models(market_data, account_info, position_info)
        
        print("\n" + "━"*70)
        print(f"🔍 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 三模型分析開始")
        print("━"*70)
        
        system_prompt, user_prompt = self._prepare_prompts(
            market_data, account_info, position_info
        )
        
        # 並行調用三個模型
        decisions = {}
        
        # Model A: Llama 405B
        print(f"\n🤖 [{self.model_a.name}] 分析中...")
        result_a = self.model_a.analyze(system_prompt, user_prompt)
        
        if result_a['success']:
            decisions['A'] = self._parse_decision(result_a['content'])
            decisions['A']['model'] = self.model_a.name
            decisions['A']['weight'] = self.model_a.weight
            decisions['A']['elapsed'] = result_a['elapsed_time']
            print(f"✅ [{self.model_a.name}]: {decisions['A']['action']} (信心度 {decisions['A']['confidence']}%) - {result_a['elapsed_time']:.1f}s")
        else:
            print(f"❌ [{self.model_a.name}] 失敗: {result_a.get('error')}")
            decisions['A'] = None
        
        time.sleep(1)
        
        # Model B: Gemini 2.0
        print(f"\n🤖 [{self.model_b.name}] 分析中...")
        result_b = self.model_b.analyze(system_prompt, user_prompt)
        
        if result_b['success']:
            decisions['B'] = self._parse_decision(result_b['content'])
            decisions['B']['model'] = self.model_b.name
            decisions['B']['weight'] = self.model_b.weight
            decisions['B']['elapsed'] = result_b['elapsed_time']
            print(f"✅ [{self.model_b.name}]: {decisions['B']['action']} (信心度 {decisions['B']['confidence']}%) - {result_b['elapsed_time']:.1f}s")
        else:
            print(f"❌ [{self.model_b.name}] 失敗: {result_b.get('error')}")
            decisions['B'] = None
        
        time.sleep(1)
        
        # Model C: Llama 70B (Groq)
        print(f"\n🤖 [{self.model_c.name}] 分析中...")
        result_c = self.model_c.analyze(system_prompt, user_prompt)
        
        if result_c['success']:
            decisions['C'] = self._parse_decision(result_c['content'])
            decisions['C']['model'] = self.model_c.name
            decisions['C']['weight'] = self.model_c.weight
            decisions['C']['elapsed'] = result_c['elapsed_time']
            print(f"✅ [{self.model_c.name}]: {decisions['C']['action']} (信心度 {decisions['C']['confidence']}%) - {result_c['elapsed_time']:.1f}s")
        else:
            print(f"❌ [{self.model_c.name}] 失敗: {result_c.get('error')}")
            decisions['C'] = None
        
        # 共識決策
        final_decision = self._consensus_voting(decisions)
        
        # 記錄歷史
        self.decision_history.append({
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'decisions': decisions,
            'final': final_decision
        })
        
        print("\n" + "━"*70)
        print("✅ 最終共識決策")
        print("━"*70)
        print(f"Action: {final_decision['action']}")
        print(f"Confidence: {final_decision['confidence']}%")
        print(f"Agreement: {final_decision.get('agreement_count', 0)}/3 模型同意")
        print(f"Reasoning: {final_decision['reasoning'][:200]}...")
        print("━"*70 + "\n")
        
        return final_decision
    
    def _prepare_prompts(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> Tuple[str, str]:
        system_prompt = """你是一個頂尖的加密貨幣量化交易 AI。你正在參加 AI 交易競賽，目標是獲得最高收益。

分析要求：
1. 仔細分析所有技術指標 (RSI, MACD, Bollinger Bands, ATR, EMA, Volume)
2. 識別關鍵支撐/壓力位
3. 考慮多時間周期趨勢 (15m, 1h, 4h)
4. 評估風險收益比
5. 給出明確的進場/止損/止盈價位

輸出 JSON 格式：
{
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
  "confidence": 0-100,
  "leverage": 1-5,
  "position_size_usdt": 數字,
  "entry_price": 數字,
  "stop_loss": 數字,
  "take_profit": 數字,
  "reasoning": "詳細理由",
  "risk_assessment": "LOW" | "MEDIUM" | "HIGH",
  "technical_analysis": "技術分析詳情",
  "risk_reward_ratio": 數字
}

重要: 只有在信心度 > 75% 且風險收益比 > 2:1 時才建議交易。"""
        
        user_prompt = f"""市場數據 (更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})：
{json.dumps(market_data, indent=2, ensure_ascii=False)}

賬戶資訊：
{json.dumps(account_info, indent=2, ensure_ascii=False)}

當前持倉：
{json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'}

請給出你的分析和交易建議。"""
        
        return system_prompt, user_prompt
    
    def _parse_decision(self, content: str) -> Dict:
        try:
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                decision = json.loads(json_str)
                return decision
        except:
            pass
        
        return {
            'action': 'HOLD',
            'confidence': 30,
            'leverage': 1,
            'position_size_usdt': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'reasoning': f'解析失敗',
            'risk_assessment': 'HIGH'
        }
    
    def _consensus_voting(self, decisions: Dict) -> Dict:
        """三模型共識決策逻輯"""
        
        valid_decisions = {k: v for k, v in decisions.items() if v is not None}
        
        if len(valid_decisions) == 0:
            return self._emergency_hold()
        
        if len(valid_decisions) < 2:
            return list(valid_decisions.values())[0]
        
        # 統計每個 action 的投票
        action_votes = {}
        for k, decision in valid_decisions.items():
            action = decision['action']
            if action not in action_votes:
                action_votes[action] = {'count': 0, 'total_confidence': 0, 'total_weight': 0, 'decisions': []}
            
            action_votes[action]['count'] += 1
            action_votes[action]['total_confidence'] += decision['confidence']
            action_votes[action]['total_weight'] += decision['weight']
            action_votes[action]['decisions'].append(decision)
        
        # 找到最多票數的 action
        max_votes = max(v['count'] for v in action_votes.values())
        
        # 如果有 2 個或更多模型同意
        if max_votes >= 2:
            winning_action = max(action_votes.items(), key=lambda x: (x[1]['count'], x[1]['total_weight']))[0]
            winning_votes = action_votes[winning_action]
            
            avg_confidence = int(winning_votes['total_confidence'] / winning_votes['count'])
            
            # 加權平均價格
            avg_entry = sum(d['entry_price'] * d['weight'] for d in winning_votes['decisions']) / winning_votes['total_weight']
            avg_stop_loss = sum(d['stop_loss'] * d['weight'] for d in winning_votes['decisions']) / winning_votes['total_weight']
            avg_take_profit = sum(d['take_profit'] * d['weight'] for d in winning_votes['decisions']) / winning_votes['total_weight']
            avg_position_size = sum(d['position_size_usdt'] * d['weight'] for d in winning_votes['decisions']) / winning_votes['total_weight']
            
            return {
                'action': winning_action,
                'confidence': avg_confidence,
                'leverage': max(d['leverage'] for d in winning_votes['decisions']),
                'position_size_usdt': avg_position_size,
                'entry_price': avg_entry,
                'stop_loss': avg_stop_loss,
                'take_profit': avg_take_profit,
                'reasoning': f"✅ {winning_votes['count']}/3 模型共識: {winning_action}",
                'risk_assessment': winning_votes['decisions'][0]['risk_assessment'],
                'agreement_count': winning_votes['count'],
                'consensus': True
            }
        else:
            # 三個模型意見分歧，採用 HOLD
            print("⚠️ 三模型意見不一致，等待下次機會")
            
            return {
                'action': 'HOLD',
                'confidence': 40,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'reasoning': f"⚠️ 模型意見分歧: {', '.join(f'{k}={v['action']}' for k, v in valid_decisions.items())}",
                'risk_assessment': 'HIGH',
                'agreement_count': 0,
                'consensus': False
            }
    
    def _emergency_hold(self) -> Dict:
        return {
            'action': 'HOLD',
            'confidence': 0,
            'leverage': 1,
            'position_size_usdt': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'reasoning': '緊急 HOLD: 所有模型失敗',
            'risk_assessment': 'HIGH',
            'agreement_count': 0,
            'consensus': False
        }
    
    def get_statistics(self) -> Dict:
        if not self.decision_history:
            return {'total': 0}
        
        total = len(self.decision_history)
        consensus_count = sum(1 for d in self.decision_history if d['final'].get('consensus', False))
        
        return {
            'total_decisions': total,
            'consensus_decisions': consensus_count,
            'disagreement_decisions': total - consensus_count,
            'consensus_rate': (consensus_count / total) * 100 if total > 0 else 0
        }
