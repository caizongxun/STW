"""
兩階段仲裁決策系統 - 多平台備援版

階段 1: 兩個快速模型獨立分析
  - Model A: Llama 3.3 70B (Groq) - 第一選擇
  - Model B: Gemini 2.0 Flash (Google) - 第一選擇（取代 DeepSeek V3）

階段 2: 仲裁者模型最終決策（多平台備援）
  1. 優先: Gemini 2.0 Flash Thinking (Google) - 免費推理模型
  2. 備用 1: Llama 3.3 70B (Groq) - 速度極快
  3. 備用 2: DeepSeek R1 (OpenRouter) - 推理能力強
  4. 備用 3: Llama 3.1 405B (OpenRouter) - 最強免費模型

修正：
- 移除 DeepSeek V3（OpenRouter 經常 404）
- 改用 Gemini 2.0 Flash 作為 Model B
- Groq + Google 雙平台，100% 穩定
"""
import json
import time
import os
from typing import Dict, Optional, List, Tuple
import requests
from datetime import datetime
from pathlib import Path


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
        
        # OpenRouter 特別需求：增加 referer 和 title
        if 'openrouter.ai' in self.base_url:
            headers['HTTP-Referer'] = 'https://github.com/caizongxun/STW'
            headers['X-Title'] = 'STW Trading Bot'
        
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
    兩階段仲裁決策引擎 + 決策歷史記錄 + 多平台備援
    用於 AI 競賽，平衡交易機會與準確性
    全部使用免費模型
    """
    
    def __init__(self):
        self.fast_model_a = None
        self.fast_model_b = None
        self.arbitrator_candidates = []  # 仲裁者候選人
        
        self.decision_history: List[Dict] = []
        self.arbitration_count = 0
        self.agreement_count = 0
        
        # 決策歷史檔案路徑
        self.history_file = Path('decision_history.json')
        
        # 讀取歷史決策
        self._load_history()
        
        self._init_models()
    
    def _load_history(self):
        """從檔案讀取歷史決策"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decision_history = data.get('decisions', [])
                    print(f"📝 讀取 {len(self.decision_history)} 筆歷史決策")
        except Exception as e:
            print(f"⚠️ 讀取歷史失敗: {e}")
            self.decision_history = []
    
    def _save_history(self):
        """保存歷史決策到檔案"""
        try:
            # 只保存最近 100 筆
            recent_decisions = self.decision_history[-100:]
            
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_decisions': len(self.decision_history),
                'decisions': recent_decisions
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"⚠️ 保存歷史失敗: {e}")
    
    def _get_recent_decisions(self, limit=5) -> List[Dict]:
        """獲取最近的 N 筆決策"""
        if not self.decision_history:
            return []
        
        recent = []
        for record in reversed(self.decision_history[-limit:]):
            final = record.get('final', {})
            recent.append({
                'datetime': record.get('datetime', ''),
                'action': final.get('action', 'UNKNOWN'),
                'confidence': final.get('confidence', 0),
                'reasoning': final.get('reasoning', '')[:100],
                'arbitration': record.get('needed_arbitration', False)
            })
        
        return recent
    
    def _init_models(self):
        print("\n" + "="*70)
        print("🏆 兩階段仲裁決策系統啟動 (Groq + Google 雙平台)")
        print("="*70)
        
        # Fast Model A: Groq Llama 70B（第一選擇）
        if os.getenv('GROQ_API_KEY'):
            self.fast_model_a = OpenAICompatibleModel(
                name='Llama_70B_Fast',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile'
            )
            print("✅ 快速模型 A: Llama 3.3 70B (Groq) - 速度極快")
        elif os.getenv('GOOGLE_API_KEY'):
            self.fast_model_a = GeminiModel(
                name='Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash'
            )
            print("✅ 快速模型 A: Gemini 2.0 Flash (Google) - 備用")
        
        # Fast Model B: Gemini 2.0 Flash（第一選擇，取代 DeepSeek V3）
        if os.getenv('GOOGLE_API_KEY'):
            self.fast_model_b = GeminiModel(
                name='Gemini_2_Flash',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash'
            )
            print("✅ 快速模型 B: Gemini 2.0 Flash (Google) - 第一選擇")
        elif os.getenv('GROQ_API_KEY'):
            self.fast_model_b = OpenAICompatibleModel(
                name='Llama_70B_Backup',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile'
            )
            print("✅ 快速模型 B: Llama 3.3 70B (Groq) - 備用")
        
        # 仲裁者候選人（按優先度排序）
        print("\n🧠 仲裁者候選人（按優先度）：")
        
        # 1. Gemini 2.0 Flash Thinking (Google) - 免費推理模型
        if os.getenv('GOOGLE_API_KEY'):
            candidate = GeminiModel(
                name='Gemini_Thinking',
                api_key=os.getenv('GOOGLE_API_KEY'),
                base_url='',
                model='gemini-2.0-flash-thinking-exp'
            )
            self.arbitrator_candidates.append(candidate)
            print("✅ 1. Gemini 2.0 Flash Thinking (Google) - 免費推理模型")
        
        # 2. Llama 3.3 70B (Groq) - 速度極快
        if os.getenv('GROQ_API_KEY'):
            candidate = OpenAICompatibleModel(
                name='Llama_70B_Arbitrator',
                api_key=os.getenv('GROQ_API_KEY'),
                base_url='https://api.groq.com/openai/v1',
                model='llama-3.3-70b-versatile'
            )
            self.arbitrator_candidates.append(candidate)
            print("✅ 2. Llama 3.3 70B (Groq) - 速度極快")
        
        # 3. DeepSeek R1 (OpenRouter) - 推理能力強
        if os.getenv('OPENROUTER_API_KEY'):
            candidate = OpenAICompatibleModel(
                name='DeepSeek_R1_Arbitrator',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-r1:free'
            )
            self.arbitrator_candidates.append(candidate)
            print("✅ 3. DeepSeek R1 (OpenRouter) - 推理能力強 (備用)")
        
        # 如果沒有任何模型，顯示警告
        if not self.fast_model_a and not self.fast_model_b:
            print("⚠️  警告: 沒有配置任何 API Key")
            print("    請設定 GROQ_API_KEY 或 GOOGLE_API_KEY")
        
        if not self.arbitrator_candidates:
            print("⚠️  警告: 沒有任何仲裁者候選人")
        
        print("\n💡 策略: 兩個快速模型分析 → 同意則執行，分歧則由仲裁者仲裁")
        print("✅ 100% 穩定: Groq (Llama 70B) + Google (Gemini 2.0 Flash)")
        print("❌ 移除: DeepSeek V3 (OpenRouter 經常 404)")
        print("🆓 全部免費: 每天約 500+ 次請求")
        print("📝 決策歷史：自動記錄至 decision_history.json")
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
        
        # 獲取最近決策
        recent_decisions = self._get_recent_decisions(5)
        
        system_prompt, user_prompt = self._prepare_prompts(
            market_data, account_info, position_info,
            historical_candles, successful_cases, recent_decisions
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
                print("🧠 階段 2: 調用仲裁者 (多平台備援)")
                print("━"*70)
                
                self.arbitration_count += 1
                final_decision = self._arbitrate(
                    market_data, account_info, position_info,
                    decision_a, decision_b,
                    historical_candles, successful_cases, recent_decisions
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
            'needed_arbitration': final_decision.get('arbitration', False),
            'market_price': market_data.get('close', 0)
        })
        
        # 保存到檔案
        self._save_history()
        
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
        successful_cases: Optional[List[Dict]],
        recent_decisions: List[Dict]
    ) -> Dict:
        """仲裁者模型決策（多平台備援）"""
        
        if not self.arbitrator_candidates:
            print("⚠️ 仲裁者未配置，選擇信心度較高的模型")
            if decision_a['confidence'] >= decision_b['confidence']:
                return decision_a
            else:
                return decision_b
        
        # 準備仲裁者 prompt
        arbitrator_system_prompt = """你是一個頂尖的加密貨幣交易 AI 仲裁者。

你的任務是根據兩個模型的分析，給出你的最終判斷。

重要：你會看到「最近 5 筆決策歷史」，請避免：
1. 重複下單（如果剛才已經 OPEN_LONG，不要再 OPEN_LONG）
2. 矛盾操作（如果持有多單，不要 OPEN_SHORT）
3. 頻繁交易（如果 5 分鐘前才交易，需要更強的訊號才再交易）

輸出 JSON 格式：
{
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
  "confidence": 0-100,
  "leverage": 1-5,
  "position_size_usdt": 數字,
  "entry_price": 數字,
  "stop_loss": 數字,
  "take_profit": 數字,
  "reasoning": "你的仲裁理由",
  "risk_assessment": "LOW" | "MEDIUM" | "HIGH"
}"""
        
        # 準備仲裁者的完整資訊
        user_prompt_parts = [
            "市場數據:",
            json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n賬戶資訊:",
            json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n持倉資訊:",
            json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'
        ]
        
        # 增加最近決策歷史
        if recent_decisions:
            user_prompt_parts.extend([
                "\n---\n最近 5 筆決策歷史（請避免重複或矛盾）:",
                json.dumps(recent_decisions, indent=2, ensure_ascii=False)
            ])
        
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
            "\n---\n",
            f"\n模型 B ({self.fast_model_b.name}) 的分析:",
            f"決策: {decision_b['action']}",
            f"信心度: {decision_b['confidence']}%",
            f"理由: {decision_b['reasoning']}",
            "\n---\n",
            "\n現在請你作為仲裁者，給出你的最終判斷。"
        ])
        
        arbitrator_user_prompt = "\n".join(user_prompt_parts)
        
        # 依次嘗試仲裁者候選人
        for idx, arbitrator in enumerate(self.arbitrator_candidates):
            print(f"\n🧠 [{arbitrator.name}] 仲裁中...")
            result = arbitrator.analyze(arbitrator_system_prompt, arbitrator_user_prompt)
            
            if result['success']:
                final_decision = self._parse_decision(result['content'])
                print(f"✅ 仲裁完成: {final_decision['action']} (信心度 {final_decision['confidence']}%) - {result['elapsed_time']:.1f}s")
                return final_decision
            else:
                print(f"❌ 仲裁失敗: {result.get('error', 'Unknown')[:100]}")
                if idx < len(self.arbitrator_candidates) - 1:
                    print(f"➡️ 嘗試下一個仲裁者...")
                    time.sleep(1)
        
        # 所有仲裁者都失敗，選擇信心度較高的模型
        print("\n⚠️ 所有仲裁者都失敗，選擇信心度較高的模型")
        if decision_a['confidence'] >= decision_b['confidence']:
            return decision_a
        else:
            return decision_b
    
    def _merge_agreements(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """合併兩個同意的決策"""
        avg_confidence = (decision_a['confidence'] + decision_b['confidence']) // 2
        
        return {
            'action': decision_a['action'],
            'confidence': min(avg_confidence + 5, 95),
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
        successful_cases: Optional[List[Dict]],
        recent_decisions: List[Dict]
    ) -> Tuple[str, str]:
        """準備快速模型的 prompt（增強版）"""
        
        system_prompt = """你是專業的加密貨幣交易 AI 分析師。

重要：你會看到「最近 5 筆決策歷史」，請避免：
1. 重複下單（如果剛才已經 OPEN_LONG，不要再 OPEN_LONG）
2. 矛盾操作（如果持有多單，不要 OPEN_SHORT）
3. 頻繁交易（如果 5 分鐘前才交易，需要更強的訊號才再交易）

分析時請重點關注：
- K 線型態（錘子、十字星、包含線、影線長度）
- 趨勢反轉訊號（連續上漲/下跌後的轉折）
- 量能變化（放量/縮量）
- 支撑/壓力位置
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
  "reasoning": "詳細理由",
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
        
        # 增加最近決策歷史
        if recent_decisions:
            user_prompt_parts.extend([
                "\n---\n最近 5 筆決策歷史（請避免重複或矛盾）:",
                json.dumps(recent_decisions, indent=2, ensure_ascii=False)
            ])
        
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
                "\n---\n過去成功案例（供參考）:",
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
