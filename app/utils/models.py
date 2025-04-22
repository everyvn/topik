"""
데이터 모델 정의

애플리케이션에서 사용되는 데이터 모델과 관련 유틸리티 함수를 정의합니다.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union, Type
from uuid import uuid4
from pydantic import BaseModel, Field, validator


class ContentType(str, Enum):
    """콘텐츠 유형 열거형"""
    DIALOGUE = "dialogue"
    MONOLOGUE = "monologue_explanation"
    NEWS = "news_reading"
    LECTURE = "lecture"
    SHORT_READING = "short_reading"
    LONG_READING = "long_reading"
    IMAGE_READING = "image_description_reading"
    IMAGE_LISTENING = "image_description_listening"


class ContentLevel(str, Enum):
    """콘텐츠 난이도 열거형"""
    BEGINNER = "초급"
    INTERMEDIATE = "중급"
    ADVANCED = "고급"


class ContentBase(BaseModel):
    """콘텐츠 기본 모델"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    level: str
    topic: Optional[str] = None
    place: Optional[str] = None
    keywords: Optional[List[str]] = None
    tokens: Optional[int] = None
    
    # 생성/수정 관련 필드
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # 재생성 관련 필드 
    regenerated: Optional[bool] = None
    user_comment: Optional[str] = None
    original_content: Optional[Dict[str, Any]] = None
    original_prompt: Optional[str] = None
    
    @validator('keywords', pre=True)
    def ensure_keywords_list(cls, v):
        """키워드가 문자열인 경우 리스트로 변환"""
        if isinstance(v, str):
            return [k.strip() for k in v.split(',')]
        return v
    
    class Config:
        extra = "allow"  # 추가 필드 허용
    
    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return self.dict(exclude_unset=True)


class DialogueContent(ContentBase):
    """대화 콘텐츠 모델"""
    situation: str
    dialogue: List[str]
    
    @validator('dialogue')
    def validate_dialogue(cls, v):
        """대화 형식 검증 (A:, B: 시작)"""
        if not all(line.startswith(('A:', 'B:')) for line in v):
            raise ValueError("대화 형식이 올바르지 않습니다. 각 라인은 'A:' 또는 'B:'로 시작해야 합니다.")
        return v


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
    
    @validator('answer_index')
    def validate_answer_index(cls, v, values):
        """정답 인덱스 유효성 검증"""
        if v is not None and 'choices' in values and values['choices']:
            if v < 0 or v >= len(values['choices']):
                raise ValueError(f"정답 인덱스가 유효하지 않습니다. 0에서 {len(values['choices'])-1} 사이어야 합니다.")
        return v


# 콘텐츠 타입별 모델 매핑
CONTENT_TYPE_MODELS = {
    ContentType.DIALOGUE: DialogueContent,
    ContentType.MONOLOGUE: MonologueContent,
    ContentType.NEWS: MonologueContent,
    ContentType.LECTURE: MonologueContent,
    ContentType.SHORT_READING: ReadingContent,
    ContentType.LONG_READING: ReadingContent,
    ContentType.IMAGE_READING: ReadingContent,
    ContentType.IMAGE_LISTENING: ListeningContent,
}


def parse_content(data: Dict[str, Any]) -> ContentBase:
    """
    콘텐츠 타입에 따라 적절한 모델로 변환합니다.
    
    Args:
        data: 변환할 콘텐츠 데이터
        
    Returns:
        변환된 모델 인스턴스
    """
    content_type = data.get("type", "")
    
    # 열거형과 문자열 모두 지원
    if isinstance(content_type, ContentType):
        model_class = CONTENT_TYPE_MODELS.get(content_type)
    else:
        # 문자열 기반으로 매칭 시도
        try:
            ct = ContentType(content_type)
            model_class = CONTENT_TYPE_MODELS.get(ct)
        except ValueError:
            # 직접 매핑 시도
            if "dialogue" in content_type or content_type == "image_description_listening":
                model_class = DialogueContent
            elif content_type in ["monologue_explanation", "news_reading", "lecture"]:
                model_class = MonologueContent
            elif "reading" in content_type:
                model_class = ReadingContent
            else:
                model_class = ContentBase
    
    # 모델 클래스가 결정되었으면 인스턴스 생성
    if model_class:
        try:
            return model_class(**data)
        except Exception as e:
            # 변환 오류 발생 시 기본 모델로 폴백
            return ContentBase(**data)
    else:
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


def create_content_model(content_type: Union[str, ContentType], 
                         level: Union[str, ContentLevel], 
                         **kwargs) -> ContentBase:
    """
    지정된 타입과 레벨로 새 콘텐츠 모델을 생성합니다.
    
    Args:
        content_type: 콘텐츠 타입
        level: 콘텐츠 레벨
        **kwargs: 추가 필드
        
    Returns:
        생성된 콘텐츠 모델 인스턴스
    """
    # 타입 문자열 변환
    if isinstance(content_type, ContentType):
        type_str = content_type.value
    else:
        type_str = content_type
    
    # 레벨 문자열 변환
    if isinstance(level, ContentLevel):
        level_str = level.value
    else:
        level_str = level
    
    # 기본 데이터
    data = {
        "type": type_str,
        "level": level_str,
        **kwargs
    }
    
    return parse_content(data)