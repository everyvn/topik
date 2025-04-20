"""
데이터 모델 정의
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import uuid


class ContentBase(BaseModel):
    """콘텐츠 기본 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    level: str
    topic: Optional[str] = None
    place: Optional[str] = None
    keywords: Optional[List[str]] = None
    tokens: Optional[int] = None


class DialogueContent(ContentBase):
    """대화 콘텐츠 모델"""
    situation: str
    dialogue: List[str]


class MonologueContent(ContentBase):
    """독백/설명문 콘텐츠 모델"""
    situation: Optional[str] = None
    script: str


class ReadingContent(ContentBase):
    """읽기 지문 콘텐츠 모델"""
    title: Optional[str] = None
    text: Optional[str] = None
    description: Optional[str] = None


class ListeningContent(ContentBase):
    """듣기 지문 콘텐츠 모델"""
    dialogue: Optional[List[str]] = None
    script: Optional[str] = None
    choices: Optional[List[str]] = None
    answer_index: Optional[int] = None


def parse_content(data: Dict[str, Any]) -> BaseModel:
    """
    콘텐츠 타입에 따라 적절한 모델로 변환합니다.
    
    Args:
        data: 변환할 콘텐츠 데이터
        
    Returns:
        변환된 모델 인스턴스
    """
    content_type = data.get("type", "")
    
    if "dialogue" in content_type or content_type == "image_description_listening":
        return DialogueContent(**data)
    elif content_type in ["monologue_explanation", "news_reading", "lecture"]:
        return MonologueContent(**data)
    elif "reading" in content_type:
        return ReadingContent(**data)
    else:
        # 기본적으로 베이스 모델로 변환
        return ContentBase(**data)


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """
    모델을 딕셔너리로 변환합니다.
    
    Args:
        model: 변환할 모델 인스턴스
        
    Returns:
        변환된 딕셔너리
    """
    return model.dict(exclude_unset=True)