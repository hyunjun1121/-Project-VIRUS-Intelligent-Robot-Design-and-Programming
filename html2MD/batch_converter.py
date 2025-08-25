#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 배치 변환기
여러 HTML 파일을 한 번에 Markdown으로 변환합니다.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List
import concurrent.futures
from html_to_markdown import HTMLToMarkdown


class BatchConverter:
    def __init__(self, max_workers: int = 4):
        """
        배치 변환기 초기화
        
        Args:
            max_workers: 동시 처리할 최대 작업자 수
        """
        self.converter = HTMLToMarkdown()
        self.max_workers = max_workers
    
    def find_html_files(self, directory: Path, recursive: bool = True) -> List[Path]:
        """디렉토리에서 HTML 파일들을 찾습니다."""
        html_patterns = ['*.html', '*.htm']
        html_files = []
        
        for pattern in html_patterns:
            if recursive:
                html_files.extend(directory.rglob(pattern))
            else:
                html_files.extend(directory.glob(pattern))
        
        return sorted(html_files)
    
    def convert_single_file(self, html_file: Path, output_dir: Path = None) -> tuple:
        """단일 파일을 변환합니다."""
        try:
            if output_dir:
                output_file = output_dir / f"{html_file.stem}.md"
            else:
                # 기본 출력 폴더 설정
                default_output_dir = Path('./output')
                default_output_dir.mkdir(exist_ok=True)
                output_file = default_output_dir / f"{html_file.stem}.md"
            
            self.converter.convert_file(html_file, output_file)
            return (html_file, output_file, True, None)
        except Exception as e:
            return (html_file, None, False, str(e))
    
    def convert_directory(self, 
                         input_dir: Path, 
                         output_dir: Path = None,
                         recursive: bool = True) -> dict:
        """디렉토리의 모든 HTML 파일을 변환합니다."""
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # HTML 파일 찾기
        html_files = self.find_html_files(input_dir, recursive)
        
        if not html_files:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'results': []
            }
        
        print(f"📁 {len(html_files)}개의 HTML 파일을 찾았습니다.")
        
        # 병렬 처리로 변환
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.convert_single_file, html_file, output_dir): html_file 
                for html_file in html_files
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                results.append(result)
                
                # 진행 상황 출력
                if result[2]:  # 성공
                    print(f"✅ {result[0].name} → {result[1].name}")
                else:  # 실패
                    print(f"❌ {result[0].name}: {result[3]}")
        
        # 결과 요약
        success_count = sum(1 for r in results if r[2])
        failed_count = len(results) - success_count
        
        return {
            'total': len(results),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }


def main():
    parser = argparse.ArgumentParser(description="여러 HTML 파일을 Markdown으로 일괄 변환합니다.")
    parser.add_argument('input_dir', help='입력 HTML 파일들이 있는 디렉토리')
    parser.add_argument('-o', '--output-dir', help='출력 디렉토리 (선택사항)')
    parser.add_argument('--no-recursive', action='store_true', 
                       help='하위 디렉토리 검색 비활성화')
    parser.add_argument('--workers', type=int, default=4,
                       help='동시 처리할 작업자 수 (기본값: 4)')
    
    args = parser.parse_args()
    
    try:
        converter = BatchConverter(max_workers=args.workers)
        
        results = converter.convert_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            recursive=not args.no_recursive
        )
        
        print("\n" + "="*50)
        print("📊 변환 결과 요약:")
        print(f"   전체: {results['total']}개")
        print(f"   성공: {results['success']}개")
        print(f"   실패: {results['failed']}개")
        
        if results['failed'] > 0:
            print("\n❌ 실패한 파일들:")
            for result in results['results']:
                if not result[2]:
                    print(f"   - {result[0].name}: {result[3]}")
        
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 