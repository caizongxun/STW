import pandas as pd
import numpy as np

class V3LabelGenerator:
    """
    實作《Advances in Financial Machine Learning》中的三重障礙法 (Triple Barrier Method)
    """
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 計算每根K線的目標波動率 (用於設定上下軌)
        # 若無 atr，使用 20 期標準差代替
        daily_vol = df['volatility_20'] if 'volatility_20' in df.columns else df['close'].pct_change().rolling(20).std()
        
        # 儲存標籤的陣列: 1 (做多盈利), -1 (做空盈利/做多止損), 0 (超時平倉)
        labels = np.zeros(len(df))
        
        pt_ratio = self.config.pt_sl_ratio[0]
        sl_ratio = self.config.pt_sl_ratio[1]
        t_bars = self.config.t_events_bars
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        vols = daily_vol.values
        
        # 向量化不易實現精確的三重障礙，此處使用 Numba 友好的迴圈或簡單迴圈
        for i in range(len(df) - t_bars):
            if np.isnan(vols[i]) or vols[i] == 0:
                continue
                
            entry_price = closes[i]
            # 根據波動率計算絕對的價格變化閾值
            barrier_up = entry_price * (1 + pt_ratio * vols[i])
            barrier_down = entry_price * (1 - sl_ratio * vols[i])
            
            hit_label = 0 # 預設時間障礙
            
            # 遍歷未來 t_bars 根 K 線
            for j in range(1, t_bars + 1):
                idx = i + j
                
                # 觸碰上軌 (Profit Taking for Long / Stop Loss for Short)
                if highs[idx] >= barrier_up:
                    hit_label = 1
                    break
                    
                # 觸碰下軌 (Stop Loss for Long / Profit Taking for Short)
                elif lows[idx] <= barrier_down:
                    hit_label = -1
                    break
            
            labels[i] = hit_label
            
        df['label'] = labels
        
        # 將三重障礙標籤轉換為兩個二元分類任務的標籤 (Long & Short)
        # 針對底部反轉 (做多): 希望未來碰到上軌 (+1)
        df['label_long'] = (df['label'] == 1).astype(int)
        
        # 針對頂部反轉 (做空): 希望未來碰到下軌 (-1)
        df['label_short'] = (df['label'] == -1).astype(int)
        
        # 移除最後無法計算完整時間障礙的資料
        df.iloc[-t_bars:, df.columns.get_indexer(['label', 'label_long', 'label_short'])] = np.nan
        
        return df