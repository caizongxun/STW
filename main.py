# Smart Trading Terminal (STT) - 命令行入口
import argparse
from strategies import AVAILABLE_VERSIONS

def main():
    parser = argparse.ArgumentParser(description="Smart Trading Terminal (STT) 命令行工具")
    parser.add_argument("--version", required=True, help="策略版本 (v1-v6)")
    parser.add_argument("--action", required=True, choices=["train", "backtest"], help="操作类型")
    args = parser.parse_args()
    
    strategy = AVAILABLE_VERSIONS[args.version]
    
    if args.action == "train":
        # 执行训练
        strategy.train()
    elif args.action == "backtest":
        # 执行回测
        strategy.backtest()

if __name__ == "__main__":
    main()