from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
import uuid
from openai import OpenAI
from typing import Optional, Dict, Any, List
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수에서 API 키 불러오기
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

client = OpenAI(api_key=api_key)

# FastAPI 설정
app = FastAPI(title="TOPIK 문제 생성기")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 저장용 파일 경로
CONFIRM_FILE = "confirmed_questions.json"
confirmed_data = []

# GPT 프롬프트 템플릿
TEMPLATE = {
    "dialogue": """{level} 학습자에게 적합한 일상 대화문을 하나 생성해 주세요.
- 장소: 실생활에서 흔히 일어날 수 있는 곳 (예: 카페, 병원, 사무실 등)
- 구성: 두 명의 화자 A, B가 등장하며, 2~5문장 내외의 대화로 구성
- 문체: 자연스러운 구어체, 높임말 혹은 반말 혼용 가능
- 목적: 일상적인 요청, 제안, 설명, 문제 해결 등의 상황 반영
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "dialogue",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "situation": "...",
  "dialogue": ["A: ...", "B: ..."],
  "tokens": ...
}}""",

    "monologue_explanation": """{level} 학습자에게 적합한 혼잣말 형식의 설명문을 생성해 주세요.
- 문체: 혼잣말처럼 말하는 1인칭 구어체 혹은 발표체
- 기능: 일정 안내, 절차 설명, 경험 공유, 통계 발표 등
- 구성: 도입(배경) → 설명(내용) → 정리(마무리)
- 길이: 150~300자 내외, 4~7문장
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "monologue_explanation",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "situation": "...",
  "script": "...",
  "tokens": ...
}}""",

    "news_reading": """{level} 학습자에게 적합한 뉴스 기사 형식의 듣기 지문을 작성해 주세요.
- 문체: 간결하고 중립적인 기사체
- 내용: 기상, 사고, 발표, 정책 등 현실성 있는 주제
- 구성: 시간/장소 → 사건 → 영향 및 조치
- 길이: 약 200~300자
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "news_reading",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "script": "...",
  "tokens": ...
}}""",

    "lecture": """{level} 학습자에게 적합한 강의 형식의 지문을 생성해 주세요.
- 문체: 설명문, 객관적이며 교사/강사 어조
- 주제: 역사, 사회, 과학, 문화 등 중립적 주제
- 구성: 정의 → 예시 → 결론 / 명확한 정보 구조
- 길이: 300~400자
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "lecture",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "script": "...",
  "tokens": ...
}}""",

    "short_reading": """{level} 학습자에게 적합한 짧은 읽기 지문을 생성해 주세요.
- 문체: 안내문, 일기, 블로그 글 등 개인적 문체 가능
- 길이: 150~200자 / 단문 1개 지문
- 목적: 중심 내용 파악, 정보 요약, 의견 이해 등
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "short_reading",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "title": "...",
  "text": "...",
  "tokens": ...
}}""",

    "long_reading": """{level} 학습자에게 적합한 장문 읽기 지문을 생성해 주세요.
- 문체: 설명문, 기사체, 에세이체 등
- 구성: 주제 제시 → 설명 → 예시/결론
- 길이: 약 300~500자 / 문단 구조를 명확히 할 것
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "long_reading",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "title": "...",
  "text": "...",
  "tokens": ...
}}""",

    "image_description_reading": """{level} 학습자에게 적합한 포스터, 이메일, 통계자료 등의 시각 자료를 설명하는 읽기 지문을 작성해 주세요.
- 문체: 안내문, 정보 설명 문체
- 구성: 제목 → 내용 요약 → 시간/장소/대상 정보
- 길이: 150~250자
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "image_description_reading",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "description": "...",
  "tokens": ...
}}""",

    "image_description_listening": """{level} 학습자에게 적합한 듣기용 그림 선택 문제를 구성해 주세요.
- 구성: 상황 대화문 1개 + 그림 설명 4개 중 1개는 정답
- 문체: 구어체
- 길이: 대화문은 3~4문장 / 설명문은 간결히
- 추가 항목: topic, place, keywords(5개), tokens

출력 형식:
{{
  "type": "image_description_listening",
  "topic": "...",
  "place": "...",
  "keywords": ["...", "...", "...", "...", "..."],
  "dialogue": ["A: ...", "B: ..."],
  "choices": ["...", "...", "...", "..."],
  "answer_index": 0,
  "tokens": ...
}}"""
}

# 애플리케이션 시작 시 저장된 데이터 로드
def load_confirmed_data() -> List[Dict[str, Any]]:
    """저장된 콘텐츠 데이터를 로드합니다."""
    data = []
    if os.path.exists(CONFIRM_FILE):
        try:
            with open(CONFIRM_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                else:
                    logger.warning(f"'{CONFIRM_FILE}' 파일이 비어 있습니다.")
                    return []
            
            logger.info(f"'{CONFIRM_FILE}'에서 {len(data)}개의 콘텐츠를 로드했습니다.")
            
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
                with open(CONFIRM_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info("유효한 데이터만 다시 파일에 저장했습니다.")
                
        except json.JSONDecodeError as e:
            logger.error(f"'{CONFIRM_FILE}' 파일의 JSON 형식이 올바르지 않습니다: {e}")
            # 손상된 파일 백업
            backup_file = f"{CONFIRM_FILE}.bak"
            try:
                os.rename(CONFIRM_FILE, backup_file)
                logger.info(f"손상된 파일을 {backup_file}로 백업했습니다.")
                # 새 빈 파일 생성
                with open(CONFIRM_FILE, 'w', encoding='utf-8') as f:
                    f.write('[]')
                logger.info(f"새로운 빈 {CONFIRM_FILE} 파일을 생성했습니다.")
            except Exception as e:
                logger.error(f"파일 백업 중 오류: {e}")
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
    else:
        logger.info(f"'{CONFIRM_FILE}' 파일이 존재하지 않습니다. 새로운 파일이 생성될 것입니다.")
        # 빈 파일 생성
        with open(CONFIRM_FILE, 'w', encoding='utf-8') as f:
            f.write('[]')
    
    return data

# 데이터 저장 함수
def save_confirmed_data(data: List[Dict[str, Any]]) -> bool:
    """데이터를 파일에 저장합니다."""
    try:
        with open(CONFIRM_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"{len(data)}개의 콘텐츠를 '{CONFIRM_FILE}'에 저장했습니다.")
        return True
    except Exception as e:
        logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
        return False

# 초기 데이터 로드
confirmed_data = load_confirmed_data()

def generate_prompt_content(qtype: str, level: str) -> str:
    """GPT를 사용하여 콘텐츠를 생성합니다."""
    if not api_key:
        mock_content = {
            "type": qtype,
            "level": level,
            "error": "API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요."
        }
        
        if qtype == "dialogue":
            mock_content.update({
                "situation": "API 키 없이 예시로 생성된 대화",
                "dialogue": ["A: 안녕하세요?", "B: 네, 안녕하세요. 반갑습니다."]
            })
        elif "reading" in qtype:
            mock_content.update({
                "title": "API 키 없이 예시로 생성된 지문",
                "text": "이것은 API 키가 없을 때 제공되는 예시 텍스트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            })
        else:
            mock_content.update({
                "topic": "API 키 없이 예시로 생성된 콘텐츠",
                "script": "이것은 API 키가 없을 때 제공되는 예시 스크립트입니다. 실제 API 키를 설정하면 다양한 콘텐츠가 생성됩니다."
            })
        
        return json.dumps(mock_content, ensure_ascii=False)
    
    try:
        prompt = TEMPLATE[qtype].format(level=level)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 한국어 교육용 콘텐츠를 생성하는 AI입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"콘텐츠 생성 성공: {qtype} / {level}")
        return result
    except Exception as e:
        logger.error(f"GPT API 호출 중 오류: {str(e)}")
        error_content = {
            "type": qtype,
            "level": level,
            "error": f"콘텐츠 생성 중 오류가 발생했습니다: {str(e)}"
        }
        return json.dumps(error_content, ensure_ascii=False)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """메인 페이지를 표시합니다."""
    return templates.TemplateResponse("generator.html", {"request": request, "content": None})

@app.post("/generate", response_class=HTMLResponse)
def generate_content(request: Request, qtype: str = Form(...), level: str = Form(...)):
    """선택한 유형과 레벨에 따라 콘텐츠를 생성합니다."""
    raw_content = generate_prompt_content(qtype, level)
    
    try:
        parsed = json.loads(raw_content)
        # 레벨 정보를 응답에 추가
        if "level" not in parsed:
            parsed["level"] = level
    except json.JSONDecodeError:
        logger.error(f"생성된 콘텐츠를 JSON으로 파싱할 수 없습니다: {raw_content}")
        parsed = {
            "error": "GPT 응답이 JSON 형식이 아닙니다.",
            "raw": raw_content,
            "type": qtype,
            "level": level
        }
    except Exception as e:
        logger.error(f"콘텐츠 파싱 중 오류: {str(e)}")
        parsed = {
            "error": f"응답 처리 중 오류가 발생했습니다: {str(e)}",
            "raw": raw_content,
            "type": qtype,
            "level": level
        }
    
    return templates.TemplateResponse("generator.html", {
        "request": request,
        "content": raw_content,
        "parsed": parsed
    })

@app.post("/confirm", response_class=HTMLResponse)
def confirm_content(request: Request, content: str = Form(...)):
    """편집된 콘텐츠를 확인하고 저장합니다."""
    global confirmed_data
    
    logger.info(f"confirm 데이터 타입: {type(content)}")
    logger.info(f"confirm 데이터 앞부분: {content[:150]}..." if len(content) > 150 else content)
    
    try:
        if not content or content.isspace():
            raise ValueError("빈 콘텐츠가 전송되었습니다.")
            
        # 문자열에서 JSON 파싱
        parsed = json.loads(content)
        
        if not isinstance(parsed, dict):
            raise ValueError(f"파싱된 데이터가 딕셔너리가 아닙니다: {type(parsed)}")
        
        # ID가 없으면 새로 생성
        if "id" not in parsed:
            parsed["id"] = str(uuid.uuid4())
        
        # 기존 데이터에서 동일 ID 검색
        found = False
        for i, item in enumerate(confirmed_data):
            if isinstance(item, dict) and item.get("id") == parsed["id"]:
                # 기존 항목 업데이트
                confirmed_data[i] = parsed
                logger.info(f"기존 콘텐츠 업데이트: {parsed['id']}")
                found = True
                break
        
        if not found:
            # 새 항목 추가
            confirmed_data.append(parsed)
            logger.info(f"새 콘텐츠 추가: {parsed['id']}")
        
        # 파일에 저장
        if save_confirmed_data(confirmed_data):
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": "✅ 저장 완료! 콘텐츠가 성공적으로 저장되었습니다.",
                "content": None
            })
        else:
            return templates.TemplateResponse("generator.html", {
                "request": request,
                "message": "❌ 파일 저장 중 오류가 발생했습니다.",
                "content": content
            })
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}, 받은 데이터: {content[:150]}...")
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 저장 실패: 유효하지 않은 JSON 형식입니다 - {str(e)}",
            "content": content
        })
    except Exception as e:
        logger.error(f"콘텐츠 저장 중 오류: {str(e)}")
        logger.error(f"오류 상세: {type(e).__name__}, 받은 데이터 타입: {type(content)}")
        
        # 디버깅용 임시 코드 추가
        if isinstance(content, str):
            try:
                # content가 따옴표로 이스케이프된 경우 처리
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1].replace('\\"', '"')
                
                # content가 문자열이더라도 직접 파싱 시도
                parsed_data = json.loads(content)
                logger.info(f"비상 처리 - 파싱 성공, 데이터 타입: {type(parsed_data)}")
                
                # 정상적으로 파싱되면 여기서 저장 시도
                if isinstance(parsed_data, dict):
                    if "id" not in parsed_data:
                        parsed_data["id"] = str(uuid.uuid4())
                    
                    # 기존 ID 검색
                    for i, item in enumerate(confirmed_data):
                        if isinstance(item, dict) and item.get("id") == parsed_data["id"]:
                            confirmed_data[i] = parsed_data
                            break
                    else:
                        confirmed_data.append(parsed_data)
                    
                    if save_confirmed_data(confirmed_data):
                        return templates.TemplateResponse("generator.html", {
                            "request": request,
                            "message": "✅ 비상 처리를 통해 저장에 성공했습니다.",
                            "content": None
                        })
            except Exception as inner_e:
                logger.error(f"비상 처리 중 추가 오류: {str(inner_e)}")
        
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "message": f"❌ 저장 실패: {str(e)}",
            "content": content
        })

@app.get("/confirmed", response_class=HTMLResponse)
def show_confirmed(request: Request):
    """저장된 모든 콘텐츠를 표시합니다."""
    global confirmed_data
    
    # 페이지 로드 시 항상 최신 데이터 다시 로드
    confirmed_data = load_confirmed_data()
    
    logger.info(f"저장된 콘텐츠 페이지 로드: {len(confirmed_data)}개 항목")
    return templates.TemplateResponse("confirmed.html", {
        "request": request,
        "data": confirmed_data
    })

@app.get("/content/{content_id}", response_class=HTMLResponse)
def get_content(request: Request, content_id: str):
    """특정 콘텐츠의 상세 정보를 표시합니다."""
    global confirmed_data
    
    # 최신 데이터 로드
    if not confirmed_data:
        confirmed_data = load_confirmed_data()
    
    # 콘텐츠 ID로 검색
    for item in confirmed_data:
        if isinstance(item, dict) and item.get("id") == content_id:
            logger.info(f"콘텐츠 상세 보기: {content_id}")
            return templates.TemplateResponse("content_detail.html", {
                "request": request,
                "item": item
            })
    
    # 콘텐츠를 찾지 못한 경우
    logger.warning(f"존재하지 않는 콘텐츠 ID: {content_id}")
    return templates.TemplateResponse("error.html", {
        "request": request,
        "message": "요청한 콘텐츠를 찾을 수 없습니다."
    })

@app.get("/delete/{content_id}", response_class=HTMLResponse)
def delete_content(request: Request, content_id: str):
    """특정 콘텐츠를 삭제합니다."""
    global confirmed_data
    
    try:
        # 삭제할 콘텐츠 검색
        for i, item in enumerate(confirmed_data):
            if isinstance(item, dict) and item.get("id") == content_id:
                # 항목 삭제
                removed_item = confirmed_data.pop(i)
                logger.info(f"콘텐츠 삭제: {content_id} - {removed_item.get('type')}")
                
                # 파일에 저장
                if save_confirmed_data(confirmed_data):
                    return RedirectResponse(url="/confirmed", status_code=303)
                else:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "message": "콘텐츠 삭제 후 파일 저장 중 오류가 발생했습니다."
                    })
        
        # 콘텐츠를 찾지 못한 경우
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)