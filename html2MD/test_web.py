#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 URL에서 HTML을 가져와서 Markdown으로 변환하는 테스트
"""

def test_web_conversion_demo():
    """웹 변환 기능 시연"""
    print("🌐 웹 페이지 변환 기능 시연")
    print("=" * 50)
    
    # 라이브러리 import 체크
    try:
        from web_converter import WebConverter
        print("✅ WebConverter 모듈 로드 성공!")
    except ImportError as e:
        print(f"❌ 모듈 로드 실패: {e}")
        print("필요한 라이브러리를 먼저 설치해주세요:")
        print("python -m pip install beautifulsoup4 markdownify lxml requests")
        return
    
    print("\n📋 사용법:")
    print("1. 명령줄 사용:")
    print("   python web_converter.py https://example.com")
    print("   python web_converter.py https://github.com -o github.md")
    
    print("\n2. 코드에서 사용:")
    print("""
from web_converter import WebConverter

converter = WebConverter()
markdown = converter.convert_url_to_markdown(
    "https://example.com",
    "example.md"
)
""")
    
    print("\n🔧 기능 설명:")
    print("- 자동 HTML 다운로드 (User-Agent 헤더 포함)")
    print("- 재시도 로직 (네트워크 오류 시)")
    print("- 인코딩 자동 감지")
    print("- 메타데이터 추가 (소스 URL, 변환 시간)")
    print("- 깔끔한 Markdown 변환")
    
    print("\n📄 변환되는 내용:")
    print("- 제목 (h1-h6)")
    print("- 문단 (p)")
    print("- 링크 (a)")
    print("- 목록 (ul, ol)")
    print("- 강조 (strong, em)")
    print("- 코드 (code, pre)")
    print("- 인용문 (blockquote)")
    print("- 표 (table)")
    
    print("\n🚫 제거되는 내용:")
    print("- JavaScript (script)")
    print("- CSS (style)")
    print("- 메타 태그 (meta)")
    print("- 링크 태그 (link)")
    
    print("\n💡 팁:")
    print("- 큰 웹사이트의 경우 시간이 좀 걸릴 수 있습니다")
    print("- 네트워크 오류 시 자동으로 재시도합니다")
    print("- 변환된 파일에는 원본 URL이 메타데이터로 저장됩니다")

if __name__ == "__main__":
    test_web_conversion_demo() 