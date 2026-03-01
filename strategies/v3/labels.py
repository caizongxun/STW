import pandas as pd
import numpy as np

class V3LabelGenerator:
    """
    優化版三重障礙法 (Triple Barrier Method)
    """
    def __init__(self, config):
        self.config = config
        
    def generate(self, df):
        df = df.copy()
        
        # 取得波動率，最低限制波動率避免死水行情導致目標過小
        daily_vol = df['volatility_20'].clip(lower=0.001) if 'volatility_20' in df.columns else df['close'].pct_change().rolling(20).std().clip(lower=0.001)
        
        labels = np.zeros(len(df))
        
        # 放寬止盈止損比例 (預設可能太大導致打不到)
        pt_ratio = self.config.pt_sl_ratio[0]
        sl_ratio = self.config.pt_sl_ratio[1]
        t_bars = self.config.t_events_bars
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        vols = daily_vol.values
        
        for i in range(len(df) - t_bars):
            if np.isnan(vols[i]) or vols[i] == 0:
                continue
                
            entry_price = closes[i]
            
            # 使用更大的波動率乘數，或者加入 min_return 限制，確保利潤空間
            pt_target = max(pt_ratio * vols[i], self.config.min_return)
            sl_target = max(sl_ratio * vols[i], self.config.min_return)
            
            barrier_up = entry_price * (1 + pt_target)
            barrier_down = entry_price * (1 - sl_target)
            
            hit_label = 0 # 0 代表觸碰時間障礙
            
            for j in range(1, t_bars + 1):
                idx = i + j
                
                # 同一根K線如果同時碰到上下軌，通常以最高價最低價發生的先後順序為準
                # 這裡簡單假設：如果波動過大，記為無效(0) 或視為止損優先以防風險
                if highs[idx] >= barrier_up and lows[idx] <= barrier_down:
                    hit_label = -1 # 保守起見，視作止損
                    break
                    
                if highs[idx] >= barrier_up:
                    hit_label = 1
                    break
                    
                elif lows[idx] <= barrier_down:
                    hit_label = -1
                    break
            
            labels[i] = hit_label
            
        df['label'] = labels
        
        # 標籤二值化
        df['label_long'] = (df['label'] == 1).astype(int)
        df['label_short'] = (df['label'] == -1).astype(int)
        
        df.iloc[-t_bars:, df.columns.get_indexer(['label', 'label_long', 'label_short'])] = np.nan
        
        return df