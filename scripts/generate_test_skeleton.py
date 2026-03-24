"""
test_plan_skeleton.json 자동 생성 스크립트.

extract_result.json + reference 이미지 + 구성 체크리스트(scenario_draft_source.md)를 분석하여
AI가 보완할 기초 구조인 test_plan_skeleton.json을 생성한다.

Usage:
    python scripts/generate_test_skeleton.py [--output-dir outputs]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


CATEGORY_RANGES = {
    "basic_function": (1, 50),
    "button_state": (51, 100),
    "navigation": (101, 150),
    "edge_case": (151, 180),
    "accessibility": (181, 200),
}


def load_extract_result(output_dir: str) -> dict:
    path = os.path.join(output_dir, "extract_result.json")
    if not os.path.exists(path):
        print(f"[ERROR] {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_checklist(output_dir: str) -> dict[int, list[str]]:
    """scenario_draft_source.md의 '구성 체크 리스트' 섹션을 파싱하여 페이지별 요소 목록 반환."""
    path = os.path.join(output_dir, "scenario_draft_source.md")
    if not os.path.exists(path):
        return {}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    checklist_section = ""
    match = re.search(r"## 구성 체크 리스트.*?\n", content)
    if match:
        checklist_section = content[match.end():]

    result: dict[int, list[str]] = {}
    current_page = None
    for line in checklist_section.split("\n"):
        page_match = re.match(r"### 페이지 (\d+)", line)
        if page_match:
            current_page = int(page_match.group(1))
            result[current_page] = []
            continue
        if current_page is not None and line.startswith("- "):
            item = line[2:].strip()
            if item and not item.startswith("!["):
                result[current_page].append(item)
    return result


def collect_reference_images(output_dir: str) -> dict[int, list[str]]:
    """reference/ 폴더의 이미지를 슬라이드 번호별로 그룹화."""
    ref_dir = os.path.join(output_dir, "reference")
    if not os.path.isdir(ref_dir):
        return {}

    images: dict[int, list[str]] = {}
    for fname in sorted(os.listdir(ref_dir)):
        if not fname.endswith(".png"):
            continue
        m = re.match(r"slide_(\d+)_img_(\d+)\.png", fname)
        if m:
            slide_num = int(m.group(1))
            img_path = os.path.join(output_dir, "reference", fname)
            images.setdefault(slide_num, []).append(img_path)
    return images


def extract_ui_descriptions(page: dict) -> list[dict]:
    """페이지의 tables에서 UI Description 테이블을 파싱."""
    descriptions = []
    for table in page.get("tables", []):
        if not table:
            continue
        header = table[0] if table else []
        has_no = any("No" in str(cell) for cell in header)
        has_desc = any("Description" in str(cell) or "description" in str(cell) for cell in header)
        if has_no and has_desc:
            for row in table[1:]:
                if len(row) >= 2:
                    no = str(row[0]).strip()
                    desc = str(row[1]).strip()
                    if desc:
                        descriptions.append({"no": no, "description": desc})
    return descriptions


def extract_page_id(page: dict) -> str:
    """페이지의 tables에서 Page ID를 추출."""
    for table in page.get("tables", []):
        for row in table:
            if len(row) >= 2 and "Page ID" in str(row[0]):
                return str(row[1]).strip().replace("\\_", "_")
    for text in page.get("texts", []):
        m = re.search(r"NRV\.[A-Z]\.\d+\.\d+(?:\.\d+(?:_\d+)?)?", text)
        if m:
            return m.group(0)
    return ""


def generate_skeleton(output_dir: str) -> dict:
    data = load_extract_result(output_dir)
    checklist = load_checklist(output_dir)
    ref_images = collect_reference_images(output_dir)

    pages = data.get("pages", [])
    tc_counters = {cat: start for cat, (start, _) in CATEGORY_RANGES.items()}

    skeleton = {
        "test_plan_id": "TP_001",
        "base_url": "${base_url}",
        "precondition": {
            "description": "TODO: 테스트 공통 선행 조건 (AI가 실제 DOM 기반으로 보완)",
            "actions": [
                {"action": "navigate", "url": "${base_url}"},
                {"action": "wait_for_selector", "selector": "body", "state": "visible", "timeout": 5000},
            ],
            "success_checks": [
                {"action": "check", "selector": "body", "visible": True},
            ],
        },
        "test_cases": [],
    }

    for page in pages:
        page_num = page["page_num"]
        page_id = extract_page_id(page)
        ui_descs = extract_ui_descriptions(page)
        page_images = ref_images.get(page_num, [])
        page_checklist = checklist.get(page_num, [])

        if not ui_descs and not page_images and not page_checklist:
            continue

        page_label = page_id if page_id else f"page_{page_num}"

        for desc_item in ui_descs:
            no = desc_item["no"]
            description = desc_item["description"]

            tc_num = tc_counters["basic_function"]
            if tc_num > CATEGORY_RANGES["basic_function"][1]:
                break
            tc_counters["basic_function"] = tc_num + 1

            tc_id = f"TC_{tc_num:03d}"
            short_desc = description[:60].replace("\n", " ")
            tc_name = f"[{page_label}] {short_desc}"

            actions = []
            actions.append({
                "action": "screenshot",
                "filename": f"outputs/screenshot_{tc_id}_{page_label}.png",
            })

            if page_images:
                actions.append({
                    "action": "compare_with_reference",
                    "reference": page_images[0],
                    "screenshot": f"outputs/screenshot_{tc_id}_{page_label}.png",
                    "threshold": 40,
                })

            actions.append({
                "action": "check",
                "selector": f"TODO_SELECTOR_FOR_{page_label}_{no}",
                "visible": True,
                "_ai_hint": f"UI Description #{no}: {description[:120]}",
            })

            skeleton["test_cases"].append({
                "tc_id": tc_id,
                "name": tc_name,
                "category": "basic_function",
                "priority": "high",
                "actions": actions,
            })

        for desc_item in ui_descs:
            description = desc_item["description"]
            has_button_keyword = any(kw in description for kw in [
                "버튼", "클릭", "활성", "비활성", "disabled", "토글", "선택",
            ])
            if not has_button_keyword:
                continue

            tc_num = tc_counters["button_state"]
            if tc_num > CATEGORY_RANGES["button_state"][1]:
                break
            tc_counters["button_state"] = tc_num + 1

            tc_id = f"TC_{tc_num:03d}"
            short_desc = description[:60].replace("\n", " ")
            skeleton["test_cases"].append({
                "tc_id": tc_id,
                "name": f"[{page_label}] 버튼 상태: {short_desc}",
                "category": "button_state",
                "priority": "medium",
                "actions": [
                    {
                        "action": "check",
                        "selector": "TODO_SELECTOR",
                        "visible": True,
                        "_ai_hint": f"버튼 상태 검증 필요: {description[:120]}",
                    },
                    {
                        "action": "screenshot",
                        "filename": f"outputs/screenshot_{tc_id}_{page_label}.png",
                    },
                ],
            })

        for check_item in page_checklist[:3]:
            tc_num = tc_counters["navigation"]
            if tc_num > CATEGORY_RANGES["navigation"][1]:
                break
            tc_counters["navigation"] = tc_num + 1

            tc_id = f"TC_{tc_num:03d}"
            skeleton["test_cases"].append({
                "tc_id": tc_id,
                "name": f"[{page_label}] 구성요소 확인: {check_item[:40]}",
                "category": "navigation",
                "priority": "low",
                "actions": [
                    {
                        "action": "check",
                        "selector": f"TODO_SELECTOR",
                        "expected": check_item,
                        "_ai_hint": f"구성 체크리스트 항목: {check_item}",
                    },
                ],
            })

    edge_tc_num = tc_counters["edge_case"]
    edge_placeholders = [
        "경계값 입력 테스트 (최대 글자수 초과)",
        "빈 입력값 제출 시 유효성 검증",
        "비속어 필터링 동작 확인",
    ]
    for placeholder in edge_placeholders:
        if edge_tc_num > CATEGORY_RANGES["edge_case"][1]:
            break
        tc_id = f"TC_{edge_tc_num:03d}"
        skeleton["test_cases"].append({
            "tc_id": tc_id,
            "name": f"[edge_case] {placeholder}",
            "category": "edge_case",
            "priority": "high",
            "actions": [
                {"action": "check", "selector": "TODO_SELECTOR", "visible": True,
                 "_ai_hint": f"AI가 실제 DOM 기반으로 완전한 시나리오 작성 필요: {placeholder}"},
            ],
        })
        edge_tc_num += 1
    tc_counters["edge_case"] = edge_tc_num

    a11y_tc_num = tc_counters["accessibility"]
    a11y_placeholders = [
        "아이콘 aria-label 접근성 확인",
        "입력 필드 placeholder/label 접근성 확인",
    ]
    for placeholder in a11y_placeholders:
        if a11y_tc_num > CATEGORY_RANGES["accessibility"][1]:
            break
        tc_id = f"TC_{a11y_tc_num:03d}"
        skeleton["test_cases"].append({
            "tc_id": tc_id,
            "name": f"[accessibility] {placeholder}",
            "category": "accessibility",
            "priority": "low",
            "actions": [
                {"action": "evaluate",
                 "expression": "TODO: AI가 접근성 검사 expression 작성",
                 "_ai_hint": placeholder},
            ],
        })
        a11y_tc_num += 1
    tc_counters["accessibility"] = a11y_tc_num

    return skeleton


def main():
    parser = argparse.ArgumentParser(description="test_plan_skeleton.json 자동 생성")
    parser.add_argument("--output-dir", default="outputs", help="산출물 디렉토리 (기본: outputs)")
    args = parser.parse_args()

    skeleton = generate_skeleton(args.output_dir)

    out_path = os.path.join(args.output_dir, "test_plan_skeleton.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(skeleton, f, ensure_ascii=False, indent=2)

    tc_count = len(skeleton["test_cases"])
    category_counts = {}
    for tc in skeleton["test_cases"]:
        cat = tc["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"[OK] {out_path} generated ({tc_count} TCs)")
    for cat, count in sorted(category_counts.items()):
        r = CATEGORY_RANGES[cat]
        print(f"  {cat}: {count} TCs (TC_{r[0]:03d}~TC_{r[1]:03d})")


if __name__ == "__main__":
    main()
