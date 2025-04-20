"""
GPT 프롬프트 템플릿 모듈
"""

# GPT 프롬프트 템플릿
TEMPLATES = {
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