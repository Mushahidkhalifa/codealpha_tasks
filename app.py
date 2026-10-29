
from flask import Flask, request, redirect, render_template
import sqlite3
import secrets
import string
from urllib.parse import urlparse

app = Flask(__name__)
DATABASE = "urls.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL
            )
        """)


def make_short_code():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))


def valid_url(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and not any(c.isspace() for c in url)
        )
    except ValueError:
        return False


@app.route("/", methods=["GET", "POST"])
def home():
    short_url = None
    error = None

    if request.method == "POST":
        original_url = request.form.get("url", "").strip()

        if not valid_url(original_url):
            error = "Enter a valid URL beginning with http:// or https://"
        else:
            with get_db() as db:
                while True:
                    code = make_short_code()
                    exists = db.execute(
                        "SELECT 1 FROM urls WHERE short_code = ?",
                        (code,)
                    ).fetchone()

                    if not exists:
                        break

                db.execute(
                    "INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
                    (code, original_url)
                )

            short_url = request.host_url + code

    return render_template(
        "index.html",
        short_url=short_url,
        error=error
    )


@app.route("/<short_code>")
def visit(short_code):
    with get_db() as db:
        row = db.execute(
            "SELECT original_url FROM urls WHERE short_code = ?",
            (short_code,)
        ).fetchone()

    if row is None:
        return "Short URL not found.", 404

    return redirect(row["original_url"])


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
