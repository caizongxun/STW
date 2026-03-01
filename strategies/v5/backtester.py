import pandas as pd
import numpy as np
from datetime import timedelta

class V5Backtester:
    """V5 配對交易回測引擎 (優化版)"""
    
    def __init__(self, config):
        self.config = config
        
    def run(self, df_long, df_short, fe):
        print("[V5] Running Optimized Pairs Trading Strategy...")
        
        df = fe.generate(df_long, df_short)
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
        
        if self.config.simulation_days > 0 and 'open_time' in df.columns:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
            print(f"[V5] 回測區間: {start_time.date()} 至 {end_time.date()}")
        
        capital = self.config.capital
        positions = []
        trades = []
        equity_curve = []
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        total_fee_rate = self.config.fee_rate + self.config.slippage
        last_exit_idx = -self.config.cooldown_bars
        
        for i in range(len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital < self.config.capital * 0.1:
                break
            
            # ==========================================
            # 1. 檢查現有倉位是否需要平倉
            # ==========================================
            positions_to_close = []
            for pos in positions:
                current_zscore = row['zscore']
                holding_bars = i - pos['entry_idx']
                
                # 出場條件 1：Z-Score 回歸到出場閾值
                if abs(current_zscore) < self.config.exit_zscore:
                    positions_to_close.append(pos)
                    
                # 出場條件 2：Z-Score 持續偏離，觸發止損
                elif abs(current_zscore) > self.config.stop_zscore:
                    if (pos['direction'] == 'long_spread' and current_zscore > 0) or \
                       (pos['direction'] == 'short_spread' and current_zscore < 0):
                        positions_to_close.append(pos)
                
                # 出場條件 3：持倉過久，強制平倉
                elif holding_bars > self.config.max_holding_bars:
                    positions_to_close.append(pos)
            
            for pos in positions_to_close:
                exit_price_long = row['price_long']
                exit_price_short = row['price_short']
                
                if pos['direction'] == 'long_spread':
                    pnl_long = (exit_price_long - pos['entry_price_long']) / pos['entry_price_long']
                    pnl_short = (pos['entry_price_short'] - exit_price_short) / pos['entry_price_short']
                else:
                    pnl_long = (pos['entry_price_long'] - exit_price_long) / pos['entry_price_long']
                    pnl_short = (exit_price_short - pos['entry_price_short']) / pos['entry_price_short']
                
                avg_pnl = (pnl_long + pnl_short) / 2
                pnl_usd = pos['position_size'] * avg_pnl - (pos['position_size'] * total_fee_rate * 4)
                
                capital += pnl_usd
                positions.remove(pos)
                last_exit_idx = i
                
                trades.append({
                    'type': f"close_{pos['direction']}",
                    'pnl_usd': pnl_usd,
                    'return': avg_pnl,
                    'capital': capital,
                    'holding_bars': i - pos['entry_idx']
                })
            
            # ==========================================
            # 2. 檢查是否有新的開倉機會
            # ==========================================
            if len(positions) < self.config.max_positions and (i - last_exit_idx) >= self.config.cooldown_bars:
                current_zscore = row['zscore']
                zscore_change = row.get('zscore_change', 0)
                
                direction = None
                
                # 加入動量確認：只有當 Z-Score 開始向均值回歸時才開倉
                if current_zscore > self.config.entry_zscore:
                    # Z-Score 過高，且開始下降（回歸）
                    if self.config.use_momentum_filter:
                        if zscore_change < 0:  # Z-Score 正在下降
                            direction = 'short_spread'
                    else:
                        direction = 'short_spread'
                        
                elif current_zscore < -self.config.entry_zscore:
                    # Z-Score 過低，且開始上升（回歸）
                    if self.config.use_momentum_filter:
                        if zscore_change > 0:  # Z-Score 正在上升
                            direction = 'long_spread'
                    else:
                        direction = 'long_spread'
                
                if direction:
                    max_loss_usd = capital * self.config.risk_per_trade
                    position_size = min(max_loss_usd / 0.05, capital * self.config.max_leverage)
                    
                    positions.append({
                        'direction': direction,
                        'entry_idx': i,
                        'entry_price_long': row['price_long'],
                        'entry_price_short': row['price_short'],
                        'entry_zscore': current_zscore,
                        'position_size': position_size
                    })
        
        # 計算統計
        wins = len([t for t in trades if t['pnl_usd'] > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        total_return = (capital - self.config.capital) / self.config.capital * 100
        
        days_diff = 0
        monthly_return = 0
        if start_time and end_time:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
        
        avg_holding_hours = 0
        if trades:
            bars_per_hour = 1 if self.config.timeframe == '1h' else (4 if self.config.timeframe == '15m' else 0.25)
            avg_holding_bars = np.mean([t['holding_bars'] for t in trades if 'holding_bars' in t])
            avg_holding_hours = avg_holding_bars / bars_per_hour
        
        avg_leverage = self.config.max_leverage * 0.5
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'total_trades': total,
            'win_rate': win_rate * 100,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'days_tested': days_diff,
            'avg_leverage': avg_leverage,
            'avg_holding_hours': avg_holding_hours
        }
    
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