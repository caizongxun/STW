import pandas as pd
import numpy as np

class V4Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, fe):
        print("[V4] Running ICT / SMC Fair Value Gap Strategy...")
        
        df = fe.generate(df)
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars
        position_size_usd = 0 
        
        # 動態止損與止盈
        current_sl_price = 0
        current_tp_price = 0
        sl_distance = 0
        
        # ICT 狀態追蹤
        active_bull_fvg = None
        active_bear_fvg = None
        
        trades = []
        equity_curve = []
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        
        # 從第3根開始(因為FVG需要3根K線確認)
        for i in range(2, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital < 10:
                break
                
            # ==========================================
            # 1. 倉位管理 (平倉邏輯)
            # ==========================================
            if position > 0:
                current_profit_dist = row['high'] - entry_price
                current_r = current_profit_dist / sl_distance if sl_distance > 0 else 0
                
                # 保本推移：當利潤達到設定的 R 倍數時，無風險保本
                if current_r >= self.config.breakeven_r and current_sl_price < entry_price * (1 + total_fee_rate * 2):
                    current_sl_price = entry_price * (1 + total_fee_rate * 2)
                
                if row['low'] < current_sl_price:
                    exit_price = current_sl_price
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl_usd': pnl_usd, 'return': pnl_pct})
                    
                elif row['high'] > current_tp_price:
                    exit_price = current_tp_price
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl_usd': pnl_usd, 'return': pnl_pct})
                    
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
                    trades.append({'type': 'sl_short', 'pnl_usd': pnl_usd, 'return': pnl_pct})
                    
                elif row['low'] < current_tp_price:
                    exit_price = current_tp_price
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl_usd': pnl_usd, 'return': pnl_pct})
            
            # ==========================================
            # 2. 進場邏輯 (SMC FVG Retracement)
            # ==========================================
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 判斷多頭進場：價格回踩到 Bullish FVG 內部
                if active_bull_fvg and row['low'] <= active_bull_fvg['top'] and row['close'] > row['ema_trend']:
                    # 模擬限價單成交 (Limit Order at FVG Top)
                    entry_price = min(row['open'], active_bull_fvg['top'])
                    sl_price = active_bull_fvg['sl']
                    
                    sl_dist = entry_price - sl_price
                    sl_pct = sl_dist / entry_price
                    if sl_pct < 0.001: sl_pct = 0.001 # 最小止損距離 0.1%
                    
                    max_loss_usd = capital * self.config.risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    position_size_usd = min(target_position_size, capital * self.config.max_leverage)
                    
                    # 檢查是否在同一根 K 線內直接打到止損 (防止回測作弊)
                    if row['low'] <= sl_price:
                        # 瞬間止損
                        pnl_usd = -max_loss_usd
                        capital += pnl_usd
                        trades.append({'type': 'sl_long_instant', 'pnl_usd': pnl_usd, 'return': -sl_pct})
                    else:
                        position = 1
                        entry_idx = i
                        current_sl_price = sl_price
                        sl_distance = sl_dist
                        current_tp_price = entry_price + sl_dist * self.config.risk_reward_ratio
                    
                    active_bull_fvg = None # FVG 被使用過後失效
                    
                # 判斷空頭進場：價格反彈到 Bearish FVG 內部
                elif active_bear_fvg and row['high'] >= active_bear_fvg['bottom'] and row['close'] < row['ema_trend']:
                    entry_price = max(row['open'], active_bear_fvg['bottom'])
                    sl_price = active_bear_fvg['sl']
                    
                    sl_dist = sl_price - entry_price
                    sl_pct = sl_dist / entry_price
                    if sl_pct < 0.001: sl_pct = 0.001
                    
                    max_loss_usd = capital * self.config.risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    position_size_usd = min(target_position_size, capital * self.config.max_leverage)
                    
                    if row['high'] >= sl_price:
                        pnl_usd = -max_loss_usd
                        capital += pnl_usd
                        trades.append({'type': 'sl_short_instant', 'pnl_usd': pnl_usd, 'return': -sl_pct})
                    else:
                        position = -1
                        entry_idx = i
                        current_sl_price = sl_price
                        sl_distance = sl_dist
                        current_tp_price = entry_price - sl_dist * self.config.risk_reward_ratio
                        
                    active_bear_fvg = None

            # ==========================================
            # 3. ICT 狀態更新 (偵測新的 FVG)
            # ==========================================
            # FVG 老化或失效
            if active_bull_fvg:
                active_bull_fvg['age'] += 1
                # 如果價格收盤跌破 FVG 底部，代表該 FVG 被破壞 (Mitigated)
                if row['close'] < active_bull_fvg['bottom'] or active_bull_fvg['age'] > self.config.fvg_max_age:
                    active_bull_fvg = None
                    
            if active_bear_fvg:
                active_bear_fvg['age'] += 1
                if row['close'] > active_bear_fvg['top'] or active_bear_fvg['age'] > self.config.fvg_max_age:
                    active_bear_fvg = None
            
            # 偵測這根 K 線確認的新 FVG
            if row['fvg_bull']:
                # SMC 結構止損：設置在創造該 FVG 的這波起漲點 (過去3根K線的最低點)
                sl = min(df['low'].iloc[i], df['low'].iloc[i-1], df['low'].iloc[i-2]) - row['atr'] * 0.2
                active_bull_fvg = {
                    'top': row['fvg_bull_top'],
                    'bottom': row['fvg_bull_bottom'],
                    'sl': sl,
                    'age': 0
                }
                
            if row['fvg_bear']:
                # 結構止損：這波起跌點的最高點
                sl = max(df['high'].iloc[i], df['high'].iloc[i-1], df['high'].iloc[i-2]) + row['atr'] * 0.2
                active_bear_fvg = {
                    'top': row['fvg_bear_top'],
                    'bottom': row['fvg_bear_bottom'],
                    'sl': sl,
                    'age': 0
                }
                    
        # === 統計與返回 ===
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