#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
시나리오 문서 단일 진입점: 확장자로 포맷 감지 후 해당 추출기 호출, 공통 스키마 JSON/마크다운 출력.
Usage: python extract_document.py <path> [--output DIR] [--reference-dir DIR]
  path: 파일 경로 또는 inputs/ 같은 디렉터리(지원 확장자 첫 파일 사용)
"""

import importlib.util
import json
import os
import sys

SUPPORTED_EXTENSIONS = {
    ".pptx": "pptx",
    ".docx": "docx",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

EXTRACTOR_ENTRY = {"pptx": "extract_pptx", "docx": "extract_docx", "pdf": "extract_pdf", "image": "extract_images"}


def detect_format(path):
    """파일 경로로 포맷 감지. 디렉터리면 지원 확장자 첫 파일 반환."""
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        return path, SUPPORTED_EXTENSIONS.get(ext)
    if os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                return os.path.join(path, name), SUPPORTED_EXTENSIONS[ext]
    return None, None


def normalize_result(data, format_type):
    """추출기별 반환값을 공통 스키마로 통일. pages[], reference_images[]."""
    if format_type == "pptx":
        pages = data.get("slides", [])
        for p in pages:
            if "slide_num" in p and "page_num" not in p:
                p["page_num"] = p["slide_num"]
        return {"pages": pages, "reference_images": data.get("reference_images", [])}
    if format_type in ("docx", "pdf", "image"):
        pages = data.get("pages", data.get("slides", []))
        return {"pages": pages, "reference_images": data.get("reference_images", [])}
    return {"pages": [], "reference_images": []}


def _load_extractor(format_type, script_dir):
    """같은 디렉터리의 추출기 모듈 로드."""
    name = EXTRACTOR_ENTRY.get(format_type)
    if not name:
        return None
    path = os.path.join(script_dir, name + ".py")
    if not os.path.exists(path):
        return None
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def extract_document(path, output_dir=None, reference_dir=None, script_dir=None):
    """문서 추출: 포맷 감지 후 해당 추출기 호출, 공통 스키마 반환."""
    file_path, format_type = detect_format(path)
    if not file_path or not format_type:
        print(f"Error: 지원하지 않는 경로 또는 포맷입니다. - {path}")
        print("지원: .pptx, .docx, .pdf, .png, .jpg, .jpeg")
        return None

    ref_dir = reference_dir or "outputs/reference"
    _script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
    mod = _load_extractor(format_type, _script_dir)
    if mod is None:
        print(f"Error: 추출기 없음 - {format_type} (파일: {EXTRACTOR_ENTRY.get(format_type, '')}.py)")
        return None

    if format_type == "image":
        fn_name = "extract_images"
    else:
        fn_name = "extract_" + format_type
    extract_fn = getattr(mod, fn_name, None)
    if not extract_fn:
        print(f"Error: 모듈에 {fn_name} 함수가 없습니다.")
        return None

    raw = extract_fn(file_path, reference_dir=ref_dir)
    if raw is None:
        return None
    result = normalize_result(raw, format_type)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "extract_result.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[저장] {json_path}")

        md_path = os.path.join(output_dir, "scenario_draft_source.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# 시나리오 문서 추출 요약\n\n")
            f.write(f"소스: {os.path.basename(file_path)}\n\n")
            for p in result["pages"]:
                f.write(f"## 페이지 {p.get('page_num', '?')}\n\n")
                for t in p.get("texts", []):
                    f.write(t + "\n\n")
                for table in p.get("tables", []):
                    for row in table:
                        f.write(" | ".join(row) + "\n")
                    f.write("\n")
                if p.get("notes"):
                    f.write(f"*노트*: {p['notes']}\n\n")
            f.write("## 구성 체크 리스트 (기획서 기준 표시 요소)\n\n")
            f.write("테스트 시 해당 페이지/화면에서 아래 요소 존재 여부를 확인할 수 있습니다.\n\n")
            for p in result["pages"]:
                texts = p.get("texts", [])[:15]
                if not texts:
                    continue
                f.write(f"### 페이지 {p.get('page_num', '?')} 예상 요소\n")
                for t in texts:
                    if len(t.strip()) > 2:
                        f.write(f"- {t.strip()}\n")
                f.write("\n")
        print(f"[저장] {md_path}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_document.py <path> [--output DIR] [--reference-dir DIR]")
        print("Example: python extract_document.py inputs/")
        print("         python extract_document.py inputs/quiz.pptx --output outputs")
        sys.exit(1)

    path = sys.argv[1]
    output_dir = None
    reference_dir = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 2
            continue
        if args[i] == "--reference-dir" and i + 1 < len(args):
            reference_dir = args[i + 1]
            i += 2
            continue
        i += 1

    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    script_dir = os.path.dirname(os.path.abspath(__file__))
    result = extract_document(
        path, output_dir=output_dir or "outputs", reference_dir=reference_dir, script_dir=script_dir
    )
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
