from types import SimpleNamespace

import pytest
from flask import Flask

import utils.decorators as decorators


@pytest.fixture
def role_app(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test-secret"
    state = {"user": SimpleNamespace(id=1, role="user", is_active=True)}
    monkeypatch.setattr(decorators, "_current_user", lambda: state["user"])

    @app.route("/upload")
    @decorators.admin_required
    def upload():
        return "upload"

    @app.route("/export/sls/csv")
    @decorators.admin_required
    def export():
        return "export"

    @app.route("/admin/users")
    @decorators.admin_required
    def users():
        return "users"

    @app.route("/dashboard")
    @decorators.login_required
    def dashboard():
        return "dashboard"

    app.config["TESTING"] = False
    return app, state


def test_user_cannot_open_admin_routes(role_app):
    app, _state = role_app
    client = app.test_client()
    assert client.get("/upload").status_code == 403
    assert client.get("/export/sls/csv").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert client.get("/dashboard").status_code == 200


def test_admin_can_open_all_features(role_app):
    app, state = role_app
    state["user"] = SimpleNamespace(id=1, role="admin", is_active=True)
    client = app.test_client()
    assert client.get("/upload").status_code == 200
    assert client.get("/export/sls/csv").status_code == 200
    assert client.get("/admin/users").status_code == 200
    assert client.get("/dashboard").status_code == 200

