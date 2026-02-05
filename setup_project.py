import os
import json

def create_qa_automation_env():
    # 1. 기본 폴더 구조 정의
    base_dir = "ai-qa-automation"
    folders = [
        "agents",
        "protocols",
        "inputs",
        "outputs",
        "scripts",
        "logs/screenshots",
    ]

    print(f"📂 '{base_dir}' 프로젝트 생성 시작...")

    for folder in folders:
        path = os.path.join(base_dir, folder)
        os.makedirs(path, exist_ok=True)
        print(f"  - 폴더 생성 완료: {path}")

    # 2. 에이전트 스펙 파일 (.md) 정의
    agents = {
        "agent_master.md": "# Master Orchestrator\n전체 워크플로우를 관리하고 서브 에이전트들의 결과물을 검수합니다.",
        "agent_doc_analyst.md": "# DocAnalyst Spec\nPPTX 시나리오를 분석하여 비즈니스 로직(MD)을 추출합니다.",
        "agent_test_architect.md": "# TestArchitect Spec\n분석된 MD를 바탕으로 JSON 형식의 테스트 케이스를 설계합니다.",
        "agent_qa_executor.md": "# QAExecutor Spec\nPlaywright를 사용하여 실제 웹 테스트를 수행하고 결과를 기록합니다."
    }

    for name, content in agents.items():
        with open(os.path.join(base_dir, "agents", name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  - 에이전트 파일 생성: {name}")

    # 3. 데이터 교환 규약 (JSON Schema) 정의
    schemas = {
        "schema_scenario.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ScenarioSchema",
            "type": "object",
            "properties": {
                "scenario_id": {"type": "string"},
                "features": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "steps": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            },
            "required": ["scenario_id", "features"]
        },
        "schema_testplan.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "TestPlanSchema",
            "type": "object",
            "properties": {
                "test_plan_id": {"type": "string"},
                "test_cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tc_id": {"type": "string"},
                            "actions": {"type": "array"}
                        }
                    }
                }
            },
            "required": ["test_plan_id", "test_cases"]
        }
    }

    for name, content in schemas.items():
        with open(os.path.join(base_dir, "protocols", name), "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"  - 스키마 파일 생성: {name}")

    # 4. 마스터 워크플로우 가이드 생성
    workflow_guide = """# Project Workflow Guide
1. **Input:** `inputs/` 폴더에 시나리오 PPTX를 넣습니다.
2. **Analysis:** `DocAnalyst`가 `scenario_draft.md`를 생성합니다.
3. **Planning:** `TestArchitect`가 `test_plan.json`을 생성합니다.
4. **Execution:** `QAExecutor`가 실제 테스트를 수행하고 `logs/`를 남깁니다.
5. **Report:** 모든 결과를 취합하여 `outputs/`에 리포트를 생성합니다.
"""
    with open(os.path.join(base_dir, "Master_Flow.md"), "w", encoding="utf-8") as f:
        f.write(workflow_guide)

    print("\n✨ 모든 프로젝트 구조와 문서화가 완료되었습니다!")
    print(f"이제 '{base_dir}' 폴더로 이동하여 작업을 시작하세요.")

if __name__ == "__main__":
    create_qa_automation_env()