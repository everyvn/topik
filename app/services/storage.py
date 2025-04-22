"""
콘텐츠 저장 서비스

생성된 콘텐츠를 관리하는 저장소 서비스를 제공합니다.
파일 기반으로 콘텐츠를 저장, 검색, 수정, 삭제할 수 있습니다.
"""

import json
import os
import shutil
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
from datetime import datetime
from pathlib import Path

from app.config import Files, Directories, AppConfig
from app.utils.logger import get_logger
from app.utils.json_debug import safely_parse_json

# 모듈 로거 설정
logger = get_logger("storage")


class BaseStorage:
    """기본 저장소 클래스"""
    
    def __init__(self, file_path: Path):
        """
        BaseStorage 초기화
        
        Args:
            file_path: 데이터 저장 파일 경로
        """
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """파일에서 데이터 로드"""
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
                
                logger.info(f"'{self.file_path}'에서 {len(data)}개의 항목을 로드했습니다.")
                
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
                self._backup_corrupted_file()
                # 새 빈 파일 생성
                self._create_empty_json_file()
            except Exception as e:
                logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
        else:
            logger.info(f"'{self.file_path}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
            # 빈 파일 생성
            self._create_empty_json_file()
        
        return data
    
    def _backup_corrupted_file(self) -> str:
        """
        손상된 파일을 백업합니다.
        
        Returns:
            백업 파일 경로
        """
        try:
            backup_file = f"{self.file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.file_path, backup_file)
            logger.info(f"손상된 파일을 {backup_file}로 백업했습니다.")
            return backup_file
        except Exception as e:
            logger.error(f"파일 백업 중 오류: {str(e)}")
            return ""
    
    def _create_empty_json_file(self) -> bool:
        """
        빈 JSON 파일을 생성합니다.
        
        Returns:
            성공 여부
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write('[]')
            logger.info(f"새로운 빈 {self.file_path} 파일을 생성했습니다.")
            return True
        except Exception as e:
            logger.error(f"빈 파일 생성 중 오류: {str(e)}")
            return False
    
    def _save_to_file(self, data: List[Dict[str, Any]], file_path: Optional[Path] = None) -> bool:
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
            logger.info(f"{len(data)}개의 항목을 '{file_path}'에 저장했습니다.")
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
        return self._save_to_file(self.data)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 항목을 반환합니다.
        
        Returns:
            모든 항목 리스트
        """
        return self.data
    
    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 특정 항목을 검색합니다.
        
        Args:
            item_id: 검색할 항목 ID
            
        Returns:
            항목 데이터 또는 None (없을 경우)
        """
        for item in self.data:
            if isinstance(item, dict) and item.get("id") == item_id:
                return item
        return None
    
    def add(self, item: Dict[str, Any]) -> str:
        """
        새 항목을 추가합니다.
        
        Args:
            item: 추가할 항목 데이터
            
        Returns:
            추가된 항목의 ID
        """
        # ID가 없으면 생성
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        
        # 생성일/수정일 추가
        now = datetime.now().isoformat()
        if "created_at" not in item:
            item["created_at"] = now
        item["updated_at"] = now
            
        self.data.append(item)
        self.save()
        return item["id"]
    
    def update(self, item: Dict[str, Any]) -> bool:
        """
        기존 항목을 업데이트합니다.
        
        Args:
            item: 업데이트할 항목 데이터 (id 포함)
            
        Returns:
            업데이트 성공 여부
        """
        if "id" not in item:
            logger.error("업데이트할 항목에 ID가 없습니다.")
            return False
            
        item_id = item["id"]
        
        for i, existing_item in enumerate(self.data):
            if isinstance(existing_item, dict) and existing_item.get("id") == item_id:
                # 수정일 업데이트
                item["updated_at"] = datetime.now().isoformat()
                # 생성일 보존
                if "created_at" in existing_item and "created_at" not in item:
                    item["created_at"] = existing_item["created_at"]
                
                self.data[i] = item
                self.save()
                return True
                
        logger.warning(f"업데이트할 항목을 찾을 수 없음: {item_id}")
        return False
    
    def delete(self, item_id: str) -> bool:
        """
        특정 항목을 삭제합니다.
        
        Args:
            item_id: 삭제할 항목 ID
            
        Returns:
            삭제 성공 여부
        """
        for i, item in enumerate(self.data):
            if isinstance(item, dict) and item.get("id") == item_id:
                self.data.pop(i)
                self.save()
                return True
                
        logger.warning(f"삭제할 항목을 찾을 수 없음: {item_id}")
        return False
        
    def filter(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        조건에 맞는 항목을 필터링합니다.
        
        Args:
            criteria: 필터링 조건 (키-값 쌍)
            
        Returns:
            조건에 맞는 항목 리스트
        """
        filtered = []
        
        for item in self.data:
            if not isinstance(item, dict):
                continue
                
            match = True
            for key, value in criteria.items():
                if key not in item or item[key] != value:
                    match = False
                    break
                    
            if match:
                filtered.append(item)
                
        return filtered
        
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        텍스트 검색을 수행합니다.
        
        Args:
            query: 검색어
            fields: 검색할 필드 목록 (기본값: None = 모든 텍스트 필드)
            
        Returns:
            검색 결과 항목 리스트
        """
        if not query:
            return self.data
            
        query = query.lower()
        results = []
        
        for item in self.data:
            if not isinstance(item, dict):
                continue
                
            item_matches = False
            
            # 검색할 필드 결정
            search_fields = fields if fields else [
                field for field, value in item.items() 
                if isinstance(value, (str, list)) and field not in ('id', 'created_at', 'updated_at')
            ]
            
            # 각 필드 검색
            for field in search_fields:
                if field not in item:
                    continue
                    
                value = item[field]
                
                # 문자열 필드
                if isinstance(value, str) and query in value.lower():
                    item_matches = True
                    break
                    
                # 리스트 필드 (키워드 등)
                if isinstance(value, list) and any(
                    isinstance(item, str) and query in item.lower() for item in value
                ):
                    item_matches = True
                    break
            
            if item_matches:
                results.append(item)
                
        return results


class BackupMixin:
    """백업 기능을 제공하는 믹스인"""
    
    def __init__(self, backup_dir: Path, max_backups: int = 30):
        """
        BackupMixin 초기화
        
        Args:
            backup_dir: 백업 디렉토리 경로
            max_backups: 유지할 최대 백업 수
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        
        # 백업 디렉토리 생성
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _create_auto_backup(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        자동 백업을 생성합니다.
        
        Args:
            data: 백업할 데이터
            
        Returns:
            생성된 백업 파일 경로 또는 None (실패 시)
        """
        try:
            # 하루에 한 번만 백업 생성 (이미 오늘 백업이 있으면 생성하지 않음)
            today = datetime.now().strftime('%Y%m%d')
            existing_backups = [
                f for f in os.listdir(self.backup_dir) 
                if f.startswith(f"auto_backup_{today}")
            ]
            
            if not existing_backups:
                backup_file = os.path.join(
                    self.backup_dir, 
                    f"auto_backup_{today}_{datetime.now().strftime('%H%M%S')}.json"
                )
                
                try:
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"자동 백업 생성 완료: {os.path.basename(backup_file)}")
                    
                    # 오래된 백업 정리
                    self._cleanup_old_backups()
                    
                    return backup_file
                    
                except Exception as e:
                    logger.error(f"백업 파일 생성 중 오류: {str(e)}")
                    return None
        
        except Exception as e:
            logger.error(f"자동 백업 생성 중 오류: {str(e)}")
            return None
    
    def _cleanup_old_backups(self) -> int:
        """
        오래된 백업 파일을 정리합니다.
        
        Returns:
            삭제된 백업 파일 수
        """
        try:
            backup_files = [
                os.path.join(self.backup_dir, f) 
                for f in os.listdir(self.backup_dir) 
                if f.startswith("auto_backup_")
            ]
            
            # 백업 파일이 최대 개수를 초과하면 오래된 것부터 삭제
            if len(backup_files) > self.max_backups:
                # 수정 시간으로 정렬
                backup_files.sort(key=lambda x: os.path.getmtime(x))
                
                # 오래된 파일 삭제
                delete_count = len(backup_files) - self.max_backups
                for old_file in backup_files[:delete_count]:
                    os.remove(old_file)
                    logger.info(f"오래된 백업 파일 삭제: {os.path.basename(old_file)}")
                
                return delete_count
                
            return 0
        except Exception as e:
            logger.error(f"오래된 백업 정리 중 오류: {str(e)}")
            return 0
    
    def create_manual_backup(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        수동 백업을 생성합니다.
        
        Args:
            data: 백업할 데이터
            
        Returns:
            생성된 백업 파일 경로 또는 None (실패 시)
        """
        try:
            backup_file = os.path.join(
                self.backup_dir, 
                f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"수동 백업 생성 완료: {os.path.basename(backup_file)}")
            return backup_file
            
        except Exception as e:
            logger.error(f"수동 백업 생성 중 오류: {str(e)}")
            return None
    
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
                            except json.JSONDecodeError:
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


class TrashMixin:
    """휴지통 기능을 제공하는 믹스인"""
    
    def __init__(self, trash_path: Path):
        """
        TrashMixin 초기화
        
        Args:
            trash_path: 휴지통 파일 경로
        """
        self.trash_path = trash_path
        self.trash_data = self._load_trash_data()
    
    def _load_trash_data(self) -> List[Dict[str, Any]]:
        """휴지통 데이터 로드"""
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
                backup_file = f"{self.trash_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    shutil.copy2(self.trash_path, backup_file)
                    logger.info(f"손상된 휴지통 파일을 {backup_file}로 백업했습니다.")
                except Exception as backup_err:
                    logger.error(f"휴지통 파일 백업 중 오류: {str(backup_err)}")
                
                # 새 빈 파일 생성
                try:
                    with open(self.trash_path, 'w', encoding='utf-8') as f:
                        f.write('[]')
                    logger.info(f"새로운 빈 휴지통 파일을 생성했습니다.")
                except Exception as create_err:
                    logger.error(f"빈 휴지통 파일 생성 중 오류: {str(create_err)}")
            except Exception as e:
                logger.error(f"휴지통 데이터 로드 중 오류 발생: {str(e)}")
        else:
            logger.info(f"'{self.trash_path}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
            # 빈 파일 생성
            try:
                with open(self.trash_path, 'w', encoding='utf-8') as f:
                    f.write('[]')
                logger.info(f"새로운 빈 휴지통 파일을 생성했습니다.")
            except Exception as e:
                logger.error(f"빈 휴지통 파일 생성 중 오류: {str(e)}")
        
        return data
    
    def save_trash(self) -> bool:
        """
        현재 메모리에 있는 휴지통 데이터를 파일에 저장합니다.
        
        Returns:
            저장 성공 여부
        """
        try:
            # 파일이 위치할 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(self.trash_path), exist_ok=True)
            
            with open(self.trash_path, 'w', encoding='utf-8') as f:
                json.dump(self.trash_data, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(self.trash_data)}개의 휴지통 항목을 '{self.trash_path}'에 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"휴지통 데이터 저장 중 오류: {str(e)}")
            return False
    
    def get_trash(self) -> List[Dict[str, Any]]:
        """
        휴지통에 있는 모든 항목을 반환합니다.
        
        Returns:
            휴지통의 항목 리스트
        """
        return self.trash_data
    
    def get_trash_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        휴지통에서 ID로 특정 항목을 검색합니다.
        
        Args:
            item_id: 검색할 항목 ID
            
        Returns:
            항목 데이터 또는 None (없을 경우)
        """
        for item in self.trash_data:
            if isinstance(item, dict) and item.get("id") == item_id:
                return item
        return None
    
    def move_to_trash(self, item_id: str, data: List[Dict[str, Any]]) -> bool:
        """
        특정 항목을 휴지통으로 이동합니다.
        
        Args:
            item_id: 이동할 항목 ID
            data: 현재 데이터 목록
            
        Returns:
            이동 성공 여부
        """
        for i, item in enumerate(data):
            if isinstance(item, dict) and item.get("id") == item_id:
                # 휴지통으로 이동 시간 추가
                item["trashed_at"] = datetime.now().isoformat()
                
                # 휴지통으로 이동
                self.trash_data.append(item)
                self.save_trash()
                
                # 원본 위치 반환 (삭제를 위해)
                logger.info(f"항목을 휴지통으로 이동: {item_id}")
                return True
                
        logger.warning(f"휴지통으로 이동할 항목을 찾을 수 없음: {item_id}")
        return False
    
    def restore_from_trash(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        휴지통에서 항목을 복원합니다.
        
        Args:
            item_id: 복원할 항목 ID
            
        Returns:
            복원된 항목 또는 None (실패 시)
        """
        for i, item in enumerate(self.trash_data):
            if isinstance(item, dict) and item.get("id") == item_id:
                # 휴지통 정보 제거
                if "trashed_at" in item:
                    del item["trashed_at"]
                
                # 복원 시간 업데이트
                item["restored_at"] = datetime.now().isoformat()
                item["updated_at"] = datetime.now().isoformat()
                
                # 휴지통에서 제거
                restored_item = self.trash_data.pop(i)
                self.save_trash()
                
                logger.info(f"항목을 휴지통에서 복원: {item_id}")
                return restored_item
                
        logger.warning(f"복원할 항목을 휴지통에서 찾을 수 없음: {item_id}")
        return None
    
    def empty_trash(self) -> int:
        """
        휴지통을 비웁니다.
        
        Returns:
            삭제된 항목 수
        """
        count = len(self.trash_data)
        self.trash_data = []
        self.save_trash()
        logger.info(f"휴지통 비우기 완료: {count}개 항목 삭제")
        return count
    
    def delete_from_trash(self, item_id: str) -> bool:
        """
        휴지통에서 항목을 영구 삭제합니다.
        
        Args:
            item_id: 삭제할 항목 ID
            
        Returns:
            삭제 성공 여부
        """
        for i, item in enumerate(self.trash_data):
            if isinstance(item, dict) and item.get("id") == item_id:
                self.trash_data.pop(i)
                self.save_trash()
                logger.info(f"휴지통에서 항목 영구 삭제: {item_id}")
                return True
                
        logger.warning(f"휴지통에서 삭제할 항목을 찾을 수 없음: {item_id}")
        return False


class ContentStorage(BaseStorage, BackupMixin, TrashMixin):
    """
    콘텐츠 데이터를 관리하는 저장소 서비스
    """
    
    def __init__(self, file_path: Optional[Path] = None, trash_path: Optional[Path] = None, 
                 backup_dir: Optional[Path] = None, max_backups: int = None):
        """
        ContentStorage 초기화
        
        Args:
            file_path: 데이터 저장 파일 경로 (기본값: config의 CONFIRM_FILE)
            trash_path: 휴지통 파일 경로 (기본값: DATA_DIR/trash.json)
            backup_dir: 백업 디렉토리 경로 (기본값: DATA_DIR/backups)
            max_backups: 유지할 최대 백업 수 (기본값: AppConfig.MAX_BACKUPS)
        """
        # 기본 값 설정
        self.file_path = file_path or Files.CONFIRM
        trash_path = trash_path or Files.TRASH
        backup_dir = backup_dir or Directories.BACKUPS
        max_backups = max_backups or AppConfig.MAX_BACKUPS
        
        # 부모 클래스 초기화
        BaseStorage.__init__(self, self.file_path)
        BackupMixin.__init__(self, backup_dir, max_backups)
        TrashMixin.__init__(self, trash_path)
        
        # 백업 실행 (AppConfig.AUTO_BACKUP이 True인 경우)
        if AppConfig.AUTO_BACKUP:
            self._create_auto_backup(self.data)
            
    def save(self) -> bool:
        """
        현재 메모리에 있는 데이터를 파일에 저장하고 백업을 생성합니다.
        
        Returns:
            저장 성공 여부
        """
        # 자동 백업 생성
        if AppConfig.AUTO_BACKUP:
            self._create_auto_backup(self.data)
            
        # 파일에 저장
        return BaseStorage.save(self)
    
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
    
    def trash(self, content_id: str) -> bool:
        """
        특정 콘텐츠를 휴지통으로 이동합니다.
        
        Args:
            content_id: 이동할 콘텐츠 ID
            
        Returns:
            이동 성공 여부
        """
        # 휴지통으로 이동
        if self.move_to_trash(content_id, self.data):
            # 원본 삭제
            for i, item in enumerate(self.data):
                if isinstance(item, dict) and item.get("id") == content_id:
                    self.data.pop(i)
                    self.save()
                    return True
        
        return False
    
    def restore(self, content_id: str) -> bool:
        """
        휴지통에서 콘텐츠를 복원합니다.
        
        Args:
            content_id: 복원할 콘텐츠 ID
            
        Returns:
            복원 성공 여부
        """
        restored_item = self.restore_from_trash(content_id)
        if restored_item:
            # 복원된 항목 추가
            self.data.append(restored_item)
            self.save()
            return True
        
        return False
    
    def search_contents(self, query: str = None, content_type: str = None, 
                       level: str = None) -> List[Dict[str, Any]]:
        """
        콘텐츠를 검색합니다.
        
        Args:
            query: 검색어 (기본값: None)
            content_type: 콘텐츠 유형 필터 (기본값: None)
            level: 콘텐츠 레벨 필터 (기본값: None)
            
        Returns:
            검색 결과 목록
        """
        # 기본 결과 (모든 항목)
        results = self.data
        
        # 필터 적용
        if content_type:
            results = [item for item in results if isinstance(item, dict) and item.get("type") == content_type]
            
        if level:
            results = [item for item in results if isinstance(item, dict) and item.get("level") == level]
        
        # 텍스트 검색
        if query:
            query_results = []
            query = query.lower()
            
            for item in results:
                if not isinstance(item, dict):
                    continue
                
                # 검색 필드: topic, title, situation, place, keywords
                searchable_fields = ['topic', 'title', 'situation', 'place']
                
                # 각 필드 검색
                item_matches = False
                
                # 텍스트 필드 검색
                for field in searchable_fields:
                    if field in item and isinstance(item[field], str) and query in item[field].lower():
                        item_matches = True
                        break
                
                # 키워드 검색
                if not item_matches and 'keywords' in item and isinstance(item['keywords'], list):
                    for keyword in item['keywords']:
                        if isinstance(keyword, str) and query in keyword.lower():
                            item_matches = True
                            break
                
                # 대화 검색
                if not item_matches and 'dialogue' in item and isinstance(item['dialogue'], list):
                    for line in item['dialogue']:
                        if isinstance(line, str) and query in line.lower():
                            item_matches = True
                            break
                
                # 텍스트/스크립트 검색
                if not item_matches:
                    for field in ['text', 'script']:
                        if field in item and isinstance(item[field], str) and query in item[field].lower():
                            item_matches = True
                            break
                
                if item_matches:
                    query_results.append(item)
            
            results = query_results
        
        return results
    
    def restore_from_backup(self, backup_path: str) -> Tuple[int, str]:
        """
        백업 파일에서 데이터를 복원합니다.
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            복원된 항목 수와 백업 ID
        """
        try:
            # 현재 데이터 백업
            pre_restore_backup = self.create_manual_backup(self.data)
            
            # 백업 파일 로드
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.loads(f.read())
            
            if not isinstance(backup_data, list):
                raise ValueError("백업 데이터는 리스트 형식이어야 합니다.")
            
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
            
            return len(valid_items), os.path.basename(pre_restore_backup) if pre_restore_backup else ""
            
        except Exception as e:
            logger.error(f"백업 복원 중 오류: {str(e)}")
            raise ValueError(f"백업 복원 실패: {str(e)}")