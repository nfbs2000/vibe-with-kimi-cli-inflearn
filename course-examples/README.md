# Course Examples - Kimi CLI 인터리빙 리스닝 패턴 강의

이 디렉토리는 인프런 강의 "Kimi CLI 인터리빙 리스닝 패턴"의 실습 예제 코드를 포함합니다.

## 디렉토리 구조

```
course-examples/
├── ch1/  # 챕터 1: 기초 개념
│   └── tool_usage_demo.py - 도구 사용 및 승인 시스템 데모
├── ch2/  # 챕터 2: 컨텍스트 관리
│   └── compaction_observer.py - 컨텍스트 압축 관찰 스크립트
└── ch3/  # 챕터 3: 인터리빙 리스닝
    ├── interleaving_probe.py - 인터리빙 리스닝 기본 실험
    └── batch_interleaving_tests.py - 배치 인터리빙 테스트

## 실행 요구 사항

### 환경 변수 설정
```bash
export KIMI_BASE_URL="https://api.moonshot.cn/v1"
export KIMI_API_KEY="sk-..."
export KIMI_MODEL_NAME="kimi-k2-thinking"
```

### 설치
```bash
# 프로젝트 루트에서
uv sync
```

## 실행 예제

### 챕터 1: 도구 사용 데모
```bash
uv run python course-examples/ch1/tool_usage_demo.py --prompt "README.md를 읽어줘"
```

### 챕터 2: 컨텍스트 압축 관찰
```bash
uv run python course-examples/ch2/compaction_observer.py --trigger-compaction
```

### 챕터 3: 인터리빙 리스닝 실험
```bash
# 기본 실험
uv run python course-examples/ch3/interleaving_probe.py --log run_on.jsonl

# Thinking 모드 끄고 비교
uv run python course-examples/ch3/interleaving_probe.py --thinking-off --log run_off.jsonl

# 배치 테스트
uv run python course-examples/ch3/batch_interleaving_tests.py --out logs/ch3_batch
```

## 코드 수정 내역

모든 예제는 실제 Kimi CLI 코드베이스와 완벽히 호환되도록 다음과 같이 수정되었습니다:

1. **Import 수정**: `serialize_wire_message` 사용
2. **Wire API**: `wire.ui_side(merge=True)` 패턴 적용
3. **Async 패턴**: `await Session.create(work_dir)` 사용
4. **Type 안정성**: `KaosPath.cwd()` 사용

## 참고 자료

- [Kimi CLI 공식 문서](https://www.kimi.com/coding/docs/kimi-cli.html)
- [GitHub 리포지토리](https://github.com/nfbs2000/vibe-with-kimi-cli-inflearn)
