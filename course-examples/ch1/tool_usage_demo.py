"""
도구 사용 데모 스크립트 - Section 1-4 (Approval), 1-5 (Tools) 실습용

목적:
- 다양한 도구(ReadFile, WriteFile, Grep, Glob)를 실제로 호출
- 승인(Approval) 시스템 동작 관찰
- YOLO 모드 vs 일반 모드 비교
- Wire 이벤트를 통해 ToolCall → (Approval) → ToolResult 흐름 추적

요구 사항:
- KIMI_BASE_URL / KIMI_API_KEY / KIMI_MODEL_NAME 환경 변수 설정
- 프로젝트 루트에서 실행: python3 scripts/ch1/tool_usage_demo.py

동작:
- KimiCLI를 생성해 다양한 도구 호출을 유도하는 프롬프트 실행
- Wire 이벤트에서 ToolCall, ApprovalRequest, ToolResult 추적
- 승인이 필요한 도구(WriteFile)와 안전한 도구(ReadFile) 구분
- YOLO 모드 토글로 승인 흐름 차이 관찰
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


class ToolUsageStats:
    """도구 사용 통계 추적"""
    def __init__(self):
        self.tool_calls: dict[str, int] = {}
        self.approval_requests: list[dict[str, Any]] = []
        self.tool_results: dict[str, list[str]] = {}
        self.safe_tools: set[str] = set()
        self.approval_required_tools: set[str] = set()

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1

    def record_approval(self, tool_call_id: str, sender: str, action: str) -> None:
        self.approval_requests.append({
            "tool_call_id": tool_call_id,
            "sender": sender,
            "action": action
        })
        # sender는 도구 이름
        self.approval_required_tools.add(sender)

    def record_tool_result(self, tool_call_id: str, result_class: str) -> None:
        if tool_call_id not in self.tool_results:
            self.tool_results[tool_call_id] = []
        self.tool_results[tool_call_id].append(result_class)

    def infer_safe_tools(self) -> None:
        """승인 요청 없이 성공한 도구를 안전한 도구로 분류"""
        for tool_name in self.tool_calls.keys():
            if tool_name not in self.approval_required_tools:
                self.safe_tools.add(tool_name)

    def print_summary(self, yolo_mode: bool) -> None:
        print("\n" + "="*60)
        print(f"🛠️  TOOL USAGE DEMO SUMMARY (YOLO: {yolo_mode})")
        print("="*60)

        print(f"\n📊 Tool Calls: {sum(self.tool_calls.values())} total")
        for tool, count in sorted(self.tool_calls.items()):
            emoji = "🔓" if tool in self.safe_tools else "🔒"
            print(f"  {emoji} {tool}: {count}x")

        if self.approval_requests:
            print(f"\n🔐 Approval Requests: {len(self.approval_requests)}")
            for req in self.approval_requests:
                print(f"  - {req['sender']}:{req['action']} (tcid={req['tool_call_id'][:8]}...)")
        else:
            print("\n✅ No approval requests (all tools were safe)")

        print(f"\n🔓 Safe Tools (no approval needed): {len(self.safe_tools)}")
        for tool in sorted(self.safe_tools):
            print(f"  - {tool}")

        print(f"\n🔒 Approval-Required Tools: {len(self.approval_required_tools)}")
        for tool in sorted(self.approval_required_tools):
            print(f"  - {tool}")

        print("="*60 + "\n")


def _summarize(msg: Any, stats: ToolUsageStats, yolo_mode: bool) -> str:
    """Human-friendly one-liner for console with tool emphasis."""
    match msg:
        case ApprovalRequest(tool_call_id=tcid, sender=sender, action=action, description=desc):
            stats.record_approval(tcid, sender, action)
            if yolo_mode:
                return f"🔐➡️✅ [approval AUTO] {sender}:{action} ({desc[:40]})"
            else:
                return f"🔐 [approval] {sender}:{action} ({desc[:40]}) tcid={tcid[:8]}..."
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
            # Think 토큰은 생략
            if kind == "think":
                return ""
            return f"[content:{kind}] {text[:60]}"
        case ToolCall(function=fn):
            stats.record_tool_call(fn.name)
            return f"🛠️  [tool_call] {fn.name} args={fn.arguments[:50]}"
        case ToolCallPart(function=fn):
            return f"[tool_call_part] {getattr(fn, 'name', '')} Δargs={getattr(fn, 'arguments', '')[:50]}"
        case ToolResult(tool_call_id=tcid, result=result):
            result_class = result.__class__.__name__
            stats.record_tool_result(tcid, result_class)
            ok = getattr(result, "brief", "") or getattr(result, "message", "")
            emoji = "✅" if "Error" not in result_class else "❌"
            return f"{emoji} [tool_result] {result_class} {ok[:50]}"
        case _:
            return f"[unknown] {msg}"


def _to_jsonable(msg: Any) -> dict[str, Any]:
    """Serialize WireMessage to JSON-friendly dict."""
    return serialize_wire_message(msg)


async def _demo(app: KimiCLI, prompt: str, log_path: Path, yolo_mode: bool) -> ToolUsageStats:
    events: list[Any] = []
    stats = ToolUsageStats()

    async def ui_loop(wire) -> None:
        wire_ui = wire.ui_side(merge=True)
        while True:
            try:
                msg = await wire_ui.receive()
            except asyncio.QueueShutDown:
                break
            events.append(msg)
            summary = _summarize(msg, stats, yolo_mode)
            if summary:  # Skip empty summaries (think tokens)
                print(summary)

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
        print(f"\n💾 Saved wire log to {log_path}")

    stats.infer_safe_tools()
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tool Usage Demo - Section 1-4 (Approval), 1-5 (Tools) 실습"
    )
    parser.add_argument(
        "--prompt",
        help="모델에게 던질 요청 (기본값: 도구 사용을 유도하는 프롬프트)",
    )
    parser.add_argument(
        "--log",
        default="tool_usage_log.jsonl",
        help="Wire 이벤트를 저장할 JSONL 경로",
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        help="YOLO 모드: 모든 승인 자동 허용 (기본값: True for demo)",
    )
    parser.add_argument(
        "--demo-approval",
        action="store_true",
        help="승인이 필요한 WriteFile 도구 호출 데모",
    )
    args = parser.parse_args()

    # 기본 프롬프트: 다양한 도구 사용 유도
    if args.demo_approval:
        default_prompt = """
다음 작업을 수행해주세요:
1. README.md 파일을 읽어주세요 (ReadFile 사용)
2. src 디렉터리에서 Python 파일을 찾아주세요 (Glob 사용)
3. src에서 "class" 키워드를 검색해주세요 (Grep 사용)
4. /tmp/demo_output.txt 파일에 현재 시각을 기록해주세요 (WriteFile 사용 - 승인 필요)
"""
    else:
        default_prompt = """
다음 안전한 작업들을 수행해주세요:
1. README.md 파일을 읽어주세요
2. src 디렉터리에서 Python 파일 목록을 찾아주세요
3. src에서 "async" 키워드를 검색해주세요
"""

    prompt = args.prompt or default_prompt
    yolo_mode = True if not args.demo_approval else args.yolo

    work_dir = KaosPath.cwd()
    session = await Session.create(work_dir)
    app = await KimiCLI.create(
        session,
        yolo=yolo_mode,
        thinking=True,
    )

    mode_label = "YOLO (auto-approve)" if yolo_mode else "Normal (approval required)"
    print(f"🔍 Starting Tool Usage Demo... (Mode: {mode_label})")
    print(f"📝 Prompt: {prompt[:100]}...")
    print("="*60 + "\n")

    stats = await _demo(app, prompt, Path(args.log), yolo_mode)
    stats.print_summary(yolo_mode)


if __name__ == "__main__":
    asyncio.run(main())
