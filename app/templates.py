"""
GPT 프롬프트 템플릿 모듈

TOPIK 문제 생성기에서 사용하는 다양한 유형의 GPT 프롬프트 템플릿을 정의합니다.
"""

from enum import Enum
from typing import Dict, Optional


class TemplateType(str, Enum):
    """프롬프트 템플릿 유형"""
    DIALOGUE = "dialogue"
    MONOLOGUE = "monologue_explanation"
    NEWS = "news_reading"
    LECTURE = "lecture"
    SHORT_READING = "short_reading"
    LONG_READING = "long_reading"
    IMAGE_READING = "image_description_reading"
    IMAGE_LISTENING = "image_description_listening"


class PromptTemplate:
    """GPT 프롬프트 템플릿 클래스"""
    
    def __init__(self, template: str, output_format: Optional[str] = None):
        """
        프롬프트 템플릿 초기화
        
        Args:
            template: 프롬프트 템플릿 문자열
            output_format: 출력 형식 지정 (기본값: None)
        """
        self.template = template
        self.output_format = output_format
    
    def format(self, **kwargs) -> str:
        """
        프롬프트 템플릿에 변수를 적용하여 최종 프롬프트 생성
        
        Args:
            **kwargs: 템플릿에 적용할 변수
            
        Returns:
            변수가 적용된 프롬프트 문자열
        """
        prompt = self.template.format(**kwargs)
        
        # 출력 형식이 정의되어 있으면 추가
        if self.output_format:
            prompt += f"\n\n출력 형식:\n{self.output_format}"
            
        return prompt


# 기본 출력 형식 템플릿
_BASE_OUTPUT_FORMAT = """
{{
  "type": "{type}",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  {additional_fields}
  "tokens": ...
}}"""


# 각 콘텐츠 유형별 출력 형식 필드
_OUTPUT_FORMAT_FIELDS = {
    TemplateType.DIALOGUE: '"situation": "...",\n  "dialogue": ["A: ...", "B: ..."],',
    TemplateType.MONOLOGUE: '"situation": "...",\n  "script": "...",',
    TemplateType.NEWS: '"script": "...",',
    TemplateType.LECTURE: '"script": "...",',
    TemplateType.SHORT_READING: '"title": "...",\n  "text": "...",',
    TemplateType.LONG_READING: '"title": "...",\n  "text": "...",',
    TemplateType.IMAGE_READING: '"description": "...",',
    TemplateType.IMAGE_LISTENING: '"dialogue": ["A: ...", "B: ..."],\n  "choices": ["...", "...", "...", "..."],\n  "answer_index": 0,',
}


def _create_output_format(template_type: TemplateType) -> str:
    """템플릿 유형에 맞는 출력 형식 생성"""
    additional_fields = _OUTPUT_FORMAT_FIELDS.get(template_type, "")
    return _BASE_OUTPUT_FORMAT.format(
        type=template_type.value,
        additional_fields=additional_fields
    )


# 템플릿 정의
_TEMPLATE_DEFINITIONS = {
    TemplateType.DIALOGUE: """
{level} 학습자에게 적합한 일상 대화문을 하나 생성해 주세요.
- 장소: 실생활에서 흔히 일어날 수 있는 곳 (예: 카페, 병원, 사무실 등)
- 구성: 두 명의 화자 A, B가 등장하며, 2~5문장 내외의 대화로 구성
- 문체: 자연스러운 구어체, 높임말 혹은 반말 혼용 가능
- 목적: 일상적인 요청, 제안, 설명, 문제 해결 등의 상황 반영
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.MONOLOGUE: """
{level} 학습자에게 적합한 혼잣말 형식의 설명문을 생성해 주세요.
- 문체: 혼잣말처럼 말하는 1인칭 구어체 혹은 발표체
- 기능: 일정 안내, 절차 설명, 경험 공유, 통계 발표 등
- 구성: 도입(배경) → 설명(내용) → 정리(마무리)
- 길이: 150~300자 내외, 4~7문장
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.NEWS: """
{level} 학습자에게 적합한 뉴스 기사 형식의 듣기 지문을 작성해 주세요.
- 문체: 간결하고 중립적인 기사체
- 내용: 기상, 사고, 발표, 정책 등 현실성 있는 주제
- 구성: 시간/장소 → 사건 → 영향 및 조치
- 길이: 약 200~300자
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.LECTURE: """
{level} 학습자에게 적합한 강의 형식의 지문을 생성해 주세요.
- 문체: 설명문, 객관적이며 교사/강사 어조
- 주제: 역사, 사회, 과학, 문화 등 중립적 주제
- 구성: 정의 → 예시 → 결론 / 명확한 정보 구조
- 길이: 300~400자
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.SHORT_READING: """
{level} 학습자에게 적합한 짧은 읽기 지문을 생성해 주세요.
- 문체: 안내문, 일기, 블로그 글 등 개인적 문체 가능
- 길이: 150~200자 / 단문 1개 지문
- 목적: 중심 내용 파악, 정보 요약, 의견 이해 등
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.LONG_READING: """
{level} 학습자에게 적합한 장문 읽기 지문을 생성해 주세요.
- 문체: 설명문, 기사체, 에세이체 등
- 구성: 주제 제시 → 설명 → 예시/결론
- 길이: 약 300~500자 / 문단 구조를 명확히 할 것
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.IMAGE_READING: """
{level} 학습자에게 적합한 포스터, 이메일, 통계자료 등의 시각 자료를 설명하는 읽기 지문을 작성해 주세요.
- 문체: 안내문, 정보 설명 문체
- 구성: 제목 → 내용 요약 → 시간/장소/대상 정보
- 길이: 150~250자
- 추가 항목: topic, place, keywords(5개), tokens
""",

    TemplateType.IMAGE_LISTENING: """
{level} 학습자에게 적합한 듣기용 그림 선택 문제를 구성해 주세요.
- 구성: 상황 대화문 1개 + 그림 설명 4개 중 1개는 정답
- 문체: 구어체
- 길이: 대화문은 3~4문장 / 설명문은 간결히
- 추가 항목: topic, place, keywords(5개), tokens
"""
}


# PromptTemplate 인스턴스 생성
TEMPLATES = {
    template_type.value: PromptTemplate(
        template=_TEMPLATE_DEFINITIONS[template_type],
        output_format=_create_output_format(template_type)
    )
    for template_type in TemplateType
}


# 재생성용 템플릿
REGENERATE_TEMPLATE = """
다음은 이전에 생성된 한국어 교육용 콘텐츠입니다:

{original_content}

이 콘텐츠를 다음 요구사항에 맞게 수정해 주세요:

{user_comment}

응답은 반드시 원본과 동일한 JSON 형식으로 제공해 주세요.
마크다운이나 설명 없이 순수한 JSON 객체만 반환해주세요.
"""


def get_template(template_type: str) -> Optional[PromptTemplate]:
    """
    템플릿 유형에 해당하는 프롬프트 템플릿을 반환합니다.
    
    Args:
        template_type: 템플릿 유형
        
    Returns:
        해당 유형의 PromptTemplate 또는 None (없을 경우)
    """
    return TEMPLATES.get(template_type)


def build_regenerate_prompt(original_content: str, user_comment: str) -> str:
    """
    재생성 프롬프트를 구성합니다.
    
    Args:
        original_content: 원본 콘텐츠 JSON 문자열
        user_comment: 사용자 요청 사항
        
    Returns:
        구성된 재생성 프롬프트
    """
    return REGENERATE_TEMPLATE.format(
        original_content=original_content,
        user_comment=user_comment
    )