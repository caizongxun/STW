import pandas as pd
import numpy as np

class V3Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, long_model, short_model, fe):
        print("[V3] Backtesting...")
        
        df = fe.generate(df)
        X = df[fe.get_feature_names(df)]
        
        df['long_prob'] = long_model.predict_proba(X)[:, 1]
        df['short_prob'] = short_model.predict_proba(X)[:, 1]
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        trades = []
        equity_curve = []
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if position > 0:
                if row['low'] < entry_price - row['atr'] * self.config.atr_sl_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_sl_multiplier
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'sl_long', 'pnl': pnl})
                elif row['high'] > entry_price + row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_tp_multiplier
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'tp_long', 'pnl': pnl})
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (row['close'] - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'time_long', 'pnl': pnl})
                    
            elif position < 0:
                if row['high'] > entry_price + row['atr'] * self.config.atr_sl_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_sl_multiplier
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'sl_short', 'pnl': pnl})
                elif row['low'] < entry_price - row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_tp_multiplier
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'tp_short', 'pnl': pnl})
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (entry_price - row['close']) / entry_price * self.config.leverage
                    capital *= (1 + pnl - self.config.fee_rate*2)
                    position = 0
                    trades.append({'type': 'time_short', 'pnl': pnl})
                    
            if position == 0:
                # 放寬回測時的進場條件：移除過於嚴格的RSI限制，直接依賴模型的機率判斷
                if row['long_prob'] > self.config.signal_threshold:
                    position = 1
                    entry_price = row['close']
                    entry_idx = i
                elif row['short_prob'] > self.config.signal_threshold:
                    position = -1
                    entry_price = row['close']
                    entry_idx = i
                    
        wins = len([t for t in trades if t['pnl'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        
        return {
            'final_capital': capital,
            'return_pct': (capital - self.config.capital) / self.config.capital * 100,
            'total_trades': total,
            'win_rate': win_rate * 100
        }