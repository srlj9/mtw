from flask import Flask, request, jsonify, render_template
import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "movie.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ========== الصفحات (Frontend) ==========

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/login", methods=["GET"])
def login_page():
    return render_template('login.html')

@app.route("/watchlist-page", methods=["GET"])
def watchlist_page():
    return render_template('watchlist.html')


# ========== الأفلام ==========

@app.route("/movies", methods=["GET"])
def movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Cannot connect to TMDB"}), 500
    return jsonify(response.json())


# ========== Register ==========

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Username, email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, password))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({
            "message": "Account created successfully",
            "user_id": user_id,
            "username": username
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400
    finally:
        conn.close()


# ========== Login ==========

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email
        FROM users
        WHERE email = ? AND password = ?
    """, (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"]
        })
    return jsonify({"error": "Invalid email or password"}), 401


# ========== Profile ==========

@app.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))


# ========== Add to Watchlist ==========

@app.route("/watchlist", methods=["POST"])
def add_movie():
    data = request.get_json()
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")
    title = data.get("title")
    poster_path = data.get("poster_path")

    if not user_id or not movie_id or not title:
        return jsonify({"error": "user_id, movie_id and title are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watchlist (user_id, movie_id, title, poster_path)
        VALUES (?, ?, ?, ?)
    """, (user_id, movie_id, title, poster_path))
    conn.commit()
    watchlist_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Movie added successfully",
        "id": watchlist_id,
        "user_id": user_id,
        "movie_id": movie_id,
        "title": title,
        "poster_path": poster_path
    }), 201


# ========== Get Watchlist ==========

@app.route("/watchlist/<int:user_id>", methods=["GET"])
def get_watchlist(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, movie_id, title, poster_path
        FROM watchlist
        WHERE user_id = ?
    """, (user_id,))
    movies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(movies)


# ========== Delete Movie ==========

@app.route("/watchlist/<int:id>", methods=["DELETE"])
def delete_movie(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE id = ?", (id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify({"message": "Movie deleted successfully"})


# ========== Delete Account ==========

@app.route("/account/<int:user_id>", methods=["DELETE"])
def delete_account(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "Account deleted successfully"})

if __name__ == "__main__":
    app.run(debug=True)