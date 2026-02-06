#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_plan.json 파일의 유효성을 검사
Usage: python validate_json.py <json_path>
"""

import sys
import json
import os


def validate_test_plan(json_path):
    """test_plan.json 유효성 검사"""
    
    if not os.path.exists(json_path):
        print(f"Error: 파일을 찾을 수 없습니다 - {json_path}")
        return False
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: JSON 파싱 실패 - {e}")
        return False
    
    errors = []
    warnings = []
    
    # 필수 필드 확인
    if 'test_plan_id' not in data:
        errors.append("필수 필드 누락: test_plan_id")
    
    if 'test_cases' not in data:
        errors.append("필수 필드 누락: test_cases")
    elif not isinstance(data['test_cases'], list):
        errors.append("test_cases는 배열이어야 합니다")
    elif len(data['test_cases']) == 0:
        warnings.append("test_cases가 비어있습니다")
    else:
        # 테스트 케이스 검증
        valid_actions = ['navigate', 'click', 'input', 'check', 'wait', 'screenshot', 'hover', 'check_attribute', 'compare_with_reference']

        for i, tc in enumerate(data['test_cases']):
            tc_id = tc.get('tc_id', f'index_{i}')
            
            if 'tc_id' not in tc:
                errors.append(f"테스트 케이스 {i}: tc_id 누락")
            
            if 'actions' not in tc:
                errors.append(f"{tc_id}: actions 누락")
            elif not isinstance(tc['actions'], list):
                errors.append(f"{tc_id}: actions는 배열이어야 합니다")
            else:
                for j, action in enumerate(tc['actions']):
                    if 'action' not in action:
                        errors.append(f"{tc_id}.actions[{j}]: action 타입 누락")
                    elif action['action'] not in valid_actions:
                        warnings.append(f"{tc_id}.actions[{j}]: 알 수 없는 액션 '{action['action']}'")
                    
                    # 액션별 필수 파라미터 확인
                    action_type = action.get('action')
                    if action_type == 'navigate' and 'url' not in action:
                        errors.append(f"{tc_id}.actions[{j}]: navigate 액션에 url 필요")
                    if action_type == 'click' and 'selector' not in action:
                        warnings.append(f"{tc_id}.actions[{j}]: click 액션에 selector 권장")
                    if action_type == 'input' and ('selector' not in action or 'value' not in action):
                        errors.append(f"{tc_id}.actions[{j}]: input 액션에 selector, value 필요")
                    if action_type == 'compare_with_reference':
                        if 'reference' not in action and 'reference_path' not in action:
                            warnings.append(f"{tc_id}.actions[{j}]: compare_with_reference에 reference 또는 reference_path 권장")
                        if 'screenshot' not in action and 'actual_path' not in action:
                            warnings.append(f"{tc_id}.actions[{j}]: compare_with_reference 시 스크린샷 경로 또는 촬영 후 경로 필요")

    # 결과 출력
    print(f"=== {os.path.basename(json_path)} 검증 결과 ===\n")
    
    if errors:
        print("❌ 오류:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print("⚠️ 경고:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ 검증 통과: 문제 없음")
    elif not errors:
        print("✅ 검증 통과 (경고 있음)")
    else:
        print("❌ 검증 실패")
    
    # 통계
    if 'test_cases' in data and isinstance(data['test_cases'], list):
        total_tc = len(data['test_cases'])
        total_actions = sum(len(tc.get('actions', [])) for tc in data['test_cases'])
        print(f"\n📊 통계:")
        print(f"  - 테스트 케이스: {total_tc}개")
        print(f"  - 총 액션: {total_actions}개")
    
    return len(errors) == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_json.py <json_path>")
        print("Example: python validate_json.py outputs/test_plan.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    # UTF-8 출력 설정
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    success = validate_test_plan(json_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
