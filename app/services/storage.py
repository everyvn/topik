"""
콘텐츠 저장 서비스
"""

import json
import os
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

from app.config import CONFIRM_FILE
from app.utils.logger import logger


class ContentStorage:
    """
    콘텐츠 데이터를 관리하는 저장소 서비스
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        ContentStorage 초기화
        
        Args:
            file_path: 데이터 저장 파일 경로 (기본값: config의 CONFIRM_FILE)
        """
        self.file_path = file_path or CONFIRM_FILE
        self.data = self.load()
        
    def load(self) -> List[Dict[str, Any]]:
        """
        저장된 콘텐츠 데이터를 로드합니다.
        
        Returns:
            로드된 콘텐츠 데이터 리스트
        """
        data = []
        
        # 파일이 위치할 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                    else:
                        logger.warning(f"'{self.file_path}' 파일이 비어 있습니다.")
                        return []
                
                logger.info(f"'{self.file_path}'에서 {len(data)}개의 콘텐츠를 로드했습니다.")
                
                # 데이터 유효성 검사
                valid_data = []
                for item in data:
                    if isinstance(item, dict) and 'type' in item:
                        valid_data.append(item)
                    else:
                        logger.warning(f"유효하지 않은 데이터 항목 발견: {item}")
                
                if len(valid_data) != len(data):
                    logger.warning(f"{len(data) - len(valid_data)}개의 유효하지 않은 항목이 제외되었습니다.")
                    data = valid_data
                    
                    # 유효하지 않은 항목이 있었다면 파일 다시 저장
                    self._save_to_file(data)
                    logger.info("유효한 데이터만 다시 파일에 저장했습니다.")
                    
            except json.JSONDecodeError as e:
                logger.error(f"'{self.file_path}' 파일의 JSON 형식이 올바르지 않습니다: {e}")
                # 손상된 파일 백업
                backup_file = f"{self.file_path}.bak"
                try:
                    os.rename(self.file_path, backup_file)
                    logger.info(f"손상된 파일을 {backup_file}로 백업했습니다.")
                    # 새 빈 파일 생성
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        f.write('[]')
                    logger.info(f"새로운 빈 {self.file_path} 파일을 생성했습니다.")
                except Exception as e:
                    logger.error(f"파일 백업 중 오류: {e}")
            except Exception as e:
                logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
        else:
            logger.info(f"'{self.file_path}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
            # 빈 파일 생성
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write('[]')
            logger.info(f"새로운 빈 {self.file_path} 파일을 생성했습니다.")
        
        return data
    
    def _save_to_file(self, data: List[Dict[str, Any]]) -> bool:
        """
        데이터를 파일에 저장합니다.
        
        Args:
            data: 저장할 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            # 파일이 위치할 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(data)}개의 콘텐츠를 '{self.file_path}'에 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
            return False
    
    def save(self) -> bool:
        """
        현재 메모리에 있는 데이터를 파일에 저장합니다.
        
        Returns:
            저장 성공 여부
        """
        return self._save_to_file(self.data)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 콘텐츠를 반환합니다.
        
        Returns:
            모든 콘텐츠 리스트
        """
        return self.data
    
    def get_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 특정 콘텐츠를 검색합니다.
        
        Args:
            content_id: 검색할 콘텐츠 ID
            
        Returns:
            콘텐츠 데이터 또는 None (없을 경우)
        """
        for item in self.data:
            if isinstance(item, dict) and item.get("id") == content_id:
                return item
        return None
    
    def add(self, content: Dict[str, Any]) -> str:
        """
        새 콘텐츠를 추가합니다.
        
        Args:
            content: 추가할 콘텐츠 데이터
            
        Returns:
            추가된 콘텐츠의 ID
        """
        # ID가 없으면 생성
        if "id" not in content:
            content["id"] = str(uuid.uuid4())
            
        self.data.append(content)
        self.save()
        return content["id"]
    
    def update(self, content: Dict[str, Any]) -> bool:
        """
        기존 콘텐츠를 업데이트합니다.
        
        Args:
            content: 업데이트할 콘텐츠 데이터 (id 포함)
            
        Returns:
            업데이트 성공 여부
        """
        if "id" not in content:
            logger.error("업데이트할 콘텐츠에 ID가 없습니다.")
            return False
            
        content_id = content["id"]
        
        for i, item in enumerate(self.data):
            if isinstance(item, dict) and item.get("id") == content_id:
                self.data[i] = content
                self.save()
                return True
                
        logger.warning(f"업데이트할 콘텐츠를 찾을 수 없음: {content_id}")
        return False
    
    def save_content(self, content: Dict[str, Any]) -> str:
        """
        콘텐츠를 저장합니다. (기존 항목 업데이트 또는 새 항목 추가)
        
        Args:
            content: 저장할 콘텐츠 데이터
            
        Returns:
            저장된 콘텐츠의 ID
        """
        if "id" in content and self.get_by_id(content["id"]):
            self.update(content)
            return content["id"]
        else:
            return self.add(content)
    
    def delete(self, content_id: str) -> bool:
        """
        특정 콘텐츠를 삭제합니다.
        
        Args:
            content_id: 삭제할 콘텐츠 ID
            
        Returns:
            삭제 성공 여부
        """
        for i, item in enumerate(self.data):
            if isinstance(item, dict) and item.get("id") == content_id:
                self.data.pop(i)
                self.save()
                return True
                
        logger.warning(f"삭제할 콘텐츠를 찾을 수 없음: {content_id}")
        return False