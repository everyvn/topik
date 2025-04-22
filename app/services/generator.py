"""
콘텐츠 생성 서비스

GPT 모델을 사용하여 한국어 학습 콘텐츠를 생성하는 서비스를 제공합니다.
"""

import json
from typing import Dict, Any, Optional, List, Union
import re

from openai import OpenAI
from app.config import AIConfig
from app.templates import get_template, build_regenerate_prompt, TemplateType
from app.utils.logger import get_logger
from app.utils.json_debug import safely_parse_json, fix_common_json_errors

# 모듈 로거 설정
logger = get_logger("generator")


class ContentGenerator:
    """
    GPT를 사용하여 한국어 학습 콘텐츠를 생성하는 서비스
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        ContentGenerator 초기화
        
        Args:
            api_key: OpenAI API 키 (기본값: config의 API_KEY)
            model: 사용할 GPT 모델 (기본값: config의 MODEL)
        """
        self.api_key = api_key or AIConfig.API_KEY
        self.model = model or AIConfig.MODEL
        self.client = self._create_client()
        
    def _create_client(self) -> Optional[OpenAI]:
        """OpenAI 클라이언트 생성"""
        if not self.api_key:
            logger.warning("API 키가 설정되지 않았습니다.")
            return None
        
        try:
            return OpenAI(api_key=self.api_key)
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 생성 중 오류: {str(e)}")
            return None
        
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
            return self._generate_mock_content(content_type, level)
            
        try:
            logger.info(f"콘텐츠 생성 시작: {content_type} / {level}")
            
            # 템플릿 가져오기
            template = get_template(content_type)
            if not template:
                raise ValueError(f"알 수 없는 콘텐츠 유형: {content_type}")
            
            # 프롬프트 생성
            prompt = template.format(level=level)
            
            # GPT 호출
            response = self._call_gpt(
                system_message="당신은 한국어 교육용 콘텐츠를 생성하는 AI입니다.",
                user_message=prompt
            )
            
            # 결과 처리 및 반환
            return self._process_generation_result(response, content_type, level, prompt)
                
        except Exception as e:
            logger.error(f"콘텐츠 생성 중 오류: {str(e)}")
            return {
                "error": f"콘텐츠 생성 중 오류가 발생했습니다: {str(e)}",
                "type": content_type,
                "level": level
            }
    
    def regenerate(self, content_data: Union[Dict[str, Any], str], user_comment: str) -> Dict[str, Any]:
        """
        기존 콘텐츠와 사용자 요구사항을 기반으로 콘텐츠를 재생성합니다.
        
        Args:
            content_data: 기존 콘텐츠 데이터 (딕셔너리 또는 JSON 문자열)
            user_comment: 사용자의 추가 요구사항
            
        Returns:
            재생성된 콘텐츠의 딕셔너리
        """
        # 입력 데이터 전처리
        content_data = self._prepare_content_data(content_data)
        
        if not self.client:
            logger.warning("API 키가 설정되지 않아 모의 재생성 콘텐츠를 반환합니다.")
            content_data["regenerated"] = True
            content_data["user_comment"] = user_comment
            return content_data
            
        try:
            # 콘텐츠 정보 추출
            content_type = content_data.get("type", "")
            level = content_data.get("level", "")
            
            logger.info(f"콘텐츠 재생성 시작: {content_type} / {level}")
            
            # 재생성 프롬프트 구성
            prompt = self._build_regenerate_prompt(content_data, user_comment)
            
            # GPT 호출
            response = self._call_gpt(
                system_message="당신은 한국어 교육용 콘텐츠를 생성하는 AI입니다. 응답은 항상 순수한 JSON 형식으로만 반환합니다.",
                user_message=prompt,
                temperature=0.7
            )
            
            # 결과 처리 및 반환
            return self._process_regeneration_result(response, content_data, user_comment)
                
        except Exception as e:
            logger.error(f"콘텐츠 재생성 중 오류: {str(e)}")
            # 오류 시 원본 콘텐츠에 오류 정보 추가
            content_data["error"] = f"콘텐츠 재생성 중 오류가 발생했습니다: {str(e)}"
            content_data["user_comment"] = user_comment
            return content_data
            
    def _call_gpt(self, system_message: str, user_message: str, 
                 temperature: Optional[float] = None) -> str:
        """
        GPT 모델을 호출하여 응답을 생성합니다.
        
        Args:
            system_message: 시스템 메시지
            user_message: 사용자 메시지
            temperature: 생성 온도 (기본값: AIConfig.TEMPERATURE)
            
        Returns:
            GPT 응답 텍스트
        """
        if not self.client:
            raise ValueError("OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature or AIConfig.TEMPERATURE,
                max_tokens=AIConfig.MAX_TOKENS
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GPT 호출 중 오류: {str(e)}")
            raise ValueError(f"GPT 호출 실패: {str(e)}")
    
    def _prepare_content_data(self, content_data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        콘텐츠 데이터를 전처리합니다.
        
        Args:
            content_data: 콘텐츠 데이터 (딕셔너리 또는 JSON 문자열)
            
        Returns:
            전처리된 콘텐츠 데이터 딕셔너리
        """
        # 문자열인 경우 JSON 파싱
        if isinstance(content_data, str):
            try:
                return safely_parse_json(content_data)
            except ValueError as e:
                logger.error(f"콘텐츠 데이터 파싱 실패: {str(e)}")
                raise ValueError(f"콘텐츠 데이터를 파싱할 수 없습니다: {str(e)}")
        
        return content_data
    
    def _build_regenerate_prompt(self, content_data: Dict[str, Any], user_comment: str) -> str:
        """
        재생성 프롬프트를 구성합니다.
        
        Args:
            content_data: 기존 콘텐츠 데이터 
            user_comment: 사용자의 추가 요구사항
            
        Returns:
            구성된 프롬프트
        """
        # 원본 콘텐츠를 JSON 문자열로 변환
        try:
            original_content_str = json.dumps(content_data, ensure_ascii=False)
        except TypeError as e:
            logger.error(f"JSON 직렬화 오류: {str(e)}")
            # 직렬화할 수 없는 값 필터링
            filtered_content = {}
            for k, v in content_data.items():
                try:
                    json.dumps({k: v})
                    filtered_content[k] = v
                except (TypeError, OverflowError):
                    filtered_content[k] = str(v)
            original_content_str = json.dumps(filtered_content, ensure_ascii=False)
        
        # 원본 프롬프트 가져오기
        original_prompt = content_data.get("original_prompt", "")
        
        # 원본 프롬프트가 없고 콘텐츠 타입이 있는 경우 템플릿에서 재구성
        if not original_prompt and "type" in content_data:
            template = get_template(content_data["type"])
            if template and "level" in content_data:
                original_prompt = template.format(level=content_data["level"])
        
        # 재생성 프롬프트 구성
        return build_regenerate_prompt(
            original_content=original_content_str,
            user_comment=user_comment
        )
    
    def _process_generation_result(self, result: str, content_type: str, 
                                  level: str, prompt: str) -> Dict[str, Any]:
        """
        생성 결과를 처리합니다.
        
        Args:
            result: GPT 응답 텍스트
            content_type: 콘텐츠 유형
            level: 콘텐츠 레벨
            prompt: 사용된 프롬프트
            
        Returns:
            처리된 콘텐츠 데이터
        """
        try:
            # JSON 파싱 시도
            content_data = safely_parse_json(result)
            
            # 기본 정보 추가
            if "level" not in content_data:
                content_data["level"] = level
                
            if "type" not in content_data:
                content_data["type"] = content_type
            
            # 원본 프롬프트 저장
            content_data["original_prompt"] = prompt
            
            logger.info(f"콘텐츠 생성 성공: {content_type} / {level}")
            return content_data
            
        except ValueError as e:
            logger.error(f"생성된 콘텐츠를 JSON으로 파싱할 수 없습니다: {result}")
            # 파싱 실패 시 오류 정보 반환
            return {
                "error": f"GPT 응답이 JSON 형식이 아닙니다: {str(e)}",
                "raw": result,
                "type": content_type,
                "level": level,
                "original_prompt": prompt
            }
    
    def _process_regeneration_result(self, result: str, original_content: Dict[str, Any], 
                                    user_comment: str) -> Dict[str, Any]:
        """
        재생성 결과를 처리합니다.
        
        Args:
            result: GPT 응답 텍스트
            original_content: 원본 콘텐츠 데이터
            user_comment: 사용자 요청 사항
            
        Returns:
            처리된 콘텐츠 데이터
        """
        try:
            # JSON 추출 시도
            cleaned_result = self._extract_json_from_result(result)
            
            # JSON 파싱 시도
            try:
                new_content_data = safely_parse_json(cleaned_result)
            except ValueError as e:
                logger.error(f"재생성 결과 파싱 실패: {str(e)}")
                # 오류 시 원본 콘텐츠에 오류 정보 추가
                original_content["error"] = f"재생성 결과 파싱 실패: {str(e)}"
                original_content["raw_regenerated"] = result
                original_content["user_comment"] = user_comment
                return original_content
            
            # 원본 정보 유지
            self._preserve_original_fields(new_content_data, original_content)
            
            # 재생성 정보 추가
            new_content_data["regenerated"] = True
            new_content_data["user_comment"] = user_comment
            new_content_data["original_prompt"] = original_content.get("original_prompt", "")
            
            # 원본 콘텐츠 저장 (재생성 비교용)
            new_content_data["original_content"] = original_content
            
            # ID 보존 (있는 경우)
            if "id" in original_content:
                new_content_data["id"] = original_content["id"]
            
            logger.info(f"콘텐츠 재생성 성공: {new_content_data.get('type')} / {new_content_data.get('level')}")
            return new_content_data
            
        except Exception as e:
            logger.error(f"재생성된 콘텐츠 처리 중 예외 발생: {str(e)}")
            # 오류 시 원본 콘텐츠에 오류 정보 추가
            original_content["error"] = f"콘텐츠 처리 중 오류: {str(e)}"
            original_content["raw_regenerated"] = result
            original_content["user_comment"] = user_comment
            return original_content
    
    def _extract_json_from_result(self, result: str) -> str:
        """
        결과 텍스트에서 JSON 부분을 추출합니다.
        
        Args:
            result: GPT 응답 텍스트
            
        Returns:
            추출된 JSON 문자열
        """
        # 마크다운 코드 블록 제거
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        code_block_match = re.search(code_block_pattern, result)
        
        if code_block_match:
            # 마크다운 코드 블록에서 JSON 추출
            cleaned_result = code_block_match.group(1).strip()
            logger.info("마크다운 코드 블록에서 JSON 추출 성공")
            return cleaned_result
        
        # JSON 객체 패턴 추출 시도
        json_pattern = r'(\{[\s\S]*\})'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            cleaned_result = json_match.group(1).strip()
            logger.info("JSON 객체 패턴으로 추출 성공")
            return cleaned_result
        
        # 추출 실패 시 원본 반환
        logger.info("JSON 패턴 추출 실패, 원본 응답 사용")
        return result
    
    def _preserve_original_fields(self, new_content: Dict[str, Any], 
                                 original_content: Dict[str, Any]) -> None:
        """
        원본 콘텐츠의 중요 필드를 새 콘텐츠에 유지합니다.
        
        Args:
            new_content: 새 콘텐츠 데이터 (수정됨)
            original_content: 원본 콘텐츠 데이터
        """
        # 필수 필드 목록
        essential_fields = ["level", "type"]
        
        # 필수 필드가 없으면 원본에서 복사
        for field in essential_fields:
            if field not in new_content and field in original_content:
                new_content[field] = original_content[field]
    
    def _generate_mock_content(self, content_type: str, level: str) -> Dict[str, Any]:
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
            "error": "API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요.",
            "topic": "모의 콘텐츠",
            "place": "온라인",
            "keywords": ["테스트", "모의", "API_키", "필요", "샘플"]
        }
        
        # 유형별 추가 필드
        type_specific_fields = {
            "dialogue": {
                "situation": "API 키 없이 예시로 생성된 대화",
                "dialogue": ["A: 안녕하세요?", "B: 네, 안녕하세요. 반갑습니다."]
            },
            "reading": {
                "title": "API 키 없이 예시로 생성된 지문",
                "text": "이것은 API 키가 없을 때 제공되는 예시 텍스트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            },
            "default": {
                "script": "이것은 API 키가 없을 때 제공되는 예시 스크립트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            }
        }
        
        # 콘텐츠 타입에 따라 필드 추가
        if "dialogue" in content_type:
            mock_content.update(type_specific_fields["dialogue"])
        elif "reading" in content_type:
            mock_content.update(type_specific_fields["reading"])
        else:
            mock_content.update(type_specific_fields["default"])
        
        return mock_content