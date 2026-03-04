"""
加密貨幣新聞獲取器
從公開API獲取最新新聞並進行情緒分析
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time


class CryptoNewsFetcher:
    """獲取和分析加密貨幣新聞"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: CryptoPanic API token (免費版本可用)
                      申請地址: https://cryptopanic.com/developers/api/
        """
        self.api_token = api_token
        self.base_url = "https://cryptopanic.com/api/free/v1/posts/"
        
        # 情緒關鍵字
        self.positive_keywords = [
            'rally', 'bullish', 'surge', 'breakout', 'adoption', 'partnership',
            'upgrade', 'launch', 'bull', 'gains', 'up', 'rise', 'growth',
            'institutional', 'approval', 'accepted', 'integration', 'positive'
        ]
        
        self.negative_keywords = [
            'crash', 'bearish', 'dump', 'regulation', 'hack', 'scam', 'fraud',
            'ban', 'decline', 'down', 'fall', 'loss', 'lawsuit', 'investigation',
            'warning', 'risk', 'concern', 'negative', 'sec', 'fine'
        ]
    
    def fetch_recent_news(self, symbol: str = 'BTC', hours: int = 24, limit: int = 20) -> List[Dict]:
        """
        獲取最近N小時的新聞
        
        Args:
            symbol: 幣種 (BTC/ETH/BNB...)
            hours: 時間範圍 (小時)
            limit: 最大返回數量
        
        Returns:
            新聞列表
        """
        news = []
        
        try:
            # CryptoPanic API (不需token也可以用免費版)
            params = {
                'currencies': symbol,
                'public': 'true',
                'kind': 'news'  # 只要新聞，不要社區討論
            }
            
            if self.api_token:
                params['auth_token'] = self.api_token
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for item in results[:limit]:
                published_at = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                
                # 只保留指定時間範圍內的新聞
                if published_at < cutoff_time:
                    continue
                
                news.append({
                    'time': item['published_at'],
                    'title': item['title'],
                    'url': item['url'],
                    'source': item.get('source', {}).get('title', 'Unknown'),
                    'votes': item.get('votes', {}),
                    'sentiment_score': self._calculate_sentiment(item['title'])
                })
            
            print(f"Fetched {len(news)} news articles for {symbol} in last {hours} hours")
            return news
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch news: {e}")
            return []
        except Exception as e:
            print(f"Error processing news: {e}")
            return []
    
    def _calculate_sentiment(self, text: str) -> int:
        """
        計算單條新聞的情緒分數
        
        Args:
            text: 新聞標題
        
        Returns:
            分數 (-N 至 +N)
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in self.positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in self.negative_keywords if kw in text_lower)
        
        return positive_count - negative_count
    
    def analyze_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        分析多條新聞的整體情緒
        
        Args:
            news_list: 由 fetch_recent_news() 返回的新聞列表
        
        Returns:
            情緒分析結果
        """
        if not news_list:
            return {
                'total_score': 0,
                'sentiment': 'neutral',
                'news_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'confidence': 0
            }
        
        total_score = sum(item['sentiment_score'] for item in news_list)
        positive_count = sum(1 for item in news_list if item['sentiment_score'] > 0)
        negative_count = sum(1 for item in news_list if item['sentiment_score'] < 0)
        neutral_count = len(news_list) - positive_count - negative_count
        
        # 決定整體情緒
        avg_score = total_score / len(news_list)
        
        if avg_score > 0.5:
            sentiment = 'bullish'
        elif avg_score < -0.5:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        # 信心度 (基於新聞數量和一致性)
        confidence = min(len(news_list) * 5, 100)  # 更多新聞 = 更高信心
        
        return {
            'total_score': total_score,
            'avg_score': round(avg_score, 2),
            'sentiment': sentiment,
            'news_count': len(news_list),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'confidence': confidence
        }
    
    def get_top_headlines(self, news_list: List[Dict], count: int = 5) -> List[Dict]:
        """
        獲取最重要的新聞標題
        
        Args:
            news_list: 新聞列表
            count: 返回數量
        
        Returns:
            按重要性排序的新聞
        """
        # 按情緒分數的絕對值排序 (極端情緒更重要)
        sorted_news = sorted(news_list, key=lambda x: abs(x['sentiment_score']), reverse=True)
        return sorted_news[:count]
    
    def format_news_for_ai(self, symbol: str, hours: int = 24) -> str:
        """
        格式化新聞為AI可讀的文字
        
        Args:
            symbol: 幣種
            hours: 時間範圍
        
        Returns:
            格式化後的文字
        """
        news = self.fetch_recent_news(symbol, hours=hours)
        
        if not news:
            return f"No recent news for {symbol} in the last {hours} hours."
        
        sentiment = self.analyze_sentiment(news)
        top_headlines = self.get_top_headlines(news, count=5)
        
        output = f"""News Analysis for {symbol} (Last {hours} hours)

Overall Sentiment: {sentiment['sentiment'].upper()}
Total News: {sentiment['news_count']}
Sentiment Score: {sentiment['total_score']} (Avg: {sentiment['avg_score']})
Breakdown: {sentiment['positive_count']} positive, {sentiment['negative_count']} negative, {sentiment['neutral_count']} neutral

Top Headlines:
"""
        
        for idx, item in enumerate(top_headlines, 1):
            sentiment_label = 'BULLISH' if item['sentiment_score'] > 0 else 'BEARISH' if item['sentiment_score'] < 0 else 'NEUTRAL'
            output += f"{idx}. [{sentiment_label}] {item['title']}\n"
            output += f"   Source: {item['source']} | Time: {item['time']}\n"
        
        return output
    
    def get_news_context_for_trading(self, symbol: str) -> Dict:
        """
        獲取給交易決策使用的新聞上下文
        
        Args:
            symbol: 幣種
        
        Returns:
            新聞上下文字典
        """
        # 獲取24小時的新聞
        news = self.fetch_recent_news(symbol, hours=24)
        sentiment = self.analyze_sentiment(news)
        top_headlines = self.get_top_headlines(news, count=3)
        
        return {
            'has_news': len(news) > 0,
            'sentiment': sentiment['sentiment'],
            'sentiment_score': sentiment['total_score'],
            'news_count': sentiment['news_count'],
            'top_headlines': [item['title'] for item in top_headlines],
            'recommendation': self._get_news_recommendation(sentiment)
        }
    
    def _get_news_recommendation(self, sentiment: Dict) -> str:
        """根據新聞情緒給出建議"""
        if sentiment['news_count'] < 3:
            return "Insufficient news data for reliable assessment"
        
        if sentiment['sentiment'] == 'bullish' and sentiment['total_score'] > 5:
            return "Strong positive news momentum - Consider LONG bias"
        elif sentiment['sentiment'] == 'bearish' and sentiment['total_score'] < -5:
            return "Strong negative news sentiment - Consider SHORT bias or avoid trading"
        elif sentiment['negative_count'] > sentiment['positive_count'] * 2:
            return "High negative news ratio - Exercise caution"
        else:
            return "Mixed or neutral news sentiment - Rely more on technical analysis"


class NewsAwareTrading:
    """整合新聞到交易決策的工具類"""
    
    def __init__(self, news_fetcher: CryptoNewsFetcher):
        self.news_fetcher = news_fetcher
    
    def should_trade_based_on_news(self, symbol: str, technical_signal: str) -> tuple[bool, str]:
        """
        根據新聞判斷是否應該交易
        
        Args:
            symbol: 幣種
            technical_signal: 'LONG' / 'SHORT' / 'HOLD'
        
        Returns:
            (should_trade, reason)
        """
        news_context = self.news_fetcher.get_news_context_for_trading(symbol)
        
        if not news_context['has_news']:
            return True, "No significant news, proceed with technical signal"
        
        sentiment = news_context['sentiment']
        score = news_context['sentiment_score']
        
        # 新聞與技術共振
        if technical_signal == 'LONG' and sentiment == 'bullish':
            return True, "Technical and news sentiment aligned (BULLISH)"
        
        if technical_signal == 'SHORT' and sentiment == 'bearish':
            return True, "Technical and news sentiment aligned (BEARISH)"
        
        # 新聞與技術矛盾
        if technical_signal == 'LONG' and sentiment == 'bearish' and score < -8:
            return False, "Strong negative news contradicts LONG signal - AVOID"
        
        if technical_signal == 'SHORT' and sentiment == 'bullish' and score > 8:
            return False, "Strong positive news contradicts SHORT signal - AVOID"
        
        # 中性情況
        return True, "News sentiment is neutral or weak, proceed with caution"
    
    def adjust_confidence_with_news(self, base_confidence: float, symbol: str) -> float:
        """
        用新聞情緒調整AI信心度
        
        Args:
            base_confidence: AI原始信心度 (0-100)
            symbol: 幣種
        
        Returns:
            調整後的信心度
        """
        news_context = self.news_fetcher.get_news_context_for_trading(symbol)
        
        if not news_context['has_news']:
            return base_confidence
        
        sentiment = news_context['sentiment']
        score = news_context['sentiment_score']
        
        # 正面新聞增加信心
        if sentiment == 'bullish' and score > 5:
            return min(base_confidence + 10, 100)
        
        # 負面新聞降低信心
        if sentiment == 'bearish' and score < -5:
            return max(base_confidence - 15, 0)
        
        return base_confidence
