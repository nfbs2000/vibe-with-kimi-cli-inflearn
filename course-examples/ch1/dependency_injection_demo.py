"""
의존성 주입 마법 체험 실습 - Section 1-1 (agent.py) 핵심 개념

목적:
- inspect.signature를 사용한 자동 파라미터 주입 이해
- 타입 기반 의존성 해결(Dependency Resolution) 체험
- load_agent() 함수의 핵심 로직 단순화 버전 구현
- 도구 클래스가 필요한 타입만 선언하면 자동으로 주입되는 마법 경험

학습 목표:
1. Config, Runtime, Approval 같은 의존성 타입 이해
2. inspect.signature로 생성자 파라미터 분석
3. 타입 힌트 기반 자동 매칭
4. 실제 agent.py의 load_agent() 로직 이해

실행 방법:
    python3 scripts/ch1/dependency_injection_demo.py

    # 또는 상세 로그 모드
    python3 scripts/ch1/dependency_injection_demo.py --verbose
"""
from __future__ import annotations

import argparse
import inspect
from dataclasses import dataclass
from typing import Any, Type, get_type_hints


# ============================================================
# Step 1: 의존성 타입 정의 (Config, Runtime, Approval)
# ============================================================

@dataclass
class Config:
    """설정 정보 - agent.py의 UnifiedConfig와 유사"""
    project_name: str
    max_iterations: int
    debug_mode: bool

    def __repr__(self) -> str:
        return f"Config(project={self.project_name}, max_iter={self.max_iterations})"


@dataclass
class Runtime:
    """런타임 환경 정보 - agent.py의 AgentRuntime과 유사"""
    model_name: str
    api_endpoint: str
    timeout: int

    def __repr__(self) -> str:
        return f"Runtime(model={self.model_name}, timeout={self.timeout}s)"


@dataclass
class Approval:
    """승인 시스템 - agent.py의 Approval과 동일 개념"""
    yolo_mode: bool

    def __repr__(self) -> str:
        mode = "YOLO (auto-approve)" if self.yolo_mode else "Manual approval"
        return f"Approval({mode})"


# ============================================================
# Step 2: 도구 클래스 정의 (다양한 의존성 요구 사항)
# ============================================================

class ReadFileTool:
    """파일 읽기 도구 - Config와 Approval 필요"""

    def __init__(self, config: Config, approval: Approval):
        self.config = config
        self.approval = approval
        print(f"  ✅ ReadFileTool 생성 완료")
        print(f"     - {config}")
        print(f"     - {approval}")

    def execute(self, filepath: str) -> str:
        return f"[ReadFile] Reading {filepath}... (approved={self.approval.yolo_mode})"


class WriteFileTool:
    """파일 쓰기 도구 - Config, Approval, Runtime 모두 필요"""

    def __init__(self, config: Config, approval: Approval, runtime: Runtime):
        self.config = config
        self.approval = approval
        self.runtime = runtime
        print(f"  ✅ WriteFileTool 생성 완료")
        print(f"     - {config}")
        print(f"     - {approval}")
        print(f"     - {runtime}")

    def execute(self, filepath: str, content: str) -> str:
        if not self.approval.yolo_mode:
            return f"[WriteFile] ❌ Approval required for {filepath}"
        return f"[WriteFile] Writing to {filepath}... (timeout={self.runtime.timeout}s)"


class SearchTool:
    """검색 도구 - Config와 Runtime만 필요 (Approval 불필요)"""

    def __init__(self, config: Config, runtime: Runtime):
        self.config = config
        self.runtime = runtime
        print(f"  ✅ SearchTool 생성 완료")
        print(f"     - {config}")
        print(f"     - {runtime}")

    def execute(self, query: str) -> str:
        return f"[Search] Searching '{query}' with {self.runtime.model_name}"


class SimpleTool:
    """간단한 도구 - 의존성 없음"""

    def __init__(self):
        print(f"  ✅ SimpleTool 생성 완료 (의존성 없음)")

    def execute(self) -> str:
        return "[SimpleTool] No dependencies needed!"


# ============================================================
# Step 3: 의존성 주입 컨테이너 (agent.py의 load_agent 핵심 로직)
# ============================================================

class SimpleDIContainer:
    """
    간단한 의존성 주입 컨테이너

    agent.py의 load_agent() 함수에서 하는 일:
    1. 의존성 딕셔너리 준비 (Config, Runtime, Approval 등)
    2. 도구 클래스의 __init__ 파라미터 분석 (inspect.signature)
    3. 타입 기반으로 필요한 의존성 찾아서 자동 주입
    4. 도구 인스턴스 생성 및 반환
    """

    def __init__(self, verbose: bool = False):
        self.dependencies: dict[Type, Any] = {}
        self.verbose = verbose

    def register(self, dependency: Any) -> None:
        """의존성 객체 등록"""
        dep_type = type(dependency)
        self.dependencies[dep_type] = dependency
        if self.verbose:
            print(f"📦 Registered: {dep_type.__name__} = {dependency}")

    def create_tool(self, tool_class: Type) -> Any:
        """
        🎯 의존성 주입의 마법 핵심!

        1. inspect.signature로 생성자(__init__) 파라미터 분석
        2. 타입 힌트 추출 (get_type_hints)
        3. 준비된 딕셔너리에서 타입 매칭해서 찾기
        4. 필요한 파라미터만 자동으로 주입해서 인스턴스 생성
        """
        print(f"\n🔍 Analyzing {tool_class.__name__}...")

        # Step 1: 생성자 시그니처 분석
        sig = inspect.signature(tool_class.__init__)
        type_hints = get_type_hints(tool_class.__init__)

        if self.verbose:
            print(f"  📋 Signature: {sig}")
            print(f"  🏷️  Type hints: {type_hints}")

        # Step 2: 필요한 파라미터 찾기 (self 제외)
        kwargs: dict[str, Any] = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Step 3: 타입 힌트에서 필요한 타입 확인
            if param_name in type_hints:
                param_type = type_hints[param_name]

                # Step 4: 딕셔너리에서 해당 타입 찾기
                if param_type in self.dependencies:
                    kwargs[param_name] = self.dependencies[param_type]
                    print(f"  ✨ 자동 주입: {param_name} = {param_type.__name__}")
                else:
                    raise ValueError(
                        f"❌ 의존성 찾을 수 없음: {param_name}: {param_type.__name__}"
                    )

        # Step 5: 도구 인스턴스 생성 (마법!)
        print(f"  🎁 생성 중...")
        tool_instance = tool_class(**kwargs)
        return tool_instance


# ============================================================
# Step 4: 데모 실행 (agent.py의 load_agent 흐름 재현)
# ============================================================

def demo_dependency_injection(verbose: bool = False) -> None:
    """의존성 주입 마법 체험"""

    print("="*70)
    print("🎓 의존성 주입 마법 체험 데모")
    print("   (agent.py의 load_agent() 핵심 로직 재현)")
    print("="*70)

    # ============================================================
    # Phase 1: 의존성 준비 (load_agent의 4단계)
    # ============================================================
    print("\n📦 Phase 1: 의존성 딕셔너리 준비")
    print("-" * 70)

    container = SimpleDIContainer(verbose=verbose)

    # Config, Runtime, Approval 같은 타입들을 미리 준비
    config = Config(
        project_name="vibe-with-kimi",
        max_iterations=10,
        debug_mode=True
    )
    runtime = Runtime(
        model_name="kimi-k2-thinking",
        api_endpoint="https://api.moonshot.cn",
        timeout=30
    )
    approval = Approval(yolo_mode=True)

    container.register(config)
    container.register(runtime)
    container.register(approval)

    # ============================================================
    # Phase 2: 도구 로딩 (load_agent의 5단계 - 의존성 주입 마법!)
    # ============================================================
    print("\n🔧 Phase 2: 도구 로딩 (의존성 자동 주입)")
    print("-" * 70)

    tools = []

    # 각 도구는 필요한 타입만 선언하면 끝!
    # 컨테이너가 알아서 찾아서 주입해줍니다

    print("\n1️⃣ ReadFileTool 생성 (Config + Approval 필요)")
    read_tool = container.create_tool(ReadFileTool)
    tools.append(read_tool)

    print("\n2️⃣ WriteFileTool 생성 (Config + Approval + Runtime 필요)")
    write_tool = container.create_tool(WriteFileTool)
    tools.append(write_tool)

    print("\n3️⃣ SearchTool 생성 (Config + Runtime 필요)")
    search_tool = container.create_tool(SearchTool)
    tools.append(search_tool)

    print("\n4️⃣ SimpleTool 생성 (의존성 없음)")
    simple_tool = container.create_tool(SimpleTool)
    tools.append(simple_tool)

    # ============================================================
    # Phase 3: 도구 실행 테스트
    # ============================================================
    print("\n🎯 Phase 3: 생성된 도구 실행")
    print("-" * 70)

    print(f"\n{read_tool.execute('example.txt')}")
    print(f"{write_tool.execute('output.txt', 'Hello World')}")
    print(f"{search_tool.execute('dependency injection')}")
    print(f"{simple_tool.execute()}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*70)
    print("✨ 의존성 주입의 마법 정리")
    print("="*70)
    print("""
🎯 핵심 개념:
1. 도구 클래스는 필요한 타입만 생성자에 선언
   예: def __init__(self, config: Config, approval: Approval)

2. inspect.signature로 생성자 파라미터 자동 분석
   → 어떤 타입이 필요한지 파악

3. 준비된 딕셔너리에서 타입 기반으로 검색
   → Config 타입 필요? → 딕셔너리[Config] 찾기

4. 자동으로 파라미터 주입해서 인스턴스 생성
   → tool = ToolClass(config=config_obj, approval=approval_obj)

💡 장점:
- 도구 개발자는 복잡한 초기화 신경 쓸 필요 없음
- 필요한 의존성만 선언하면 자동으로 주입됨
- 타입 안전성 보장 (Type Hints)
- agent.py의 실제 load_agent()가 이렇게 동작함!

📚 agent.py 대응:
- Config → UnifiedConfig
- Runtime → AgentRuntime
- Approval → Approval
- container.create_tool() → load_agent()의 5단계
""")
    print("="*70)


# ============================================================
# Phase 4: 의존성 없는 도구 vs 있는 도구 비교
# ============================================================

def demo_comparison() -> None:
    """수동 vs 자동 주입 비교"""

    print("\n" + "="*70)
    print("🔍 비교: 수동 주입 vs 자동 주입")
    print("="*70)

    config = Config("test", 5, False)
    runtime = Runtime("gpt-4", "https://api.openai.com", 30)
    approval = Approval(True)

    print("\n❌ 수동 주입 (기존 방식):")
    print("-" * 70)
    print("""
# 매번 모든 파라미터를 직접 전달해야 함
read_tool = ReadFileTool(
    config=config,
    approval=approval
)
write_tool = WriteFileTool(
    config=config,
    approval=approval,
    runtime=runtime
)
# 😓 번거롭고 실수하기 쉬움
""")

    print("\n✅ 자동 주입 (agent.py 방식):")
    print("-" * 70)
    print("""
# 컨테이너가 알아서 찾아서 주입
container = SimpleDIContainer()
container.register(config)
container.register(runtime)
container.register(approval)

read_tool = container.create_tool(ReadFileTool)  # 끝!
write_tool = container.create_tool(WriteFileTool)  # 끝!

# 😎 간단하고 깔끔함, 타입 안전!
""")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="의존성 주입 마법 체험 - agent.py 핵심 개념"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세한 로그 출력"
    )
    parser.add_argument(
        "--comparison",
        "-c",
        action="store_true",
        help="수동 vs 자동 주입 비교 출력"
    )
    args = parser.parse_args()

    demo_dependency_injection(verbose=args.verbose)

    if args.comparison:
        demo_comparison()

    print("\n💡 다음 단계:")
    print("   - 실제 agent.py의 load_agent() 함수 코드 읽어보기")
    print("   - tools/ 디렉터리의 다양한 도구 클래스 생성자 확인")
    print("   - 직접 새로운 도구 클래스 만들어서 테스트해보기\n")


if __name__ == "__main__":
    main()
