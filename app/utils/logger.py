"""
로깅 설정 모듈

애플리케이션 전체에서 사용되는 로깅 기능을 제공합니다.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LogConfig:
    """로깅 설정 관련 상수"""
    APP_NAME = "topik_generator"
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 로그 파일 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    LOG_DIR = BASE_DIR / "logs"
    LOG_FILE = LOG_DIR / f"{APP_NAME}.log"
    
    # 로그 파일 크기 설정 (10MB)
    MAX_LOG_SIZE = 10 * 1024 * 1024
    BACKUP_COUNT = 5


def setup_logger(name=LogConfig.APP_NAME, level=None, 
                 log_to_file=True, log_to_console=True):
    """
    애플리케이션 로거를 설정하고 반환합니다.
    
    Args:
        name: 로거 이름
        level: 로그 레벨 (기본값: LogConfig.LOG_LEVEL)
        log_to_file: 파일 로깅 활성화 여부
        log_to_console: 콘솔 로깅 활성화 여부
        
    Returns:
        설정된 로거 인스턴스
    """
    if level is None:
        level = LogConfig.LOG_LEVEL
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 설정되어 있으면 중복 방지
    if logger.handlers:
        return logger
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        LogConfig.LOG_FORMAT, 
        datefmt=LogConfig.LOG_DATE_FORMAT
    )
    
    # 콘솔 로깅 설정
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 파일 로깅 설정
    if log_to_file:
        try:
            # 로그 디렉토리 생성
            os.makedirs(LogConfig.LOG_DIR, exist_ok=True)
            
            # 파일 핸들러 생성
            file_handler = RotatingFileHandler(
                LogConfig.LOG_FILE,
                maxBytes=LogConfig.MAX_LOG_SIZE,
                backupCount=LogConfig.BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            # 파일 로깅 초기화 실패 시 경고 기록
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.WARNING)
            console_handler.emit(
                logging.LogRecord(
                    name, 
                    logging.WARNING,
                    pathname="",
                    lineno=0,
                    msg=f"로그 파일 설정 실패: {e}",
                    args=(),
                    exc_info=None
                )
            )
    
    return logger


# 앱 전체에서 사용할 로거 인스턴스
logger = setup_logger()


def get_logger(module_name):
    """
    모듈별 로거 인스턴스를 반환합니다.
    
    Args:
        module_name: 모듈 이름
        
    Returns:
        해당 모듈의 로거 인스턴스
    """
    return setup_logger(f"{LogConfig.APP_NAME}.{module_name}", log_to_file=False)