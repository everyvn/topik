"""
콘텐츠 저장 서비스
"""

import json
import os
import shutil
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
from pathlib import Path

from app.config import CONFIRM_FILE, DATA_DIR
from app.utils.logger import logger


class ContentStorage:
    """
    콘텐츠 데이터를 관리하는 저장소 서비스
    """
    
    def __init__(self, file_path: Optional[str] = None, trash_path: Optional[str] = None):
        """
        ContentStorage 초기화
        
        Args:
            file_path: 데이터 저장 파일 경로 (기본값: config의 CONFIRM_FILE)
            trash_path: 휴지통 파일 경로 (기본값: DATA_DIR/trash.json)
        """
        self.file_path = file_path or CONFIRM_FILE
        self.trash_path = trash_path or os.path.join(DATA_DIR, "trash.json")
        self.data = self.load()
        self.trash_data = self.load_trash()
        
        # 백업 디렉토리 설정
        self.backup_dir = os.path.join(DATA_DIR, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
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
                self._backup_corrupted_file(self.file_path)
                # 새 빈 파일 생성
                self._create_empty_json_file(self.file_path)
            except Exception as e:
                logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
        else:
            logger.info(f"'{self.file_path}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
            # 빈 파일 생성
            self._create_empty_json_file(self.file_path)
        
        return data
    
    def load_trash(self) -> List[Dict[str, Any]]:
        """
        휴지통 데이터를 로드합니다.
        
        Returns:
            휴지통에 있는 콘텐츠 데이터 리스트
        """
        data = []
        
        # 파일이 위치할 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(self.trash_path), exist_ok=True)
        
        if os.path.exists(self.trash_path):
            try:
                with open(self.trash_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                    else:
                        logger.info(f"'{self.trash_path}' 파일이 비어 있습니다.")
                        return []
                
                logger.info(f"'{self.trash_path}'에서 {len(data)}개의 휴지통 항목을 로드했습니다.")
            except json.JSONDecodeError as e:
                logger.error(f"'{self.trash_path}' 파일의 JSON 형식이 올바르지 않습니다: {e}")
                # 손상된 파일 백업
                self._backup_corrupted_file(self.trash_path)
                # 새 빈 파일 생성
                self._create_empty_json_file(self.trash_path)
            except Exception as e:
                logger.error(f"휴지통 데이터 로드 중 오류 발생: {str(e)}")
        else:
            logger.info(f"'{self.trash_path}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
            # 빈 파일 생성
            self._create_empty_json_file(self.trash_path)
        
        return data
    
    def _backup_corrupted_file(self, file_path: str) -> None:
        """
        손상된 파일을 백업합니다.
        
        Args:
            file_path: 백업할 파일 경로
        """
        try:
            backup_file = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_file)
            logger.info(f"손상된 파일을 {backup_file}로 백업했습니다.")
        except Exception as e:
            logger.error(f"파일 백업 중 오류: {str(e)}")
    
    def _create_empty_json_file(self, file_path: str) -> None:
        """
        빈 JSON 파일을 생성합니다.
        
        Args:
            file_path: 생성할 파일 경로
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('[]')
            logger.info(f"새로운 빈 {file_path} 파일을 생성했습니다.")
        except Exception as e:
            logger.error(f"빈 파일 생성 중 오류: {str(e)}")
    
    def _save_to_file(self, data: List[Dict[str, Any]], file_path: Optional[str] = None) -> bool:
        """
        데이터를 파일에 저장합니다.
        
        Args:
            data: 저장할 데이터
            file_path: 저장할 파일 경로 (기본값: self.file_path)
            
        Returns:
            저장 성공 여부
        """
        if file_path is None:
            file_path = self.file_path
            
        try:
            # 파일이 위치할 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(data)}개의 콘텐츠를 '{file_path}'에 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생 ({file_path}): {str(e)}")
            return False
    
    def save(self) -> bool:
        """
        현재 메모리에 있는 데이터를 파일에 저장합니다.
        
        Returns:
            저장 성공 여부
        """
        # 자동 백업 생성
        self._create_auto_backup()
        return self._save_to_file(self.data)
    
    def save_trash(self) -> bool:
        """
        현재 메모리에 있는, 휴지통 데이터를 파일에 저장합니다.
        
        Returns:
            저장 성공 여부
        """
        return self._save_to_file(self.trash_data, self.trash_path)
    
    def _create_auto_backup(self) -> None:
        """정기적인 자동 백업을 생성합니다."""
        try:
            # 하루에 한 번만 백업 생성 (이미 오늘 백업이 있으면 생성하지 않음)
            today = datetime.now().strftime('%Y%m%d')
            existing_backups = [f for f in os.listdir(self.backup_dir) if f.startswith(f"auto_backup_{today}")]
            
            if not existing_backups:
                backup_file = os.path.join(self.backup_dir, f"auto_backup_{today}_{datetime.now().strftime('%H%M%S')}.json")
                self._save_to_file(self.data, backup_file)
                logger.info(f"자동 백업 생성 완료: {os.path.basename(backup_file)}")
                
                # 오래된 백업 정리 (최대 30개 유지)
                self._cleanup_old_backups()
        except Exception as e:
            logger.error(f"자동 백업 생성 중 오류: {str(e)}")
    
    def _cleanup_old_backups(self, max_backups: int = 30) -> None:
        """
        오래된 백업 파일을 정리합니다.
        
        Args:
            max_backups: 유지할 최대 백업 파일 수
        """
        try:
            backup_files = [os.path.join(self.backup_dir, f) for f in os.listdir(self.backup_dir) if f.startswith("auto_backup_")]
            
            # 백업 파일이 최대 개수를 초과하면 오래된 것부터 삭제
            if len(backup_files) > max_backups:
                # 수정 시간으로 정렬
                backup_files.sort(key=lambda x: os.path.getmtime(x))
                
                # 오래된 파일 삭제
                for old_file in backup_files[:(len(backup_files) - max_backups)]:
                    os.remove(old_file)
                    logger.info(f"오래된 백업 파일 삭제: {os.path.basename(old_file)}")
        except Exception as e:
            logger.error(f"오래된 백업 정리 중 오류: {str(e)}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 콘텐츠를 반환합니다.
        
        Returns:
            모든 콘텐츠 리스트
        """
        return self.data
    
    def get_trash(self) -> List[Dict[str, Any]]:
        """
        휴지통에 있는 모든 콘텐츠를 반환합니다.
        
        Returns:
            휴지통의 콘텐츠 리스트
        """
        return self.trash_data
    
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
    
    def get_trash_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        휴지통에서 ID로 특정 콘텐츠를 검색합니다.
        
        Args:
            content_id: 검색할 콘텐츠 ID
            
        Returns:
            콘텐츠 데이터 또는 None (없을 경우)
        """
        for item in self.trash_data:
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
        
        # 생성일/수정일 추가
        now = datetime.now().isoformat()
        if "created_at" not in content:
            content["created_at"] = now
        content["updated_at"] = now
            
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
                # 수정일 업데이트
                content["updated_at"] = datetime.now().isoformat()
                # 생성일 보존
                if "created_at" in item and "created_at" not in content:
                    content["created_at"] = item["created_at"]
                
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
        특정 콘텐츠를 영구적으로 삭제합니다.
        
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
                
        # 휴지통에서도 찾아보기
        for i, item in enumerate(self.trash_data):
            if isinstance(item, dict) and item.get("id") == content_id:
                self.trash_data.pop(i)
                self.save_trash()
                return True
        
        logger.warning(f"삭제할 콘텐츠를 찾을 수 없음: {content_id}")
        return False
    
    def move_to_trash(self, content_id: str) -> bool:
        """
        특정 콘텐츠를 휴지통으로 이동합니다.
        
        Args:
            content_id: 이동할 콘텐츠 ID
            
        Returns:
            이동 성공 여부
        """
        for i, item in enumerate(self.data):
            if isinstance(item, dict) and item.get("id") == content_id:
                # 휴지통으로 이동 시간 추가
                item["trashed_at"] = datetime.now().isoformat()
                
                # 휴지통으로 이동
                self.trash_data.append(item)
                self.save_trash()
                
                # 원본 삭제
                self.data.pop(i)
                self.save()
                
                logger.info(f"콘텐츠를 휴지통으로 이동: {content_id}")
                return True
                
        logger.warning(f"휴지통으로 이동할 콘텐츠를 찾을 수 없음: {content_id}")
        return False
    
    def restore_from_trash(self, content_id: str) -> bool:
        """
        휴지통에서 콘텐츠를 복원합니다.
        
        Args:
            content_id: 복원할 콘텐츠 ID
            
        Returns:
            복원 성공 여부
        """
        for i, item in enumerate(self.trash_data):
            if isinstance(item, dict) and item.get("id") == content_id:
                # 휴지통 정보 제거
                if "trashed_at" in item:
                    del item["trashed_at"]
                
                # 복원 시간 업데이트
                item["restored_at"] = datetime.now().isoformat()
                item["updated_at"] = datetime.now().isoformat()
                
                # 원본으로 복원
                self.data.append(item)
                self.save()
                
                # 휴지통에서 제거
                self.trash_data.pop(i)
                self.save_trash()
                
                logger.info(f"콘텐츠를 휴지통에서 복원: {content_id}")
                return True
                
        logger.warning(f"복원할 콘텐츠를 휴지통에서 찾을 수 없음: {content_id}")
        return False
    
    def create_manual_backup(self) -> str:
        """
        수동 백업을 생성합니다.
        
        Returns:
            생성된 백업 파일 경로
        """
        backup_file = os.path.join(self.backup_dir, f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if self._save_to_file(self.data, backup_file):
            logger.info(f"수동 백업 생성 완료: {os.path.basename(backup_file)}")
            return backup_file
        else:
            raise RuntimeError("백업 생성 실패")
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 백업 목록을 반환합니다.
        
        Returns:
            백업 정보 목록 (파일명, 생성일, 크기 등)
        """
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json') and ('backup' in filename):
                    file_path = os.path.join(self.backup_dir, filename)
                    
                    try:
                        # 백업 정보 수집
                        stat = os.stat(file_path)
                        created_time = datetime.fromtimestamp(stat.st_mtime)
                        size_kb = stat.st_size / 1024
                        
                        # 백업 내용 미리보기
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            try:
                                data = json.loads(content)
                                item_count = len(data) if isinstance(data, list) else 0
                            except:
                                item_count = -1  # 파싱 실패
                        
                        backups.append({
                            "filename": filename,
                            "path": file_path,
                            "created_at": created_time.isoformat(),
                            "size_kb": round(size_kb, 2),
                            "item_count": item_count,
                            "type": "자동" if filename.startswith("auto_backup_") else "수동"
                        })
                    except Exception as e:
                        logger.error(f"백업 파일 처리 중 오류 ({filename}): {str(e)}")
                        continue
            
            # 최신 순으로 정렬
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"백업 목록 조회 중 오류: {str(e)}")
            return []
    
    def restore_from_backup(self, backup_data: List[Dict[str, Any]]) -> int:
        """
        백업 데이터로부터 복원합니다.
        
        Args:
            backup_data: 복원할 백업 데이터
            
        Returns:
            복원된 항목 수
        """
        if not isinstance(backup_data, list):
            raise ValueError("백업 데이터는 리스트 형식이어야 합니다.")
        
        # 현재 데이터 백업
        current_backup_file = os.path.join(self.backup_dir, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        self._save_to_file(self.data, current_backup_file)
        logger.info(f"복원 전 현재 데이터 백업 완료: {os.path.basename(current_backup_file)}")
        
        # 유효한 항목만 필터링
        valid_items = []
        for item in backup_data:
            if isinstance(item, dict) and "type" in item:
                # ID가 없으면 생성
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                    
                # 복원 정보 추가
                item["restored_from_backup"] = True
                item["restored_at"] = datetime.now().isoformat()
                
                valid_items.append(item)
        
        # 데이터 교체 및 저장
        self.data = valid_items
        self.save()
        
        return len(valid_items)