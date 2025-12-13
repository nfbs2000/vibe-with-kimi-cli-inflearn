"""
Batch runner to stress-test Kimi K2 Thinking's interleaving reasoning with multiple prompts.

Features:
- Runs each prompt through the real KimiCLI + Wire pipeline (same path as CLI).
- Captures all Wire events (Think/Text/ToolCall/ToolResult/Approval/Compaction/Status) to per-prompt JSONL.
- Optional thinking-off run for A/B comparison.

Usage:
  export KIMI_BASE_URL=...
  export KIMI_API_KEY=...
  export KIMI_MODEL_NAME=kimi-k2-thinking

  python3 scripts/ch3/batch_interleaving_tests.py \
    --prompts "README 요약" "tests 구조 설명" \
    --out logs/ch3_run \
    --thinking-off   # optional: run a second pass without thinking
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from kaos.path import KaosPath
from kimi_cli.app import KimiCLI
from kimi_cli.session import Session
from kimi_cli.soul import RunCancelled, run_soul
from kimi_cli.wire.message import (
    ApprovalRequest,
    CompactionBegin,
    CompactionEnd,
    ContentPart,
    StatusUpdate,
    StepBegin,
    StepInterrupted,
    ToolCall,
    ToolCallPart,
    ToolResult,
)
from kimi_cli.wire.serde import serialize_wire_message


def _clean_filename(text: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip())[:80]
    return base or "prompt"


def _summarize(msg: Any) -> str:
    match msg:
        case ApprovalRequest(tool_call_id=tcid, sender=sender, action=action, description=desc):
            return f"[approval] {sender}:{action} ({desc}) tcid={tcid}"
        case StepBegin(n=n):
            return f"[step {n}] begin"
        case StepInterrupted():
            return "[step] interrupted"
        case CompactionBegin():
            return "[compaction] begin"
        case CompactionEnd():
            return "[compaction] end"
        case StatusUpdate(status=status):
            return f"[status] context_usage={status.context_usage:.2%}"
        case ContentPart():
            kind = msg.type if hasattr(msg, "type") else "content"
            text = getattr(msg, "text", "") or str(msg)
            return f"[content:{kind}] {text[:80]}"
        case ToolCall(function=fn):
            return f"[tool_call] {fn.name} args={fn.arguments[:80]}"
        case ToolCallPart(function=fn):
            return f"[tool_call_part] {getattr(fn, 'name', '')} Δargs={getattr(fn, 'arguments', '')[:80]}"
        case ToolResult(tool_call_id=tcid, result=result):
            brief = getattr(result, "brief", "") or getattr(result, "message", "")
            return f"[tool_result] tcid={tcid} ok={result.__class__.__name__} {brief[:80]}"
        case _:
            return f"[unknown] {msg}"


def _to_jsonable(msg: Any) -> dict[str, Any]:
    return serialize_wire_message(msg)


async def _run_prompt(app: KimiCLI, prompt: str, log_path: Path) -> None:
    events: list[Any] = []

    async def ui_loop(wire) -> None:
        wire_ui = wire.ui_side(merge=True)
        while True:
            try:
                msg = await wire_ui.receive()
            except asyncio.QueueShutDown:
                break
            events.append(msg)
            print(_summarize(msg))

    cancel_event = asyncio.Event()
    try:
        await run_soul(app.soul, prompt, ui_loop, cancel_event)
    except RunCancelled:
        print("Run cancelled by user")
    finally:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as f:
            for msg in events:
                f.write(json.dumps(_to_jsonable(msg), ensure_ascii=False) + "\n")
        print(f"[saved] {log_path}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch interleaving tests for Kimi K2 Thinking")
    parser.add_argument(
        "--prompts",
        nargs="+",
        help="테스트할 프롬프트들. 미지정 시 기본 셋 사용",
    )
    parser.add_argument(
        "--out",
        default="logs/ch3_batch",
        help="로그 저장 디렉터리",
    )
    parser.add_argument(
        "--thinking-off",
        action="store_true",
        help="thinking 모드를 끈 비교 러닝도 추가 실행",
    )
    args = parser.parse_args()

    default_prompts = [
        "README.md를 요약하고 tests 디렉터리의 테스트 목적을 정리해줘",
        "src에서 최근 수정 파일 5개를 찾고, 관련 tests 또는 tests_ai의 케이스가 있는지 조사해줘",
        "tests_ai 디렉터리의 테스트 플랜을 세우고, 누락된 스크립트가 있으면 목록화해",
    ]
    prompts = args.prompts or default_prompts

    work_dir = KaosPath.cwd()
    session = await Session.create(work_dir)
    app_on = await KimiCLI.create(session, yolo=True, thinking=True)

    for prompt in prompts:
        name = _clean_filename(prompt)
        log_path = Path(args.out) / f"{name}_thinking_on.jsonl"
        print(f"\n[run] thinking=on prompt='{prompt}'")
        await _run_prompt(app_on, prompt, log_path)

    if args.thinking_off:
        session_off = await Session.create(work_dir)
        app_off = await KimiCLI.create(session_off, yolo=True, thinking=False)
        for prompt in prompts:
            name = _clean_filename(prompt)
            log_path = Path(args.out) / f"{name}_thinking_off.jsonl"
            print(f"\n[run] thinking=off prompt='{prompt}'")
            await _run_prompt(app_off, prompt, log_path)


if __name__ == "__main__":
    asyncio.run(main())
