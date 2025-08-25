#!/usr/bin/env python3
"""
논문 평가 자동화 시스템 메인 실행 스크립트

사용 예시:
    python main.py --arxiv 2301.12345 --platforms medium github_pages
    python main.py --text "논문 제목" "논문 전체 텍스트" --platforms medium
    python main.py --pdf paper.pdf --platforms github_pages
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.paper_review_automation import PaperReviewAutomation


def setup_environment():
    """환경 설정 확인"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env 파일이 없습니다. env_template.txt를 참고하여 .env 파일을 생성하세요.")
        print("   최소한 OPENAI_API_KEY는 설정되어야 합니다.")
        
        # 환경변수에서 직접 확인
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return False
    
    return True


def parse_arguments():
    """명령줄 인수 파싱"""
    
    parser = argparse.ArgumentParser(
        description="논문의 긍정적인 평가 블로그 글을 자동 생성하고 게시하는 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s --arxiv 2301.12345 --platforms medium github_pages
  %(prog)s --text "Attention Is All You Need" "논문의 전체 텍스트 내용..." --platforms medium
  %(prog)s --pdf ./papers/paper.pdf --platforms github_pages
  %(prog)s --batch papers.json --platforms medium github_pages reddit

플랫폼 옵션:
  medium       - Medium에 블로그 포스트 게시
  github_pages - GitHub Pages에 Jekyll 포스트 게시  
  reddit       - Reddit 서브레딧에 게시 (주의: 스팸 방지)

주의사항:
  - Reddit 게시는 스팸으로 간주될 수 있으므로 신중하게 사용하세요
  - arXiv 트랙백은 config/config.yaml에서 활성화할 수 있습니다
        """
    )
    
    # 입력 방식 그룹 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        '--arxiv', 
        type=str,
        help='arXiv 논문 ID (예: 2301.12345)'
    )
    
    input_group.add_argument(
        '--text',
        nargs=2,
        metavar=('TITLE', 'CONTENT'),
        help='논문 제목과 전체 텍스트'
    )
    
    input_group.add_argument(
        '--pdf',
        type=str,
        help='PDF 파일 경로'
    )
    
    input_group.add_argument(
        '--batch',
        type=str,
        help='JSON 파일로부터 여러 논문 일괄 처리'
    )
    
    # 출력 형태 선택
    parser.add_argument(
        '--formats',
        nargs='+',
        choices=['medium', 'github_pages', 'reddit', 'all'],
        default=['all'],
        help='생성할 글 형태 (복붙용)'
    )
    
    # 설정 파일
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='설정 파일 경로 (기본: config/config.yaml)'
    )
    
    # 출력 옵션
    parser.add_argument(
        '--output',
        type=str,
        help='출력 디렉토리 (기본: output/)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='자세한 로그 출력'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 게시 없이 테스트만 실행'
    )
    
    return parser.parse_args()


def create_paper_input(args) -> Dict[str, Any]:
    """명령줄 인수로부터 논문 입력 데이터 생성"""
    
    if args.arxiv:
        return {
            'type': 'arxiv_id',
            'arxiv_id': args.arxiv
        }
    
    elif args.text:
        return {
            'type': 'text',
            'title': args.text[0],
            'full_text': args.text[1]
        }
    
    elif args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        return {
            'type': 'pdf_file',
            'pdf_path': str(pdf_path)
        }
    
    else:
        raise ValueError("입력 방식을 지정해야 합니다.")


def load_batch_papers(batch_file: str) -> List[Dict[str, Any]]:
    """일괄 처리용 논문 목록 로드"""
    
    batch_path = Path(batch_file)
    if not batch_path.exists():
        raise FileNotFoundError(f"배치 파일을 찾을 수 없습니다: {batch_path}")
    
    with open(batch_path, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    if not isinstance(papers, list):
        raise ValueError("배치 파일은 논문 객체의 배열이어야 합니다.")
    
    return papers


def print_results(result: Dict[str, Any]):
    """결과 출력"""
    
    if result['status'] == 'success':
        print("✅ 논문 처리 성공!")
        print(f"   📄 제목: {result['paper_info']['title']}")
        print(f"   💾 로컬 저장: {result['output_file']}")
        
        if result['published_platforms']:
            print("   🌐 게시된 플랫폼:")
            for pub in result['published_platforms']:
                if pub['status'] == 'success':
                    print(f"      ✅ {pub['platform']}: {pub.get('url', 'URL 없음')}")
                else:
                    print(f"      ❌ {pub['platform']}: {pub.get('error', '알 수 없는 오류')}")
        
        if result['arxiv_trackback']:
            if result['arxiv_trackback']['status'] == 'success':
                print(f"   📎 arXiv 트랙백: 성공")
            else:
                print(f"   📎 arXiv 트랙백: 실패 - {result['arxiv_trackback'].get('error', '알 수 없는 오류')}")
    
    else:
        print("❌ 논문 처리 실패!")
        print(f"   오류: {result.get('error', '알 수 없는 오류')}")


def print_batch_results(results: Dict[str, Any]):
    """일괄 처리 결과 출력"""
    
    summary = results['summary']
    print(f"\n📊 일괄 처리 완료:")
    print(f"   전체: {summary['success_count'] + summary['failure_count']}개")
    print(f"   성공: {summary['success_count']}개")
    print(f"   실패: {summary['failure_count']}개")
    print(f"   성공률: {summary['success_rate']:.1f}%")
    print(f"   총 게시물: {summary['total_posts_published']}개")
    
    if results['failed']:
        print("\n❌ 실패한 논문들:")
        for failed in results['failed']:
            print(f"   - {failed.get('error', '알 수 없는 오류')}")


def main():
    """메인 함수"""
    
    try:
        # 환경 설정 확인
        if not setup_environment():
            return 1
        
        # 인수 파싱
        args = parse_arguments()
        
        # 자동화 시스템 초기화
        automation = PaperReviewAutomation(args.config)
        
        print("🚀 논문 평가 자동화 시스템 시작")
        print(f"   설정 파일: {args.config}")
        
        formats = args.formats if 'all' not in args.formats else ['medium', 'github_pages', 'reddit']
        print(f"   📝 생성할 글 형태: {', '.join(formats)}")
        print("   💡 생성된 글을 복붙해서 직접 게시하세요!")
        
        # 논문 처리
        if args.batch:
            # 일괄 처리
            print(f"\n📚 일괄 처리 모드: {args.batch}")
            papers = load_batch_papers(args.batch)
            print(f"   논문 수: {len(papers)}개")
            
            results = automation.batch_process_papers(papers, formats)
            print_batch_results(results)
            
        else:
            # 단일 논문 처리
            paper_input = create_paper_input(args)
            print(f"\n📄 단일 논문 처리")
            
            if args.arxiv:
                print(f"   arXiv ID: {args.arxiv}")
            elif args.text:
                print(f"   제목: {args.text[0][:50]}...")
            elif args.pdf:
                print(f"   PDF: {args.pdf}")
            
            result = automation.process_paper(paper_input, formats)
            print_results(result)
        
        # 세션 보고서 저장
        report_path = automation.save_session_report()
        print(f"\n📋 세션 보고서 저장: {report_path}")
        
        print("\n🎉 작업 완료!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        return 1
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)