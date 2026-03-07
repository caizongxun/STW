# Bug Fix Notes - AI 聊天室顯示修復

## 問題描述

AI 聊天室中 Executor (執行審核員) 的回應無法顯示，顯示「無內容」。

## 根本原因

### 問題 1: Gemini API 輸出被截斷

**原因**:
- `max_output_tokens=2000` 不足，導致生成到一半停止
- 生成的 JSON 不完整，無法解析

**修復** (已完成 in `trading_executor_agent.py`):
```python
# 第 341 行
max_output_tokens=4000  # 2000 -> 4000
```

**增強**:
1. 添加 `_detect_truncation()` 檢測輸出截斷
2. 添加 `_infer_from_truncated()` 智能推斷決策
   - 基於關鍵詞：「符合執行」、「拒絕執行」、「減少倉位」
   - 基於信心度：60%/50% 門檢，逆勢 70%

---

### 問題 2: `arbitrator_consensus_agent.py` else 分支沒有保存 `raw_content`

**原因**:
第 780-795 行：
```python
if hasattr(self.trading_executor, 'last_raw_response'):
    self.last_analysis_detail['model_responses']['executor'] = {
        'raw_content': self.trading_executor.last_raw_response,  # ✔️ 有
        ...
    }
else:
    self.last_analysis_detail['model_responses']['executor'] = {
        # ❌ 沒有 raw_content！
        'execution_decision': ...,
        ...
    }
```

**當 `last_raw_response` 不存在或為 `None` 時**，代碼走到 `else`，**沒有保存 `raw_content`**！

前端 `api_routes_ai_chat.py` 第 138 行：
```python
content = model_resp.get('raw_content', model_resp.get('reasoning', '無內容'))
```
因為 `raw_content` 不存在，所以顯示「無內容」！

---

## 修復方案

### 修復 `arbitrator_consensus_agent.py`

**位置**: 第 780-798 行

**原代碼** (問題):
```python
if hasattr(self.trading_executor, 'last_raw_response'):
    self.last_analysis_detail['model_responses']['executor'] = {
        'raw_content': self.trading_executor.last_raw_response,
        ...
    }
else:
    self.last_analysis_detail['model_responses']['executor'] = {
        'execution_decision': execution_review['execution_decision'],
        'final_action': execution_review['final_action'],
        'adjusted_confidence': execution_review['adjusted_confidence'],
        'reasoning': execution_review['executor_reasoning']
        # ❌ 沒有 raw_content
    }
```

**修復後代碼**:
```python
# 儲存執行審核員的回應
if hasattr(self.trading_executor, 'last_raw_response') and self.trading_executor.last_raw_response:
    self.last_analysis_detail['model_responses']['executor'] = {
        'raw_content': self.trading_executor.last_raw_response,
        'execution_decision': execution_review['execution_decision'],
        'final_action': execution_review['final_action'],
        'adjusted_confidence': execution_review['adjusted_confidence'],
        'reasoning': execution_review['executor_reasoning']
    }
else:
    # 當沒有 last_raw_response 時，使用 executor_reasoning 作為顯示內容
    executor_content = execution_review.get('executor_reasoning', '執行審核員回應')
    self.last_analysis_detail['model_responses']['executor'] = {
        'raw_content': executor_content,  # ✔️ 確保前端可以顯示
        'execution_decision': execution_review['execution_decision'],
        'final_action': execution_review['final_action'],
        'adjusted_confidence': execution_review['adjusted_confidence'],
        'reasoning': execution_review['executor_reasoning']
    }
```

**關鍵修改**:
1. `if` 條件添加 `and self.trading_executor.last_raw_response` 檢查非空
2. `else` 分支添加 `'raw_content': executor_content`
3. 使用 `executor_reasoning` 作為備用內容源

---

## 測試計劃

1. **別忘了修改 `arbitrator_consensus_agent.py`**
2. 重啟 Streamlit 應用
3. 觸發一次交易決策
4. 檢查 AI 聊天室中 Executor 是否有內容

---

## 檢查清單

- [x] 修復 `trading_executor_agent.py` (Commit: e0db685)
  - [x] `max_output_tokens` 2000 → 4000
  - [x] 添加 `_detect_truncation()`
  - [x] 添加 `_infer_from_truncated()`

- [ ] 修復 `arbitrator_consensus_agent.py` (待辦)
  - [ ] 第 781 行: 添加 `and self.trading_executor.last_raw_response`
  - [ ] 第 795-799 行: 添加 `executor_content` 和 `raw_content`

---

## Commit 記錄

- `e0db685`: 修復 Gemini 截斷問題 + AI 聊天室顯示 (trading_executor_agent.py)
- **下一步**: 修復 arbitrator_consensus_agent.py else 分支
