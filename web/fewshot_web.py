#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Few-shot Web 管理界面
使用方法:
    python fewshot_web.py
    然後訪問 http://localhost:5001
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import sqlite3
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Few-shot 管理類
class FewShotManager:
    def __init__(self, db_root_path='PosTest'):
        self.db_root_path = db_root_path
        self.fewshot_file = Path(db_root_path) / 'fewshot' / 'managed_examples.json'
        self.db_path = Path(db_root_path) / 'dev' / 'dev_databases' / db_root_path / f'{db_root_path}.sqlite'
        
        if not self.fewshot_file.exists():
            self.fewshot_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fewshot_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
    
    def load_fewshot(self):
        with open(self.fewshot_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_fewshot(self, data):
        with open(self.fewshot_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def validate_sql(self, sql):
        if not self.db_path.exists():
            return False, "資料庫文件不存在"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.close()
            return True, "SQL 驗證通過"
        except Exception as e:
            return False, str(e)

manager = FewShotManager()

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Few-shot 管理系統</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
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
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-success {
            background: #4caf50;
            color: white;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-warning {
            background: #ff9800;
            color: white;
        }
        
        .btn-small {
            padding: 5px 10px;
            font-size: 12px;
        }
        
        .search-box {
            flex: 1;
            min-width: 200px;
        }
        
        .search-box input {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .examples-list {
            display: grid;
            gap: 15px;
        }
        
        .example-item {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            transition: all 0.3s;
        }
        
        .example-item:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        
        .example-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .example-id {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 600;
        }
        
        .difficulty {
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .difficulty-simple {
            background: #e8f5e9;
            color: #4caf50;
        }
        
        .difficulty-moderate {
            background: #fff3e0;
            color: #ff9800;
        }
        
        .difficulty-challenging {
            background: #ffebee;
            color: #f44336;
        }
        
        .example-question {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        
        .example-sql {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            margin-bottom: 10px;
            overflow-x: auto;
        }
        
        .example-actions {
            display: flex;
            gap: 10px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.show {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #666;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 80px;
            font-family: 'Monaco', 'Courier New', monospace;
        }
        
        .modal-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            flex: 1;
            min-width: 150px;
            background: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        
        .validation-result {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .validation-success {
            background: #e8f5e9;
            color: #4caf50;
        }
        
        .validation-error {
            background: #ffebee;
            color: #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Few-shot 管理系統</h1>
            <p>管理和優化你的 Few-shot 範例</p>
        </div>
        
        <div class="card">
            <div class="stats" id="stats">
                <div class="stat-item">
                    <div class="stat-value" id="totalCount">0</div>
                    <div class="stat-label">總範例數</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="simpleCount">0</div>
                    <div class="stat-label">簡單</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="moderateCount">0</div>
                    <div class="stat-label">中等</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="challengingCount">0</div>
                    <div class="stat-label">困難</div>
                </div>
            </div>
            
            <div class="toolbar">
                <button class="btn btn-primary" onclick="showAddModal()">
                    ➕ 添加範例
                </button>
                <button class="btn btn-success" onclick="validateAll()">
                    ✅ 驗證全部
                </button>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 搜尋問題或 SQL..." 
                           onkeyup="filterExamples()">
                </div>
            </div>
            
            <div class="examples-list" id="examplesList">
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div>還沒有 Few-shot 範例</div>
                    <div>點擊「添加範例」開始</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 添加/編輯模態框 -->
    <div class="modal" id="editModal">
        <div class="modal-content">
            <div class="modal-header" id="modalTitle">添加範例</div>
            <form id="exampleForm" onsubmit="saveExample(event)">
                <input type="hidden" id="editId">
                
                <div class="form-group">
                    <label>問題 *</label>
                    <input type="text" id="question" required placeholder="例如：有多少筆銷售交易？">
                </div>
                
                <div class="form-group">
                    <label>SQL *</label>
                    <textarea id="sql" required placeholder="SELECT COUNT(*) FROM pos_sale"></textarea>
                    <button type="button" class="btn btn-warning btn-small" onclick="validateSQL()" 
                            style="margin-top: 5px;">
                        驗證 SQL
                    </button>
                    <div id="validationResult"></div>
                </div>
                
                <div class="form-group">
                    <label>難度 *</label>
                    <select id="difficulty" required>
                        <option value="simple">簡單 (Simple)</option>
                        <option value="moderate">中等 (Moderate)</option>
                        <option value="challenging">困難 (Challenging)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>提示 (可選)</label>
                    <input type="text" id="evidence" placeholder="例如：需要 JOIN 兩個表">
                </div>
                
                <div class="modal-actions">
                    <button type="button" class="btn" onclick="closeModal()">取消</button>
                    <button type="submit" class="btn btn-primary">保存</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        let examples = [];
        
        // 載入範例
        async function loadExamples() {
            try {
                const response = await fetch('/api/examples');
                examples = await response.json();
                renderExamples();
                updateStats();
            } catch (error) {
                console.error('載入失敗:', error);
            }
        }
        
        // 渲染範例列表
        function renderExamples(filteredExamples = null) {
            const list = document.getElementById('examplesList');
            const data = filteredExamples || examples;
            
            if (data.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <div>${filteredExamples ? '沒有符合的範例' : '還沒有 Few-shot 範例'}</div>
                        <div>${filteredExamples ? '' : '點擊「添加範例」開始'}</div>
                    </div>
                `;
                return;
            }
            
            list.innerHTML = data.map(ex => `
                <div class="example-item">
                    <div class="example-header">
                        <span class="example-id">#${ex.question_id}</span>
                        <span class="difficulty difficulty-${ex.difficulty}">${ex.difficulty}</span>
                    </div>
                    <div class="example-question">${ex.question}</div>
                    <div class="example-sql">${ex.SQL}</div>
                    ${ex.evidence ? `<div style="color: #666; font-size: 14px; margin-bottom: 10px;">💡 ${ex.evidence}</div>` : ''}
                    <div class="example-actions">
                        <button class="btn btn-primary btn-small" onclick="editExample(${ex.question_id})">
                            ✏️ 編輯
                        </button>
                        <button class="btn btn-danger btn-small" onclick="deleteExample(${ex.question_id})">
                            🗑️ 刪除
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        // 更新統計
        function updateStats() {
            document.getElementById('totalCount').textContent = examples.length;
            document.getElementById('simpleCount').textContent = 
                examples.filter(e => e.difficulty === 'simple').length;
            document.getElementById('moderateCount').textContent = 
                examples.filter(e => e.difficulty === 'moderate').length;
            document.getElementById('challengingCount').textContent = 
                examples.filter(e => e.difficulty === 'challenging').length;
        }
        
        // 搜尋過濾
        function filterExamples() {
            const keyword = document.getElementById('searchInput').value.toLowerCase();
            if (!keyword) {
                renderExamples();
                return;
            }
            
            const filtered = examples.filter(ex => 
                ex.question.toLowerCase().includes(keyword) ||
                ex.SQL.toLowerCase().includes(keyword) ||
                (ex.evidence && ex.evidence.toLowerCase().includes(keyword))
            );
            renderExamples(filtered);
        }
        
        // 顯示添加模態框
        function showAddModal() {
            document.getElementById('modalTitle').textContent = '添加範例';
            document.getElementById('exampleForm').reset();
            document.getElementById('editId').value = '';
            document.getElementById('validationResult').innerHTML = '';
            document.getElementById('editModal').classList.add('show');
        }
        
        // 編輯範例
        function editExample(id) {
            const example = examples.find(e => e.question_id === id);
            if (!example) return;
            
            document.getElementById('modalTitle').textContent = '編輯範例';
            document.getElementById('editId').value = id;
            document.getElementById('question').value = example.question;
            document.getElementById('sql').value = example.SQL;
            document.getElementById('difficulty').value = example.difficulty;
            document.getElementById('evidence').value = example.evidence || '';
            document.getElementById('validationResult').innerHTML = '';
            document.getElementById('editModal').classList.add('show');
        }
        
        // 關閉模態框
        function closeModal() {
            document.getElementById('editModal').classList.remove('show');
        }
        
        // 驗證 SQL
        async function validateSQL() {
            const sql = document.getElementById('sql').value;
            const resultDiv = document.getElementById('validationResult');
            
            if (!sql) {
                resultDiv.innerHTML = '<div class="validation-error">請輸入 SQL</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div>驗證中...</div>';
            
            try {
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sql: sql})
                });
                const data = await response.json();
                
                if (data.valid) {
                    resultDiv.innerHTML = `<div class="validation-success">✅ ${data.message}</div>`;
                } else {
                    resultDiv.innerHTML = `<div class="validation-error">❌ ${data.message}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="validation-error">❌ 驗證失敗</div>`;
            }
        }
        
        // 保存範例
        async function saveExample(event) {
            event.preventDefault();
            
            const id = document.getElementById('editId').value;
            const data = {
                question: document.getElementById('question').value,
                SQL: document.getElementById('sql').value,
                difficulty: document.getElementById('difficulty').value,
                evidence: document.getElementById('evidence').value
            };
            
            try {
                const url = id ? `/api/examples/${id}` : '/api/examples';
                const method = id ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    closeModal();
                    loadExamples();
                } else {
                    alert('保存失敗');
                }
            } catch (error) {
                alert('保存失敗: ' + error.message);
            }
        }
        
        // 刪除範例
        async function deleteExample(id) {
            if (!confirm('確定要刪除這個範例嗎？')) return;
            
            try {
                const response = await fetch(`/api/examples/${id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadExamples();
                } else {
                    alert('刪除失敗');
                }
            } catch (error) {
                alert('刪除失敗: ' + error.message);
            }
        }
        
        // 驗證全部
        async function validateAll() {
            if (examples.length === 0) {
                alert('沒有範例可驗證');
                return;
            }
            
            if (!confirm(`確定要驗證全部 ${examples.length} 個範例嗎？`)) return;
            
            try {
                const response = await fetch('/api/validate-all');
                const data = await response.json();
                
                alert(`驗證完成！\n通過: ${data.passed}\n失敗: ${data.failed}`);
            } catch (error) {
                alert('驗證失敗: ' + error.message);
            }
        }
        
        // 初始化
        loadExamples();
        
        // 點擊模態框外部關閉
        document.getElementById('editModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """首頁"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """獲取所有範例"""
    return jsonify(manager.load_fewshot())

@app.route('/api/examples', methods=['POST'])
def add_example():
    """添加範例"""
    data = request.get_json()
    examples = manager.load_fewshot()
    
    # 生成新 ID
    new_id = max([e.get('question_id', 0) for e in examples], default=-1) + 1
    
    new_example = {
        "question_id": new_id,
        "db_id": manager.db_root_path,
        "question": data['question'],
        "raw_question": data['question'],
        "evidence": data.get('evidence', ''),
        "SQL": data['SQL'],
        "difficulty": data['difficulty']
    }
    
    examples.append(new_example)
    manager.save_fewshot(examples)
    
    return jsonify({"success": True, "id": new_id})

@app.route('/api/examples/<int:id>', methods=['PUT'])
def update_example(id):
    """更新範例"""
    data = request.get_json()
    examples = manager.load_fewshot()
    
    for i, ex in enumerate(examples):
        if ex.get('question_id') == id:
            examples[i].update({
                "question": data['question'],
                "raw_question": data['question'],
                "evidence": data.get('evidence', ''),
                "SQL": data['SQL'],
                "difficulty": data['difficulty']
            })
            manager.save_fewshot(examples)
            return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Not found"}), 404

@app.route('/api/examples/<int:id>', methods=['DELETE'])
def delete_example(id):
    """刪除範例"""
    examples = manager.load_fewshot()
    examples = [e for e in examples if e.get('question_id') != id]
    manager.save_fewshot(examples)
    return jsonify({"success": True})

@app.route('/api/validate', methods=['POST'])
def validate_sql():
    """驗證 SQL"""
    data = request.get_json()
    valid, message = manager.validate_sql(data['sql'])
    return jsonify({"valid": valid, "message": message})

@app.route('/api/validate-all', methods=['GET'])
def validate_all():
    """驗證所有範例"""
    examples = manager.load_fewshot()
    passed = 0
    failed = 0
    
    for ex in examples:
        valid, _ = manager.validate_sql(ex.get('SQL', ''))
        if valid:
            passed += 1
        else:
            failed += 1
    
    return jsonify({"passed": passed, "failed": failed})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 啟動 Few-shot Web 管理界面")
    print("=" * 60)
    print("訪問 http://localhost:5001 開始管理")
    print("按 Ctrl+C 停止服務器")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False)
