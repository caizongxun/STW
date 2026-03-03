import pandas as pd
import numpy as np
import talib
from datetime import timedelta
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

class V11Backtester:
    """V11 AI 機器學習回測引擎"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.features = []
        
    def prepare_features(self, df):
        """生成供 AI 學習的大量特徵 (Feature Engineering)"""
        df = df.copy()
        
        # 1. 趨勢特徵
        df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['dist_ema20'] = (df['close'] - df['ema_20']) / df['close']
        df['dist_ema50'] = (df['close'] - df['ema_50']) / df['close']
        
        # 2. 動能特徵
        df['rsi_14'] = talib.RSI(df['close'], timeperiod=14)
        df['rsi_7'] = talib.RSI(df['close'], timeperiod=7)
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
        df['roc_5'] = talib.ROC(df['close'], timeperiod=5) # 變化率
        df['roc_15'] = talib.ROC(df['close'], timeperiod=15)
        
        # 3. 波動率特徵
        df['atr_14'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['atr_ratio'] = df['atr_14'] / df['close']
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_pos'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 4. K線形態特徵
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # 5. 成交量特徵
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma20']
        
        # 清理缺失值
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        # 定義特徵列表
        self.features = [
            'dist_ema20', 'dist_ema50', 'rsi_14', 'rsi_7', 'macd_hist', 
            'roc_5', 'roc_15', 'atr_ratio', 'bb_width', 'bb_pos',
            'body_size', 'upper_shadow', 'lower_shadow', 'vol_ratio'
        ]
        
        return df
        
    def generate_labels(self, df):
        """生成 AI 的目標標籤 (Target Label)"""
        # 目標：未來 N 根 K 線內，最高價是否超過當前收盤價的 (ATR * tp_r)，且沒有觸發止損
        # 簡化標籤：未來 N 根K線的最高價漲幅 > 最低價跌幅的 1.5倍
        
        future_high = df['high'].rolling(window=self.config.look_forward_bars).max().shift(-self.config.look_forward_bars)
        future_low = df['low'].rolling(window=self.config.look_forward_bars).min().shift(-self.config.look_forward_bars)
        
        # 潛在上漲空間
        up_space = (future_high - df['close']) / df['close']
        # 潛在下跌空間
        down_space = (df['close'] - future_low) / df['close']
        
        # Label: 如果上漲空間明顯大於下跌空間，且有足夠的絕對漲幅，標記為 1 (好機會)
        df['target'] = np.where((up_space > down_space * 1.2) & (up_space > 0.005), 1, 0)
        
        # 移除最後幾筆無法計算未來的數據
        df.dropna(subset=['target'], inplace=True)
        return df
    
    def train_ai_model(self, train_df):
        """訓練 XGBoost 模型"""
        X = train_df[self.features]
        y = train_df['target']
        
        # 建立 XGBoost 分類器
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X, y)
        
        # 計算特徵重要性
        importances = self.model.feature_importances_
        feat_imp = {feat: float(imp) for feat, imp in zip(self.features, importances)}
        feat_imp = dict(sorted(feat_imp.items(), key=lambda x: x[1], reverse=True))
        
        # 計算訓練集 AUC 評估模型質量
        train_preds = self.model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, train_preds) if len(np.unique(y)) > 1 else 0.5
        
        return auc, feat_imp

    def run(self, df):
        print(f"[V11] Preparing features for AI Model...")
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
            
        if self.config.simulation_days > 0:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
            
        df = self.prepare_features(df)
        df = self.generate_labels(df)
        
        # 劃分訓練集與測試集 (Time-series split)
        split_idx = int(len(df) * self.config.train_test_split)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        print(f"[V11] Training XGBoost Model on {len(train_df)} samples...")
        auc_score, feature_importance = self.train_ai_model(train_df)
        print(f"[V11] Model trained! AUC Score: {auc_score:.4f}")
        
        # 使用測試集進行模擬交易
        test_df = test_df.copy()
        test_df['ai_prob'] = self.model.predict_proba(test_df[self.features])[:, 1]
        
        capital = self.config.capital
        initial_capital = capital
        peak_capital = capital
        
        position = 0
        entry_price = 0
        sl_price = 0
        tp_price = 0
        position_size_usd = 0
        entry_time = None
        
        trades = []
        equity_curve = []
        
        start_time = test_df['open_time'].iloc[0] if 'open_time' in test_df.columns else None
        end_time = test_df['open_time'].iloc[-1] if 'open_time' in test_df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        for i in range(len(test_df)):
            row = test_df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital: peak_capital = capital
            if (peak_capital - capital) / peak_capital > self.config.max_drawdown_stop: break
            
            # 1. 檢查出場
            if position == 1:
                exit_price = 0
                if row['high'] >= tp_price:
                    exit_price = tp_price
                elif row['low'] <= sl_price:
                    exit_price = sl_price
                    
                if exit_price > 0:
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    
                    holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                    trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': holding_hours})
            
            # 2. AI 驅動進場
            if position == 0:
                # 核心邏輯：AI 預測上漲機率大於閾值
                if row['ai_prob'] > self.config.ai_confidence_threshold:
                    
                    # 額外的基礎趨勢過濾 (確保 AI 沒有瘋掉)
                    if row['ema_20'] > row['ema_50']:
                        
                        position = 1
                        entry_price = row['close']
                        entry_time = row['open_time'] if 'open_time' in test_df.columns else None
                        
                        sl_distance = row['atr_14'] * self.config.atr_multiplier
                        sl_price = entry_price - sl_distance
                        tp_price = entry_price + (sl_distance * self.config.tp_r)
                        
                        sl_pct = sl_distance / entry_price
                        max_loss = capital * self.config.base_risk
                        position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)

        # 統計
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        days_diff = (end_time - start_time).days if start_time and end_time else 0
        monthly_return = total_return / (days_diff / 30.0) if days_diff > 0 else 0
        
        returns_series = pd.Series([t['return'] for t in trades])
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if len(returns_series) > 1 else 0
        
        total_profit = sum([t['pnl_usd'] for t in trades if t['pnl_usd'] > 0])
        total_loss = abs(sum([t['pnl_usd'] for t in trades if t['pnl_usd'] < 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        avg_holding_hours = np.mean([t['holding_hours'] for t in trades]) if trades else 0
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'total_trades': total,
            'win_rate': win_rate * 100,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'days_tested': days_diff,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'avg_holding_hours': avg_holding_hours,
            'model_auc': auc_score,
            'feature_importance': feature_importance
        }
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve: return 0.0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak: peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd: max_dd = dd
        return max_dd