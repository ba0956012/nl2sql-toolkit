# 檔案結構遷移指南

## 變更摘要

專案進行了檔案結構整理，將相關檔案分類到不同目錄中。

## 檔案移動對照表

### Web 介面 → `web/`
| 舊位置 | 新位置 |
|--------|--------|
| `api_server.py` | `web/api_server.py` |
| `web_interface.py` | `web/web_interface.py` |
| `fewshot_web.py` | `web/fewshot_web.py` |
| `fewshot_advanced.py` | `web/fewshot_advanced.py` |

### 設置腳本 → `scripts/setup/`
| 舊位置 | 新位置 |
|--------|--------|
| `setup_env.sh` | `scripts/setup/setup_env.sh` |
| `setup_from_sqlite_with_fewshot.sh` | `scripts/setup/setup_from_sqlite_with_fewshot.sh` |

### Few-shot 工具 → `scripts/fewshot/`
| 舊位置 | 新位置 |
|--------|--------|
| `auto_generate_fewshot.py` | `scripts/fewshot/auto_generate_fewshot.py` |
| `manage_fewshot.py` | `scripts/fewshot/manage_fewshot.py` |
| `sync_fewshot.py` | `scripts/fewshot/sync_fewshot.py` |
| `test_fewshot_format.py` | `scripts/fewshot/test_fewshot_format.py` |

### ChromaDB 工具 → `scripts/chromadb/`
| 舊位置 | 新位置 |
|--------|--------|
| `build_chromadb_index.py` | `scripts/chromadb/build_chromadb_index.py` |
| `manage_chromadb.py` | `scripts/chromadb/manage_chromadb.py` |
| `test_chromadb_retrieval.py` | `scripts/chromadb/test_chromadb_retrieval.py` |

### 其他工具 → `scripts/utils/`
| 舊位置 | 新位置 |
|--------|--------|
| `create_custom_db_template.py` | `scripts/utils/create_custom_db_template.py` |
| `analyze_failure.py` | `scripts/utils/analyze_failure.py` |
| `analyze_fewshot_usage.py` | `scripts/utils/analyze_fewshot_usage.py` |

### 測試檔案 → `tests/`
| 舊位置 | 新位置 |
|--------|--------|
| `test_query_interface.py` | `tests/test_query_interface.py` |
| `test_fewshot_retrieval.py` | `tests/test_fewshot_retrieval.py` |
| `debug_query_result.py` | `tests/debug_query_result.py` |
| `test_logs.sh` | `tests/test_logs.sh` |

### 文檔 → `docs/`
| 舊位置 | 新位置 |
|--------|--------|
| `FEWSHOT_ANALYSIS.md` | `docs/FEWSHOT_ANALYSIS.md` |
| `FEWSHOT_RETRIEVAL.md` | `docs/FEWSHOT_RETRIEVAL.md` |
| `CHROMADB_MIGRATION.md` | `docs/CHROMADB_MIGRATION.md` |

## 更新你的命令

### 啟動 Web 服務

**舊方式：**
```bash
python web_interface.py
python fewshot_advanced.py
```

**新方式：**
```bash
python web/web_interface.py
python web/fewshot_advanced.py
```

**Docker 方式（推薦）：**
```bash
docker-compose up  # 自動使用正確路徑
```

### 執行設置腳本

**舊方式：**
```bash
sh setup_from_sqlite_with_fewshot.sh MyDB /path/to/db.sqlite
```

**新方式：**
```bash
bash scripts/setup/setup_from_sqlite_with_fewshot.sh MyDB /path/to/db.sqlite
```

### Few-shot 管理

**舊方式：**
```bash
python auto_generate_fewshot.py
python sync_fewshot.py
```

**新方式：**
```bash
python scripts/fewshot/auto_generate_fewshot.py
python scripts/fewshot/sync_fewshot.py
```

### ChromaDB 管理

**舊方式：**
```bash
python build_chromadb_index.py
python manage_chromadb.py
```

**新方式：**
```bash
python scripts/chromadb/build_chromadb_index.py
python scripts/chromadb/manage_chromadb.py
```

### 測試和調試

**舊方式：**
```bash
python test_query_interface.py
python debug_query_result.py
```

**新方式：**
```bash
python tests/test_query_interface.py
python tests/debug_query_result.py
```

## Docker 使用者

Docker 配置已自動更新，無需修改你的使用方式：

```bash
# 這些命令保持不變
docker-compose up
docker-compose down
docker-compose logs
```

## 自動化腳本更新

如果你有自己的腳本引用這些檔案，請更新路徑：

**範例：**
```bash
# 舊腳本
python auto_generate_fewshot.py
python web_interface.py

# 更新為
python scripts/fewshot/auto_generate_fewshot.py
python web/web_interface.py
```

## 不受影響的檔案

以下檔案保持在原位置：
- `query_interface.py` - 主要查詢介面（根目錄）
- `docker-compose.yml` - Docker 配置
- `Dockerfile` - Docker 映像
- `requirements.txt` - Python 依賴
- `.env` - 環境變數
- `readme.md` - 主要文檔
- `src/` - 核心程式碼目錄
- `PosTest/` - 資料庫目錄
- `results/` - 結果目錄
- `logs/` - 日誌目錄

## 優點

✅ **更清晰的結構** - 相關檔案集中管理
✅ **易於導航** - 快速找到需要的檔案
✅ **更好的組織** - 符合 Python 專案最佳實踐
✅ **簡化根目錄** - 只保留核心配置檔案

## 需要幫助？

查看以下文檔：
- [快速參考](QUICK_REFERENCE.md) - 常用命令
- [專案結構](PROJECT_STRUCTURE.md) - 完整結構說明
- [主要文檔](../readme.md) - 使用指南
