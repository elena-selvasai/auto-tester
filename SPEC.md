# 서비스명: AI QA 자동화 에이전트

## 목표
입력된 pptx 시나리오를 바탕으로 웹 자동화 테스트를 수행하고 결과를 리포팅한다.

## 단계별 수행 가이드 (Antigravity Task)

### Phase 1: 문서 분석 및 환경 구축
1. `inputs/` 폴더 내의 `.pptx` 파일을 읽어 `scenario.md`로 변환한다.
   - 필요 시 `python-pptx` 및 `VLM` 라이브러리를 사용하는 Python 스크립트를 작성 및 실행한다.
2. 분석된 시나리오에서 테스트 케이스(TC)를 추출하여 `test_cases.json`으로 저장한다.

### Phase 2: 테스트 실행 환경 준비
1. 테스트 대상 URL 및 실행 방법(예: 로그인 정보)을 확인한다.
2. `playwright` 또는 `puppeteer` 환경이 구축되어 있는지 확인하고, 필요 라이브러리를 설치한다.

### Phase 3: 테스트 실행 (Antigravity Browser 사용)
1. `test_cases.json`의 각 단계를 Antigravity의 브라우저 툴을 사용하여 순차 실행한다.
2. 각 단계별로 성공 여부를 체크하고, 실패 시 스크린샷을 `logs/`에 저장한다.
3. 실패 상황 발생 시, 에이전트는 스스로 원인을 분석하고 'Self-healing'을 시도한다.

### Phase 4: 결과 요약 및 보고서 생성
1. 모든 테스트 결과를 취합하여 `REPORT_YYYYMMDD.md` 파일을 생성한다.
2. 발견된 버그나 UI/UX 개선 제안 사항을 포함한다.