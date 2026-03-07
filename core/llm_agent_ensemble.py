"""
增强版 AI Agent - 支持多 API 輪換 + 多模型集成
取代原有的 PositionAwareDeepSeekAgent
"""
import os
import json
from typing import Dict, List, Optional, Any
from core.multi_model_ensemble import MultiModelEnsemble


class EnhancedTradingAgent:
    """增强版交易 Agent"""
    
    def __init__(self, enable_ensemble: bool = True):
        """
        Args:
            enable_ensemble: 是否启用多模型集成决策
        """
        self.enable_ensemble = enable_ensemble
        self.min_models = int(os.getenv('MIN_MODELS_FOR_CONSENSUS', 2))
        self.max_models = int(os.getenv('MAX_MODELS_PER_REQUEST', 3))
        
        self.system_prompt = self._build_system_prompt()
        self.ensemble = MultiModelEnsemble(self.system_prompt)
        
        print(f"\n🤖 增强版 Trading Agent 已启动")
        print(f"  - 集成决策: {'\u2705 启用' if enable_ensemble else '❌ 禁用'}")
        if enable_ensemble:
            print(f"  - 最少模型: {self.min_models}")
            print(f"  - 最多模型: {self.max_models}")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一位专业的加密货币交易分析师，擅长技术分析和风险管理。

你的任务：
1. 分析当前市场数据（价格、技术指标、趋势）
2. 考虑当前账户情况（余额、持仓、浮盈浮亏）
3. 评估风险并给出交易建议

必须以 JSON 格式返回：
```json
{
  "action": "OPEN_LONG | OPEN_SHORT | CLOSE | ADD_POSITION | REDUCE_POSITION | HOLD",
  "confidence": 70,
  "leverage": 2,
  "position_size_usdt": 1000,
  "stop_loss": 45000,
  "take_profit": 48000,
  "reasoning": "详细分析...",
  "risk_assessment": "LOW | MEDIUM | HIGH",
  "key_factors": [
    "RSI 超卖 (35)",
    "MACD 金叉",
    "布林带下轨支撑"
  ]
}
```

决策原则：
- OPEN_LONG: RSI < 40 + MACD 金叉 + 趋势向上
- OPEN_SHORT: RSI > 60 + MACD 死叉 + 趋势向下
- CLOSE: 止盈/止损触发 或 趋势反转
- ADD_POSITION: 原有仓位盈利 > 2% 且趋势继续
- REDUCE_POSITION: 原有仓位亏损 > 1% 或趋势转弱
- HOLD: 不符合以上条件

风险管理：
- 单次仓位不超过可用余额的 30%
- 根据波动度调整杠杆 (1-10x)
- 必须设置止损和止盈
"""
    
    def analyze_with_position(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """分析市场并给出交易建议
        
        Args:
            market_data: 市场数据（价格、指标）
            account_info: 账户信息（余额、权益）
            position_info: 当前持仓（可选）
        
        Returns:
            交易决策
        """
        prompt = self._build_analysis_prompt(market_data, account_info, position_info)
        
        if self.enable_ensemble:
            # 多模型集成决策
            result = self.ensemble.get_ensemble_decision(
                prompt,
                min_models=self.min_models,
                max_models=self.max_models
            )
            
            self._print_ensemble_result(result)
            
            return result['final_decision']
        else:
            # 单模型决策
            result = self.ensemble.get_single_decision(prompt, purpose='reasoning')
            
            if result:
                decision = self.ensemble._parse_decision(result['content'])
                print(f"\n👉 决策: {decision['action']} (信心度 {decision['confidence']}%)")
                return decision
            else:
                return self._get_default_decision()
    
    def analyze_fast(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Optional[Dict] = None
    ) -> Dict:
        """快速分析（使用最快的 API）"""
        prompt = self._build_analysis_prompt(market_data, account_info, position_info)
        
        result = self.ensemble.get_single_decision(prompt, purpose='fast')
        
        if result:
            decision = self.ensemble._parse_decision(result['content'])
            return decision
        else:
            return self._get_default_decision()
    
    def get_position_control(
        self,
        market_data: Dict,
        account_info: Dict,
        position_info: Dict
    ) -> Dict:
        """仓位管理控制（使用 Groq 快速决策）"""
        prompt = f"""
当前持仓情况：
- 方向: {position_info.get('side')}
- 持仓量: {position_info.get('size')}
- 开仓价: {position_info.get('entry_price')}
- 当前价: {market_data.get('close')}
- 浮盈浮亏: {position_info.get('unrealized_pnl')}%

请决定是否需要：
1. 加仓 (ADD_POSITION)
2. 减仓 (REDUCE_POSITION)
3. 平仓 (CLOSE)
4. 保持 (HOLD)

只返回 JSON。
        """
        
        result = self.ensemble.get_single_decision(prompt, purpose='position')
        
        if result:
            return self.ensemble._parse_decision(result['content'])
        else:
            return {'action': 'HOLD', 'confidence': 0}
    
    def _build_analysis_prompt(self, market_data: Dict, account_info: Dict, position_info: Optional[Dict]) -> str:
        """构建分析提示"""
        prompt = f"""
## 市场数据
- 价格: ${market_data.get('close', 0):,.2f}
- RSI: {market_data.get('rsi', 50):.2f}
- MACD Hist: {market_data.get('macd_hist', 0):.4f}
- ADX: {market_data.get('adx', 25):.2f}
- 布林带位置: {market_data.get('bb_position', 0.5):.2%}
- ATR: {market_data.get('atr', 0):.2f}
- 成交量比率: {market_data.get('volume_ratio', 1):.2f}

## 账户信息
- 总资产: ${account_info.get('total_equity', 0):,.2f}
- 可用余额: ${account_info.get('available_balance', 0):,.2f}
- 未实现盈亏: ${account_info.get('unrealized_pnl', 0):,.2f}
"""
        
        if position_info:
            prompt += f"""
## 当前持仓
- 方向: {position_info.get('side', 'NONE')}
- 持仓量: {position_info.get('size', 0)}
- 开仓价: ${position_info.get('entry_price', 0):,.2f}
- 浮盈浮亏: {position_info.get('unrealized_pnl_pct', 0):.2f}%
- 杠杆: {position_info.get('leverage', 1)}x
"""
        else:
            prompt += "\n## 当前持仓\n- 无持仓"
        
        prompt += "\n\n请分析市场并给出交易建议，必须以 JSON 格式返回。"
        
        return prompt
    
    def _print_ensemble_result(self, result: Dict):
        """打印集成决策结果"""
        print("\n" + "=" * 60)
        print("🤝 多模型集成决策结果")
        print("=" * 60)
        
        print(f"\n📊 使用模型数: {result['models_used']}")
        print(f"🎯 共识度: {result['consensus_level'] * 100:.0f}%")
        
        print("\n📦 各模型决策:")
        for i, decision in enumerate(result['individual_decisions'], 1):
            print(f"  {i}. {decision.get('provider', 'Unknown')} ({decision.get('model', 'Unknown')}):")
            print(f"     动作: {decision.get('action', 'HOLD')} | 信心: {decision.get('confidence', 0)}%")
        
        final = result['final_decision']
        print(f"\n✅ 最终决策: {final['action']}")
        print(f"   信心度: {final['confidence']}%")
        print(f"   投票: {final.get('votes', 0)}/{final.get('total_models', 0)}")
        print(f"   杠杆: {final.get('leverage', 1)}x")
        print(f"   理由: {final.get('reasoning', 'N/A')}")
        print("=" * 60)
    
    def _get_default_decision(self) -> Dict:
        """默认决策（API 失败时）"""
        return {
            'action': 'HOLD',
            'confidence': 0,
            'leverage': 1,
            'position_size_usdt': 0,
            'reasoning': 'API 不可用，默认观望',
            'risk_assessment': 'HIGH'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.ensemble.get_stats()
