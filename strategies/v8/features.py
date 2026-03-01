import pandas as pd
import numpy as np
import talib

class V8FeatureEngine:
    """V8 高級特徵生成引擎 - 為 LSTM 提供豐富特徵"""
    
    def __init__(self, config):
        self.config = config
        
    def generate(self, df, timeframe='15m'):
        """生成完整特徵集"""
        df = df.copy()
        
        # ==========================================
        # 1. 基礎技術指標
        # ==========================================
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
        df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # Stochastic
        df['slowk'], df['slowd'] = talib.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=14, slowk_period=3, slowd_period=3
        )
        
        # ==========================================
        # 2. 價格行為特徵
        # ==========================================
        df['returns'] = df['close'].pct_change()
        df['returns_5'] = df['close'].pct_change(5)
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['total_range'] = df['high'] - df['low']
        df['body_ratio'] = df['body'] / df['total_range'].replace(0, 0.0001)
        df['upper_wick_ratio'] = df['upper_wick'] / df['total_range'].replace(0, 0.0001)
        df['lower_wick_ratio'] = df['lower_wick'] / df['total_range'].replace(0, 0.0001)
        
        # ==========================================
        # 3. 成交量特徵
        # ==========================================
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma'].replace(0, 0.0001)
        df['volume_std'] = df['volume'].rolling(window=20).std()
        
        # ==========================================
        # 4. 趨勢與位置特徵
        # ==========================================
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        
        df['swing_high_20'] = df['high'].rolling(window=20).max()
        df['swing_low_20'] = df['low'].rolling(window=20).min()
        df['price_position'] = (df['close'] - df['swing_low_20']) / (df['swing_high_20'] - df['swing_low_20']).replace(0, 0.0001)
        
        df['distance_to_ema12'] = (df['close'] - df['ema_12']) / df['close']
        df['distance_to_ema26'] = (df['close'] - df['ema_26']) / df['close']
        
        # Z-Score
        df['zscore_20'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std().replace(0, 0.0001)
        
        # ==========================================
        # 5. 反轉形態特徵
        # ==========================================
        # Pin Bar 檢測
        df['is_pin_bar_bullish'] = (
            (df['lower_wick_ratio'] > 0.5) &
            (df['body_ratio'] < 0.3) &
            (df['upper_wick_ratio'] < 0.2)
        ).astype(int)
        
        df['is_pin_bar_bearish'] = (
            (df['upper_wick_ratio'] > 0.5) &
            (df['body_ratio'] < 0.3) &
            (df['lower_wick_ratio'] < 0.2)
        ).astype(int)
        
        # 呠噬形態
        df['is_bullish_engulfing'] = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (df['open'] < df['close'].shift(1))
        ).astype(int)
        
        df['is_bearish_engulfing'] = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open'].shift(1)) &
            (df['open'] > df['close'].shift(1))
        ).astype(int)
        
        # RSI 背離簡化檢測
        df['rsi_slope'] = df['rsi'].diff(3)
        df['price_slope'] = df['close'].pct_change(3)
        df['rsi_divergence_bullish'] = ((df['price_slope'] < 0) & (df['rsi_slope'] > 0)).astype(int)
        df['rsi_divergence_bearish'] = ((df['price_slope'] > 0) & (df['rsi_slope'] < 0)).astype(int)
        
        # ==========================================
        # 6. 多周期特徵（如果需要）
        # ==========================================
        # 在 backtester 中用 1h 數據來確認趨勢
        
        # 清理無效數據
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df
    
    def get_feature_columns(self):
        """LSTM 模型使用的特徵列"""
        return [
            'returns', 'returns_5', 'volatility',
            'rsi', 'macd_hist', 'slowk', 'slowd',
            'volume_ratio', 'body_ratio', 'upper_wick_ratio', 'lower_wick_ratio',
            'distance_to_ema12', 'distance_to_ema26',
            'zscore_20', 'price_position', 'adx',
            'is_pin_bar_bullish', 'is_pin_bar_bearish',
            'is_bullish_engulfing', 'is_bearish_engulfing',
            'rsi_divergence_bullish', 'rsi_divergence_bearish'
        ]