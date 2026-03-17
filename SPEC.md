# AI QA 자동화 — 기술 명세 (단일 원본)

> 이 파일이 Phase 수행 가이드, Key Conventions, 산출물 정의의 **공식 원본**입니다.
> 다른 문서(CLAUDE.md, README.md, agent 파일)는 이 파일을 참조합니다.

## 목표

입력된 시나리오 문서(PPTX/DOCX/PDF/이미지)를 바탕으로 웹 자동화 테스트를 수행하고, 결과를 리포팅한다.

YAML+CLI 상태 관리를 통해 Phase 순서 보장, 중단 후 재개, 검증 게이트를 지원한다.

---

## 아키텍처

```
inputs/                          # 입력 문서
scripts/qa_cli.py                # YAML+CLI 상태 관리 (검증 게이트)
.cursor/skills/qa-automation/scripts/  # 문서 추출·비교 Python 스크립트
.claude/agents/ (또는 .cursor/agents/) # AI 에이전트 정의
outputs/                         # 산출물 (qa_state.yaml 포함)
```

---

## Phase별 수행 가이드

모든 Phase 전환은 `scripts/qa_cli.py`를 통해서만 수행됩니다.

```bash
python scripts/qa_cli.py init      # 새 세션 초기화
python scripts/qa_cli.py start <N> # Phase N 시작 (검증 게이트)
python scripts/qa_cli.py complete <N> --files [산출물...]  # Phase N 완료
python scripts/qa_cli.py fail <N> "사유"                   # Phase N 실패
python scripts/qa_cli.py status    # 전체 현황
python scripts/qa_cli.py next      # 다음 할 일
python scripts/qa_cli.py resume    # 중단 지점 재개
```

### Phase 0: 사전 검증

- GitHub CLI 설치/로그인 확인
- 테스트 URL 수집 → `qa_cli.py set test_url <url>`
- GitHub Repo 수집 → `qa_cli.py set github_repo <owner/repo>`
- 산출물: 없음 (config만 저장)

### Phase 1: 문서 분석

- `inputs/`의 PPTX/DOCX/PDF/이미지 분석
- `extract_document.py`로 텍스트, 표, 노트, 삽입 이미지 추출
- 슬라이드/페이지별 참조 이미지 → `outputs/reference/`
- 산출물: `scenario_draft.md`, `extract_result.json`, `scenario_draft_source.md`
- 검증 게이트: Phase 0 completed 필요

### Phase 2: 테스트 설계

- `scenario_draft.md`를 JSON 테스트 플랜으로 변환
- 5개 카테고리: `basic_function`, `button_state`, `navigation`, `edge_case`, `accessibility`
- `validate_json.py`로 유효성 검증
- 산출물: `test_plan.json`
- 검증 게이트: Phase 1 completed + `scenario_draft.md` 존재 필요

### Phase 3: 테스트 실행

- Playwright 브라우저 자동화로 `test_plan.json` 순차 실행
- 스크린샷 캡처 + `compare_screenshot.py`로 화면 비교
- 구성 체크 리스트 검증 (`scenario_draft_source.md`)
- 산출물: `test_result.json`, `screenshot_TC_{tc_id}_{description}.png`
- 검증 게이트: Phase 2 completed + `test_plan.json` 존재 필요

### Phase 4: 리포트 생성

- `test_result.json`을 Markdown 리포트로 변환
- 카테고리별 통계, 스크린샷 목록, 발견 사항 포함
- 산출물: `REPORT.md`
- 검증 게이트: Phase 3 completed + `test_result.json` 존재 필요

### Phase 5: GitHub 이슈 등록

- 실패 테스트 → `gh issue create`로 GitHub Issues 등록
- `skip_github=true`이면 자동 skip
- 산출물: `issues_created.json`
- 검증 게이트: Phase 4 completed + `REPORT.md` 존재 필요

### Phase 5.5: 실패 자동 수정 (선택)

- 실패 원인 분류: `selector_mismatch`, `text_mismatch`, `timing_issue`, `app_bug` 등
- `app_bug`는 수정하지 않음 — 사용자에게 보고만
- **모든 수정은 사용자 승인 후 적용**
- 산출물: `fix_log.json`
- 검증 게이트: Phase 5 completed 필요

### Phase 6: 정리 (Cleanup)

- 임시 파일 삭제 (`debug_*.png`, `issue_ISS_*`, 임시 스크립트 등)
- 이전 결과 폴더 삭제 제안 (`outputs_/` 등)
- 검증 게이트: Phase 4 completed 필요 (5, 5.5는 선택적)

---

## 검증 게이트 동작

```bash
# 예: Phase 1 미완료 상태에서 Phase 2 시작 시도
python scripts/qa_cli.py start 2

# 출력:
# [GATE BLOCKED] Phase 2 시작 거부
# 사유: Phase 1 (문서 분석)이(가) 완료되지 않았습니다.
# 해결 방법: python scripts/qa_cli.py complete 1
# exit code: 2
```

에이전트는 exit code 2를 받으면 즉시 중단하고 사유를 사용자에게 보고합니다.

---

## 산출물 목록

| 파일 | Phase | 설명 |
|------|-------|------|
| `qa_state.yaml` | 전체 | Phase 진행 상태 DB |
| `scenario_draft.md` | 1 | 테스트 시나리오 |
| `extract_result.json` | 1 | 문서 추출 결과 |
| `scenario_draft_source.md` | 1 | 추출 요약 + 구성 체크 |
| `reference/*.png` | 1 | 기획서 참조 이미지 |
| `test_plan.json` | 2 | JSON 테스트 플랜 |
| `test_result.json` | 3 | 테스트 실행 결과 |
| `screenshot_TC_*.png` | 3 | 테스트 스크린샷 |
| `REPORT.md` | 4 | 최종 리포트 |
| `issues_created.json` | 5 | 생성된 이슈 목록 |
| `fix_log.json` | 5.5 | 자동 수정 이력 |

---

## Key Conventions

### test_plan.json 구조

5개 카테고리와 TC 번호 범위:

| 카테고리 | TC 범위 | 최소 수 |
|---------|---------|--------|
| `basic_function` | TC_001~050 | 8개 |
| `button_state` | TC_051~100 | 4개 |
| `navigation` | TC_101~150 | 3개 |
| `edge_case` | TC_151~180 | 3개 |
| `accessibility` | TC_181~200 | 2개 |

`base_url`은 항상 `"${base_url}"` 플레이스홀더로 설정합니다.

지원 액션: `navigate`, `click`, `input`, `check`, `wait`, `screenshot`, `hover`, `check_attribute`, `compare_with_reference`

### 선택자 우선순위

`data-testid` > `id` > `aria-label` > `class`

### auto-fixer 수정 범위

- **수정 가능**: `selector_mismatch`, `text_mismatch`, `date_format`, `timing_issue`, `scroll_target`
- **수정 불가** (`app_bug`): 기능 미구현, 동작 오류 → 사용자에게 보고만
- **모든 수정은 사용자 승인 후에만 적용**

### 오류 처리

- 요소 찾기 실패 → 대체 선택자 시도
- 타임아웃 → 대기 시간 2배 후 최대 2회 재시도
- 네트워크 오류 → 5초 간격 최대 3회 재시도

### Phase 6 정리 대상

삭제 대상 (`outputs/` 내 임시 파일):
- `issue_ISS_*`, `issue_body_TC*.md`, `REPORT_EXECUTED.md`, `SUMMARY.md`
- `TEST_EXECUTION_SUMMARY.md`, `test_result_executed.json`, `debug_*.png`

삭제 대상 (루트 임시 스크립트 — AI가 세션 중 생성한 것):
- `explore_page.py`, `explore_dom*.py`, `run_test_tc*.py`, `run_tests.py`, `create_github_dir.py`, `run_commands.bat`

보존 대상 (삭제 금지):
- `scripts/run_all_tests.py`, `outputs/issue_body.md`

---

## 의존성

```
playwright>=1.40.0
python-pptx>=0.6.21
python-docx>=1.0.0
PyMuPDF>=1.23.0
Pillow>=10.0.0
imagehash>=4.3.0
pyyaml>=6.0.0
```
