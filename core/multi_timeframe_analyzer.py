"""
多時間框架分析器
負責獲取並處理 15m, 1h, 4h 的市場數據
讓 AI 可以看清大趨勢，同時允許高信心度逆勢操作
"""
import pandas as pd
from typing import Dict, List, Optional
from strategies.v13.market_features import prepare_market_features


class MultiTimeframeAnalyzer:
    """
    多時間框架分析器
    
    主時間框架：15m (進出場時機)
    輔助時間框架：1h, 4h (大趨勢判斷)
    """
    
    def __init__(self, data_loader):
        """
        Args:
            data_loader: RealtimeDataLoader 實例
        """
        self.data_loader = data_loader
    
    def prepare_multi_timeframe_data(
        self,
        symbol: str,
        primary_timeframe: str = '15m',
        secondary_timeframes: List[str] = ['1h', '4h'],
        num_candles: int = 20
    ) -> Dict:
        """
        準備多時間框架數據
        
        Args:
            symbol: 交易對 (e.g., 'BTCUSDT')
            primary_timeframe: 主時間框架 (e.g., '15m')
            secondary_timeframes: 輔助時間框架 (e.g., ['1h', '4h'])
            num_candles: 每個時間框架要取的 K 棒數量
        
        Returns:
            {
                '15m': {'current': {...}, 'candles': [...]},
                '1h': {'current': {...}, 'candles': [...]},
                '4h': {'current': {...}, 'candles': [...]}
            }
        """
        result = {}
        
        # 處理主時間框架
        primary_df = self.data_loader.load_data(symbol, primary_timeframe)
        if primary_df is not None and len(primary_df) >= 200:
            result[primary_timeframe] = self._process_timeframe_data(
                primary_df,
                primary_timeframe,
                num_candles
            )
        
        # 處理輔助時間框架
        for tf in secondary_timeframes:
            try:
                df = self.data_loader.load_data(symbol, tf)
                if df is not None and len(df) >= 200:
                    result[tf] = self._process_timeframe_data(
                        df,
                        tf,
                        num_candles
                    )
            except Exception as e:
                print(f"⚠️ 無法載入 {tf} 數據: {e}")
        
        return result
    
    def _process_timeframe_data(
        self,
        df: pd.DataFrame,
        timeframe: str,
        num_candles: int
    ) -> Dict:
        """
        處理單一時間框架的數據
        
        Returns:
            {
                'timeframe': '1h',
                'current': {...},  # 當前 K 棒的所有指標
                'candles': [...],  # 前 N 根 K 棒的所有指標
                'trend': 'UP' | 'DOWN' | 'SIDEWAYS',
                'strength': 0-100
            }
        """
        # 當前 K 棒的完整指標
        current_candle = df.iloc[-1]
        current_features = prepare_market_features(current_candle, df)
        
        # 歷史 K 棒
        candles = []
        for i in range(-num_candles, 0):
            df_slice = df.iloc[:len(df) + i + 1].copy()
            row = df.iloc[i]
            features = prepare_market_features(row, df_slice)
            
            candles.append({
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'features': features
            })
        
        # 判斷趨勢和強度
        trend_info = self._analyze_trend(df, current_features)
        
        return {
            'timeframe': timeframe,
            'current': current_features,
            'candles': candles,
            'trend': trend_info['trend'],
            'strength': trend_info['strength'],
            'summary': trend_info['summary']
        }
    
    def _analyze_trend(self, df: pd.DataFrame, features: Dict) -> Dict:
        """
        分析趨勢方向和強度
        
        Returns:
            {
                'trend': 'UP' | 'DOWN' | 'SIDEWAYS',
                'strength': 0-100,
                'summary': '文字描述'
            }
        """
        close = features.get('close', 0)
        ema9 = features.get('ema9', close)
        ema21 = features.get('ema21', close)
        ema50 = features.get('ema50', close)
        ema200 = features.get('ema200', close)
        adx = features.get('adx', 0)
        rsi = features.get('rsi', 50)
        macd_hist = features.get('macd_hist', 0)
        
        # 判斷趨勢方向
        if close > ema9 > ema21 > ema50:
            trend = 'UP'
            strength = min(adx * 1.5, 100)
        elif close < ema9 < ema21 < ema50:
            trend = 'DOWN'
            strength = min(adx * 1.5, 100)
        else:
            trend = 'SIDEWAYS'
            strength = max(25 - adx, 0)
        
        # 生成摘要
        if trend == 'UP':
            if strength > 60:
                summary = f"強勁上升趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
            elif strength > 40:
                summary = f"温和上升趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
            else:
                summary = f"弱上升趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
        elif trend == 'DOWN':
            if strength > 60:
                summary = f"強勁下跌趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
            elif strength > 40:
                summary = f"温和下跌趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
            else:
                summary = f"弱下跌趨勢 (ADX={adx:.1f}, RSI={rsi:.1f})"
        else:
            summary = f"盤整中 (ADX={adx:.1f}, RSI={rsi:.1f})"
        
        return {
            'trend': trend,
            'strength': strength,
            'summary': summary
        }
    
    def get_counter_trend_signal(self, multi_tf_data: Dict) -> Dict:
        """
        判斷是否有高信心度逆勢操作機會
        
        條件：
        1. 15m 超賣/超買 (RSI<30 or RSI>70)
        2. 1h 趨勢明確且強勁
        3. 1h 和 15m 趨勢相反
        4. 4h 也支持 1h 趨勢
        
        Returns:
            {
                'has_signal': True/False,
                'direction': 'LONG' | 'SHORT' | None,
                'confidence': 0-100,
                'reasoning': '文字說明'
            }
        """
        if '15m' not in multi_tf_data or '1h' not in multi_tf_data:
            return {'has_signal': False, 'direction': None, 'confidence': 0, 'reasoning': '缺少數據'}
        
        tf_15m = multi_tf_data['15m']
        tf_1h = multi_tf_data['1h']
        tf_4h = multi_tf_data.get('4h')
        
        current_15m = tf_15m['current']
        current_1h = tf_1h['current']
        
        rsi_15m = current_15m.get('rsi', 50)
        trend_1h = tf_1h['trend']
        strength_1h = tf_1h['strength']
        
        # 檢查逆勢條件
        is_oversold_15m = rsi_15m < 30
        is_overbought_15m = rsi_15m > 70
        is_strong_trend_1h = strength_1h > 50
        
        # 情境 1：15m 超賣 + 1h 上升趨勢 = 做多機會
        if is_oversold_15m and trend_1h == 'UP' and is_strong_trend_1h:
            confidence = min(70 + (strength_1h - 50) / 2, 90)
            reasoning = f"15m 超賣 (RSI={rsi_15m:.1f}) + 1h 強勁上升 (強度={strength_1h:.1f}) = 高信心做多"
            
            # 如果 4h 也是上升，信心度 +5
            if tf_4h and tf_4h['trend'] == 'UP':
                confidence += 5
                reasoning += f" (4h 也是上升)"
            
            return {
                'has_signal': True,
                'direction': 'LONG',
                'confidence': confidence,
                'reasoning': reasoning
            }
        
        # 情境 2：15m 超買 + 1h 下跌趨勢 = 做空機會
        if is_overbought_15m and trend_1h == 'DOWN' and is_strong_trend_1h:
            confidence = min(70 + (strength_1h - 50) / 2, 90)
            reasoning = f"15m 超買 (RSI={rsi_15m:.1f}) + 1h 強勁下跌 (強度={strength_1h:.1f}) = 高信心做空"
            
            # 如果 4h 也是下跌，信心度 +5
            if tf_4h and tf_4h['trend'] == 'DOWN':
                confidence += 5
                reasoning += f" (4h 也是下跌)"
            
            return {
                'has_signal': True,
                'direction': 'SHORT',
                'confidence': confidence,
                'reasoning': reasoning
            }
        
        return {
            'has_signal': False,
            'direction': None,
            'confidence': 0,
            'reasoning': '無明顯逆勢機會'
        }
