"""
애플리케이션 설정 및 상수
"""

import os
from pathlib import Path

# 애플리케이션 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 데이터 디렉토리 설정
DATA_DIR = BASE_DIR / "data"
os.makedirs(DATA_DIR, exist_ok=True)  # 디렉토리가 없으면 생성

# 파일 경로 설정
CONFIRM_FILE = DATA_DIR / "confirmed_questions.json"

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPT 모델 설정
GPT_MODEL = "gpt-3.5-turbo"