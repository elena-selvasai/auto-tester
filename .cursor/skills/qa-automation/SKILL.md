---
name: qa-automation
description: 시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 테스트 시나리오를 생성하고, 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 자동 수행. "QA 자동화", "테스트 시작", "기획서 분석", "QA 테스트" 언급 시 자동 적용.
user-invocable: true
---

# QA 자동화

시나리오 문서 분석부터 웹 테스트 실행, 리포트 생성, GitHub 이슈 등록까지 전체 QA 워크플로우를 자동화합니다.

> **기술 명세 (단일 원본)**: [SPEC.md](../../../SPEC.md) — Phase 수행 가이드, Key Conventions, 산출물 정의

## 빠른 시작

사용자가 "QA 자동화 시작해줘"라고 하면:

1. **Phase 0**: 사전 검증 (GitHub CLI, 테스트 URL, GitHub 리포지토리 수집)
2. `inputs/` 폴더의 시나리오 문서 확인
3. 전체 워크플로우 실행 (Phase 1~6)

## 워크플로우

Phase 0(사전 검증) → 1(문서 분석) → 2(테스트 설계) → 3(테스트 실행) → 4(리포트) → 5(이슈 등록) → 5.5(실패 수정, 선택) → 6(정리)

모든 Phase 전환은 `scripts/qa_cli.py`를 통해서만 수행. `start <N>` exit code 2 → 즉시 중단.

### Phase 0: 사전 검증

```bash
python scripts/qa_cli.py init
python scripts/qa_cli.py start 0
gh --version && gh auth status
```

사용자에게 테스트 URL(필수), GitHub 리포지토리(선택) 요청 후:
```bash
python scripts/qa_cli.py set test_url "<URL>"
python scripts/qa_cli.py set github_repo "<owner/repo>"
python scripts/qa_cli.py complete 0
```

### Phase 1: 문서 분석

```bash
python scripts/qa_cli.py start 1
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

추출 결과(`extract_result.json`, `scenario_draft_source.md`, `reference/`)를 바탕으로 `outputs/scenario_draft.md` 작성.

```bash
python scripts/qa_cli.py complete 1
```

### Phase 2: 테스트 설계 (스켈레톤 + 병렬 생성)

3단계로 수행됩니다:

**Step 1**: 스켈레톤 자동 생성 (Python, ~2초)
```bash
python scripts/qa_cli.py start 2
python scripts/generate_test_skeleton.py --output-dir outputs
```

**Step 2**: 5개 카테고리 병렬 Task 위임 (test-architect × 5)
각 Task가 스켈레톤의 `TODO_SELECTOR`를 실제 CSS 선택자로 교체하고 액션을 구체화하여 `outputs/test_plan_{카테고리}.json` 생성.

**Step 3**: 병합 및 검증
```bash
python scripts/merge_test_plans.py --output-dir outputs
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
python scripts/qa_cli.py complete 2
```

TC 번호, JSON 구조, 선택자 우선순위 등은 [SPEC.md](../../../SPEC.md) Key Conventions 참조.

### Phase 3: 테스트 실행

```bash
python scripts/qa_cli.py start 3
```

`browser_snapshot`으로 실제 DOM 확인 후 테스트 실행. 스크린샷: `screenshot_TC_{tc_id}_{description}.png`.

화면 비교: `python .cursor/skills/qa-automation/scripts/compare_screenshot.py <ref> <screenshot> [--threshold 10]`
구성 체크: `scenario_draft_source.md`의 예상 요소를 DOM에서 확인.

```bash
python scripts/qa_cli.py complete 3
```

### Phase 4~6

Phase 4(리포트), 5(이슈 등록), 5.5(실패 수정), 6(정리)의 상세 가이드는 [SPEC.md](../../../SPEC.md) 참조.

## 유틸리티 스크립트

```bash
python .cursor/skills/qa-automation/scripts/extract_document.py <path> [--output outputs]
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <ref> <actual> [--threshold 10]
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
python scripts/generate_test_skeleton.py [--output-dir outputs]
python scripts/merge_test_plans.py [--output-dir outputs] [--skeleton path]
```

## 에러 대응

| 상황 | 대응 |
|------|------|
| inputs/ 문서 없음 | 파일 추가 요청 |
| URL 접속 불가 | URL 유효성 확인 |
| 요소 찾기 실패 | DOM 재분석 후 선택자 수정 |
| GitHub CLI 미설치 | 설치 안내, `skip_github=true` |
| **기획서 vs 실제 동작 불일치** | **임의로 pass 처리하지 말고 반드시 사용자에게 확인** |
| **앱 버그 수정 필요** | **AI는 앱 소스 코드를 수정할 수 없음 — 사용자에게 보고, 수정 후 재테스트 요청 대기** |
