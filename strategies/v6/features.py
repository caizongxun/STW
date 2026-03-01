import pandas as pd
import numpy as np

class V6FeatureEngine:
    """V6 資金費率套利特徵生成引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        """
        生成資金費率套利所需的特徵
        注意：由於實際交易所 API 才能取得即時資金費率，
        這裡我們用歷史波動率來模擬資金費率的變化
        """
        
        df = df.copy()
        
        # 計算價格波動率（用於模擬資金費率）
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=24).std()  # 24 根 K 線（8 小時級別）
        
        # 模擬資金費率（基於波動率）
        # 實際應該從交易所 API 取得，這裡用波動率乘以係數來近似
        # 正常情況下，波動越大，多頭情緒越高，資金費率越高
        df['simulated_funding_rate'] = df['volatility'] * 2  # 簡化模型
        
        # 限制資金費率在合理範圍（-0.3% ~ 0.5%）
        df['simulated_funding_rate'] = df['simulated_funding_rate'].clip(-0.003, 0.005)
        
        # 計算基差（現貨與合約價差）
        # 實際應該比較 spot price 與 futures price
        # 這裡簡化為用收盘價的 MA 偏離來模擬
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['basis'] = (df['close'] - df['ma_20']) / df['ma_20']
        
        # 計算 EMA 趨勢（用於判斷市場情緒）
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['trend'] = np.where(df['close'] > df['ema_50'], 1, -1)  # 1=牛市, -1=熊市
        
        # 清理無效數據
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna().reset_index(drop=True)
        
        return df