# NL2SQL Toolkit

[中文說明](README.zh-TW.md)

A Text-to-SQL toolkit built on top of **[OpenSearch-SQL](https://github.com/OpenSearch-AI/OpenSearch-SQL)**, designed to convert natural language questions into SQL queries. The system includes a web-based query console, few-shot example management, and automated setup tools.

---

## 🚀 Quick Start

```bash
# 1. Create configuration
cp .env.example .env && nano .env

# 2. Setup database + few-shot examples
bash scripts/setup/setup_from_sqlite_with_fewshot.sh MyDB /path/to/your.sqlite

# 3. Run services
docker-compose up
```

Web Interfaces:

- Query UI: http://localhost:5002  
- Few-shot Management: http://localhost:5003  

---

## 🧠 Text-to-SQL Overview

Text-to-SQL automatically converts natural language into SQL queries.

Example:

```
Question: Which product has the highest sales?
System: SELECT product_name, SUM(amount) ...
```

---

# ✨ Features

## Core Features
- Convert natural language queries into SQL  
- Web-based query interface  
- Few-shot example management  
- Support custom few-shot examples to improve accuracy  

## Extended Features
- Fully automated build pipeline (including auto few-shot generation)  
- Dynamic few-shot retrieval via ChromaDB  
- Unified configuration via `.env`  
- One-command Docker deployment  

---

# 🆕 Major Enhancements

## 1. Automated Build Pipeline

Run a single command:

```bash
sh setup_from_sqlite_with_fewshot.sh MyDB /path/to/db.sqlite
```

Included steps:

- Database schema extraction  
- Table description generation  
- Data preprocessing  
- Automatic few-shot creation  
- Embedding building  
- Full system validation  

---

## 2. Dynamic Few-shot Selection (ChromaDB)

On startup, the system embeds all few-shot examples and constructs a vector index.  
During execution, it retrieves the most relevant examples automatically.

Workflow:

```
User question → ChromaDB search → Select few-shot → Generate SQL
```

Benefits:

- Few-shot updates are automatically re-indexed  
- Persistent embedding storage  
- No need to re-calculate embeddings manually  
- More reliable SQL generation  

---

## 3. Unified `.env` Configuration

You can configure:

- Azure OpenAI / OpenAI API keys  
- Web server ports  
- Database root directory  
- Model parameters  
- Few-shot data directory  
- Embedding settings  

---

# 🛠 Usage

## 1. Configure `.env`

```bash
cp .env.example .env
nano .env
```

Minimal configuration:

```env
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
DB_ROOT_DIRECTORY=MyDB
```

---

## 2. Build database and few-shot examples

```bash
bash scripts/setup/setup_from_sqlite_with_fewshot.sh MyDB /path/to/your.sqlite
```

---

## 3. Start the web services

```bash
docker-compose up
```

---

# 📁 Project Structure

```
OpenSearch-SQL/
├── src/
│   ├── config.py
│   ├── llm/
│   ├── pipeline/
│   └── runner/
│
├── web/
│   ├── web_interface.py
│   ├── fewshot_advanced.py
│   ├── api_server.py
│   └── fewshot_web.py
│
├── scripts/
│   ├── setup/
│   ├── fewshot/
│   ├── chromadb/
│   └── utils/
│
├── query_interface.py
├── docker-compose.yml
├── .env.example
└── .env
```


