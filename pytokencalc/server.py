"""REST API server for PyTokenCalc - multi-provider token counter workflow integration."""

from typing import Any, Dict, Optional

from ._version import __version__
from .tokenizers import TokenCounterCache, TokenCounterRegistry


class PyTokenCalcServer:
    """REST API server for token counting workflows.

    SECURITY: Defaults to binding on 127.0.0.1 (localhost only). Binding to
    "0.0.0.0" (all interfaces) exposes this server to the network with no
    built-in authentication -- only do that behind a reverse proxy / auth
    layer you control, and pass host="0.0.0.0" explicitly.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8005):
        """Initialize server."""
        self.host = host
        self.port = port
        self.cache = TokenCounterCache()
        self.registry = TokenCounterRegistry(cache=self.cache)

    def count_tokens(
        self, text: str, model: str, provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Count tokens for text."""
        try:
            result = self.registry.count_tokens(model, text, provider)
            return {
                "status": "success",
                "model": model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "image_tokens": result.image_tokens,
                "system_tokens": result.system_tokens,
                "tool_tokens": result.tool_tokens,
                "total_tokens": result.total_tokens,
                "source": result.source,
                "cached": result.cached,
                "latency_ms": result.latency_ms,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "model": model}

    def count_vision(
        self,
        text: str,
        model: str,
        image_count: int = 1,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Count tokens for text + vision."""
        try:
            result = self.registry.count_vision(
                model, text, num_images=image_count, provider=provider
            )
            return {
                "status": "success",
                "model": model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "image_tokens": result.image_tokens,
                "system_tokens": result.system_tokens,
                "tool_tokens": result.tool_tokens,
                "total_tokens": result.total_tokens,
                "source": result.source,
                "cached": result.cached,
                "latency_ms": result.latency_ms,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "model": model}

    def list_providers(self) -> Dict[str, Any]:
        """List providers."""
        providers = self.registry.list_providers()
        return {
            "status": "success",
            "providers": providers,
            "count": len(providers),
        }

    def list_models(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """List models."""
        if provider:
            models = self.registry.list_models(provider)
            return {
                "status": "success",
                "provider": provider,
                "models": models,
                "count": len(models),
            }
        else:
            all_models = self.registry.list_models()
            return {
                "status": "success",
                "models": all_models,
                "count": len(all_models),
            }

    def list_catalog(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Return normalized model metadata."""
        from .catalog import list_models

        specs = list_models(provider)
        return {
            "status": "success",
            "provider": provider,
            "models": [spec.to_dict() for spec in specs],
            "count": len(specs),
        }

    def estimate_usage(
        self,
        model: str,
        usage: Dict[str, Any],
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Estimate line-item USD cost from explicit usage fields."""
        from .pricing import Usage
        from .pricing import estimate_usage as _estimate_usage

        if not isinstance(usage, dict):
            raise ValueError("usage must be an object")
        breakdown = _estimate_usage(model, Usage(**usage), provider)
        return {"status": "success", "cost": breakdown.to_dict()}

    def reconcile_response(
        self,
        model: str,
        response: Dict[str, Any],
        provider: Optional[str] = None,
        expected_cost_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Reconcile provider usage/cost from a response payload."""
        from .reconcile import reconcile

        result = reconcile(
            model,
            response,
            provider=provider,
            expected_cost_usd=expected_cost_usd,
        )
        return {"status": "success", **result.to_dict()}

    def preflight_request(
        self,
        messages: Any,
        model: str,
        tools: Any = None,
        max_output_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Estimate chat prompt tokens, context fit, and cost."""
        from .preflight import preflight

        result = preflight(
            messages,
            model,
            tools=tools,
            max_output_tokens=max_output_tokens,
            provider=provider,
            registry=self.registry,
        )
        return {"status": "success", **result.to_dict()}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache stats."""
        stats = self.cache.get_stats()
        return {
            "status": "success",
            "cached_counts": stats.get("size", 0),
            "cache_hits": stats.get("hits", 0),
            "cache_misses": stats.get("misses", 0),
            "hit_rate": stats.get("hit_rate_percent", 0.0),
        }

    def clear_cache(self) -> Dict[str, Any]:
        """Clear cache."""
        self.cache.clear()
        return {"status": "success", "message": "Cache cleared successfully"}

    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "pytokencalc",
            "version": __version__,
            "providers_available": len(self.registry.list_providers()),
        }


def create_flask_app(server: Optional[PyTokenCalcServer] = None):
    """Create Flask app for REST API."""
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        raise ImportError(
            'Flask is required for REST API. Install with: pip install "pytokencalc[server]"'
        ) from None

    app = Flask(__name__)
    srv = server or PyTokenCalcServer()

    @app.route("/health", methods=["GET"])
    def health():
        """Health check."""
        return jsonify(srv.health_check())

    @app.route("/providers", methods=["GET"])
    def providers():
        """List providers."""
        return jsonify(srv.list_providers())

    @app.route("/models", methods=["GET"])
    def models():
        """List models."""
        provider = request.args.get("provider")
        return jsonify(srv.list_models(provider))

    @app.route("/count", methods=["POST"])
    def count():
        """Count tokens."""
        data = request.get_json() or {}
        text = data.get("text")
        model = data.get("model")
        provider = data.get("provider")

        if not text or not model:
            return (
                jsonify(
                    {"status": "error", "message": "text and model required"}
                ),
                400,
            )

        return jsonify(srv.count_tokens(text, model, provider))

    @app.route("/count-vision", methods=["POST"])
    def count_vision():
        """Count vision tokens."""
        data = request.get_json() or {}
        text = data.get("text")
        model = data.get("model")
        image_count = data.get("image_count", 1)
        provider = data.get("provider")

        if not text or not model:
            return (
                jsonify(
                    {"status": "error", "message": "text and model required"}
                ),
                400,
            )

        return jsonify(srv.count_vision(text, model, image_count, provider))

    @app.route("/cache", methods=["GET"])
    def cache():
        """Get cache stats."""
        return jsonify(srv.get_cache_stats())

    @app.route("/cache", methods=["DELETE"])
    def clear_cache():
        """Clear cache."""
        return jsonify(srv.clear_cache())

    @app.route("/v1/models", methods=["GET"])
    def v1_models():
        """Normalized model catalog."""
        return jsonify(srv.list_catalog(request.args.get("provider")))

    @app.route("/v1/cost", methods=["POST"])
    def v1_cost():
        """Usage-aware cost estimate."""
        data = request.get_json() or {}
        model = data.get("model")
        usage = data.get("usage")
        if not model or not isinstance(usage, dict):
            return (
                jsonify({"status": "error", "message": "model and usage object required"}),
                400,
            )
        try:
            return jsonify(srv.estimate_usage(model, usage, data.get("provider")))
        except (TypeError, ValueError) as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/v1/reconcile", methods=["POST"])
    def v1_reconcile():
        """Reconcile a provider response's usage/cost."""
        data = request.get_json() or {}
        model = data.get("model")
        response = data.get("response", data)
        if not model or not isinstance(response, dict):
            return (
                jsonify({"status": "error", "message": "model and response object required"}),
                400,
            )
        try:
            return jsonify(
                srv.reconcile_response(
                    model,
                    response,
                    provider=data.get("provider"),
                    expected_cost_usd=data.get("expected_cost_usd"),
                )
            )
        except (TypeError, ValueError) as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/v1/preflight", methods=["POST"])
    def v1_preflight():
        """Estimate tokens/context/cost before sending a chat request."""
        data = request.get_json() or {}
        model = data.get("model")
        messages = data.get("messages")
        if not model or messages is None:
            return (
                jsonify({"status": "error", "message": "model and messages required"}),
                400,
            )
        try:
            return jsonify(
                srv.preflight_request(
                    messages,
                    model,
                    tools=data.get("tools"),
                    max_output_tokens=data.get("max_output_tokens"),
                    provider=data.get("provider"),
                )
            )
        except (TypeError, ValueError) as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/openapi.json", methods=["GET"])
    def openapi():
        """OpenAPI 3.0 description of the REST surface."""
        return jsonify(openapi_spec())

    return app


def openapi_spec() -> Dict[str, Any]:
    """Return an OpenAPI 3.0.3 document for the REST surface."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "PyTokenCalc REST API",
            "version": __version__,
            "description": "Token counting, cost estimation, reconciliation, and chat preflight.",
        },
        "paths": {
            "/health": {"get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}},
            "/providers": {"get": {"summary": "List tokenizer providers", "responses": {"200": {"description": "OK"}}}},
            "/models": {"get": {"summary": "List provider-supported model IDs", "responses": {"200": {"description": "OK"}}}},
            "/v1/models": {
                "get": {
                    "summary": "Normalized model catalog",
                    "parameters": [
                        {
                            "name": "provider",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/count": {"post": {"summary": "Count text tokens", "responses": {"200": {"description": "OK"}, "400": {"description": "Invalid request"}}}},
            "/count-vision": {"post": {"summary": "Count text+image tokens", "responses": {"200": {"description": "OK"}, "400": {"description": "Invalid request"}}}},
            "/v1/cost": {"post": {"summary": "Usage-aware cost estimate", "responses": {"200": {"description": "OK"}, "400": {"description": "Invalid request"}}}},
            "/v1/reconcile": {"post": {"summary": "Reconcile provider usage/cost", "responses": {"200": {"description": "OK"}, "400": {"description": "Invalid request"}}}},
            "/v1/preflight": {"post": {"summary": "Chat context/cost preflight", "responses": {"200": {"description": "OK"}, "400": {"description": "Invalid request"}}}},
            "/cache": {"get": {"summary": "Cache stats", "responses": {"200": {"description": "OK"}}}, "delete": {"summary": "Clear cache", "responses": {"200": {"description": "OK"}}}},
        },
    }


def run_server(host: str = "127.0.0.1", port: int = 8005):
    """Run the REST API server.

    SECURITY: Defaults to localhost-only. Pass host="0.0.0.0" explicitly to
    expose this on the network -- do so only behind your own auth/proxy layer.
    """
    app = create_flask_app(PyTokenCalcServer(host=host, port=port))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
