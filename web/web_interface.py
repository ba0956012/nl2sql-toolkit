#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web 界面 - 在瀏覽器中體驗 OpenSearch-SQL
使用方法:
    python web_interface.py
    然後訪問 http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sys
import os
import sqlite3
from pathlib import Path

# 添加父目錄和 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from query_interface import QueryInterface

app = Flask(__name__)
CORS(app)

# 初始化查詢接口
query_interface = QueryInterface()

# 資料庫路徑（從環境變數讀取）
DB_ROOT = os.getenv('DB_ROOT_DIRECTORY', 'PosTest')
DB_PATH = f"{DB_ROOT}/dev/dev_databases/{DB_ROOT}/{DB_ROOT}.sqlite"

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSearch-SQL 查詢助手</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        .input-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s;
        }
        
        .input-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            flex: 1;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .result-section {
            margin-top: 20px;
            display: none;
        }
        
        .result-section.show {
            display: block;
        }
        
        .result-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .result-icon {
            font-size: 24px;
            margin-right: 10px;
        }
        
        .result-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            flex: 1;
        }
        
        .edit-hint {
            font-size: 12px;
            color: #999;
            font-weight: normal;
            margin-left: 10px;
        }
        
        .sql-output {
            position: relative;
        }
        
        .sql-editor {
            width: 100%;
            min-height: 150px;
            max-height: 400px;
            padding: 15px;
            padding-top: 45px;
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.8;
            color: #2c3e50;
            resize: vertical;
            transition: border-color 0.3s;
        }
        
        .sql-editor:focus {
            outline: none;
            border-color: #667eea;
            background: #ffffff;
        }
        
        .sql-editor:hover {
            border-color: #b0b0b0;
        }
        
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 8px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.3s;
        }
        
        .copy-btn:hover {
            background: #5568d3;
        }
        
        .loading {
            text-align: center;
            padding: 30px;
            display: none;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .examples {
            margin-top: 20px;
        }
        
        .examples-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #666;
        }
        
        .example-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .example-chip {
            padding: 8px 15px;
            background: #f0f0f0;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .example-chip:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        
        .error-message {
            background: #fee;
            border: 2px solid #fcc;
            border-radius: 8px;
            padding: 15px;
            color: #c33;
            margin-top: 15px;
        }
        
        .execute-btn {
            width: 100%;
            margin-top: 15px;
            margin-bottom: 15px;
            padding: 15px 25px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .execute-btn:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
        }
        
        .execute-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .data-table-container {
            margin-top: 20px;
            overflow-x: auto;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .data-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        .data-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .data-table tr:hover {
            background: #f8f9fa;
        }
        
        .data-table tr:nth-child(even) {
            background: #fafafa;
        }
        
        .data-table tr:nth-child(even):hover {
            background: #f0f0f0;
        }
        
        .no-data {
            text-align: center;
            padding: 30px;
            color: #999;
        }
        
        .result-count {
            margin-top: 10px;
            padding: 10px;
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            color: #333;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .card {
                padding: 20px;
            }
            
            .button-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 OpenSearch-SQL</h1>
            <p>將自然語言轉換為 SQL 查詢</p>
        </div>
        
        <div class="card">
            <div class="input-group">
                <label for="question">💬 輸入你的問題</label>
                <textarea 
                    id="question" 
                    rows="3" 
                    placeholder="例如：有多少筆銷售交易？"
                ></textarea>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="generateSQL()">
                    🚀 生成 SQL
                </button>
                <button class="btn btn-secondary" onclick="clearAll()">
                    🗑️ 清除
                </button>
            </div>
            
            <div class="examples">
                <div class="examples-title">💡 試試這些問題：</div>
                <div class="example-chips">
                    <div class="example-chip" onclick="setQuestion('有多少筆銷售交易？')">
                        有多少筆銷售交易？
                    </div>
                    <div class="example-chip" onclick="setQuestion('總銷售額是多少？')">
                        總銷售額是多少？
                    </div>
                    <div class="example-chip" onclick="setQuestion('哪個商品賣得最好？')">
                        哪個商品賣得最好？
                    </div>
                    <div class="example-chip" onclick="setQuestion('列出所有店鋪')">
                        列出所有店鋪
                    </div>
                    <div class="example-chip" onclick="setQuestion('平均每筆交易金額')">
                        平均每筆交易金額
                    </div>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在生成 SQL 查詢...</p>
        </div>
        
        <div class="card result-section" id="result">
            <div class="result-header">
                <span class="result-icon">✅</span>
                <span class="result-title">生成的 SQL 查詢</span>
                <span class="edit-hint">✏️ 可編輯</span>
            </div>
            <button class="execute-btn" onclick="executeSQL()" id="executeBtn">
                <span>▶️</span>
                <span>執行 SQL 並查看結果</span>
            </button>
            <div class="sql-output" id="sqlOutput">
                <button class="copy-btn" onclick="copySQL()">📋 複製</button>
                <textarea 
                    class="sql-editor" 
                    id="sqlText"
                    placeholder="SQL 查詢將顯示在這裡，你可以編輯後再執行..."
                ></textarea>
            </div>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="timeValue">-</div>
                    <div class="stat-label">耗時（秒）</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="lengthValue">-</div>
                    <div class="stat-label">SQL 長度</div>
                </div>
            </div>
        </div>
        
        <div class="card result-section" id="dataResult">
            <div class="result-header">
                <span class="result-icon">📊</span>
                <span class="result-title">查詢結果</span>
            </div>
            <div class="result-count" id="resultCount"></div>
            <div class="data-table-container" id="dataTableContainer">
                <table class="data-table" id="dataTable">
                    <thead id="tableHead"></thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>
        
        <div class="card result-section" id="error" style="display: none;">
            <div class="error-message" id="errorMessage"></div>
        </div>
    </div>
    
    <script>
        function setQuestion(question) {
            document.getElementById('question').value = question;
        }
        
        function clearAll() {
            document.getElementById('question').value = '';
            document.getElementById('result').classList.remove('show');
            document.getElementById('dataResult').classList.remove('show');
            document.getElementById('error').style.display = 'none';
        }
        
        let currentSQL = '';
        
        function formatSQL(sql) {
            // 簡單的 SQL 格式化：在關鍵字前添加換行
            const keywords = [
                'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
                'INNER JOIN', 'OUTER JOIN', 'ON', 'GROUP BY', 'HAVING', 
                'ORDER BY', 'LIMIT', 'OFFSET', 'UNION', 'AND', 'OR'
            ];
            
            let formatted = sql;
            
            // 為主要關鍵字添加換行
            const majorKeywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT'];
            majorKeywords.forEach(keyword => {
                const regex = new RegExp(`\\s+(${keyword})\\s+`, 'gi');
                formatted = formatted.replace(regex, '\\n$1 ');
            });
            
            // 為 JOIN 添加換行
            formatted = formatted.replace(/\\s+((?:LEFT|RIGHT|INNER|OUTER)?\\s*JOIN)\\s+/gi, '\\n$1 ');
            
            // 為 AND/OR 添加換行（在 WHERE 子句中）
            formatted = formatted.replace(/\\s+(AND|OR)\\s+/gi, '\\n  $1 ');
            
            // 清理多餘的空白
            formatted = formatted.replace(/\\n\\s*\\n/g, '\\n');
            formatted = formatted.trim();
            
            return formatted;
        }
        
        async function executeSQL() {
            // 從編輯器獲取當前的 SQL（可能已被用戶修改）
            const sqlToExecute = document.getElementById('sqlText').value.trim();
            
            if (!sqlToExecute) {
                alert('沒有可執行的 SQL');
                return;
            }
            
            const executeBtn = document.getElementById('executeBtn');
            executeBtn.disabled = true;
            executeBtn.innerHTML = '<span>⏳</span><span>執行中...</span>';
            
            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ sql: sqlToExecute })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    displayResults(data);
                    document.getElementById('dataResult').classList.add('show');
                } else {
                    alert('執行失敗：' + (data.error || '未知錯誤'));
                }
            } catch (error) {
                alert('請求失敗：' + error.message);
            } finally {
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<span>▶️</span><span>執行 SQL 並查看結果</span>';
            }
        }
        
        function displayResults(data) {
            const { columns, rows, count } = data;
            
            // 顯示結果數量
            document.getElementById('resultCount').textContent = 
                `📈 共查詢到 ${count} 筆資料`;
            
            // 清空表格
            const tableHead = document.getElementById('tableHead');
            const tableBody = document.getElementById('tableBody');
            tableHead.innerHTML = '';
            tableBody.innerHTML = '';
            
            if (count === 0) {
                tableBody.innerHTML = '<tr><td colspan="100" class="no-data">沒有查詢到任何資料</td></tr>';
                return;
            }
            
            // 創建表頭
            const headerRow = document.createElement('tr');
            columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                headerRow.appendChild(th);
            });
            tableHead.appendChild(headerRow);
            
            // 創建表格內容
            rows.forEach(row => {
                const tr = document.createElement('tr');
                columns.forEach(col => {
                    const td = document.createElement('td');
                    const value = row[col];
                    td.textContent = value !== null && value !== undefined ? value : 'NULL';
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        }
        
        async function generateSQL() {
            const question = document.getElementById('question').value.trim();
            
            if (!question) {
                alert('請輸入問題！');
                return;
            }
            
            // 隱藏結果，顯示載入
            document.getElementById('result').classList.remove('show');
            document.getElementById('error').style.display = 'none';
            document.getElementById('loading').classList.add('show');
            
            const startTime = Date.now();
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                
                document.getElementById('loading').classList.remove('show');
                
                if (data.status === 'success') {
                    // 保存原始 SQL
                    currentSQL = data.sql;
                    
                    // 格式化並顯示 SQL（使用 value 而不是 textContent）
                    const formattedSQL = formatSQL(data.sql);
                    document.getElementById('sqlText').value = formattedSQL;
                    document.getElementById('timeValue').textContent = elapsed;
                    document.getElementById('lengthValue').textContent = data.sql.length;
                    document.getElementById('result').classList.add('show');
                    
                    // 隱藏之前的查詢結果
                    document.getElementById('dataResult').classList.remove('show');
                } else {
                    // 顯示錯誤
                    document.getElementById('errorMessage').textContent = 
                        '❌ 生成失敗：' + (data.error || '未知錯誤');
                    document.getElementById('error').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('loading').classList.remove('show');
                document.getElementById('errorMessage').textContent = 
                    '❌ 請求失敗：' + error.message;
                document.getElementById('error').style.display = 'block';
            }
        }
        
        function copySQL() {
            const sqlText = document.getElementById('sqlText').value;
            navigator.clipboard.writeText(sqlText).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = '✅ 已複製';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            });
        }
        
        // 支持 Enter 鍵提交（Ctrl/Cmd + Enter）
        document.getElementById('question').addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                generateSQL();
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    """首頁 - 顯示 Web 界面"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/query", methods=["POST"])
def query():
    """處理查詢請求"""
    try:
        data = request.get_json()

        if not data or "question" not in data:
            return jsonify({"status": "error", "error": "請提供 'question' 參數"}), 400

        question = data["question"].strip()

        if not question:
            return jsonify({"status": "error", "error": "問題不能為空"}), 400

        # 執行查詢
        print(f"\n收到問題: {question}")
        sql = query_interface.query(question)

        if sql:
            print(f"生成 SQL: {sql}")
            return jsonify({"question": question, "sql": sql, "status": "success"})
        else:
            return jsonify(
                {"question": question, "status": "error", "error": "無法生成 SQL"}
            ), 500

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/execute", methods=["POST"])
def execute():
    """執行 SQL 查詢並返回結果"""
    try:
        data = request.get_json()
        
        if not data or "sql" not in data:
            return jsonify({"status": "error", "error": "請提供 'sql' 參數"}), 400
        
        sql = data["sql"].strip()
        
        if not sql:
            return jsonify({"status": "error", "error": "SQL 不能為空"}), 400
        
        # 檢查資料庫是否存在
        if not Path(DB_PATH).exists():
            return jsonify({"status": "error", "error": f"資料庫不存在: {DB_PATH}"}), 500
        
        # 連接資料庫並執行查詢
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            
            # 獲取列名
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # 獲取結果
            rows = cursor.fetchall()
            
            # 轉換為字典列表
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            conn.close()
            
            return jsonify({
                "status": "success",
                "columns": columns,
                "rows": results,
                "count": len(results)
            })
            
        except sqlite3.Error as e:
            conn.close()
            return jsonify({"status": "error", "error": f"SQL 執行錯誤: {str(e)}"}), 400
            
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/health")
def health():
    """健康檢查"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 啟動 OpenSearch-SQL Web 界面")
    print("=" * 60)
    print("訪問 http://localhost:5002 開始使用")
    print("按 Ctrl+C 停止服務器")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=5002, debug=False)
