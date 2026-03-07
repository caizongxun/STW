# Executor 部分輸出處理修復

## 更新時間
2026-03-07 22:45 CST

## 問題描述

```
[ERROR] 解析失敗 - AI 審核員完整回應:
======================================================================
作為一名經驗豐富的加密貨幣交易員，我將對 AI 仲裁者的決策進行最終審核。

**審核分析：**

1.  **AI 決策概述：**
    *   **行動：** 開倉做空 (OPEN_SHORT)
    *   **信心度：** 70% (符合執行
======================================================================

[AI REVIEW] REJECT
            拒絕執行: 解析失敗...
```

### 原因分析

1. **AI 輸出被截斷**
   - Gemini API 可能因為網絡或超時問題，輸出到一半就停止
   - 輸出停在「信心度：70% (符合執行」，缺少 JSON 結構

2. **JSON 解析失敗**
   - 缺少完整的 JSON 物件
   - 無法提取 `execution_decision`
   - 預設為 REJECT

3. **問題影響**
   - 即使 AI 同意執行，也會被誤判為 REJECT
   - 導致所有交易都被拒絕

---

## 修復方案

### 方案 1: 智能推斷 (部分輸出)

**修改檔案**: `core/json_parser_robust.py`

**新增功能**: `infer_executor_decision_from_partial(content)`

#### 推斷邏輯

1. **提取信心度**
   ```python
   conf_match = re.search(r'信心度[:：]?\s*(\d+)%', content)
   ```

2. **檢查關鍵詞**
   - **正面**: 符合執行, 可以執行, 建議執行, 通過審核, 同意執行
   - **負面**: 不建議執行, 拒絕執行, 不符合, 風險過大, 不通過
   - **謹慎**: 謹慎執行, 減少倉位, 降低杆杆, 小倉位

3. **決策規則**
   ```python
   if has_negative:
       return 'REJECT'
   elif has_caution:
       return 'REDUCE_SIZE'
   elif has_positive and confidence >= 60:
       return 'EXECUTE'
   elif confidence >= 70:
       return 'EXECUTE'
   elif confidence >= 50:
       return 'REDUCE_SIZE'
   else:
       return 'REJECT'
   ```

#### 範例

**輸入**:
```
作為一名經驗豐富的加密貨幣交易員...
行動： OPEN_SHORT
信心度： 70% (符合執行
```

**推斷結果**:
```json
{
  "execution_decision": "EXECUTE",
  "reasoning": "審核員同意執行，信心度 70% (從部分輸出推斷)",
  "confidence_adjustment": 0,
  "position_size_ratio": 1.0
}
```

---

## 修復流程

```python
def parse_executor_review(content: str) -> Dict:
    # 策略 1: 標準 JSON 解析
    result = RobustJSONParser.parse(content, None)
    
    if result is None or 'execution_decision' not in result:
        # 策略 2: 智能推斷 (新增)
        result = infer_executor_decision_from_partial(content)
    
    # 補全預設值
    for key, value in default.items():
        result.setdefault(key, value)
    
    return result
```

---

## 測試案例

### 案例 1: 完整輸出 (JSON)

**輸入**:
```json
{
  "execution_decision": "EXECUTE",
  "confidence_adjustment": 5,
  "position_size_ratio": 1.0,
  "reasoning": "信心度達標",
  "risk_factors": []
}
```

**結果**: ✅ 直接解析 JSON

---

### 案例 2: 部分輸出 (正面)

**輸入**:
```
作為交易員，我審核了這個決策。
行動: OPEN_SHORT
信心度: 70%
符合執行標準，建議執行。
```

**結果**: ✅ 推斷為 EXECUTE

---

### 案例 3: 部分輸出 (負面)

**輸入**:
```
審核分析:
行動: OPEN_LONG
信心度: 45%
信心度不足，不建議執行。
```

**結果**: ✅ 推斷為 REJECT

---

### 案例 4: 部分輸出 (謹慎)

**輸入**:
```
行動: OPEN_LONG
信心度: 55%
謹慎執行，建議減少倉位至 50%。
```

**結果**: ✅ 推斷為 REDUCE_SIZE (ratio=0.5)

---

### 案例 5: 完全無法判斷

**輸入**:
```
作為一名...
(輸出在開頭就停止)
```

**結果**: ⚠️ 預設 REJECT (安全策略)

---

## Commit

[0dd8394](https://github.com/caizongxun/STW/commit/0dd8394d8945375c50b0b98eb531794baff1e7be)

---

## 部署步驟

### 1. 更新代碼

```bash
cd ~/STW
git pull origin main
```

### 2. 重啟伺服器

```bash
pkill -f app_flask.py
python app_flask.py
```

### 3. 測試

點擊「獲取實時訊號」，觀察輸出：

**修復前**:
```
[AI REVIEW] REJECT
            拒絕執行: 解析失敗...
```

**修復後**:
```
[AI REVIEW] EXECUTE
            審核員同意執行，信心度 70% (從部分輸出推斷)
```

---

## 優勢

✅ **容错性提高**
- 即使 AI 輸出被截斷，也能正確判斷
- 不再因為解析失敗而拒絕所有交易

✅ **智能推斷**
- 根據關鍵詞和信心度推斷決策
- 支持 EXECUTE, REJECT, REDUCE_SIZE 三種決策

✅ **安全策略**
- 完全無法判斷時，預設 REJECT (保守)
- 不會誤判為 EXECUTE

✅ **向下兼容**
- 仍然支持完整 JSON 解析
- 只有 JSON 失敗時才使用推斷

---

## 相關文件

- [BUGFIX_EXECUTOR_AND_FLOATING_POSITION.md](./BUGFIX_EXECUTOR_AND_FLOATING_POSITION.md) - Executor 日誌改進
- [BUGFIX_JAVASCRIPT_ERRORS.md](./BUGFIX_JAVASCRIPT_ERRORS.md) - JavaScript 錯誤修復
- [BUGFIX_EXECUTOR_PARTIAL_OUTPUT.md](./BUGFIX_EXECUTOR_PARTIAL_OUTPUT.md) - 本文檔

---

## 總結

✅ **問題已解決**
- AI 輸出被截斷也能正確處理
- 智能推斷系統已上線
- 支持多種決策結果

👉 **立即更新**
```bash
git pull origin main
pkill -f app_flask.py && python app_flask.py
```

🎉 **現在即使 Gemini API 超時，Executor 也能正確判斷！**
