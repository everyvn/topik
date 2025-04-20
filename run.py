"""
애플리케이션 실행 스크립트
"""

import uvicorn
from app.utils.logger import logger


def main():
    """애플리케이션을 실행합니다."""
    logger.info("TOPIK 문제 생성기 애플리케이션 시작")
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True  # 개발 모드에서 코드 변경 시 자동 재시작
    )


if __name__ == "__main__":
    main()