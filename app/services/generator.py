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
                
                # 원본 프롬프트 저장
                content_data["original_prompt"] = prompt
                
                logger.info(f"콘텐츠 생성 성공: {content_type} / {level}")
                return content_data
            except json.JSONDecodeError:
                logger.error(f"생성된 콘텐츠를 JSON으로 파싱할 수 없습니다: {result}")
                return {
                    "error": "GPT 응답이 JSON 형식이 아닙니다.",
                    "raw": result,
                    "type": content_type,
                    "level": level,
                    "original_prompt": prompt
                }
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 중 오류: {str(e)}")
            return {
                "error": f"콘텐츠 생성 중 오류가 발생했습니다: {str(e)}",
                "type": content_type,
                "level": level
            }
    
    def regenerate(self, content_data: Dict[str, Any], user_comment: str) -> Dict[str, Any]:
        """
        기존 콘텐츠와 사용자 요구사항을 기반으로 콘텐츠를 재생성합니다.
        
        Args:
            content_data: 기존 콘텐츠 데이터
            user_comment: 사용자의 추가 요구사항
            
        Returns:
            재생성된 콘텐츠의 딕셔너리
        """
        if not self.client:
            logger.warning("API 키가 설정되지 않아 모의 콘텐츠를 반환합니다.")
            content_data["regenerated"] = True
            content_data["user_comment"] = user_comment
            return content_data
            
        try:
            # 기존 콘텐츠 정보 추출
            content_type = content_data.get("type", "")
            level = content_data.get("level", "")
            
            logger.info(f"콘텐츠 재생성 시작: {content_type} / {level}")
            
            # 원본 콘텐츠를 JSON 문자열로 변환
            original_content_str = json.dumps(content_data, ensure_ascii=False)
            
            # 원본 프롬프트 가져오기 (없으면 템플릿에서 재생성)
            original_prompt = content_data.get("original_prompt", "")
            if not original_prompt and content_type in TEMPLATES:
                original_prompt = TEMPLATES[content_type].format(level=level)
            
            # 재생성 프롬프트 구성
            regenerate_prompt = f"""
다음은 이전에 생성된 한국어 교육용 콘텐츠입니다:

{original_content_str}

이 콘텐츠를 다음 요구사항에 맞게 수정해 주세요:

{user_comment}

응답은 반드시 원본과 동일한 JSON 형식으로 제공해 주세요.
"""
            
            # GPT 호출
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 한국어 교육용 콘텐츠를 생성하는 AI입니다."},
                    {"role": "user", "content": f"원본 요청: {original_prompt}"},
                    {"role": "user", "content": regenerate_prompt}
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            
            # 결과 파싱 및 반환
            try:
                # JSON 문자열 전처리 - 잘못된 이스케이프 문자 처리
                cleaned_result = result
                
                # 따옴표 안에 이스케이프되지 않은 따옴표가 있는 경우 수정 시도
                try:
                    new_content_data = json.loads(cleaned_result)
                except json.JSONDecodeError as e:
                    logger.warning(f"첫 번째 JSON 파싱 시도 실패: {str(e)}")
                    
                    # 응답에서 JSON 부분만 추출 시도 (마크다운 코드 블록 등에서)
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|(\{[\s\S]*\})'
                    json_matches = re.findall(json_pattern, cleaned_result)
                    
                    if json_matches:
                        for match in json_matches:
                            # 매치된 그룹 중 비어있지 않은 것 선택
                            json_str = next((m for m in match if m), None)
                            if json_str:
                                try:
                                    new_content_data = json.loads(json_str)
                                    logger.info("JSON 블록에서 유효한 JSON 추출 성공")
                                    break
                                except json.JSONDecodeError:
                                    continue
                    
                    # 여전히 파싱 실패 시 원본 콘텐츠 반환
                    if 'new_content_data' not in locals():
                        logger.error(f"재생성된 콘텐츠를 JSON으로 파싱할 수 없습니다: {cleaned_result}")
                        # 오류 시 원본 콘텐츠에 오류 정보 추가
                        content_data["error"] = f"GPT 응답이 JSON 형식이 아닙니다: {str(e)}"
                        content_data["raw_regenerated"] = cleaned_result
                        content_data["user_comment"] = user_comment
                        return content_data
                
                # 원본 정보 유지
                if "level" not in new_content_data and "level" in content_data:
                    new_content_data["level"] = content_data["level"]
                
                if "type" not in new_content_data and "type" in content_data:
                    new_content_data["type"] = content_data["type"]
                
                # 재생성 정보 추가
                new_content_data["regenerated"] = True
                new_content_data["user_comment"] = user_comment
                new_content_data["original_prompt"] = original_prompt
                
                # 원본 콘텐츠 저장 (재생성 비교용)
                new_content_data["original_content"] = content_data
                
                # ID 보존 (있는 경우)
                if "id" in content_data:
                    new_content_data["id"] = content_data["id"]
                
                logger.info(f"콘텐츠 재생성 성공: {content_type} / {level}")
                return new_content_data
            except Exception as e:
                logger.error(f"재생성된 콘텐츠 처리 중 예외 발생: {str(e)}")
                # 오류 시 원본 콘텐츠에 오류 정보 추가
                content_data["error"] = f"콘텐츠 처리 중 오류: {str(e)}"
                content_data["raw_regenerated"] = result
                content_data["user_comment"] = user_comment
                return content_data
                
        except Exception as e:
            logger.error(f"콘텐츠 재생성 중 오류: {str(e)}")
            # 오류 시 원본 콘텐츠에 오류 정보 추가
            content_data["error"] = f"콘텐츠 재생성 중 오류가 발생했습니다: {str(e)}"
            content_data["user_comment"] = user_comment
            return content_data
    
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