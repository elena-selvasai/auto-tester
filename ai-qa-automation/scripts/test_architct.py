import os
import json

# 공통 AI 설정 모듈에서 model import
from ai_config import model

class TestArchitect:
    def __init__(self, md_path, schema_path):
        self.md_path = md_path
        self.schema_path = schema_path

    def load_content(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_test_plan(self):
        print(f"📋 테스트 케이스 설계 시작: {self.md_path}")
        
        scenario_content = self.load_content(self.md_path)
        schema_content = self.load_content(self.schema_path)

        # 에이전트 지시문 (시스템 프롬프트)
        prompt = f"""
        당신은 'QA 자동화 설계 전문가'입니다. 
        제시된 [비즈니스 시나리오]를 분석하여 실제 자동화 테스트가 가능한 [JSON 테스트 플랜]으로 변환하세요.

        [비즈니스 시나리오]
        {scenario_content}

        [JSON 스키마 규약]
        {schema_content}

        [작성 지침]
        1. 각 액션은 최소 단위(click, input, navigate, check)로 쪼개세요.
        2. 'Selector' 필드에는 해당 요소를 찾기 위한 추정되는 CSS Selector나 ID를 적으세요 (예: #login-button, .submit-pkg).
        3. 반드시 제공된 [JSON 스키마 규약]을 100% 준수해야 합니다.
        4. 출력은 JSON 코드 블록 없이 순수 JSON 데이터만 반환하세요.
        """

        response = model.generate_content(prompt)
        
        # 응답 정제 및 JSON 파싱
        try:
            raw_json = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(raw_json)
        except Exception as e:
            print(f"❌ JSON 파싱 에러: {e}")
            return None

# --- 실행부 ---
if __name__ == "__main__":
    input_md = "outputs/scenario_draft.md"
    schema_file = "protocols/schema_testplan.json"
    output_json = "outputs/test_plan.json"

    if os.path.exists(input_md):
        architect = TestArchitect(input_md, schema_file)
        test_plan = architect.generate_test_plan()
        
        if test_plan:
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(test_plan, f, indent=2, ensure_ascii=False)
            print(f"✅ 테스트 플랜 설계 완료: {output_json}")
    else:
        print(f"❌ 시나리오 파일을 찾을 수 없습니다. Step 1을 먼저 실행하세요.")