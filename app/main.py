"""
FastAPI 애플리케이션 및 라우팅
"""

import json
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.services import ContentGenerator, ContentStorage
from app.utils.logger import logger


# FastAPI 애플리케이션 설정
app = FastAPI(title="TOPIK 문제 생성기")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 서비스 초기화
content_generator = ContentGenerator()
content_storage = ContentStorage()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """메인 페이지를 표시합니다."""
    return templates.TemplateResponse("generator.html", {"request": request, "content": None})


@app.post("/generate", response_class=HTMLResponse)
def generate_content(request: Request, qtype: str = Form(...), level: str = Form(...)):
    """선택한 유형과 레벨에 따라 콘텐츠를 생성합니다."""
    try:
        content_data = content_generator.generate(qtype, level)
        
        # JSON 문자열로 변환
        raw_content = json.dumps(content_data, ensure_ascii=False)
        logger.info(f"콘텐츠 생성 완료: {qtype} / {level}")
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "content": raw_content,
            "parsed": content_data
        })
    except Exception as e:
        logger.error(f"콘텐츠 생성 라우트 처리 중 오류: {str(e)}")
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 콘텐츠 생성 중 오류가 발생했습니다: {str(e)}",
            "content": None
        })


@app.post("/regenerate", response_class=HTMLResponse)
def regenerate_content(request: Request, content: str = Form(...), user_comment: str = Form(...)):
    """사용자 코멘트를 반영하여 콘텐츠를 재생성합니다."""
    try:
        logger.info(f"콘텐츠 재생성 요청: 코멘트 길이 {len(user_comment)}")
        logger.info(f"재생성 콘텐츠 데이터 타입: {type(content)}")
        
        # 문자열에서 JSON 파싱
        if isinstance(content, str):
            # 따옴표로 이스케이프된 경우 처리
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1].replace('\\"', '"')
                
            content_data = json.loads(content)
            
            if not isinstance(content_data, dict):
                raise ValueError(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(content_data)}")
            
            # 재생성 요청
            regenerated_data = content_generator.regenerate(content_data, user_comment)
            
            # JSON 문자열로 변환
            raw_regenerated = json.dumps(regenerated_data, ensure_ascii=False)
            logger.info(f"콘텐츠 재생성 완료: {regenerated_data.get('type')} / {regenerated_data.get('level')}")
            
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "content": raw_regenerated,
                "parsed": regenerated_data,
                "user_comment": user_comment
            })
        else:
            raise ValueError(f"콘텐츠 데이터가 문자열이 아닙니다: {type(content)}")
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류 (재생성): {str(e)}, 받은 데이터: {content[:150]}...")
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 재생성 실패: 유효하지 않은 JSON 형식입니다 - {str(e)}",
            "content": content,
            "user_comment": user_comment
        })
    except Exception as e:
        logger.error(f"콘텐츠 재생성 중 오류: {str(e)}")
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 재생성 실패: {str(e)}",
            "content": content,
            "user_comment": user_comment
        })


@app.post("/confirm", response_class=HTMLResponse)
def confirm_content(request: Request, content: str = Form(...)):
    """편집된 콘텐츠를 확인하고 저장합니다."""
    logger.info(f"confirm 데이터 타입: {type(content)}")
    logger.info(f"confirm 데이터 앞부분: {content[:150]}..." if len(content) > 150 else content)
    
    try:
        if not content or content.isspace():
            raise ValueError("빈 콘텐츠가 전송되었습니다.")
            
        # 문자열에서 JSON 파싱
        # content가 따옴표로 이스케이프된 경우 처리
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1].replace('\\"', '"')
            
        parsed = json.loads(content)
        
        if not isinstance(parsed, dict):
            raise ValueError(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(parsed)}")
        
        # 저장
        content_id = content_storage.save_content(parsed)
        logger.info(f"콘텐츠 저장 완료: {content_id}")
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": "✅ 저장 완료! 콘텐츠가 성공적으로 저장되었습니다.",
            "content": None
        })
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}, 받은 데이터: {content[:150]}...")
        
        # 비상 처리 시도
        try:
            # content가 문자열이더라도 직접 파싱 시도
            if isinstance(content, str):
                parsed_data = json.loads(content)
                logger.info(f"비상 처리 - 파싱 성공, 데이터 타입: {type(parsed_data)}")
                
                # 정상적으로 파싱되면 여기서 저장 시도
                if isinstance(parsed_data, dict):
                    content_id = content_storage.save_content(parsed_data)
                    logger.info(f"비상 처리로 콘텐츠 저장 완료: {content_id}")
                    
                    return templates.TemplateResponse("generator.html", {
                        "request": request,
                        "message": "✅ 비상 처리를 통해 저장에 성공했습니다.",
                        "content": None
                    })
        except Exception as inner_e:
            logger.error(f"비상 처리 중 추가 오류: {str(inner_e)}")
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 저장 실패: 유효하지 않은 JSON 형식입니다 - {str(e)}",
            "content": content
        })
    except Exception as e:
        logger.error(f"콘텐츠 저장 중 오류: {str(e)}")
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 저장 실패: {str(e)}",
            "content": content
        })


@app.get("/confirmed", response_class=HTMLResponse)
def show_confirmed(request: Request):
    """저장된 모든 콘텐츠를 표시합니다."""
    # 최신 데이터 로드
    data = content_storage.load()
    
    logger.info(f"저장된 콘텐츠 페이지 로드: {len(data)}개 항목")
    return templates.TemplateResponse("confirmed.html", {
        "request": request,
        "data": data
    })


@app.get("/content/{content_id}", response_class=HTMLResponse)
def get_content(request: Request, content_id: str):
    """특정 콘텐츠의 상세 정보를 표시합니다."""
    item = content_storage.get_by_id(content_id)
    
    if not item:
        logger.warning(f"존재하지 않는 콘텐츠 ID: {content_id}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "요청한 콘텐츠를 찾을 수 없습니다."
        })
    
    logger.info(f"콘텐츠 상세 보기: {content_id}")
    return templates.TemplateResponse("content_detail.html", {
        "request": request,
        "item": item
    })


@app.get("/delete/{content_id}")
def delete_content(request: Request, content_id: str):
    """특정 콘텐츠를 삭제합니다."""
    try:
        if content_storage.delete(content_id):
            logger.info(f"콘텐츠 삭제 성공: {content_id}")
            return RedirectResponse(url="/confirmed", status_code=303)
        else:
            logger.warning(f"삭제할 콘텐츠를 찾을 수 없음: {content_id}")
            return templates.TemplateResponse("error.html", {
                "request": request,
                "message": "삭제할 콘텐츠를 찾을 수 없습니다."
            })
    except Exception as e:
        logger.error(f"콘텐츠 삭제 중 오류: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"콘텐츠 삭제 중 오류가 발생했습니다: {str(e)}"
        })