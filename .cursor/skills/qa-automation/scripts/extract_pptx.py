#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPTX 기획서에서 텍스트, 표, 노트, 삽입 이미지를 추출하여 공통 스키마로 반환.
Usage: python extract_pptx.py <pptx_path> [output_path] [--reference-dir DIR]
"""

import sys
import os

# 공통 스키마: slides[].page_num, texts, tables, notes, images[]; reference_images[]
REFERENCE_DIR_DEFAULT = "outputs/reference"
CONTENT_TYPE_TO_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/bmp": "bmp"}


def extract_pptx(pptx_path, output_path=None, reference_dir=None):
    """PPTX 파일에서 내용 추출. 공통 스키마 반환."""
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        print("Error: python-pptx 라이브러리가 필요합니다.")
        print("설치: pip install python-pptx")
        sys.exit(1)

    if not os.path.exists(pptx_path):
        print(f"Error: 파일을 찾을 수 없습니다 - {pptx_path}")
        sys.exit(1)

    ref_dir = reference_dir or REFERENCE_DIR_DEFAULT
    ref_dir = os.path.normpath(ref_dir)
    if not os.path.isabs(ref_dir):
        ref_dir = os.path.join(os.getcwd(), ref_dir)
    os.makedirs(ref_dir, exist_ok=True)

    prs = Presentation(pptx_path)
    slides_out = []
    reference_images = []

    for slide_idx, slide in enumerate(prs.slides, 1):
        slide_content = {
            "page_num": slide_idx,
            "texts": [],
            "tables": [],
            "notes": "",
            "images": [],
        }

        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_content["texts"].append(shape.text.strip())

            if shape.has_table:
                table_data = []
                for row in shape.table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                slide_content["tables"].append(table_data)

            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    img = shape.image
                    ext = CONTENT_TYPE_TO_EXT.get(img.content_type, "png")
                    if not ext:
                        ext = "png"
                    rel_name = f"slide_{slide_idx}_img_{len(slide_content['images'])}.{ext}"
                    abs_path = os.path.join(ref_dir, rel_name)
                    with open(abs_path, "wb") as f:
                        f.write(img.blob)
                    rel_path = os.path.normpath(os.path.join(ref_dir, rel_name))
                    try:
                        rel_path = os.path.relpath(rel_path, os.getcwd())
                    except ValueError:
                        pass
                    rel_path = rel_path.replace("\\", "/")
                    slide_content["images"].append({"path": rel_path, "description": ""})
                    reference_images.append({"source_page": slide_idx, "path": rel_path})
                except Exception as e:
                    slide_content["images"].append({"path": "", "description": f"(추출 실패: {e})"})

        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame and notes_frame.text:
                slide_content["notes"] = notes_frame.text.strip()

        slides_out.append(slide_content)

    result = {"slides": slides_out, "reference_images": reference_images}

    # 기존 stdout 출력 유지
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
        print("Usage: python extract_pptx.py <pptx_path> [output_path] [--reference-dir DIR]")
        print("Example: python extract_pptx.py inputs/quiz.pptx")
        sys.exit(1)

    pptx_path = sys.argv[1]
    output_path = None
    reference_dir = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--reference-dir" and i + 1 < len(args):
            reference_dir = args[i + 1]
            i += 2
            continue
        if not args[i].startswith("-"):
            output_path = args[i]
        i += 1

    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    extract_pptx(pptx_path, output_path, reference_dir)


if __name__ == "__main__":
    main()
