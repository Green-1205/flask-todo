import pytest

from flask_demo import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})
    return app.test_client()


def test_empty_list(client):
    assert "這裡沒有項目" in client.get("/").get_data(as_text=True)


def test_add_toggle_delete(client):
    client.post("/todos", data={"title": "買牛奶"})
    page = client.get("/").get_data(as_text=True)
    assert "買牛奶" in page and "共 1 項，完成 0 項" in page

    client.post("/todos/1/toggle")
    assert "完成 1 項" in client.get("/").get_data(as_text=True)
    assert "買牛奶" not in client.get("/?show=active").get_data(as_text=True)
    assert "買牛奶" in client.get("/?show=done").get_data(as_text=True)

    client.post("/todos/1/delete")
    assert "共 0 項" in client.get("/").get_data(as_text=True)


def test_blank_title_ignored(client):
    client.post("/todos", data={"title": "   "})
    assert "共 0 項" in client.get("/").get_data(as_text=True)


def test_clear_done(client):
    for title in ("a", "b", "c"):
        client.post("/todos", data={"title": title})
    client.post("/todos/1/toggle")
    client.post("/todos/3/toggle")
    client.post("/todos/clear-done")
    assert "共 1 項，完成 0 項" in client.get("/").get_data(as_text=True)


def test_missing_todo_404(client):
    assert client.post("/todos/99/toggle").status_code == 404
    assert client.post("/todos/99/delete").status_code == 404


def test_title_is_escaped(client):
    client.post("/todos", data={"title": "<script>x</script>"})
    assert "<script>x</script>" not in client.get("/").get_data(as_text=True)
