# auth_service/database.py
import sqlite3
import hashlib
import os
from datetime import datetime

class AuthDatabase:
    def __init__(self, db_path="auth.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create artists table (for makeup artists)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                specialization TEXT,
                experience_years INTEGER,
                rating FLOAT DEFAULT 0,
                is_available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    @staticmethod
    def hash_password(password):
        """Hash password using SHA256"""
        salt = os.urandom(32)
        return hashlib.sha256((password + salt.hex()).encode()).hexdigest()

    def create_user(self, name, email, phone, password):
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple hash (in production, use bcrypt)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
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
