#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPTX 기획서에서 텍스트·표(markitdown), 노트·이미지(python-pptx)를 추출하여 공통 스키마로 반환.
Usage: python extract_pptx.py <pptx_path> [--reference-dir DIR]
"""

import os
import re
import sys

from _utils import parse_reference_dir, resolve_ref_dir, setup_stdout_utf8, to_rel_path

CONTENT_TYPE_TO_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/bmp": "bmp"}


def _parse_markitdown_slides(md_text):
    """markitdown PPTX 출력을 슬라이드 번호 → markdown 내용으로 분리."""
    slides = {}
    current_slide = None
    current_lines = []

    for line in md_text.splitlines():
        m = re.match(r"<!--\s*Slide number:\s*(\d+)\s*-->", line)
        if m:
            if current_slide is not None:
                slides[current_slide] = "\n".join(current_lines).strip()
            current_slide = int(m.group(1))
            current_lines = []
        elif current_slide is not None:
            current_lines.append(line)

    if current_slide is not None:
        slides[current_slide] = "\n".join(current_lines).strip()

    return slides


def _extract_texts_and_tables(md_content):
    """슬라이드 markdown에서 텍스트 목록과 표(2차원 배열) 목록을 추출."""
    lines = md_content.splitlines()
    texts = []
    tables = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            # 표 블록 수집
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = []
            for tl in table_lines:
                if re.match(r"\s*\|[-|\s:]+\|\s*$", tl):
                    continue  # 구분선 제거
                cells = [c.strip() for c in tl.strip().strip("|").split("|")]
                rows.append(cells)
            if rows:
                tables.append(rows)
        else:
            # 마크다운 마커 제거 후 텍스트 수집
            text = re.sub(r"^#+\s*", "", line).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            if text and text != "---":
                texts.append(text)
            i += 1

    return texts, tables


def extract_pptx(pptx_path, reference_dir=None):
    """PPTX 파일에서 내용 추출. 공통 스키마 반환."""
    try:
        from markitdown import MarkItDown
    except ImportError:
        print("Error: markitdown 라이브러리가 필요합니다.")
        print("설치: pip install markitdown")
        return None
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        print("Error: python-pptx 라이브러리가 필요합니다.")
        print("설치: pip install python-pptx")
        return None

    if not os.path.exists(pptx_path):
        print(f"Error: 파일을 찾을 수 없습니다 - {pptx_path}")
        return None

    ref_dir = resolve_ref_dir(reference_dir)

    # markitdown으로 텍스트·표 추출 후 슬라이드별 분리
    md_result = MarkItDown().convert(pptx_path)
    slide_md_map = _parse_markitdown_slides(md_result.text_content)

    # python-pptx로 이미지·노트 추출
    prs = Presentation(pptx_path)
    slides_out = []
    reference_images = []

    for slide_idx, slide in enumerate(prs.slides, 1):
        texts, tables = _extract_texts_and_tables(slide_md_map.get(slide_idx, ""))

        images = []
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    img = shape.image
                    ext = CONTENT_TYPE_TO_EXT.get(img.content_type, "png") or "png"
                    rel_name = f"slide_{slide_idx}_img_{len(images)}.{ext}"
                    abs_path = os.path.join(ref_dir, rel_name)
                    with open(abs_path, "wb") as f:
                        f.write(img.blob)
                    rel_path = to_rel_path(abs_path, os.path.join("outputs", "reference", rel_name))
                    images.append({"path": rel_path, "description": ""})
                    reference_images.append({"source_page": slide_idx, "path": rel_path})
                except Exception as e:
                    images.append({"path": "", "description": f"(추출 실패: {e})"})

        notes = ""
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame and notes_frame.text:
                notes = notes_frame.text.strip()

        slides_out.append({
            "page_num": slide_idx,
            "texts": texts,
            "tables": tables,
            "notes": notes,
            "images": images,
        })

    result = {"slides": slides_out, "reference_images": reference_images}

    print(f"=== {os.path.basename(pptx_path)} 분석 결과 ===\n")
    for slide in slides_out:
        print(f"--- Slide {slide['page_num']} ---")
        for text in slide["texts"]:
            print(text)
        if slide["tables"]:
            print("\n[표 데이터]")
            for table in slide["tables"]:
                for row in table:
                    print(" | ".join(row))
                print()
        if slide["notes"]:
            print(f"\n[노트] {slide['notes']}")
        if slide["images"]:
            print("\n[삽입 이미지]")
            for im in slide["images"]:
                if im["path"]:
                    print(f"  - {im['path']}")
        print()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pptx.py <pptx_path> [--reference-dir DIR]")
        print("Example: python extract_pptx.py inputs/quiz.pptx")
        sys.exit(1)

    setup_stdout_utf8()
    r = extract_pptx(sys.argv[1], reference_dir=parse_reference_dir(sys.argv))
    sys.exit(0 if r is not None else 1)


if __name__ == "__main__":
    main()
