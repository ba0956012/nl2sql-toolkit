#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Few-shot 完整版管理界面 - 直接管理 questions.json
支持編輯 extract, parse, questions 三個部分
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path
import sqlite3

app = Flask(__name__)
CORS(app)


class FewShotAdvancedManager:
    def __init__(self, db_root_path=None):
        import os
        if db_root_path is None:
            db_root_path = os.getenv('DB_ROOT_DIRECTORY', 'PosTest')
        
        self.db_root_path = db_root_path
        self.questions_file = Path(db_root_path) / "fewshot" / "questions.json"
        self.db_path = (
            Path(db_root_path)
            / "dev"
            / "dev_databases"
            / db_root_path
            / f"{db_root_path}.sqlite"
        )

        if not self.questions_file.exists():
            self.questions_file.parent.mkdir(parents=True, exist_ok=True)
            self._create_empty_file()

    def _create_empty_file(self):
        data = {"extract": {}, "parse": {}, "questions": []}
        with open(self.questions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_data(self):
        with open(self.questions_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_data(self, data):
        # 備份
        backup_file = self.questions_file.with_suffix(".json.backup")
        if self.questions_file.exists():
            import shutil

            shutil.copy2(self.questions_file, backup_file)

        with open(self.questions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def validate_sql(self, sql):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
            conn.close()
            return True, "SQL 語法正確"
        except Exception as e:
            return False, str(e)


manager = FewShotAdvancedManager()

# HTML 模板（完整版界面）
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Few-shot 完整管理系統</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .mode-switch {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .mode-btn {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .mode-btn.active {
            background: #667eea;
            color: white;
        }
        
        .mode-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .controls {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-success {
            background: #48bb78;
            color: white;
        }
        
        .btn-danger {
            background: #f56565;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .search-box {
            flex: 1;
            min-width: 300px;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .examples-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .example-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        
        .example-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .example-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        
        .example-id {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .example-actions {
            display: flex;
            gap: 8px;
        }
        
        .icon-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2em;
            padding: 5px;
            transition: all 0.3s;
        }
        
        .icon-btn:hover {
            transform: scale(1.2);
        }
        
        .example-question {
            font-size: 1.1em;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .example-section {
            margin: 10px 0;
            padding: 10px;
            background: #f7fafc;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }
        
        .section-title {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        
        .section-content {
            font-size: 0.85em;
            color: #4a5568;
            white-space: pre-wrap;
            max-height: 100px;
            overflow-y: auto;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            overflow-y: auto;
        }
        
        .modal-content {
            background: white;
            max-width: 1200px;
            margin: 50px auto;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .modal-header h2 {
            color: #667eea;
        }
        
        .close-btn {
            font-size: 2em;
            cursor: pointer;
            color: #a0aec0;
            transition: all 0.3s;
        }
        
        .close-btn:hover {
            color: #667eea;
            transform: rotate(90deg);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
            font-family: inherit;
        }
        
        .form-group textarea {
            min-height: 150px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        
        .form-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .tab-btn {
            padding: 10px 20px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 1em;
            color: #718096;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stat-card {
            text-align: center;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .alert-success {
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #48bb78;
        }
        
        .alert-error {
            background: #fed7d7;
            color: #742a2a;
            border-left: 4px solid #f56565;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .empty-state-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .help-text {
            font-size: 0.85em;
            color: #718096;
            margin-top: 5px;
        }
        
        .preview-box {
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Few-shot 完整管理系統</h1>
            <p>直接管理 questions.json - 支持 extract, parse, questions 三個部分</p>
        </div>

        <div class="mode-switch">
            <span style="font-weight: 600; color: #2d3748;">顯示模式：</span>
            <button class="mode-btn active" onclick="switchMode('simple')">簡化視圖</button>
            <button class="mode-btn" onclick="switchMode('advanced')">完整視圖</button>
        </div>
        
        <div id="alert" class="alert"></div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalCount">0</div>
                <div class="stat-label">總範例數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="extractCount">0</div>
                <div class="stat-label">Extract 範例</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="parseCount">0</div>
                <div class="stat-label">Parse 範例</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="questionsCount">0</div>
                <div class="stat-label">Questions 範例</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="showAddModal()">
                ➕ 新增範例
            </button>
            <button class="btn btn-success" onclick="validateAll()">
                ✅ 驗證所有 SQL
            </button>
            <button class="btn btn-danger" onclick="exportBackup()">
                💾 導出備份
            </button>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 搜尋問題、SQL..." 
                       oninput="filterExamples()">
            </div>
        </div>
        
        <div id="examplesContainer" class="examples-grid"></div>
    </div>
    
    <!-- 新增/編輯模態框 -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">新增範例</h2>
                <span class="close-btn" onclick="closeModal()">&times;</span>
            </div>
            
            <div class="form-tabs">
                <button class="tab-btn active" onclick="switchTab('basic')">基本信息</button>
                <button class="tab-btn" onclick="switchTab('extract')">Extract</button>
                <button class="tab-btn" onclick="switchTab('parse')">Parse</button>
                <button class="tab-btn" onclick="switchTab('questions')">Questions</button>
            </div>
            
            <!-- 基本信息 Tab -->
            <div id="basicTab" class="tab-content active">
                <div class="form-group">
                    <label>範例 ID *</label>
                    <input type="text" id="exampleId" placeholder="例如: 0, 1, 2...">
                    <div class="help-text">唯一識別碼，通常使用數字</div>
                </div>
                
                <div class="form-group">
                    <label>問題 *</label>
                    <input type="text" id="question" placeholder="例如：有多少筆銷售交易？">
                </div>
                
                <div class="form-group">
                    <label>SQL 查詢 *</label>
                    <textarea id="sql" placeholder="SELECT COUNT(*) FROM pos_sale"></textarea>
                    <button class="btn btn-primary" onclick="validateSQL()" style="margin-top: 10px;">
                        驗證 SQL
                    </button>
                </div>
                
                <div class="form-group">
                    <label>提示 (Evidence)</label>
                    <textarea id="evidence" placeholder="選填：額外的提示信息"></textarea>
                </div>
                
                <div class="form-group">
                    <label>資料庫 ID</label>
                    <input type="text" id="dbId" value="PosTest">
                </div>
            </div>
            
            <!-- Extract Tab -->
            <div id="extractTab" class="tab-content">
                <div class="form-group">
                    <label>Extract Prompt</label>
                    <textarea id="extractPrompt" placeholder="/* 範例：提取問題中的關鍵資訊 */
/* 問題：... */
#reason: ...
#key_columns: ...
#key_values: ...
#answer: ..." oninput="updateExtractPreview()"></textarea>
                    <div class="help-text">用於提取階段的 prompt，幫助 LLM 識別欄位和值</div>
                    <button class="btn btn-primary" onclick="autoGenerateExtract()" style="margin-top: 10px;">
                        🤖 自動生成
                    </button>
                </div>
                <div class="preview-box" id="extractPreview"></div>
            </div>
            
            <!-- Parse Tab -->
            <div id="parseTab" class="tab-content">
                <div class="form-group">
                    <label>Parse Prompt</label>
                    <textarea id="parsePrompt" placeholder="/* 範例：解析問題中的欄位和值 */
/* 問題：... */
#columns: ...
#values: ...
#operations: ..." oninput="updateParsePreview()"></textarea>
                    <div class="help-text">用於解析階段的 prompt，識別 SQL 操作類型</div>
                    <button class="btn btn-primary" onclick="autoGenerateParse()" style="margin-top: 10px;">
                        🤖 自動生成
                    </button>
                </div>
                <div class="preview-box" id="parsePreview"></div>
            </div>
            
            <!-- Questions Tab -->
            <div id="questionsTab" class="tab-content">
                <div class="form-group">
                    <label>Questions Prompt</label>
                    <textarea id="questionsPrompt" placeholder="/* 給定以下資料庫 schema: */
CREATE TABLE ...

/* 回答以下問題：... */
SELECT ..." oninput="updateQuestionsPreview()"></textarea>
                    <div class="help-text">完整的問題-SQL 範例，包含 schema</div>
                    <button class="btn btn-primary" onclick="autoGenerateQuestions()" style="margin-top: 10px;">
                        🤖 自動生成
                    </button>
                </div>
                <div class="preview-box" id="questionsPreview"></div>
            </div>
            
            <div style="margin-top: 30px; display: flex; gap: 10px; justify-content: flex-end;">
                <button class="btn btn-primary" onclick="saveExample()">💾 保存</button>
                <button class="btn" onclick="closeModal()" style="background: #e2e8f0;">取消</button>
            </div>
        </div>
    </div>

    <script>
        let allData = { extract: {}, parse: {}, questions: [] };
        let currentMode = 'simple';
        let editingId = null;
        
        // 載入數據
        async function loadData() {
            try {
                // 添加時間戳避免快取
                const timestamp = new Date().getTime();
                const response = await fetch(`/api/data?t=${timestamp}`, {
                    cache: 'no-cache',
                    headers: {
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                });
                allData = await response.json();
                console.log('載入資料:', {
                    questions: allData.questions.length,
                    extract: Object.keys(allData.extract).length,
                    parse: Object.keys(allData.parse).length
                });
                updateStats();
                renderExamples();
            } catch (error) {
                console.error('載入失敗:', error);
                showAlert('載入失敗: ' + error.message, 'error');
            }
        }
        
        // 更新統計
        function updateStats() {
            document.getElementById('totalCount').textContent = allData.questions.length;
            document.getElementById('extractCount').textContent = Object.keys(allData.extract).length;
            document.getElementById('parseCount').textContent = Object.keys(allData.parse).length;
            document.getElementById('questionsCount').textContent = allData.questions.length;
        }
        
        // 渲染範例
        function renderExamples() {
            const container = document.getElementById('examplesContainer');
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            
            if (allData.questions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <div>還沒有 Few-shot 範例</div>
                        <div>點擊「新增範例」開始</div>
                    </div>
                `;
                return;
            }
            
            let html = '';
            allData.questions.forEach((q, index) => {
                const qText = q.question.toLowerCase();
                const qPrompt = (q.prompt || '').toLowerCase();
                
                if (searchTerm && !qText.includes(searchTerm) && !qPrompt.includes(searchTerm)) {
                    return;
                }
                
                const extractData = allData.extract[String(index)] || {};
                const parseData = allData.parse[String(index)] || {};
                
                html += `
                    <div class="example-card">
                        <div class="example-header">
                            <span class="example-id">ID: ${index}</span>
                            <div class="example-actions">
                                <button class="icon-btn" onclick="editExample(${index})" title="編輯">✏️</button>
                                <button class="icon-btn" onclick="deleteExample(${index})" title="刪除">🗑️</button>
                            </div>
                        </div>
                        <div class="example-question">${q.question}</div>
                        ${currentMode === 'advanced' ? `
                            <div class="example-section">
                                <div class="section-title">Extract</div>
                                <div class="section-content">${extractData.prompt || '未設置'}</div>
                            </div>
                            <div class="example-section">
                                <div class="section-title">Parse</div>
                                <div class="section-content">${parseData.prompt || '未設置'}</div>
                            </div>
                        ` : ''}
                        <div class="example-section">
                            <div class="section-title">SQL</div>
                            <div class="section-content">${extractSQLFromPrompt(q.prompt)}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // 從 prompt 中提取 SQL
        function extractSQLFromPrompt(prompt) {
            if (!prompt) return 'N/A';
            
            const lines = prompt.split('\n');
            
            // 方法 1: 尋找最後一個 SELECT/INSERT/UPDATE/DELETE 語句
            // 這樣可以跳過 CREATE TABLE 等 schema 定義
            let lastSQLStart = -1;
            for (let i = lines.length - 1; i >= 0; i--) {
                const line = lines[i].trim();
                if (line.match(/^(SELECT|INSERT|UPDATE|DELETE|WITH)\b/i)) {
                    lastSQLStart = i;
                    break;
                }
            }
            
            if (lastSQLStart >= 0) {
                // 從找到的位置開始，收集到結尾或遇到分號
                const sqlLines = [];
                for (let i = lastSQLStart; i < lines.length; i++) {
                    const line = lines[i];
                    sqlLines.push(line);
                    // 如果遇到分號結尾，停止
                    if (line.trim().endsWith(';')) {
                        break;
                    }
                }
                return sqlLines.join('\n').trim();
            }
            
            // 方法 2: 如果沒找到 SELECT 等，嘗試找任何 SQL 關鍵字
            for (let i = lines.length - 1; i >= 0; i--) {
                const line = lines[i].trim();
                if (line && !line.startsWith('/*') && !line.startsWith('//') && !line.startsWith('--')) {
                    // 檢查是否看起來像 SQL
                    if (line.match(/\b(FROM|WHERE|JOIN|GROUP|ORDER|LIMIT)\b/i) || line.endsWith(';')) {
                        // 往回找完整的 SQL
                        let start = i;
                        while (start > 0 && !lines[start - 1].trim().startsWith('/*')) {
                            start--;
                        }
                        return lines.slice(start, i + 1).join('\n').trim();
                    }
                }
            }
            
            return 'N/A';
        }
        
        // 切換模式
        function switchMode(mode) {
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            renderExamples();
        }
        
        // 切換 Tab
        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tab + 'Tab').classList.add('active');
        }
        
        // 顯示新增模態框
        function showAddModal() {
            editingId = null;
            document.getElementById('modalTitle').textContent = '新增範例';
            document.getElementById('exampleId').value = allData.questions.length;
            document.getElementById('question').value = '';
            document.getElementById('sql').value = '';
            document.getElementById('evidence').value = '';
            document.getElementById('dbId').value = 'PosTest';
            document.getElementById('extractPrompt').value = '';
            document.getElementById('parsePrompt').value = '';
            document.getElementById('questionsPrompt').value = '';
            
            // 清空預覽
            document.getElementById('extractPreview').textContent = '（預覽區域）';
            document.getElementById('parsePreview').textContent = '（預覽區域）';
            document.getElementById('questionsPreview').textContent = '（預覽區域）';
            
            document.getElementById('editModal').style.display = 'block';
        }
        
        // 編輯範例
        async function editExample(id) {
            editingId = id;
            document.getElementById('modalTitle').textContent = '編輯範例';
            
            // 重新載入最新資料，避免快取問題
            await loadData();
            
            const question = allData.questions[id];
            const extract = allData.extract[String(id)] || {};
            const parse = allData.parse[String(id)] || {};
            
            console.log('編輯範例 #' + id, {
                question: question,
                extract: extract,
                parse: parse
            });
            
            // 從 prompt 中提取 SQL
            let sql = extractSQLFromPrompt(question.prompt);
            
            // 如果提取失敗，嘗試從 extract 的 answer 中獲取
            if (sql === 'N/A' && extract.prompt) {
                const answerMatch = extract.prompt.match(/#answer:\s*(.+?)(?:\n|$)/s);
                if (answerMatch) {
                    sql = answerMatch[1].trim();
                }
            }
            
            document.getElementById('exampleId').value = id;
            document.getElementById('question').value = question.question;
            document.getElementById('sql').value = sql;
            document.getElementById('evidence').value = '';
            document.getElementById('dbId').value = question.db_id || 'PosTest';
            document.getElementById('extractPrompt').value = extract.prompt || '';
            document.getElementById('parsePrompt').value = parse.prompt || '';
            document.getElementById('questionsPrompt').value = question.prompt || '';
            
            // 更新預覽
            updateExtractPreview();
            updateParsePreview();
            updateQuestionsPreview();
            
            document.getElementById('editModal').style.display = 'block';
        }
        
        // 關閉模態框
        function closeModal() {
            document.getElementById('editModal').style.display = 'none';
        }
        
        // 保存範例
        async function saveExample() {
            console.log('=== 開始保存範例 ===');
            
            try {
                const id = document.getElementById('exampleId').value;
                const question = document.getElementById('question').value;
                const sql = document.getElementById('sql').value;
                const evidence = document.getElementById('evidence').value;
                const dbId = document.getElementById('dbId').value;
                const extractPrompt = document.getElementById('extractPrompt').value;
                const parsePrompt = document.getElementById('parsePrompt').value;
                let questionsPrompt = document.getElementById('questionsPrompt').value;
                
                console.log('表單數據:', { id, question, sql, dbId });
                
                if (!question || !sql) {
                    console.error('驗證失敗: 缺少必填欄位');
                    showAlert('請填寫問題和 SQL', 'error');
                    return;
                }
                
                // 自動同步 SQL 到 questionsPrompt
                // 提取 questionsPrompt 中的舊 SQL
                let oldSQL = '';
                if (questionsPrompt) {
                    const lines = questionsPrompt.split('\n');
                    let sqlStartIndex = -1;
                    for (let i = lines.length - 1; i >= 0; i--) {
                        if (lines[i].trim().match(/^(SELECT|INSERT|UPDATE|DELETE|WITH)\b/i)) {
                            sqlStartIndex = i;
                            break;
                        }
                    }
                    if (sqlStartIndex >= 0) {
                        const sqlLines = [];
                        for (let i = sqlStartIndex; i < lines.length; i++) {
                            sqlLines.push(lines[i]);
                            if (lines[i].trim().endsWith(';')) break;
                        }
                        oldSQL = sqlLines.join('\n').trim();
                    }
                }
                
                // 比較新舊 SQL，如果不同則更新
                const newSQL = sql.trim();
                if (oldSQL !== newSQL) {
                    console.log('⚠️  SQL 已修改，自動更新 questions_prompt');
                    console.log('舊 SQL:', oldSQL.substring(0, 50) + '...');
                    console.log('新 SQL:', newSQL.substring(0, 50) + '...');
                    
                    if (questionsPrompt && questionsPrompt.includes('CREATE TABLE')) {
                        // 保留 schema 部分，替換 SQL
                        const lines = questionsPrompt.split('\n');
                        let sqlStartIndex = -1;
                        for (let i = lines.length - 1; i >= 0; i--) {
                            if (lines[i].trim().match(/^(SELECT|INSERT|UPDATE|DELETE|WITH)\b/i)) {
                                sqlStartIndex = i;
                                break;
                            }
                        }
                        if (sqlStartIndex >= 0) {
                            questionsPrompt = lines.slice(0, sqlStartIndex).join('\n') + '\n' + newSQL;
                        } else {
                            questionsPrompt = questionsPrompt + '\n\n' + newSQL;
                        }
                    } else {
                        // 沒有 schema，直接使用 SQL
                        questionsPrompt = `/* 回答以下問題：${question} */\n${newSQL}`;
                    }
                }
                
                const data = {
                    id: id,
                    question: question,
                    sql: sql,
                    evidence: evidence,
                    db_id: dbId,
                    extract_prompt: extractPrompt,
                    parse_prompt: parsePrompt,
                    questions_prompt: questionsPrompt
                };
                
                console.log('準備發送請求:', data);
                
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                console.log('收到回應:', response.status, response.statusText);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('HTTP 錯誤:', errorText);
                    showAlert(`保存失敗 (${response.status}): ${errorText}`, 'error');
                    return;
                }
                
                const result = await response.json();
                console.log('解析結果:', result);
                
                if (result.success) {
                    console.log('保存成功！');
                    showAlert('保存成功！', 'success');
                    closeModal();
                    loadData();
                } else {
                    console.error('保存失敗:', result.error);
                    showAlert('保存失敗: ' + result.error, 'error');
                }
            } catch (error) {
                console.error('捕獲異常:', error);
                showAlert('保存失敗: ' + error.message, 'error');
            }
        }

        // 刪除範例
        async function deleteExample(id) {
            if (!confirm(`確定要刪除範例 ${id} 嗎？`)) return;
            
            try {
                const response = await fetch(`/api/delete/${id}`, { method: 'DELETE' });
                const result = await response.json();
                if (result.success) {
                    showAlert('刪除成功！', 'success');
                    loadData();
                } else {
                    showAlert('刪除失敗: ' + result.error, 'error');
                }
            } catch (error) {
                showAlert('刪除失敗: ' + error.message, 'error');
            }
        }
        
        // 驗證 SQL
        async function validateSQL() {
            const sql = document.getElementById('sql').value;
            if (!sql) {
                showAlert('請輸入 SQL', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/validate_sql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sql })
                });
                
                const result = await response.json();
                if (result.valid) {
                    showAlert('✅ SQL 語法正確', 'success');
                } else {
                    showAlert('❌ SQL 錯誤: ' + result.error, 'error');
                }
            } catch (error) {
                showAlert('驗證失敗: ' + error.message, 'error');
            }
        }
        
        // 驗證所有 SQL
        async function validateAll() {
            try {
                const response = await fetch('/api/validate_all');
                const result = await response.json();
                showAlert(`驗證完成！通過: ${result.passed}, 失敗: ${result.failed}`, 'success');
            } catch (error) {
                showAlert('驗證失敗: ' + error.message, 'error');
            }
        }
        
        // 更新預覽
        function updateExtractPreview() {
            const content = document.getElementById('extractPrompt').value;
            document.getElementById('extractPreview').textContent = content || '（預覽區域）';
        }
        
        function updateParsePreview() {
            const content = document.getElementById('parsePrompt').value;
            document.getElementById('parsePreview').textContent = content || '（預覽區域）';
        }
        
        function updateQuestionsPreview() {
            const content = document.getElementById('questionsPrompt').value;
            document.getElementById('questionsPreview').textContent = content || '（預覽區域）';
        }
        
        // 自動生成 Extract
        function autoGenerateExtract() {
            const question = document.getElementById('question').value;
            const sql = document.getElementById('sql').value;
            const evidence = document.getElementById('evidence').value;
            
            if (!question || !sql) {
                showAlert('請先填寫問題和 SQL', 'error');
                return;
            }
            
            // 簡單的自動生成邏輯
            const columns = extractColumns(sql);
            const values = extractValues(sql);
            
            const prompt = `/* 範例：提取問題中的關鍵資訊 */
/* 問題：${question} */
/* 提示：${evidence || 'None'} */
#reason: 這個問題需要查詢相關的資料表和欄位
#key_columns: ${columns.join(', ') || 'None'}
#key_values: ${values.join(', ') || 'None'}
#answer: ${sql}`;
            
            document.getElementById('extractPrompt').value = prompt;
            document.getElementById('extractPreview').textContent = prompt;
            showAlert('Extract prompt 已自動生成', 'success');
        }
        
        // 自動生成 Parse
        function autoGenerateParse() {
            const question = document.getElementById('question').value;
            const sql = document.getElementById('sql').value;
            
            if (!question || !sql) {
                showAlert('請先填寫問題和 SQL', 'error');
                return;
            }
            
            const columns = extractColumns(sql);
            const operations = extractOperations(sql);
            
            const prompt = `/* 範例：解析問題中的欄位和值 */
/* 問題：${question} */
#columns: ${columns.join(', ') || 'None'}
#values: None
#operations: ${operations.join(', ') || 'SELECT'}`;
            
            document.getElementById('parsePrompt').value = prompt;
            document.getElementById('parsePreview').textContent = prompt;
            showAlert('Parse prompt 已自動生成', 'success');
        }
        
        // 自動生成 Questions
        function autoGenerateQuestions() {
            const question = document.getElementById('question').value;
            const sql = document.getElementById('sql').value;
            
            if (!question || !sql) {
                showAlert('請先填寫問題和 SQL', 'error');
                return;
            }
            
            const prompt = `/* 給定以下資料庫 schema: */
/* 請根據實際資料庫補充 schema */

/* 回答以下問題：${question} */
${sql}`;
            
            document.getElementById('questionsPrompt').value = prompt;
            document.getElementById('questionsPreview').textContent = prompt;
            showAlert('Questions prompt 已自動生成', 'success');
        }
        
        // 提取欄位
        function extractColumns(sql) {
            const regex = /\\b(\\w+\\.\\w+)\\b/g;
            const matches = sql.match(regex) || [];
            return [...new Set(matches)].slice(0, 5);
        }
        
        // 提取值
        function extractValues(sql) {
            const regex = /'([^']+)'/g;
            const matches = [];
            let match;
            while ((match = regex.exec(sql)) !== null) {
                matches.push(match[1]);
            }
            return [...new Set(matches)].slice(0, 3);
        }
        
        // 提取操作
        function extractOperations(sql) {
            const operations = [];
            const sqlUpper = sql.toUpperCase();
            
            if (sqlUpper.includes('COUNT')) operations.push('COUNT');
            if (sqlUpper.includes('SUM')) operations.push('SUM');
            if (sqlUpper.includes('AVG')) operations.push('AVG');
            if (sqlUpper.includes('JOIN')) operations.push('JOIN');
            if (sqlUpper.includes('GROUP BY')) operations.push('GROUP BY');
            if (sqlUpper.includes('ORDER BY')) operations.push('ORDER BY');
            if (sqlUpper.includes('LIMIT')) operations.push('LIMIT');
            
            return operations.length > 0 ? operations : ['SELECT'];
        }
        
        // 過濾範例
        function filterExamples() {
            renderExamples();
        }
        
        // 導出備份
        async function exportBackup() {
            const dataStr = JSON.stringify(allData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `questions_backup_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            showAlert('備份已導出', 'success');
        }
        
        // 顯示提示
        function showAlert(message, type) {
            console.log(`showAlert: ${type} - ${message}`);
            const alert = document.getElementById('alert');
            if (!alert) {
                console.error('找不到 alert 元素！');
                // 使用瀏覽器原生 alert 作為後備
                window.alert(message);
                return;
            }
            alert.textContent = message;
            alert.className = `alert alert-${type}`;
            alert.style.display = 'block';
            
            // 確保提示可見
            alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000); // 延長顯示時間到 5 秒
        }
        
        // 初始化
        loadData();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    """健康檢查端點"""
    return jsonify({"status": "healthy"})


@app.route("/api/data")
def get_data():
    return jsonify(manager.load_data())


@app.route("/api/save", methods=["POST"])
def save_example():
    try:
        print("=== 收到保存請求 ===")
        data = request.get_json()
        print(f"請求數據 keys: {data.keys()}")
        
        all_data = manager.load_data()
        print(f"當前數據: questions={len(all_data['questions'])}, extract={len(all_data['extract'])}, parse={len(all_data['parse'])}")

        id_str = str(data["id"])
        question = data["question"]
        db_id = data.get("db_id", "PosTest")
        
        # 打印收到的 SQL 和 questions_prompt
        sql = data.get("sql", "")
        questions_prompt = data.get("questions_prompt", "")
        print(f"處理範例 #{id_str}: {question[:50]}...")
        print(f"收到的 SQL (前 100 字元): {sql[:100]}...")
        print(f"收到的 questions_prompt 長度: {len(questions_prompt)}")
        if questions_prompt:
            # 提取 questions_prompt 中的 ORDER BY
            for line in questions_prompt.split('\n'):
                if 'ORDER BY' in line:
                    print(f"questions_prompt 中的 ORDER BY: {line.strip()}")

        # 1. 更新 extract - 直接使用用戶輸入的內容
        extract_prompt = data.get("extract_prompt", "")
        if extract_prompt and extract_prompt.strip():
            all_data["extract"][id_str] = {"prompt": extract_prompt}
            print(f"✅ 更新 extract[{id_str}]")
        elif id_str not in all_data["extract"]:
            # 只有在新增且沒有提供時才創建空的
            all_data["extract"][id_str] = {"prompt": ""}
            print(f"⚠️  創建空 extract[{id_str}]")

        # 2. 更新 parse - 直接使用用戶輸入的內容
        parse_prompt = data.get("parse_prompt", "")
        if parse_prompt and parse_prompt.strip():
            all_data["parse"][id_str] = {"prompt": parse_prompt}
            print(f"✅ 更新 parse[{id_str}]")
        elif id_str not in all_data["parse"]:
            # 只有在新增且沒有提供時才創建空的
            all_data["parse"][id_str] = {"prompt": ""}
            print(f"⚠️  創建空 parse[{id_str}]")

        # 3. 更新 questions
        questions_prompt = data.get("questions_prompt", "")
        sql = data.get("sql", "")
        
        if questions_prompt and questions_prompt.strip():
            # 用戶有提供 questions_prompt，直接使用
            print(f"✅ 使用用戶提供的 questions_prompt")
        else:
            # 沒有提供，使用基本信息生成
            questions_prompt = f"/* 回答以下問題：{question} */\n{sql}"
            print(f"⚠️  自動生成 questions_prompt")

        question_obj = {
            "question_id": int(data["id"]),
            "question": question,
            "db_id": db_id,
            "prompt": questions_prompt,
        }
        
        print(f"Question object: question_id={question_obj['question_id']}, question={question_obj['question'][:30]}..., prompt length={len(question_obj['prompt'])}")

        # 判斷是新增還是更新
        # 注意：陣列索引從 0 開始，所以 id < len 表示已存在
        question_id = int(data["id"])
        if question_id < len(all_data["questions"]):
            # 更新現有範例
            all_data["questions"][question_id] = question_obj
            print(f"更新範例 #{question_id}")
        else:
            # 新增範例
            all_data["questions"].append(question_obj)
            print(f"新增範例 #{question_id}")

        manager.save_data(all_data)
        print("✅ 保存成功")
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"❌ 保存失敗: {error_msg}")
        print(error_trace)
        return jsonify({"success": False, "error": error_msg}), 500


@app.route("/api/delete/<int:id>", methods=["DELETE"])
def delete_example(id):
    try:
        print(f"=== 刪除範例 #{id} ===")
        all_data = manager.load_data()
        
        # 檢查 ID 是否有效
        if id >= len(all_data["questions"]):
            return jsonify({"success": False, "error": f"範例 #{id} 不存在"}), 404

        # 1. 刪除 questions
        all_data["questions"].pop(id)
        print(f"已刪除 questions[{id}]")

        # 2. 重建 extract 和 parse（重新編號）
        new_extract = {}
        new_parse = {}
        
        # 遍歷所有 ID，跳過被刪除的，其他的重新編號
        for old_id in sorted([int(k) for k in all_data["extract"].keys()]):
            if old_id < id:
                # ID 小於被刪除的，保持不變
                new_extract[str(old_id)] = all_data["extract"][str(old_id)]
            elif old_id > id:
                # ID 大於被刪除的，減 1
                new_extract[str(old_id - 1)] = all_data["extract"][str(old_id)]
            # old_id == id 的情況，直接跳過（刪除）
        
        for old_id in sorted([int(k) for k in all_data["parse"].keys()]):
            if old_id < id:
                new_parse[str(old_id)] = all_data["parse"][str(old_id)]
            elif old_id > id:
                new_parse[str(old_id - 1)] = all_data["parse"][str(old_id)]
        
        all_data["extract"] = new_extract
        all_data["parse"] = new_parse
        
        # 3. 更新 questions 中的 question_id
        for i, q in enumerate(all_data["questions"]):
            q["question_id"] = i
        
        print(f"重新編號完成: questions={len(all_data['questions'])}, extract={len(new_extract)}, parse={len(new_parse)}")
        
        manager.save_data(all_data)
        print("✅ 刪除成功")
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"❌ 刪除失敗: {error_msg}")
        print(error_trace)
        return jsonify({"success": False, "error": error_msg}), 500


@app.route("/api/validate_sql", methods=["POST"])
def validate_sql():
    data = request.get_json()
    valid, message = manager.validate_sql(data["sql"])
    return jsonify({"valid": valid, "error": message if not valid else ""})


@app.route("/api/validate_all")
def validate_all():
    all_data = manager.load_data()
    passed = 0
    failed = 0

    for q in all_data["questions"]:
        sql = q.get("prompt", "").split("\\n")[-1]
        valid, _ = manager.validate_sql(sql)
        if valid:
            passed += 1
        else:
            failed += 1

    return jsonify({"passed": passed, "failed": failed})


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 啟動 Few-shot 完整管理界面")
    print("=" * 60)
    print("訪問 http://localhost:5003 開始管理")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5003, debug=False)
