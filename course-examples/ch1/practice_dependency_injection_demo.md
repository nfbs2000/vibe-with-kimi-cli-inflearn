# 실습: Dependency Injection Demo - 의존성 주입 마법 체험

**섹션**: 1-1 (Agent Loading)
**난이도**: ⭐⭐ (초중급)
**소요시간**: 30분
**학습목표**:
- inspect.signature를 통한 자동 파라미터 분석 이해
- 타입 기반 의존성 해결(Dependency Resolution) 체험
- agent.py의 load_agent() 함수 핵심 로직 이해
- 도구 클래스가 필요한 타입만 선언하면 자동 주입되는 "마법" 경험

---

## 📋 사전 준비

### 1. 프로젝트 구조 확인

```bash
# 현재 위치 확인
pwd
# /path/to/vibe-with-kimi-cli-main

# 필요한 디렉터리 확인
ls -la .claude/skills/course-builder/output/inflearn_sections/ch1/
# dependency_injection_demo.py 파일이 존재해야 함
```

### 2. 데모 스크립트 위치 확인

```bash
ls -la .claude/skills/course-builder/output/inflearn_sections/ch1/dependency_injection_demo.py
# 파일이 존재하는지 확인
```

### 3. Python 환경 확인

```bash
python3 --version
# Python 3.8 이상이어야 함 (type hints, dataclass 지원)
```

---

## 🎯 실습 1: 의존성 주입 마법 체험 (기본 실행)

### 목표
의존성 주입 컨테이너가 자동으로 필요한 의존성을 찾아 주입하는 과정을 관찰합니다.

### 실행 명령

```bash
cd .claude/skills/course-builder/output/inflearn_sections/ch1
python3 dependency_injection_demo.py
```

### 예상 출력

```
======================================================================
🎓 의존성 주입 마법 체험 데모
   (agent.py의 load_agent() 핵심 로직 재현)
======================================================================

📦 Phase 1: 의존성 딕셔너리 준비
----------------------------------------------------------------------

🔧 Phase 2: 도구 로딩 (의존성 자동 주입)
----------------------------------------------------------------------

1️⃣ ReadFileTool 생성 (Config + Approval 필요)

🔍 Analyzing ReadFileTool...
  ✨ 자동 주입: config = Config
  ✨ 자동 주입: approval = Approval
  🎁 생성 중...
  ✅ ReadFileTool 생성 완료
     - Config(project=vibe-with-kimi, max_iter=10)
     - Approval(YOLO (auto-approve))

2️⃣ WriteFileTool 생성 (Config + Approval + Runtime 필요)

🔍 Analyzing WriteFileTool...
  ✨ 자동 주입: config = Config
  ✨ 자동 주입: approval = Approval
  ✨ 자동 주입: runtime = Runtime
  🎁 생성 중...
  ✅ WriteFileTool 생성 완료
     - Config(project=vibe-with-kimi, max_iter=10)
     - Approval(YOLO (auto-approve))
     - Runtime(model=kimi-k2-thinking, timeout=30s)

3️⃣ SearchTool 생성 (Config + Runtime 필요)

🔍 Analyzing SearchTool...
  ✨ 자동 주입: config = Config
  ✨ 자동 주입: runtime = Runtime
  🎁 생성 중...
  ✅ SearchTool 생성 완료
     - Config(project=vibe-with-kimi, max_iter=10)
     - Runtime(model=kimi-k2-thinking, timeout=30s)

4️⃣ SimpleTool 생성 (의존성 없음)

🔍 Analyzing SimpleTool...
  🎁 생성 중...
  ✅ SimpleTool 생성 완료 (의존성 없음)

🎯 Phase 3: 생성된 도구 실행
----------------------------------------------------------------------

[ReadFile] Reading example.txt... (approved=True)
[WriteFile] Writing to output.txt... (timeout=30s)
[Search] Searching 'dependency injection' with kimi-k2-thinking
[SimpleTool] No dependencies needed!

======================================================================
✨ 의존성 주입의 마법 정리
======================================================================

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
======================================================================

💡 다음 단계:
   - 실제 agent.py의 load_agent() 함수 코드 읽어보기
   - tools/ 디렉터리의 다양한 도구 클래스 생성자 확인
   - 직접 새로운 도구 클래스 만들어서 테스트해보기
```

### 관찰 포인트

1. **자동 파라미터 주입**
   - `✨ 자동 주입: config = Config` → 타입 기반 자동 매칭
   - 도구마다 필요한 의존성이 다름 (ReadFile: 2개, WriteFile: 3개, SimpleTool: 0개)
   - 컨테이너가 알아서 필요한 것만 주입

2. **타입 안전성**
   - Config 타입이 필요하면 → 딕셔너리에서 Config 타입 찾기
   - 타입이 맞지 않으면 에러 발생 (자동으로 검증됨)

3. **agent.py와의 연결**
   - 실제 agent.py의 load_agent() 5단계가 이렇게 동작
   - 도구 클래스는 필요한 것만 선언 (`__init__` 파라미터)
   - 컨테이너가 자동으로 찾아서 주입

---

## 🎯 실습 2: 상세 로그 모드 - inspect.signature 분석 과정 관찰

### 목표
inspect.signature가 생성자를 분석하는 과정을 상세하게 관찰합니다.

### 실행 명령

```bash
python3 dependency_injection_demo.py --verbose
```

### 예상 출력 (일부)

```
📦 Phase 1: 의존성 딕셔너리 준비
----------------------------------------------------------------------
📦 Registered: Config = Config(project=vibe-with-kimi, max_iter=10)
📦 Registered: Runtime = Runtime(model=kimi-k2-thinking, timeout=30s)
📦 Registered: Approval = Approval(YOLO (auto-approve))

🔧 Phase 2: 도구 로딩 (의존성 자동 주입)
----------------------------------------------------------------------

1️⃣ ReadFileTool 생성 (Config + Approval 필요)

🔍 Analyzing ReadFileTool...
  📋 Signature: (self, config: __main__.Config, approval: __main__.Approval)
  🏷️  Type hints: {'config': <class '__main__.Config'>, 'approval': <class '__main__.Approval'>}
  ✨ 자동 주입: config = Config
  ✨ 자동 주입: approval = Approval
  🎁 생성 중...
  ✅ ReadFileTool 생성 완료
     - Config(project=vibe-with-kimi, max_iter=10)
     - Approval(YOLO (auto-approve))
...
```

### 관찰 포인트

1. **Signature 분석**
   - `📋 Signature: (self, config: Config, approval: Approval)`
   - inspect.signature가 생성자의 파라미터 목록을 추출함

2. **Type Hints 추출**
   - `🏷️ Type hints: {'config': <class 'Config'>, 'approval': <class 'Approval'>}`
   - get_type_hints()로 각 파라미터의 타입 정보 추출

3. **딕셔너리 검색 과정**
   - config 파라미터 → Config 타입 필요 → 딕셔너리에서 Config 찾기
   - approval 파라미터 → Approval 타입 필요 → 딕셔너리에서 Approval 찾기

---

## 🎯 실습 3: 수동 vs 자동 주입 비교

### 목표
기존 수동 주입 방식과 의존성 주입 패턴의 차이를 이해합니다.

### 실행 명령

```bash
python3 dependency_injection_demo.py --comparison
```

### 예상 출력

```
======================================================================
🔍 비교: 수동 주입 vs 자동 주입
======================================================================

❌ 수동 주입 (기존 방식):
----------------------------------------------------------------------

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

✅ 자동 주입 (agent.py 방식):
----------------------------------------------------------------------

# 컨테이너가 알아서 찾아서 주입
container = SimpleDIContainer()
container.register(config)
container.register(runtime)
container.register(approval)

read_tool = container.create_tool(ReadFileTool)  # 끝!
write_tool = container.create_tool(WriteFileTool)  # 끝!

# 😎 간단하고 깔끔함, 타입 안전!
```

### 관찰 포인트

1. **코드 간결성**
   - 수동: 매번 모든 파라미터를 직접 전달
   - 자동: 도구 클래스만 전달하면 끝

2. **실수 방지**
   - 수동: 파라미터 순서 틀리면 버그 발생
   - 자동: 타입 기반이라 순서 무관, 타입 체크 자동

3. **유지보수성**
   - 수동: 의존성 추가 시 모든 호출 코드 수정 필요
   - 자동: 생성자 파라미터만 수정하면 자동 반영

---

## 🎯 실습 4: 커스텀 도구 클래스 추가

### 목표
새로운 도구 클래스를 추가하여 의존성 주입이 유연하게 동작하는지 확인합니다.

### 코드 수정

dependency_injection_demo.py 파일을 열어서 다음 클래스를 추가:

```python
class CustomTool:
    """커스텀 도구 - Runtime만 필요"""

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        print(f"  ✅ CustomTool 생성 완료")
        print(f"     - {runtime}")

    def execute(self, task: str) -> str:
        return f"[CustomTool] Executing {task} with {self.runtime.model_name}"
```

### demo_dependency_injection 함수에 추가

```python
# Phase 2의 마지막 부분 (line 258 근처)에 추가
print("\n5️⃣ CustomTool 생성 (Runtime만 필요)")
custom_tool = container.create_tool(CustomTool)
tools.append(custom_tool)

# Phase 3의 마지막 부분 (line 269 근처)에 추가
print(f"{custom_tool.execute('custom task')}")
```

### 실행 및 확인

```bash
python3 dependency_injection_demo.py
```

**예상 출력**:
```
5️⃣ CustomTool 생성 (Runtime만 필요)

🔍 Analyzing CustomTool...
  ✨ 자동 주입: runtime = Runtime
  🎁 생성 중...
  ✅ CustomTool 생성 완료
     - Runtime(model=kimi-k2-thinking, timeout=30s)
...
[CustomTool] Executing custom task with kimi-k2-thinking
```

### 관찰 포인트

1. **유연한 의존성 요구**
   - CustomTool은 Runtime만 필요함
   - Config, Approval은 자동으로 무시됨
   - 필요한 것만 정확하게 주입됨

2. **확장성**
   - 새 도구 추가가 매우 쉬움
   - 생성자 파라미터만 정의하면 자동 동작
   - agent.py도 이렇게 새 도구 추가 가능

---

## 📊 코드 분석: 핵심 로직 이해

### 1. 의존성 타입 정의

```python
@dataclass
class Config:
    """설정 정보 - agent.py의 UnifiedConfig와 유사"""
    project_name: str
    max_iterations: int
    debug_mode: bool
```

**역할**:
- agent.py의 UnifiedConfig에 대응
- 에이전트 실행에 필요한 설정값 저장
- 타입 기반 주입의 "키" 역할

### 2. SimpleDIContainer 클래스

```python
class SimpleDIContainer:
    def __init__(self, verbose: bool = False):
        self.dependencies: dict[Type, Any] = {}  # 타입을 키로 사용
        self.verbose = verbose

    def register(self, dependency: Any) -> None:
        """의존성 객체 등록"""
        dep_type = type(dependency)
        self.dependencies[dep_type] = dependency
```

**핵심**:
- `dict[Type, Any]` → 타입을 키로 사용하는 딕셔너리
- `type(dependency)` → 객체의 타입을 키로 저장
- Config 객체 등록 → `{Config: config_instance}`

### 3. create_tool 메서드 - 마법의 핵심!

```python
def create_tool(self, tool_class: Type) -> Any:
    # Step 1: 생성자 시그니처 분석
    sig = inspect.signature(tool_class.__init__)
    type_hints = get_type_hints(tool_class.__init__)

    # Step 2: 필요한 파라미터 찾기
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

    # Step 5: 도구 인스턴스 생성
    return tool_class(**kwargs)
```

**동작 원리**:
1. `inspect.signature` → 생성자 파라미터 목록 추출
2. `get_type_hints` → 각 파라미터의 타입 정보 추출
3. 타입 기반 딕셔너리 검색 → `self.dependencies[Config]`
4. `**kwargs` 언패킹 → 자동으로 파라미터 전달

**agent.py 연결**:
- agent.py의 `load_agent()` 5단계가 이 로직
- 실제로는 더 복잡하지만 핵심 원리는 동일

---

## 🧪 실험 아이디어

### 실험 1: 의존성 누락 테스트

```python
# 코드 수정: container.register(runtime) 주석 처리
# container.register(runtime)  # 주석 처리!

python3 dependency_injection_demo.py
```

**예상 결과**:
```
❌ 의존성 찾을 수 없음: runtime: Runtime
```
→ 필요한 의존성이 없으면 명확한 에러 메시지

### 실험 2: 복잡한 의존성 체인

```python
class DatabaseTool:
    def __init__(self, config: Config, runtime: Runtime, approval: Approval):
        # 모든 의존성 필요
        pass

class CacheTool:
    def __init__(self):
        # 의존성 없음
        pass
```

→ 다양한 의존성 조합이 자동으로 처리되는지 확인

### 실험 3: 타입 변경 실험

```python
# 잘못된 타입으로 등록
container.register("문자열")  # str 타입
container.register(123)       # int 타입

# ReadFileTool은 Config, Approval 필요 → 에러!
```

→ 타입 안전성이 보장되는지 확인

---

## ✅ 체크리스트

실습을 완료하면서 다음 항목을 확인하세요:

- [ ] 기본 실행으로 4가지 도구가 자동 주입되는 것을 확인했다
- [ ] `--verbose` 모드로 inspect.signature 분석 과정을 관찰했다
- [ ] `--comparison` 모드로 수동 vs 자동 주입의 차이를 이해했다
- [ ] SimpleDIContainer의 `create_tool()` 메서드 로직을 이해했다
- [ ] 타입 기반 딕셔너리 검색 원리를 이해했다
- [ ] agent.py의 load_agent() 5단계가 이렇게 동작함을 이해했다
- [ ] 커스텀 도구 클래스를 추가하여 유연성을 확인했다
- [ ] 의존성 주입 패턴의 장점(간결성, 타입 안전성, 유지보수성)을 체감했다

---

## 🎓 학습 정리

### 핵심 개념

1. **의존성 주입(Dependency Injection)**
   - 객체가 필요로 하는 의존성을 외부에서 주입
   - 생성자에 필요한 타입만 선언하면 자동 주입
   - 결합도 낮춤, 테스트 용이성 향상

2. **타입 기반 해결(Type-based Resolution)**
   ```python
   dependencies: dict[Type, Any] = {
       Config: config_instance,
       Runtime: runtime_instance,
       Approval: approval_instance
   }
   ```
   - 타입을 딕셔너리의 키로 사용
   - 파라미터 타입 → 딕셔너리 검색 → 자동 매칭

3. **inspect 모듈 활용**
   - `inspect.signature()` → 함수/메서드 파라미터 분석
   - `get_type_hints()` → 타입 힌트 정보 추출
   - 런타임에 타입 정보를 활용한 자동화

4. **agent.py 연결**
   ```
   agent.py의 load_agent() 5단계:
   1. 에이전트 스펙 로드
   2. 시스템 프롬프트 로드
   3. 서브에이전트 로딩
   4. 의존성 딕셔너리 준비 ← 여기!
   5. 도구 로딩 (자동 주입) ← 여기!
   6. MCP 서버 도구 추가
   7. Agent 객체 생성
   ```

### 실무 적용

1. **새 도구 추가 방법**
   ```python
   # tools/my_tool.py
   class MyTool:
       def __init__(self, config: Config, runtime: Runtime):
           # 필요한 의존성만 선언!
           pass
   ```
   → agent.py가 자동으로 주입해줌

2. **의존성 변경 시**
   - 생성자 파라미터만 수정
   - 호출 코드는 수정 불필요
   - 타입 안전성 자동 보장

3. **테스트 작성 시**
   ```python
   # Mock 객체 주입 가능
   mock_config = Config("test", 1, False)
   container.register(mock_config)
   tool = container.create_tool(MyTool)
   ```

### 다음 단계

- **Section 1-2**: Runtime 생성 과정 학습
- **Section 1-3**: Tool 클래스 구현 패턴
- **Section 1-4**: Approval 시스템 동작 원리
- **고급**: 실제 agent.py 코드 분석 및 커스텀 도구 개발

---

## 🔗 참고 자료

### 관련 파일
- `src/kimi_cli/agent.py:247-350` - load_agent() 함수 전체
- `src/kimi_cli/config.py` - UnifiedConfig 클래스
- `src/kimi_cli/runtime.py` - AgentRuntime 클래스
- `src/kimi_cli/approval.py` - Approval 클래스
- `src/kimi_cli/tools/` - 다양한 도구 구현 예시

### Python 문서
- [inspect 모듈](https://docs.python.org/3/library/inspect.html)
- [typing.get_type_hints()](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)

### 디자인 패턴
- Dependency Injection Pattern
- Service Locator Pattern
- Inversion of Control (IoC)

---

**작성일**: 2025-12-14
**버전**: 1.0
**난이도**: ⭐⭐ (초중급)
