"""Pre-request context-window and cost preflight for chat requests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from .catalog import get_model_spec
from .pricing import CostBreakdown, Usage, estimate_usage
from .tokenizers.registry import get_global_registry

MESSAGE_OVERHEAD_TOKENS = 4
CONVERSATION_PRIMER_TOKENS = 3
TOOL_OVERHEAD_TOKENS = 8


@dataclass(frozen=True)
class PreflightResult:
    model: str
    provider: Optional[str]
    input_tokens: int
    text_tokens: int
    image_tokens: int
    tool_tokens: int
    message_overhead_tokens: int
    context_length: Optional[int]
    max_output_tokens: Optional[int]
    context_remaining: Optional[int]
    fits: Optional[bool]
    estimated_cost_usd: Optional[float]
    cost: Optional[CostBreakdown]
    estimated: bool
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "text_tokens": self.text_tokens,
            "image_tokens": self.image_tokens,
            "tool_tokens": self.tool_tokens,
            "message_overhead_tokens": self.message_overhead_tokens,
            "context_length": self.context_length,
            "max_output_tokens": self.max_output_tokens,
            "context_remaining": self.context_remaining,
            "fits": self.fits,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated": self.estimated,
            "warnings": list(self.warnings),
            "cost": self.cost.to_dict() if self.cost is not None else None,
        }


def _content_parts(content: Any) -> Tuple[List[str], int, List[str]]:
    """Return (text_parts, image_count, warnings) for message content."""
    if content is None:
        return [], 0, []
    if isinstance(content, str):
        return [content], 0, []
    if not isinstance(content, Sequence) or isinstance(content, (bytes, bytearray)):
        return [str(content)], 0, ["non-string message content was stringified"]

    texts: List[str] = []
    images = 0
    warnings: List[str] = []
    for part in content:
        if isinstance(part, str):
            texts.append(part)
            continue
        if not isinstance(part, Mapping):
            warnings.append("non-mapping content part was ignored")
            continue
        part_type = str(part.get("type", ""))
        if part_type in {"text", "input_text"}:
            value = part.get("text")
            if value is not None:
                texts.append(str(value))
        elif part_type in {"image_url", "image", "input_image"}:
            images += 1
        elif part_type in {"input_audio", "audio"}:
            warnings.append("audio content is not counted by PyTokenCalc preflight")
        elif part_type in {"file", "input_file"}:
            warnings.append("file content is not counted by PyTokenCalc preflight")
        else:
            warnings.append(f"unsupported content part type: {part_type or 'unknown'}")
    return texts, images, warnings


def _coerce_messages(messages: Any) -> List[Mapping[str, Any]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if isinstance(messages, Mapping):
        return [messages]
    if not isinstance(messages, Sequence) or isinstance(messages, (bytes, bytearray)):
        raise TypeError("messages must be a string or a sequence of message objects")
    coerced: List[Mapping[str, Any]] = []
    for message in messages:
        if not isinstance(message, Mapping):
            raise TypeError("each message must be a mapping with role/content")
        coerced.append(message)
    return coerced


def preflight(
    messages: Any,
    model: str,
    *,
    tools: Any = None,
    max_output_tokens: Optional[int] = None,
    provider: Optional[str] = None,
    registry: Any = None,
) -> PreflightResult:
    """Estimate prompt tokens, context fit, and cost for a chat request.

    Text tokens use the real tokenizer for *model*. Chat framing, tool-schema
    overhead, and image tokens are estimates; image support depends on the
    provider counter (OpenAI currently returns a formula-based estimate).
    """
    if max_output_tokens is not None and (
        isinstance(max_output_tokens, bool)
        or not isinstance(max_output_tokens, int)
        or max_output_tokens < 0
    ):
        raise ValueError("max_output_tokens must be a non-negative integer")

    spec = get_model_spec(model)
    effective_provider = provider or (spec.provider if spec is not None else None)
    counter_registry = registry if registry is not None else get_global_registry()
    message_list = _coerce_messages(messages)

    warnings: List[str] = []
    text_tokens = 0
    image_count = 0

    for message in message_list:
        texts, images, content_warnings = _content_parts(message.get("content"))
        warnings.extend(content_warnings)
        for text in texts:
            if text:
                text_tokens += counter_registry.count_tokens(
                    model, text, effective_provider
                ).input_tokens
        image_count += images

        tool_calls = message.get("tool_calls")
        if tool_calls:
            text_tokens += counter_registry.count_tokens(
                model,
                json.dumps(tool_calls, separators=(",", ":"), ensure_ascii=False),
                effective_provider,
            ).input_tokens

    message_overhead = (
        MESSAGE_OVERHEAD_TOKENS * len(message_list) + CONVERSATION_PRIMER_TOKENS
        if message_list
        else 0
    )

    tool_tokens = 0
    if tools:
        serialized_tools = json.dumps(tools, separators=(",", ":"), ensure_ascii=False)
        tool_tokens = counter_registry.count_tokens(
            model, serialized_tools, effective_provider
        ).input_tokens
        if isinstance(tools, Sequence) and not isinstance(tools, (str, bytes, bytearray)):
            tool_tokens += TOOL_OVERHEAD_TOKENS * len(tools)

    image_tokens = 0
    if image_count:
        try:
            vision = counter_registry.count_vision(
                "", model, num_images=image_count, provider=effective_provider
            )
            image_tokens = vision.image_tokens
        except Exception as exc:  # noqa: BLE001 - surface as a warning
            warnings.append(f"image token counting failed: {exc}")
        if image_tokens == 0:
            warnings.append(
                "image token counting is unavailable for this provider; "
                "context/cost may be underestimated"
            )

    input_tokens = text_tokens + tool_tokens + image_tokens + message_overhead
    context_length = spec.context_length if spec is not None else None
    if context_length is None:
        warnings.append("context window is unknown for this model")
        context_remaining = None
        fits = None
    else:
        context_remaining = context_length - input_tokens
        fits = input_tokens + (max_output_tokens or 0) <= context_length

    cost: Optional[CostBreakdown] = None
    estimated_cost: Optional[float] = None
    try:
        cost = estimate_usage(
            model,
            Usage(
                input_tokens=input_tokens,
                output_tokens=max_output_tokens or 0,
            ),
            effective_provider,
        )
        estimated_cost = cost.total_usd
    except ValueError as exc:
        warnings.append(f"pricing unavailable: {exc}")

    warnings.append(
        "chat framing and tool overhead are approximate; text tokens use the model tokenizer"
    )

    return PreflightResult(
        model=model,
        provider=effective_provider,
        input_tokens=input_tokens,
        text_tokens=text_tokens,
        image_tokens=image_tokens,
        tool_tokens=tool_tokens,
        message_overhead_tokens=message_overhead,
        context_length=context_length,
        max_output_tokens=max_output_tokens,
        context_remaining=context_remaining,
        fits=fits,
        estimated_cost_usd=estimated_cost,
        cost=cost,
        estimated=True,
        warnings=tuple(dict.fromkeys(warnings)),
    )
