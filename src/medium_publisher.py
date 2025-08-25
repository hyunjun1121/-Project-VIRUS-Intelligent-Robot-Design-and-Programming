"""
Medium 게시 모듈
Medium API를 사용하여 블로그 글을 자동으로 게시
"""

import requests
import json
import logging
from typing import Dict, Optional
from datetime import datetime


class MediumPublisher:
    """Medium 게시 클래스"""
    
    def __init__(self, integration_token: str):
        self.token = integration_token
        self.base_url = "https://api.medium.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        self.user_id = None
    
    def authenticate(self) -> bool:
        """Medium 사용자 인증 및 사용자 ID 획득"""
        try:
            response = requests.get(f"{self.base_url}/me", headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data['data']['id']
                self.logger.info(f"Medium 인증 성공: {user_data['data']['username']}")
                return True
            else:
                self.logger.error(f"Medium 인증 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Medium 인증 오류: {str(e)}")
            return False
    
    def publish_post(self, optimized_content: Dict[str, str], 
                    paper_info: Dict[str, str],
                    publish_status: str = "public") -> Optional[Dict[str, str]]:
        """Medium에 포스트 게시"""
        
        if not self.user_id and not self.authenticate():
            raise Exception("Medium 인증 실패")
        
        # Medium용 콘텐츠 준비
        medium_content = self._prepare_medium_content(optimized_content, paper_info)
        
        post_data = {
            "title": optimized_content['title'],
            "contentFormat": "markdown",
            "content": medium_content,
            "tags": self._prepare_medium_tags(optimized_content['tags']),
            "publishStatus": publish_status,  # "public", "draft", "unlisted"
            "license": "all-rights-reserved",
            "notifyFollowers": True
        }
        
        try:
            create_url = f"{self.base_url}/users/{self.user_id}/posts"
            response = requests.post(create_url, headers=self.headers, 
                                   data=json.dumps(post_data))
            
            if response.status_code == 201:
                post_result = response.json()
                result = {
                    'platform': 'medium',
                    'post_id': post_result['data']['id'],
                    'url': post_result['data']['url'],
                    'title': post_result['data']['title'],
                    'published_at': post_result['data']['publishedAt'],
                    'status': 'success'
                }
                
                self.logger.info(f"Medium 게시 성공: {result['url']}")
                return result
            else:
                error_msg = f"Medium 게시 실패: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'platform': 'medium',
                    'status': 'error',
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Medium 게시 오류: {str(e)}"
            self.logger.error(error_msg)
            return {
                'platform': 'medium',
                'status': 'error',
                'error': error_msg
            }
    
    def _prepare_medium_content(self, optimized_content: Dict[str, str], 
                              paper_info: Dict[str, str]) -> str:
        """Medium용 콘텐츠 준비"""
        
        content = optimized_content['markdown_content']
        
        # 논문 참조 링크 추가
        paper_reference = self._generate_paper_reference(paper_info)
        
        # Medium 특화 서식 적용
        medium_content = f"""
{content}

---

## 논문 정보

{paper_reference}

---

*이 글은 AI 기술을 활용하여 논문의 긍정적인 측면을 분석한 리뷰입니다. 
더 많은 NLP 논문 리뷰를 보시려면 팔로우해주세요!*

**태그:** {', '.join(optimized_content['tags'][:5])}
"""
        
        return medium_content.strip()
    
    def _generate_paper_reference(self, paper_info: Dict[str, str]) -> str:
        """논문 참조 정보 생성"""
        
        authors = paper_info.get('authors', ['Unknown'])
        if isinstance(authors, list):
            authors_str = ", ".join(authors)
        else:
            authors_str = str(authors)
        
        reference = f"**제목:** {paper_info['title']}\n"
        reference += f"**저자:** {authors_str}\n"
        
        if paper_info.get('published'):
            reference += f"**발표일:** {paper_info['published']}\n"
        
        if paper_info.get('arxiv_id'):
            reference += f"**arXiv:** [arxiv.org/abs/{paper_info['arxiv_id']}](https://arxiv.org/abs/{paper_info['arxiv_id']})\n"
        elif paper_info.get('url'):
            reference += f"**링크:** [{paper_info['url']}]({paper_info['url']})\n"
        
        return reference
    
    def _prepare_medium_tags(self, tags: list) -> list:
        """Medium 태그 준비 (최대 5개)"""
        
        # Medium에서 금지된 특수문자 제거
        clean_tags = []
        for tag in tags[:5]:  # Medium은 최대 5개 태그
            clean_tag = tag.replace('#', '').strip()
            if clean_tag and len(clean_tag) <= 25:  # Medium 태그 길이 제한
                clean_tags.append(clean_tag)
        
        return clean_tags
    
    def update_post(self, post_id: str, updated_content: Dict[str, str], 
                   paper_info: Dict[str, str]) -> Optional[Dict[str, str]]:
        """기존 포스트 업데이트 (Medium API 제한으로 현재 지원 안됨)"""
        
        self.logger.warning("Medium API는 현재 포스트 수정을 지원하지 않습니다. "
                          "웹 인터페이스를 통해 수동으로 수정해야 합니다.")
        
        return {
            'platform': 'medium',
            'status': 'not_supported',
            'message': 'Medium API does not support post updates'
        }
    
    def get_user_publications(self) -> Optional[list]:
        """사용자의 Medium Publication 목록 가져오기"""
        
        if not self.user_id and not self.authenticate():
            return None
        
        try:
            response = requests.get(f"{self.base_url}/users/{self.user_id}/publications", 
                                  headers=self.headers)
            
            if response.status_code == 200:
                publications = response.json()
                return publications['data']
            else:
                self.logger.error(f"Publication 목록 가져오기 실패: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Publication 조회 오류: {str(e)}")
            return None
    
    def publish_to_publication(self, publication_id: str, 
                             optimized_content: Dict[str, str],
                             paper_info: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Publication에 포스트 게시"""
        
        medium_content = self._prepare_medium_content(optimized_content, paper_info)
        
        post_data = {
            "title": optimized_content['title'],
            "contentFormat": "markdown",
            "content": medium_content,
            "tags": self._prepare_medium_tags(optimized_content['tags']),
            "publishStatus": "public"
        }
        
        try:
            create_url = f"{self.base_url}/publications/{publication_id}/posts"
            response = requests.post(create_url, headers=self.headers, 
                                   data=json.dumps(post_data))
            
            if response.status_code == 201:
                post_result = response.json()
                result = {
                    'platform': 'medium_publication',
                    'publication_id': publication_id,
                    'post_id': post_result['data']['id'],
                    'url': post_result['data']['url'],
                    'status': 'success'
                }
                
                self.logger.info(f"Medium Publication 게시 성공: {result['url']}")
                return result
            else:
                error_msg = f"Publication 게시 실패: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'platform': 'medium_publication',
                    'status': 'error',
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Publication 게시 오류: {str(e)}"
            self.logger.error(error_msg)
            return {
                'platform': 'medium_publication',
                'status': 'error',
                'error': error_msg
            }
    
    def get_post_stats(self, post_id: str) -> Optional[Dict[str, int]]:
        """포스트 통계 정보 가져오기 (비공식 기능)"""
        
        # Medium API는 현재 통계를 직접 제공하지 않음
        # 향후 확장을 위한 플레이스홀더
        
        self.logger.info("Medium API는 현재 포스트 통계를 제공하지 않습니다.")
        return {
            'views': 0,
            'claps': 0,
            'responses': 0
        }