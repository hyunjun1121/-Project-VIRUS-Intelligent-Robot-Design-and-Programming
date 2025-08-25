#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 변환기
HTML 파일이나 HTML 문자열을 Markdown 형식으로 변환합니다.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Union
import re
import html

try:
    from bs4 import BeautifulSoup
    import markdownify
except ImportError:
    print("필요한 라이브러리가 설치되지 않았습니다.")
    print("다음 명령으로 설치해주세요:")
    print("pip install beautifulsoup4 markdownify lxml")
    sys.exit(1)


class HTMLToMarkdown:
    def __init__(self, 
                 strip_tags: Optional[list] = None,
                 convert_links: bool = True,
                 heading_style: str = "ATX"):
        """
        HTML to Markdown 변환기 초기화
        
        Args:
            strip_tags: 제거할 HTML 태그 목록
            convert_links: 링크 변환 여부
            heading_style: 헤딩 스타일 ("ATX" 또는 "UNDERLINED")
        """
        self.strip_tags = strip_tags or ['script', 'style', 'meta', 'link']
        self.convert_links = convert_links
        self.heading_style = heading_style
    
    def clean_html(self, html_content: str) -> str:
        """HTML 내용을 정리합니다."""
        # 1. HTML 엔티티 디코딩
        html_content = html.unescape(html_content)
        
        # 2. BeautifulSoup로 파싱
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 3. 불필요한 태그 제거
        for tag in self.strip_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # 4. 텍스트 정리
        cleaned_html = str(soup)
        
        # 5. 특수 문자 정리
        cleaned_html = self.fix_encoding_issues(cleaned_html)
        
        # 6. 여러 공백을 하나로 정리
        cleaned_html = re.sub(r'\n\s*\n', '\n\n', cleaned_html)
        
        return cleaned_html
    
    def fix_encoding_issues(self, text: str) -> str:
        """일반적인 인코딩 문제들을 수정합니다."""
        # 일반적인 문제 문자들 매핑
        replacements = {
            '\u2019': "'",     # 아포스트로피
            '\u201c': '"',     # 여는 따옴표
            '\u201d': '"',     # 닫는 따옴표
            '\u2014': '\u2014',  # em dash
            '\u2013': '\u2013',  # en dash
            '\u2022': '\u2022',  # 불릿
            '\u2026': '\u2026',  # 말줄임표
            '\u2212': '\u2212',  # 마이너스
            '\u2264': '\u2264',  # 작거나 같음
            '\u2265': '\u2265',  # 크거나 같음
            '\u2192': '\u2192',  # 오른쪽 화살표
            '\u2190': '\u2190',  # 왼쪽 화살표
            '\u2191': '\u2191',  # 위쪽 화살표
            '\u2193': '\u2193',  # 아래쪽 화살표
            'Ã¡': 'á',       # a with acute
            'Ã©': 'é',       # e with acute
            'Ã­': 'í',       # i with acute
            'Ã³': 'ó',       # o with acute
            'Ãº': 'ú',       # u with acute
            'Ã±': 'ñ',       # n with tilde
            'Ã§': 'ç',       # c with cedilla
            'Â': '',         # non-breaking space 문제
            'Ã': '',         # 잘못된 인코딩 제거
            'â€™': "'",      # 잘못된 인코딩 아포스트로피
            'â€œ': '"',      # 잘못된 인코딩 여는 따옴표
            'â€': '"',       # 잘못된 인코딩 닫는 따옴표
            'â€"': '-',      # 잘못된 인코딩 대시
            'â€¢': '•',      # 잘못된 인코딩 불릿
            'â€¦': '...',    # 잘못된 인코딩 말줄임표
        }
        
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        
        # 연속된 특수문자 정리
        text = re.sub(r'[^\x00-\x7F]+', lambda m: self.clean_unicode(m.group(0)), text)
        
        return text
    
    def clean_unicode(self, text: str) -> str:
        """유니코드 문자를 정리합니다."""
        try:
            # 유효한 유니코드 범위들
            valid_ranges = [
                (0x0000, 0x007F),    # 기본 ASCII
                (0x00A0, 0x024F),    # 라틴 확장 A, B
                (0x1E00, 0x1EFF),    # 라틴 확장 추가
                (0x2000, 0x206F),    # 일반 문장부호
                (0x2070, 0x209F),    # 위첨자/아래첨자
                (0x20A0, 0x20CF),    # 통화 기호
                (0x2100, 0x214F),    # 문자형 기호
                (0x2190, 0x21FF),    # 화살표
                (0x2200, 0x22FF),    # 수학 연산자
                (0x2300, 0x23FF),    # 기타 기술 기호
                (0x2400, 0x243F),    # 제어 그림
                (0x2500, 0x257F),    # 상자 그리기
                (0x2580, 0x259F),    # 블록 요소
                (0x25A0, 0x25FF),    # 기하학적 모양
                (0x2600, 0x26FF),    # 기타 기호
                (0x2700, 0x27BF),    # 딩뱃
                (0x3000, 0x303F),    # CJK 기호 및 문장부호
                (0x3040, 0x309F),    # 히라가나
                (0x30A0, 0x30FF),    # 가타카나
                (0x4E00, 0x9FFF),    # CJK 통합 한자
                (0xAC00, 0xD7AF),    # 한글 음절
                (0xF900, 0xFAFF),    # CJK 호환 한자
                (0x1F000, 0x1F9FF),  # 이모지
            ]
            
            def is_valid_char(char):
                code = ord(char)
                for start, end in valid_ranges:
                    if start <= code <= end:
                        return True
                return False
            
            # 문자별로 검사하여 유효한 문자만 유지
            cleaned = ''
            for char in text:
                if is_valid_char(char):
                    cleaned += char
                elif char in '\r\n\t ':  # 기본 공백 문자들은 유지
                    cleaned += char
                # 무효한 문자는 건너뛰기
            
            return cleaned
        except:
            return text
    
    def convert_to_markdown(self, html_content: str) -> str:
        """HTML을 Markdown으로 변환합니다."""
        # HTML 정리
        cleaned_html = self.clean_html(html_content)
        
        # Markdown으로 변환
        markdown = markdownify.markdownify(
            cleaned_html,
            heading_style=markdownify.ATX if self.heading_style == "ATX" else markdownify.UNDERLINED,
            bullets="-",
            escape_misc=False
        )
        
        # 추가 정리
        markdown = self.post_process_markdown(markdown)
        
        return markdown
    
    def post_process_markdown(self, markdown: str) -> str:
        """변환된 Markdown을 후처리합니다."""
        # 여러 줄바꿈을 두 개로 제한
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # 시작과 끝의 공백 제거
        markdown = markdown.strip()
        
        # 리스트 항목 사이의 빈 줄 제거
        markdown = re.sub(r'(\* .+)\n\n(\* .+)', r'\1\n\2', markdown)
        markdown = re.sub(r'(\d+\. .+)\n\n(\d+\. .+)', r'\1\n\2', markdown)
        
        return markdown
    
    def convert_file(self, input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> str:
        """HTML 파일을 Markdown 파일로 변환합니다."""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")
        
        # HTML 파일 읽기
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Markdown으로 변환
        markdown_content = self.convert_to_markdown(html_content)
        
        # 출력 파일 경로 결정
        if output_path is None:
            # 기본 출력 폴더 설정
            output_dir = Path('./output')
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / input_path.with_suffix('.md').name
        else:
            output_path = Path(output_path)
            # 출력 디렉토리가 없으면 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Markdown 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(output_path)
    
    def convert_string(self, html_string: str) -> str:
        """HTML 문자열을 Markdown 문자열로 변환합니다."""
        return self.convert_to_markdown(html_string)


def main():
    parser = argparse.ArgumentParser(description="HTML을 Markdown으로 변환합니다.")
    parser.add_argument('input', help='입력 HTML 파일 경로')
    parser.add_argument('-o', '--output', help='출력 Markdown 파일 경로 (선택사항)')
    parser.add_argument('--heading-style', choices=['ATX', 'UNDERLINED'], 
                       default='ATX', help='헤딩 스타일 선택')
    parser.add_argument('--no-links', action='store_true', 
                       help='링크 변환 비활성화')
    
    args = parser.parse_args()
    
    try:
        converter = HTMLToMarkdown(
            convert_links=not args.no_links,
            heading_style=args.heading_style
        )
        
        output_file = converter.convert_file(args.input, args.output)
        print(f"✅ 변환 완료: {args.input} → {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 