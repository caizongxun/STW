"""
市場分析器
提取K棒序列特徵，只使用已完成的K棒進行判斷
"""
import pandas as pd
import numpy as np
import talib
from typing import Dict, List
from datetime import datetime


class MarketAnalyzer:
    """市場數據分析器，提供給AI使用的市場特徵"""
    
    def __init__(self, use_completed_candles_only: bool = True, lookback_bars: int = 5):
        """
        Args:
            use_completed_candles_only: True 表示只使用已完成的K棒 (強烈建議)
            lookback_bars: 回望K棒數量 (用於序列分析)
        """
        self.use_completed_only = use_completed_candles_only
        self.lookback_bars = lookback_bars
    
    def prepare_market_features(self, df: pd.DataFrame, symbol: str = 'UNKNOWN') -> Dict:
        """
        準備完整的市場特徵 (包含K棒序列)
        
        Args:
            df: 完整的歷史K線數據 (OHLCV + 技術指標)
            symbol: 交易對
        
        Returns:
            包含當前K棒、序列、趨勢的字典
        """
        # 如果設定只用已完成K棒，排除最後一根
        if self.use_completed_only and len(df) > 1:
            df = df.iloc[:-1].copy()
            print(f"Using completed candles only: {len(df)} bars (excluded last incomplete candle)")
        
        if len(df) < self.lookback_bars + 50:
            raise ValueError(f"Insufficient data: need at least {self.lookback_bars + 50} bars, got {len(df)}")
        
        # 計算技術指標
        df = self._calculate_indicators(df)
        
        # 獲取最後一根已完成K棒
        current_idx = len(df) - 1
        current_candle = df.iloc[current_idx]
        
        # 提取序列 (前n根K棒)
        sequence_start = max(0, current_idx - self.lookback_bars)
        sequence_df = df.iloc[sequence_start:current_idx + 1]
        
        # 構建特徵字典
        features = {
            'symbol': symbol,
            'timestamp': str(current_candle.get('timestamp', current_candle.name)),
            'current_candle': self._extract_candle_features(current_candle),
            'recent_sequence': self._extract_sequence_features(sequence_df),
            'indicator_trends': self._calculate_indicator_trends(sequence_df),
            'market_context': self._get_market_context(df, current_idx)
        }
        
        return features
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有技術指標"""
        df = df.copy()
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # 趨勢指標
        df['ema9'] = talib.EMA(close, timeperiod=9)
        df['ema21'] = talib.EMA(close, timeperiod=21)
        df['ema50'] = talib.EMA(close, timeperiod=50)
        df['ema200'] = talib.EMA(close, timeperiod=200)
        macd, macd_signal, macd_hist = talib.MACD(close)
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        df['adx'] = talib.ADX(high, low, close, timeperiod=14)
        
        # 動能指標
        df['rsi'] = talib.RSI(close, timeperiod=14)
        df['stoch_k'], df['stoch_d'] = talib.STOCH(high, low, close)
        df['cci'] = talib.CCI(high, low, close, timeperiod=14)
        df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
        df['willr'] = talib.WILLR(high, low, close, timeperiod=14)
        
        # 波動指標
        df['atr'] = talib.ATR(high, low, close, timeperiod=14)
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        df['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        # 成交量指標
        df['volume_ma20'] = talib.SMA(volume, timeperiod=20)
        df['volume_ratio'] = volume / (df['volume_ma20'] + 1e-10)
        df['obv'] = talib.OBV(close, volume)
        
        # 支撐/壓力
        df['pivot'] = (high + low + close) / 3
        df['resistance_1'] = df['pivot'] + (high - low)
        df['support_1'] = df['pivot'] - (high - low)
        df['dist_to_resistance'] = (df['resistance_1'] - close) / close * 100
        df['dist_to_support'] = (close - df['support_1']) / close * 100
        
        return df
    
    def _extract_candle_features(self, candle: pd.Series) -> Dict:
        """提取單根K棒的特徵"""
        features = {
            'close': float(candle['close']),
            'open': float(candle['open']),
            'high': float(candle['high']),
            'low': float(candle['low']),
            'volume': float(candle['volume'])
        }
        
        # 技術指標
        indicator_cols = [
            'rsi', 'macd_hist', 'bb_position', 'volume_ratio', 'adx',
            'ema9', 'ema21', 'ema50', 'ema200', 'atr',
            'stoch_k', 'stoch_d', 'cci', 'mfi', 'willr',
            'dist_to_resistance', 'dist_to_support'
        ]
        
        for col in indicator_cols:
            if col in candle.index and not pd.isna(candle[col]):
                features[col] = round(float(candle[col]), 4)
        
        return features
    
    def _extract_sequence_features(self, sequence_df: pd.DataFrame) -> List[Dict]:
        """提取K棒序列特徵"""
        sequence = []
        
        for idx, row in sequence_df.iterrows():
            candle_data = {
                'position': len(sequence) - len(sequence_df) + 1,  # -5, -4, -3, -2, -1, 0
                'close': float(row['close']),
                'rsi': round(float(row['rsi']), 2) if not pd.isna(row['rsi']) else None,
                'volume_ratio': round(float(row['volume_ratio']), 2) if not pd.isna(row['volume_ratio']) else None,
                'bb_position': round(float(row['bb_position']), 2) if not pd.isna(row['bb_position']) else None,
                'macd_hist': round(float(row['macd_hist']), 4) if not pd.isna(row['macd_hist']) else None
            }
            sequence.append(candle_data)
        
        return sequence
    
    def _calculate_indicator_trends(self, sequence_df: pd.DataFrame) -> Dict:
        """計算指標趨勢"""
        trends = {}
        key_indicators = ['rsi', 'macd_hist', 'volume_ratio', 'bb_position', 'adx']
        
        for indicator in key_indicators:
            if indicator not in sequence_df.columns:
                continue
            
            values = sequence_df[indicator].dropna().values
            
            if len(values) < 3:
                continue
            
            # 線性回歸計算斜率
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if abs(slope) < 0.01:
                trend = 'flat'
            elif slope > 0:
                trend = 'rising'
            else:
                trend = 'falling'
            
            trends[indicator] = {
                'trend': trend,
                'slope': round(float(slope), 4),
                'values': [round(float(v), 2) for v in values],
                'current': round(float(values[-1]), 2),
                'change': round(float(values[-1] - values[0]), 2)
            }
        
        return trends
    
    def _get_market_context(self, df: pd.DataFrame, current_idx: int) -> Dict:
        """獲取市場上下文資訊"""
        current_price = df.iloc[current_idx]['close']
        
        # 距離高低點
        high_20 = df['high'].iloc[max(0, current_idx - 20):current_idx + 1].max()
        low_20 = df['low'].iloc[max(0, current_idx - 20):current_idx + 1].min()
        
        dist_from_high_pct = (high_20 - current_price) / current_price * 100
        dist_from_low_pct = (current_price - low_20) / current_price * 100
        
        # 趨勢判斷
        ema50 = df.iloc[current_idx]['ema50']
        ema200 = df.iloc[current_idx]['ema200']
        
        if current_price > ema50 > ema200:
            trend = 'strong_uptrend'
        elif current_price > ema50:
            trend = 'uptrend'
        elif current_price < ema50 < ema200:
            trend = 'strong_downtrend'
        elif current_price < ema50:
            trend = 'downtrend'
        else:
            trend = 'sideways'
        
        return {
            'trend': trend,
            'dist_from_high_20_pct': round(dist_from_high_pct, 2),
            'dist_from_low_20_pct': round(dist_from_low_pct, 2),
            'is_near_high': dist_from_high_pct < 2,
            'is_near_low': dist_from_low_pct < 2,
            'price_above_ema50': current_price > ema50,
            'price_above_ema200': current_price > ema200
        }
    
    def format_for_ai_prompt(self, features: Dict) -> str:
        """
        格式化特徵為AI可讀的文字
        
        Args:
            features: 由 prepare_market_features() 返回的特徵字典
        
        Returns:
            格式化後的Prompt文字
        """
        current = features['current_candle']
        context = features['market_context']
        trends = features['indicator_trends']
        
        prompt = f"""Current Market State for {features['symbol']}
Timestamp: {features['timestamp']}

Price Action:
- Current Price: ${current['close']:,.2f}
- High: ${current['high']:,.2f} | Low: ${current['low']:,.2f}
- Market Trend: {context['trend'].upper()}
- Distance from 20-bar High: {context['dist_from_high_20_pct']:.2f}%
- Distance from 20-bar Low: {context['dist_from_low_20_pct']:.2f}%

Key Technical Indicators (Current Value):
- RSI(14): {current.get('rsi', 'N/A')}
- MACD Histogram: {current.get('macd_hist', 'N/A')}
- Bollinger Position: {current.get('bb_position', 'N/A')}
- Volume Ratio: {current.get('volume_ratio', 'N/A')}
- ADX(14): {current.get('adx', 'N/A')}

Indicator Trends (Last {len(features['recent_sequence'])} Candles):
"""
        
        for indicator, trend_data in trends.items():
            values_str = ' -> '.join([str(v) for v in trend_data['values']])
            prompt += f"- {indicator.upper()}: {values_str} ({trend_data['trend']}, slope={trend_data['slope']})\n"
        
        prompt += f"\nRecent Price Sequence:\n"
        for candle in features['recent_sequence']:
            prompt += f"  Position {candle['position']}: Close=${candle['close']:,.2f}, RSI={candle['rsi']}, Volume={candle['volume_ratio']}x\n"
        
        return prompt
    
    def is_market_suitable_for_trading(self, features: Dict) -> tuple[bool, str]:
        """
        判斷市場是否適合交易
        
        Args:
            features: 市場特徵
        
        Returns:
            (is_suitable, reason)
        """
        current = features['current_candle']
        context = features['market_context']
        
        # 檢查波動率
        if current.get('atr') and current.get('close'):
            atr_pct = (current['atr'] / current['close']) * 100
            if atr_pct < 0.5:
                return False, f"Too low volatility (ATR={atr_pct:.2f}%), poor trading conditions"
        
        # 檢查成交量
        volume_ratio = current.get('volume_ratio', 1.0)
        if volume_ratio < 0.5:
            return False, f"Low volume (ratio={volume_ratio:.2f}), avoid trading"
        
        # 檢查是否接近極端位置
        if context['is_near_high'] and context['dist_from_low_20_pct'] > 10:
            return True, "Near 20-bar high but with upside potential"
        
        if context['is_near_low'] and context['dist_from_high_20_pct'] > 10:
            return True, "Near 20-bar low but with downside risk"
        
        return True, "Market conditions acceptable for trading"
