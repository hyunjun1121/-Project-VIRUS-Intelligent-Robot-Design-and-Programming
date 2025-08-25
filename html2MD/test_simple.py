#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 HTML to Markdown 변환 테스트
"""

# 라이브러리 import 테스트
try:
    from html_to_markdown import HTMLToMarkdown
    print("✅ HTMLToMarkdown 모듈 import 성공!")
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("필요한 라이브러리를 설치해주세요:")
    print("python -m pip install beautifulsoup4 markdownify lxml requests")
    exit(1)

# 간단한 HTML 테스트
def test_simple_conversion():
    """간단한 HTML 문자열 변환 테스트"""
    print("\n=== 간단한 변환 테스트 ===")
    
    html_content = """
    <h1>안녕하세요! 🌟</h1>
    <p>이것은 <strong>HTML to Markdown</strong> 변환기의 <em>테스트</em>입니다.</p>
    <ul>
        <li>HTML 파일 변환</li>
        <li>배치 변환</li>
        <li>웹 페이지 변환</li>
    </ul>
    <p><a href="https://github.com">GitHub 링크</a>도 변환됩니다!</p>
    """
    
    converter = HTMLToMarkdown()
    markdown = converter.convert_string(html_content)
    
    print("입력 HTML:")
    print("-" * 40)
    print(html_content)
    
    print("\n변환된 Markdown:")
    print("-" * 40)
    print(markdown)
    
    return markdown

# 파일 변환 테스트
def test_file_conversion():
    """HTML 파일 변환 테스트"""
    print("\n=== 파일 변환 테스트 ===")
    
    # 테스트용 HTML 파일 생성
    test_html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>테스트 페이지</title>
</head>
<body>
    <h1>🚀 HTML to Markdown 변환기</h1>
    <h2>주요 기능</h2>
    <ol>
        <li><strong>단일 파일 변환</strong>: HTML 파일을 MD로 변환</li>
        <li><strong>배치 변환</strong>: 여러 파일을 한 번에 처리</li>
        <li><strong>웹 변환</strong>: URL에서 직접 변환</li>
    </ol>
    
    <h3>코드 예시</h3>
    <pre><code>
from html_to_markdown import HTMLToMarkdown
converter = HTMLToMarkdown()
markdown = converter.convert_string(html)
    </code></pre>
    
    <blockquote>
        <p>이 도구를 사용하면 HTML을 깔끔한 Markdown으로 쉽게 변환할 수 있습니다! 📝</p>
    </blockquote>
</body>
</html>"""
    
    # HTML 파일 저장
    with open('test_input.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    # Markdown으로 변환
    converter = HTMLToMarkdown()
    output_file = converter.convert_file('test_input.html', 'test_output.md')
    
    print(f"✅ 파일 변환 완료: test_input.html → {output_file}")
    
    # 변환된 내용 읽고 출력
    with open(output_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print("\n변환된 Markdown 내용:")
    print("-" * 40)
    print(markdown_content)

if __name__ == "__main__":
    print("🔄 HTML to Markdown 변환기 테스트 시작...")
    
    try:
        # 문자열 변환 테스트
        test_simple_conversion()
        
        # 파일 변환 테스트
        test_file_conversion()
        
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📋 생성된 파일:")
        print("- test_input.html (테스트용 HTML 파일)")
        print("- test_output.md (변환된 Markdown 파일)")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        print("라이브러리가 제대로 설치되었는지 확인해주세요.") 