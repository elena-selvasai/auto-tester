"""
AI 설정 공통 모듈

이 모듈은 Google Gemini API 설정을 중앙에서 관리합니다.
모든 스크립트에서 이 모듈을 import하여 사용하세요.

사용법:
    from ai_config import model
    response = model.generate_content("프롬프트")
"""

import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# 프로젝트 루트에서 .env 파일 로드
# scripts 폴더 기준으로 상위 폴더들에서 .env 찾기
def find_and_load_env():
    """프로젝트 루트의 .env 파일을 찾아서 로드"""
    current_dir = Path(__file__).resolve().parent
    
    # 상위 폴더를 순회하며 .env 파일 찾기
    for parent in [current_dir] + list(current_dir.parents):
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return str(env_path)
    
    # 기본 load_dotenv 실행
    load_dotenv()
    return None

# 환경변수 로드
env_file = find_and_load_env()

# API 키 가져오기
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.\n"
        "   다음 단계를 확인하세요:\n"
        "   1. 프로젝트 루트에 .env 파일이 있는지 확인\n"
        "   2. .env 파일에 GOOGLE_API_KEY=your_key 형식으로 설정\n"
        "   3. Google AI Studio에서 API 키 발급: https://aistudio.google.com/app/apikey"
    )

# Gemini API 설정
genai.configure(api_key=GOOGLE_API_KEY)

# 기본 모델 인스턴스 생성
model = genai.GenerativeModel('gemini-1.5-pro')

# 다른 모델이 필요한 경우 사용
def get_model(model_name: str = 'gemini-1.5-pro') -> genai.GenerativeModel:
    """지정된 모델 인스턴스를 반환합니다.
    
    Args:
        model_name: 사용할 모델 이름 (기본값: gemini-1.5-pro)
        
    Returns:
        GenerativeModel 인스턴스
    """
    return genai.GenerativeModel(model_name)


# 초기화 완료 메시지 (디버그용)
if __name__ == "__main__":
    print("✅ AI 설정 모듈 초기화 완료")
    print(f"   - 환경 파일: {env_file}")
    print(f"   - 모델: gemini-1.5-pro")
