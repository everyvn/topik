"""
TOPIK 문제 생성기 애플리케이션 패키지

한국어 능력 시험(TOPIK) 문제를 자동으로 생성하고 관리하는 애플리케이션입니다.
"""

__version__ = "1.0.0"
__author__ = "TOPIK Generator Team"
__license__ = "MIT"

# 애플리케이션 초기화 함수
def init_app():
    """
    애플리케이션 초기화 작업을 수행합니다.
    필요한 디렉토리를 생성하고 리소스를 준비합니다.
    """
    from app.config import ensure_directories
    from app.utils.logger import logger
    
    # 필요한 디렉토리 생성
    ensure_directories()
    
    logger.info("TOPIK 문제 생성기 애플리케이션 초기화 완료")
    logger.info(f"버전: {__version__}")
    
    return True