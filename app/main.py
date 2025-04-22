"""
FastAPI 애플리케이션 및 라우팅

TOPIK 문제 생성기의 웹 인터페이스와 API 엔드포인트를 정의합니다.
"""

import json
import re
import functools
from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional, List, Callable

from app.config import AppConfig
from app.services import create_content_generator, create_content_storage
from app.utils.logger import logger
from app.utils.json_debug import safely_parse_json


# 서비스 인스턴스를 생성하는 의존성 함수
def get_content_generator():
    """ContentGenerator 인스턴스를 제공하는 의존성 함수"""
    return create_content_generator()

def get_content_storage():
    """ContentStorage 인스턴스를 제공하는 의존성 함수"""
    return create_content_storage()


# 라우트 오류 처리 데코레이터
def handle_route_errors(func):
    """라우트 함수의 오류를 처리하는 데코레이터"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"값 오류: {str(e)}")
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            return templates.TemplateResponse(
                "generator.html", 
                {
                    "request": request,
                    "message": f"❌ 처리 실패: {str(e)}",
                    "content": None
                },
                status_code=400
            )
        except Exception as e:
            logger.error(f"처리 중 예외 발생: {str(e)}")
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            return templates.TemplateResponse(
                "generator.html", 
                {
                    "request": request,
                    "message": f"❌ 서버 오류: {str(e)}",
                    "content": None
                },
                status_code=500
            )
    return wrapper


# FastAPI 애플리케이션 설정
app = FastAPI(
    title="TOPIK 문제 생성기",
    description="한국어 능력 시험(TOPIK) 문제를 자동으로 생성하는 애플리케이션",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지를 표시합니다."""
    return templates.TemplateResponse("generator.html", {"request": request, "content": None})


@app.post("/generate", response_class=HTMLResponse)
@handle_route_errors
async def generate_content(
    request: Request, 
    qtype: str = Form(...), 
    level: str = Form(...),
    generator = Depends(get_content_generator)
):
    """
    선택한 유형과 레벨에 따라 콘텐츠를 생성합니다.
    
    Args:
        request: FastAPI 요청 객체
        qtype: 콘텐츠 유형 (dialogue, lecture 등)
        level: 학습자 레벨 (초급, 중급, 고급 등)
        generator: ContentGenerator 인스턴스 (의존성 주입)
    """
    logger.info(f"콘텐츠 생성 요청: {qtype} / {level}")
    
    # 콘텐츠 생성
    content_data = generator.generate(qtype, level)
    
    # JSON 문자열로 변환
    raw_content = json.dumps(content_data, ensure_ascii=False)
    logger.info(f"콘텐츠 생성 완료: {qtype} / {level}")
    
    return templates.TemplateResponse(
        "generator.html", 
        {
            "request": request,
            "content": raw_content,
            "parsed": content_data
        }
    )


@app.post("/regenerate", response_class=HTMLResponse)
@handle_route_errors
async def regenerate_content(
    request: Request, 
    content: str = Form(...), 
    user_comment: str = Form(...),
    generator = Depends(get_content_generator)
):
    """
    사용자 코멘트를 반영하여 콘텐츠를 재생성합니다.
    
    Args:
        request: FastAPI 요청 객체
        content: 원본 콘텐츠 JSON
        user_comment: 사용자의 추가 요구사항
        generator: ContentGenerator 인스턴스 (의존성 주입)
    """
    logger.info(f"콘텐츠 재생성 요청: 코멘트 길이 {len(user_comment)}")
    
    # 입력 데이터 유효성 검사
    if not content or content.isspace():
        raise ValueError("콘텐츠 데이터가 비어있습니다.")
    
    # 콘텐츠 파싱
    content_data = safely_parse_json(content)
    
    # 재생성 요청
    regenerated_data = generator.regenerate(content_data, user_comment)
    
    # JSON 문자열로 변환
    raw_regenerated = json.dumps(regenerated_data, ensure_ascii=False)
    logger.info(f"콘텐츠 재생성 완료: {regenerated_data.get('type')} / {regenerated_data.get('level')}")
    
    return templates.TemplateResponse(
        "generator.html", 
        {
            "request": request,
            "content": raw_regenerated,
            "parsed": regenerated_data,
            "user_comment": user_comment
        }
    )


@app.post("/confirm", response_class=HTMLResponse)
@handle_route_errors
async def confirm_content(
    request: Request, 
    content: str = Form(...),
    storage = Depends(get_content_storage)
):
    """
    편집된 콘텐츠를 확인하고 저장합니다.
    
    Args:
        request: FastAPI 요청 객체
        content: 저장할 콘텐츠 JSON
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    logger.info(f"콘텐츠 저장 요청: 데이터 길이 {len(content)}")
    
    # 입력 데이터 유효성 검사
    if not content or content.isspace():
        raise ValueError("빈 콘텐츠가 전송되었습니다.")
    
    # 콘텐츠 파싱
    parsed = safely_parse_json(content)
    
    # 저장
    content_id = storage.save_content(parsed)
    logger.info(f"콘텐츠 저장 완료: {content_id}")
    
    return templates.TemplateResponse(
        "generator.html", 
        {
            "request": request,
            "message": "✅ 저장 완료! 콘텐츠가 성공적으로 저장되었습니다.",
            "content": None
        }
    )


@app.get("/confirmed", response_class=HTMLResponse)
@handle_route_errors
async def show_confirmed(
    request: Request,
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    level_filter: Optional[str] = None,
    storage = Depends(get_content_storage)
):
    """
    저장된 모든 콘텐츠를 표시합니다.
    
    Args:
        request: FastAPI 요청 객체
        search: 검색어 (선택 사항)
        type_filter: 콘텐츠 유형 필터 (선택 사항)
        level_filter: 콘텐츠 레벨 필터 (선택 사항)
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    # 콘텐츠 검색
    data = storage.search_contents(search, type_filter, level_filter)
    
    # 사용 가능한 유형 및 레벨 목록 수집
    types = set()
    levels = set()
    for item in storage.get_all():
        if isinstance(item, dict):
            if "type" in item and item["type"]:
                types.add(item["type"])
            if "level" in item and item["level"]:
                levels.add(item["level"])
    
    logger.info(f"저장된 콘텐츠 페이지 로드: {len(data)}개 항목")
    return templates.TemplateResponse(
        "confirmed.html", 
        {
            "request": request,
            "data": data,
            "search": search,
            "type_filter": type_filter,
            "level_filter": level_filter,
            "types": sorted(types),
            "levels": sorted(levels)
        }
    )


@app.get("/content/{content_id}", response_class=HTMLResponse)
@handle_route_errors
async def get_content(
    request: Request, 
    content_id: str,
    storage = Depends(get_content_storage)
):
    """
    특정 콘텐츠의 상세 정보를 표시합니다.
    
    Args:
        request: FastAPI 요청 객체
        content_id: 콘텐츠 ID
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    item = storage.get_by_id(content_id)
    
    if not item:
        logger.warning(f"존재하지 않는 콘텐츠 ID: {content_id}")
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "message": "요청한 콘텐츠를 찾을 수 없습니다."
            },
            status_code=404
        )
    
    logger.info(f"콘텐츠 상세 보기: {content_id}")
    return templates.TemplateResponse(
        "content_detail.html", 
        {
            "request": request,
            "item": item
        }
    )


@app.get("/delete/{content_id}")
@handle_route_errors
async def delete_content(
    request: Request, 
    content_id: str,
    storage = Depends(get_content_storage)
):
    """
    특정 콘텐츠를 삭제합니다.
    
    Args:
        request: FastAPI 요청 객체
        content_id: 삭제할 콘텐츠 ID
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    if storage.delete(content_id):
        logger.info(f"콘텐츠 삭제 성공: {content_id}")
        return RedirectResponse(url="/confirmed", status_code=303)
    else:
        logger.warning(f"삭제할 콘텐츠를 찾을 수 없음: {content_id}")
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "message": "삭제할 콘텐츠를 찾을 수 없습니다."
            },
            status_code=404
        )


@app.get("/trash/{content_id}")
@handle_route_errors
async def trash_content(
    request: Request, 
    content_id: str,
    storage = Depends(get_content_storage)
):
    """
    특정 콘텐츠를 휴지통으로 이동합니다.
    
    Args:
        request: FastAPI 요청 객체
        content_id: 이동할 콘텐츠 ID
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    if storage.trash(content_id):
        logger.info(f"콘텐츠 휴지통 이동 성공: {content_id}")
        return RedirectResponse(url="/confirmed", status_code=303)
    else:
        logger.warning(f"휴지통으로 이동할 콘텐츠를 찾을 수 없음: {content_id}")
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "message": "휴지통으로 이동할 콘텐츠를 찾을 수 없습니다."
            },
            status_code=404
        )


@app.get("/trash")
@handle_route_errors
async def show_trash(
    request: Request,
    storage = Depends(get_content_storage)
):
    """
    휴지통의 콘텐츠를 표시합니다.
    
    Args:
        request: FastAPI 요청 객체
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    data = storage.get_trash()
    
    logger.info(f"휴지통 페이지 로드: {len(data)}개 항목")
    return templates.TemplateResponse(
        "trash.html", 
        {
            "request": request,
            "data": data
        }
    )


@app.get("/restore/{content_id}")
@handle_route_errors
async def restore_content(
    request: Request, 
    content_id: str,
    storage = Depends(get_content_storage)
):
    """
    휴지통에서 콘텐츠를 복원합니다.
    
    Args:
        request: FastAPI 요청 객체
        content_id: 복원할 콘텐츠 ID
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    if storage.restore(content_id):
        logger.info(f"콘텐츠 복원 성공: {content_id}")
        return RedirectResponse(url="/trash", status_code=303)
    else:
        logger.warning(f"복원할 콘텐츠를 찾을 수 없음: {content_id}")
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "message": "복원할 콘텐츠를 찾을 수 없습니다."
            },
            status_code=404
        )


@app.get("/empty-trash")
@handle_route_errors
async def empty_trash(
    request: Request,
    storage = Depends(get_content_storage)
):
    """
    휴지통을 비웁니다.
    
    Args:
        request: FastAPI 요청 객체
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    count = storage.empty_trash()
    logger.info(f"휴지통 비우기 완료: {count}개 항목 삭제")
    
    return RedirectResponse(url="/trash", status_code=303)


@app.get("/backup")
@handle_route_errors
async def backup_data(
    request: Request,
    storage = Depends(get_content_storage)
):
    """
    데이터 백업을 생성하고 다운로드합니다.
    
    Args:
        request: FastAPI 요청 객체
        storage: ContentStorage 인스턴스 (의존성 주입)
    """
    from fastapi.responses import FileResponse
    import os
    
    # 수동 백업 생성
    backup_path = storage.create_manual_backup(storage.get_all())
    
    if not backup_path or not os.path.exists(backup_path):
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "message": "백업 파일 생성에 실패했습니다."
            },
            status_code=500
        )
    
    logger.info(f"데이터 백업 다운로드: {os.path.basename(backup_path)}")
    return FileResponse(
        path=backup_path,
        filename=os.path.basename(backup_path),
        media_type="application/json"
    )