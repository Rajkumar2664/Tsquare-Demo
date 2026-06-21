from flask import Flask, request, jsonify
import mysql.connector
import hashlib
import os

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'db',
    'user': 'root',
    'password': 'password',
    'database': 'library_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + key

def verify_password(stored_password, provided_password):
    salt = stored_password[:32]
    stored_key = stored_password[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return new_key == stored_key

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({"error": "Missing fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "User already exists"}), 400
    
    # Hash password and create user
    hashed_password = hash_password(password)
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hashed_password)
    )
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return jsonify({"message": "User created successfully"}), 201

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({"error": "Missing fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user and verify_password(user['password'], password):
        return jsonify({
            "user_id": user['id'],
            "name": user['name']
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)            cursor.execute('''
                INSERT INTO users (name, email, phone, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {"user_id": user_id, "message": "User created successfully"}
        except sqlite3.IntegrityError:
            return {"error": "Email already exists"}
        except Exception as e:
            return {"error": str(e)}

    def authenticate_user(self, email, password):
        """Authenticate user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                SELECT user_id, name, email, phone 
                FROM users 
                WHERE email = ? AND password_hash = ? AND is_active = 1
            ''', (email, password_hash))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "user_id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "phone": user[3]
                }
            else:
                return {"error": "Invalid credentials"}
        except Exception as e:
            return {"error": str(e)}

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, name, email, phone, created_at
                FROM users 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "user_id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "phone": user[3],
                    "created_at": user[4]
                }
            else:
                return {"error": "User not found"}
        except Exception as e:
            return {"error": str(e)}

    def update_user(self, user_id, **kwargs):
        """Update user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query dynamically
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'phone']:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return {"error": "No fields to update"}
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return {"message": "User updated successfully"}
        except Exception as e:
            return {"error": str(e)}
