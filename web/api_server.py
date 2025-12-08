#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web API 服務器 - 提供 REST API 接口
使用方法:
    python api_server.py
    
然後訪問:
    POST http://localhost:5000/query
    Body: {"question": "有多少筆銷售交易？"}
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 添加父目錄和 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from query_interface import QueryInterface

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 初始化查詢接口
query_interface = QueryInterface()

@app.route('/')
def home():
    """首頁"""
    return jsonify({
        "service": "OpenSearch-SQL API",
        "version": "1.0",
        "endpoints": {
            "POST /query": "提交自然語言問題，返回 SQL 查詢",
            "GET /health": "健康檢查"
        },
        "example": {
            "url": "POST /query",
            "body": {
                "question": "有多少筆銷售交易？"
            },
            "response": {
                "question": "有多少筆銷售交易？",
                "sql": "SELECT COUNT(*) FROM pos_sale",
                "status": "success"
            }
        }
    })

@app.route('/health')
def health():
    """健康檢查"""
    return jsonify({"status": "healthy"})

@app.route('/query', methods=['POST'])
def query():
    """
    處理查詢請求
    
    Request Body:
        {
            "question": "自然語言問題"
        }
    
    Response:
        {
            "question": "原始問題",
            "sql": "生成的 SQL",
            "status": "success" | "error",
            "error": "錯誤訊息（如果有）"
        }
    """
    try:
        # 獲取請求數據
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "status": "error",
                "error": "請提供 'question' 參數"
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                "status": "error",
                "error": "問題不能為空"
            }), 400
        
        # 執行查詢
        sql = query_interface.query(question)
        
        if sql:
            return jsonify({
                "question": question,
                "sql": sql,
                "status": "success"
            })
        else:
            return jsonify({
                "question": question,
                "status": "error",
                "error": "無法生成 SQL"
            }), 500
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/batch_query', methods=['POST'])
def batch_query():
    """
    批量查詢
    
    Request Body:
        {
            "questions": ["問題1", "問題2", ...]
        }
    
    Response:
        {
            "results": [
                {"question": "問題1", "sql": "SQL1", "status": "success"},
                {"question": "問題2", "sql": "SQL2", "status": "success"},
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'questions' not in data:
            return jsonify({
                "status": "error",
                "error": "請提供 'questions' 參數（數組）"
            }), 400
        
        questions = data['questions']
        
        if not isinstance(questions, list):
            return jsonify({
                "status": "error",
                "error": "'questions' 必須是數組"
            }), 400
        
        results = []
        for question in questions:
            try:
                sql = query_interface.query(question)
                results.append({
                    "question": question,
                    "sql": sql,
                    "status": "success" if sql else "error"
                })
            except Exception as e:
                results.append({
                    "question": question,
                    "status": "error",
                    "error": str(e)
                })
        
        return jsonify({
            "results": results
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 啟動 OpenSearch-SQL API 服務器")
    print("=" * 60)
    print("訪問 http://localhost:5000 查看 API 文檔")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
