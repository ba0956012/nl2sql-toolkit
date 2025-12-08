# Few-shot 使用分析指南

## 📊 查看使用的 Few-shot 範例

系統會在日誌中記錄每次查詢使用了哪些 Few-shot 範例。

### 方法 1：查看日誌檔案

日誌位置：`logs/logs/<question_id>_<db_id>.log`

```bash
# 查看最新的日誌
tail -f logs/logs/*.log | grep "Using few-shot"
```

你會看到類似這樣的輸出：
```
INFO - Using extract few-shot example #0
INFO - Using few-shot example #0: 查詢所有支付方式的付款總額...
```

### 方法 2：使用分析工具

```bash
# 分析所有日誌
python analyze_fewshot_usage.py

# 指定資料庫
python analyze_fewshot_usage.py --db-root MyDB --logs-dir logs/logs
```

**輸出範例：**
```
============================================================
📈 Few-shot 使用統計
============================================================

🔍 Extract Few-shot 使用次數:
  範例 #0: 5 次
  範例 #1: 3 次
  範例 #2: 2 次

🎯 Candidate Few-shot 使用次數:
  範例 #0: 5 次
    問題: 查詢所有支付方式的付款總額...
  範例 #1: 3 次
    問題: 查詢每種支付方式的付款次數...

============================================================
📚 Few-shot 範例詳情:
============================================================

🔥 最常使用的範例:

範例 #0 (使用 5 次):
  問題: 查詢所有支付方式的付款總額。
  SQL: SELECT payment_method, SUM(payment_amount) AS total_amount FROM pos_payment GROUP BY payment_method...
```

## 🔍 理解日誌內容

### 日誌結構

每個查詢的日誌包含多個階段：

```
############################## Human at step extract_col_value ##############################

[LLM 的輸入 prompt，包含 few-shot 範例]

############################## AI at step extract_col_value ##############################

[LLM 的輸出結果]

############################## Human at step candidate_generate ##############################

[包含完整的 few-shot 範例和資料庫 schema]

############################## AI at step candidate_generate ##############################

[生成的 SQL 查詢]
```

### 關鍵資訊

1. **使用的 Few-shot 範例 ID**
   ```
   INFO - Using few-shot example #0
   ```

2. **Few-shot 範例內容**
   - 在 `Human at step candidate_generate` 部分
   - 包含範例問題和對應的 SQL

3. **生成的 SQL**
   - 在 `AI at step candidate_generate` 部分

## 📈 分析 Few-shot 效果

### 1. 查看哪些範例最常被使用

```bash
python analyze_fewshot_usage.py
```

**高頻使用的範例** = 代表性強，對系統很有幫助

### 2. 查看哪些範例從未被使用

如果某些範例從未被使用，可能：
- 範例太特殊，不具代表性
- 範例與實際查詢差異太大
- 需要新增更多類似的查詢來觸發

### 3. 分析查詢失敗的情況

```bash
# 查看失敗的查詢
grep -r "ERROR" logs/logs/*.log

# 查看失敗時使用的 few-shot
grep -B 5 "ERROR" logs/logs/*.log | grep "Using few-shot"
```

## 🎯 改進 Few-shot 品質

### 策略 1：增加高頻查詢的範例

如果發現某類查詢很常見但沒有對應的 few-shot：

1. 訪問 Few-shot 管理界面 (http://localhost:5003)
2. 新增該類型的範例
3. 測試改進效果

### 策略 2：改進低效範例

如果某個範例使用頻率高但效果不好：

1. 查看使用該範例的查詢日誌
2. 分析為什麼生成的 SQL 不正確
3. 改進範例的問題描述或 SQL
4. 重新測試

### 策略 3：移除無用範例

如果某些範例從未被使用：

1. 評估是否真的需要
2. 如果不需要，可以刪除以減少 token 使用
3. 或者改進範例使其更具代表性

## 📊 監控指標

### 關鍵指標

1. **Few-shot 使用分布**
   - 是否有範例被過度使用？
   - 是否有範例從未使用？

2. **查詢成功率**
   - 使用特定 few-shot 的查詢成功率
   - 不同類型查詢的成功率

3. **Few-shot 覆蓋率**
   - 實際查詢類型 vs Few-shot 範例類型
   - 是否有查詢類型缺少對應範例？

### 監控命令

```bash
# 統計查詢總數
ls logs/logs/*.log | wc -l

# 統計成功的查詢
grep -l "SQL:" logs/logs/*.log | wc -l

# 統計失敗的查詢
grep -l "ERROR" logs/logs/*.log | wc -l

# 查看 few-shot 使用分布
python analyze_fewshot_usage.py
```

## 🔄 持續改進流程

```
1. 收集查詢日誌
   ↓
2. 分析 Few-shot 使用情況
   ↓
3. 識別問題
   - 缺少的範例類型
   - 效果不好的範例
   - 從未使用的範例
   ↓
4. 改進 Few-shot
   - 新增範例
   - 修改範例
   - 刪除範例
   ↓
5. 測試改進效果
   ↓
6. 重複流程
```

## 💡 最佳實踐

### 1. 定期分析

```bash
# 每週分析一次
python analyze_fewshot_usage.py > fewshot_analysis_$(date +%Y%m%d).txt
```

### 2. A/B 測試

測試不同的 few-shot 配置：

```bash
# 備份當前配置
cp PosTest/fewshot/questions.json PosTest/fewshot/questions.json.backup

# 測試新配置
# ... 修改 few-shot ...

# 比較結果
python analyze_fewshot_usage.py
```

### 3. 版本控制

```bash
# 記錄 few-shot 變更
git add PosTest/fewshot/questions.json
git commit -m "feat: 新增銷售分析相關的 few-shot 範例"
```

## 🛠️ 進階分析

### 自訂分析腳本

```python
import json
from pathlib import Path

# 載入日誌
log_file = Path("logs/logs/0_PosTest.log")
with open(log_file) as f:
    content = f.read()

# 提取資訊
# ... 你的分析邏輯 ...

# 生成報告
print("分析結果...")
```

### 整合到 CI/CD

```yaml
# .github/workflows/analyze-fewshot.yml
name: Analyze Few-shot Usage

on:
  schedule:
    - cron: '0 0 * * 0'  # 每週日執行

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Analyze Few-shot
        run: python analyze_fewshot_usage.py > report.txt
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: fewshot-analysis
          path: report.txt
```

## 📚 相關文檔

- [Few-shot 設置指南](FEWSHOT_SETUP_GUIDE.md)
- [配置指南](SETUP_CONFIG.md)
- [快速開始](QUICK_START.md)

---

**提示：** 持續監控和改進 Few-shot 範例是提高查詢品質的關鍵！
