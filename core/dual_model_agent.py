"""
雙模型決策系統
使用兩個**不同的優質模型**互相驗證，提高決策準確性
- Model A: Llama 3.3 70B / Gemini 2.0 (速度快、推理好)
- Model B: GPT-4o-mini / Qwen3 32B (穩定性好)
更新為 2026 年可用模型
"""
import json
import time
import os
from typing import Dict, Optional, List, Tuple
import requests


class ModelInterface:
    """模型接口 - 用於調用不同 API"""
    
    def __init__(self, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        """調用模型分析"""
        raise NotImplementedError


class OpenAICompatibleModel(ModelInterface):
    """支持 OpenAI API 格式的模型 (Groq, OpenRouter, GitHub Models)"""
    
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
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {
                'success': True,
                'content': content,
                'model': self.model
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': self.model
            }


class GeminiModel(ModelInterface):
    """Google Gemini API"""
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            return {
                'success': True,
                'content': response.text,
                'model': self.model
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': self.model
            }


class DualModelDecisionAgent:
    """
    雙模型決策引擎
    使用兩個**不同的優質模型**獨立分析，然後比對結果
    """
    
    def __init__(self):
        self.model_a = None  # Llama 3.3 70B / Gemini 2.0
        self.model_b = None  # GPT-4o-mini / Qwen3 32B
        self.decision_history: List[Dict] = []
        
        self._init_models()
    
    def _init_models(self):
        """初始化兩個不同模型 (2026 可用)"""
        
        # Model A: 選擇速度快且推理好的模型
        if os.getenv('GROQ_API_KEY'):
            self.model_a = OpenAICompatibleModel(
                name='Groq_Llama_3_3_70B',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile'
            )
            print("✅ Model A: Groq Llama 3.3 70B Versatile")
        elif os.getenv('GOOGLE_API_KEY'):
            self.model_a = GeminiModel(
                name='Google_Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash'
            )
            print("✅ Model A: Google Gemini 2.0 Flash")
        elif os.getenv('OPENROUTER_API_KEY'):
            self.model_a = OpenAICompatibleModel(
                name='OpenRouter_Gemini_2_Flash',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='google/gemini-2.0-flash-exp:free'
            )
            print("✅ Model A: OpenRouter Gemini 2.0 Flash")
        else:
            print("⚠️ Model A 未配置")
        
        # Model B: 選擇穩定的備用模型
        if os.getenv('GITHUB_TOKEN'):
            self.model_b = OpenAICompatibleModel(
                name='GitHub_GPT4o_mini',
                api_key=os.getenv('GITHUB_TOKEN'),
                base_url='https://models.inference.ai.azure.com',
                model='gpt-4o-mini'
            )
            print("✅ Model B: GitHub GPT-4o-mini")
        elif os.getenv('OPENROUTER_API_KEY') and self.model_a and not self.model_a.name.startswith('OpenRouter'):
            # 如果 Model A 不是 OpenRouter，用 OpenRouter 的其他模型
            self.model_b = OpenAICompatibleModel(
                name='OpenRouter_Qwen3_32B',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='qwen/qwen3-32b:free'
            )
            print("✅ Model B: OpenRouter Qwen3 32B")
        elif os.getenv('GROQ_API_KEY') and self.model_a and self.model_a.model != 'mixtral-8x7b-32768':
            # 如果 Model A 用了 Groq Llama，這裡用 Groq Mixtral
            self.model_b = OpenAICompatibleModel(
                name='Groq_Mixtral_8x7B',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='mixtral-8x7b-32768'
            )
            print("✅ Model B: Groq Mixtral 8x7B")
        else:
            print("⚠️ Model B 未配置")
    
    def analyze_with_dual_models(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None,
        mode: str = 'consensus'
    ) -> Dict:
        """
        雙模型分析
        """
        if not self.model_a or not self.model_b:
            print("⚠️ 雙模型未完全配置，降級為單模型")
            # 降級使用單模型
            from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
            agent = PositionAwareDeepSeekAgent()
            return agent.analyze_with_position(market_data, account_info, position_info)
        
        print("\n" + "="*60)
        print("🔍 雙模型決策系統啟動")
        print(f"Model A: {self.model_a.name} ({self.model_a.model})")
        print(f"Model B: {self.model_b.name} ({self.model_b.model})")
        print("="*60)
        
        # 準備 prompt
        system_prompt, user_prompt = self._prepare_prompts(
            market_data, account_info, position_info
        )
        
        # Model A 分析
        print(f"\n🤖 {self.model_a.name} 分析中...")
        result_a = self.model_a.analyze(system_prompt, user_prompt)
        
        if not result_a['success']:
            print(f"❌ {self.model_a.name} 失敗: {result_a.get('error')}")
            return self._fallback_decision(market_data, account_info, position_info)
        
        decision_a = self._parse_decision(result_a['content'])
        print(f"✅ {self.model_a.name}: {decision_a['action']} (信心度 {decision_a['confidence']}%)")
        
        # 等待 2 秒避免 RPM 限制
        time.sleep(2)
        
        # Model B 分析
        print(f"\n🤖 {self.model_b.name} 分析中...")
        result_b = self.model_b.analyze(system_prompt, user_prompt)
        
        if not result_b['success']:
            print(f"❌ {self.model_b.name} 失敗: {result_b.get('error')}")
            print(f"→ 使用 {self.model_a.name} 的決策")
            return decision_a
        
        decision_b = self._parse_decision(result_b['content'])
        print(f"✅ {self.model_b.name}: {decision_b['action']} (信心度 {decision_b['confidence']}%)")
        
        # 比對結果
        print("\n" + "="*60)
        print("⚡ 決策比對")
        print("="*60)
        print(f"{self.model_a.name}: {decision_a['action']} ({decision_a['confidence']}%)")
        print(f"  {decision_a['reasoning'][:100]}...")
        print(f"\n{self.model_b.name}: {decision_b['action']} ({decision_b['confidence']}%)")
        print(f"  {decision_b['reasoning'][:100]}...")
        
        # 根據模式決策
        if mode == 'consensus':
            final_decision = self._consensus_decision(decision_a, decision_b)
        elif mode == 'vote':
            final_decision = self._vote_decision(decision_a, decision_b)
        elif mode == 'weighted':
            final_decision = self._weighted_decision(decision_a, decision_b)
        else:
            final_decision = self._consensus_decision(decision_a, decision_b)
        
        # 記錄歷史
        self.decision_history.append({
            'timestamp': time.time(),
            'model_a': {
                'name': self.model_a.name,
                'model': self.model_a.model,
                'decision': decision_a
            },
            'model_b': {
                'name': self.model_b.name,
                'model': self.model_b.model,
                'decision': decision_b
            },
            'final': final_decision,
            'mode': mode
        })
        
        print("\n" + "="*60)
        print("✅ 最終決策")
        print("="*60)
        print(f"Action: {final_decision['action']}")
        print(f"Confidence: {final_decision['confidence']}%")
        print(f"Reasoning: {final_decision['reasoning'][:150]}...")
        print("="*60 + "\n")
        
        return final_decision
    
    def _prepare_prompts(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> Tuple[str, str]:
        """準備 system 和 user prompts"""
        
        system_prompt = """你是一個專業的加密貨幣交易 AI 分析師。
你的任務是根據市場數據、賬戶資訊和持倉狀況，給出交易建議。

輸出格式（必須是 JSON）：
{
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
  "confidence": 0-100,
  "leverage": 1-10,
  "position_size_usdt": 數字,
  "entry_price": 數字,
  "stop_loss": 數字,
  "take_profit": 數字,
  "reasoning": "理由",
  "risk_assessment": "LOW" | "MEDIUM" | "HIGH"
}"""
        
        user_prompt = f"""市場數據：
{json.dumps(market_data, indent=2, ensure_ascii=False)}

賬戶資訊：
{json.dumps(account_info, indent=2, ensure_ascii=False)}

持倉資訊：
{json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'}

請分析並給出交易建議。"""
        
        return system_prompt, user_prompt
    
    def _parse_decision(self, content: str) -> Dict:
        """解析模型輸出"""
        try:
            # 嘗試直接解析 JSON
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                decision = json.loads(json_str)
                return decision
            else:
                raise ValueError("No JSON found")
        except:
            # 如果解析失敗，返回預設值
            return {
                'action': 'HOLD',
                'confidence': 30,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'reasoning': f'模型輸出解析失敗: {content[:100]}',
                'risk_assessment': 'HIGH'
            }
    
    def _consensus_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """共識模式"""
        action_a = decision_a['action']
        action_b = decision_b['action']
        
        if action_a == action_b:
            avg_confidence = (decision_a['confidence'] + decision_b['confidence']) // 2
            
            return {
                'action': action_a,
                'confidence': avg_confidence,
                'leverage': max(decision_a['leverage'], decision_b['leverage']),
                'position_size_usdt': (decision_a['position_size_usdt'] + decision_b['position_size_usdt']) / 2,
                'entry_price': (decision_a['entry_price'] + decision_b['entry_price']) / 2,
                'stop_loss': (decision_a['stop_loss'] + decision_b['stop_loss']) / 2,
                'take_profit': (decision_a['take_profit'] + decision_b['take_profit']) / 2,
                'reasoning': f'✅ 兩個模型一致建議: {action_a}',
                'risk_assessment': decision_a['risk_assessment'],
                'agreement': True
            }
        else:
            print("⚠️ 模型意見不一致，採用保守策略 (HOLD)")
            
            return {
                'action': 'HOLD',
                'confidence': 30,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': decision_a['entry_price'],
                'stop_loss': decision_a['stop_loss'],
                'take_profit': decision_a['take_profit'],
                'reasoning': f'⚠️ 模型意見分歧: {self.model_a.name}建議 {action_a}, {self.model_b.name}建議 {action_b}. 等待更明確訊號.',
                'risk_assessment': 'HIGH',
                'agreement': False
            }
    
    def _vote_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        return self._consensus_decision(decision_a, decision_b)
    
    def _weighted_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """加權模式"""
        action_a = decision_a['action']
        action_b = decision_b['action']
        conf_a = decision_a['confidence']
        conf_b = decision_b['confidence']
        
        if action_a == action_b:
            return self._consensus_decision(decision_a, decision_b)
        
        if conf_a > conf_b:
            winner = decision_a
            winner_name = self.model_a.name
        else:
            winner = decision_b
            winner_name = self.model_b.name
        
        adjusted_confidence = int(winner['confidence'] * 0.7)
        
        print(f"⚠️ 模型意見不一致，{winner_name} 信心度更高，但降低至 {adjusted_confidence}%")
        
        return {
            'action': winner['action'],
            'confidence': adjusted_confidence,
            'leverage': winner['leverage'],
            'position_size_usdt': winner['position_size_usdt'] * 0.7,
            'entry_price': winner['entry_price'],
            'stop_loss': winner['stop_loss'],
            'take_profit': winner['take_profit'],
            'reasoning': f'⚠️ {winner_name} 信心度更高，但有爭議',
            'risk_assessment': 'MEDIUM',
            'agreement': False
        }
    
    def _fallback_decision(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> Dict:
        """備用決策（當雙模型失敗時）"""
        from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
        agent = PositionAwareDeepSeekAgent()
        return agent.analyze_with_position(market_data, account_info, position_info)
    
    def get_agreement_rate(self, last_n: int = 10) -> float:
        if not self.decision_history:
            return 0.0
        
        recent = self.decision_history[-last_n:]
        agreements = sum(1 for d in recent if d['final'].get('agreement', False))
        return (agreements / len(recent)) * 100
    
    def get_model_performance(self) -> Dict:
        if not self.decision_history:
            return {'total': 0, 'agreement_rate': 0}
        
        total = len(self.decision_history)
        agreements = sum(1 for d in self.decision_history if d['final'].get('agreement', False))
        
        return {
            'total_decisions': total,
            'agreements': agreements,
            'disagreements': total - agreements,
            'agreement_rate': (agreements / total) * 100 if total > 0 else 0
        }
