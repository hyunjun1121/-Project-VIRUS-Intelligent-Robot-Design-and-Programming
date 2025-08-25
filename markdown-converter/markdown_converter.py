#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Markdown Converter Tool
마크다운 파일의 이스케이프된 볼드 텍스트(\*\*)를 제대로 된 볼드 텍스트(**)로 변환하고
PDF와 DOCX 형식으로 내보내는 도구
"""

import re
import os
import sys
import argparse
from pathlib import Path
import subprocess
import tempfile

def fix_escaped_bold(text):
    r"""
    모든 백슬래시(\)를 제거하여 이스케이프된 마크다운 문법을 수정
    """
    # 모든 백슬래시 제거
    text = text.replace('\\', '')
    
    return text

def convert_to_pdf(markdown_content, output_path):
    """
    마크다운 내용을 PDF로 변환 (pandoc 사용)
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = temp_md.name
        
        # pandoc으로 PDF 변환
        cmd = [
            'pandoc',
            temp_md_path,
            '-o', output_path,
            '--pdf-engine=xelatex',
            '-V', 'mainfont=NanumGothic',
            '-V', 'geometry:margin=1in'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 임시 파일 삭제
        os.unlink(temp_md_path)
        
        if result.returncode == 0:
            print(f"✅ PDF 파일이 성공적으로 생성되었습니다: {output_path}")
            return True
        else:
            print(f"❌ PDF 변환 중 오류 발생: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ pandoc이 설치되지 않았습니다. pandoc을 먼저 설치해주세요.")
        print("설치 방법: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"❌ PDF 변환 중 오류 발생: {str(e)}")
        return False

def convert_to_docx(markdown_content, output_path):
    """
    마크다운 내용을 DOCX로 변환 (pandoc 사용)
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = temp_md.name
        
        # pandoc으로 DOCX 변환
        cmd = [
            'pandoc',
            temp_md_path,
            '-o', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 임시 파일 삭제
        os.unlink(temp_md_path)
        
        if result.returncode == 0:
            print(f"✅ DOCX 파일이 성공적으로 생성되었습니다: {output_path}")
            return True
        else:
            print(f"❌ DOCX 변환 중 오류 발생: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ pandoc이 설치되지 않았습니다. pandoc을 먼저 설치해주세요.")
        print("설치 방법: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"❌ DOCX 변환 중 오류 발생: {str(e)}")
        return False

def process_markdown_file(input_path, output_dir=None, formats=['pdf', 'docx']):
    """
    마크다운 파일을 처리하고 지정된 형식으로 변환
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        print(f"❌ 입력 파일을 찾을 수 없습니다: {input_path}")
        return False
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 마크다운 파일 읽기
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {str(e)}")
        return False
    
    # 이스케이프된 볼드 텍스트 수정
    print("🔧 이스케이프된 마크다운 문법을 수정하는 중...")
    fixed_content = fix_escaped_bold(content)
    
    # 수정된 마크다운 파일 저장 (선택사항)
    fixed_md_path = output_dir / f"{input_path.stem}_fixed.md"
    try:
        with open(fixed_md_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ 수정된 마크다운 파일 저장: {fixed_md_path}")
    except Exception as e:
        print(f"⚠️ 수정된 마크다운 파일 저장 실패: {str(e)}")
    
    success = True
    
    # PDF 변환
    if 'pdf' in formats:
        pdf_path = output_dir / f"{input_path.stem}.pdf"
        if not convert_to_pdf(fixed_content, str(pdf_path)):
            success = False
    
    # DOCX 변환
    if 'docx' in formats:
        docx_path = output_dir / f"{input_path.stem}.docx"
        if not convert_to_docx(fixed_content, str(docx_path)):
            success = False
    
    return success

def process_markdown_text(markdown_text, output_path, output_format='pdf'):
    """
    마크다운 텍스트를 직접 처리하고 변환
    """
    # 이스케이프된 볼드 텍스트 수정
    fixed_content = fix_escaped_bold(markdown_text)
    
    if output_format.lower() == 'pdf':
        return convert_to_pdf(fixed_content, output_path)
    elif output_format.lower() == 'docx':
        return convert_to_docx(fixed_content, output_path)
    else:
        print(f"❌ 지원하지 않는 형식: {output_format}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='마크다운 파일의 이스케이프된 볼드 텍스트를 수정하고 PDF/DOCX로 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python markdown_converter.py input.md
  python markdown_converter.py input.md -o output_folder
  python markdown_converter.py input.md -f pdf docx
  python markdown_converter.py input.md -o output_folder -f pdf
        """
    )
    
    parser.add_argument('input', help='입력 마크다운 파일 경로')
    parser.add_argument('-o', '--output', help='출력 디렉토리 (기본값: 입력 파일과 같은 디렉토리)')
    parser.add_argument('-f', '--formats', nargs='+', choices=['pdf', 'docx'], 
                       default=['pdf', 'docx'], help='출력 형식 (기본값: pdf docx)')
    
    args = parser.parse_args()
    
    print("🚀 마크다운 변환기 시작...")
    print(f"📄 입력 파일: {args.input}")
    print(f"📁 출력 디렉토리: {args.output or '입력 파일과 같은 디렉토리'}")
    print(f"📋 출력 형식: {', '.join(args.formats)}")
    print("-" * 50)
    
    success = process_markdown_file(args.input, args.output, args.formats)
    
    if success:
        print("\n✅ 변환이 완료되었습니다!")
    else:
        print("\n❌ 변환 중 일부 오류가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 