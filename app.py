from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

AUTH_URL = "http://auth_service:5001"
BOOK_URL = "http://book_service:5002"
BORROW_URL = "http://borrow_service:5003"

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("books"))
    return redirect(url_for("signin"))

# ---------- AUTH ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"]
        }
        try:
            res = requests.post(f"{AUTH_URL}/signup", json=data, timeout=5)
            if res.status_code == 201:
                flash("Signup successful!", "success")
                return redirect(url_for("signin"))
            else:
                flash("Signup failed", "danger")
        except requests.exceptions.RequestException:
            flash("Service unavailable", "danger")
    return render_template("signup.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        data = {"email": request.form["email"], "password": request.form["password"]}
        try:
            res = requests.post(f"{AUTH_URL}/signin", json=data, timeout=5)
            if res.status_code == 200:
                user = res.json()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("books"))
            else:
                flash("Invalid credentials", "danger")
        except requests.exceptions.RequestException:
            flash("Service unavailable", "danger")
    return render_template("signin.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("signin"))

# ---------- BOOKS ----------
@app.route("/books")
def books():
    if "user_id" not in session:
        return redirect(url_for("signin"))
    try:
        res = requests.get(f"{BOOK_URL}/books", timeout=5)
        return render_template("books.html", books=res.json())
    except requests.exceptions.RequestException:
        flash("Book service unavailable", "danger")
        return render_template("books.html", books=[])

# ---------- BORROW ----------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))
    data = {"user_id": session["user_id"], "book_id": book_id}
    try:
        res = requests.post(f"{BORROW_URL}/borrow", json=data, timeout=5)
        if res.status_code == 201:
            flash("Book borrowed!", "success")
        elif res.status_code == 400:
            flash("Book not available", "warning")
        else:
            flash("Borrow failed", "danger")
    except requests.exceptions.RequestException:
        flash("Service unavailable", "danger")
    return redirect(url_for("books"))

@app.route("/mybooks")
def mybooks():
    if "user_id" not in session:
        return redirect(url_for("signin"))
    try:
        res = requests.get(f"{BORROW_URL}/mybooks/{session['user_id']}", timeout=5)
        return render_template("borrow.html", books=res.json())
    except requests.exceptions.RequestException:
        flash("Service unavailable", "danger")
        return render_template("borrow.html", books=[])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)    
    try:
        res = requests.get(f"{SERVICE_URL}/services")
        if res.status_code == 200:
            return render_template("services.html", services=res.json())
        else:
            flash("Unable to fetch services.", "warning")
            return render_template("services.html", services=[])
    except:
        flash("Service unavailable. Please try again later.", "danger")
        return render_template("services.html", services=[])

@app.route("/service/<int:service_id>")
def service_detail(service_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    try:
        res = requests.get(f"{SERVICE_URL}/service/{service_id}")
        if res.status_code == 200:
            return render_template("service_detail.html", service=res.json())
        else:
            flash("Service not found.", "danger")
            return redirect(url_for("services"))
    except:
        flash("Service unavailable.", "danger")
        return redirect(url_for("services"))

# ---------- BOOKING ----------
@app.route("/book/<int:service_id>", methods=["GET", "POST"])
def book(service_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    if request.method == "POST":
        booking_data = {
            "user_id": session["user_id"],
            "service_id": service_id,
            "booking_date": request.form["booking_date"],
            "booking_time": request.form["booking_time"],
            "artist_preference": request.form.get("artist_preference", ""),
            "special_requests": request.form.get("special_requests", "")
        }
        
        try:
            res = requests.post(f"{BOOKING_URL}/book", json=booking_data)
            if res.status_code == 201:
                flash("Booking confirmed successfully!", "success")
                return redirect(url_for("my_bookings"))
            else:
                flash("Booking failed. Please try again.", "danger")
        except:
            flash("Booking service unavailable.", "danger")
    
    # GET request - show booking form
    try:
        service_res = requests.get(f"{SERVICE_URL}/service/{service_id}")
        if service_res.status_code == 200:
            return render_template("book_service.html", service=service_res.json())
        else:
            flash("Service not available.", "danger")
            return redirect(url_for("services"))
    except:
        flash("Service unavailable.", "danger")
        return redirect(url_for("services"))

@app.route("/my_bookings")
def my_bookings():
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    try:
        res = requests.get(f"{BOOKING_URL}/my_bookings/{session['user_id']}")
        if res.status_code == 200:
            return render_template("my_bookings.html", bookings=res.json())
        else:
            return render_template("my_bookings.html", bookings=[])
    except:
        flash("Unable to fetch your bookings.", "warning")
        return render_template("my_bookings.html", bookings=[])

@app.route("/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    try:
        res = requests.delete(f"{BOOKING_URL}/cancel_booking/{booking_id}")
        if res.status_code == 200:
            flash("Booking cancelled successfully.", "info")
        else:
            flash("Failed to cancel booking.", "danger")
    except:
        flash("Booking service unavailable.", "danger")
    
    return redirect(url_for("my_bookings"))

@app.route("/reschedule/<int:booking_id>", methods=["GET", "POST"])
def reschedule(booking_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    if request.method == "POST":
        data = {
            "booking_date": request.form["booking_date"],
            "booking_time": request.form["booking_time"]
        }
        
        try:
            res = requests.put(f"{BOOKING_URL}/reschedule/{booking_id}", json=data)
            if res.status_code == 200:
                flash("Booking rescheduled successfully!", "success")
                return redirect(url_for("my_bookings"))
            else:
                flash("Failed to reschedule booking.", "danger")
        except:
            flash("Booking service unavailable.", "danger")
    
    # GET - show reschedule form
    try:
        booking_res = requests.get(f"{BOOKING_URL}/booking/{booking_id}")
        if booking_res.status_code == 200:
            return render_template("reschedule.html", booking=booking_res.json())
        else:
            flash("Booking not found.", "danger")
            return redirect(url_for("my_bookings"))
    except:
        flash("Booking service unavailable.", "danger")
        return redirect(url_for("my_bookings"))

# ---------- USER PROFILE ----------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("signin"))
    
    try:
        res = requests.get(f"{AUTH_URL}/user/{session['user_id']}")
        if res.status_code == 200:
            return render_template("profile.html", user=res.json())
        else:
            flash("Unable to fetch profile.", "warning")
            return render_template("profile.html")
    except:
        flash("Auth service unavailable.", "danger")
        return render_template("profile.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
