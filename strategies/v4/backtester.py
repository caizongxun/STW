import pandas as pd
import numpy as np

class V4Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, fe):
        print("[V4] Running ICT Strategy with Compounding and Killzones...")
        
        df = fe.generate(df)
        
        # 確保 open_time 為 datetime 格式以便處理時間
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
            df['hour'] = df['open_time'].dt.hour
        else:
            df['hour'] = 12 # fallback
            
        capital = self.config.capital
        peak_capital = capital # 用於 High-Water Mark 提款/複利邏輯
        
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars
        position_size_usd = 0 
        
        current_sl_price = 0
        current_tp_price = 0
        sl_distance = 0
        
        active_bull_fvg = None
        active_bear_fvg = None
        
        trades = []
        equity_curve = []
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        last_sweep_low_idx = -999
        last_sweep_high_idx = -999
        
        for i in range(2, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital > peak_capital:
                peak_capital = capital
                
            if capital < self.config.capital * 0.1: # 虧損超過 90% 停損
                break
                
            if row['sweep_low']: last_sweep_low_idx = i
            if row['sweep_high']: last_sweep_high_idx = i
            
            # 判斷是否在活躍交易時間 (倫敦尾盤/紐約早盤/亞洲波動區)
            # 大約是 UTC 12:00-20:00 (紐約) 和 00:00-04:00 (亞洲早盤) 和 07:00-11:00 (倫敦)
            # 簡單排除最死水的 UTC 21:00-23:00 和 04:00-06:00
            is_active_session = True
            if self.config.use_killzones:
                h = row['hour']
                if (21 <= h <= 23) or (4 <= h <= 6):
                    is_active_session = False
                
            # ==========================================
            # 1. 倉位管理
            # ==========================================
            if position > 0:
                current_profit_dist = row['high'] - entry_price
                current_r = current_profit_dist / sl_distance if sl_distance > 0 else 0
                
                if current_r >= self.config.breakeven_r and current_sl_price < entry_price * (1 + total_fee_rate * 2):
                    current_sl_price = entry_price * (1 + total_fee_rate * 2)
                
                if row['low'] < current_sl_price:
                    exit_price = current_sl_price
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl_usd': pnl_usd, 'return': pnl_pct, 'capital': capital})
                    
                elif row['high'] > current_tp_price:
                    exit_price = current_tp_price
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl_usd': pnl_usd, 'return': pnl_pct, 'capital': capital})
                    
            elif position < 0:
                current_profit_dist = entry_price - row['low']
                current_r = current_profit_dist / sl_distance if sl_distance > 0 else 0
                
                if current_r >= self.config.breakeven_r and current_sl_price > entry_price * (1 - total_fee_rate * 2):
                    current_sl_price = entry_price * (1 - total_fee_rate * 2)
                    
                if row['high'] > current_sl_price:
                    exit_price = current_sl_price
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_short', 'pnl_usd': pnl_usd, 'return': pnl_pct, 'capital': capital})
                    
                elif row['low'] < current_tp_price:
                    exit_price = current_tp_price
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl_usd': pnl_usd, 'return': pnl_pct, 'capital': capital})
            
            # ==========================================
            # 2. FVG 狀態管理
            # ==========================================
            if active_bull_fvg:
                active_bull_fvg['age'] += 1
                if row['close'] < active_bull_fvg['bottom'] or active_bull_fvg['age'] > self.config.fvg_max_age:
                    active_bull_fvg = None
                    
            if active_bear_fvg:
                active_bear_fvg['age'] += 1
                if row['close'] > active_bear_fvg['top'] or active_bear_fvg['age'] > self.config.fvg_max_age:
                    active_bear_fvg = None
            
            if row['fvg_bull']:
                valid = True
                if self.config.require_sweep and (i - last_sweep_low_idx) > 5:
                    valid = False
                if valid:
                    sl = df['swing_low'].iloc[i] - row['atr'] * 0.1
                    active_bull_fvg = {'top': row['fvg_bull_top'], 'bottom': row['fvg_bull_bottom'], 'sl': sl, 'age': 0}
                
            if row['fvg_bear']:
                valid = True
                if self.config.require_sweep and (i - last_sweep_high_idx) > 5:
                    valid = False
                if valid:
                    sl = df['swing_high'].iloc[i] + row['atr'] * 0.1
                    active_bear_fvg = {'top': row['fvg_bear_top'], 'bottom': row['fvg_bear_bottom'], 'sl': sl, 'age': 0}
            
            # ==========================================
            # 3. 進場邏輯
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars and is_active_session:
                
                # 計算用來開倉的基準資金 (複利 vs 單利)
                trading_capital = capital if self.config.use_compounding else self.config.capital
                
                if active_bull_fvg and row['low'] <= active_bull_fvg['top'] and row['close'] > row['ema_trend']:
                    entry_price = min(row['open'], active_bull_fvg['top'])
                    sl_price = active_bull_fvg['sl']
                    sl_dist = entry_price - sl_price
                    sl_pct = sl_dist / entry_price
                    if sl_pct < 0.002: sl_pct = 0.002 
                    
                    max_loss_usd = trading_capital * self.config.risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    position_size_usd = min(target_position_size, trading_capital * self.config.max_leverage)
                    
                    if row['low'] <= sl_price:
                        pnl_usd = -max_loss_usd
                        capital += pnl_usd
                        trades.append({'type': 'sl_long_instant', 'pnl_usd': pnl_usd, 'return': -sl_pct, 'capital': capital})
                    else:
                        position = 1
                        entry_idx = i
                        current_sl_price = sl_price
                        sl_distance = sl_dist
                        current_tp_price = entry_price + sl_dist * self.config.risk_reward_ratio
                    
                    active_bull_fvg = None
                    
                elif active_bear_fvg and row['high'] >= active_bear_fvg['bottom'] and row['close'] < row['ema_trend']:
                    entry_price = max(row['open'], active_bear_fvg['bottom'])
                    sl_price = active_bear_fvg['sl']
                    sl_dist = sl_price - entry_price
                    sl_pct = sl_dist / entry_price
                    if sl_pct < 0.002: sl_pct = 0.002
                    
                    max_loss_usd = trading_capital * self.config.risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    position_size_usd = min(target_position_size, trading_capital * self.config.max_leverage)
                    
                    if row['high'] >= sl_price:
                        pnl_usd = -max_loss_usd
                        capital += pnl_usd
                        trades.append({'type': 'sl_short_instant', 'pnl_usd': pnl_usd, 'return': -sl_pct, 'capital': capital})
                    else:
                        position = -1
                        entry_idx = i
                        current_sl_price = sl_price
                        sl_distance = sl_dist
                        current_tp_price = entry_price - sl_dist * self.config.risk_reward_ratio
                        
                    active_bear_fvg = None
                    
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - self.config.capital) / self.config.capital * 100
        
        monthly_return = 0
        if start_time is not None and end_time is not None:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                # 嚴格的月化報酬公式： (總報酬+1) ^ (30/總天數) - 1
                compound_monthly = ((capital / self.config.capital) ** (30.0 / days_diff) - 1) * 100
                monthly_return = compound_monthly
                
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
            'avg_loss_pct': avg_loss * 100,
            'days_tested': days_diff if 'days_diff' in locals() else 0
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