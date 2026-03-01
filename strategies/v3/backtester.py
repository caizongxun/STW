import pandas as pd
import numpy as np

class V3Backtester:
    def __init__(self, config):
        self.config = config
        
    def run(self, df, long_model, short_model, fe):
        print("[V3] Running Trend-Aligned Reversal Strategy with Fixed Risk...")
        
        df = fe.generate(df)
        X = df[fe.get_feature_names(df)]
        
        df['long_prob'] = long_model.predict_proba(X)[:, 1]
        df['short_prob'] = short_model.predict_proba(X)[:, 1]
        
        capital = self.config.capital
        position = 0
        entry_price = 0
        entry_idx = 0
        last_exit_idx = -self.config.cooldown_bars
        position_size_usd = 0 # 實際開倉的美元價值
        
        trades = []
        equity_curve = []
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            # 破產保護 (資本低於10%停止)
            if capital < self.config.capital * 0.1:
                break
                
            total_fee_rate = self.config.fee_rate + self.config.slippage
            
            # === 平倉邏輯 ===
            if position > 0:
                current_profit_pct = (row['high'] - entry_price) / entry_price
                dynamic_sl = entry_price - row['atr'] * self.config.atr_sl_multiplier
                
                # 保本推移：當獲利超過 1.5 倍 ATR，止損線上移至成本價 + 手續費
                if current_profit_pct > (row['atr'] * 1.5 / entry_price):
                    dynamic_sl = max(dynamic_sl, entry_price * (1 + total_fee_rate * 2))
                
                # 止損觸發
                if row['low'] < dynamic_sl:
                    exit_price = dynamic_sl
                    pnl_pct = (exit_price - entry_price) / entry_price
                    # 計算實際盈虧金額
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_long', 'pnl_usd': pnl_usd, 'capital': capital})
                    
                # 止盈觸發
                elif row['high'] > entry_price + row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price + row['atr'] * self.config.atr_tp_multiplier
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_long', 'pnl_usd': pnl_usd, 'capital': capital})
                    
                # 時間平倉
                elif i - entry_idx >= self.config.t_events_bars:
                    exit_price = row['close']
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_long', 'pnl_usd': pnl_usd, 'capital': capital})
                    
            elif position < 0:
                current_profit_pct = (entry_price - row['low']) / entry_price
                dynamic_sl = entry_price + row['atr'] * self.config.atr_sl_multiplier
                
                if current_profit_pct > (row['atr'] * 1.5 / entry_price):
                    dynamic_sl = min(dynamic_sl, entry_price * (1 - total_fee_rate * 2))
                    
                # 止損
                if row['high'] > dynamic_sl:
                    exit_price = dynamic_sl
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'sl_short', 'pnl_usd': pnl_usd, 'capital': capital})
                    
                # 止盈
                elif row['low'] < entry_price - row['atr'] * self.config.atr_tp_multiplier:
                    exit_price = entry_price - row['atr'] * self.config.atr_tp_multiplier
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'tp_short', 'pnl_usd': pnl_usd, 'capital': capital})
                    
                # 時間平倉
                elif i - entry_idx >= self.config.t_events_bars:
                    exit_price = row['close']
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_usd = position_size_usd * pnl_pct - (position_size_usd * total_fee_rate * 2)
                    capital += pnl_usd
                    position = 0
                    last_exit_idx = i
                    trades.append({'type': 'time_short', 'pnl_usd': pnl_usd, 'capital': capital})
                    
            # === 開倉邏輯 (順勢接刀) ===
            if position == 0 and (i - last_exit_idx) >= self.config.cooldown_bars:
                
                # 宏觀趨勢判定：EMA50 與 EMA200 的多空排列
                uptrend = row['close'] > row['ema_200'] and row['ema_50'] > row['ema_200']
                downtrend = row['close'] < row['ema_200'] and row['ema_50'] < row['ema_200']
                
                if not self.config.use_trend_filter:
                    uptrend = downtrend = True
                
                # 進場條件：AI 判定反轉 + 符合大趨勢 (回調買入) + 遠離布林帶中軌(證明有跌/漲過一段)
                long_cond = (
                    row['long_prob'] > self.config.signal_threshold and 
                    uptrend and 
                    row['bb_position'] < 0.3 # 價格在布林帶下半部 (回調)
                )
                
                short_cond = (
                    row['short_prob'] > self.config.signal_threshold and 
                    downtrend and 
                    row['bb_position'] > 0.7 # 價格在布林帶上半部 (反彈)
                )
                
                if long_cond or short_cond:
                    # == 固定風險倉位管理 (Fixed Risk Position Sizing) ==
                    # 計算如果打到止損，價格會跌/漲幾 %
                    sl_distance_price = row['atr'] * self.config.atr_sl_multiplier
                    sl_pct = sl_distance_price / row['close']
                    
                    # 我們願意在這筆交易中虧損的絕對金額
                    max_loss_usd = capital * self.config.risk_per_trade
                    
                    # 反推應該開多大的倉位：倉位價值 * 止損% = 預期虧損
                    # 這樣不管波動多大，打止損我們永遠只虧 capital * risk_per_trade
                    target_position_size = max_loss_usd / (sl_pct + total_fee_rate * 2)
                    
                    # 限制最大槓桿 (保護機制，避免波動極小時開出幾百倍槓桿)
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