import pandas as pd
import numpy as np
from datetime import timedelta

class V8Backtester:
    """V8 回測引擎 - LSTM 反轉預測"""
    
    def __init__(self, config, lstm_model):
        self.config = config
        self.lstm_model = lstm_model
        self.filter_stats = {
            'lstm_signals': 0,
            'pass_confidence': 0,
            'pass_trend': 0,
            'pass_pattern': 0,
            'final_trades': 0
        }
        
    def run(self, df_15m, df_1h, fe):
        print("[V8] Running LSTM Reversal Strategy...")
        
        if 'open_time' in df_15m.columns:
            df_15m['open_time'] = pd.to_datetime(df_15m['open_time'])
        if 'open_time' in df_1h.columns:
            df_1h['open_time'] = pd.to_datetime(df_1h['open_time'])
        
        if self.config.simulation_days > 0:
            end_time_15m = df_15m['open_time'].max()
            start_time_15m = end_time_15m - timedelta(days=self.config.simulation_days)
            
            train_end_idx = int(len(df_15m) * self.config.train_size_pct)
            df_15m_test = df_15m.iloc[train_end_idx:].reset_index(drop=True)
            df_15m_test = df_15m_test[df_15m_test['open_time'] >= start_time_15m].reset_index(drop=True)
            
            print(f"[V8] 回測區間: {df_15m_test['open_time'].min().date()} 至 {df_15m_test['open_time'].max().date()}")
        else:
            train_end_idx = int(len(df_15m) * self.config.train_size_pct)
            df_15m_test = df_15m.iloc[train_end_idx:].reset_index(drop=True)
        
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
        daily_trades_count = 0
        last_trade_date = None
        last_exit_idx = -self.config.cooldown_bars
        
        start_time = df_15m_test['open_time'].iloc[0] if 'open_time' in df_15m_test.columns else None
        end_time = df_15m_test['open_time'].iloc[-1] if 'open_time' in df_15m_test.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        lstm_predictions = 0
        lstm_correct = 0
        
        for i in range(self.config.lstm_lookback, len(df_15m_test)):
            row = df_15m_test.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital:
                peak_capital = capital
            
            current_dd = (peak_capital - capital) / peak_capital
            if current_dd > self.config.max_drawdown_stop:
                print(f"[V8] 回撤超過 {self.config.max_drawdown_stop*100}%，停止交易")
                break
            
            if 'open_time' in df_15m_test.columns:
                current_date = row['open_time'].date()
                if last_trade_date != current_date:
                    daily_trades_count = 0
                    last_trade_date = current_date
            
            # ==========================================
            # 1. 倉位管理
            # ==========================================
            if position != 0:
                if position > 0:
                    current_profit = row['high'] - entry_price
                    sl_distance = entry_price - sl_price
                    current_r = current_profit / sl_distance if sl_distance > 0 else 0
                    
                    if current_r >= self.config.trailing_stop_trigger and sl_price < entry_price:
                        sl_price = entry_price * 1.001
                    
                    if row['low'] <= sl_price:
                        exit_price = sl_price
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        
                        if pnl_usd > 0:
                            lstm_correct += 1
                        
                        position = 0
                        last_exit_idx = i
                        
                        holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                        trades.append({
                            'type': 'sl',
                            'pnl_usd': pnl_usd,
                            'return': pnl_pct,
                            'capital': capital,
                            'holding_hours': holding_hours
                        })
                    elif row['high'] >= tp_price:
                        exit_price = tp_price
                        pnl_pct = (exit_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        lstm_correct += 1
                        position = 0
                        last_exit_idx = i
                        
                        holding_hours = (row['open_time'] - entry_time).total_seconds() / 3600 if entry_time else 0
                        trades.append({
                            'type': 'tp',
                            'pnl_usd': pnl_usd,
                            'return': pnl_pct,
                            'capital': capital,
                            'holding_hours': holding_hours
                        })
            
            # ==========================================
            # 2. LSTM 預測 + 多重過濾
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                if daily_trades_count >= self.config.max_daily_trades:
                    continue
                
                # LSTM 預測
                direction, confidence = self.lstm_model.predict(df_15m_test, i)
                lstm_predictions += 1
                
                if direction == 1:
                    self.filter_stats['lstm_signals'] += 1
                
                if confidence < self.config.lstm_confidence:
                    continue
                
                if direction != 1:
                    continue
                
                self.filter_stats['pass_confidence'] += 1
                
                # 雙時間框架確認
                if self.config.enable_dual_timeframe:
                    if not self._check_1h_trend(df_1h, row['open_time']):
                        continue
                
                self.filter_stats['pass_trend'] += 1
                
                # 反轉形態過濾
                if self.config.enable_pattern_filter:
                    if not self._check_reversal_pattern(df_15m_test, i):
                        continue
                
                self.filter_stats['pass_pattern'] += 1
                
                # 開倉
                position = 1
                entry_price = row['close']
                entry_time = row['open_time'] if 'open_time' in df_15m_test.columns else None
                
                sl_distance = row['atr'] * self.config.atr_multiplier
                sl_price = entry_price - sl_distance
                tp_price = entry_price + sl_distance * self.config.tp_ratio
                
                sl_pct = sl_distance / entry_price
                max_loss = capital * self.config.base_risk
                position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
                
                daily_trades_count += 1
                self.filter_stats['final_trades'] += 1
        
        # 統計
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        days_diff = 0
        monthly_return = 0
        if start_time and end_time:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
        
        returns_series = pd.Series([t['return'] for t in trades])
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if len(returns_series) > 1 else 0
        
        total_profit = sum([t['pnl_usd'] for t in trades if t['pnl_usd'] > 0])
        total_loss = abs(sum([t['pnl_usd'] for t in trades if t['pnl_usd'] < 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        avg_holding_hours = np.mean([t['holding_hours'] for t in trades if 'holding_hours' in t]) if trades else 0
        
        lstm_accuracy = (lstm_correct / lstm_predictions * 100) if lstm_predictions > 0 else 0
        
        print(f"[V8] 過濾統計: LSTM信號={self.filter_stats['lstm_signals']}, 通過信心度={self.filter_stats['pass_confidence']}, 通過趨勢={self.filter_stats['pass_trend']}, 最終交易={self.filter_stats['final_trades']}")
        
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
            'lstm_train_acc': self.lstm_model.train_accuracy,
            'lstm_test_acc': self.lstm_model.test_accuracy,
            'winrate_improvement': lstm_accuracy - 50,
            'filter_stats': self.filter_stats
        }
    
    def _check_1h_trend(self, df_1h, current_time_15m):
        """放寬 1h 趨勢檢查"""
        if 'open_time' not in df_1h.columns:
            return True
        
        df_1h_filtered = df_1h[df_1h['open_time'] <= current_time_15m]
        if len(df_1h_filtered) < 50:
            return True
        
        row_1h = df_1h_filtered.iloc[-1]
        
        # 放寬條件：只要不是強烈下跌趨勢即可
        strong_downtrend = (row_1h['ema_12'] < row_1h['ema_26']) and (row_1h['ema_26'] < row_1h['ema_50']) and (row_1h['rsi'] < 40)
        
        return not strong_downtrend
    
    def _check_reversal_pattern(self, df, i):
        """放寬反轉形態檢查"""
        if i < 5:
            return False
        
        row = df.iloc[i]
        
        conditions = [
            row['rsi'] < 40,  # 放宬到 40
            row['zscore_20'] < -1.0,  # 放宬到 -1.0
            row['is_pin_bar_bullish'] == 1,
            row['is_bullish_engulfing'] == 1,
            row['rsi_divergence_bullish'] == 1
        ]
        
        return sum(conditions) >= 1
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd