"""
콘텐츠 생성 서비스
"""

import json
from typing import Dict, Any, Optional

from openai import OpenAI
from app.config import OPENAI_API_KEY, GPT_MODEL
from app.templates import TEMPLATES
from app.utils.logger import logger


class ContentGenerator:
    """
    GPT를 사용하여 한국어 학습 콘텐츠를 생성하는 서비스
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        ContentGenerator 초기화
        
        Args:
            api_key: OpenAI API 키 (기본값: config의 OPENAI_API_KEY)
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
    def generate(self, content_type: str, level: str) -> Dict[str, Any]:
        """
        지정된 유형과 레벨로 콘텐츠를 생성합니다.
        
        Args:
            content_type: 생성할 콘텐츠 유형 (dialogue, lecture 등)
            level: 학습자 레벨 (초급, 중급, 고급 등)
            
        Returns:
            생성된 콘텐츠의 딕셔너리
        """
        if not self.client:
            logger.warning("API 키가 설정되지 않아 모의 콘텐츠를 반환합니다.")
            return self._mock_content(content_type, level)
            
        try:
            logger.info(f"콘텐츠 생성 시작: {content_type} / {level}")
            
            template = TEMPLATES.get(content_type)
            if not template:
                raise ValueError(f"알 수 없는 콘텐츠 유형: {content_type}")
            
            prompt = template.format(level=level)
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 한국어 교육용 콘텐츠를 생성하는 AI입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            # 결과 파싱 및 반환
            try:
                content_data = json.loads(result)
                # 레벨 정보 추가
                if "level" not in content_data:
                    content_data["level"] = level
                logger.info(f"콘텐츠 생성 성공: {content_type} / {level}")
                return content_data
            except json.JSONDecodeError:
                logger.error(f"생성된 콘텐츠를 JSON으로 파싱할 수 없습니다: {result}")
                return {
                    "error": "GPT 응답이 JSON 형식이 아닙니다.",
                    "raw": result,
                    "type": content_type,
                    "level": level
                }
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 중 오류: {str(e)}")
            return {
                "error": f"콘텐츠 생성 중 오류가 발생했습니다: {str(e)}",
                "type": content_type,
                "level": level
            }
    
    def _mock_content(self, content_type: str, level: str) -> Dict[str, Any]:
        """
        API 키가 없을 때 사용할 모의 콘텐츠를 생성합니다.
        
        Args:
            content_type: 콘텐츠 유형
            level: 학습자 레벨
            
        Returns:
            모의 콘텐츠 딕셔너리
        """
        mock_content = {
            "type": content_type,
            "level": level,
            "error": "API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요."
        }
        
        if content_type == "dialogue":
            mock_content.update({
                "topic": "일상 대화",
                "place": "카페",
                "keywords": ["대화", "만남", "인사", "카페", "음료"],
                "situation": "API 키 없이 예시로 생성된 대화",
                "dialogue": ["A: 안녕하세요?", "B: 네, 안녕하세요. 반갑습니다."]
            })
        elif "reading" in content_type:
            mock_content.update({
                "topic": "읽기 지문",
                "place": "온라인",
                "keywords": ["읽기", "학습", "예시", "API", "설정"],
                "title": "API 키 없이 예시로 생성된 지문",
                "text": "이것은 API 키가 없을 때 제공되는 예시 텍스트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            })
        else:
            mock_content.update({
                "topic": "기본 콘텐츠",
                "place": "교실",
                "keywords": ["예시", "기본", "콘텐츠", "API", "설정"],
                "script": "이것은 API 키가 없을 때 제공되는 예시 스크립트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            })
        
        return mock_content