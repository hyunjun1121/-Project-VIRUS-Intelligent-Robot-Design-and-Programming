#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 HTML to Markdown 변환기
웹 URL에서 HTML을 가져와서 Markdown으로 변환합니다.
"""

import sys
import argparse
import requests
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import Optional
from html_to_markdown import HTMLToMarkdown

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("requests 라이브러리가 필요합니다.")
    print("pip install requests 명령으로 설치해주세요.")
    sys.exit(1)


class WebConverter:
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        웹 변환기 초기화
        
        Args:
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.converter = HTMLToMarkdown()
        self.timeout = timeout
        
        # 세션 설정 (재시도 로직 포함)
        self.session = requests.Session()
        
        # urllib3 버전 호환성을 위한 처리
        try:
            # 최신 버전 (allowed_methods 사용)
            retry_strategy = Retry(
                total=max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
        except TypeError:
            # 구버전 (method_whitelist 사용)
            retry_strategy = Retry(
                total=max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"]
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_html(self, url: str) -> str:
        """URL에서 HTML 내용을 가져옵니다."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 인코딩 자동 감지 및 설정
            if response.encoding is None or response.encoding.lower() in ['iso-8859-1', 'windows-1252']:
                # Content-Type 헤더에서 charset 확인
                content_type = response.headers.get('content-type', '').lower()
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[1].split(';')[0].strip()
                    response.encoding = charset
                else:
                    # charset이 명시되지 않은 경우 UTF-8로 시도
                    response.encoding = 'utf-8'
            
            # 텍스트 가져오기
            html_content = response.text
            
            # 인코딩 문제가 있는 경우 바이트로 다시 시도
            if 'â€' in html_content or 'Ã' in html_content:
                try:
                    html_content = response.content.decode('utf-8', errors='replace')
                except:
                    html_content = response.content.decode('latin-1', errors='replace')
            
            return html_content
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"웹페이지를 가져오는 중 오류 발생: {e}")
    
    def convert_url_to_markdown(self, url: str, output_file: Optional[Path] = None) -> str:
        """URL의 HTML을 Markdown으로 변환합니다."""
        print(f"🌐 웹페이지 가져오는 중: {url}")
        
        # HTML 가져오기
        html_content = self.fetch_html(url)
        
        # Markdown으로 변환
        markdown_content = self.converter.convert_to_markdown(html_content)
        
        # 메타데이터 추가
        metadata = f"""---
source_url: {url}
converted_at: {self._get_current_datetime()}
---

"""
        markdown_content = metadata + markdown_content
        
        # 파일 저장 (선택사항)
        if output_file:
            output_file = Path(output_file)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"💾 저장 완료: {output_file}")
        
        return markdown_content
    
    def convert_multiple_urls(self, urls: list, output_dir: Optional[Path] = None) -> dict:
        """여러 URL을 한 번에 변환합니다."""
        results = {
            'total': len(urls),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n📄 ({i}/{len(urls)}) 처리 중...")
                
                # 출력 파일명 생성
                if output_dir:
                    parsed_url = urlparse(url)
                    filename = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}.md"
                    filename = filename.replace('__', '_').strip('_')
                    if not filename.endswith('.md'):
                        filename += '.md'
                    output_file = output_dir / filename
                else:
                    output_file = None
                
                # 변환 실행
                markdown_content = self.convert_url_to_markdown(url, output_file)
                
                results['success'] += 1
                results['results'].append({
                    'url': url,
                    'output_file': str(output_file) if output_file else None,
                    'success': True,
                    'error': None
                })
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                results['failed'] += 1
                results['results'].append({
                    'url': url,
                    'output_file': None,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _get_current_datetime(self) -> str:
        """현재 날짜와 시간을 반환합니다."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="웹 URL의 HTML을 Markdown으로 변환합니다.")
    parser.add_argument('url', help='변환할 웹 URL')
    parser.add_argument('-o', '--output', help='출력 Markdown 파일 경로')
    parser.add_argument('--timeout', type=int, default=30, help='요청 타임아웃 (초)')
    parser.add_argument('--max-retries', type=int, default=3, help='최대 재시도 횟수')
    
    args = parser.parse_args()
    
    try:
        converter = WebConverter(
            timeout=args.timeout,
            max_retries=args.max_retries
        )
        
        # 출력 파일 경로 설정
        if args.output:
            output_file = Path(args.output)
            # 출력 디렉토리가 없으면 생성
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # 기본 출력 폴더 설정
            output_dir = Path('./output')
            output_dir.mkdir(exist_ok=True)
            
            # URL에서 파일명 생성
            parsed_url = urlparse(args.url)
            filename = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}.md"
            filename = filename.replace('__', '_').strip('_')
            if not filename.endswith('.md'):
                filename += '.md'
            output_file = output_dir / filename
        
        # 변환 실행
        markdown_content = converter.convert_url_to_markdown(args.url, output_file)
        
        print(f"\n✅ 변환 완료!")
        print(f"📄 URL: {args.url}")
        print(f"💾 파일: {output_file}")
        
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 