"""Tests for `pytokencalc/server.py` (REST API surface).

Previously had no dedicated test file (ROADMAP_HONEST.md section 3). Flask is
an optional dependency, so the HTTP tests skip when it isn't installed; the
`PyTokenCalcServer` method tests run regardless.
"""

import pytest

from pytokencalc.server import PyTokenCalcServer


@pytest.fixture
def server():
    return PyTokenCalcServer()


class TestServerMethods:
    def test_health_check(self, server):
        health = server.health_check()
        assert health["status"] == "healthy"
        assert health["service"] == "pytokencalc"
        assert health["version"]
        assert health["providers_available"] >= 0

    def test_count_tokens_success(self, server):
        result = server.count_tokens("Tell me a story about a robot", "gpt-4o")
        assert result["status"] == "success"
        assert result["input_tokens"] > 0
        assert result["model"] == "gpt-4o"

    def test_count_tokens_error_is_returned_not_raised(self, server):
        result = server.count_tokens("hello", "not-a-real-model-xyz")
        assert result["status"] == "error"
        assert "message" in result

    def test_list_providers(self, server):
        result = server.list_providers()
        assert result["status"] == "success"
        assert result["count"] == len(result["providers"])

    def test_list_models_all(self, server):
        result = server.list_models()
        assert result["status"] == "success"
        assert result["count"] == len(result["models"])

    def test_list_models_filtered(self, server):
        result = server.list_models("openai")
        assert result["status"] == "success"
        assert result["provider"] == "openai"

    def test_cache_stats_and_clear(self, server):
        stats = server.get_cache_stats()
        assert stats["status"] == "success"
        cleared = server.clear_cache()
        assert cleared["status"] == "success"

    def test_list_catalog(self, server):
        result = server.list_catalog("openai")
        assert result["status"] == "success"
        assert result["count"] > 0
        assert all(model["provider"] == "openai" for model in result["models"])

    def test_estimate_usage(self, server):
        result = server.estimate_usage(
            "gpt-4o",
            {"input_tokens": 1_000, "output_tokens": 500},
        )
        assert result["status"] == "success"
        assert result["cost"]["costs_usd"]["total"] == pytest.approx(0.0075)

    def test_reconcile_response(self, server):
        result = server.reconcile_response(
            "gpt-4o",
            {"usage": {"prompt_tokens": 100, "completion_tokens": 20}},
            expected_cost_usd=0.001,
        )
        assert result["status"] == "success"
        assert result["usage"]["input_tokens"] == 100
        assert result["delta_usd"] is not None

    def test_preflight_request(self, server):
        result = server.preflight_request(
            [{"role": "user", "content": "Hello world"}],
            "gpt-4o",
            max_output_tokens=100,
        )
        assert result["status"] == "success"
        assert result["input_tokens"] > 0
        assert result["fits"] is True


def test_openapi_spec():
    from pytokencalc.server import openapi_spec

    spec = openapi_spec()
    assert spec["openapi"].startswith("3.")
    assert "/v1/models" in spec["paths"]
    assert "/v1/cost" in spec["paths"]


class TestFlaskApp:
    @pytest.fixture
    def client(self):
        pytest.importorskip("flask")
        from pytokencalc.server import create_flask_app

        app = create_flask_app()
        app.config.update(TESTING=True)
        return app.test_client()

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "healthy"

    def test_providers_endpoint(self, client):
        resp = client.get("/providers")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "success"

    def test_models_endpoint(self, client):
        resp = client.get("/models?provider=openai")
        assert resp.status_code == 200
        assert resp.get_json()["provider"] == "openai"

    def test_count_endpoint_success(self, client):
        resp = client.post(
            "/count", json={"text": "Tell me a story about a robot", "model": "gpt-4o"}
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["input_tokens"] > 0

    def test_count_endpoint_requires_text_and_model(self, client):
        resp = client.post("/count", json={"text": "only text"})
        assert resp.status_code == 400
        assert resp.get_json()["status"] == "error"

    def test_cache_endpoints(self, client):
        assert client.get("/cache").status_code == 200
        assert client.delete("/cache").status_code == 200

    def test_v1_catalog_endpoint(self, client):
        resp = client.get("/v1/models?provider=openai")
        assert resp.status_code == 200
        assert resp.get_json()["count"] > 0

    def test_v1_cost_endpoint(self, client):
        resp = client.post(
            "/v1/cost",
            json={
                "model": "gpt-4o",
                "usage": {"input_tokens": 1000, "output_tokens": 500},
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["cost"]["costs_usd"]["total"] == pytest.approx(0.0075)

    def test_v1_preflight_endpoint(self, client):
        resp = client.post(
            "/v1/preflight",
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello world"}],
                "max_output_tokens": 100,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["input_tokens"] > 0

    def test_openapi_endpoint(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert resp.get_json()["openapi"].startswith("3.")
