import numpy as np
import pandas as pd

def run_backtest(model, X, data, config):
    # 预测信号
    if config.model_type == 'xgboost_lstm':
        X_lstm = X.reshape(X.shape[0], X.shape[1], 1)
        predictions = model.predict(X_lstm).argmax(axis=1)
    else:
        predictions = model.predict(X)
    
    # 模拟交易
    capital = config.capital
    position = 0
    trades = []
    account_value = [capital]
    entry_price = 0
    
    # 对齐数据
    trade_data = data.iloc[len(data)-len(X):].reset_index(drop=True)
    
    for i, (pred, close, high, low, atr) in enumerate(zip(predictions, trade_data["close"], trade_data["high"], trade_data["low"], trade_data["atr"])):
        current_value = account_value[-1]
        
        # 做多信号
        if pred == 1 and position == 0:
            # 开多仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = position_size
            stop_loss = entry_price - (atr * 2)  # 动态止损
            trades.append({
                "type": "LONG",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size,
                "stop_loss": stop_loss
            })
        # 做空信号
        elif pred == -1 and position == 0:
            # 开空仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = -position_size
            stop_loss = entry_price + (atr * 2)  # 动态止损
            trades.append({
                "type": "SHORT",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size,
                "stop_loss": stop_loss
            })
        # 平仓信号或止损
        elif position != 0:
            # 检查止损
            if position > 0 and low <= trades[-1]["stop_loss"]:
                # 多仓止损
                exit_price = trades[-1]["stop_loss"]
                profit = (exit_price - entry_price) * position
                current_value += profit
                account_value.append(current_value)
                position = 0
                trades[-1]["exit_time"] = trade_data["open_time"].iloc[i]
                trades[-1]["exit_price"] = exit_price
                trades[-1]["profit"] = profit
                trades[-1]["exit_reason"] = "stop_loss"
            elif position < 0 and high >= trades[-1]["stop_loss"]:
                # 空仓止损
                exit_price = trades[-1]["stop_loss"]
                profit = (entry_price - exit_price) * abs(position)
                current_value += profit
                account_value.append(current_value)
                position = 0
                trades[-1]["exit_time"] = trade_data["open_time"].iloc[i]
                trades[-1]["exit_price"] = exit_price
                trades[-1]["profit"] = profit
                trades[-1]["exit_reason"] = "stop_loss"
            elif pred == 0:
                # 平仓信号
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
                trades[-1]["exit_reason"] = "signal"
    
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
        "total_trades": len(trades),
        "avg_trade_profit": sum(t.get("profit", 0) for t in trades) / len(trades) if trades else 0
    }
    
    return metrics, predictions