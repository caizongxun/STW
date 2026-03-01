import pandas as pd
import numpy as np
from datetime import timedelta

class V6Backtester:
    """V6 資金費率套利回測引擎"""
    
    def __init__(self, config):
        self.config = config
        
    def run(self, df, fe):
        print("[V6] Running Funding Rate Arbitrage Strategy...")
        
        # 生成特徵
        df = fe.generate(df)
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'])
        
        # 裁切回測區間
        if self.config.simulation_days > 0 and 'open_time' in df.columns:
            end_time = df['open_time'].max()
            start_time = end_time - timedelta(days=self.config.simulation_days)
            df = df[df['open_time'] >= start_time].reset_index(drop=True)
            print(f"[V6] 回測區間: {start_time.date()} 至 {end_time.date()}")
        
        capital = self.config.capital
        positions = []  # 當前套利倉位
        equity_curve = []
        funding_collections = 0
        total_funding_earned = 0
        
        start_time = df['open_time'].iloc[0] if 'open_time' in df.columns else None
        end_time = df['open_time'].iloc[-1] if 'open_time' in df.columns else None
        
        for i in range(len(df)):
            row = df.iloc[i]
            equity_curve.append(capital)
            
            if capital < self.config.capital * 0.1:
                break
            
            # ==========================================
            # 1. 檢查現有套利倉位，收取資金費率
            # ==========================================
            for pos in positions:
                # 每根 K 線（8 小時）結算一次資金費率
                funding_rate = row['simulated_funding_rate']
                
                if funding_rate > 0:
                    # 資金費率為正：多頭支付空頭，我們做空合約收錢
                    funding_income = pos['position_size'] * funding_rate
                    capital += funding_income
                    total_funding_earned += funding_income
                    funding_collections += 1
                    pos['total_earned'] += funding_income
                else:
                    # 資金費率為負：空頭支付多頭，我們虧損
                    funding_loss = pos['position_size'] * abs(funding_rate)
                    capital -= funding_loss
                    pos['total_earned'] -= funding_loss
                
                pos['holding_bars'] += 1
            
            # ==========================================
            # 2. 檢查是否需要平倉
            # ==========================================
            positions_to_close = []
            for pos in positions:
                # 平倉條件 1：資金費率轉負且持續虧損
                if row['simulated_funding_rate'] < 0 and pos['total_earned'] < 0:
                    positions_to_close.append(pos)
                
                # 平倉條件 2：基差過大（對沖失效風險）
                elif abs(row['basis']) > self.config.max_basis_pct:
                    positions_to_close.append(pos)
                
                # 平倉條件 3：達到目標收益（例如賺取 2% 就離場）
                elif pos['total_earned'] / pos['position_size'] > 0.02:
                    positions_to_close.append(pos)
            
            for pos in positions_to_close:
                # 平倉手續費
                close_fee = pos['position_size'] * (self.config.spot_fee_rate + self.config.futures_fee_rate)
                capital -= close_fee
                positions.remove(pos)
            
            # ==========================================
            # 3. 檢查是否開啟新的套利倉位
            # ==========================================
            if len(positions) < self.config.max_positions:
                funding_rate = row['simulated_funding_rate']
                basis = row['basis']
                
                # 開倉條件：
                # 1. 資金費率 > 最低閾值
                # 2. 基差在合理範圍內
                if funding_rate > self.config.min_funding_rate and abs(basis) < self.config.max_basis_pct:
                    # 計算套利倉位大小
                    position_size = capital * self.config.allocation_pct
                    
                    # 開倉手續費（現貨買入 + 合約開空）
                    open_fee = position_size * (self.config.spot_fee_rate + self.config.futures_fee_rate)
                    capital -= open_fee
                    
                    positions.append({
                        'entry_idx': i,
                        'position_size': position_size,
                        'entry_funding_rate': funding_rate,
                        'total_earned': 0,
                        'holding_bars': 0
                    })
        
        # ==========================================
        # 4. 計算統計指標
        # ==========================================
        total_return = (capital - self.config.capital) / self.config.capital * 100
        
        days_diff = 0
        monthly_return = 0
        if start_time and end_time:
            days_diff = (end_time - start_time).days
            if days_diff > 0:
                monthly_return = total_return / (days_diff / 30.0)
        
        avg_funding_rate = total_funding_earned / funding_collections if funding_collections > 0 else 0
        
        return {
            'final_capital': capital,
            'return_pct': total_return,
            'monthly_return': monthly_return,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'days_tested': days_diff,
            'funding_collections': funding_collections,
            'avg_funding_rate': avg_funding_rate / self.config.capital if avg_funding_rate > 0 else 0,
            'total_funding_earned': total_funding_earned
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