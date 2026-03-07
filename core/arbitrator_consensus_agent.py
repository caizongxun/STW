"""
兩階段仲裁決策系統 - AI 競賽優化版

階段 1: 兩個快速模型獨立分析
  - Model A: Llama 3.3 70B (Groq) 或 DeepSeek R1 (OpenRouter)
  - Model B: DeepSeek V3 (OpenRouter) 或 Gemini 2.0 Flash

階段 2: 仲裁者模型最終決策
  - Llama 3.1 405B (OpenRouter) - 最強免費模型

優勢:
1. 全部免費模型，無需信用卡
2. 多個備用選擇，避免單點失敗
3. DeepSeek 推理能力強，適合交易分析
"""
import json
import time
import os
from typing import Dict, Optional, List, Tuple
import requests
from datetime import datetime


class ModelInterface:
    def __init__(self, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
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
            'max_tokens': 4000
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
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
                    max_output_tokens=4000
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


class ArbitratorConsensusAgent:
    """
    兩階段仲裁決策引擎
    用於 AI 競賽，平衡交易機會與準確性
    全部使用免費模型
    """
    
    def __init__(self):
        self.fast_model_a = None
        self.fast_model_b = None
        self.arbitrator = None
        
        self.decision_history: List[Dict] = []
        self.arbitration_count = 0
        self.agreement_count = 0
        
        self._init_models()
    
    def _init_models(self):
        print("\n" + "="*70)
        print("🏆 兩階段仲裁決策系統啟動 (全部免費模型)")
        print("="*70)
        
        # Fast Model A: 優先 Groq Llama 70B，備用 OpenRouter DeepSeek R1
        if os.getenv('GROQ_API_KEY'):
            self.fast_model_a = OpenAICompatibleModel(
                name='Llama_70B_Fast',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile'
            )
            print("✅ 快速模型 A: Llama 3.3 70B (Groq) - 速度極快")
        elif os.getenv('OPENROUTER_API_KEY'):
            self.fast_model_a = OpenAICompatibleModel(
                name='DeepSeek_R1',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-r1:free'
            )
            print("✅ 快速模型 A: DeepSeek R1 (OpenRouter) - 推理能力強")
        
        # Fast Model B: 優先 OpenRouter DeepSeek V3，備用 Gemini
        if os.getenv('OPENROUTER_API_KEY'):
            self.fast_model_b = OpenAICompatibleModel(
                name='DeepSeek_V3',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-chat:free'
            )
            print("✅ 快速模型 B: DeepSeek V3 (OpenRouter) - 通用強")
        elif os.getenv('GOOGLE_API_KEY'):
            self.fast_model_b = GeminiModel(
                name='Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash'
            )
            print("✅ 快速模型 B: Gemini 2.0 Flash (Google) - 備用")
        
        # Arbitrator: Llama 3.1 405B (OpenRouter 免費最強)
        if os.getenv('OPENROUTER_API_KEY'):
            self.arbitrator = OpenAICompatibleModel(
                name='Llama_405B_Arbitrator',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='meta-llama/llama-3.1-405b-instruct:free'
            )
            print("✅ 仲裁者: Llama 3.1 405B (OpenRouter) - 免費最強")
        
        # 如果沒有任何模型，顯示警告
        if not self.fast_model_a and not self.fast_model_b:
            print("⚠️  警告: 沒有配置任何 API Key")
            print("    請設定 OPENROUTER_API_KEY 或 GROQ_API_KEY")
        
        print("\n💡 策略: 兩個快速模型分析 → 同意則執行，分歧則由 405B 仲裁")
        print("🆓 全部免費: OpenRouter (20 req/min, 200 req/day)")
        print("="*70 + "\n")
    
    def analyze_with_arbitration(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None,
        historical_candles: Optional[List[Dict]] = None,
        successful_cases: Optional[List[Dict]] = None
    ) -> Dict:
        """兩階段仲裁分析（增強版）"""
        
        if not all([self.fast_model_a, self.fast_model_b]):
            print("⚠️ 快速模型未配置，降級為單模型")
            from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
            agent = PositionAwareDeepSeekAgent()
            return agent.analyze_with_position(market_data, account_info, position_info)
        
        print("\n" + "━"*70)
        print(f"🔍 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 階段 1: 兩個快速模型分析")
        print("━"*70)
        
        system_prompt, user_prompt = self._prepare_prompts(
            market_data, account_info, position_info,
            historical_candles, successful_cases
        )
        
        # 階段 1: 兩個快速模型同時分析
        print(f"\n🤖 [{self.fast_model_a.name}] 分析中...")
        result_a = self.fast_model_a.analyze(system_prompt, user_prompt)
        
        if result_a['success']:
            decision_a = self._parse_decision(result_a['content'])
            decision_a['raw_reasoning'] = result_a['content']
            print(f"✅ [{self.fast_model_a.name}]: {decision_a['action']} (信心度 {decision_a['confidence']}%) - {result_a['elapsed_time']:.1f}s")
            print(f"   理由: {decision_a['reasoning'][:80]}...")
        else:
            print(f"❌ [{self.fast_model_a.name}] 失敗: {result_a.get('error', 'Unknown')[:100]}")
            decision_a = None
        
        time.sleep(1)
        
        print(f"\n🤖 [{self.fast_model_b.name}] 分析中...")
        result_b = self.fast_model_b.analyze(system_prompt, user_prompt)
        
        if result_b['success']:
            decision_b = self._parse_decision(result_b['content'])
            decision_b['raw_reasoning'] = result_b['content']
            print(f"✅ [{self.fast_model_b.name}]: {decision_b['action']} (信心度 {decision_b['confidence']}%) - {result_b['elapsed_time']:.1f}s")
            print(f"   理由: {decision_b['reasoning'][:80]}...")
        else:
            print(f"❌ [{self.fast_model_b.name}] 失敗: {result_b.get('error', 'Unknown')[:100]}")
            decision_b = None
        
        # 檢查是否需要仲裁
        if decision_a and decision_b:
            if decision_a['action'] == decision_b['action']:
                # 同意，直接執行
                print("\n" + "━"*70)
                print("✅ 兩個模型同意，直接執行")
                print("━"*70)
                
                self.agreement_count += 1
                final_decision = self._merge_agreements(decision_a, decision_b)
                final_decision['arbitration'] = False
                
            else:
                # 分歧，需要仲裁
                print("\n" + "━"*70)
                print(f"⚠️ 意見分歧: {decision_a['action']} vs {decision_b['action']}")
                print("🧠 階段 2: 調用仲裁者 (Llama 405B)")
                print("━"*70)
                
                self.arbitration_count += 1
                final_decision = self._arbitrate(
                    market_data, account_info, position_info,
                    decision_a, decision_b,
                    historical_candles, successful_cases
                )
                final_decision['arbitration'] = True
        
        elif decision_a:
            print("\n⚠️ 模型 B 失敗，使用模型 A 的結果")
            final_decision = decision_a
            final_decision['arbitration'] = False
        elif decision_b:
            print("\n⚠️ 模型 A 失敗，使用模型 B 的結果")
            final_decision = decision_b
            final_decision['arbitration'] = False
        else:
            print("\n❌ 兩個模型都失敗，HOLD")
            final_decision = self._emergency_hold()
            final_decision['arbitration'] = False
        
        # 記錄歷史
        self.decision_history.append({
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'decision_a': decision_a,
            'decision_b': decision_b,
            'final': final_decision,
            'needed_arbitration': final_decision.get('arbitration', False)
        })
        
        print("\n" + "━"*70)
        print("✅ 最終決策")
        print("━"*70)
        print(f"Action: {final_decision['action']}")
        print(f"Confidence: {final_decision['confidence']}%")
        if final_decision.get('arbitration'):
            print("🧠 由仲裁者決定")
        else:
            print("✅ 兩個模型共識")
        print(f"Reasoning: {final_decision['reasoning'][:150]}...")
        print("━"*70 + "\n")
        
        return final_decision
    
    def _arbitrate(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict],
        decision_a: Dict,
        decision_b: Dict,
        historical_candles: Optional[List[Dict]],
        successful_cases: Optional[List[Dict]]
    ) -> Dict:
        """仲裁者模型決策"""
        
        if not self.arbitrator:
            print("⚠️ 仲裁者未配置，選擇信心度較高的模型")
            if decision_a['confidence'] >= decision_b['confidence']:
                return decision_a
            else:
                return decision_b
        
        # 準備仲裁者 prompt
        arbitrator_system_prompt = """你是一個頂尖的加密貨幣交易 AI 仲裁者。

你的任務是根據兩個模型的分析，給出你的最終判斷。

你需要：
1. 仔細閱讀兩個模型的分析
2. 評估各自的優勣勢
3. 結合當前市場數據
4. 參考歷史 K 棒和成功案例
5. 給出你的最終決策

輸出 JSON 格式：
{
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
  "confidence": 0-100,
  "leverage": 1-5,
  "position_size_usdt": 數字,
  "entry_price": 數字,
  "stop_loss": 數字,
  "take_profit": 數字,
  "reasoning": "你的仲裁理由，說明為什麼選擇這個決策",
  "risk_assessment": "LOW" | "MEDIUM" | "HIGH",
  "analysis_of_model_a": "評價模型 A 的分析",
  "analysis_of_model_b": "評價模型 B 的分析"
}

重要: 你可以選擇 A、B 或給出完全不同的第三個答案。"""
        
        # 準備仲裁者的完整資訊
        user_prompt_parts = [
            "市場數據:",
            json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n賬戶資訊:",
            json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n持倉資訊:",
            json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'
        ]
        
        # 增加歷史 K 棒資訊
        if historical_candles and len(historical_candles) > 0:
            user_prompt_parts.extend([
                "\n---\n歷史 K 棒 (最近 20 根):",
                json.dumps(historical_candles[-20:], indent=2, ensure_ascii=False)
            ])
        
        # 增加成功案例
        if successful_cases and len(successful_cases) > 0:
            user_prompt_parts.extend([
                "\n---\n過去成功案例（供參考）:",
                json.dumps(successful_cases[:5], indent=2, ensure_ascii=False)
            ])
        
        user_prompt_parts.extend([
            "\n---\n",
            f"\n模型 A ({self.fast_model_a.name}) 的分析:",
            f"決策: {decision_a['action']}",
            f"信心度: {decision_a['confidence']}%",
            f"理由: {decision_a['reasoning']}",
            f"完整分析:",
            decision_a.get('raw_reasoning', '')[:1500],
            "\n---\n",
            f"\n模型 B ({self.fast_model_b.name}) 的分析:",
            f"決策: {decision_b['action']}",
            f"信心度: {decision_b['confidence']}%",
            f"理由: {decision_b['reasoning']}",
            f"完整分析:",
            decision_b.get('raw_reasoning', '')[:1500],
            "\n---\n",
            "\n現在請你作為仲裁者，給出你的最終判斷。"
        ])
        
        arbitrator_user_prompt = "\n".join(user_prompt_parts)
        
        print(f"\n🧠 [{self.arbitrator.name}] 仲裁中...")
        result = self.arbitrator.analyze(arbitrator_system_prompt, arbitrator_user_prompt)
        
        if result['success']:
            final_decision = self._parse_decision(result['content'])
            print(f"✅ 仲裁完成: {final_decision['action']} (信心度 {final_decision['confidence']}%) - {result['elapsed_time']:.1f}s")
            return final_decision
        else:
            print(f"❌ 仲裁失敗: {result.get('error', 'Unknown')[:100]}")
            print("⚠️ 選擇信心度較高的模型")
            if decision_a['confidence'] >= decision_b['confidence']:
                return decision_a
            else:
                return decision_b
    
    def _merge_agreements(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """合併兩個同意的決策"""
        avg_confidence = (decision_a['confidence'] + decision_b['confidence']) // 2
        
        return {
            'action': decision_a['action'],
            'confidence': min(avg_confidence + 5, 95),  # 同意提高信心度
            'leverage': max(decision_a['leverage'], decision_b['leverage']),
            'position_size_usdt': (decision_a['position_size_usdt'] + decision_b['position_size_usdt']) / 2,
            'entry_price': (decision_a['entry_price'] + decision_b['entry_price']) / 2,
            'stop_loss': (decision_a['stop_loss'] + decision_b['stop_loss']) / 2,
            'take_profit': (decision_a['take_profit'] + decision_b['take_profit']) / 2,
            'reasoning': f"✅ 兩個模型共識: {decision_a['action']}. A: {decision_a['reasoning'][:50]}... B: {decision_b['reasoning'][:50]}...",
            'risk_assessment': decision_a['risk_assessment']
        }
    
    def _prepare_prompts(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict],
        historical_candles: Optional[List[Dict]],
        successful_cases: Optional[List[Dict]]
    ) -> Tuple[str, str]:
        """準備快速模型的 prompt（增強版）"""
        
        system_prompt = """你是專業的加密貨幣交易 AI 分析師。

你會收到：
1. 40 種技術指標（RSI, MACD, Bollinger Bands 等）
2. 歷史 K 棒（最近 20 根，包含開高低收和影線資訊）
3. 過去成功案例（供參考學習）

分析時請重點關注：
- K 線型態（錘子、十字星、包含線、影線長度）
- 趋勡反轉訊號（連續上漲/下跌後的轉折）
- 量能變化（放量/縮量）
- 支撐/壔力位置
- 過去成功案例的經驗

輸出 JSON 格式:
{
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
  "confidence": 0-100,
  "leverage": 1-5,
  "position_size_usdt": 數字,
  "entry_price": 數字,
  "stop_loss": 數字,
  "take_profit": 數字,
  "reasoning": "詳細理由，包含 K 線判斷和趋勡分析",
  "risk_assessment": "LOW" | "MEDIUM" | "HIGH"
}"""
        
        # 準備 user prompt
        user_prompt_parts = [
            "市場數據（40 種技術指標）:",
            json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n賬戶資訊:",
            json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n持倉:",
            json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'
        ]
        
        # 增加歷史 K 棒
        if historical_candles and len(historical_candles) > 0:
            user_prompt_parts.extend([
                "\n---\n歷史 K 棒 (最近 20 根):",
                "請特別注意 K 線的顏色、影線長度和型態。",
                json.dumps(historical_candles[-20:], indent=2, ensure_ascii=False)
            ])
        
        # 增加成功案例
        if successful_cases and len(successful_cases) > 0:
            user_prompt_parts.extend([
                "\n---\n過去成功案例（供參考，學習何時該進場/出場）:",
                json.dumps(successful_cases[:5], indent=2, ensure_ascii=False)
            ])
        
        user_prompt_parts.append("\n請分析並給出交易建議。")
        
        user_prompt = "\n".join(user_prompt_parts)
        
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
            'reasoning': '解析失敗',
            'risk_assessment': 'HIGH'
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
            'reasoning': '緊急 HOLD: 模型失敗',
            'risk_assessment': 'HIGH'
        }
    
    def get_statistics(self) -> Dict:
        if not self.decision_history:
            return {'total': 0}
        
        total = len(self.decision_history)
        
        return {
            'total_decisions': total,
            'agreements': self.agreement_count,
            'arbitrations': self.arbitration_count,
            'agreement_rate': (self.agreement_count / total) * 100 if total > 0 else 0,
            'arbitration_rate': (self.arbitration_count / total) * 100 if total > 0 else 0
        }
