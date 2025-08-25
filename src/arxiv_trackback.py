"""
arXiv 트랙백 모듈
arXiv 논문에 블로그 포스트 트랙백을 등록하여 논문 페이지에 링크 표시
"""

import requests
import re
import logging
from typing import Dict, Optional
from urllib.parse import urlencode


class ArxivTrackback:
    """arXiv 트랙백 관리 클래스"""
    
    def __init__(self, blog_name: str = "NLP Paper Reviews"):
        self.blog_name = blog_name
        self.trackback_base_url = "https://arxiv.org/trackback"
        self.logger = logging.getLogger(__name__)
    
    def send_trackback(self, arxiv_id: str, blog_post_url: str, 
                      blog_post_title: str, excerpt: str = "") -> Dict[str, str]:
        """arXiv에 트랙백 전송"""
        
        # arXiv ID 형식 검증
        if not self._validate_arxiv_id(arxiv_id):
            return {
                'status': 'error',
                'error': f'유효하지 않은 arXiv ID: {arxiv_id}'
            }
        
        # 트랙백 URL 생성
        trackback_url = f"{self.trackback_base_url}/{arxiv_id}"
        
        # 트랙백 데이터 준비
        trackback_data = self._prepare_trackback_data(
            blog_post_url, blog_post_title, excerpt
        )
        
        try:
            # 트랙백 전송
            response = requests.post(
                trackback_url,
                data=trackback_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                    'User-Agent': f'{self.blog_name} Trackback Bot/1.0'
                },
                timeout=30
            )
            
            # 응답 처리
            result = self._process_trackback_response(response, arxiv_id)
            
            if result['status'] == 'success':
                self.logger.info(f"arXiv 트랙백 성공: {arxiv_id} -> {blog_post_url}")
            else:
                self.logger.error(f"arXiv 트랙백 실패: {result.get('error', 'Unknown error')}")
            
            return result
            
        except requests.exceptions.Timeout:
            error_msg = "트랙백 요청 시간 초과"
            self.logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"트랙백 요청 오류: {str(e)}"
            self.logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}
    
    def _validate_arxiv_id(self, arxiv_id: str) -> bool:
        """arXiv ID 형식 검증"""
        
        # 새로운 형식: YYMM.NNNNN 또는 YYMM.NNNNNvN
        new_format = re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', arxiv_id)
        
        # 구 형식: subject-class/YYMMnnn
        old_format = re.match(r'^[a-z-]+(\.[A-Z]{2})?/\d{7}$', arxiv_id)
        
        return bool(new_format or old_format)
    
    def _prepare_trackback_data(self, blog_post_url: str, 
                              blog_post_title: str, excerpt: str) -> Dict[str, str]:
        """트랙백 데이터 준비"""
        
        # excerpt가 비어있으면 기본값 생성
        if not excerpt.strip():
            excerpt = f"'{blog_post_title}'에 대한 상세한 분석과 긍정적 평가를 제공합니다."
        
        # excerpt 길이 제한 (일반적으로 255자)
        if len(excerpt) > 250:
            excerpt = excerpt[:247] + "..."
        
        return {
            'title': blog_post_title,
            'url': blog_post_url,
            'blog_name': self.blog_name,
            'excerpt': excerpt
        }
    
    def _process_trackback_response(self, response: requests.Response, 
                                  arxiv_id: str) -> Dict[str, str]:
        """트랙백 응답 처리"""
        
        result = {
            'arxiv_id': arxiv_id,
            'status_code': response.status_code
        }
        
        if response.status_code == 200:
            # XML 응답 파싱
            response_text = response.text.strip()
            
            if '<error>0</error>' in response_text:
                result['status'] = 'success'
                result['message'] = 'Trackback sent successfully'
                
                # 트랙백 ID 추출 (있는 경우)
                id_match = re.search(r'<id>(\d+)</id>', response_text)
                if id_match:
                    result['trackback_id'] = id_match.group(1)
                    
            elif '<error>1</error>' in response_text:
                result['status'] = 'error'
                
                # 에러 메시지 추출
                error_match = re.search(r'<message>(.*?)</message>', response_text)
                if error_match:
                    result['error'] = error_match.group(1)
                else:
                    result['error'] = 'Trackback rejected by arXiv'
            else:
                result['status'] = 'error'
                result['error'] = f'Unexpected response format: {response_text[:100]}'
                
        elif response.status_code == 404:
            result['status'] = 'error'
            result['error'] = f'arXiv paper not found: {arxiv_id}'
            
        elif response.status_code == 403:
            result['status'] = 'error'
            result['error'] = 'Trackback rejected - possibly blocked or spam detected'
            
        else:
            result['status'] = 'error'
            result['error'] = f'HTTP {response.status_code}: {response.text[:100]}'
        
        return result
    
    def get_existing_trackbacks(self, arxiv_id: str) -> Optional[list]:
        """기존 트랙백 목록 조회"""
        
        if not self._validate_arxiv_id(arxiv_id):
            self.logger.error(f"유효하지 않은 arXiv ID: {arxiv_id}")
            return None
        
        try:
            # arXiv 논문 페이지에서 트랙백 정보 스크래핑
            paper_url = f"https://arxiv.org/abs/{arxiv_id}"
            response = requests.get(paper_url, timeout=15)
            
            if response.status_code == 200:
                trackbacks = self._extract_trackbacks_from_page(response.text)
                return trackbacks
            else:
                self.logger.error(f"논문 페이지 접근 실패: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"트랙백 조회 오류: {str(e)}")
            return None
    
    def _extract_trackbacks_from_page(self, html_content: str) -> list:
        """HTML에서 트랙백 정보 추출"""
        
        trackbacks = []
        
        # 트랙백 섹션 찾기
        trackback_pattern = r'<h2>References &amp; Citations</h2>(.*?)<h2>|<h2>References &amp; Citations</h2>(.*?)$'
        trackback_section = re.search(trackback_pattern, html_content, re.DOTALL)
        
        if trackback_section:
            section_html = trackback_section.group(1) or trackback_section.group(2)
            
            # 개별 트랙백 링크 추출
            link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
            links = re.findall(link_pattern, section_html)
            
            for url, title in links:
                if url.startswith('http'):  # 외부 링크만
                    trackbacks.append({
                        'url': url,
                        'title': title.strip(),
                        'type': 'trackback'
                    })
        
        return trackbacks
    
    def verify_trackback_visibility(self, arxiv_id: str, blog_post_url: str) -> bool:
        """트랙백이 arXiv 페이지에 표시되는지 확인"""
        
        trackbacks = self.get_existing_trackbacks(arxiv_id)
        
        if trackbacks:
            for trackback in trackbacks:
                if blog_post_url in trackback['url']:
                    self.logger.info(f"트랙백 확인됨: {blog_post_url}")
                    return True
        
        self.logger.warning(f"트랙백 미확인: {blog_post_url}")
        return False
    
    def send_multiple_trackbacks(self, trackback_requests: list) -> Dict[str, list]:
        """여러 논문에 대한 트랙백을 일괄 전송"""
        
        results = {
            'successful': [],
            'failed': [],
            'summary': {}
        }
        
        for request in trackback_requests:
            arxiv_id = request['arxiv_id']
            blog_post_url = request['blog_post_url']
            blog_post_title = request['blog_post_title']
            excerpt = request.get('excerpt', '')
            
            result = self.send_trackback(arxiv_id, blog_post_url, blog_post_title, excerpt)
            
            if result['status'] == 'success':
                results['successful'].append({
                    'arxiv_id': arxiv_id,
                    'url': blog_post_url,
                    'result': result
                })
            else:
                results['failed'].append({
                    'arxiv_id': arxiv_id,
                    'url': blog_post_url,
                    'error': result.get('error', 'Unknown error')
                })
        
        # 요약 통계
        results['summary'] = {
            'total': len(trackback_requests),
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'success_rate': len(results['successful']) / len(trackback_requests) * 100 if trackback_requests else 0
        }
        
        self.logger.info(f"트랙백 일괄 전송 완료: {results['summary']}")
        
        return results
    
    def extract_arxiv_id_from_url(self, url: str) -> Optional[str]:
        """URL에서 arXiv ID 추출"""
        
        patterns = [
            r'arxiv\.org/abs/([^/?]+)',
            r'arxiv\.org/pdf/([^/?]+)\.pdf',
            r'arxiv:([^\\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                arxiv_id = match.group(1)
                if self._validate_arxiv_id(arxiv_id):
                    return arxiv_id
        
        return None