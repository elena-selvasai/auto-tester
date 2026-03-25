"""
카테고리별 분할 JSON → 단일 test_plan.json 병합 스크립트.

5개 병렬 Task가 생성한 카테고리별 JSON 파일을 하나의 test_plan.json으로 병합한다.
스켈레톤의 root precondition을 유지하고, test_cases를 TC 번호순으로 정렬한다.

파일 형식:
  - outputs/test_plan_basic_function.json
  - outputs/test_plan_button_state.json
  - outputs/test_plan_navigation.json
  - outputs/test_plan_edge_case.json
  - outputs/test_plan_accessibility.json

각 파일은 { "test_cases": [...] } 또는 전체 test_plan 구조를 포함할 수 있다.

Usage:
    python scripts/merge_test_plans.py [--output-dir outputs] [--skeleton outputs/test_plan_skeleton.json]
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
    def _load_test_url_from_state(output_dir: str) -> str:
        state_path = os.path.join(output_dir, "qa_state.yaml")
        if os.path.exists(state_path):
            with open(state_path, encoding="utf-8") as f:
                state = yaml.safe_load(f)
            return state.get("config", {}).get("test_url") or ""
        return ""
except ImportError:
    def _load_test_url_from_state(output_dir: str) -> str:
        return ""


CATEGORIES = [
    "basic_function",
    "button_state",
    "navigation",
    "edge_case",
    "accessibility",
]


def tc_sort_key(tc: dict) -> int:
    """TC_001 → 1, TC_051 → 51 등 숫자 추출."""
    tc_id = tc.get("tc_id", "TC_999")
    m = re.search(r"(\d+)", tc_id)
    return int(m.group(1)) if m else 999


def load_category_file(output_dir: str, category: str) -> list[dict]:
    """카테고리별 JSON 파일에서 test_cases를 추출."""
    path = os.path.join(output_dir, f"test_plan_{category}.json")
    if not os.path.exists(path):
        print(f"[WARN] {path} not found, skipping", file=sys.stderr)
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if "test_cases" in data:
        return data["test_cases"]
    return []


def load_skeleton(skeleton_path: str) -> dict:
    """스켈레톤 JSON에서 root 구조(precondition 등)를 로드."""
    if not os.path.exists(skeleton_path):
        return {
            "test_plan_id": "TP_001",
            "base_url": "${base_url}",
            "precondition": None,
        }

    with open(skeleton_path, encoding="utf-8") as f:
        data = json.load(f)

    return {
        "test_plan_id": data.get("test_plan_id", "TP_001"),
        "base_url": data.get("base_url", "${base_url}"),
        "precondition": data.get("precondition"),
    }


def validate_merged(test_cases: list[dict]) -> list[str]:
    """병합된 TC 목록의 기본 검증."""
    errors = []
    seen_ids = set()
    for tc in test_cases:
        tc_id = tc.get("tc_id", "")
        if not tc_id:
            errors.append("tc_id가 비어있는 TC 발견")
        elif tc_id in seen_ids:
            errors.append(f"중복 tc_id: {tc_id}")
        seen_ids.add(tc_id)

        if not tc.get("actions"):
            errors.append(f"{tc_id}: actions가 비어있음")
        if not tc.get("category"):
            errors.append(f"{tc_id}: category 미지정")

    return errors


def strip_ai_hints(obj):
    """_ai_hint 키를 재귀적으로 제거 (최종 test_plan에는 불필요)."""
    if isinstance(obj, dict):
        return {k: strip_ai_hints(v) for k, v in obj.items() if k != "_ai_hint"}
    if isinstance(obj, list):
        return [strip_ai_hints(item) for item in obj]
    return obj


def main():
    parser = argparse.ArgumentParser(description="카테고리별 JSON → test_plan.json 병합")
    parser.add_argument("--output-dir", default="outputs", help="산출물 디렉토리 (기본: outputs)")
    parser.add_argument("--skeleton", default=None, help="스켈레톤 파일 경로 (기본: {output-dir}/test_plan_skeleton.json)")
    parser.add_argument("--keep-hints", action="store_true", help="_ai_hint 키 유지")
    args = parser.parse_args()

    skeleton_path = args.skeleton or os.path.join(args.output_dir, "test_plan_skeleton.json")
    base = load_skeleton(skeleton_path)

    all_cases = []
    for cat in CATEGORIES:
        cases = load_category_file(args.output_dir, cat)
        print(f"  {cat}: {len(cases)} TCs loaded")
        all_cases.extend(cases)

    all_cases.sort(key=tc_sort_key)

    errors = validate_merged(all_cases)
    if errors:
        print(f"\n[WARN] 검증 경고 {len(errors)}건:", file=sys.stderr)
        for err in errors[:10]:
            print(f"  - {err}", file=sys.stderr)

    test_url = _load_test_url_from_state(args.output_dir)
    merged = {
        "test_plan_id": base["test_plan_id"],
        "test_url": test_url,
        "base_url": test_url if test_url else base["base_url"],
    }
    if base.get("precondition"):
        merged["precondition"] = base["precondition"]
    merged["test_cases"] = all_cases

    if not args.keep_hints:
        merged = strip_ai_hints(merged)

    out_path = os.path.join(args.output_dir, "test_plan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {out_path} generated ({len(all_cases)} TCs)")
    cat_counts = {}
    for tc in all_cases:
        cat = tc.get("category", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    for cat in CATEGORIES:
        print(f"  {cat}: {cat_counts.get(cat, 0)} TCs")


if __name__ == "__main__":
    main()
