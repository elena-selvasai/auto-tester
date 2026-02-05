# Agent Task: Autonomous Web QA Execution

## 1. Goal
`outputs/test_plan.json` 파일에 정의된 테스트 케이스를 Antigravity의 브라우저 툴을 사용하여 실제로 수행하고, 그 결과를 문서화한다.

## 2. Context & Input
- **Test Plan Path:** `outputs/test_plan.json`
- **Output Directory:** `logs/` 및 `outputs/`
- **Tool Access:** Browser (Preview), File System, Terminal

## 3. Detailed Execution Logic (The "How-To")

### Phase 1: Environment Setup
1. `outputs/test_plan.json` 파일을 읽어 수행해야 할 `test_cases`와 `actions` 리스트를 파악한다.
2. Antigravity의 **Preview Browser**를 실행하고 테스트 대상 URL로 이동한다.

### Phase 2: Sequential Execution & Self-Healing
각 테스트 케이스의 액션을 순차적으로 수행하며 다음 규칙을 따른다:
- **Action Execution:** 각 `action`의 `selector`를 사용하여 요소를 찾고 조작(click, input 등)한다.
- **Verification:** `expected` 결과가 화면에 나타나는지 어설션(Assertion)을 수행한다.
- **⚠️ Self-Healing (중요):** - 만약 정의된 `selector`로 요소를 찾을 수 없다면, 현재 브라우저의 **DOM 트리와 스크린샷을 분석**한다.
    - AI의 판단에 따라 가장 적절한 새로운 Selector를 찾아 실행을 재시도한다.
    - 셀프 힐링이 발생한 경우, 어떤 Selector가 왜 실패했고 무엇으로 대체했는지 로그에 기록한다.

### Phase 3: Evidence Collection
- **Success:** 각 단계 완료 후 상태를 기록한다.
- **Failure:** 실패 시 즉시 해당 화면의 스크린샷을 `logs/screenshots/` 폴더에 `TC_ID_Step_Num_Fail.png`로 저장한다.

## 4. Reporting (Final Output)
모든 테스트 종료 후, `outputs/FINAL_TEST_REPORT.md` 파일을 생성한다. 보고서에는 다음이 포함되어야 한다:
1. 전체 테스트 결과 요약 (Success/Fail Count)
2. 각 테스트 케이스별 상세 수행 로그
3. **Self-Healing Report:** 에이전트가 스스로 수정한 Selector 목록
4. 발견된 버그 및 UI/UX 개선 제안 사항