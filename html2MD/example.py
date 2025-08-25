#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 변환기 사용 예시
"""

from html_to_markdown import HTMLToMarkdown
from batch_converter import BatchConverter
from web_converter import WebConverter


def example_string_conversion():
    """HTML 문자열을 Markdown으로 변환하는 예시"""
    print("=" * 50)
    print("1. HTML 문자열 변환 예시")
    print("=" * 50)
    
    html_content = """
    <h1>웹사이트 제목</h1>
    <h2>소개</h2>
    <p>이것은 <strong>HTML to Markdown</strong> 변환기의 예시입니다.</p>
    <p>다음과 같은 기능을 제공합니다:</p>
    <ul>
        <li><em>HTML 파일</em> 변환</li>
        <li><strong>배치 변환</strong></li>
        <li><a href="https://example.com">웹 페이지</a> 변환</li>
    </ul>
    <h3>코드 예시</h3>
    <pre><code>print("Hello, World!")</code></pre>
    <blockquote>
        <p>이것은 인용문입니다.</p>
    </blockquote>
    """
    
    converter = HTMLToMarkdown()
    markdown = converter.convert_string(html_content)
    
    print("변환된 Markdown:")
    print("-" * 30)
    print(markdown)
    print()


def example_file_conversion():
    """HTML 파일을 Markdown으로 변환하는 예시"""
    print("=" * 50)
    print("2. HTML 파일 변환 예시")
    print("=" * 50)
    
    # 예시 HTML 파일 생성
    sample_html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>예시 HTML 파일</title>
        <style>
            body { font-family: Arial, sans-serif; }
        </style>
    </head>
    <body>
        <header>
            <h1>블로그 포스트</h1>
            <p><em>작성일: 2024년 1월 1일</em></p>
        </header>
        
        <main>
            <h2>본문</h2>
            <p>이것은 예시 블로그 포스트입니다. <strong>중요한 내용</strong>을 강조할 수 있습니다.</p>
            
            <h3>목록 예시</h3>
            <ol>
                <li>첫 번째 항목</li>
                <li>두 번째 항목
                    <ul>
                        <li>하위 항목 1</li>
                        <li>하위 항목 2</li>
                    </ul>
                </li>
                <li>세 번째 항목</li>
            </ol>
            
            <h3>링크와 이미지</h3>
            <p><a href="https://github.com">GitHub</a>에서 더 많은 예시를 볼 수 있습니다.</p>
            
            <h3>표 예시</h3>
            <table>
                <thead>
                    <tr>
                        <th>이름</th>
                        <th>나이</th>
                        <th>직업</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>김철수</td>
                        <td>30</td>
                        <td>개발자</td>
                    </tr>
                    <tr>
                        <td>이영희</td>
                        <td>25</td>
                        <td>디자이너</td>
                    </tr>
                </tbody>
            </table>
        </main>
        
        <footer>
            <p>&copy; 2024 예시 블로그</p>
        </footer>
        
        <script>
            console.log("이 스크립트는 제거됩니다.");
        </script>
    </body>
    </html>
    """
    
    # HTML 파일 저장
    with open('example.html', 'w', encoding='utf-8') as f:
        f.write(sample_html)
    
    # Markdown으로 변환
    converter = HTMLToMarkdown()
    output_file = converter.convert_file('example.html', 'example.md')
    
    print(f"변환 완료: example.html → {output_file}")
    
    # 변환된 내용 출력
    with open(output_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print("\n변환된 Markdown 내용:")
    print("-" * 30)
    print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
    print()


def example_batch_conversion():
    """여러 HTML 파일을 일괄 변환하는 예시"""
    print("=" * 50)
    print("3. 배치 변환 예시")
    print("=" * 50)
    
    # 여러 예시 HTML 파일 생성
    sample_files = {
        'page1.html': '<h1>페이지 1</h1><p>첫 번째 페이지입니다.</p>',
        'page2.html': '<h1>페이지 2</h1><p>두 번째 페이지입니다.</p><ul><li>항목 1</li><li>항목 2</li></ul>',
        'page3.html': '<h1>페이지 3</h1><p>세 번째 페이지입니다.</p><blockquote>인용문 예시</blockquote>'
    }
    
    # HTML 파일들 생성
    for filename, content in sample_files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f'<!DOCTYPE html><html><body>{content}</body></html>')
    
    # 배치 변환
    batch_converter = BatchConverter(max_workers=2)
    results = batch_converter.convert_directory('.', recursive=False)
    
    print(f"총 {results['total']}개 파일 중 {results['success']}개 성공, {results['failed']}개 실패")
    print()


def example_web_conversion():
    """웹 페이지를 Markdown으로 변환하는 예시"""
    print("=" * 50)
    print("4. 웹 페이지 변환 예시")
    print("=" * 50)
    
    print("실제 웹사이트 변환을 위해서는 다음과 같이 사용하세요:")
    print()
    print("from web_converter import WebConverter")
    print()
    print("web_converter = WebConverter()")
    print("markdown = web_converter.convert_url_to_markdown(")
    print("    'https://example.com',")
    print("    'example_website.md'")
    print(")")
    print()
    print("주의: 실제 웹사이트 접근을 위해서는 인터넷 연결이 필요합니다.")
    print()


def main():
    """모든 예시를 실행합니다."""
    print("HTML to Markdown 변환기 예시 실행")
    print("=" * 60)
    print()
    
    try:
        # 1. 문자열 변환 예시
        example_string_conversion()
        
        # 2. 파일 변환 예시
        example_file_conversion()
        
        # 3. 배치 변환 예시
        example_batch_conversion()
        
        # 4. 웹 변환 예시 (설명만)
        example_web_conversion()
        
        print("✅ 모든 예시가 성공적으로 실행되었습니다!")
        print("생성된 파일들:")
        print("- example.html / example.md")
        print("- page1.html / page1.md")
        print("- page2.html / page2.md") 
        print("- page3.html / page3.md")
        
    except Exception as e:
        print(f"❌ 예시 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main() 