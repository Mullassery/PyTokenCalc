#!/usr/bin/env python3
"""
PyTokenCalc vs tiktoken -- real-data correctness and speed comparison.

For OpenAI models PyTokenCalc wraps tiktoken directly, so this checks
whether the wrapper ever diverges from the ground truth it wraps, and
measures the wrapper's own overhead honestly (warm, not cold-start).

Usage:
    pip install pytokencalc tiktoken requests
    python3 docs/bench/tiktoken_comparison.py
"""
import statistics
import time

import requests
import tiktoken

from pytokencalc import count_tokens
from pytokencalc.tokenizers.registry import get_global_registry
from pytokencalc.tokenizers.streaming import StreamingTokenCounter

MODELS = ["gpt-4o", "gpt-4"]


def fetch_real_corpus() -> dict:
    urls = [
        ("https://raw.githubusercontent.com/pallets/flask/main/README.md", "flask_readme"),
        ("https://raw.githubusercontent.com/psf/requests/main/README.md", "requests_readme"),
        ("https://raw.githubusercontent.com/pytorch/pytorch/main/README.md", "pytorch_readme"),
    ]
    texts = {}
    for url, name in urls:
        r = requests.get(url, timeout=30, headers={"User-Agent": "pytokencalc-benchmark/1.0"})
        r.raise_for_status()
        texts[name] = r.text

    w = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query", "prop": "extracts", "explaintext": 1,
            "redirects": 1, "titles": "Artificial intelligence", "format": "json",
        },
        headers={"User-Agent": "pytokencalc-benchmark/1.0"},
        timeout=30,
    )
    w.raise_for_status()
    for page in w.json()["query"]["pages"].values():
        if "extract" in page:
            texts[f"wiki_{page['title'].replace(' ', '_')}"] = page["extract"]
    return texts


EDGE_CASES = {
    "empty": "",
    "emoji": "Hello \U0001f44b\U0001f30d let's test emoji \U0001f680\U0001f525\U0001f4af tokenization!! \U0001f605\U0001f602\U0001f914",
    "japanese": "これは日本語のテキストです。トークン化のテストを行っています。",
    "chinese": "这是中文文本。我们正在测试分词功能。",
    "mixed_code": "def foo(x: int) -> int:\n    return x ** 2 + len('日本語テスト')  # コメント\n",
    "long_repeat": "the quick brown fox jumps over the lazy dog. " * 500,
}


def correctness_check():
    corpus = fetch_real_corpus()
    total = 0
    matched = 0
    for name, text in corpus.items():
        for model in MODELS:
            enc = tiktoken.encoding_for_model(model)
            tk = len(enc.encode(text))
            ptc = count_tokens(text, model=model)
            total += 1
            matched += int(tk == ptc)
            print(f"[corpus] {name:28s} {model:8s} tiktoken={tk:6d} ptc={ptc:6d} match={tk == ptc}")

    enc4o = tiktoken.encoding_for_model("gpt-4o")
    for name, text in EDGE_CASES.items():
        tk = len(enc4o.encode(text))
        ptc = count_tokens(text, model="gpt-4o")
        total += 1
        matched += int(tk == ptc)
        print(f"[edge]   {name:28s} gpt-4o   tiktoken={tk:6d} ptc={ptc:6d} match={tk == ptc}")

    print(f"\nExact match: {matched}/{total}")


def speed_check():
    """Interleaved measurement: alternates tiktoken/PyTokenCalc calls within
    each iteration so both see the same system-load noise. Non-interleaved
    back-to-back blocks are vulnerable to load drift between blocks and can
    flip which one looks faster run to run on a loaded machine -- don't
    trust a single non-interleaved timing."""
    enc = tiktoken.encoding_for_model("gpt-4o")
    text = EDGE_CASES["long_repeat"]
    count_tokens("warmup", model="gpt-4o")
    len(enc.encode("warmup"))

    n = 200
    tk_times, ptc_times = [], []
    for _ in range(n):
        t0 = time.perf_counter()
        len(enc.encode(text))
        tk_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        count_tokens(text, model="gpt-4o")
        ptc_times.append(time.perf_counter() - t0)

    tk_med, ptc_med = statistics.median(tk_times), statistics.median(ptc_times)
    print(f"\nWarm, interleaved median latency over {len(text)} chars, {n} iters:")
    print(f"tiktoken: {tk_med * 1000:.4f}ms  pytokencalc: {ptc_med * 1000:.4f}ms  "
          f"overhead: {(ptc_med / tk_med - 1) * 100:.1f}%")


def streaming_check():
    registry = get_global_registry()
    counter = registry.get_counter("openai")
    model = "gpt-4o"
    enc = tiktoken.encoding_for_model(model)

    text = (
        "The quick brown fox jumps over the lazy dog, and "
        "internationalization/日本語/emoji \U0001f680 tokens can merge "
        "across chunk boundaries in surprising ways."
    )
    chunks = [text[i:i + 3] for i in range(0, len(text), 3)]

    stream = StreamingTokenCounter(counter, model=model)
    deltas_sum = 0
    naive_sum = 0
    for c in chunks:
        deltas_sum += stream.add_chunk(c)
        naive_sum += len(enc.encode(c))

    ground_truth = len(enc.encode(text))
    print(f"\nStreaming counter: ground_truth={ground_truth} "
          f"delta_sum={deltas_sum} (match={deltas_sum == ground_truth}) "
          f"naive_per_chunk_sum={naive_sum} (off by {naive_sum - ground_truth})")


if __name__ == "__main__":
    correctness_check()
    speed_check()
    streaming_check()
