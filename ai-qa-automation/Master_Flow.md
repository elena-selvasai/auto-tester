# Project Workflow Guide
1. **Input:** `inputs/` 폴더에 시나리오 PPTX를 넣습니다.
2. **Analysis:** `DocAnalyst`가 `scenario_draft.md`를 생성합니다.
3. **Planning:** `TestArchitect`가 `test_plan.json`을 생성합니다.
4. **Execution:** `QAExecutor`가 실제 테스트를 수행하고 `logs/`를 남깁니다.
5. **Report:** 모든 결과를 취합하여 `outputs/`에 리포트를 생성합니다.
