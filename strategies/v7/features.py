import pandas as pd
import numpy as np
import talib

class V7FeatureEngine:
    """V7 特徵生成引擎 - 為 AI 模型與策略提供豐富特徵"""
    
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        """生成完整特徵集"""
        df = df.copy()
        
        # ==========================================
        # 1. 基礎技術指標
        # ==========================================
        # ATR
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 移動平均線
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # ==========================================
        # 2. 動量與波動率特徵
        # ==========================================
        # 價格動量
        df['returns'] = df['close'].pct_change()
        df['returns_5'] = df['close'].pct_change(5)
        df['returns_20'] = df['close'].pct_change(20)
        
        # 波動率
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # 成交量特徵
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # ==========================================
        # 3. 價格行為特徵（K 線形態）
        # ==========================================
        # 實體與影線比例
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['wick_ratio'] = (df['upper_wick'] + df['lower_wick']) / df['body'].replace(0, 0.0001)
        
        # 高低點距離
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        
        # ==========================================
        # 4. 趨勢強度特徵
        # ==========================================
        # ADX（趨勢強度）
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        
        # EMA 排列
        df['ema_trend'] = np.where(
            (df['ema_20'] > df['ema_50']) & (df['ema_50'] > df['ema_200']), 1,
            np.where((df['ema_20'] < df['ema_50']) & (df['ema_50'] < df['ema_200']), -1, 0)
        )
        
        # ==========================================
        # 5. 支撐壓力特徵
        # ==========================================
        # 近期高低點
        df['swing_high'] = df['high'].rolling(window=20).max()
        df['swing_low'] = df['low'].rolling(window=20).min()
        df['distance_to_high'] = (df['swing_high'] - df['close']) / df['close']
        df['distance_to_low'] = (df['close'] - df['swing_low']) / df['close']
        
        # ==========================================
        # 6. 流動性掃蕩檢測
        # ==========================================
        # 檢測大陰陽線（可能是流動性掃蕩）
        df['is_big_wick'] = df['wick_ratio'] > self.config.liquidity_wick_ratio
        df['is_bullish_wick'] = (df['lower_wick'] > df['upper_wick']) & df['is_big_wick']
        df['is_bearish_wick'] = (df['upper_wick'] > df['lower_wick']) & df['is_big_wick']
        
        # 清理無效數據
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df