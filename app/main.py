"""
FastAPI 애플리케이션 및 라우팅
"""

import json
import re
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
        
        # 입력 데이터 유효성 검사
        if not content or content.isspace():
            raise ValueError("콘텐츠 데이터가 비어있습니다.")
        
        # 콘텐츠 처리: 문자열 → 딕셔너리 변환
        try:
            # 1. 직접 파싱 시도
            try:
                content_data = json.loads(content)
                logger.info("첫 번째 JSON 파싱 시도 성공: %s", type(content_data))
                
                # 만약 여전히 문자열이라면 다시 파싱 시도 (이중 문자열화된 경우)
                if isinstance(content_data, str):
                    logger.warning("파싱 결과가 문자열입니다. 다시 파싱 시도합니다.")
                    content_data = json.loads(content_data)
                    logger.info("두 번째 JSON 파싱 시도 성공: %s", type(content_data))
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                
                # 2. 이스케이프된 문자열이라면 처리 시도
                if content.startswith('"') and content.endswith('"'):
                    try:
                        unescaped = content[1:-1].replace('\\"', '"')
                        content_data = json.loads(unescaped)
                        logger.info("이스케이프 처리 후 JSON 파싱 성공: %s", type(content_data))
                    except json.JSONDecodeError as e2:
                        logger.error(f"이스케이프 처리 후에도 JSON 파싱 오류: {str(e2)}")
                        raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e2)}")
                else:
                    raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e)}")
            
            # 3. 결과 유효성 검사
            if not isinstance(content_data, dict):
                logger.error(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(content_data)}")
                
                # 3-1. 문자열인 경우 마지막으로 한 번 더 파싱 시도
                if isinstance(content_data, str):
                    try:
                        content_data = json.loads(content_data)
                        logger.info("마지막 JSON 파싱 시도 성공: %s", type(content_data))
                        
                        if not isinstance(content_data, dict):
                            raise ValueError(f"최종 파싱 결과가 딕셔너리가 아닙니다: {type(content_data)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"마지막 JSON 파싱 시도 실패: {str(e)}")
                        raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e)}")
                else:
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
            
        except ValueError as ve:
            logger.error(f"콘텐츠 처리 중 오류: {str(ve)}")
            
            error_response = {
                "error": f"콘텐츠 처리 중 오류: {str(ve)}",
                "user_comment": user_comment,
                "original_content": content[:200] + ("..." if len(content) > 200 else "")  # 디버깅용 원본 콘텐츠 일부 포함
            }
            
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": f"❌ 재생성 실패: {str(ve)}",
                "content": json.dumps(error_response),
                "parsed": error_response,
                "user_comment": user_comment
            })
            
        except Exception as e:
            logger.error(f"콘텐츠 처리 중 오류: {str(e)}")
            
            error_response = {
                "error": f"콘텐츠 처리 중 오류: {str(e)}",
                "user_comment": user_comment,
                "original_content": content[:200] + ("..." if len(content) > 200 else "")  # 디버깅용 원본 콘텐츠 일부 포함
            }
            
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": f"❌ 재생성 실패: {str(e)}",
                "content": json.dumps(error_response),
                "parsed": error_response,
                "user_comment": user_comment
            })
            
    except Exception as e:
        logger.error(f"콘텐츠 재생성 중 오류: {str(e)}")
        
        error_response = {
            "error": f"콘텐츠 재생성 중 오류가 발생했습니다: {str(e)}",
            "user_comment": user_comment
        }
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 재생성 실패: {str(e)}",
            "content": json.dumps(error_response),
            "parsed": error_response,
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
        
        # 콘텐츠 처리: 문자열 → 딕셔너리 변환
        try:
            # 1. 직접 파싱 시도
            try:
                parsed = json.loads(content)
                logger.info("첫 번째 JSON 파싱 시도 성공: %s", type(parsed))
                
                # 만약 여전히 문자열이라면 다시 파싱 시도 (이중 문자열화된 경우)
                if isinstance(parsed, str):
                    logger.warning("파싱 결과가 문자열입니다. 다시 파싱 시도합니다.")
                    parsed = json.loads(parsed)
                    logger.info("두 번째 JSON 파싱 시도 성공: %s", type(parsed))
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                
                # 2. 이스케이프된 문자열이라면 처리 시도
                if content.startswith('"') and content.endswith('"'):
                    try:
                        unescaped = content[1:-1].replace('\\"', '"')
                        parsed = json.loads(unescaped)
                        logger.info("이스케이프 처리 후 JSON 파싱 성공: %s", type(parsed))
                    except json.JSONDecodeError as e2:
                        logger.error(f"이스케이프 처리 후에도 JSON 파싱 오류: {str(e2)}")
                        
                        # 3. 콤마 오류 수정 시도 (Expecting ',' delimiter)
                        if "delimiter" in str(e2) and "," in str(e2) and hasattr(e2, 'pos'):
                            try:
                                pos = e2.pos
                                fixed_content = unescaped[:pos] + "," + unescaped[pos:]
                                parsed = json.loads(fixed_content)
                                logger.info("콤마 추가 후 JSON 파싱 성공: %s", type(parsed))
                            except json.JSONDecodeError as e3:
                                logger.error(f"콤마 추가 후에도 JSON 파싱 오류: {str(e3)}")
                                raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e2)}")
                        else:
                            raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e2)}")
                else:
                    # 4. 콤마 오류 수정 시도
                    if "delimiter" in str(e) and "," in str(e) and hasattr(e, 'pos'):
                        try:
                            pos = e.pos
                            fixed_content = content[:pos] + "," + content[pos:]
                            parsed = json.loads(fixed_content)
                            logger.info("콤마 추가 후 JSON 파싱 성공: %s", type(parsed))
                        except json.JSONDecodeError as e2:
                            logger.error(f"콤마 추가 후에도 JSON 파싱 오류: {str(e2)}")
                            raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e)}")
                    else:
                        raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e)}")
            
            # 5. 결과 유효성 검사
            if not isinstance(parsed, dict):
                logger.error(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(parsed)}")
                
                # 5-1. 문자열인 경우 마지막으로 한 번 더 파싱 시도
                if isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                        logger.info("마지막 JSON 파싱 시도 성공: %s", type(parsed))
                        
                        if not isinstance(parsed, dict):
                            raise ValueError(f"최종 파싱 결과가 딕셔너리가 아닙니다: {type(parsed)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"마지막 JSON 파싱 시도 실패: {str(e)}")
                        raise ValueError(f"유효한 JSON 형식이 아닙니다: {str(e)}")
                else:
                    raise ValueError(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(parsed)}")
            
            # 저장
            content_id = content_storage.save_content(parsed)
            logger.info(f"콘텐츠 저장 완료: {content_id}")
            
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": "✅ 저장 완료! 콘텐츠가 성공적으로 저장되었습니다.",
                "content": None
            })
            
        except ValueError as ve:
            logger.error(f"콘텐츠 처리 중 오류: {str(ve)}")
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": f"❌ 저장 실패: {str(ve)}",
                "content": content
            })
            
        except Exception as e:
            logger.error(f"콘텐츠 처리 중 예외 발생: {str(e)}")
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": f"❌ 저장 실패: {str(e)}",
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