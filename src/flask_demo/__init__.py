import os
import sqlite3

from flask import Flask, abort, g, redirect, render_template, request, url_for

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=os.path.join(app.instance_path, "todos.sqlite3"))
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)

    @app.get("/")
    def index():
        show = request.args.get("show", "all")
        where = {"active": "WHERE done = 0", "done": "WHERE done = 1"}.get(show, "")
        todos = get_db().execute(f"SELECT * FROM todos {where} ORDER BY done, id DESC").fetchall()
        counts = get_db().execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM todos"
        ).fetchone()
        return render_template("index.html", todos=todos, show=show, counts=counts)

    @app.post("/todos")
    def create():
        title = request.form.get("title", "").strip()
        if title:
            db = get_db()
            db.execute("INSERT INTO todos (title) VALUES (?)", (title[:200],))
            db.commit()
        return redirect(url_for("index", show=request.args.get("show", "all")))

    @app.post("/todos/<int:todo_id>/toggle")
    def toggle(todo_id: int):
        db = get_db()
        cur = db.execute("UPDATE todos SET done = 1 - done WHERE id = ?", (todo_id,))
        if cur.rowcount == 0:
            abort(404)
        db.commit()
        return redirect(url_for("index", show=request.args.get("show", "all")))

    @app.post("/todos/<int:todo_id>/delete")
    def delete(todo_id: int):
        db = get_db()
        cur = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cur.rowcount == 0:
            abort(404)
        db.commit()
        return redirect(url_for("index", show=request.args.get("show", "all")))

    @app.post("/todos/clear-done")
    def clear_done():
        db = get_db()
        db.execute("DELETE FROM todos WHERE done = 1")
        db.commit()
        return redirect(url_for("index", show=request.args.get("show", "all")))

    return app


def main() -> None:
    create_app().run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5001")),
        debug=True,
    )
