"""
애플리케이션 설정 및 상수

환경 변수, 경로 설정, API 키 등 애플리케이션 구성 정보를 관리합니다.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

# 로거 설정 (config 모듈 전용)
logger = logging.getLogger("topik_generator.config")

# 애플리케이션 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 디렉토리 설정
class Directories:
    """애플리케이션에서 사용하는 디렉토리 경로"""
    DATA = BASE_DIR / "data"
    LOGS = BASE_DIR / "logs"
    TEMP = BASE_DIR / "temp"
    BACKUPS = DATA / "backups"


# 파일 경로 설정
class Files:
    """애플리케이션에서 사용하는 파일 경로"""
    CONFIRM = Directories.DATA / "confirmed_questions.json"
    TRASH = Directories.DATA / "trash.json"
    CONFIG = Directories.DATA / "config.json"


# AI 모델 설정
class AIConfig:
    """AI 모델 관련 설정"""
    # OpenAI API 키 (환경 변수에서 가져오거나 기본값 사용)
    API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 모델 설정
    MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
    
    # 생성 설정
    TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", "1500"))
    
    @classmethod
    def is_configured(cls) -> bool:
        """API 키가 설정되어 있는지 확인"""
        return bool(cls.API_KEY)


# 앱 설정
class AppConfig:
    """애플리케이션 일반 설정"""
    # 서버 설정
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("APP_PORT", "8000"))
    DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "yes")
    
    # 백업 설정
    MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "30"))
    AUTO_BACKUP = os.getenv("AUTO_BACKUP", "True").lower() in ("true", "1", "yes")
    
    # 사용자 설정 로드
    @classmethod
    def load_user_config(cls) -> Dict[str, Any]:
        """config.json에서 사용자 설정 로드"""
        try:
            if Files.CONFIG.exists():
                with open(Files.CONFIG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"사용자 설정 로드 실패: {str(e)}")
            return {}
    
    @classmethod
    def save_user_config(cls, config: Dict[str, Any]) -> bool:
        """사용자 설정을 config.json에 저장"""
        try:
            os.makedirs(Directories.DATA, exist_ok=True)
            with open(Files.CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"사용자 설정 저장 실패: {str(e)}")
            return False
    
    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> Any:
        """설정 값 조회 (환경 변수 > 사용자 설정 > 기본값 순서로 확인)"""
        # 1. 환경 변수에서 확인
        env_val = os.getenv(key)
        if env_val is not None:
            return env_val
        
        # 2. 사용자 설정에서 확인
        user_config = cls.load_user_config()
        if key in user_config:
            return user_config[key]
        
        # 3. 기본값 반환
        return default


def ensure_directories() -> None:
    """필요한 디렉토리가 존재하는지 확인하고 없으면 생성"""
    for dir_path in [
        Directories.DATA,
        Directories.LOGS,
        Directories.TEMP,
        Directories.BACKUPS
    ]:
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"디렉토리 확인/생성: {dir_path}")


# 앱 시작 시 디렉토리 생성
ensure_directories()