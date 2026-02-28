import numpy as np
import pandas as pd
from .features import generate_features

def run_backtest(model, X, data, config, scaler=None):
    # 生成特征数据
    df = generate_features(data)
    feature_columns = [col for col in df.columns if col not in ["open_time", "close_time", "open", "high", "low", "close", "volume", 
                                                               "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", 
                                                               "number_of_trades"]]
    X_features = df[feature_columns]
    
    # 标准化数据
    if scaler is not None:
        X_scaled = scaler.transform(X_features)
    else:
        X_scaled = X_features
    
    # 预测信号
    if config.use_lstm:
        timesteps = 1
        features = X_scaled.shape[1]
        X_lstm = X_scaled.reshape((X_scaled.shape[0], timesteps, features))
        predictions = model.predict(X_lstm).argmax(axis=1)
        # 转换标签：0→-1, 1→0, 2→1
        predictions = predictions - 1
    else:
        predictions = model.predict(X_scaled)
        # 转换标签：0→-1, 1→0, 2→1
        predictions = predictions - 1
    
    # 模拟交易
    capital = config.capital
    position = 0
    trades = []
    account_value = [capital]
    entry_price = 0
    stop_loss_price = 0
    
    # 对齐数据，predictions是X_test的预测结果，对应df的后20%
    trade_data = df.iloc[len(df)-len(predictions):].reset_index(drop=True)
    
    for i, (pred, close, high, low, atr) in enumerate(zip(predictions, trade_data["close"], trade_data["high"], trade_data["low"], trade_data["atr"])):
        current_value = account_value[-1]
        
        # 做多信号
        if pred == 1 and position == 0:
            # 开多仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = position_size
            # 设置动态止损
            if config.dynamic_stop_loss:
                stop_loss_price = entry_price - (atr * config.stop_loss_multiplier)
            trades.append({
                "type": "LONG",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size,
                "stop_loss": stop_loss_price if config.dynamic_stop_loss else None
            })
        # 做空信号
        elif pred == -1 and position == 0:
            # 开空仓
            position_size = (current_value * config.position_pct * config.leverage) / close
            entry_price = close
            position = -position_size
            # 设置动态止损
            if config.dynamic_stop_loss:
                stop_loss_price = entry_price + (atr * config.stop_loss_multiplier)
            trades.append({
                "type": "SHORT",
                "entry_time": trade_data["open_time"].iloc[i],
                "entry_price": entry_price,
                "position_size": position_size,
                "stop_loss": stop_loss_price if config.dynamic_stop_loss else None
            })
        # 平仓信号或止损
        elif position != 0:
            # 检查止损
            stop_loss_triggered = False
            if config.dynamic_stop_loss:
                if position > 0 and low <= trades[-1]["stop_loss"]:
                    # 多仓止损
                    exit_price = trades[-1]["stop_loss"]
                    stop_loss_triggered = True
                elif position < 0 and high >= trades[-1]["stop_loss"]:
                    # 空仓止损
                    exit_price = trades[-1]["stop_loss"]
                    stop_loss_triggered = True
            
            # 平仓信号
            if pred == 0 or stop_loss_triggered:
                if not stop_loss_triggered:
                    exit_price = close
                
                # 计算利润
                if position > 0:
                    profit = (exit_price - entry_price) * position
                else:
                    profit = (entry_price - exit_price) * abs(position)
                
                # 扣除交易成本
                profit -= (entry_price * abs(position) * 0.001)  # 0.1%佣金
                profit -= (abs(exit_price - entry_price) * abs(position) * 0.0005)  # 0.05%滑点
                
                current_value += profit
                account_value.append(current_value)
                position = 0
                
                # 更新交易记录
                trades[-1]["exit_time"] = trade_data["open_time"].iloc[i]
                trades[-1]["exit_price"] = exit_price
                trades[-1]["profit"] = profit
                trades[-1]["exit_reason"] = "stop_loss" if stop_loss_triggered else "signal"
    
    # 计算指标
    final_value = account_value[-1]
    total_return = (final_value - config.capital) / config.capital
    # 计算月化报酬率（假设数据是15m，一天96根，一个月2400根）
    monthly_return = (1 + total_return) ** (2400 / len(trade_data)) - 1
    
    win_trades = [t for t in trades if t.get("profit", 0) > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    
    total_profit = sum(t.get("profit", 0) for t in win_trades)
    total_loss = sum(abs(t.get("profit", 0)) for t in trades if t.get("profit", 0) < 0)
    profit_factor = total_profit / total_loss if total_loss != 0 else 0
    
    # 计算最大回撤
    peak = account_value[0]
    max_drawdown = 0
    drawdown_history = []
    for value in account_value:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        drawdown_history.append(drawdown)
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    metrics = {
        "total_return": total_return,
        "monthly_return": monthly_return,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "total_trades": len(trades),
        "avg_trade_profit": sum(t.get("profit", 0) for t in trades) / len(trades) if trades else 0,
        "final_account_value": final_value
    }
    
    return metrics, predictions, account_value, trades