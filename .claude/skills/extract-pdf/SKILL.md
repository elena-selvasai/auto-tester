---
name: extract-pdf
description: Use when extracting content from PDF files for QA test scenario generation. Triggers on PDF analysis, page text/image extraction, or Phase 1 document analysis with PDF input.
---

# PDF 문서 추출

PDF 기획서에서 텍스트, 이미지를 추출하고 페이지별 렌더 이미지를 저장합니다.

## 실행

```bash
# 통합 진입점 (권장)
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs

# PDF 직접 호출
python .cursor/skills/qa-automation/scripts/extract_pdf.py inputs/spec.pdf --reference-dir outputs/reference
```

## 의존성

```bash
pip install PyMuPDF
```

## 추출 항목

| 항목 | 방식 | 비고 |
|------|------|------|
| 텍스트 | `fitz` text blocks | 페이지별 텍스트 블록 |
| 이미지 | `fitz` extract_images | embedded 이미지 |
| 페이지 렌더 | `fitz` page.get_pixmap | 전체 페이지를 PNG로 렌더링 |

## 출력 스키마

```json
{
  "pages": [
    {
      "page_num": 1,
      "texts": ["텍스트 블록"],
      "tables": [],
      "notes": "",
      "images": [
        { "path": "outputs/reference/pdf_page_1.png", "description": "page render" },
        { "path": "outputs/reference/pdf_img_1_0.png", "description": "" }
      ]
    }
  ],
  "reference_images": [
    { "source_page": 1, "path": "outputs/reference/pdf_page_1.png" }
  ]
}
```

PDF는 자연스러운 페이지 구분이 있어 `page_num`이 실제 페이지 번호와 일치합니다.

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `fitz` import 에러 | `pip install PyMuPDF` (패키지명 ≠ import명) |
| 텍스트 추출 빈 결과 | 스캔 PDF는 텍스트 레이어 없음 — OCR 필요 |
| 렌더 해상도 낮음 | 스크립트 내 DPI 설정 조정 |
