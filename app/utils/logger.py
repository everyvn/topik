"""
로깅 설정 모듈
"""

import logging

def setup_logger():
    """애플리케이션 로거를 설정하고 반환합니다."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    logger = logging.getLogger("topik_generator")
    return logger

# 앱 전체에서 사용할 로거 인스턴스
logger = setup_logger()