"""Bounded, thread-based timeout for blocking library calls.

`transformers.AutoTokenizer.from_pretrained()` has no native timeout
parameter, so a slow or unreachable HuggingFace Hub can block a caller for
the full OS-level TCP connect timeout (60-90s observed). This helper runs
the call in a daemon thread and raises `TimeoutError` in the caller if it
doesn't finish within `timeout` seconds, so `count_tokens()` can't hang
indefinitely on an uncached model ID.

Note: the underlying thread cannot be force-cancelled (Python has no safe
thread cancellation), so on timeout the download may continue in the
background. The daemon thread will not block interpreter shutdown. This is
intentional: the goal is to bound the *caller's* wait, which is what the
public API needs.
"""

import os
import queue
import threading
from typing import Any, Callable, TypeVar

T = TypeVar("T")

# Default ceiling for a single tokenizer load, in seconds. Overridable per
# counter instance or via the PYTOKENCALC_HF_TIMEOUT environment variable.
DEFAULT_HF_LOAD_TIMEOUT = 30.0


def resolve_default_timeout() -> float:
    """Return the default tokenizer-load timeout, honoring the env override."""
    raw = os.environ.get("PYTOKENCALC_HF_TIMEOUT")
    if raw is None:
        return DEFAULT_HF_LOAD_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_HF_LOAD_TIMEOUT
    return value if value > 0 else DEFAULT_HF_LOAD_TIMEOUT


def call_with_timeout(
    func: Callable[..., T],
    timeout: float,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Run ``func(*args, **kwargs)`` and raise `TimeoutError` after ``timeout``.

    Args:
        func: The blocking callable to run.
        timeout: Seconds to wait before giving up (must be > 0).
        *args, **kwargs: Forwarded to ``func``.

    Returns:
        Whatever ``func`` returns.

    Raises:
        TimeoutError: If ``func`` doesn't complete within ``timeout``.
        Exception: Any exception raised by ``func`` is re-raised here.
    """
    if timeout <= 0:
        return func(*args, **kwargs)

    result_queue: "queue.Queue[Any]" = queue.Queue(maxsize=1)

    def _target() -> None:
        try:
            result_queue.put((True, func(*args, **kwargs)))
        except BaseException as exc:  # noqa: BLE001 - relayed to caller below
            result_queue.put((False, exc))

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()

    try:
        ok, value = result_queue.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(
            f"Operation did not complete within {timeout:g}s "
            f"(set PYTOKENCALC_HF_TIMEOUT to adjust the tokenizer load limit)"
        ) from None

    if ok:
        return value
    raise value
