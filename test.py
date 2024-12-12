from flask import Flask, jsonify, request
import mysql.connector
import base64

app = Flask(__name__)

# 데이터베이스 연결 설정
db_config = {
    "host": "localhost",  # 또는 "127.0.0.1"
    "user": "myuser",
    "password": "mypassword",  # myuser의 실제 비밀번호
    "database": "mydb",
    "port": 3306
}

# 기존 테스트 엔드포인트
@app.route('/test', methods=['GET'])
def test_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Connection successful",
            "db_status": "Connected",
            "users_count": result['count']
        })
    except Exception as e:
        return jsonify({
            "message": "Test failed",
            "error": str(e)
        }), 500

# 회원가입 API
@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 비밀번호 인코딩
        password_hash = base64.b64encode(data['password'].encode('utf-8')).decode('utf-8')
        
        cursor.execute(
            "INSERT INTO users (email, password_hash, name, phone) VALUES (%s, %s, %s, %s)",
            (data['email'], password_hash, data['name'], data.get('phone'))
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        })
    except Exception as e:
        return jsonify({
            "message": "Registration failed",
            "error": str(e)
        }), 500

# 로그인 API
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 비밀번호 인코딩
        password_hash = base64.b64encode(data['password'].encode('utf-8')).decode('utf-8')
        
        cursor.execute(
            "SELECT user_id, email, name FROM users WHERE email = %s AND password_hash = %s",
            (data['email'], password_hash)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return jsonify({
                "message": "Login successful",
                "user": user
            })
        else:
            return jsonify({
                "message": "Invalid credentials"
            }), 401
            
    except Exception as e:
        return jsonify({
            "message": "Login failed",
            "error": str(e)
        }), 500

# 사용자 목록 조회 API
@app.route('/users', methods=['GET'])
def get_users():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT user_id, email, name, created_at FROM users")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            "users": users
        })
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch users",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 