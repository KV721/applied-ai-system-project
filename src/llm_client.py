"""
Gemini API wrapper with structured logging and retry logic.
"""

import concurrent.futures
import json
import os
import sys
import time
import traceback
from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from src.logger import log_llm_call

MAX_CALLS_PER_TURN = 10
TIMEOUT_SECONDS = 30


class LLMClient:
    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        self.model_name = model
        self._client = None
        self._turn_calls = 0

    def reset_turn_counter(self) -> None:
        self._turn_calls = 0

    def _get_client(self):
        if self._client is None:
            from google import genai

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def call(
        self,
        system: str,
        user: str,
        schema: Optional[Type[BaseModel]] = None,
        json_mode: bool = False,
        max_tokens: int = 1024,
        prompt_type: str = "unknown",
    ) -> str:
        """
        Call the Gemini API.
        - schema: Pydantic class → structured JSON output (response_schema + mime_type).
        - json_mode: True → JSON output without schema (mime_type only; use when the
          schema contains dict fields that Gemini's API rejects as additionalProperties).
        Logs every call, enforces per-turn call cap, retries once on failure,
        and enforces a 30s per-call timeout.
        """
        if self._turn_calls >= MAX_CALLS_PER_TURN:
            raise RuntimeError(
                f"Max {MAX_CALLS_PER_TURN} LLM calls per turn exceeded"
            )
        self._turn_calls += 1

        start = time.time()
        status = "ok"
        retry_count = 0
        response = None

        # Build config and client inside the timed block so import/init errors
        # are caught, logged, and retried rather than silently bypassing the log.
        try:
            from google.genai import types

            config_kwargs: dict = {
                "system_instruction": system,
                "max_output_tokens": max_tokens,
            }
            if schema is not None:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = schema
            elif json_mode:
                config_kwargs["response_mime_type"] = "application/json"

            config = types.GenerateContentConfig(**config_kwargs)
            client = self._get_client()

            def _call(contents: str):
                return client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

            response = self._run_with_timeout(_call, user)
        except Exception as first_err:
            retry_count = 1
            print(
                f"[llm_client] {prompt_type} first attempt failed — "
                f"{type(first_err).__name__}: {first_err}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)
            # Only add a JSON hint when the failure looks like a format/parse issue.
            # Timeout and network errors get the original message unchanged.
            is_json_err = isinstance(first_err, (json.JSONDecodeError, ValidationError, ValueError))
            retry_user = user + "\n\nIMPORTANT: Return valid JSON only." if is_json_err else user
            try:
                response = self._run_with_timeout(_call, retry_user)
                status = "retry_ok"
            except Exception as second_err:
                latency_ms = (time.time() - start) * 1000
                err_msg = f"{type(second_err).__name__}: {second_err}"
                print(
                    f"[llm_client] {prompt_type} retry also failed — {err_msg}",
                    file=sys.stderr,
                )
                log_llm_call(
                    model=self.model_name,
                    prompt_type=prompt_type,
                    input_len=len(system) + len(user),
                    output_len=0,
                    latency_ms=latency_ms,
                    status="failed",
                    retry_count=retry_count,
                    error=err_msg,
                )
                raise RuntimeError(
                    f"LLM call failed after retry: {second_err}"
                ) from second_err

        latency_ms = (time.time() - start) * 1000
        text = response.text
        log_llm_call(
            model=self.model_name,
            prompt_type=prompt_type,
            input_len=len(system) + len(user),
            output_len=len(text),
            latency_ms=latency_ms,
            status=status,
            retry_count=retry_count,
        )
        return text

    def _run_with_timeout(self, fn, *args):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args)
            try:
                return future.result(timeout=TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(
                    f"LLM call timed out after {TIMEOUT_SECONDS}s"
                )
