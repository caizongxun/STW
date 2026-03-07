"""
強健的 JSON 解析器

處理各種模型輸出格式問題：
1. Markdown 代碼塊 (```json ... ```)
2. 多餘的文字說明
3. 單引號與雙引號混用
4. 缺少逗號或大括號
5. 中文出現在 JSON key 中
6. 多個 JSON 物件 (取第一個)
7. 文字和 JSON 混合
8. True/False vs true/false
9. None vs null
10. NaN, Infinity 等非法值
11. AI 輸出被截斷 (部分輸出)
"""
import json
import re
from typing import Dict, Optional, Any


class RobustJSONParser:
    """
    強健的 JSON 解析器
    可以處理各種格式錯誤的模型輸出
    """
    
    @staticmethod
    def clean_json_string(text: str) -> str:
        """清理 JSON 字串"""
        # 1. 移除 Markdown 代碼塊
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # 2. 移除 HTML 標籤
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. 替換 Python 常量為 JSON 格式
        text = text.replace('True', 'true')
        text = text.replace('False', 'false')
        text = text.replace('None', 'null')
        
        # 4. 移除 NaN, Infinity
        text = re.sub(r'\bNaN\b', '0', text)
        text = re.sub(r'\bInfinity\b', '999999', text)
        text = re.sub(r'-Infinity\b', '-999999', text)
        
        return text
    
    @staticmethod
    def extract_json_candidates(text: str) -> list:
        """提取所有可能的 JSON 候選"""
        candidates = []
        
        # 嘗試找到所有 { ... } 結構
        depth = 0
        start = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    candidates.append(text[start:i+1])
                    start = -1
        
        return candidates
    
    @staticmethod
    def fix_common_issues(json_str: str) -> str:
        """修復常見的 JSON 格式問題"""
        # 1. 修復單引號與雙引號混用 (簡單版本)
        # 將 key 名稱的單引號改為雙引號
        json_str = re.sub(r"'([a-zA-Z_][a-zA-Z0-9_]*)'", r'"\1"', json_str)
        
        # 2. 移除尾随逗號 (在大括號前)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 3. 修復缺少逗號的情況 (兩個字串間)
        json_str = re.sub(r'"\s+"', '","', json_str)
        
        # 4. 移除行內註釋
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        
        # 5. 移除多行註釋
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str
    
    @staticmethod
    def parse(text: str, default: Optional[Dict] = None) -> Dict:
        """
        解析 JSON ，如果失敗則返回預設值
        
        Args:
            text: 模型輸出的文字
            default: 解析失敗時的預設值
        
        Returns:
            解析出的 Dict
        """
        if not text or not isinstance(text, str):
            return default or {}
        
        # 清理文字
        text = RobustJSONParser.clean_json_string(text)
        
        # 策略 1: 直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 策略 2: 提取第一個 JSON 候選
        candidates = RobustJSONParser.extract_json_candidates(text)
        
        for candidate in candidates:
            # 2.1: 直接解析
            try:
                return json.loads(candidate)
            except:
                pass
            
            # 2.2: 修復後解析
            try:
                fixed = RobustJSONParser.fix_common_issues(candidate)
                return json.loads(fixed)
            except:
                pass
        
        # 策略 3: 使用正則提取關鍵資訊
        extracted = RobustJSONParser.extract_by_regex(text)
        if extracted:
            return extracted
        
        # 所有策略失敗，返回預設值
        return default or {}
    
    @staticmethod
    def extract_by_regex(text: str) -> Optional[Dict]:
        """
        使用正則表達式提取關鍵資訊
        當 JSON 解析完全失敗時的備用方案
        """
        result = {}
        
        # 提取 action
        action_match = re.search(r'["\']?action["\']?\s*:\s*["\']?(OPEN_LONG|OPEN_SHORT|CLOSE|HOLD)["\']?', text, re.IGNORECASE)
        if action_match:
            result['action'] = action_match.group(1).upper()
        
        # 提取 confidence
        conf_match = re.search(r'["\']?confidence["\']?\s*:\s*(\d+)', text)
        if conf_match:
            result['confidence'] = int(conf_match.group(1))
        
        # 提取 leverage
        lev_match = re.search(r'["\']?leverage["\']?\s*:\s*(\d+)', text)
        if lev_match:
            result['leverage'] = int(lev_match.group(1))
        
        # 提取數字欄位
        for key in ['position_size_usdt', 'entry_price', 'stop_loss', 'take_profit']:
            match = re.search(rf'["\']?{key}["\']?\s*:\s*([\d.]+)', text)
            if match:
                result[key] = float(match.group(1))
        
        # 提取 reasoning
        reasoning_match = re.search(r'["\']?reasoning["\']?\s*:\s*["\']([^"\'}]+)["\']', text)
        if reasoning_match:
            result['reasoning'] = reasoning_match.group(1)
        
        # 提取 risk_assessment
        risk_match = re.search(r'["\']?risk_assessment["\']?\s*:\s*["\']?(LOW|MEDIUM|HIGH)["\']?', text, re.IGNORECASE)
        if risk_match:
            result['risk_assessment'] = risk_match.group(1).upper()
        
        # 提取 is_counter_trend
        counter_match = re.search(r'["\']?is_counter_trend["\']?\s*:\s*(true|false)', text, re.IGNORECASE)
        if counter_match:
            result['is_counter_trend'] = counter_match.group(1).lower() == 'true'
        
        # 如果提取到了主要欄位，則認為成功
        if 'action' in result and 'confidence' in result:
            # 補全缺失的預設值
            result.setdefault('leverage', 1)
            result.setdefault('position_size_usdt', 0)
            result.setdefault('entry_price', 0)
            result.setdefault('stop_loss', 0)
            result.setdefault('take_profit', 0)
            result.setdefault('reasoning', '正則提取的資訊')
            result.setdefault('risk_assessment', 'MEDIUM')
            result.setdefault('is_counter_trend', False)
            return result
        
        return None


def parse_trading_decision(content: str) -> Dict:
    """
    解析交易決策
    適用於所有模型輸出 (Model A/B/Arbitrator/Executor)
    """
    default = {
        'action': 'HOLD',
        'confidence': 30,
        'leverage': 1,
        'position_size_usdt': 0,
        'entry_price': 0,
        'stop_loss': 0,
        'take_profit': 0,
        'reasoning': '解析失敗',
        'risk_assessment': 'HIGH',
        'is_counter_trend': False
    }
    
    result = RobustJSONParser.parse(content, default)
    
    # 確保所有必要欄位存在
    for key, value in default.items():
        result.setdefault(key, value)
    
    # 數值類型檢查和修正
    try:
        result['confidence'] = int(result['confidence'])
        result['leverage'] = int(result['leverage'])
        result['position_size_usdt'] = float(result['position_size_usdt'])
        result['entry_price'] = float(result['entry_price'])
        result['stop_loss'] = float(result['stop_loss'])
        result['take_profit'] = float(result['take_profit'])
    except (ValueError, TypeError):
        pass
    
    # action 正規化
    if isinstance(result['action'], str):
        result['action'] = result['action'].upper()
        if result['action'] not in ['OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'HOLD']:
            result['action'] = 'HOLD'
    
    return result


def parse_executor_review(content: str) -> Dict:
    """
    解析執行審核員的回應
    特別處理 AI 輸出被截斷的情況
    """
    default = {
        'execution_decision': 'REJECT',
        'confidence_adjustment': 0,
        'position_size_ratio': 1.0,
        'reasoning': '解析失敗',
        'risk_factors': ['解析錯誤']
    }
    
    # 策略 1: 標準 JSON 解析
    result = RobustJSONParser.parse(content, None)
    
    if result is None or 'execution_decision' not in result:
        # 策略 2: 智能推斷 (部分輸出)
        result = infer_executor_decision_from_partial(content)
    
    # 補全預設值
    for key, value in default.items():
        result.setdefault(key, value)
    
    # 類型修正
    try:
        result['confidence_adjustment'] = int(result.get('confidence_adjustment', 0))
        result['position_size_ratio'] = float(result.get('position_size_ratio', 1.0))
    except (ValueError, TypeError):
        pass
    
    # execution_decision 正規化
    if isinstance(result['execution_decision'], str):
        result['execution_decision'] = result['execution_decision'].upper()
        if result['execution_decision'] not in ['EXECUTE', 'REJECT', 'REDUCE_SIZE']:
            result['execution_decision'] = 'REJECT'
    
    return result


def infer_executor_decision_from_partial(content: str) -> Dict:
    """
    從部分輸出中推斷 Executor 的決策
    當 AI 輸出被截斷時使用
    """
    content_lower = content.lower()
    result = {}
    
    # 1. 提取信心度
    conf_match = re.search(r'信心度[:：]?\s*(\d+)%', content)
    if conf_match:
        confidence = int(conf_match.group(1))
    else:
        confidence = None
    
    # 2. 檢查關鍵詞來推斷決策
    positive_keywords = ['符合執行', '可以執行', '建議執行', '通過審核', '同意執行']
    negative_keywords = ['不建議執行', '拒絕執行', '不符合', '風險過大', '不通過']
    caution_keywords = ['謹慎執行', '減少倉位', '降低杆杆', '小倉位']
    
    has_positive = any(kw in content for kw in positive_keywords)
    has_negative = any(kw in content for kw in negative_keywords)
    has_caution = any(kw in content for kw in caution_keywords)
    
    # 3. 根據關鍵詞和信心度決定
    if has_negative:
        result['execution_decision'] = 'REJECT'
        result['reasoning'] = '審核員拒絕執行 (從部分輸出推斷)'
    elif has_caution:
        result['execution_decision'] = 'REDUCE_SIZE'
        result['position_size_ratio'] = 0.5
        result['reasoning'] = '審核員建議減少倉位 (從部分輸出推斷)'
    elif has_positive and confidence and confidence >= 60:
        result['execution_decision'] = 'EXECUTE'
        result['reasoning'] = f'審核員同意執行，信心度 {confidence}% (從部分輸出推斷)'
    elif confidence:
        # 有信心度但沒有明確關鍵詞
        if confidence >= 70:
            result['execution_decision'] = 'EXECUTE'
            result['reasoning'] = f'信心度達標 {confidence}% (從部分輸出推斷)'
        elif confidence >= 50:
            result['execution_decision'] = 'REDUCE_SIZE'
            result['position_size_ratio'] = 0.5
            result['reasoning'] = f'信心度中等 {confidence}%，減少倉位 (從部分輸出推斷)'
        else:
            result['execution_decision'] = 'REJECT'
            result['reasoning'] = f'信心度不足 {confidence}% (從部分輸出推斷)'
    else:
        # 無法判斷，預設拒絕
        result['execution_decision'] = 'REJECT'
        result['reasoning'] = 'AI 輸出不完整，無法判斷，預設拒絕'
    
    return result
