from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_CONFIG = {
    'host': 'db',
    'user': 'root',
    'password': 'password',
    'database': 'library_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/books", methods=["GET"])
def get_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, title, author, isbn, available_copies FROM books")
    books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(books), 200

@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, title, author, isbn, available_copies FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if book:
        return jsonify(book), 200
    return jsonify({"error": "Book not found"}), 404

@app.route("/books", methods=["POST"])
def create_book():
    data = request.json
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    copies = data.get('available_copies', 1)
    
    if not all([title, author, isbn]):
        return jsonify({"error": "Missing fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO books (title, author, isbn, available_copies) VALUES (%s, %s, %s, %s)",
        (title, author, isbn, copies)
    )
    conn.commit()
    
    book_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({"id": book_id, "message": "Book created"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
