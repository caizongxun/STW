"""
JSON 解析器測試

測試各種模型輸出格式問題：
1. Markdown 代碼塊
2. 單引號與雙引號混用
3. 多餘的文字說明
4. True/False vs true/false
5. 正則提取備用
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.json_parser_robust import parse_trading_decision, parse_executor_review


def test_case_1_markdown_code_block():
    """測試1: Markdown 代碼塊"""
    content = """```json
{
  "action": "OPEN_LONG",
  "confidence": 75,
  "leverage": 3,
  "position_size_usdt": 1000,
  "entry_price": 67800,
  "stop_loss": 67000,
  "take_profit": 69000,
  "reasoning": "BTC 失敗線超賣反彈",
  "risk_assessment": "MEDIUM"
}
```"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試1: Markdown 代碼塊 ===")
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Reasoning: {result['reasoning']}")
    assert result['action'] == 'OPEN_LONG', "Failed: action"
    assert result['confidence'] == 75, "Failed: confidence"
    print("\u2705 通過")


def test_case_2_single_quotes():
    """測試2: 單引號"""
    content = """{
  'action': 'OPEN_SHORT',
  'confidence': 68,
  'leverage': 2,
  'position_size_usdt': 800,
  'entry_price': 67900,
  'stop_loss': 68500,
  'take_profit': 66800,
  'reasoning': '阻力位反轉',
  'risk_assessment': 'LOW'
}"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試2: 單引號 ===")
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']}%")
    assert result['action'] == 'OPEN_SHORT', "Failed: action"
    assert result['confidence'] == 68, "Failed: confidence"
    print("\u2705 通過")


def test_case_3_mixed_text():
    """測試3: 混合文字和 JSON"""
    content = """根據當前市場狀況分析，我建議：

{
  "action": "HOLD",
  "confidence": 55,
  "leverage": 1,
  "position_size_usdt": 0,
  "entry_price": 0,
  "stop_loss": 0,
  "take_profit": 0,
  "reasoning": "市場方向不明確，等待更好機會",
  "risk_assessment": "MEDIUM"
}

以上是我的分析。"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試3: 混合文字和 JSON ===")
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']}%")
    assert result['action'] == 'HOLD', "Failed: action"
    print("\u2705 通過")


def test_case_4_python_style():
    """測試4: Python 風格 (True/False/None)"""
    content = """{
  "action": "CLOSE",
  "confidence": 80,
  "leverage": 1,
  "position_size_usdt": 500,
  "entry_price": 68000,
  "stop_loss": 0,
  "take_profit": 0,
  "reasoning": "止盈出場",
  "risk_assessment": "LOW",
  "is_counter_trend": False
}"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試4: Python 風格 ===")
    print(f"Action: {result['action']}")
    print(f"Counter Trend: {result['is_counter_trend']}")
    assert result['action'] == 'CLOSE', "Failed: action"
    assert result['is_counter_trend'] == False, "Failed: is_counter_trend"
    print("\u2705 通過")


def test_case_5_regex_fallback():
    """測試5: 完全錯誤的 JSON，使用正則提取"""
    content = """我認為應該 action: OPEN_LONG, confidence: 72, 因為市場出現反彈訊號。
leverage: 2, position_size_usdt: 900, entry_price: 67850
stop_loss: 67200, take_profit: 68800
reasoning: 技術指標超賣反彈
risk_assessment: MEDIUM"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試5: 正則提取備用 ===")
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']}%")
    assert result['action'] == 'OPEN_LONG', "Failed: action"
    assert result['confidence'] == 72, "Failed: confidence"
    print("\u2705 通過 (使用正則提取)")


def test_case_6_executor_review():
    """測試6: 執行審核員回應"""
    content = """```json
{
  "execution_decision": "REDUCE_SIZE",
  "confidence_adjustment": -10,
  "position_size_ratio": 0.5,
  "reasoning": "信心度中等，市場波動較大",
  "risk_factors": ["波動性高", "信心度不足"]
}
```"""
    
    result = parse_executor_review(content)
    print("\n=== 測試6: 執行審核員回應 ===")
    print(f"Decision: {result['execution_decision']}")
    print(f"Size Ratio: {result['position_size_ratio']}")
    assert result['execution_decision'] == 'REDUCE_SIZE', "Failed: execution_decision"
    assert result['position_size_ratio'] == 0.5, "Failed: position_size_ratio"
    print("\u2705 通過")


def test_case_7_completely_broken():
    """測試7: 完全無法解析的內容"""
    content = """這是一段完全無法解析的文字，沒有任何 JSON 資訊。"""
    
    result = parse_trading_decision(content)
    print("\n=== 測試7: 完全無法解析 ===")
    print(f"Action: {result['action']} (應該是 HOLD)")
    print(f"Confidence: {result['confidence']}% (應該是 30)")
    assert result['action'] == 'HOLD', "Failed: should default to HOLD"
    assert result['confidence'] == 30, "Failed: should default to 30"
    print("\u2705 通過 (使用預設值)")


if __name__ == '__main__':
    print("\n" + "="*70)
    print(" JSON 解析器測試")
    print("="*70)
    
    try:
        test_case_1_markdown_code_block()
        test_case_2_single_quotes()
        test_case_3_mixed_text()
        test_case_4_python_style()
        test_case_5_regex_fallback()
        test_case_6_executor_review()
        test_case_7_completely_broken()
        
        print("\n" + "="*70)
        print("\u2705 所有測試通過!")
        print("="*70 + "\n")
    except AssertionError as e:
        print(f"\n\u274c 測試失敗: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\u274c 異常發生: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
