#!/usr/bin/env python
"""
애플리케이션 실행 스크립트

TOPIK 문제 생성기 애플리케이션을 시작하고 관리하는 진입점입니다.
"""

import argparse
import os
import sys
import uvicorn

# 현재 디렉토리를 모듈 검색 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import init_app
from app.config import AppConfig
from app.utils.logger import logger


def parse_arguments():
    """
    명령행 인수를 파싱합니다.
    
    Returns:
        파싱된 명령행 인수
    """
    parser = argparse.ArgumentParser(description="TOPIK 문제 생성기 애플리케이션 실행")
    
    parser.add_argument(
        "--host", 
        type=str, 
        default=AppConfig.HOST,
        help=f"서버 호스트 주소 (기본값: {AppConfig.HOST})"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=AppConfig.PORT,
        help=f"서버 포트 (기본값: {AppConfig.PORT})"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="코드 변경 시 자동으로 서버 재시작 (개발 모드)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    return parser.parse_args()


def main():
    """애플리케이션을 초기화하고 실행합니다."""
    # 명령행 인수 파싱
    args = parse_arguments()
    
    # 환경 변수 설정
    if args.debug:
        os.environ["APP_DEBUG"] = "True"
    
    # 애플리케이션 초기화
    logger.info("TOPIK 문제 생성기 애플리케이션 시작")
    init_app()
    
    # Uvicorn 서버 실행 옵션
    server_options = {
        "app": "app.main:app", 
        "host": args.host, 
        "port": args.port, 
        "reload": args.reload,
        "log_level": "debug" if args.debug else "info",
        "workers": 1
    }
    
    # 실행 정보 로깅
    logger.info(f"서버를 {args.host}:{args.port}에서 시작합니다.")
    if args.reload:
        logger.info("개발 모드: 코드 변경 시 자동 재시작이 활성화되었습니다.")
    
    # Uvicorn 서버 실행
    uvicorn.run(**server_options)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {str(e)}")
        sys.exit(1)