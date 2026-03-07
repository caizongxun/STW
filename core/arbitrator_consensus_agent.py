"""
三階段仲裁決策系統 - 方案 B + 多層備用機制 + 配置檔熱更新 + 多時間框架 + 交易執行審核

階段1: Model A + Model B 快速分析
階段2: 仲裁者決策 (意見分歧時)
階段3: 交易執行審核 (最終把關) ← 新增!

主力配置（方案 B）：
  - Model A: Llama 3.3 70B (Groq) - 第一選擇
  - Model B: Gemini 2.5 Flash (Google) - 修正模型名稱
  - 仲裁者: Llama 3.3 70B (Groq) - 速度快+穩定
  - 執行審核員: Gemini 2.5 Flash (Google) - 最終把關

備用機制：
  - Model A 失敗 -> Gemini Flash (Google) -> Mixtral 8x7B (Groq)
  - Model B 失敗 -> Llama 70B (Groq) -> Mixtral 8x7B (Groq)
  - 仲裁者失敗 -> Gemini Flash (Google) -> Mixtral 8x7B (Groq) -> DeepSeek R1 (OpenRouter)

新功能：
  - 配置檔支持: arbitrator_config.json
  - 熱更新: 修改配置後自動重新載入模型
  - 自定義優先序: 在 Web UI 調整模型順序
  - 詳細記錄: 記錄每次 prompt 和模型回應
  - 多時間框架: 15m (主) + 1h + 4h 看大趨勢
  - 逆勢操作: 允許在信心度高時做 1h 內逆勢
  - 交易審核: 基於信心度和市場狀況最終核准
  - 強健 JSON 解析: 自動修復各種格式錯誤

優勢：
  - 跨平台備援：Groq + Google + OpenRouter
  - 每天 16,400+ 次請求
  - 失敗自動降級，無需手動介入
  - Web UI 修改立即生效
  - 多時間框架避免小時間框架噪音
  - 三層把關減少错誤交易

修復：
  - Payload Too Large: 減少歷史 K 棒數量 (20->10)
  - Circular Reference: 移除 analysis_detail 循環引用
  - JSON 解析錯誤: 使用強健解析器自動修復
"""
import json
import time
import os
from typing import Dict, Optional, List, Tuple
import requests
from datetime import datetime
from pathlib import Path

# 導入強健 JSON 解析器
try:
    from core.json_parser_robust import parse_trading_decision
    HAS_ROBUST_PARSER = True
except ImportError:
    HAS_ROBUST_PARSER = False
    print("[WARNING] 強健 JSON 解析器不可用，使用基礎解析")


class ModelInterface:
    def __init__(self, name: str, api_key: str, base_url: str, model: str, priority: int = 1):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.priority = priority
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        raise NotImplementedError


class OpenAICompatibleModel(ModelInterface):
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
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
    三階段仲裁決策引擎 + 多層備用機制 + 配置檔熱更新 + 多時間框架 + 交易執行審核
    方案 B: Groq + Google 雙平台
    失敗自動降級備用
    """
    
    DEFAULT_CONFIG = {
        'model_a_priority': [
            {'provider': 'groq', 'model': 'llama-3.3-70b-versatile', 'name': 'Llama_70B'},
            {'provider': 'google', 'model': 'gemini-2.5-flash', 'name': 'Gemini_Flash'},
            {'provider': 'groq', 'model': 'mixtral-8x7b-32768', 'name': 'Mixtral_8x7B'}
        ],
        'model_b_priority': [
            {'provider': 'google', 'model': 'gemini-2.5-flash', 'name': 'Gemini_Flash'},
            {'provider': 'groq', 'model': 'llama-3.3-70b-versatile', 'name': 'Llama_70B'},
            {'provider': 'groq', 'model': 'mixtral-8x7b-32768', 'name': 'Mixtral_8x7B'}
        ],
        'arbitrator_priority': [
            {'provider': 'groq', 'model': 'llama-3.3-70b-versatile', 'name': 'Llama_70B'},
            {'provider': 'google', 'model': 'gemini-2.5-flash', 'name': 'Gemini_Flash'},
            {'provider': 'groq', 'model': 'mixtral-8x7b-32768', 'name': 'Mixtral_8x7B'},
            {'provider': 'openrouter', 'model': 'deepseek/deepseek-r1:free', 'name': 'DeepSeek_R1'}
        ],
        'enable_trading_executor': True
    }
    
    def __init__(self, config_file: str = 'arbitrator_config.json'):
        self.primary_model_a = None
        self.primary_model_b = None
        self.backup_models_a = []
        self.backup_models_b = []
        self.arbitrator_candidates = []
        
        self.decision_history: List[Dict] = []
        self.arbitration_count = 0
        self.agreement_count = 0
        
        self.last_analysis_detail = None
        
        self.config_file = Path(config_file)
        self.model_config = self._load_config()
        
        self.history_file = Path('decision_history.json')
        self._load_history()
        
        self._init_models()
        
        # 初始化交易執行審核員
        self.trading_executor = None
        self.enable_executor = self.model_config.get('enable_trading_executor', True)
        if self.enable_executor:
            try:
                from core.trading_executor_agent import TradingExecutorAgent
                self.trading_executor = TradingExecutorAgent()
                print("[OK] 交易執行審核員已啟動")
            except Exception as e:
                print(f"[WARNING] 交易執行審核員無法啟動: {e}")
                self.trading_executor = None
    
    def _load_config(self) -> Dict:
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"[OK] 讀取配置: {self.config_file}")
                    return config
        except Exception as e:
            print(f"[WARNING] 讀取配置失敗: {e}")
        
        print("[INFO] 使用預設配置")
        return self.DEFAULT_CONFIG
    
    def _save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_config, f, indent=2, ensure_ascii=False)
            print(f"[OK] 配置已保存: {self.config_file}")
        except Exception as e:
            print(f"[WARNING] 保存配置失敗: {e}")
    
    def reload_models(self):
        print("\n" + "="*70)
        print("[RELOAD] 熱更新: 重新載入模型配置...")
        print("="*70)
        
        self.model_config = self._load_config()
        self.primary_model_a = None
        self.primary_model_b = None
        self.backup_models_a = []
        self.backup_models_b = []
        self.arbitrator_candidates = []
        self._init_models()
        
        print("[OK] 模型熱更新完成!")
        print("="*70 + "\n")
    
    def _create_model_instance(self, provider: str, model: str, name: str, priority: int):
        if provider == 'groq':
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                return None
            return OpenAICompatibleModel(
                name=name,
                api_key=api_key,
                base_url='https://api.groq.com/openai/v1',
                model=model,
                priority=priority
            )
        
        elif provider == 'google':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return None
            return GeminiModel(
                name=name,
                api_key=api_key,
                base_url='',
                model=model,
                priority=priority
            )
        
        elif provider == 'openrouter':
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                return None
            return OpenAICompatibleModel(
                name=name,
                api_key=api_key,
                base_url='https://openrouter.ai/api/v1',
                model=model,
                priority=priority
            )
        
        return None
    
    def _load_history(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decision_history = data.get('decisions', [])
                    print(f"[INFO] 讀取 {len(self.decision_history)} 筆歷史決策")
        except Exception as e:
            print(f"[WARNING] 讀取歷史失敗: {e}")
            self.decision_history = []
    
    def _save_history(self):
        try:
            recent_decisions = self.decision_history[-100:]
            
            # 移除循環引用
            safe_decisions = []
            for record in recent_decisions:
                safe_record = {
                    'timestamp': record.get('timestamp'),
                    'datetime': record.get('datetime'),
                    'needed_arbitration': record.get('needed_arbitration'),
                    'market_price': record.get('market_price')
                }
                
                # 只保留必要的決策資訊
                for key in ['decision_a', 'decision_b', 'final']:
                    if key in record and record[key]:
                        safe_record[key] = {
                            'action': record[key].get('action'),
                            'confidence': record[key].get('confidence'),
                            'reasoning': record[key].get('reasoning', '')[:100]
                        }
                
                safe_decisions.append(safe_record)
            
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_decisions': len(self.decision_history),
                'decisions': safe_decisions
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] 保存歷史失敗: {e}")
    
    def _get_recent_decisions(self, limit=5) -> List[Dict]:
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
        print("[SYSTEM] 方案 B: 雙平台均衡 + 多層備用 + 配置熱更新 + 多時間框架 + 交易審核")
        print("="*70)
        
        print("\n[MODEL A] 快速模型 A (按優先度):")
        model_a_configs = self.model_config.get('model_a_priority', self.DEFAULT_CONFIG['model_a_priority'])
        for idx, config in enumerate(model_a_configs, 1):
            instance = self._create_model_instance(
                provider=config['provider'],
                model=config['model'],
                name=f"{config['name']}_A{idx}",
                priority=idx
            )
            
            if instance:
                if idx == 1:
                    self.primary_model_a = instance
                    print(f"  [OK] {idx}. {config['name']} ({config['provider'].upper()}) - 主力模型")
                else:
                    self.backup_models_a.append(instance)
                    print(f"  [OK] {idx}. {config['name']} ({config['provider'].upper()}) - 備用 {idx-1}")
            else:
                print(f"  [FAIL] {idx}. {config['name']} ({config['provider'].upper()}) - API Key 缺失")
        
        print("\n[MODEL B] 快速模型 B (按優先度):")
        model_b_configs = self.model_config.get('model_b_priority', self.DEFAULT_CONFIG['model_b_priority'])
        for idx, config in enumerate(model_b_configs, 1):
            instance = self._create_model_instance(
                provider=config['provider'],
                model=config['model'],
                name=f"{config['name']}_B{idx}",
                priority=idx
            )
            
            if instance:
                if idx == 1:
                    self.primary_model_b = instance
                    print(f"  [OK] {idx}. {config['name']} ({config['provider'].upper()}) - 主力模型")
                else:
                    self.backup_models_b.append(instance)
                    print(f"  [OK] {idx}. {config['name']} ({config['provider'].upper()}) - 備用 {idx-1}")
            else:
                print(f"  [FAIL] {idx}. {config['name']} ({config['provider'].upper()}) - API Key 缺失")
        
        print("\n[ARBITRATOR] 仲裁者候選人 (按優先度):")
        arbitrator_configs = self.model_config.get('arbitrator_priority', self.DEFAULT_CONFIG['arbitrator_priority'])
        for idx, config in enumerate(arbitrator_configs, 1):
            instance = self._create_model_instance(
                provider=config['provider'],
                model=config['model'],
                name=f"{config['name']}_Arb{idx}",
                priority=idx
            )
            
            if instance:
                self.arbitrator_candidates.append(instance)
                print(f"  [OK] {idx}. {config['name']} ({config['provider'].upper()})")
            else:
                print(f"  [FAIL] {idx}. {config['name']} ({config['provider'].upper()}) - API Key 缺失")
        
        print("\n[STATS] 系統統計:")
        print(f"  Model A: {1 if self.primary_model_a else 0} 主力 + {len(self.backup_models_a)} 備用")
        print(f"  Model B: {1 if self.primary_model_b else 0} 主力 + {len(self.backup_models_b)} 備用")
        print(f"  仲裁者: {len(self.arbitrator_candidates)} 候選人")
        print(f"  執行審核員: {'Enabled' if self.trading_executor else 'Disabled'}")
        print(f"  JSON 解析: {'Robust Parser' if HAS_ROBUST_PARSER else 'Basic Parser'}")
        
        print("\n[STRATEGY] 策略: 三階段決策流程")
        print("  階段1: 兩個快速模型分析 (Model A + Model B)")
        print("  階段2: 仲裁者決策 (分歧時調用)")
        if self.trading_executor:
            print("  階段3: 交易執行審核 (最終把關)")
            print("    - 信心度 >= 60%: 自動執行")
            print("    - 信心度 50-59%: 減少倉位 50%")
            print("    - 信心度 < 50%: 拒絕執行")
            print("    - 逆勢操作需要 >= 70% 信心度")
        print("  跨平台: Groq + Google + OpenRouter")
        print("  每天約 16,400+ 次請求")
        print(f"  決策歷史: {self.history_file}")
        print(f"  配置檔: {self.config_file}")
        print("  熱更新: 修改配置立即生效 (無需重啟)")
        print("  多時間框架: 15m (主) + 1h + 4h 分析")
        print("  逆勢操作: 允許在 1h 內高信心度逆勢")
        print("  Payload 優化: 歷史 K 棒減少 (20->10)")
        if HAS_ROBUST_PARSER:
            print("  JSON 解析: 自動修復 Markdown/單引號/格式錯誤")
        print("="*70 + "\n")
    
    def _try_model_with_backups(self, primary_model, backup_models, system_prompt, user_prompt, label="Model"):
        if primary_model:
            print(f"\n[{primary_model.name}] 分析中...")
            result = primary_model.analyze(system_prompt, user_prompt)
            
            if result['success']:
                decision = self._parse_decision(result['content'])
                decision['raw_reasoning'] = result['content']
                decision['model_name'] = primary_model.name
                print(f"[OK] [{primary_model.name}]: {decision['action']} (信心度 {decision['confidence']}%) - {result['elapsed_time']:.1f}s")
                print(f"     理由: {decision['reasoning'][:80]}...")
                return decision
            else:
                error_msg = result.get('error', 'Unknown')[:150]
                print(f"[FAIL] [{primary_model.name}] 失敗: {error_msg}")
                if 'Payload Too Large' in error_msg or '413' in error_msg:
                    print("       -> 建議: 減少歷史 K 棒數量")
        
        for idx, backup in enumerate(backup_models, 1):
            print(f"\n[BACKUP] 嘗試備用模型 {idx}: [{backup.name}]")
            time.sleep(1)
            
            result = backup.analyze(system_prompt, user_prompt)
            
            if result['success']:
                decision = self._parse_decision(result['content'])
                decision['raw_reasoning'] = result['content']
                decision['model_name'] = backup.name
                print(f"[OK] [{backup.name}]: {decision['action']} (信心度 {decision['confidence']}%) - {result['elapsed_time']:.1f}s")
                print(f"     理由: {decision['reasoning'][:80]}...")
                return decision
            else:
                print(f"[FAIL] [{backup.name}] 失敗: {result.get('error', 'Unknown')[:80]}")
        
        print(f"\n[FAIL] {label} 所有模型都失敗")
        return None
    
    def analyze_with_arbitration(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None,
        historical_candles: Optional[List[Dict]] = None,
        successful_cases: Optional[List[Dict]] = None,
        multi_timeframe_data: Optional[Dict] = None
    ) -> Dict:
        if not self.primary_model_a and not self.primary_model_b:
            print("[WARNING] 快速模型未配置，降級為單模型")
            from core.llm_agent_position_aware import PositionAwareDeepSeekAgent
            agent = PositionAwareDeepSeekAgent()
            return agent.analyze_with_position(market_data, account_info, position_info)
        
        print("\n" + "="*70)
        print(f"[ANALYSIS] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 階段 1: 兩個快速模型分析")
        print("="*70)
        
        recent_decisions = self._get_recent_decisions(5)
        
        # 減少 Payload: 歷史 K 棒從 20 根減至 10 根
        if historical_candles and len(historical_candles) > 10:
            historical_candles = historical_candles[-10:]
        
        # 減少 Payload: 成功案例從 10 個減至 3 個
        if successful_cases and len(successful_cases) > 3:
            successful_cases = successful_cases[:3]
        
        system_prompt, user_prompt = self._prepare_prompts(
            market_data, account_info, position_info,
            historical_candles, successful_cases, recent_decisions,
            multi_timeframe_data
        )
        
        prompt_size = len(system_prompt) + len(user_prompt)
        print(f"[INFO] Prompt 大小: {prompt_size:,} 字元")
        
        self.last_analysis_detail = {
            'timestamp': datetime.now().isoformat(),
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'model_responses': {}
        }
        
        decision_a = self._try_model_with_backups(
            self.primary_model_a,
            self.backup_models_a,
            system_prompt,
            user_prompt,
            "Model A"
        )
        
        if decision_a:
            self.last_analysis_detail['model_responses']['model_a'] = {
                'model_name': decision_a.get('model_name', 'Unknown'),
                'action': decision_a['action'],
                'confidence': decision_a['confidence'],
                'reasoning': decision_a['reasoning']
            }
        
        time.sleep(1)
        
        decision_b = self._try_model_with_backups(
            self.primary_model_b,
            self.backup_models_b,
            system_prompt,
            user_prompt,
            "Model B"
        )
        
        if decision_b:
            self.last_analysis_detail['model_responses']['model_b'] = {
                'model_name': decision_b.get('model_name', 'Unknown'),
                'action': decision_b['action'],
                'confidence': decision_b['confidence'],
                'reasoning': decision_b['reasoning']
            }
        
        if decision_a and decision_b:
            if decision_a['action'] == decision_b['action']:
                print("\n" + "="*70)
                print("[OK] 兩個模型同意，直接執行")
                print("="*70)
                
                self.agreement_count += 1
                final_decision = self._merge_agreements(decision_a, decision_b)
                final_decision['arbitration'] = False
            else:
                print("\n" + "="*70)
                print(f"[WARNING] 意見分歧: {decision_a['action']} vs {decision_b['action']}")
                print("[ARBITRATOR] 階段 2: 調用仲裁者")
                print("="*70)
                
                self.arbitration_count += 1
                final_decision = self._arbitrate(
                    market_data, account_info, position_info,
                    decision_a, decision_b,
                    historical_candles, successful_cases, recent_decisions,
                    multi_timeframe_data
                )
                final_decision['arbitration'] = True
        elif decision_a:
            print("\n[WARNING] Model B 所有模型失敗，使用 Model A")
            final_decision = decision_a
            final_decision['arbitration'] = False
        elif decision_b:
            print("\n[WARNING] Model A 所有模型失敗，使用 Model B")
            final_decision = decision_b
            final_decision['arbitration'] = False
        else:
            print("\n[FAIL] 所有模型都失敗，HOLD")
            final_decision = self._emergency_hold()
            final_decision['arbitration'] = False
        
        # 階段 3: 交易執行審核
        if self.trading_executor:
            execution_review = self.trading_executor.review_trading_decision(
                arbitrator_decision=final_decision,
                market_data=market_data,
                account_info=account_info,
                position_info=position_info,
                multi_timeframe_data=multi_timeframe_data
            )
            
            self.last_analysis_detail['model_responses']['executor'] = {
                'execution_decision': execution_review['execution_decision'],
                'final_action': execution_review['final_action'],
                'adjusted_confidence': execution_review['adjusted_confidence'],
                'reasoning': execution_review['executor_reasoning']
            }
            
            # 使用審核後的決策
            final_decision = execution_review
        
        self.decision_history.append({
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'decision_a': decision_a,
            'decision_b': decision_b,
            'final': final_decision,
            'needed_arbitration': final_decision.get('arbitration', False),
            'market_price': market_data.get('close', 0)
        })
        self._save_history()
        
        print("\n" + "="*70)
        print("[FINAL] 最終決策")
        print("="*70)
        print(f"Action: {final_decision.get('final_action', final_decision.get('action'))}")
        print(f"Confidence: {final_decision.get('adjusted_confidence', final_decision.get('confidence'))}%")
        if 'execution_decision' in final_decision:
            print(f"Execution: {final_decision['execution_decision']}")
        elif final_decision.get('arbitration'):
            print("[ARBITRATOR] 由仲裁者決定")
        else:
            print("[CONSENSUS] 兩個模型共識")
        print(f"Reasoning: {final_decision.get('executor_reasoning', final_decision.get('reasoning', ''))[:150]}...")
        print("="*70 + "\n")
        
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
        recent_decisions: List[Dict],
        multi_timeframe_data: Optional[Dict] = None
    ) -> Dict:
        if not self.arbitrator_candidates:
            print("[WARNING] 仲裁者未配置，選擇信心度較高的模型")
            return decision_a if decision_a['confidence'] >= decision_b['confidence'] else decision_b
        
        arbitrator_system_prompt = """你是頂尖的加密貨幣交易 AI 仲裁者。

根據兩個模型的分析，給出你的最終判斷。

重要：避免重複下單、矛盾操作、頻繁交易。

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
        
        user_prompt_parts = [
            "市場數據:", json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n賬戶資訊:", json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n持倉:", json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無',
            "\n---\nModel A 分析:",
            f"決策: {decision_a['action']}, 信心: {decision_a['confidence']}%, 理由: {decision_a['reasoning']}",
            "\n---\nModel B 分析:",
            f"決策: {decision_b['action']}, 信心: {decision_b['confidence']}%, 理由: {decision_b['reasoning']}",
            "\n---\n請作為仲裁者給出最終判斷。"
        ]
        arbitrator_user_prompt = "\n".join(user_prompt_parts)
        
        for idx, arbitrator in enumerate(self.arbitrator_candidates):
            print(f"\n[ARBITRATOR] [{arbitrator.name}] 仲裁中...")
            result = arbitrator.analyze(arbitrator_system_prompt, arbitrator_user_prompt)
            
            if result['success']:
                final_decision = self._parse_decision(result['content'])
                final_decision['model_name'] = arbitrator.name
                final_decision['raw_reasoning'] = result['content']
                
                self.last_analysis_detail['model_responses']['arbitrator'] = {
                    'model_name': arbitrator.name,
                    'action': final_decision['action'],
                    'confidence': final_decision['confidence'],
                    'reasoning': final_decision['reasoning']
                }
                
                print(f"[OK] 仲裁完成: {final_decision['action']} (信心 {final_decision['confidence']}%) - {result['elapsed_time']:.1f}s")
                return final_decision
            else:
                print(f"[FAIL] 仲裁失敗: {result.get('error', '')[:80]}")
                if idx < len(self.arbitrator_candidates) - 1:
                    print("[BACKUP] 嘗試下一個仲裁者...")
                    time.sleep(1)
        
        print("\n[WARNING] 所有仲裁者失敗，選擇信心度高者")
        return decision_a if decision_a['confidence'] >= decision_b['confidence'] else decision_b
    
    def _merge_agreements(self, decision_a: Dict, decision_b: Dict) -> Dict:
        avg_confidence = (decision_a['confidence'] + decision_b['confidence']) // 2
        return {
            'action': decision_a['action'],
            'confidence': min(avg_confidence + 5, 95),
            'leverage': max(decision_a['leverage'], decision_b['leverage']),
            'position_size_usdt': (decision_a['position_size_usdt'] + decision_b['position_size_usdt']) / 2,
            'entry_price': (decision_a['entry_price'] + decision_b['entry_price']) / 2,
            'stop_loss': (decision_a['stop_loss'] + decision_b['stop_loss']) / 2,
            'take_profit': (decision_a['take_profit'] + decision_b['take_profit']) / 2,
            'reasoning': f"[CONSENSUS] 共識: {decision_a['action']}. A: {decision_a['reasoning'][:50]}... B: {decision_b['reasoning'][:50]}...",
            'risk_assessment': decision_a['risk_assessment']
        }
    
    def _prepare_prompts(self, market_data, account_info, position_info, historical_candles, successful_cases, recent_decisions, multi_timeframe_data=None) -> Tuple[str, str]:
        system_prompt = """專業加密貨幣交易 AI。

你的任務:
1. 分析當前市場數據、歷史 K 棒走勢、技術指標
2. 參考最近決策結果，避免重複操作
3. 學習成功案例的模式
4. **結合多時間框架** (15m + 1h + 4h) 看清大趨勢
5. 給出明確的交易建議

重要原則:
- 避免重複下單、矛盾操作、頻繁交易
- 不要在持有多單時再次 OPEN_LONG
- 不要在沒有持倉時 CLOSE
- **主時間框架為 15分鐘**，但要參考 1h 和 4h 趨勢
- **允許逆勢操作**：在信心度高 (>75%) 且技術指標強勁時，可以在 **1小時內** 做 15分鐘的逆勢操作

輸出 JSON 格式:
{"action": "OPEN_LONG|OPEN_SHORT|CLOSE|HOLD", "confidence": 0-100, "leverage": 1-5, "position_size_usdt": 數字, "entry_price": 數字, "stop_loss": 數字, "take_profit": 數字, "reasoning": "詳細理由", "risk_assessment": "LOW|MEDIUM|HIGH", "is_counter_trend": true|false}"""
        
        user_prompt_parts = [
            "=== 市場數據 (15m) ===",
            json.dumps(market_data, indent=2, ensure_ascii=False),
            "\n=== 賬戶資訊 ===",
            json.dumps(account_info, indent=2, ensure_ascii=False),
            "\n=== 當前持倉 ===",
            json.dumps(position_info, indent=2, ensure_ascii=False) if position_info else '無持倉'
        ]
        
        # 多時間框架 - 只保留關鍵資訊
        if multi_timeframe_data:
            simplified_mt = {}
            for tf, data in multi_timeframe_data.items():
                simplified_mt[tf] = {
                    'current': data.get('current', {}),
                    'trend': data.get('trend_analysis', {})
                }
            user_prompt_parts.extend([
                "\n=== 多時間框架 ===",
                json.dumps(simplified_mt, indent=2, ensure_ascii=False)
            ])
        
        if historical_candles and len(historical_candles) > 0:
            user_prompt_parts.extend([
                f"\n=== 歷史 K 棒 (前 {len(historical_candles)} 根) ===",
                json.dumps(historical_candles, indent=2, ensure_ascii=False)
            ])
        
        if recent_decisions and len(recent_decisions) > 0:
            user_prompt_parts.extend([
                f"\n=== 最近決策 ===",
                json.dumps(recent_decisions, indent=2, ensure_ascii=False)
            ])
        
        if successful_cases and len(successful_cases) > 0:
            user_prompt_parts.extend([
                f"\n=== 成功案例 ===",
                json.dumps(successful_cases, indent=2, ensure_ascii=False)
            ])
        
        user_prompt_parts.append("\n請基於以上資訊給出交易建議。")
        
        user_prompt = "\n".join(user_prompt_parts)
        
        return system_prompt, user_prompt
    
    def _parse_decision(self, content: str) -> Dict:
        """解析模型輸出為決策字典"""
        if HAS_ROBUST_PARSER:
            # 使用強健解析器
            return parse_trading_decision(content)
        else:
            # 備用: 基礎解析
            try:
                if '{' in content and '}' in content:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    decision = json.loads(content[start:end])
                    if 'is_counter_trend' not in decision:
                        decision['is_counter_trend'] = False
                    return decision
            except:
                pass
            
            return {
                'action': 'HOLD', 'confidence': 30, 'leverage': 1, 'position_size_usdt': 0,
                'entry_price': 0, 'stop_loss': 0, 'take_profit': 0,
                'reasoning': '解析失敗', 'risk_assessment': 'HIGH', 'is_counter_trend': False
            }
    
    def _emergency_hold(self) -> Dict:
        return {
            'action': 'HOLD', 'confidence': 0, 'leverage': 1, 'position_size_usdt': 0,
            'entry_price': 0, 'stop_loss': 0, 'take_profit': 0,
            'reasoning': '緊急 HOLD: 模型失敗', 'risk_assessment': 'HIGH', 'is_counter_trend': False
        }
    
    def get_last_analysis_detail(self) -> Optional[Dict]:
        return self.last_analysis_detail
    
    def get_statistics(self) -> Dict:
        if not self.decision_history:
            return {'total': 0}
        total = len(self.decision_history)
        stats = {
            'total_decisions': total,
            'agreements': self.agreement_count,
            'arbitrations': self.arbitration_count,
            'agreement_rate': (self.agreement_count / total) * 100 if total > 0 else 0,
            'arbitration_rate': (self.arbitration_count / total) * 100 if total > 0 else 0
        }
        
        if self.trading_executor:
            executor_stats = self.trading_executor.get_statistics()
            stats['executor'] = executor_stats
        
        return stats
