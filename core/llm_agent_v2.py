"""
V2 增強版 DeepSeek-R1 交易引擎
整合倉位管理、新聞分析、K棒序列比對
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from langchain_ollama import OllamaLLM
import pandas as pd

from core.market_analyzer import MarketAnalyzer
from core.portfolio_manager import PortfolioManager
from core.news_fetcher import CryptoNewsFetcher, NewsAwareTrading


class EnhancedDeepSeekAgentV2:
    """
    全功能AI交易引擎
    - K棒序列比對
    - 倉位管理
    - 新聞情緒分析
    - 案例學習
    """
    
    def __init__(
        self,
        model_name: str = "deepseek-r1:14b",
        cases_path: str = "data/detailed_success_cases.json",
        portfolio_manager: Optional[PortfolioManager] = None,
        news_fetcher: Optional[CryptoNewsFetcher] = None,
        enable_news: bool = True
    ):
        self.model = OllamaLLM(
            model=model_name,
            temperature=0.1,
            num_predict=2048
        )
        
        self.cases_path = Path(cases_path)
        self.success_cases = self._load_cases()
        
        self.market_analyzer = MarketAnalyzer(
            use_completed_candles_only=True,
            lookback_bars=5
        )
        
        self.portfolio_manager = portfolio_manager or PortfolioManager()
        
        self.enable_news = enable_news
        if enable_news:
            self.news_fetcher = news_fetcher or CryptoNewsFetcher()
            self.news_trading = NewsAwareTrading(self.news_fetcher)
        else:
            self.news_fetcher = None
            self.news_trading = None
    
    def _load_cases(self) -> List[Dict]:
        """Load learning cases"""
        if not self.cases_path.exists():
            return []
        
        try:
            with open(self.cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cases = data.get('cases', [])
                print(f"Loaded {len(cases)} learning cases")
                return cases
        except Exception as e:
            print(f"Failed to load cases: {e}")
            return []
    
    def analyze_market(
        self,
        df: pd.DataFrame,
        symbol: str,
        current_prices: Optional[Dict[str, float]] = None,
        max_cases: int = 5
    ) -> Dict:
        """
        分析市場並給出交易決策
        
        Args:
            df: 完整歷史K線數據
            symbol: 交易對
            current_prices: 當前價格字典 (for portfolio PnL calculation)
            max_cases: 最多注入多少個案例
        
        Returns:
            交易決策
        """
        try:
            # 1. 提取市場特徵 (包含K棒序列)
            market_features = self.market_analyzer.prepare_market_features(df, symbol)
            
            # 2. 檢查市場是否適合交易
            is_suitable, reason = self.market_analyzer.is_market_suitable_for_trading(market_features)
            if not is_suitable:
                return {
                    'signal': 'HOLD',
                    'confidence': 0,
                    'reasoning': reason,
                    'entry_price': market_features['current_candle']['close'],
                    'stop_loss': 0,
                    'take_profit': 0
                }
            
            # 3. 獲取倉位上下文
            portfolio_context = self.portfolio_manager.get_current_context(current_prices)
            
            # 4. 獲取新聞上下文
            news_context = None
            if self.enable_news:
                news_symbol = symbol.replace('USDT', '')
                news_context = self.news_fetcher.get_news_context_for_trading(news_symbol)
            
            # 5. 匹配相似案例
            similar_cases = self._find_similar_cases(market_features, max_cases)
            
            # 6. 構建強化Prompt
            prompt = self._build_comprehensive_prompt(
                market_features,
                portfolio_context,
                news_context,
                similar_cases
            )
            
            # 7. 調用DeepSeek
            response = self.model.invoke(prompt)
            
            # 8. 解析回答
            decision = self._parse_response(response)
            decision['matched_cases'] = [c['trade_id'] for c in similar_cases]
            decision['reasoning'] = response
            decision['market_suitable'] = is_suitable
            
            # 9. 用新聞調整信心度
            if self.enable_news and news_context:
                original_confidence = decision['confidence']
                decision['confidence'] = self.news_trading.adjust_confidence_with_news(
                    original_confidence,
                    news_symbol
                )
                decision['news_adjusted'] = decision['confidence'] != original_confidence
            
            return decision
            
        except Exception as e:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'entry_price': df.iloc[-1]['close'],
                'stop_loss': 0,
                'take_profit': 0,
                'reasoning': f"Analysis failed: {str(e)}",
                'error': str(e)
            }
    
    def _find_similar_cases(self, market_features: Dict, max_cases: int) -> List[Dict]:
        """Find similar success cases based on current market"""
        if not self.success_cases:
            return []
        
        current = market_features['current_candle']
        similarities = []
        
        for case in self.success_cases:
            entry_candle = next((c for c in case['candles'] if c['position'] == 'entry'), None)
            if not entry_candle:
                continue
            
            case_indicators = entry_candle['indicators']
            
            # Calculate similarity score
            score = 0
            weights = {
                'rsi': 2.0,
                'bb_position': 2.0,
                'volume_ratio': 1.5,
                'macd_hist': 1.5,
                'adx': 1.0
            }
            
            for key, weight in weights.items():
                current_val = current.get(key, 0)
                case_val = case_indicators.get(key, 0)
                
                if current_val == 0 and case_val == 0:
                    continue
                
                # Normalized difference
                if key == 'rsi':
                    diff = abs(current_val - case_val) / 100.0
                elif key == 'bb_position':
                    diff = abs(current_val - case_val)
                elif key == 'volume_ratio':
                    diff = abs(current_val - case_val) / max(current_val, case_val, 1.0)
                elif key == 'macd_hist':
                    diff = min(abs(current_val - case_val) * 100, 1.0)
                elif key == 'adx':
                    diff = abs(current_val - case_val) / 100.0
                else:
                    diff = 0
                
                score += weight * (1 - diff)
            
            similarities.append({
                'case': case,
                'score': score
            })
        
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return [s['case'] for s in similarities[:max_cases]]
    
    def _build_comprehensive_prompt(
        self,
        market_features: Dict,
        portfolio_context: Dict,
        news_context: Optional[Dict],
        similar_cases: List[Dict]
    ) -> str:
        """Build comprehensive prompt with all context"""
        
        prompt = "You are a professional cryptocurrency quantitative trader.\n\n"
        
        # Portfolio Context
        prompt += "=== PORTFOLIO STATUS ===\n"
        prompt += f"Available Capital: ${portfolio_context['available_capital']:,.2f}\n"
        prompt += f"Total Equity: ${portfolio_context['total_equity']:,.2f}\n"
        prompt += f"Capital Usage: {portfolio_context['capital_usage_pct']:.1f}%\n"
        prompt += f"Active Positions: {portfolio_context['active_positions']}\n"
        
        if portfolio_context['positions_detail']:
            prompt += "\nCurrent Positions:\n"
            for pos in portfolio_context['positions_detail']:
                prompt += f"  - {pos['symbol']} {pos['side']}: Entry=${pos['entry_price']:,.2f}, PnL={pos['current_pnl_pct']:+.2f}%, Days={pos['days_holding']}\n"
        
        if portfolio_context['recent_trades']:
            prompt += "\nLast 5 Trades:\n"
            for trade in portfolio_context['recent_trades'][-5:]:
                prompt += f"  - {trade['symbol']} {trade['direction']}: {trade['outcome'].upper()} {trade['pnl_pct']:+.2f}%\n"
        
        stats = portfolio_context['statistics']
        prompt += f"\nPerformance: Win Rate={stats['winning_trades']}/{stats['total_trades']}, "
        prompt += f"Consecutive Losses={stats['consecutive_losses']}\n\n"
        
        # News Context
        if news_context and news_context['has_news']:
            prompt += "=== NEWS SENTIMENT ===\n"
            prompt += f"Overall Sentiment: {news_context['sentiment'].upper()}\n"
            prompt += f"News Count: {news_context['news_count']}\n"
            prompt += f"Recommendation: {news_context['recommendation']}\n"
            if news_context['top_headlines']:
                prompt += "Top Headlines:\n"
                for idx, headline in enumerate(news_context['top_headlines'], 1):
                    prompt += f"  {idx}. {headline}\n"
            prompt += "\n"
        
        # Similar Success Cases
        if similar_cases:
            prompt += f"=== {len(similar_cases)} SIMILAR SUCCESS CASES ===\n"
            for idx, case in enumerate(similar_cases, 1):
                prompt += f"\nCase {idx}: {case['symbol']} {case['direction']} {case['outcome']}\n"
                prompt += f"Entry Time: {case['entry_time']}\n"
                prompt += f"Entry: ${case['entry_price']:,.2f} -> Exit: ${case['exit_price']:,.2f}\n"
                prompt += f"Holding: {case['holding_bars']} bars\n"
                prompt += f"Entry Logic: {case['entry_logic']}\n"
                
                if case.get('indicator_trends'):
                    prompt += "Indicator Trends:\n"
                    for indicator, trend_data in case['indicator_trends'].items():
                        values_str = ' -> '.join([str(v) for v in trend_data['values']])
                        prompt += f"  - {indicator}: [{values_str}] ({trend_data['trend']})\n"
            prompt += "\n"
        
        # Current Market
        prompt += "=== CURRENT MARKET ===\n"
        prompt += self.market_analyzer.format_for_ai_prompt(market_features)
        prompt += "\n"
        
        # Decision Requirements
        prompt += """=== DECISION REQUIREMENTS ===

Analyze the current market by comparing:
1. Current candle sequence vs similar success cases
2. Indicator trends (rising/falling/flat) similarity
3. Portfolio capacity and risk management rules
4. News sentiment alignment with technical signals

Trading Rules:
- Only open position if confidence > 70% AND similar to success cases
- If capital usage > 80%, must be HIGH confidence (>85%)
- If consecutive losses >= 3, do NOT open new positions
- Stop loss must be based on ATR
- Risk:Reward ratio must be at least 1:2
- Consider news sentiment: avoid trades contradicting strong news

IMPORTANT: Respond ONLY with numeric values (no calculations):
```json
{
  "signal": "LONG" | "SHORT" | "HOLD",
  "confidence": 0-100,
  "entry_price": <number only>,
  "stop_loss": <number only>,
  "take_profit": <number only>,
  "position_size_pct": <number only>,
  "reasoning": "<concise explanation>",
  "key_risks": ["<risk 1>", "<risk 2>"]
}
```
"""
        
        return prompt
    
    def _clean_json_math(self, text: str) -> str:
        """
        清理 JSON 中的數學計算式
        例: "stop_loss": 65505.24 - 284.12 = 65221.12
        提取為: "stop_loss": 65221.12
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 檢查是否包含計算式 (=)
            if '=' in line and any(field in line for field in ['stop_loss', 'take_profit', 'entry_price']):
                # 提取 = 後的數字
                match = re.search(r'=\s*([\d.]+)', line)
                if match:
                    result_value = match.group(1)
                    field_match = re.search(r'"(\w+)"\s*:', line)
                    if field_match:
                        field_name = field_match.group(1)
                        has_comma = line.rstrip().endswith(',')
                        new_line = f'  "{field_name}": {result_value}'
                        if has_comma:
                            new_line += ','
                        cleaned_lines.append(new_line)
                        continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _parse_response(self, response: str) -> Dict:
        """Parse DeepSeek JSON response with math expression cleaning"""
        try:
            # 步驟1: 清理計算式
            response = self._clean_json_math(response)
            
            # 步驟2: 多重 null 替換
            response = re.sub(r'\s+', ' ', response)
            response = re.sub(r'\bnull\b', '0.0', response, flags=re.IGNORECASE)
            response = re.sub(r':\s*null', ': 0.0', response, flags=re.IGNORECASE)
            response = response.replace('null', '0.0')
            
            # 步驟3: 提取JSON
            json_match = re.search(r'\{[\s\S]*?\}', response)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response.strip()
            
            # 步驟4: 解析
            decision = json.loads(json_str)
            
            # 步驟5: 安全轉型
            for field in ['confidence', 'entry_price', 'stop_loss', 'take_profit']:
                val = decision.get(field)
                decision[field] = float(val) if val is not None else 0.0
            
            decision['signal'] = decision.get('signal', 'HOLD').upper()
            if decision['signal'] not in ['LONG', 'SHORT', 'HOLD']:
                decision['signal'] = 'HOLD'
            
            return decision
            
        except Exception as e:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'entry_price': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'reasoning': f'JSON解析失敗: {str(e)}',
                'error': str(e)
            }
    
    def reload_cases(self):
        """Reload learning cases (after adding new ones)"""
        self.success_cases = self._load_cases()
