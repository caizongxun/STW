import pandas as pd
import numpy as np

class V3Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, long_model, short_model, fe):
        print("[V3] Backtesting with Optimized Risk Management...")
        
        df = fe.generate(df)
        X = df[fe.get_feature_names(df)]
        
        df['long_prob'] = long_model.predict_proba(X)[:, 1]
        df['short_prob'] = short_model.predict_proba(X)[:, 1]
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars # 初始冷卻期設定
        
        trades = []
        equity_curve = []
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            # 總回撤保護 (如果虧損超過20%，停止交易)
            if capital < self.config.capital * 0.8:
                continue
                
            # 計算實際交易手續費與滑點
            total_fee_rate = self.config.fee_rate + self.config.slippage
            
            # Position Exit Logic
            if position > 0:
                # 止損 (動態 ATR 止損)
                if row['low'] < entry_price - row['atr'] * self.config.atr_sl_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_sl_multiplier
                    # 加入手續費與滑點
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl': pnl})
                    
                # 止盈
                elif row['high'] > entry_price + row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_tp_multiplier
                    pnl = (exit_price - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl': pnl})
                    
                # 時間止損
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (row['close'] - entry_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_long', 'pnl': pnl})
                    
            elif position < 0:
                # 止損
                if row['high'] > entry_price + row['atr'] * self.config.atr_sl_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_sl_multiplier
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_short', 'pnl': pnl})
                    
                # 止盈
                elif row['low'] < entry_price - row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_tp_multiplier
                    pnl = (entry_price - exit_price) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl': pnl})
                    
                # 時間止損
                elif i - entry_idx >= self.config.t_events_bars:
                    pnl = (entry_price - row['close']) / entry_price * self.config.leverage
                    capital *= (1 + pnl * self.config.position_pct - total_fee_rate * self.config.position_pct * 2)
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_short', 'pnl': pnl})
                    
            # Entry Logic (空倉 + 滿足冷卻期)
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 多因子驗證邏輯：模型概率 + 技術指標雙重確認
                long_cond = (
                    row['long_prob'] > self.config.signal_threshold and 
                    row['rsi'] < 40 and              # RSI 不能在超買區
                    row['vol_surge_5'] > 1.2         # 需要有量能配合
                )
                
                short_cond = (
                    row['short_prob'] > self.config.signal_threshold and 
                    row['rsi'] > 60 and              # RSI 不能在超賣區
                    row['vol_surge_5'] > 1.2         # 需要有量能配合
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
        
        return {
            'final_capital': capital,
            'return_pct': (capital - self.config.capital) / self.config.capital * 100,
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