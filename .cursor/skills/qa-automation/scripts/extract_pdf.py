#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 기획서에서 텍스트, 이미지를 추출하여 공통 스키마로 반환. 페이지별 이미지 렌더 저장 지원.
Usage: python extract_pdf.py <pdf_path> [--reference-dir DIR]
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor

from _utils import parse_reference_dir, resolve_ref_dir, setup_stdout_utf8, to_rel_path

DEFAULT_WORKERS = 4


def _process_pdf_page_batch(pdf_path, page_nums, ref_dir):
    """스레드 워커: 별도 fitz.Document에서 페이지 배치를 처리합니다."""
    import fitz

    doc = fitz.open(pdf_path)
    pages_out = []
    reference_images = []

    for page_num in page_nums:
        page = doc[page_num]
        texts = []
        for block in page.get_text("blocks"):
            if block[4].strip():
                texts.append(block[4].strip())

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
                rel_path = to_rel_path(abs_path, os.path.join("outputs", "reference", rel_name))
                images.append({"path": rel_path, "description": ""})
                reference_images.append({"source_page": page_num + 1, "path": rel_path})
            except Exception:
                pass

        # 페이지 전체를 이미지로 렌더(참조용)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        render_name = f"pdf_page_{page_num + 1}.png"
        render_path = os.path.join(ref_dir, render_name)
        pix.save(render_path)
        render_rel = to_rel_path(render_path, os.path.join("outputs", "reference", render_name))
        reference_images.append({"source_page": page_num + 1, "path": render_rel})

        pages_out.append({
            "page_num": page_num + 1,
            "texts": texts,
            "tables": [],
            "notes": "",
            "images": images,
        })

        print(f"  [페이지 {page_num + 1}] 텍스트 {len(texts)}건, 이미지 {len(images)}건", flush=True)

    doc.close()
    return pages_out, reference_images


def extract_pdf(pdf_path, reference_dir=None, workers=DEFAULT_WORKERS):
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

    ref_dir = resolve_ref_dir(reference_dir)

    # 페이지 수 확인 후 즉시 닫기 (스레드별로 별도 open)
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    if total_pages == 0:
        return {"pages": [], "reference_images": []}

    actual_workers = min(workers, total_pages)

    if actual_workers <= 1:
        pages_out, reference_images = _process_pdf_page_batch(
            pdf_path, list(range(total_pages)), ref_dir
        )
    else:
        # 페이지를 N개 배치로 분배
        batches = [[] for _ in range(actual_workers)]
        for i in range(total_pages):
            batches[i % actual_workers].append(i)

        print(f"=== PDF 병렬 추출: {actual_workers} workers, {total_pages} 페이지 ===")

        pages_out = []
        reference_images = []

        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = [
                executor.submit(_process_pdf_page_batch, pdf_path, batch, ref_dir)
                for batch in batches if batch
            ]
            for future in futures:
                batch_pages, batch_refs = future.result()
                pages_out.extend(batch_pages)
                reference_images.extend(batch_refs)

    # 페이지 번호순 정렬
    pages_out.sort(key=lambda p: p["page_num"])
    reference_images.sort(key=lambda r: (r["source_page"], r["path"]))

    result = {"pages": pages_out, "reference_images": reference_images}

    print(f"\n=== {os.path.basename(pdf_path)} 분석 결과 ===\n")
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

    setup_stdout_utf8()
    r = extract_pdf(sys.argv[1], reference_dir=parse_reference_dir(sys.argv))
    sys.exit(0 if r is not None else 1)


if __name__ == "__main__":
    main()
