import pandas as pd
import numpy as np
import talib
from datetime import timedelta
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

class V12Backtester:
    """V12 高階 AI 回測引擎 (Triple Barrier & Auto-Threshold)"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.features = []
        self.best_threshold = 0.5
        
    def prepare_features(self, df):
        """建構高階量化特徵"""
        df = df.copy()
        
        # 1. 價格動能與回報率 (Returns & Momentum)
        df['ret_1'] = df['close'].pct_change(1)
        df['ret_4'] = df['close'].pct_change(4)   # 1小時
        df['ret_12'] = df['close'].pct_change(12) # 3小時
        df['ret_24'] = df['close'].pct_change(24) # 6小時
        
        # 2. 波動率 (Volatility)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['atr_ratio'] = df['atr'] / df['close']
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'], timeperiod=20)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 3. 趨勢與發散度 (Divergence)
        df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        df['dist_ema50'] = (df['close'] - df['ema_50']) / df['close']
        df['dist_ema200'] = (df['close'] - df['ema_200']) / df['close']
        
        # 4. 經典震盪指標
        df['rsi_14'] = talib.RSI(df['close'], timeperiod=14)
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
        
        # 5. 成交量特徵
        df['vol_ma'] = df['volume'].rolling(24).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma']
        
        # 清理
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        self.features = [
            'ret_1', 'ret_4', 'ret_12', 'ret_24', 'atr_ratio', 'bb_width',
            'dist_ema50', 'dist_ema200', 'rsi_14', 'macd_hist', 'vol_ratio'
        ]
        return df
        
    def generate_triple_barrier_labels(self, df):
        """
        三重屏障標籤 (Triple Barrier Method)
        真實模擬交易：在未來 N 根 K 線內，是先撞到止盈(1)，還是先撞到止損/超時(0)
        """
        print("[V12] Generating Triple-Barrier Labels...")
        
        # 預先計算每一行的止盈與止損絕對價格
        tp_prices = df['close'] + (df['atr'] * self.config.tp_atr_mult)
        sl_prices = df['close'] - (df['atr'] * self.config.sl_atr_mult)
        
        high_vals = df['high'].values
        low_vals = df['low'].values
        tp_vals = tp_prices.values
        sl_vals = sl_prices.values
        
        n_rows = len(df)
        look_forward = self.config.look_forward_bars
        targets = np.zeros(n_rows)
        
        # Vectorized-like loop for accurate barrier hit detection
        for i in range(n_rows - look_forward):
            window_high = high_vals[i+1 : i+1+look_forward]
            window_low = low_vals[i+1 : i+1+look_forward]
            
            target_tp = tp_vals[i]
            target_sl = sl_vals[i]
            
            # Find index where barriers are crossed
            hit_tp_idx = np.argmax(window_high >= target_tp)
            hit_sl_idx = np.argmax(window_low <= target_sl)
            
            # np.argmax returns 0 if not found, we must verify if it actually hit
            did_hit_tp = window_high[hit_tp_idx] >= target_tp
            did_hit_sl = window_low[hit_sl_idx] <= target_sl
            
            if did_hit_tp and not did_hit_sl:
                targets[i] = 1  # Hit TP perfectly
            elif did_hit_tp and did_hit_sl:
                if hit_tp_idx < hit_sl_idx:
                    targets[i] = 1  # Hit TP before SL
                else:
                    targets[i] = 0  # Hit SL first
            else:
                targets[i] = 0  # Hit SL only, or timed out
                
        df['target'] = targets
        
        # 移除最後無法確定的數據
        df = df.iloc[:-look_forward].copy()
        
        class_1_ratio = df['target'].mean()
        print(f"[V12] Labeling complete. Class 1 (Win) ratio: {class_1_ratio:.1%}")
        return df
    
    def train_and_optimize(self, train_df):
        """訓練模型並自動尋找最佳閾值以滿足 Precision>0.6, Recall>0.6"""
        X_train = train_df[self.features]
        y_train = train_df['target']
        
        # 處理極度不平衡的樣本 (Class Imbalance)
        pos_weight = (len(y_train) - sum(y_train)) / sum(y_train) if sum(y_train) > 0 else 1.0
        
        self.model = xgb.XGBClassifier(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=pos_weight, # 增強對少數獲利樣本的敏感度 (提升 Recall)
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X_train, y_train)
        
        train_probs = self.model.predict_proba(X_train)[:, 1]
        
        # 尋找最佳閾值 (Auto-Thresholding)
        best_score = -999
        best_th = 0.5
        
        for th in np.arange(0.30, 0.85, 0.02):
            preds = (train_probs > th).astype(int)
            p = precision_score(y_train, preds, zero_division=0)
            r = recall_score(y_train, preds, zero_division=0)
            
            # 目標：滿足 P>=0.6 且 R>=0.6
            if p >= 0.6 and r >= 0.6:
                # 滿足條件時，以 F1 score 最大化為目標，並給予巨大獎勵
                score = p + r + 10 
            else:
                # 若無法同時滿足，則尋找兩者最平衡的高點
                score = f1_score(y_train, preds)
                
            if score > best_score:
                best_score = score
                best_th = float(th)
                
        self.best_threshold = best_th
        print(f"[V12] Auto-Threshold selected: {self.best_threshold:.2f}")

    def run(self, df):
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
            
        if self.config.simulation_days > 0:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
            
        df = self.prepare_features(df)
        df = self.generate_triple_barrier_labels(df)
        
        # 劃分數據集
        split_idx = int(len(df) * self.config.train_test_split)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        print(f"[V12] Training model...")
        self.train_and_optimize(train_df)
        
        # 評估測試集表現
        X_test = test_df[self.features]
        y_test = test_df['target']
        test_probs = self.model.predict_proba(X_test)[:, 1]
        test_preds = (test_probs > self.best_threshold).astype(int)
        
        test_auc = roc_auc_score(y_test, test_probs) if len(np.unique(y_test)) > 1 else 0.5
        test_prec = precision_score(y_test, test_preds, zero_division=0)
        test_rec = recall_score(y_test, test_preds, zero_division=0)
        
        print(f"[V12] Test Metrics - AUC: {test_auc:.3f}, Precision: {test_prec:.3f}, Recall: {test_rec:.3f}")
        
        # ----------------------------------------
        # 模擬交易 (Backtest Execution)
        # ----------------------------------------
        test_df = test_df.copy()
        test_df['ai_prob'] = test_probs
        
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
        
        trades_today = 0
        last_trade_date = None
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        real_start_time = test_df['open_time'].iloc[0]
        real_end_time = test_df['open_time'].iloc[-1]
        
        for i in range(len(test_df)):
            row = test_df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital: peak_capital = capital
            if (peak_capital - capital) / peak_capital > self.config.max_drawdown_stop: break
            
            current_date = row['open_time'].date()
            if current_date != last_trade_date:
                trades_today = 0
                last_trade_date = current_date
            
            # 1. 檢查出場
            if position == 1:
                exit_price = 0
                if row['high'] >= tp_price:
                    exit_price = tp_price
                elif row['low'] <= sl_price:
                    exit_price = sl_price
                    
                # 超時強平 (如果超過 look_forward_bars 還沒碰到 TP/SL)
                time_in_trade = (row['open_time'] - entry_time).total_seconds() / 60 / 15 # 15m bars
                if exit_price == 0 and time_in_trade >= self.config.look_forward_bars:
                    exit_price = row['close']
                    
                if exit_price > 0:
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    
                    holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600
                    trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': holding_hours})
            
            # 2. 進場邏輯
            if position == 0 and trades_today < self.config.max_daily_trades:
                # 核心：AI 預測機率超過動態最佳閾值
                if row['ai_prob'] > self.config.best_threshold:
                    
                    position = 1
                    entry_price = row['close']
                    entry_time = row['open_time']
                    
                    sl_distance = row['atr'] * self.config.sl_atr_mult
                    sl_price = entry_price - sl_distance
                    tp_price = entry_price + (row['atr'] * self.config.tp_atr_mult)
                    
                    sl_pct = sl_distance / entry_price
                    max_loss = capital * self.config.base_risk
                    position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
                    
                    trades_today += 1

        # 統計與結算
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        days_diff = (real_end_time - real_start_time).days
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
            'test_auc': test_auc,
            'test_precision': test_prec,
            'test_recall': test_rec,
            'best_threshold': self.best_threshold
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