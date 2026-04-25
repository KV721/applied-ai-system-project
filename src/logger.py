"""
Structured logging setup: JSONL per-call log and session transcript writer.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def setup_logger(log_dir: str = "logs") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)


def log_llm_call(
    model: str,
    prompt_type: str,
    input_len: int,
    output_len: int,
    latency_ms: float,
    status: str = "ok",     # "ok" | "retry_ok" | "failed"
    retry_count: int = 0,
    error: Optional[str] = None,
    log_dir: str = "logs",
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "prompt_type": prompt_type,
        "input_len": input_len,
        "output_len": output_len,
        "latency_ms": round(latency_ms, 2),
        "status": status,
        "retry_count": retry_count,
        "cost_estimate_usd": _estimate_cost(model, input_len, output_len),
    }
    if error is not None:
        entry["error"] = error
    log_path = Path(log_dir) / "llm_calls.jsonl"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def save_session(session_data: dict, log_dir: str = "logs") -> None:
    sessions_dir = Path(log_dir) / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = sessions_dir / f"{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def _estimate_cost(model: str, input_len: int, output_len: int) -> float:
    # Gemini 2.5 Flash-Lite: $0.10/1M input tokens, $0.40/1M output tokens
    # Rough approximation: 4 chars ≈ 1 token
    input_tokens = input_len / 4
    output_tokens = output_len / 4
    cost = (input_tokens * 0.10 + output_tokens * 0.40) / 1_000_000
    return round(cost, 8)
