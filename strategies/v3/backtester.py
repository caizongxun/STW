import pandas as pd
import numpy as np

class V3Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, long_model, short_model, fe):
        print("[V3] High-Yield Backtesting Mode...")
        
        df = fe.generate(df)
        X = df[fe.get_feature_names(df)]
        
        df['long_prob'] = long_model.predict_proba(X)[:, 1]
        df['short_prob'] = short_model.predict_proba(X)[:, 1]
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars
        
        trades = []
        equity_curve = []
        
        # 為了計算每月報酬，需要記錄起始時間
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            # 破產保護 (低於20%本金停止交易)
            if capital < self.config.capital * 0.2:
                continue
                
            total_fee_rate = self.config.fee_rate + self.config.slippage
            
            # === 平倉邏輯 ===
            if position > 0:
                # 追蹤止盈 (Trailing Stop) 邏輯取代固定止盈
                # 假設漲幅超過 1.5 ATR 後，將止損線上移到成本價 (保本)
                current_profit = (row['high'] - entry_price) / entry_price
                dynamic_sl = entry_price - row['atr'] * self.config.atr_sl_multiplier
                
                # 如果最高價曾經碰過 1.5 ATR 獲利，止損推到 entry_price + 些微利潤
                if current_profit > (row['atr'] * 1.5 / entry_price):
                    dynamic_sl = max(dynamic_sl, entry_price * (1 + total_fee_rate * 2))
                
                # 碰到動態止損 (或原止損)
                if row['low'] < dynamic_sl:
                    exit_price = dynamic_sl
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl': pnl})
                    
                # 大波段止盈
                elif row['high'] > entry_price + row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_tp_multiplier
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl': pnl})
                    
                # 時間平倉
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (row['close'] - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_long', 'pnl': pnl})
                    
            elif position < 0:
                # 做空追蹤止損
                current_profit = (entry_price - row['low']) / entry_price
                dynamic_sl = entry_price + row['atr'] * self.config.atr_sl_multiplier
                
                if current_profit > (row['atr'] * 1.5 / entry_price):
                    dynamic_sl = min(dynamic_sl, entry_price * (1 - total_fee_rate * 2))
                    
                if row['high'] > dynamic_sl:
                    exit_price = dynamic_sl
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_short', 'pnl': pnl})
                    
                elif row['low'] < entry_price - row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_tp_multiplier
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl': pnl})
                    
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (entry_price - row['close']) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_short', 'pnl': pnl})
                    
            # === 開倉邏輯 (進攻型) ===
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 放寬指標限制，更依賴 AI 的機率判斷，避免錯失大行情
                long_cond = (
                    row['long_prob'] > self.config.signal_threshold and 
                    row['rsi'] < 55  # 從 40 放寬到 55，只要不是嚴重超買都可接多
                )
                
                short_cond = (
                    row['short_prob'] > self.config.signal_threshold and 
                    row['rsi'] > 45  # 從 60 放寬到 45
                )
                
                if long_cond:
                    position = 1
                    entry_price = row['close']
                    entry_idx = i
                elif short_cond:
                    position = -1
                    entry_price = row['close']
                    entry_idx = i
                    
        wins = len([t for t in trades if t['pnl'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - self.config.capital) / self.config.capital * 100
        
        # 計算月化報酬率
        monthly_return = 0
        if start_time is not None and end_time is not None:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'total_trades': total,
            'win_rate': win_rate * 100,
            'max_drawdown': self.calculate_max_drawdown(equity_curve)
        }
        
    def calculate_max_drawdown(self, equity_curve):
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