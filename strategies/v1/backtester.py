import numpy as np
import pandas as pd

def run_backtest(model, X, data, config):
    # 预测信号
    predictions = model.predict(X)
    
    # 模拟交易
    capital = config.capital
    position = 0
    trades = []
    account_value = [capital]
    
    # 对齐数据
    trade_data = data.iloc[len(data)-len(X):].reset_index(drop=True)
    
    for i, (pred, close) in enumerate(zip(predictions, trade_data["close"])):
        current_value = account_value[-1]
        
        # 做多信号
        if pred == 1 and position == 0:
            # 开多仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = position_size
            trades.append({
                "type": "LONG",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size
            })
        # 做空信号
        elif pred == -1 and position == 0:
            # 开空仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = -position_size
            trades.append({
                "type": "SHORT",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size
            })
        # 平仓信号
        elif pred == 0 and position != 0:
            # 平仓
            exit_price = close
            if position > 0:
                profit = (exit_price - entry_price) * position
            else:
                profit = (entry_price - exit_price) * abs(position)
            
            current_value += profit
            account_value.append(current_value)
            position = 0
            trades[-1]["exit_time"] = trade_data["open_time"].iloc[i]
            trades[-1]["exit_price"] = exit_price
            trades[-1]["profit"] = profit
    
    # 计算指标
    final_value = account_value[-1]
    total_return = (final_value - config.capital) / config.capital
    monthly_return = (1 + total_return) ** (30 / len(trade_data)) - 1
    
    win_trades = [t for t in trades if t.get("profit", 0) > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    
    total_profit = sum(t.get("profit", 0) for t in win_trades)
    total_loss = sum(abs(t.get("profit", 0)) for t in trades if t.get("profit", 0) < 0)
    profit_factor = total_profit / total_loss if total_loss != 0 else 0
    
    # 计算最大回撤
    peak = account_value[0]
    max_drawdown = 0
    for value in account_value:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    metrics = {
        "total_return": total_return,
        "monthly_return": monthly_return,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "total_trades": len(trades)
    }
    
    return metrics, predictions