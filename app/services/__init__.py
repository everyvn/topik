"""
서비스 패키지

TOPIK 문제 생성기의 핵심 서비스 모듈을 제공합니다.
이 패키지는 콘텐츠 생성, 저장, 관리 등의 비즈니스 로직을 담당합니다.
"""

# 내부 임포트 순환 참조 방지를 위해 런타임에 임포트
from app.services.generator import ContentGenerator
from app.services.storage import ContentStorage

# 서비스 팩토리 함수
def create_content_generator(**kwargs):
    """
    ContentGenerator 인스턴스를 생성합니다.
    
    Args:
        **kwargs: ContentGenerator 생성자에 전달할 인자
        
    Returns:
        생성된 ContentGenerator 인스턴스
    """
    return ContentGenerator(**kwargs)

def create_content_storage(**kwargs):
    """
    ContentStorage 인스턴스를 생성합니다.
    
    Args:
        **kwargs: ContentStorage 생성자에 전달할 인자
        
    Returns:
        생성된 ContentStorage 인스턴스
    """
    return ContentStorage(**kwargs)

# 외부에서 import 가능한 모든 심볼 정의
__all__ = [
    "ContentGenerator",
    "ContentStorage",
    "create_content_generator",
    "create_content_storage"
]