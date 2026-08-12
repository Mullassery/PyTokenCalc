"""Shared input validation for model strings that reach
`transformers.AutoTokenizer.from_pretrained()`.

`from_pretrained()` will treat its argument as a local filesystem path if it
looks like one, and otherwise fetches from the HuggingFace Hub over the
network. Once the CLI/REST server routes user-supplied `model` strings into
HuggingFaceTokenCounter / OpenSourceTokenCounter, an unvalidated string from
an untrusted caller could be used to probe the local filesystem (e.g.
"../../etc/passwd", "/etc/shadow") or trigger unexpected network fetches.

This module is a lightweight guard, not a full security boundary: it
rejects path-like input and enforces a plausible "org/model" HuggingFace
repo ID shape, and maintains a small allowlist of trusted, well-known
publisher orgs for callers that want to be strict about which orgs are
acceptable.
"""

import re
from typing import Optional

# HF repo ids are either a single canonical name ("gpt2", "bert-base-uncased")
# or namespaced "org/model" ("meta-llama/Meta-Llama-3-8B"). Each segment must
# start with an alphanumeric, then alphanumerics/._- . No leading slash, no
# "..", no whitespace, no "://" (rules out cloud URIs / path traversal).
_HF_REPO_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.\-]*(/[A-Za-z0-9][A-Za-z0-9_.\-]*)?$"
)

# Well-known publisher orgs. Not exhaustive -- PyTokenCalc intentionally
# supports "any HuggingFace model" for forward compatibility, so this is
# used as an opt-in stricter check (see `is_trusted_org`), not a hard block
# in the default path.
TRUSTED_HF_ORGS = {
    "meta-llama",
    "mistralai",
    "qwen",
    "tiiuae",
    "google",
    "microsoft",
    "huggingface",
    "eleutherai",
    "bigcode",
    "stabilityai",
    "deepseek-ai",
    "openai-community",
    "nousresearch",
    "thebloke",
}


def looks_like_hf_repo_id(model_id: str) -> bool:
    """Basic sanity check: does this look like a plausible "org/model" HF
    repo ID, rather than a filesystem path, empty string, or garbage?

    Rejects: empty strings, overly long strings, path traversal ("..",
    leading "/" or "~", backslashes), and anything not matching the
    "org/model" shape.
    """
    if not model_id or len(model_id) > 200:
        return False
    if ".." in model_id or "\\" in model_id:
        return False
    if model_id.startswith("/") or model_id.startswith("~"):
        return False
    return bool(_HF_REPO_ID_PATTERN.match(model_id))


def is_trusted_org(model_id: str) -> bool:
    """Is the org/publisher segment of `model_id` in the trusted allowlist?"""
    if "/" not in model_id:
        return False
    org = model_id.split("/", 1)[0].lower()
    return org in TRUSTED_HF_ORGS


def validate_model_id_for_from_pretrained(
    model_id: str, resolved_from_alias: bool = False
) -> Optional[str]:
    """Validate a model id before handing it to AutoTokenizer.from_pretrained.

    Args:
        model_id: The (possibly alias-resolved) HF repo id.
        resolved_from_alias: True if `model_id` came from a hardcoded,
            trusted alias table rather than directly from a caller -- in
            that case pattern validation is skipped since the value is
            already known-good.

    Returns:
        None if valid, otherwise a human-readable reason string.
    """
    if resolved_from_alias:
        return None

    if not looks_like_hf_repo_id(model_id):
        return (
            f"'{model_id}' does not look like a valid HuggingFace repo id "
            f"(expected 'org/model-name', e.g. 'meta-llama/Meta-Llama-3-8B')."
        )

    return None
