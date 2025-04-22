"""
JSON 디버깅 유틸리티

JSON 파싱 오류를 분석하고 수정하기 위한 도구를 제공합니다.
"""

import json
import re
from typing import Any, Dict, List, Tuple, Optional


def debug_json_error(json_str: str, error: json.JSONDecodeError) -> Dict[str, Any]:
    """
    JSON 파싱 오류를 디버깅하기 위한 상세 정보를 제공합니다.
    
    Args:
        json_str: 파싱에 실패한 JSON 문자열
        error: 발생한 JSONDecodeError 인스턴스
        
    Returns:
        디버깅 정보가 담긴 딕셔너리
    """
    # 기본 오류 정보
    result = {
        "error_type": "JSONDecodeError",
        "error_message": str(error),
        "line": error.lineno,
        "column": error.colno,
        "position": error.pos,
        "json_length": len(json_str)
    }
    
    # 오류 위치 컨텍스트 추출
    if error.pos is not None and error.pos < len(json_str):
        result["context"] = _extract_error_context(json_str, error.pos)
    
    # 일반적인 JSON 오류 패턴 분석
    patterns = analyze_error_patterns(json_str, error)
    if patterns:
        result["detected_issues"] = patterns
    
    # 이스케이프 문자 분석
    escape_issues = analyze_escape_chars(json_str)
    if escape_issues:
        result["escape_issues"] = escape_issues
    
    # 구조 밸런스 검사
    structure_issues = check_json_structure(json_str)
    if structure_issues:
        result["structure_issues"] = structure_issues
    
    return result


def _extract_error_context(json_str: str, pos: int, context_size: int = 50) -> Dict[str, str]:
    """
    오류 발생 위치의 컨텍스트를 추출합니다.
    
    Args:
        json_str: JSON 문자열
        pos: 오류 위치
        context_size: 추출할 컨텍스트 크기
        
    Returns:
        추출된 컨텍스트 정보
    """
    start_pos = max(0, pos - context_size)
    end_pos = min(len(json_str), pos + context_size)
    
    before_error = json_str[start_pos:pos]
    error_char = json_str[pos:pos+1] if pos < len(json_str) else "EOF"
    after_error = json_str[pos+1:end_pos] if pos+1 < len(json_str) else ""
    
    return {
        "before_error": before_error,
        "error_char": error_char,
        "after_error": after_error,
        "error_char_code": ord(error_char) if error_char != "EOF" else None
    }


def analyze_error_patterns(json_str: str, error: json.JSONDecodeError) -> List[Dict[str, Any]]:
    """
    일반적인 JSON 오류 패턴을 분석합니다.
    
    Args:
        json_str: JSON 문자열
        error: 발생한 JSONDecodeError
        
    Returns:
        탐지된 오류 패턴 목록
    """
    issues = []
    error_msg = str(error)
    
    # 오류 메시지 패턴과 설명 맵핑
    error_patterns = {
        "Expecting ',' delimiter": ("missing_comma", "콤마 누락"),
        "Expecting property name enclosed in double quotes": ("unquoted_property", "속성명이 따옴표로 감싸져 있지 않음"),
        "Expecting ':' delimiter": ("missing_colon", "콜론 누락"),
        "Expecting value": ("missing_value", "값 누락"),
        "Extra data": ("extra_data", "JSON 객체 이후에 추가 데이터 존재"),
        "Unterminated string": ("unterminated_string", "종료되지 않은 문자열")
    }
    
    # 오류 메시지 패턴 확인
    for pattern, (issue_type, description) in error_patterns.items():
        if pattern in error_msg:
            issues.append({
                "type": issue_type,
                "description": description,
                "position": error.pos
            })
    
    # 이스케이프 관련 문제 검사
    if error.pos is not None and error.pos < len(json_str):
        context_start = max(0, error.pos - 10)
        context_end = min(len(json_str), error.pos + 10)
        around_error = json_str[context_start:context_end]
        
        if '\\' in around_error:
            issues.append({
                "type": "escape_sequence",
                "description": "이스케이프 시퀀스 문제 가능성",
                "position": error.pos,
                "context": around_error
            })
    
    return issues


def analyze_escape_chars(json_str: str) -> List[Dict[str, Any]]:
    """
    이스케이프 문자 관련 문제를 분석합니다.
    
    Args:
        json_str: JSON 문자열
        
    Returns:
        탐지된 이스케이프 문자 관련 문제 목록
    """
    issues = []
    
    # 이스케이프 문자 패턴과 함수 맵핑
    escape_patterns = [
        # 패턴, 이슈 유형, 설명
        (r'\\\\["\\/bfnrt]|\\\\u[0-9a-fA-F]{4}', "double_escaped_chars", "이중 이스케이프된 문자가 발견됨"),
        (r'\\[^"\\/bfnrtu]', "invalid_escape_sequences", "유효하지 않은 이스케이프 시퀀스")
    ]
    
    # 각 패턴 확인
    for pattern, issue_type, description in escape_patterns:
        matches = re.findall(pattern, json_str)
        if matches:
            issues.append({
                "type": issue_type,
                "description": description,
                "count": len(matches),
                "examples": matches[:5]
            })
    
    # 따옴표 불일치 검사
    quote_issues = _check_unescaped_quotes(json_str)
    if quote_issues:
        issues.append({
            "type": "unescaped_quotes",
            "description": "문자열 내 이스케이프되지 않은 따옴표",
            "count": len(quote_issues),
            "examples": quote_issues[:3]
        })
    
    return issues


def _check_unescaped_quotes(json_str: str) -> List[str]:
    """
    문자열 내부에 이스케이프되지 않은 따옴표가 있는지 검사합니다.
    
    Args:
        json_str: JSON 문자열
        
    Returns:
        이스케이프되지 않은 따옴표가 있는 문자열 목록
    """
    unescaped_quotes_in_strings = re.findall(r'"[^"\\]*(?:\\.[^"\\]*)*"', json_str)
    quote_issues = []
    
    for match in unescaped_quotes_in_strings:
        if re.search(r'[^\\]"', match[1:-1]):
            quote_issues.append(match)
    
    return quote_issues


def check_json_structure(json_str: str) -> List[Dict[str, Any]]:
    """
    JSON 구조의 균형을 확인합니다.
    
    Args:
        json_str: JSON 문자열
        
    Returns:
        구조 불균형 이슈 목록
    """
    issues = []
    brackets = {'{': '}', '[': ']'}
    stack = []
    
    for i, c in enumerate(json_str):
        if c in brackets.keys():
            stack.append((c, i))
        elif c in brackets.values():
            if not stack:
                issues.append({
                    "type": "unexpected_closing_bracket",
                    "description": f"예상치 않은 닫는 괄호 '{c}'",
                    "position": i
                })
                continue
                
            last_open, pos = stack.pop()
            if brackets[last_open] != c:
                issues.append({
                    "type": "mismatched_brackets",
                    "description": f"괄호 불일치: '{last_open}' at {pos} and '{c}' at {i}",
                    "open_position": pos,
                    "close_position": i
                })
    
    # 괄호가 열린 채로 종료된 경우
    for bracket, pos in stack:
        issues.append({
            "type": "unclosed_bracket",
            "description": f"닫히지 않은 괄호 '{bracket}'",
            "position": pos
        })
    
    return issues


def fix_common_json_errors(json_str: str) -> Tuple[str, List[str]]:
    """
    일반적인 JSON 오류를 수정합니다.
    
    Args:
        json_str: 수정할 JSON 문자열
        
    Returns:
        수정된 JSON 문자열과 적용된 수정 사항 목록
    """
    fixes = []
    fixed_str = json_str
    
    # 수정 패턴과 설명 목록
    fix_patterns = [
        # 이중 이스케이프 처리
        (r'\\\\', '\\', "이중 이스케이프 문자 수정"),
        # 싱글 따옴표를 더블 따옴표로 변환 (속성명)
        (r"'([^']*)':", r'"\1":', "싱글 따옴표로 된 속성명을 더블 따옴표로 변환"),
        # 마지막 콤마 제거
        (r',\s*}', '}', "객체 끝의 불필요한 콤마 제거"),
        (r',\s*\]', ']', "배열 끝의 불필요한 콤마 제거"),
        # 주석 제거
        (r'//.*?(?:\n|$)|/\*[\s\S]*?\*/', '', "주석 제거"),
        # 콜론 뒤 공백 추가
        (r'":([^\s\n\r])', '": \\1', "콜론 뒤에 공백 추가")
    ]
    
    # 각 패턴에 대한 수정 적용
    for pattern, replacement, description in fix_patterns:
        old_str = fixed_str
        fixed_str = re.sub(pattern, replacement, fixed_str)
        if old_str != fixed_str:
            fixes.append(description)
    
    return fixed_str, fixes


def extract_valid_json(text: str) -> Optional[str]:
    """
    텍스트에서 유효한 JSON 객체를 추출합니다.
    
    Args:
        text: JSON을 추출할 텍스트
        
    Returns:
        추출된 JSON 문자열 또는 None (실패 시)
    """
    # JSON 객체 추출 패턴들
    patterns = [
        # 복잡한 중첩 객체 패턴
        r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})',
        # 단순한 객체 패턴
        r'(\{.*\})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                # 유효성 검사
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
    
    return None


def safely_parse_json(json_str: str) -> Dict[str, Any]:
    """
    다양한 상황을 처리하며 안전하게 JSON 문자열을 파싱합니다.
    
    Args:
        json_str: 파싱할 JSON 문자열
        
    Returns:
        파싱된 JSON 객체
        
    Raises:
        ValueError: JSON 파싱에 실패한 경우
    """
    if not json_str or json_str.isspace():
        raise ValueError("JSON 문자열이 비어 있습니다.")
    
    try:
        # 1. 직접 파싱 시도
        data = json.loads(json_str)
        
        # 결과가 문자열인 경우 다시 파싱 (이중 문자열화된 경우)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass
        
        return data
    except json.JSONDecodeError as e:
        # 2. 오류 발생 시 수정 시도
        fixed_str, fixes = fix_common_json_errors(json_str)
        
        if fixes:  # 수정이 적용된 경우
            try:
                data = json.loads(fixed_str)
                return data
            except json.JSONDecodeError:
                pass
        
        # 3. 여전히 실패한 경우, 유효한 JSON 추출 시도
        extracted = extract_valid_json(json_str)
        if extracted:
            try:
                data = json.loads(extracted)
                return data
            except json.JSONDecodeError:
                pass
        
        # 4. 모든 시도 실패
        debug_info = debug_json_error(json_str, e)
        raise ValueError(f"JSON 파싱 실패: {str(e)}\n디버그 정보: {debug_info}")