import pandas as pd
import numpy as np
import talib
from datetime import timedelta

class V9Backtester:
    """V9 回測引擎 - 支援三種出場模式"""
    
    def __init__(self, config):
        self.config = config
        
    def prepare_features(self, df):
        df = df.copy()
        
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
        
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        bb_width = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / bb_width.replace(0, 0.0001)
        
        ma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['z_score'] = (df['close'] - ma_20) / std_20.replace(0, 0.0001)
        
        rsi_14_low = df['rsi'].rolling(14).min()
        rsi_14_high = df['rsi'].rolling(14).max()
        rsi_range = rsi_14_high - rsi_14_low
        df['stoch_rsi'] = (df['rsi'] - rsi_14_low) / rsi_range.replace(0, 0.0001)
        
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df
    
    def run(self, df):
        print(f"[V9] Running Strategy ({self.config.exit_mode} mode)...")
        
        df = self.prepare_features(df)
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
        
        if self.config.simulation_days > 0:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
        
        capital = self.config.capital
        initial_capital = capital
        peak_capital = capital
        
        position = 0
        entry_price = 0
        sl_price = 0
        original_sl_distance = 0
        tp1_price = 0
        tp2_price = 0
        position_size_usd = 0
        entry_time = None
        
        # 狀態標記
        tp1_triggered = False
        highest_r_reached = 0.0
        
        trades = []
        equity_curve = []
        last_exit_idx = -self.config.cooldown_bars
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        # 統計
        stats = {
            'tp1_count': 0, 'tp2_count': 0, 'sl_count': 0,
            'trailing_activated': 0, 'trailing_stopped': 0
        }
        
        for i in range(200, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital:
                peak_capital = capital
            if (peak_capital - capital) / peak_capital > self.config.max_drawdown_stop:
                break
            
            # ==========================================
            # 1. 倉位管理與出場邏輯
            # ==========================================
            if position != 0:
                current_profit = row['high'] - entry_price
                current_r = current_profit / original_sl_distance if original_sl_distance > 0 else 0
                
                if current_r > highest_r_reached:
                    highest_r_reached = current_r
                
                # 模式 1: 分批止盈 (Partial TP)
                if self.config.exit_mode == 'partial_tp':
                    if not tp1_triggered and row['high'] >= tp1_price:
                        # 平倉指定比例
                        partial_size = position_size_usd * self.config.partial_tp_pct
                        pnl_pct = (tp1_price - entry_price) / entry_price
                        pnl_usd = partial_size * pnl_pct - (partial_size * total_fee_rate * 2)
                        capital += pnl_usd
                        
                        sl_price = entry_price * 1.002 # 移保本
                        tp1_triggered = True
                        position_size_usd -= partial_size
                        stats['tp1_count'] += 1
                        
                    elif tp1_triggered and row['high'] >= tp2_price:
                        # 剩餘倉位觸發最終目標
                        pnl_pct = (tp2_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        
                        position = 0
                        stats['tp2_count'] += 1
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
                        
                    elif row['low'] <= sl_price:
                        # 觸發止損 (可能是原始止損，也可能是保本止損)
                        pnl_pct = (sl_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        
                        if not tp1_triggered: stats['sl_count'] += 1
                        
                        position = 0
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
                
                # 模式 2: 動態追蹤止盈 (Trailing Stop)
                elif self.config.exit_mode == 'trailing':
                    # 啟動追蹤：達到 tp1_r 時，移至保本
                    if not tp1_triggered and row['high'] >= tp1_price:
                        sl_price = entry_price * 1.002
                        tp1_triggered = True
                        stats['trailing_activated'] += 1
                    
                    # 階梯上移：每多賺 0.5R，止損就跟著上移
                    if tp1_triggered:
                        # 計算應該鎖定的利潤點 (最高點減去 1R 的回調空間)
                        new_sl = entry_price + (highest_r_reached - 1.0) * original_sl_distance
                        if new_sl > sl_price:
                            sl_price = new_sl
                            
                    # 觸發極限目標
                    if row['high'] >= tp2_price:
                        pnl_pct = (tp2_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        position = 0
                        stats['tp2_count'] += 1
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
                        
                    # 觸發止損/追蹤止損
                    elif row['low'] <= sl_price:
                        pnl_pct = (sl_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        
                        if tp1_triggered: stats['trailing_stopped'] += 1
                        else: stats['sl_count'] += 1
                            
                        position = 0
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
                
                # 模式 3: SMC全額奔跑 (Runner)
                elif self.config.exit_mode == 'smc_runner':
                    if row['high'] >= tp2_price:
                        pnl_pct = (tp2_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        position = 0
                        stats['tp2_count'] += 1
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
                        
                    elif row['low'] <= sl_price:
                        pnl_pct = (sl_price - entry_price) / entry_price
                        pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                        capital += pnl_usd
                        position = 0
                        stats['sl_count'] += 1
                        trades.append({'pnl_usd': pnl_usd, 'return': pnl_pct, 'holding_hours': (row['open_time']-entry_time).total_seconds()/3600})
                        last_exit_idx = i
            
            # ==========================================
            # 2. 進場邏輯
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                trend_up = (row['ema_50'] > row['ema_200']) and (row['close'] > row['ema_200'])
                if not trend_up: continue
                
                near_ema = abs(row['close'] - row['ema_50']) / row['close'] < 0.040
                if not near_ema: continue
                
                oversold_signals = [
                    row['z_score'] < -1.2,
                    row['bb_position'] < 0.3,
                    row['stoch_rsi'] < 0.35
                ]
                if sum(oversold_signals) < 1: continue
                
                macd_turning = row['macd_hist'] > df['macd_hist'].iloc[i-1]
                if not macd_turning: continue
                
                # 執行進場
                position = 1
                entry_price = row['close']
                entry_time = row['open_time'] if 'open_time' in df.columns else None
                
                original_sl_distance = row['atr'] * self.config.atr_multiplier
                sl_price = entry_price - original_sl_distance
                
                tp1_price = entry_price + original_sl_distance * self.config.tp1_r
                tp2_price = entry_price + original_sl_distance * self.config.tp2_r
                
                sl_pct = original_sl_distance / entry_price
                max_loss = capital * self.config.base_risk
                position_size_usd = min(max_loss / sl_pct, capital * self.config.max_leverage)
                
                tp1_triggered = False
                highest_r_reached = 0.0
        
        # 結算
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
            'exit_stats': stats
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