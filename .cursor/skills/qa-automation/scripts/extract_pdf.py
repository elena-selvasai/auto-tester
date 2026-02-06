#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 기획서에서 텍스트, 이미지를 추출하여 공통 스키마로 반환. 페이지별 이미지 렌더 저장 지원.
Usage: python extract_pdf.py <pdf_path> [--reference-dir DIR]
"""

import os
import sys


def extract_pdf(pdf_path, output_path=None, reference_dir=None):
    """PDF 파일에서 내용 추출. 공통 스키마 반환."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Error: PyMuPDF 라이브러리가 필요합니다.")
        print("설치: pip install PyMuPDF")
        return None

    if not os.path.exists(pdf_path):
        print(f"Error: 파일을 찾을 수 없습니다 - {pdf_path}")
        return None

    ref_dir = reference_dir or "outputs/reference"
    ref_dir = os.path.normpath(ref_dir)
    if not os.path.isabs(ref_dir):
        ref_dir = os.path.join(os.getcwd(), ref_dir)
    os.makedirs(ref_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    pages_out = []
    reference_images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        texts = []
        for block in page.get_text("blocks"):
            if block[4].strip():
                texts.append(block[4].strip())
        tables = []
        images = []

        for img_info in page.get_images():
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                data = base["image"]
                ext = base["ext"]
                if ext == "jpeg":
                    ext = "jpg"
                rel_name = f"pdf_page_{page_num + 1}_img_{len(images)}.{ext}"
                abs_path = os.path.join(ref_dir, rel_name)
                with open(abs_path, "wb") as f:
                    f.write(data)
                try:
                    rel_path = os.path.relpath(abs_path, os.getcwd()).replace("\\", "/")
                except ValueError:
                    rel_path = os.path.join("outputs", "reference", rel_name).replace("\\", "/")
                images.append({"path": rel_path, "description": ""})
                reference_images.append({"source_page": page_num + 1, "path": rel_path})
            except Exception:
                pass

        # 페이지 전체를 이미지로 렌더(참조용)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        render_name = f"pdf_page_{page_num + 1}.png"
        render_path = os.path.join(ref_dir, render_name)
        pix.save(render_path)
        try:
            render_rel = os.path.relpath(render_path, os.getcwd()).replace("\\", "/")
        except ValueError:
            render_rel = os.path.join("outputs", "reference", render_name).replace("\\", "/")
        reference_images.append({"source_page": page_num + 1, "path": render_rel})

        pages_out.append({
            "page_num": page_num + 1,
            "texts": texts,
            "tables": tables,
            "notes": "",
            "images": images,
        })

    doc.close()

    result = {"pages": pages_out, "reference_images": reference_images}

    print(f"=== {os.path.basename(pdf_path)} 분석 결과 ===\n")
    for p in pages_out:
        print(f"--- 페이지 {p['page_num']} ---")
        for t in p["texts"]:
            print(t)
        for im in p.get("images", []):
            if im.get("path"):
                print(f"  [이미지] {im['path']}")
        print()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf.py <pdf_path> [--reference-dir DIR]")
        sys.exit(1)
    path = sys.argv[1]
    ref_dir = None
    for i, a in enumerate(sys.argv[2:], 2):
        if a == "--reference-dir" and i < len(sys.argv) - 1:
            ref_dir = sys.argv[i]
            break
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    r = extract_pdf(path, reference_dir=ref_dir)
    sys.exit(0 if r is not None else 1)


if __name__ == "__main__":
    main()
