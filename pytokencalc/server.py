"""REST API server for PyTokenCalc - multi-provider token counter workflow integration."""

from typing import Dict, Any, Optional

from .tokenizers import TokenCounterRegistry, TokenCounterCache


class PyTokenCalcServer:
    """REST API server for token counting workflows."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8005):
        """Initialize server."""
        self.host = host
        self.port = port
        self.registry = TokenCounterRegistry()
        self.cache = TokenCounterCache()

    def count_tokens(
        self, text: str, model: str, provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Count tokens for text."""
        try:
            result = self.registry.count(text, model, provider)
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
                text, model, num_images=image_count, provider=provider
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
            all_models = self.registry.list_all_models()
            return {
                "status": "success",
                "models": all_models,
                "count": len(all_models),
            }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache stats."""
        stats = self.cache.get_stats()
        return {
            "status": "success",
            "cached_counts": stats.get("cached_counts", 0),
            "cache_hits": stats.get("cache_hits", 0),
            "cache_misses": stats.get("cache_misses", 0),
            "hit_rate": stats.get("hit_rate", 0.0),
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
            "version": "0.7.0",
            "providers_available": len(self.registry.list_providers()),
        }


def create_flask_app(server: Optional[PyTokenCalcServer] = None):
    """Create Flask app for REST API."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        raise ImportError(
            "Flask is required for REST API. Install with: pip install flask"
        )

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

    return app


def run_server(host: str = "0.0.0.0", port: int = 8005):
    """Run the REST API server."""
    app = create_flask_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
