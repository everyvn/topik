"""
JSON 디버깅 유틸리티
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
        start_pos = max(0, error.pos - 50)
        end_pos = min(len(json_str), error.pos + 50)
        
        before_error = json_str[start_pos:error.pos]
        error_char = json_str[error.pos:error.pos+1] if error.pos < len(json_str) else "EOF"
        after_error = json_str[error.pos+1:end_pos] if error.pos+1 < len(json_str) else ""
        
        result["context"] = {
            "before_error": before_error,
            "error_char": error_char,
            "after_error": after_error,
            "error_char_code": ord(error_char) if error_char != "EOF" else None
        }
    
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

def analyze_error_patterns(json_str: str, error: json.JSONDecodeError) -> List[Dict[str, Any]]:
    """
    일반적인 JSON 오류 패턴을 분석합니다.
    """
    issues = []
    error_msg = str(error)
    
    # 일반적인 오류 패턴 확인
    if "Expecting ',' delimiter" in error_msg:
        issues.append({
            "type": "missing_comma",
            "description": "콤마 누락",
            "position": error.pos
        })
    elif "Expecting property name enclosed in double quotes" in error_msg:
        issues.append({
            "type": "unquoted_property",
            "description": "속성명이 따옴표로 감싸져 있지 않음",
            "position": error.pos
        })
    elif "Expecting ':' delimiter" in error_msg:
        issues.append({
            "type": "missing_colon",
            "description": "콜론 누락",
            "position": error.pos
        })
    elif "Expecting value" in error_msg:
        issues.append({
            "type": "missing_value",
            "description": "값 누락",
            "position": error.pos
        })
    elif "Extra data" in error_msg:
        issues.append({
            "type": "extra_data",
            "description": "JSON 객체 이후에 추가 데이터 존재",
            "position": error.pos
        })
    elif "Unterminated string" in error_msg:
        issues.append({
            "type": "unterminated_string",
            "description": "종료되지 않은 문자열",
            "position": error.pos
        })
    
    # 이스케이프 관련 문제 (중요)
    if error.pos is not None and error.pos < len(json_str):
        around_error = json_str[max(0, error.pos-10):min(len(json_str), error.pos+10)]
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
    """
    issues = []
    
    # 이중 이스케이프 문자 검사
    double_escaped = re.findall(r'\\\\["\\/bfnrt]|\\\\u[0-9a-fA-F]{4}', json_str)
    if double_escaped:
        issues.append({
            "type": "double_escaped_chars",
            "description": "이중 이스케이프된 문자가 발견됨",
            "count": len(double_escaped),
            "examples": double_escaped[:5]
        })
    
    # 잘못된 이스케이프 시퀀스 검사
    invalid_escapes = re.findall(r'\\[^"\\/bfnrtu]', json_str)
    if invalid_escapes:
        issues.append({
            "type": "invalid_escape_sequences",
            "description": "유효하지 않은 이스케이프 시퀀스",
            "count": len(invalid_escapes),
            "examples": invalid_escapes[:5]
        })
    
    # 따옴표 불일치 검사 (이스케이프되지 않은 따옴표)
    unescaped_quotes_in_strings = re.findall(r'"[^"\\]*(?:\\.[^"\\]*)*"', json_str)
    quote_issues = []
    for match in unescaped_quotes_in_strings:
        if re.search(r'[^\\]"', match[1:-1]):
            quote_issues.append(match)
    
    if quote_issues:
        issues.append({
            "type": "unescaped_quotes",
            "description": "문자열 내 이스케이프되지 않은 따옴표",
            "count": len(quote_issues),
            "examples": quote_issues[:3]
        })
    
    return issues

def check_json_structure(json_str: str) -> List[Dict[str, Any]]:
    """
    JSON 구조의 균형을 확인합니다.
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
    
    # 1. 이중 이스케이프 처리
    if '\\\\' in fixed_str:
        old_str = fixed_str
        fixed_str = fixed_str.replace('\\\\', '\\')
        if old_str != fixed_str:
            fixes.append("이중 이스케이프 문자 수정")
    
    # 2. 싱글 따옴표를 더블 따옴표로 변환 (속성명)
    property_pattern = r"'([^']*)':"
    if re.search(property_pattern, fixed_str):
        old_str = fixed_str
        fixed_str = re.sub(property_pattern, r'"\1":', fixed_str)
        if old_str != fixed_str:
            fixes.append("싱글 따옴표로 된 속성명을 더블 따옴표로 변환")
    
    # 3. 마지막 콤마 제거
    trailing_comma_object = r',\s*}'
    trailing_comma_array = r',\s*\]'
    
    if re.search(trailing_comma_object, fixed_str) or re.search(trailing_comma_array, fixed_str):
        old_str = fixed_str
        fixed_str = re.sub(trailing_comma_object, '}', fixed_str)
        fixed_str = re.sub(trailing_comma_array, ']', fixed_str)
        if old_str != fixed_str:
            fixes.append("객체/배열 끝의 불필요한 콤마 제거")
    
    # 4. 주석 제거 (JSON에서는 주석이 허용되지 않음)
    comment_pattern = r'//.*?(?:\n|$)|/\*[\s\S]*?\*/'
    if re.search(comment_pattern, fixed_str):
        old_str = fixed_str
        fixed_str = re.sub(comment_pattern, '', fixed_str)
        if old_str != fixed_str:
            fixes.append("주석 제거")
    
    # 5. 객체 키 주변 공백 수정
    space_after_colon = r'":([^\s\n\r])'
    if re.search(space_after_colon, fixed_str):
        old_str = fixed_str
        fixed_str = re.sub(space_after_colon, '": \\1', fixed_str)
        if old_str != fixed_str:
            fixes.append("콜론 뒤에 공백 추가")
    
    return fixed_str, fixes

def extract_valid_json(text: str) -> Optional[str]:
    """
    텍스트에서 유효한 JSON 객체를 추출합니다.
    
    Args:
        text: JSON을 추출할 텍스트
        
    Returns:
        추출된 JSON 문자열 또는 None (실패 시)
    """
    # 가장 바깥쪽 JSON 객체 패턴
    json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
    match = re.search(json_pattern, text)
    
    if match:
        candidate = match.group(1)
        try:
            # 유효성 검사
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    
    # 더 단순한 패턴으로 재시도
    simple_pattern = r'(\{.*\})'
    match = re.search(simple_pattern, text, re.DOTALL)
    
    if match:
        candidate = match.group(1)
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    
    return None