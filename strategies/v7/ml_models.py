import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class V7MLEngine:
    """V7 機器學習引擎 - LSTM 價格預測 + XGBoost 分類"""
    
    def __init__(self, config):
        self.config = config
        self.scaler = MinMaxScaler()
        self.lstm_model = None
        self.xgb_model = None
        self.is_trained = False
        
    def train(self, df):
        """
        訓練 ML 模型
        注意：由於這是回測環境，我們暫時使用簡化的模擬模型
        實盤時應該使用真正的 TensorFlow/PyTorch LSTM
        """
        print("[V7 ML] 訓練模型（簡化版）...")
        
        # 這裡我們用統計方法模擬 ML 模型的預測
        # 實盤時應該替換為真正的 LSTM 和 XGBoost
        self.is_trained = True
        
        print("[V7 ML] 模型訓練完成")
        
    def predict_price_direction(self, df, current_idx):
        """
        預測未來價格方向
        返回：(方向, 信心度)
        方向：1=上漲, -1=下跌, 0=不確定
        信心度：0-1 之間
        """
        if not self.is_trained or current_idx < 60:
            return 0, 0.5
        
        # 簡化模擬：使用多個技術指標組合判斷
        row = df.iloc[current_idx]
        
        signals = []
        confidences = []
        
        # 信號 1：EMA 趨勢
        if row['close'] > row['ema_20'] > row['ema_50']:
            signals.append(1)
            confidences.append(0.7)
        elif row['close'] < row['ema_20'] < row['ema_50']:
            signals.append(-1)
            confidences.append(0.7)
        
        # 信號 2：RSI
        if row['rsi'] < 30:
            signals.append(1)  # 超賣反彈
            confidences.append(0.6)
        elif row['rsi'] > 70:
            signals.append(-1)  # 超買回調
            confidences.append(0.6)
        
        # 信號 3：MACD
        if row['macd'] > row['macd_signal'] and row['macd_hist'] > 0:
            signals.append(1)
            confidences.append(0.65)
        elif row['macd'] < row['macd_signal'] and row['macd_hist'] < 0:
            signals.append(-1)
            confidences.append(0.65)
        
        # 信號 4：成交量
        if row['volume_ratio'] > 1.5:  # 放量
            if row['close'] > row['open']:  # 陽線
                signals.append(1)
                confidences.append(0.75)
            else:  # 陰線
                signals.append(-1)
                confidences.append(0.75)
        
        if not signals:
            return 0, 0.5
        
        # 綜合判斷
        avg_signal = np.mean(signals)
        avg_confidence = np.mean(confidences)
        
        if avg_signal > 0.3:
            return 1, min(avg_confidence, 0.95)
        elif avg_signal < -0.3:
            return -1, min(avg_confidence, 0.95)
        else:
            return 0, 0.5
    
    def classify_liquidation_hunt(self, df, current_idx):
        """
        分類是否為「假插針」（流動性掃蕩後反轉）
        返回：(是否為假插針, 信心度)
        """
        if not self.is_trained or current_idx < 20:
            return False, 0.5
        
        row = df.iloc[current_idx]
        
        # 檢查是否有長影線
        if not (row['is_bullish_wick'] or row['is_bearish_wick']):
            return False, 0.5
        
        # 檢查成交量是否異常
        volume_spike = row['volume_ratio'] > 2.0
        
        # 檢查是否在關鍵支撐/壓力位
        near_support = row['distance_to_low'] < 0.02
        near_resistance = row['distance_to_high'] < 0.02
        
        # 綜合判斷
        if row['is_bullish_wick'] and volume_spike and near_support:
            return True, 0.8  # 很可能是假跌破
        elif row['is_bearish_wick'] and volume_spike and near_resistance:
            return True, 0.8  # 很可能是假突破
        
        return False, 0.5