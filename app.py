from flask import Flask, request, jsonify, render_template
import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "movie.db"


# ================= DATABASE =================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            poster_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# إنشاء الجداول عند تشغيل التطبيق
init_db()


# ================= PAGES =================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/watchlist-page", methods=["GET"])
def watchlist_page():
    return render_template("watchlist.html")


# ================= MOVIES =================

@app.route("/movies", methods=["GET"])
def movies():

    if not API_KEY:
        return jsonify({
            "error": "TMDB_API_KEY is not configured"
        }), 500

    url = "https://api.themoviedb.org/3/movie/popular"

    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "page": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return jsonify({
                "error": "Cannot connect to TMDB",
                "status": response.status_code
            }), 500

        return jsonify(response.json())

    except requests.RequestException as e:
        return jsonify({
            "error": "TMDB connection failed",
            "details": str(e)
        }), 500


# ================= REGISTER =================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid JSON data"
        }), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email and password are required"
        }), 400

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

        return jsonify({
            "error": "Email already exists"
        }), 400

    finally:
        conn.close()


# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid JSON data"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

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

    return jsonify({
        "error": "Invalid email or password"
    }), 401


# ================= PROFILE =================

@app.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, email
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(dict(user))


# ================= ADD TO WATCHLIST =================

@app.route("/watchlist", methods=["POST"])
def add_movie():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid JSON data"
        }), 400

    user_id = data.get("user_id")
    movie_id = data.get("movie_id")
    title = data.get("title")
    poster_path = data.get("poster_path")

    if not user_id or not movie_id or not title:
        return jsonify({
            "error": "user_id, movie_id and title are required"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # نتأكدو بلي المستخدم موجود
    cursor.execute(
        "SELECT id FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        conn.close()

        return jsonify({
            "error": "User not found"
        }), 404

    cursor.execute("""
        INSERT INTO watchlist
        (user_id, movie_id, title, poster_path)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        movie_id,
        title,
        poster_path
    ))

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


# ================= GET WATCHLIST =================

@app.route("/watchlist/<int:user_id>", methods=["GET"])
def get_watchlist(user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, movie_id, title, poster_path
        FROM watchlist
        WHERE user_id = ?
    """, (user_id,))

    movies = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(movies)


# ================= DELETE MOVIE =================

@app.route("/watchlist/<int:id>", methods=["DELETE"])
def delete_movie(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM watchlist WHERE id = ?",
        (id,)
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:
        return jsonify({
            "error": "Movie not found"
        }), 404

    return jsonify({
        "message": "Movie deleted successfully"
    })


# ================= DELETE ACCOUNT =================

@app.route("/account/<int:user_id>", methods=["DELETE"])
def delete_account(user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM watchlist WHERE user_id = ?",
        (user_id,)
    )

    cursor.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "message": "Account deleted successfully"
    })


# ================= RUN =================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )