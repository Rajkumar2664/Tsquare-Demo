from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

DB_CONFIG = {
    'host': 'db',
    'user': 'root',
    'password': 'password',
    'database': 'library_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/borrow", methods=["POST"])
def borrow_book():
    data = request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    
    if not all([user_id, book_id]):
        return jsonify({"error": "Missing fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if book is available
    cursor.execute("SELECT available_copies FROM books WHERE id = %s FOR UPDATE", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        cursor.close()
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    if book['available_copies'] <= 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "No copies available"}), 400
    
    # Check if user already borrowed this book
    cursor.execute(
        "SELECT id FROM borrowings WHERE user_id = %s AND book_id = %s AND returned_date IS NULL",
        (user_id, book_id)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Book already borrowed"}), 400
    
    # Create borrowing record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    cursor.execute(
        "INSERT INTO borrowings (user_id, book_id, borrow_date, due_date) VALUES (%s, %s, %s, %s)",
        (user_id, book_id, borrow_date, due_date)
    )
    
    # Decrease available copies
    cursor.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id = %s",
        (book_id,)
    )
    
    conn.commit()
    borrowing_id = cursor.lastrowid
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "id": borrowing_id,
        "message": "Book borrowed successfully",
        "due_date": due_date.isoformat()
    }), 201

@app.route("/return/<int:borrowing_id>", methods=["POST"])
def return_book(borrowing_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get borrowing record
    cursor.execute(
        "SELECT book_id FROM borrowings WHERE id = %s AND returned_date IS NULL",
        (borrowing_id,)
    )
    borrowing = cursor.fetchone()
    
    if not borrowing:
        cursor.close()
        conn.close()
        return jsonify({"error": "Invalid borrowing record"}), 404
    
    # Update borrowing record
    cursor.execute(
        "UPDATE borrowings SET returned_date = %s WHERE id = %s",
        (datetime.now(), borrowing_id)
    )
    
    # Increase available copies
    cursor.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE id = %s",
        (borrowing['book_id'],)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Book returned successfully"}), 200

@app.route("/mybooks/<int:user_id>", methods=["GET"])
def get_my_books(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT b.id, b.title, b.author, br.borrow_date, br.due_date, br.id as borrowing_id
        FROM borrowings br
        JOIN books b ON br.book_id = b.id
        WHERE br.user_id = %s AND br.returned_date IS NULL
    """, (user_id,))
    
    books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(books), 200

@app.route("/borrowings", methods=["GET"])
def get_all_borrowings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT br.id, u.name as user_name, b.title as book_title, 
               br.borrow_date, br.due_date, br.returned_date
        FROM borrowings br
        JOIN users u ON br.user_id = u.id
        JOIN books b ON br.book_id = b.id
        ORDER BY br.borrow_date DESC
    """)
    
    borrowings = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(borrowings), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
  
