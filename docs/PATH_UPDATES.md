# 路徑更新總結

## 已更新的檔案

### 1. Web 介面 (`web/`)
- ✅ `web/api_server.py` - 更新 import 路徑
- ✅ `web/web_interface.py` - 更新 import 路徑

### 2. 腳本 (`scripts/`)

#### ChromaDB 工具
- ✅ `scripts/chromadb/manage_chromadb.py` - 更新 sys.path
- ✅ `scripts/chromadb/build_chromadb_index.py` - 更新 sys.path
- ✅ `scripts/chromadb/test_chromadb_retrieval.py` - 更新 sys.path

#### Few-shot 工具
- ✅ `scripts/fewshot/auto_generate_fewshot.py` - 更新 sys.path

#### 設置腳本
- ✅ `scripts/setup/setup_from_sqlite_with_fewshot.sh` - 更新所有命令路徑

### 3. 測試 (`tests/`)
- ✅ `tests/test_query_interface.py` - 更新 sys.path
- ✅ `tests/test_fewshot_retrieval.py` - 更新 sys.path

### 4. 配置檔案
- ✅ `docker-compose.yml` - 更新 fewshot_advanced.py 路徑
- ✅ `Dockerfile` - 更新 web_interface.py 路徑
- ✅ `.gitignore` - 新增 results/, model/ 等

## 路徑更新模式

### 舊模式（根目錄執行）
```python
sys.path.insert(0, 'src')
```

### 新模式（子目錄執行）
```python
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent  # 或 .parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
```

## 測試方法

### 1. 測試 Web 介面
```bash
# 從專案根目錄
python web/web_interface.py
python web/api_server.py
python web/fewshot_advanced.py
```

### 2. 測試腳本
```bash
# ChromaDB
python scripts/chromadb/build_chromadb_index.py --db-root PosTest
python scripts/chromadb/manage_chromadb.py stats PosTest

# Few-shot
python scripts/fewshot/auto_generate_fewshot.py --db_root_directory PosTest

# 設置
bash scripts/setup/setup_from_sqlite_with_fewshot.sh TestDB ./test.sqlite
```

### 3. 測試測試檔案
```bash
python tests/test_query_interface.py
python tests/test_fewshot_retrieval.py
```

### 4. 測試 Docker
```bash
docker-compose up --build
```

## 驗證清單

- [ ] Web 介面可以啟動
- [ ] Few-shot 管理介面可以啟動
- [ ] 設置腳本可以執行
- [ ] ChromaDB 工具可以執行
- [ ] 測試檔案可以執行
- [ ] Docker 服務可以啟動

## 常見問題

### Q: ModuleNotFoundError: No module named 'runner'
**A:** 檢查 sys.path 是否正確設置，應該包含專案根目錄和 src 目錄。

### Q: FileNotFoundError: 找不到檔案
**A:** 確保從專案根目錄執行命令，或使用絕對路徑。

### Q: Docker 啟動失敗
**A:** 檢查 docker-compose.yml 和 Dockerfile 中的路徑是否正確。

## 未來新增檔案注意事項

當在子目錄中新增 Python 檔案時，記得：

1. **添加正確的路徑設置**
   ```python
   from pathlib import Path
   project_root = Path(__file__).parent.parent  # 根據深度調整
   sys.path.insert(0, str(project_root))
   sys.path.insert(0, str(project_root / 'src'))
   ```

2. **或使用相對 import**（如果在同一個 package 內）
   ```python
   from ..module import something
   ```

3. **測試從根目錄執行**
   ```bash
   python path/to/your/script.py
   ```
