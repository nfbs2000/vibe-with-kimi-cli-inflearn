"""
Compaction 동작 관찰 스크립트 - Section 2-5 실습용

목적:
- 긴 대화를 유도해 컨텍스트 압축(compaction)을 트리거
- Wire 이벤트를 통해 CompactionBegin/End 캡처
- StatusUpdate로 context_usage 추이 추적
- 압축 전/후 상태를 JSONL로 기록하여 증명

요구 사항:
- KIMI_BASE_URL / KIMI_API_KEY / KIMI_MODEL_NAME 환경 변수 설정
- 프로젝트 루트에서 실행: python3 scripts/ch2/compaction_observer.py

동작:
- KimiCLI를 생성해 실제 soul.run()을 수행
- Wire로 흘러오는 모든 이벤트를 콘솔에 요약 출력
- CompactionBegin/End 이벤트를 특별히 강조
- context_usage 추이를 실시간 추적
- 동일 내용을 JSONL로 저장해 재현 가능하게 증명
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


class CompactionStats:
    """Compaction 통계 추적"""
    def __init__(self):
        self.context_usage_history: list[float] = []
        self.compaction_events: list[dict[str, Any]] = []
        self.step_count = 0
        self.tool_call_count = 0
        self.before_compaction_usage: float | None = None
        self.after_compaction_usage: float | None = None

    def record_status(self, usage: float) -> None:
        self.context_usage_history.append(usage)

    def record_compaction_begin(self, step: int) -> None:
        if self.context_usage_history:
            self.before_compaction_usage = self.context_usage_history[-1]
        self.compaction_events.append({
            "type": "begin",
            "step": step,
            "context_usage_before": self.before_compaction_usage
        })

    def record_compaction_end(self, step: int) -> None:
        if self.context_usage_history:
            self.after_compaction_usage = self.context_usage_history[-1]
        if self.compaction_events:
            self.compaction_events[-1].update({
                "type": "complete",
                "context_usage_after": self.after_compaction_usage
            })

    def print_summary(self) -> None:
        print("\n" + "="*60)
        print("📊 COMPACTION OBSERVER SUMMARY")
        print("="*60)
        print(f"Total Steps: {self.step_count}")
        print(f"Total Tool Calls: {self.tool_call_count}")
        print(f"Context Usage Measurements: {len(self.context_usage_history)}")

        if self.context_usage_history:
            print(f"Peak Context Usage: {max(self.context_usage_history):.2%}")
            print(f"Final Context Usage: {self.context_usage_history[-1]:.2%}")

        if self.compaction_events:
            print(f"\n🗜️  Compaction Events: {len(self.compaction_events)}")
            for i, event in enumerate(self.compaction_events, 1):
                print(f"  #{i}: Step {event.get('step', '?')}")
                before = event.get('context_usage_before')
                after = event.get('context_usage_after')
                if before is not None and after is not None:
                    saved = before - after
                    print(f"       Before: {before:.2%} → After: {after:.2%}")
                    print(f"       Saved: {saved:.2%} ({saved*100:.1f} percentage points)")
        else:
            print("\n⚠️  No compaction triggered during this run")
            print("   Try using --trigger-compaction flag or longer prompts")

        print("="*60 + "\n")


def _summarize(msg: Any, stats: CompactionStats) -> str:
    """Human-friendly one-liner for console with compaction emphasis."""
    match msg:
        case ApprovalRequest(tool_call_id=tcid, sender=sender, action=action, description=desc):
            return f"[approval] {sender}:{action} ({desc}) tcid={tcid}"
        case StepBegin(n=n):
            stats.step_count = n
            return f"[step {n}] begin"
        case StepInterrupted():
            return "[step] interrupted"
        case CompactionBegin():
            stats.record_compaction_begin(stats.step_count)
            return "🗜️  [COMPACTION] BEGIN - Starting context compression..."
        case CompactionEnd():
            stats.record_compaction_end(stats.step_count)
            return "✅ [COMPACTION] END - Compression complete"
        case StatusUpdate(status=status):
            stats.record_status(status.context_usage)
            usage_bar = "█" * int(status.context_usage * 20)
            return f"[status] context_usage={status.context_usage:.2%} |{usage_bar}"
        case ContentPart():
            kind = msg.type if hasattr(msg, "type") else "content"
            text = getattr(msg, "text", "") or str(msg)
            return f"[content:{kind}] {text[:60]}"
        case ToolCall(function=fn):
            stats.tool_call_count += 1
            return f"[tool_call #{stats.tool_call_count}] {fn.name} args={fn.arguments[:60]}"
        case ToolCallPart(function=fn):
            return f"[tool_call_part] {getattr(fn, 'name', '')} Δargs={getattr(fn, 'arguments', '')[:60]}"
        case ToolResult(tool_call_id=tcid, result=result):
            ok = getattr(result, "brief", "") or getattr(result, "message", "")
            return f"[tool_result] tcid={tcid} ok={result.__class__.__name__} {ok[:60]}"
        case _:
            return f"[unknown] {msg}"


def _to_jsonable(msg: Any) -> dict[str, Any]:
    """Serialize WireMessage to JSON-friendly dict."""
    return serialize_wire_message(msg)


async def _observe(app: KimiCLI, prompt: str, log_path: Path) -> CompactionStats:
    events: list[Any] = []
    stats = CompactionStats()

    async def ui_loop(wire) -> None:
        wire_ui = wire.ui_side(merge=True)
        while True:
            try:
                msg = await wire_ui.receive()
            except asyncio.QueueShutDown:
                break
            events.append(msg)
            print(_summarize(msg, stats))

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

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compaction Observer - Section 2-5 실습 스크립트"
    )
    parser.add_argument(
        "--prompt",
        help="모델에게 던질 요청. 기본값은 긴 대화를 유도하는 프롬프트",
    )
    parser.add_argument(
        "--log",
        default="compaction_log.jsonl",
        help="Wire 이벤트를 저장할 JSONL 경로",
    )
    parser.add_argument(
        "--trigger-compaction",
        action="store_true",
        help="Compaction을 트리거하기 위한 긴 프롬프트 사용 (여러 파일 분석)",
    )
    args = parser.parse_args()

    # 기본 프롬프트: compaction 트리거용 긴 작업
    if args.trigger_compaction:
        default_prompt = """
다음 작업을 수행해주세요:
1. src 디렉터리의 모든 Python 파일 목록을 찾아주세요
2. 각 파일의 크기와 마지막 수정 시간을 조사해주세요
3. 가장 최근 수정된 파일 5개를 찾아 내용을 읽어주세요
4. 각 파일의 주요 클래스와 함수를 분석해주세요
5. tests 디렉터리와 tests_ai 디렉터리의 구조를 비교해주세요
6. 테스트 커버리지를 개선할 수 있는 제안을 해주세요
7. 전체 프로젝트 구조를 요약해주세요
"""
    else:
        default_prompt = "README.md를 읽고 프로젝트의 주요 기능을 설명해주세요"

    prompt = args.prompt or default_prompt

    work_dir = KaosPath.cwd()
    session = await Session.create(work_dir)
    app = await KimiCLI.create(
        session,
        yolo=True,  # 승인 자동
        thinking=True,
    )

    print("🔍 Starting Compaction Observer...")
    print(f"📝 Prompt: {prompt[:100]}...")
    print("="*60 + "\n")

    stats = await _observe(app, prompt, Path(args.log))
    stats.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
