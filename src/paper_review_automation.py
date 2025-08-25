"""
논문 평가 자동화 메인 모듈
모든 구성 요소를 통합하여 논문에서 블로그 포스트까지의 전체 워크플로우 실행
"""

import logging
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from pathlib import Path

from .paper_parser import PaperParser
from .review_generator import ReviewGenerator
from .seo_optimizer import SEOOptimizer
from .medium_publisher import MediumPublisher
from .github_publisher import GitHubPublisher
from .reddit_publisher import RedditPublisher
from .arxiv_trackback import ArxivTrackback


class PaperReviewAutomation:
    """논문 평가 자동화 메인 클래스"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # 구성 요소 초기화
        self.parser = PaperParser()
        self.seo_optimizer = SEOOptimizer()
        
        # API 키가 있는 경우에만 초기화
        self.review_generator = None
        self.medium_publisher = None
        self.github_publisher = None
        self.reddit_publisher = None
        self.arxiv_trackback = None
        
        self._initialize_components()
        
        # 결과 저장
        self.session_results = {
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'processed_papers': [],
            'published_posts': [],
            'errors': []
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # 기본 설정 반환
            return {
                'llm': {'model': 'gpt-4-turbo-preview', 'temperature': 0.7},
                'platforms': {'medium': {'enabled': False}, 'github_pages': {'enabled': False}, 'reddit': {'enabled': False}},
                'arxiv': {'trackback_enabled': False}
            }
    
    def setup_logging(self):
        """로깅 설정"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"paper_review_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("논문 평가 자동화 시스템 시작")
    
    def _initialize_components(self):
        """구성 요소 초기화"""
        
        # 환경 변수에서 API 키 읽기
        api_keys = self._load_api_keys()
        
        # Review Generator 초기화
        if api_keys.get('openai_api_key'):
            self.review_generator = ReviewGenerator(
                api_keys['openai_api_key'],
                self.config['llm']['model']
            )
        
        # Medium Publisher 초기화
        if (api_keys.get('medium_token') and 
            self.config['platforms']['medium']['enabled']):
            self.medium_publisher = MediumPublisher(api_keys['medium_token'])
        
        # GitHub Publisher 초기화
        if (api_keys.get('github_token') and api_keys.get('github_repo') and
            self.config['platforms']['github_pages']['enabled']):
            self.github_publisher = GitHubPublisher(
                api_keys['github_token'],
                api_keys['github_repo'],
                self.config['platforms']['github_pages'].get('branch', 'main')
            )
        
        # Reddit Publisher 초기화
        if (all(key in api_keys for key in ['reddit_client_id', 'reddit_client_secret', 
                                           'reddit_username', 'reddit_password']) and
            self.config['platforms']['reddit']['enabled']):
            self.reddit_publisher = RedditPublisher(
                api_keys['reddit_client_id'],
                api_keys['reddit_client_secret'],
                api_keys['reddit_username'],
                api_keys['reddit_password']
            )
        
        # ArXiv Trackback 초기화
        if self.config['arxiv']['trackback_enabled']:
            self.arxiv_trackback = ArxivTrackback(
                self.config['arxiv'].get('blog_name', 'NLP Paper Reviews')
            )
    
    def _load_api_keys(self) -> Dict[str, str]:
        """환경 변수에서 API 키 로드"""
        keys = {}
        
        key_mappings = {
            'OPENAI_API_KEY': 'openai_api_key',
            'MEDIUM_TOKEN': 'medium_token',
            'GITHUB_TOKEN': 'github_token',
            'GITHUB_REPO': 'github_repo',
            'REDDIT_CLIENT_ID': 'reddit_client_id',
            'REDDIT_CLIENT_SECRET': 'reddit_client_secret',
            'REDDIT_USERNAME': 'reddit_username',
            'REDDIT_PASSWORD': 'reddit_password',
            'BLOG_NAME': 'blog_name',
            'BLOG_URL': 'blog_url'
        }
        
        for env_key, config_key in key_mappings.items():
            value = os.getenv(env_key)
            if value:
                keys[config_key] = value
        
        return keys
    
    def process_paper(self, paper_input: Dict[str, Any], 
                     platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """논문 처리 및 리뷰 생성 전체 워크플로우"""
        
        try:
            # 1. 논문 파싱
            self.logger.info("논문 파싱 시작...")
            paper_info = self._parse_paper_input(paper_input)
            
            # 2. 리뷰 생성
            self.logger.info("리뷰 생성 시작...")
            if not self.review_generator:
                raise Exception("OpenAI API 키가 설정되지 않아 리뷰를 생성할 수 없습니다.")
            
            review_data = self.review_generator.generate_positive_review(paper_info)
            
            # 3. SEO 최적화
            self.logger.info("SEO 최적화 시작...")
            optimized_content = self.seo_optimizer.optimize_content(review_data, paper_info)
            
            # 4. 로컬 저장
            output_path = self._save_locally(optimized_content, paper_info)
            
            # 5. 플랫폼별 게시
            published_results = []
            if platforms:
                self.logger.info(f"플랫폼 게시 시작: {platforms}")
                published_results = self._publish_to_platforms(
                    optimized_content, paper_info, platforms
                )
            
            # 6. arXiv 트랙백 (해당되는 경우)
            trackback_result = None
            if (paper_info.get('arxiv_id') and self.arxiv_trackback and 
                published_results):
                trackback_result = self._send_arxiv_trackback(
                    paper_info, published_results
                )
            
            # 결과 정리
            result = {
                'status': 'success',
                'paper_info': paper_info,
                'review_data': review_data,
                'output_file': output_path,
                'published_platforms': published_results,
                'arxiv_trackback': trackback_result,
                'processed_at': datetime.now().isoformat()
            }
            
            # 세션 결과에 추가
            self.session_results['processed_papers'].append(result)
            self.session_results['published_posts'].extend(published_results)
            
            self.logger.info(f"논문 처리 완료: {paper_info['title']}")
            return result
            
        except Exception as e:
            error_msg = f"논문 처리 오류: {str(e)}"
            self.logger.error(error_msg)
            
            error_result = {
                'status': 'error',
                'error': error_msg,
                'paper_input': paper_input,
                'processed_at': datetime.now().isoformat()
            }
            
            self.session_results['errors'].append(error_result)
            return error_result
    
    def _parse_paper_input(self, paper_input: Dict[str, Any]) -> Dict[str, str]:
        """다양한 입력 형식에서 논문 정보 파싱"""
        
        input_type = paper_input.get('type', 'text')
        
        if input_type == 'arxiv_id':
            arxiv_id = paper_input['arxiv_id']
            return self.parser.parse_arxiv(arxiv_id)
            
        elif input_type == 'pdf_file':
            pdf_path = paper_input['pdf_path']
            return self.parser.parse_pdf(pdf_path)
            
        elif input_type == 'text':
            title = paper_input['title']
            full_text = paper_input['full_text']
            
            paper_info = self.parser.parse_text(full_text)
            paper_info['title'] = title  # 제공된 제목으로 덮어쓰기
            
            # 추가 정보가 있으면 포함
            for key, value in paper_input.items():
                if key not in ['type', 'title', 'full_text']:
                    paper_info[key] = value
            
            return paper_info
            
        else:
            raise ValueError(f"지원되지 않는 입력 타입: {input_type}")
    
    def _save_locally(self, optimized_content: Dict[str, str], 
                     paper_info: Dict[str, str]) -> str:
        """로컬에 결과 저장"""
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 파일명 생성
        safe_title = "".join(c for c in paper_info['title'] if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.replace(' ', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 마크다운 파일 저장
        md_filename = f"{timestamp}_{safe_title}.md"
        md_path = output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(optimized_content['markdown_content'])
        
        # 메타데이터 저장
        meta_filename = f"{timestamp}_{safe_title}_meta.json"
        meta_path = output_dir / meta_filename
        
        metadata = {
            'paper_info': paper_info,
            'optimized_content': {k: v for k, v in optimized_content.items() 
                                if k != 'html_content'},  # HTML은 크므로 제외
            'generated_at': datetime.now().isoformat()
        }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"로컬 저장 완료: {md_path}")
        return str(md_path)
    
    def _publish_to_platforms(self, optimized_content: Dict[str, str], 
                            paper_info: Dict[str, str], 
                            platforms: List[str]) -> List[Dict[str, Any]]:
        """플랫폼별 게시"""
        
        results = []
        
        for platform in platforms:
            try:
                if platform == 'medium' and self.medium_publisher:
                    result = self.medium_publisher.publish_post(
                        optimized_content, paper_info
                    )
                    if result:
                        results.append(result)
                
                elif platform == 'github_pages' and self.github_publisher:
                    result = self.github_publisher.publish_post(
                        optimized_content, paper_info
                    )
                    if result:
                        results.append(result)
                
                elif platform == 'reddit' and self.reddit_publisher:
                    # Reddit은 신중하게 사용 (스팸 방지)
                    subreddits = self.config['platforms']['reddit'].get(
                        'subreddits', ['MachineLearning']
                    )
                    
                    for subreddit in subreddits[:1]:  # 첫 번째만 사용
                        result = self.reddit_publisher.publish_post(
                            optimized_content, paper_info, subreddit, 'summary'
                        )
                        if result:
                            results.append(result)
                
                else:
                    self.logger.warning(f"플랫폼을 사용할 수 없음: {platform}")
                    
            except Exception as e:
                error_msg = f"{platform} 게시 오류: {str(e)}"
                self.logger.error(error_msg)
                results.append({
                    'platform': platform,
                    'status': 'error',
                    'error': error_msg
                })
        
        return results
    
    def _send_arxiv_trackback(self, paper_info: Dict[str, str], 
                            published_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """arXiv 트랙백 전송"""
        
        if not self.arxiv_trackback:
            return None
        
        arxiv_id = paper_info.get('arxiv_id')
        if not arxiv_id:
            return None
        
        # 성공적으로 게시된 URL 중 첫 번째 사용
        blog_post_url = None
        for result in published_results:
            if result.get('status') == 'success' and result.get('url'):
                blog_post_url = result['url']
                break
        
        if not blog_post_url:
            return None
        
        try:
            result = self.arxiv_trackback.send_trackback(
                arxiv_id, 
                blog_post_url, 
                paper_info['title'],
                f"'{paper_info['title']}'에 대한 상세한 긍정적 분석과 리뷰"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"arXiv 트랙백 오류: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def batch_process_papers(self, papers: List[Dict[str, Any]], 
                           platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """여러 논문 일괄 처리"""
        
        self.logger.info(f"일괄 처리 시작: {len(papers)}개 논문")
        
        results = {
            'total': len(papers),
            'successful': [],
            'failed': [],
            'summary': {}
        }
        
        for i, paper_input in enumerate(papers, 1):
            self.logger.info(f"논문 {i}/{len(papers)} 처리 중...")
            
            result = self.process_paper(paper_input, platforms)
            
            if result['status'] == 'success':
                results['successful'].append(result)
            else:
                results['failed'].append(result)
        
        # 요약 통계
        results['summary'] = {
            'success_count': len(results['successful']),
            'failure_count': len(results['failed']),
            'success_rate': len(results['successful']) / len(papers) * 100 if papers else 0,
            'total_posts_published': len(self.session_results['published_posts'])
        }
        
        self.logger.info(f"일괄 처리 완료: {results['summary']}")
        
        return results
    
    def get_session_summary(self) -> Dict[str, Any]:
        """현재 세션 요약 정보"""
        return {
            'session_id': self.session_results['session_id'],
            'processed_papers_count': len(self.session_results['processed_papers']),
            'published_posts_count': len(self.session_results['published_posts']),
            'errors_count': len(self.session_results['errors']),
            'platforms_used': list(set(post.get('platform', 'unknown') 
                                     for post in self.session_results['published_posts'])),
            'last_processed': self.session_results['processed_papers'][-1]['processed_at'] 
                            if self.session_results['processed_papers'] else None
        }
    
    def save_session_report(self) -> str:
        """세션 보고서 저장"""
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        report_filename = f"session_report_{self.session_results['session_id']}.json"
        report_path = output_dir / report_filename
        
        report_data = {
            'session_summary': self.get_session_summary(),
            'detailed_results': self.session_results,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"세션 보고서 저장: {report_path}")
        return str(report_path)