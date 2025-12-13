"""
Simple harness to prove Kimi K2의 인터리빙 리스닝/툴콜 스트리밍을 실제 코드로 관찰하는 스크립트.

요구 사항:
- KIMI_BASE_URL / KIMI_API_KEY / KIMI_MODEL_NAME (thinking-capable) 환경 변수 설정
- 프로젝트 루트에서 실행: python3 scripts/interleaving_probe.py --prompt "README 요약하고 tests 구조 설명"

동작:
- KimiCLI를 생성해 실제 soul.run()을 수행
- Wire로 흘러오는 모든 이벤트/승인 요청을 콘솔에 요약 출력
- 동일 내용을 JSONL(`--log`)로 저장해 재현 가능하게 증명
"""
from __future__ import annotations

import argparse
import asyncio
import json
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


def _summarize(msg: Any) -> str:
    """Human-friendly one-liner for console."""
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
            ok = getattr(result, "brief", "") or getattr(result, "message", "")
            return f"[tool_result] tcid={tcid} ok={result.__class__.__name__} {ok[:80]}"
        case _:
            return f"[unknown] {msg}"


def _to_jsonable(msg: Any) -> dict[str, Any]:
    """Serialize WireMessage to JSON-friendly dict."""
    return serialize_wire_message(msg)


async def _capture(app: KimiCLI, prompt: str, log_path: Path) -> None:
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
        with log_path.open("w", encoding="utf-8") as f:
            for msg in events:
                f.write(json.dumps(_to_jsonable(msg), ensure_ascii=False) + "\n")
        print(f"Saved wire log to {log_path}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Kimi K2 interleaving probe")
    parser.add_argument(
        "--prompt",
        default="README.md를 요약하고 tests 디렉터리 구조를 정리해줘",
        help="모델에게 던질 요청. 툴콜을 유도하는 프롬프트를 넣어주세요.",
    )
    parser.add_argument(
        "--log",
        default="interleaving_log.jsonl",
        help="Wire 이벤트를 저장할 JSONL 경로",
    )
    parser.add_argument(
        "--thinking-off",
        action="store_true",
        help="thinking 모드를 끄고 비교 실험을 할 때 사용",
    )
    args = parser.parse_args()

    work_dir = KaosPath.cwd()
    session = await Session.create(work_dir)
    app = await KimiCLI.create(
        session,
        yolo=True,  # 승인 자동
        thinking=not args.thinking_off,
    )
    await _capture(app, args.prompt, Path(args.log))


if __name__ == "__main__":
    asyncio.run(main())
