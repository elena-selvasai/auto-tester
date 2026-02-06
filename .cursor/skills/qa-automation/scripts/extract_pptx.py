#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPTX 기획서에서 텍스트, 표, 노트를 추출하여 테스트 시나리오로 변환
Usage: python extract_pptx.py <pptx_path> [output_path]
"""

import sys
import os

def extract_pptx(pptx_path, output_path=None):
    """PPTX 파일에서 내용 추출"""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError:
        print("Error: python-pptx 라이브러리가 필요합니다.")
        print("설치: pip install python-pptx")
        sys.exit(1)
    
    if not os.path.exists(pptx_path):
        print(f"Error: 파일을 찾을 수 없습니다 - {pptx_path}")
        sys.exit(1)
    
    prs = Presentation(pptx_path)
    content = []
    
    for i, slide in enumerate(prs.slides, 1):
        slide_content = {
            'slide_num': i,
            'texts': [],
            'tables': [],
            'notes': ''
        }
        
        # 텍스트 추출
        for shape in slide.shapes:
            if hasattr(shape, 'text') and shape.text.strip():
                slide_content['texts'].append(shape.text.strip())
            
            # 표 추출
            if shape.has_table:
                table_data = []
                for row in shape.table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                slide_content['tables'].append(table_data)
        
        # 노트 추출
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame and notes_frame.text:
                slide_content['notes'] = notes_frame.text.strip()
        
        content.append(slide_content)
    
    # 결과 출력
    print(f"=== {os.path.basename(pptx_path)} 분석 결과 ===\n")
    
    for slide in content:
        print(f"--- Slide {slide['slide_num']} ---")
        
        for text in slide['texts']:
            print(text)
        
        if slide['tables']:
            print("\n[표 데이터]")
            for table in slide['tables']:
                for row in table:
                    print(" | ".join(row))
                print()
        
        if slide['notes']:
            print(f"\n[노트] {slide['notes']}")
        
        print()
    
    return content


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pptx.py <pptx_path> [output_path]")
        print("Example: python extract_pptx.py inputs/quiz.pptx")
        sys.exit(1)
    
    pptx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # UTF-8 출력 설정
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    extract_pptx(pptx_path, output_path)


if __name__ == '__main__':
    main()
