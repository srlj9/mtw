```python
import sqlite3

# Create (or open) the database file
conn = sqlite3.connect("movie.db")

# Create a cursor
cursor = conn.cursor()

# Execute SQL
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    title TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Save changes
conn.commit()

# Close the database
conn.close()

print("Database created successfully!")

