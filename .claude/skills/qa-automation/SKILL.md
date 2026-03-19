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

## Claude Code 에이전트 활용

이 Skill은 Task 도구를 통해 서브에이전트를 호출합니다:

| 에이전트 | subagent_type | Phase |
|----------|---------------|-------|
| 문서 분석 | `doc-analyst` | 1 |
| 테스트 설계 | `test-architect` | 2 |
| 테스트 실행 | `qa-executor` | 3 |
| 실패 수정 | `auto-fixer` | 5.5 |
| 총괄 | `qa-master` | 전체 |

## 워크플로우

Phase 0(사전 검증) → 1(문서 분석) → 2(테스트 설계) → 3(테스트 실행) → 4(리포트) → 5(이슈 등록) → 5.5(실패 수정, 선택) → 6(정리)

모든 Phase 전환은 `scripts/qa_cli.py`를 통해서만 수행. `start <N>` exit code 2 → 즉시 중단.

Phase별 상세 가이드, 산출물 정의, 정리 대상은 모두 [SPEC.md](../../../SPEC.md) 참조.

## 유틸리티 스크립트

```bash
# 문서 추출
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
# 화면 비교
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <ref.png> <actual.png> [--threshold 10]
# JSON 검증
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

## 에러 대응

| 상황 | 대응 |
|------|------|
| inputs/ 문서 없음 | 파일 추가 요청 |
| URL 접속 불가 | URL 유효성 확인 |
| 요소 찾기 실패 | DOM 재분석 후 선택자 수정 |
| GitHub CLI 미설치 | 설치 안내, `skip_github=true` |
| **기획서 vs 실제 동작 불일치** | **임의로 pass 처리하지 말고 반드시 사용자에게 확인** |
