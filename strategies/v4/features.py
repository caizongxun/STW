import pandas as pd
import numpy as np
import talib

class V4FeatureEngine:
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 1. 趨勢指標 (Trend)
        df['ema_fast'] = talib.EMA(df['close'], timeperiod=self.config.ema_fast)
        df['ema_slow'] = talib.EMA(df['close'], timeperiod=self.config.ema_slow)
        
        # 定義大趨勢：Fast 在 Slow 之上，且 Slow 是向上的
        df['ema_slow_slope'] = df['ema_slow'].diff(5)
        df['uptrend'] = (df['ema_fast'] > df['ema_slow']) & (df['ema_slow_slope'] > 0)
        df['downtrend'] = (df['ema_fast'] < df['ema_slow']) & (df['ema_slow_slope'] < 0)
        
        # 2. 動量指標 (Momentum - 用來找回調買點)
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.config.rsi_period)
        
        # 3. 波動率 (Volatility - 用來算止損止盈)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=self.config.atr_period)
        
        # 4. 價格行為形態 (Price Action)
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        
        # 探底反彈特徵 (拒絕下跌)：實體小，下影線長
        df['reject_lower'] = (lower_shadow > body * 1.5) & (lower_shadow > upper_shadow)
        # 衝高回落特徵 (拒絕上漲)：實體小，上影線長
        df['reject_higher'] = (upper_shadow > body * 1.5) & (upper_shadow > lower_shadow)
        
        # 5. 回踩確認 (Pullback)
        # 價格曾經跌破 fast EMA，但收盤又站上去 (破底翻)
        df['pullback_buy'] = (df['low'] < df['ema_fast']) & (df['close'] > df['ema_fast'])
        df['pullback_sell'] = (df['high'] > df['ema_fast']) & (df['close'] < df['ema_fast'])
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        return df