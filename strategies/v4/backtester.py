import pandas as pd
import numpy as np

class V4Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, fe):
        print("[V4] Running Strict Pullback Strategy...")
        
        df = fe.generate(df)
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars
        position_size_usd = 0 
        
        trades = []
        equity_curve = []
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital < 10:
                break
            
            # === 平倉邏輯 ===
            if position > 0:
                current_profit_pct = (row['high'] - entry_price) / entry_price
                dynamic_sl = entry_price - row['atr'] * self.config.atr_sl_multiplier
                
                # 保本機制：獲利超過 1 倍 ATR 就保本 (縮小被雙巴的機會)
                if current_profit_pct > (row['atr'] * 1.0 / entry_price):
                    dynamic_sl = max(dynamic_sl, entry_price * (1 + total_fee_rate * 2))
                
                if row['low'] < dynamic_sl:
                    exit_price = dynamic_sl
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
                elif row['high'] > entry_price + row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_tp_multiplier
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
                elif i - entry_idx >= self.config.max_hold_bars:
                    exit_price = row['close']
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_long', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
            elif position < 0:
                current_profit_pct = (entry_price - row['low']) / entry_price
                dynamic_sl = entry_price + row['atr'] * self.config.atr_sl_multiplier
                
                if current_profit_pct > (row['atr'] * 1.0 / entry_price):
                    dynamic_sl = min(dynamic_sl, entry_price * (1 - total_fee_rate * 2))
                    
                if row['high'] > dynamic_sl:
                    exit_price = dynamic_sl
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_short', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
                elif row['low'] < entry_price - row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_tp_multiplier
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
                elif i - entry_idx >= self.config.max_hold_bars:
                    exit_price = row['close']
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_short', 'pnl_usd': pnl_usd, 'capital': capital, 'return': pnl_pct})
                    
            # === 嚴格開倉邏輯 (狙擊手模式) ===
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 做多：強多頭 + 價格精準回踩均線 + 強力長下影線拒絕
                long_cond = (
                    row['strict_uptrend'] and 
                    row['near_fast_ema'] and 
                    (row['rsi'] < self.config.rsi_oversold or row['strong_reject_lower'])
                )
                if self.config.use_price_action:
                    long_cond = long_cond and row['strong_reject_lower']
                    
                # 做空：強空頭 + 價格反抽均線 + 強力長上影線拒絕
                short_cond = (
                    row['strict_downtrend'] and 
                    row['near_fast_ema'] and 
                    (row['rsi'] > self.config.rsi_overbought or row['strong_reject_higher'])
                )
                if self.config.use_price_action:
                    short_cond = short_cond and row['strong_reject_higher']
                
                if long_cond or short_cond:
                    sl_distance_price = row['atr'] * self.config.atr_sl_multiplier
                    if sl_distance_price < row['close'] * 0.001:
                        sl_distance_price = row['close'] * 0.001
                        
                    sl_pct = sl_distance_price / row['close']
                    
                    max_loss_usd = capital * self.config.risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    max_allowed_position = capital * self.config.max_leverage
                    position_size_usd = min(target_position_size, max_allowed_position)
                    
                    position = 1 if long_cond else -1
                    entry_price = row['close']
                    entry_idx = i
                    
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - self.config.capital) / self.config.capital * 100
        
        monthly_return = 0
        if start_time is not None and end_time is not None:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
                
        avg_win = np.mean([t['return'] for t in trades if t['pnl_usd'] > 0]) if wins > 0 else 0
        avg_loss = np.mean([t['return'] for t in trades if t['pnl_usd'] < 0]) if total > wins else 0
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'total_trades': total,
            'win_rate': win_rate * 100,
            'max_drawdown': self.calculate_max_drawdown(equity_curve),
            'avg_win_pct': avg_win * 100,
            'avg_loss_pct': avg_loss * 100
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