"""
雙模型決策系統
使用兩個 AI 模型互相驗證，提高決策準確性
- Model A: DeepSeek-R1 (推理強)
- Model B: GPT-4o / Gemini (穩定性好)
"""
import json
import time
from typing import Dict, Optional, List, Tuple
from core.llm_agent_position_aware import PositionAwareDeepSeekAgent


class DualModelDecisionAgent:
    """
    雙模型決策引擎
    使用兩個模型獨立分析，然後比對結果
    """
    
    def __init__(self):
        # Model A: DeepSeek-R1 (使用現有 agent)
        self.model_a = PositionAwareDeepSeekAgent()
        
        # Model B: 備用模型 (用于交叉驗證)
        self.model_b = PositionAwareDeepSeekAgent()  # 會自動使用不同 API
        
        self.decision_history: List[Dict] = []
    
    def analyze_with_dual_models(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None,
        mode: str = 'consensus'  # 'consensus', 'vote', 'weighted'
    ) -> Dict:
        """
        雙模型分析
        
        Args:
            market_data: 市場數據
            account_info: 帳戶資訊
            position_info: 持倉資訊
            mode: 決策模式
                - 'consensus': 兩個模型必須一致
                - 'vote': 簡單投票，一致則通過，不一致則 HOLD
                - 'weighted': 加權決策，根據信心度加權
        """
        print("\n" + "="*60)
        print("🔍 雙模型決策系統啟動")
        print("="*60)
        
        # 模型 A 分析
        print("\n🤖 Model A (DeepSeek-R1) 分析中...")
        decision_a = self.model_a.analyze_with_position(
            market_data, account_info, position_info
        )
        
        # 短暫延遲，避免 RPM 限制
        time.sleep(2)
        
        # 模型 B 分析
        print("\n🤖 Model B (備用模型) 分析中...")
        decision_b = self.model_b.analyze_with_position(
            market_data, account_info, position_info
        )
        
        # 比對結果
        print("\n" + "="*60)
        print("⚡ 決策比對")
        print("="*60)
        print(f"Model A: {decision_a['action']} (信心度 {decision_a['confidence']}%)")
        print(f"  理由: {decision_a['reasoning']}")
        print(f"\nModel B: {decision_b['action']} (信心度 {decision_b['confidence']}%)")
        print(f"  理由: {decision_b['reasoning']}")
        
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
            'model_a': decision_a,
            'model_b': decision_b,
            'final': final_decision,
            'mode': mode
        })
        
        print("\n" + "="*60)
        print("✅ 最終決策")
        print("="*60)
        print(f"Action: {final_decision['action']}")
        print(f"Confidence: {final_decision['confidence']}%")
        print(f"Reasoning: {final_decision['reasoning']}")
        print("="*60 + "\n")
        
        return final_decision
    
    def _consensus_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """
        共識模式: 兩個模型必須完全一致
        如果不一致，則返回 HOLD
        """
        action_a = decision_a['action']
        action_b = decision_b['action']
        
        if action_a == action_b:
            # 完全一致，取平均信心度
            avg_confidence = (decision_a['confidence'] + decision_b['confidence']) // 2
            
            return {
                'action': action_a,
                'confidence': avg_confidence,
                'leverage': max(decision_a['leverage'], decision_b['leverage']),
                'position_size_usdt': (decision_a['position_size_usdt'] + decision_b['position_size_usdt']) / 2,
                'entry_price': (decision_a['entry_price'] + decision_b['entry_price']) / 2,
                'stop_loss': (decision_a['stop_loss'] + decision_b['stop_loss']) / 2,
                'take_profit': (decision_a['take_profit'] + decision_b['take_profit']) / 2,
                'reasoning': f'✅ 兩個模型一致建議: {action_a}. A: {decision_a["reasoning"]} | B: {decision_b["reasoning"]}',
                'risk_assessment': decision_a['risk_assessment'],
                'agreement': True
            }
        else:
            # 不一致，保守策略
            print("⚠️ 模型意見不一致，採用保守策略 (HOLD)")
            
            return {
                'action': 'HOLD',
                'confidence': 30,
                'leverage': 1,
                'position_size_usdt': 0,
                'entry_price': decision_a['entry_price'],
                'stop_loss': decision_a['stop_loss'],
                'take_profit': decision_a['take_profit'],
                'reasoning': f'⚠️ 模型意見分歧: A建議 {action_a}, B建議 {action_b}. 等待更明確訊號.',
                'risk_assessment': 'HIGH',
                'agreement': False
            }
    
    def _vote_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """
        投票模式: 簡單多數決
        如果一致則通過，不一致則 HOLD
        """
        # 與 consensus 相同，但更寬鬆
        return self._consensus_decision(decision_a, decision_b)
    
    def _weighted_decision(self, decision_a: Dict, decision_b: Dict) -> Dict:
        """
        加權模式: 根據信心度加權
        信心度高的模型權重更大
        """
        action_a = decision_a['action']
        action_b = decision_b['action']
        conf_a = decision_a['confidence']
        conf_b = decision_b['confidence']
        
        # 如果兩個動作一致
        if action_a == action_b:
            return self._consensus_decision(decision_a, decision_b)
        
        # 如果不一致，選擇信心度高的
        if conf_a > conf_b:
            winner = decision_a
            loser = decision_b
            winner_name = 'Model A'
        else:
            winner = decision_b
            loser = decision_a
            winner_name = 'Model B'
        
        # 但降低信心度（因為有爭議）
        adjusted_confidence = int(winner['confidence'] * 0.7)  # 70% 折扣
        
        print(f"⚠️ 模型意見不一致，{winner_name} 信心度更高，但降低至 {adjusted_confidence}%")
        
        return {
            'action': winner['action'],
            'confidence': adjusted_confidence,
            'leverage': winner['leverage'],
            'position_size_usdt': winner['position_size_usdt'] * 0.7,  # 減少倉位
            'entry_price': winner['entry_price'],
            'stop_loss': winner['stop_loss'],
            'take_profit': winner['take_profit'],
            'reasoning': f'⚠️ {winner_name} 信心度更高 ({winner["confidence"]}% vs {loser["confidence"]}%), 但有爭議. {winner_name}: {winner["reasoning"]}',
            'risk_assessment': 'MEDIUM',
            'agreement': False
        }
    
    def get_agreement_rate(self, last_n: int = 10) -> float:
        """獲取最近 N 次決策的一致率"""
        if not self.decision_history:
            return 0.0
        
        recent = self.decision_history[-last_n:]
        agreements = sum(1 for d in recent if d['final'].get('agreement', False))
        return (agreements / len(recent)) * 100
    
    def get_model_performance(self) -> Dict:
        """獲取兩個模型的表現統計"""
        if not self.decision_history:
            return {'total': 0, 'agreement_rate': 0}
        
        total = len(self.decision_history)
        agreements = sum(1 for d in self.decision_history if d['final'].get('agreement', False))
        
        return {
            'total_decisions': total,
            'agreements': agreements,
            'disagreements': total - agreements,
            'agreement_rate': (agreements / total) * 100
        }
