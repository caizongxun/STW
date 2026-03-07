"""
多模型集成決策系統
使用多個 AI 模型投票，提高決策準確性
"""
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
import google.generativeai as genai
from core.multi_api_manager import MultiAPIManager, APIProvider


class MultiModelEnsemble:
    """多模型集成決策"""
    
    def __init__(self, system_prompt: str):
        self.api_manager = MultiAPIManager()
        self.system_prompt = system_prompt
    
    def _call_openai_compatible(self, provider: APIProvider, prompt: str) -> Optional[Dict]:
        """調用 OpenAI 兼容的 API"""
        try:
            client = OpenAI(
                api_key=provider.api_key,
                base_url=provider.base_url
            )
            
            provider.record_request()
            
            response = client.chat.completions.create(
                model=provider.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            provider.record_success()
            
            return {
                'provider': provider.name,
                'model': provider.model,
                'content': response.choices[0].message.content,
                'success': True
            }
            
        except Exception as e:
            provider.record_failure()
            print(f"❌ {provider.name} 調用失敗: {e}")
            return None
    
    def _call_gemini(self, provider: APIProvider, prompt: str) -> Optional[Dict]:
        """調用 Google Gemini API"""
        try:
            genai.configure(api_key=provider.api_key)
            model = genai.GenerativeModel(provider.model)
            
            provider.record_request()
            
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            response = model.generate_content(full_prompt)
            
            provider.record_success()
            
            return {
                'provider': provider.name,
                'model': provider.model,
                'content': response.text,
                'success': True
            }
            
        except Exception as e:
            provider.record_failure()
            print(f"❌ {provider.name} 調用失敗: {e}")
            return None
    
    def get_single_decision(self, prompt: str, purpose: str = 'general') -> Optional[Dict]:
        """獲取單個模型決策"""
        provider = self.api_manager.get_available_provider(purpose)
        
        if not provider:
            print("⚠️ 無可用的 API 提供商")
            return None
        
        print(f"\n📡 使用 {provider.name} ({provider.model})")
        
        # 根據提供商類型選擇調用方式
        if 'Gemini' in provider.name:
            result = self._call_gemini(provider, prompt)
        else:
            result = self._call_openai_compatible(provider, prompt)
        
        # 保存配置
        self.api_manager.save_config()
        
        return result
    
    def get_ensemble_decision(
        self,
        prompt: str,
        min_models: int = 2,
        max_models: int = 3
    ) -> Dict[str, Any]:
        """獲取多模型集成決策
        
        Args:
            prompt: 分析提示詞
            min_models: 最少需要幾個模型
            max_models: 最多使用幾個模型
        
        Returns:
            包含所有模型結果和投票結果的字典
        """
        results = []
        
        # 嘗試獲取多個模型的決策
        purposes = ['reasoning', 'fast', 'position'][:max_models]
        
        for purpose in purposes:
            result = self.get_single_decision(prompt, purpose)
            if result:
                results.append(result)
            
            if len(results) >= max_models:
                break
        
        if len(results) < min_models:
            print(f"⚠️ 只獲得 {len(results)} 個模型決策，少於最少需求 {min_models}")
        
        # 解析所有決策
        decisions = []
        for result in results:
            try:
                decision = self._parse_decision(result['content'])
                decision['provider'] = result['provider']
                decision['model'] = result['model']
                decisions.append(decision)
            except Exception as e:
                print(f"⚠️ 解析決策失敗 ({result['provider']}): {e}")
        
        # 投票決策
        final_decision = self._vote_decisions(decisions)
        
        return {
            'models_used': len(results),
            'individual_decisions': decisions,
            'final_decision': final_decision,
            'consensus_level': self._calculate_consensus(decisions)
        }
    
    def _parse_decision(self, content: str) -> Dict:
        """解析 AI 回應為結構化決策"""
        # 嘗試從回應中提取 JSON
        import re
        
        # 查找 JSON 代碼塊
        json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 查找裸 JSON
        json_match = re.search(r'{.*}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        # 如果無法解析 JSON，使用規則提取
        decision = {
            'action': 'HOLD',
            'confidence': 50,
            'leverage': 1,
            'reasoning': content[:200]
        }
        
        # 提取動作
        if 'OPEN_LONG' in content or '做多' in content:
            decision['action'] = 'OPEN_LONG'
        elif 'OPEN_SHORT' in content or '做空' in content:
            decision['action'] = 'OPEN_SHORT'
        elif 'CLOSE' in content or '平倉' in content:
            decision['action'] = 'CLOSE'
        
        # 提取信心度
        conf_match = re.search(r'confidence["\s:]+([0-9.]+)', content, re.IGNORECASE)
        if conf_match:
            decision['confidence'] = float(conf_match.group(1))
        
        return decision
    
    def _vote_decisions(self, decisions: List[Dict]) -> Dict:
        """投票決策"""
        if not decisions:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'leverage': 1,
                'reasoning': '無有效決策'
            }
        
        # 統計每個動作的投票
        action_votes = {}
        confidence_sum = {}
        leverage_sum = {}
        
        for d in decisions:
            action = d.get('action', 'HOLD')
            confidence = d.get('confidence', 50)
            leverage = d.get('leverage', 1)
            
            if action not in action_votes:
                action_votes[action] = 0
                confidence_sum[action] = 0
                leverage_sum[action] = 0
            
            action_votes[action] += 1
            confidence_sum[action] += confidence
            leverage_sum[action] += leverage
        
        # 選擇票數最多的動作
        final_action = max(action_votes, key=action_votes.get)
        vote_count = action_votes[final_action]
        
        # 計算平均信心度和槓桿
        avg_confidence = confidence_sum[final_action] / vote_count
        avg_leverage = leverage_sum[final_action] / vote_count
        
        return {
            'action': final_action,
            'confidence': round(avg_confidence, 2),
            'leverage': round(avg_leverage, 1),
            'votes': vote_count,
            'total_models': len(decisions),
            'reasoning': f"{vote_count}/{len(decisions)} 模型建議 {final_action}"
        }
    
    def _calculate_consensus(self, decisions: List[Dict]) -> float:
        """計算共識度 (0-1)"""
        if not decisions:
            return 0.0
        
        actions = [d.get('action', 'HOLD') for d in decisions]
        most_common = max(set(actions), key=actions.count)
        consensus = actions.count(most_common) / len(actions)
        
        return round(consensus, 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.api_manager.get_stats()
