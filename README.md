# STW - Smart Trading Workshop

AI驅動的加密貨幣交易系統，由 DeepSeek-R1 提供智能決策

---

## 核心特色

### V13 - DeepSeek-R1 AI 交易系統

**智能引擎**
- DeepSeek-R1 14B 本地推理 (離線運行，無API費用)
- Chain-of-Thought 多步驟推理能力
- 自動案例相似度匹配算法

**學習案例系統**
- 40+ 技術指標完整特徵：趨勢/動能/波動/成交量/支撐壓力
- 自動案例提取：從歷史數據識別獲利 > 1% 的交易
- 視覺化管理：查看/編輯/刪除/批量導入學習案例
- 指標趨勢追蹤：完整記錄進場前5根K棒的指標變化

**實時交易**
- 精確進場/止損/止盈價格
- 盈虧比自動計算 (基於ATR)
- 風險警示與等待條件

**V2 增強功能 (NEW)**
- K棒序列比對：比對當前與成功案例的前5根K棒變化趨勢
- 已完成K棒判斷：只使用已完成的K棒，避免信號反覆跳動
- 倉位管理：自動追蹤持倉、資金、交易歷史
- 新聞整合：實時獲取新聞並進行情緒分析
- 智能風控：連續虧搃20筆自動暫停交易

---

## 快速開始

### 1. 環境建置

```bash
# 克隆僉庫
git clone https://github.com/caizongxun/STW.git
cd STW

# 安裝依賴
pip install -r requirements.txt
```

### 2. 安裝 Ollama 與 DeepSeek-R1

```bash
# Windows: 下載 https://ollama.com/download
# Mac/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 下載 DeepSeek-R1 14B 模型
ollama pull deepseek-r1:14b

# 驗證安裝
ollama run deepseek-r1:14b
# 輸入測試問題，按 Ctrl+D 離開
```

### 3. 啟動系統

```bash
streamlit run app.py
```

瀏覽器會自動打開 `http://localhost:8501`

---

## 使用指南

### 建立學習案例庫 (必要步驟)

1. **進入「學習案例庫」頁籤**
2. **點擊「批量導入」分頁**
3. **配置參數**：
   - 幣種: `BTCUSDT`
   - 時間框架: `1h`
   - 歷史天數: `90` 天
   - 最低獲利: `1.0%`
4. **點擊「開始提取」**

系統會自動：
- 載入90天歷史K線數據
- 計算40+技術指標
- 模擬交易並篩選獲利 > 1% 的案例
- 提取進場時刻完整特徵並儲存到 `data/detailed_success_cases.json`

**建議**：
- 第一次使用至少提取 **20-30 個案例**
- 不同幣種 (BTC/ETH/SOL) 各提取10-20個
- 保持 LONG:SHORT = 1:1 平衡

### 獲取實時AI信號

1. **選擇幣種與時間框架**
2. **勾選「使用強化AI引擎」** (推薦)
3. **點擊「獲取實時AI信號」**

DeepSeek會：
- 分析當前市場的40+技術指標
- 自動匹配最相似的5個成功案例
- 比對RSI/BB_position/volume_ratio等關鍵特徵
- 給出LONG/SHORT/HOLD決策 + 精確價位

**顯示資訊**：
- 進場價/止損/止盈
- 盈虧比 (1:2 或更高)
- 信心度 (0-100%)
- 匹配的案例清單
- 完整推理過程

### 進階: V2增強引擎使用

```python
from core.llm_agent_v2 import EnhancedDeepSeekAgentV2
from core.portfolio_manager import PortfolioManager
from core.data_loader import DataLoader

# 初始化
portfolio = PortfolioManager(initial_capital=10000)
agent = EnhancedDeepSeekAgentV2(
    portfolio_manager=portfolio,
    enable_news=True  # 啟用新聞分析
)

# 載入數據
loader = DataLoader()
df = loader.load_data('BTCUSDT', '1h')

# 獲取交易信號
decision = agent.analyze_market(
    df=df,
    symbol='BTCUSDT',
    current_prices={'BTCUSDT': 65000}
)

print(f"Signal: {decision['signal']}")
print(f"Confidence: {decision['confidence']}%")
print(f"Entry: ${decision['entry_price']}")
print(f"Matched Cases: {decision['matched_cases']}")

# 如果信號為LONG且信心度高
if decision['signal'] == 'LONG' and decision['confidence'] > 70:
    can_trade, reason = portfolio.can_open_position(1000)
    if can_trade:
        trade_id = portfolio.open_position(
            symbol='BTCUSDT',
            side='LONG',
            entry_price=decision['entry_price'],
            size=1000,
            stop_loss=decision['stop_loss'],
            take_profit=decision['take_profit'],
            ai_confidence=decision['confidence']
        )
        print(f"Opened position: {trade_id}")
```

---

## 文件結構

```
STW/
├── app.py                      # 主程式
├── core/
│   ├── llm_agent.py            # 基礎DeepSeek引擎
│   ├── llm_agent_enhanced.py   # V1強化版 (40+指標)
│   ├── llm_agent_v2.py         # V2全功能版 (NEW)
│   ├── case_extractor.py       # 案例提取器
│   ├── market_analyzer.py      # 市場分析器 (NEW)
│   ├── portfolio_manager.py    # 倉位管理器 (NEW)
│   ├── news_fetcher.py         # 新聞獲取器 (NEW)
│   └── data_loader.py          # Binance數據載入器
├── strategies/
│   └── v13/
│       ├── __init__.py         # V13主GUI
│       ├── case_manager.py     # 案例管理器GUI
│       ├── config.py           # 配置檔
│       └── backtester.py       # 回測引擎
└── data/
    ├── detailed_success_cases.json  # 學習案例庫
    └── portfolio_state.json         # 倉位狀態 (NEW)
```

---

## V2 新功能詳解

### 1. K棒序列比對

**問題**：之前只看單根K棒的指標快照，沒有利用序列變化趨勢。

**解決**：
```python
# 現在會提取前5根K棒的序列
recent_sequence = [
    {'position': -5, 'rsi': 45, 'volume_ratio': 1.2},
    {'position': -4, 'rsi': 38, 'volume_ratio': 1.4},
    {'position': -3, 'rsi': 34, 'volume_ratio': 1.6},
    {'position': -2, 'rsi': 32, 'volume_ratio': 1.8},
    {'position': -1, 'rsi': 35, 'volume_ratio': 1.85},
]

indicator_trends = {
    'rsi': {'trend': 'falling', 'slope': -2.5, 'change': -10},
    'volume_ratio': {'trend': 'rising', 'slope': 0.15, 'change': 0.65}
}
```

AI會比對：
- 案例庫："RSI從45持續下降到32，然後反彈到35"
- 當前市場："RSI是否也呈現相同的下降後反彈模式？"

### 2. 已完成K棒判断

**問題**：使用未完成的K棒，價格每秒變動會導致信號反覆跳動。

**解決**：
```python
market_analyzer = MarketAnalyzer(use_completed_candles_only=True)

# 自動排除最後一根未完成的K棒
features = market_analyzer.prepare_market_features(df, 'BTCUSDT')
# Output: "Using completed candles only: 8640 bars (excluded last incomplete candle)"
```

**調用頻率建議**：
- 1小時K：每小時整點後5分鐘調用一次
- 15分鐘K：每15分鐘後1-2分鐘調用

### 3. 倉位管理

**功能**：
- 自動追蹤持倉、資金、交易歷史
- 持久化到 `data/portfolio_state.json`
- 提供給AI的倉位上下文

**使用示例**：
```python
portfolio = PortfolioManager(initial_capital=10000)

# 開倉
trade_id = portfolio.open_position(
    symbol='BTCUSDT',
    side='LONG',
    entry_price=65000,
    size=1000,
    stop_loss=64000,
    take_profit=67000
)

# 檢查止盈/止損
to_close = portfolio.check_stop_conditions({'BTCUSDT': 67500})
for item in to_close:
    portfolio.close_position(item['trade_id'], item['exit_price'], item['exit_reason'])

# 獲取績效
summary = portfolio.get_performance_summary()
print(f"Win Rate: {summary['win_rate']}%")
print(f"Total Return: {summary['total_return_pct']}%")
```

**智能風控**：
- 連續虧搃20筆 → 自動暫停交易
- 資金使用率 > 80% → 提高信心門檻到85%
- 可用資金不足 → 拒絕開倉

### 4. 新聞整合

**功能**：
- 從 CryptoPanic API 獲取最近24小時新聞
- 自動情緒分析 (bullish/bearish/neutral)
- 根據新聞調整AI信心度

**使用示例**：
```python
from core.news_fetcher import CryptoNewsFetcher

fetcher = CryptoNewsFetcher()
news = fetcher.fetch_recent_news('BTC', hours=24)
sentiment = fetcher.analyze_sentiment(news)

print(f"Sentiment: {sentiment['sentiment']}")
print(f"Score: {sentiment['total_score']}")
print(f"News Count: {sentiment['news_count']}")
```

**決策邏輯**：
- 技術面LONG + 新聞Bullish → 信心度 +10%
- 技術面LONG + 新聞強烈Bearish → 放棄交易
- 技術面SHORT + 新聞強烈Bullish → 放棄交易

---

## 性能調整

### Ollama 推理速度

| GPU | 速度 (tokens/秒) | VRAM |
|-----|---------------------|------|
| RTX 4090 | 8-12 | 12GB |
| RTX 3090 | 5-8 | 12GB |
| RTX 3060 | 2-3 | 8GB |
| CPU Only | 0.5-1 | N/A |

**優化建議**：
```bash
# 降低輸出長度以提速 (預設2048)
ollama run deepseek-r1:14b --num-predict 1024
```

### 案例數量調整

在 `core/llm_agent_v2.py` 修改：
```python
def analyze_market(self, df, symbol, current_prices, max_cases=5):
    # 改為 3 提速，改為 10 提高精度
```

---

## 常見問題

### Q1: DeepSeek 推理太慢怎麼辦？

**A**: 
1. 確保Ollama正在使用GPU: `nvidia-smi` 查看VRAM使用
2. 降低Prompt長度：減少案例數量到3個
3. 減少輸出長度：`num_predict=1024`

### Q2: 提取不到案例怎麼辦？

**A**:
1. 降低最低獲利%：從1.0%改為0.5%
2. 增加歷史天數：從90天改為180天
3. 檢查Binance API連接是否正常

### Q3: AI給出的信號太保守 (總是HOLD)？

**A**:
1. 增加更多案例：至少50+個
2. 降低信心門檻：從70%改為60%
3. 確保案例包含不同市場環境 (超買/超賨/震盪)

### Q4: 如何備份學習案例？

**A**:
```bash
cp data/detailed_success_cases.json data/backup_cases_$(date +%Y%m%d).json
cp data/portfolio_state.json data/backup_portfolio_$(date +%Y%m%d).json
```

---

## 依賴套件

```txt
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
ta-lib>=0.4.28
plotly>=5.18.0
langchain>=0.1.0
langchain-ollama>=0.1.0
requests>=2.31.0
```

---

## 授權

MIT License

---

## 責任聲明

風險警告：
- 本系統僅供教育與研究使用
- 加密貨幣交易具有高風險，請勿投入超過您可承受的損失金額
- AI決策不保證獲利，請結合自身判斷使用
- 建議先在模擬環境充分測試後再考慮實盤

---

## 聯系方式

- GitHub Issues: https://github.com/caizongxun/STW/issues
- 作者: zong
- Email: 69517696+caizongxun@users.noreply.github.com

---

立即開始你的AI交易之旅
