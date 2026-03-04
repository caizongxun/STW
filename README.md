# STW - Smart Trading Workshop

🤖 AI驅動的加密貨幣交易系統，由 DeepSeek-R1 提供智能決策

---

## 🌟 核心特色

### V13 - DeepSeek-R1 AI 交易系統

**🧠 智能引擎**
- DeepSeek-R1 14B 本地推理（離線運行，無API費用）
- Chain-of-Thought 多步驟推理的力
- 自動案例相似度匹配算法

**📚 學習案例系統（核心功能）**
- **40+ 技術指標完整特徵**：趨勢/動能/波動/成交量/支撐壓力
- **自動案例提取**：從歷史數據識別獲利 > 1% 的交易
- **視覺化管理**：查看/編輯/刪除/批量導入學習案例
- **指標趨勢追蹤**：完整記錄進場前5根K棒的指標變化

**📈 實時交易**
- 精確進場/止損/止盈價格
- 盈虧比自動計算（基於ATR）
- 風險警示與等待條件

---

## 🚀 快速開始

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

## 📖 使用指南

### ➕ 建立學習案例庫（必要步驟）

1. **進入「學習案例庫」頁籤**
2. **點擊「批量導入」分頁**
3. **配置參數**：
   - 幣種：`BTCUSDT`
   - 時間框架：`1h`
   - 歷史天數：`90` 天
   - 最低獲利：`1.0%`
4. **點擊「開始提取」**

系統會自動：
- 載入90天歷史K線數據
- 計算40+技術指標
- 模擬交易並篩選獲利 > 1% 的案例
- 提取進場時刻完整特徵並儲存到 `data/detailed_success_cases.json`

**建議：**
- 第一次使用至少提取 **20-30 個案例**
- 不同幣種（BTC/ETH/SOL）各提取10-20個
- 保持 LONG:SHORT ≈ 1:1 平衡

### 🔍 獲取實時AI信號

1. **選擇幣種與時間框架**
2. **勾選「使用強化AI引擎」**（推薦）
3. **點擊「獲取實時AI信號」**

DeepSeek會：
- 分析當前市場的40+技術指標
- 自動匹配最相似的5個成功案例
- 比對RSI/BB_position/volume_ratio等關鍵特徵
- 給出LONG/SHORT/HOLD決策 + 精確價位

**顯示資訊**：
- 進場價/止損/止盈
- 盈虧比（1:2 或更高）
- 信心度（0-100%）
- 匹配的案例清單
- 完整推理過程

### 📈 進階：查看案例詳情

1. **進入「案例列表」分頁**
2. **點擊展開任意案例**

每個案例包含：
- **基礎資訊**：進場/出場價、持倉時間、獲利率
- **進場邏輯**：自動生成的決策描述（例："RSI超賨 + 成交量爆發 + 布林下軌反彈"）
- **指標趨勢**：進場前5根K棒的RSI/MACD/成交量變化軌跡
- **完整指標快照**：進場時刻的40+指標數值

---

## 📁 文件結構

```
STW/
├── app.py                      # 主程式
├── core/
│   ├── llm_agent.py            # 基礎DeepSeek引擎
│   ├── llm_agent_enhanced.py   # 強化版AI引擎（支揷40+指標）
│   ├── case_extractor.py       # 案例提取器
│   └── data_loader.py          # Binance數據載入器
├── strategies/
│   └── v13/
│       ├── __init__.py         # V13主GUI
│       ├── case_manager.py     # 案例管理器GUI
│       ├── config.py           # 配置檔
│       └── backtester.py       # 回測引擎
└── data/
    └── detailed_success_cases.json  # 學習案例庫
```

---

## 💡 核心技術

### 案例相似度匹配算法

```python
# 權重設定（可調整）
weights = {
    'rsi': 2.0,           # RSI是最關鍵的動能指標
    'bb_position': 2.0,   # 布林帶位置顯示超買/超賨
    'volume_ratio': 1.5,  # 成交量爆發確認動能
    'macd_hist': 1.5,     # MACD柱狀圖轉折點
    'adx': 1.0            # 趨勢強度
}

# 歐氏距離計算
score = sum(weight * (1 - normalized_diff) for each indicator)

# 返回 Top 5 最相似案例
```

### 40+ 技術指標分類

| 類別 | 指標 | 數量 |
|------|------|------|
| **趨勢** | EMA9/21/50/200, MACD, MACD Signal, MACD Hist, ADX | 8 |
| **動能** | RSI, Stochastic K/D, CCI, MFI, Williams %R, ROC | 6 |
| **波動** | ATR, Bollinger Bands (Upper/Middle/Lower), BB Position | 5 |
| **成交量** | Volume MA, Volume Ratio, OBV, AD | 4 |
| **價格結構** | High/Low 20, Distance from High/Low, Pivot Points | 5 |
| **市場微觀** | Body%, Shadows, Consecutive Bull/Bear Candles | 6 |
| **多週期** | Price Change 5/10, Volatility, Volume Trend | 4 |
| **支撐壓力** | Resistance/Support Levels, Distance to R/S | 4 |

---

## ⚡ 性能調整

### Ollama 推理速度

| GPU | 速度 (tokens/秒) | VRAM |
|-----|---------------------|------|
| RTX 4090 | 8-12 | 12GB |
| RTX 3090 | 5-8 | 12GB |
| RTX 3060 | 2-3 | 8GB |
| CPU Only | 0.5-1 | N/A |

**優化建議**：
```bash
# 降低數量以提速（預設2048）
ollama run deepseek-r1:14b --num-predict 1024
```

### 案例數量調整

在 `core/llm_agent_enhanced.py` 修改：
```python
def analyze_market(self, current_market: Dict, max_cases: int = 5):
    # 改為 3 提速，改為 10 提高精度
```

---

## 🔧 常見問題

### Q1: DeepSeek 推理太慢怎麼辦？

**A:** 
1. 確保Ollama正在使用GPU：`nvidia-smi` 查看VRAM使用
2. 降低Prompt長度：減少案例數量到3個
3. 減少輸出長度：`num_predict=1024`

### Q2: 提取不到案例怎麼辦？

**A:**
1. 降低最低獲利%：從1.0%改為0.5%
2. 增加歷史天數：從90天改為180天
3. 檢查Binance API連接是否正常

### Q3: AI給出的信號太保守（總是HOLD）？

**A:**
1. 增加更多案例：至少50+個
2. 降低信心門檻：從70%改為60%
3. 確保案例包含不同市場環境（超買/超賨/震盪）

### Q4: 如何備份學習案例？

**A:**
```bash
cp data/detailed_success_cases.json data/backup_cases_$(date +%Y%m%d).json
```

---

## 📦 依賴套件

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

## 📝 授權

MIT License

---

## 👥 責任聲明

⚠️ **風險警告**：
- 本系統僅供教育與研究使用
- 加密貨幣交易具有高風險，請勿投入超過您可承受的損失金額
- AI決策不保證獲利，請結合自身判斷使用
- 建議先在模擬環境充分測試後再考慮實盤

---

## 📧 聯系方式

- GitHub Issues: [https://github.com/caizongxun/STW/issues](https://github.com/caizongxun/STW/issues)
- 作者: zong
- Email: 69517696+caizongxun@users.noreply.github.com

---

**🎉 立即開始你的AI交易之旅！**
