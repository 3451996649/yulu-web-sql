from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
import os
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库文件路径
DB_FILE = os.getenv('DB_FILE', 'quotes.db')

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_client_id 
        ON quotes(client_id)
    ''')
    conn.commit()
    conn.close()

@app.route('/quotes', methods=['GET', 'POST'])
def handle_quotes():
    """处理语录请求"""
    try:
        # 解析JSON数据
        if request.method == 'POST':
            request_data = request.get_json()
        else:
            # GET 请求可以从查询参数获取数据
            request_data = request.args.to_dict()
        
        # 从请求中获取类型和ID
        request_type = request_data.get('type')
        client_id = request_data.get('id', 'default')  # 提供默认id
        
        if request_type == "get":
            return send_message(client_id)
        elif request_type == "upload":
            message = request_data.get('message')
            return save_message(client_id, message)
        elif request_type == "delete":
            quote_id = request_data.get('quote_id')
            return delete_message(client_id, quote_id)
        elif request_type == "clear":
            return clear_messages(client_id)
        else:
            # 返回错误响应
            return jsonify({"error": "未知请求类型"}), 400
            
    except Exception as e:
        print(f"处理请求时出错: {e}")
        return jsonify({"error": str(e)}), 500

def send_message(client_id):
    """获取指定客户端的语录列表"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, message, created_at FROM quotes WHERE client_id = ? ORDER BY created_at DESC',
            (client_id,)
        )
        quotes = []
        for row in cursor.fetchall():
            quotes.append({
                'id': row[0],
                'message': row[1],
                'created_at': row[2]
            })
        return jsonify(quotes)
    except Exception as e:
        return jsonify({"error": f"获取语录失败: {str(e)}"}), 500
    finally:
        conn.close()

def save_message(client_id, message):
    """保存语录到数据库"""
    if not message or not message.strip():
        return jsonify({"error": "语录内容不能为空"}), 400
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO quotes (client_id, message) VALUES (?, ?)',
            (client_id, message.strip())
        )
        conn.commit()
        return jsonify({
            "status": "success", 
            "message": "语录保存成功",
            "quote_id": cursor.lastrowid
        })
    except Exception as e:
        return jsonify({"error": f"保存语录失败: {str(e)}"}), 500
    finally:
        conn.close()

def delete_message(client_id, quote_id):
    """删除指定语录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM quotes WHERE id = ? AND client_id = ?',
            (quote_id, client_id)
        )
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"status": "success", "message": "语录删除成功"})
        else:
            return jsonify({"error": "语录不存在或无权限删除"}), 404
    except Exception as e:
        return jsonify({"error": f"删除语录失败: {str(e)}"}), 500
    finally:
        conn.close()

def clear_messages(client_id):
    """清空指定客户端的所有语录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM quotes WHERE client_id = ?',
            (client_id,)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "语录清空成功"})
    except Exception as e:
        return jsonify({"error": f"清空语录失败: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 获取总语录数
        cursor.execute('SELECT COUNT(*) FROM quotes')
        total_quotes = cursor.fetchone()[0]
        
        # 获取客户端数量
        cursor.execute('SELECT COUNT(DISTINCT client_id) FROM quotes')
        total_clients = cursor.fetchone()[0]
        
        # 获取最近添加的语录
        cursor.execute('''
            SELECT client_id, message, created_at 
            FROM quotes 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_quotes = []
        for row in cursor.fetchall():
            recent_quotes.append({
                'client_id': row[0],
                'message': row[1],
                'created_at': row[2]
            })
        
        return jsonify({
            'total_quotes': total_quotes,
            'total_clients': total_clients,
            'recent_quotes': recent_quotes
        })
    except Exception as e:
        return jsonify({"error": f"获取统计信息失败: {str(e)}"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("数据库初始化完成")
    print("HTTP服务器启动")
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 6673))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=False)
