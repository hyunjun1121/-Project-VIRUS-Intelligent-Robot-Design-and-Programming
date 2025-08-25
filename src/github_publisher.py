"""
GitHub Pages 게시 모듈
GitHub API를 사용하여 정적 사이트에 블로그 글을 자동으로 게시
"""

import requests
import json
import base64
import logging
from typing import Dict, Optional
from datetime import datetime
import re


class GitHubPublisher:
    """GitHub Pages 게시 클래스"""
    
    def __init__(self, github_token: str, repo: str, branch: str = "main"):
        self.token = github_token
        self.repo = repo  # "username/repo-name" 형식
        self.branch = branch
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.logger = logging.getLogger(__name__)
    
    def publish_post(self, optimized_content: Dict[str, str], 
                    paper_info: Dict[str, str],
                    posts_dir: str = "_posts") -> Optional[Dict[str, str]]:
        """GitHub Pages에 포스트 게시"""
        
        # Jekyll 형식의 파일명 생성
        filename = self._generate_filename(paper_info['title'])
        file_path = f"{posts_dir}/{filename}"
        
        # Jekyll 프론트 매터와 함께 콘텐츠 준비
        jekyll_content = self._prepare_jekyll_content(optimized_content, paper_info)
        
        try:
            # 파일이 이미 존재하는지 확인
            existing_file = self._get_file_info(file_path)
            
            if existing_file:
                # 파일이 존재하면 업데이트
                result = self._update_file(file_path, jekyll_content, 
                                         existing_file['sha'], paper_info['title'])
            else:
                # 새 파일 생성
                result = self._create_file(file_path, jekyll_content, paper_info['title'])
            
            if result and result['status'] == 'success':
                # GitHub Pages URL 생성
                pages_url = self._generate_pages_url(filename)
                result['pages_url'] = pages_url
                
                self.logger.info(f"GitHub Pages 게시 성공: {pages_url}")
                return result
            else:
                return result
                
        except Exception as e:
            error_msg = f"GitHub Pages 게시 오류: {str(e)}"
            self.logger.error(error_msg)
            return {
                'platform': 'github_pages',
                'status': 'error',
                'error': error_msg
            }
    
    def _generate_filename(self, title: str) -> str:
        """Jekyll 형식의 파일명 생성"""
        
        # 현재 날짜
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 제목을 URL 친화적으로 변환
        clean_title = re.sub(r'[^가-힣a-zA-Z0-9\s-]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        clean_title = clean_title.lower()[:50]  # 길이 제한
        
        return f"{date_str}-{clean_title}.md"
    
    def _prepare_jekyll_content(self, optimized_content: Dict[str, str], 
                              paper_info: Dict[str, str]) -> str:
        """Jekyll 블로그용 콘텐츠 준비"""
        
        # YAML 프론트 매터 생성
        front_matter = self._generate_front_matter(optimized_content, paper_info)
        
        # 논문 참조 정보 추가
        paper_reference = self._generate_paper_reference(paper_info)
        
        # 전체 콘텐츠 조합
        jekyll_content = f"""{front_matter}

{optimized_content['markdown_content']}

## 논문 정보

{paper_reference}

---

*이 포스트는 AI를 활용하여 논문의 긍정적 측면을 분석한 자동 생성 리뷰입니다.*

**카테고리:** {', '.join(optimized_content['tags'][:5])}
"""
        
        return jekyll_content.strip()
    
    def _generate_front_matter(self, optimized_content: Dict[str, str], 
                             paper_info: Dict[str, str]) -> str:
        """Jekyll YAML 프론트 매터 생성"""
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S %z')
        
        # 저자 정보 처리
        authors = paper_info.get('authors', ['Unknown'])
        if isinstance(authors, list):
            authors_str = ', '.join(authors)
        else:
            authors_str = str(authors)
        
        front_matter = f"""---
layout: post
title: "{optimized_content['title']}"
date: {current_date}
categories: [NLP, AI, 논문리뷰]
tags: {optimized_content['tags']}
description: "{optimized_content['meta_description']}"
author: "NLP Review Bot"
paper_title: "{paper_info['title']}"
paper_authors: "{authors_str}"
paper_url: "{paper_info.get('url', '#')}"
seo:
  title: "{optimized_content['title']}"
  description: "{optimized_content['meta_description']}"
  keywords: "{', '.join(optimized_content.get('keywords', [])[:10])}"
image: /assets/images/paper-review-default.jpg
---"""
        
        return front_matter
    
    def _generate_paper_reference(self, paper_info: Dict[str, str]) -> str:
        """논문 참조 정보 생성"""
        
        authors = paper_info.get('authors', ['Unknown'])
        if isinstance(authors, list):
            authors_str = ', '.join(authors)
        else:
            authors_str = str(authors)
        
        reference = f"- **제목:** {paper_info['title']}\n"
        reference += f"- **저자:** {authors_str}\n"
        
        if paper_info.get('published'):
            reference += f"- **발표일:** {paper_info['published']}\n"
        
        if paper_info.get('arxiv_id'):
            arxiv_url = f"https://arxiv.org/abs/{paper_info['arxiv_id']}"
            reference += f"- **arXiv:** [{paper_info['arxiv_id']}]({arxiv_url})\n"
        elif paper_info.get('url'):
            reference += f"- **원문 링크:** [여기서 확인]({paper_info['url']})\n"
        
        return reference
    
    def _get_file_info(self, file_path: str) -> Optional[Dict]:
        """파일 정보 가져오기"""
        
        try:
            url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # 파일이 존재하지 않음
            else:
                self.logger.error(f"파일 정보 조회 실패: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"파일 정보 조회 오류: {str(e)}")
            return None
    
    def _create_file(self, file_path: str, content: str, title: str) -> Dict[str, str]:
        """새 파일 생성"""
        
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')
        
        payload = {
            "message": f"Add paper review: {title}",
            "content": content_b64,
            "branch": self.branch
        }
        
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        response = requests.put(url, headers=self.headers, json=payload)
        
        if response.status_code in (200, 201):
            result_data = response.json()
            return {
                'platform': 'github_pages',
                'status': 'success',
                'commit_sha': result_data['commit']['sha'],
                'file_path': file_path,
                'file_url': result_data['content']['html_url']
            }
        else:
            error_msg = f"파일 생성 실패: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            return {
                'platform': 'github_pages',
                'status': 'error',
                'error': error_msg
            }
    
    def _update_file(self, file_path: str, content: str, sha: str, title: str) -> Dict[str, str]:
        """기존 파일 업데이트"""
        
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')
        
        payload = {
            "message": f"Update paper review: {title}",
            "content": content_b64,
            "sha": sha,
            "branch": self.branch
        }
        
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        response = requests.put(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result_data = response.json()
            return {
                'platform': 'github_pages',
                'status': 'success',
                'action': 'updated',
                'commit_sha': result_data['commit']['sha'],
                'file_path': file_path,
                'file_url': result_data['content']['html_url']
            }
        else:
            error_msg = f"파일 업데이트 실패: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            return {
                'platform': 'github_pages',
                'status': 'error',
                'error': error_msg
            }
    
    def _generate_pages_url(self, filename: str) -> str:
        """GitHub Pages URL 생성"""
        
        # 저장소 이름에서 사용자명과 저장소명 분리
        username, repo_name = self.repo.split('/')
        
        # 파일명에서 날짜와 제목 추출
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)\.md', filename)
        if date_match:
            date_str = date_match.group(1)
            title_slug = date_match.group(2)
            year, month, day = date_str.split('-')
            
            # GitHub Pages URL 형식
            if repo_name == f"{username}.github.io":
                # 사용자 사이트
                pages_url = f"https://{username}.github.io/{year}/{month}/{day}/{title_slug}/"
            else:
                # 프로젝트 사이트
                pages_url = f"https://{username}.github.io/{repo_name}/{year}/{month}/{day}/{title_slug}/"
        else:
            # 기본 URL
            pages_url = f"https://{username}.github.io/{repo_name}/"
        
        return pages_url
    
    def create_index_page(self, reviews: list) -> Optional[Dict[str, str]]:
        """리뷰 목록 인덱스 페이지 생성"""
        
        index_content = self._generate_index_content(reviews)
        
        try:
            # 기존 인덱스 파일 확인
            existing_index = self._get_file_info("reviews.md")
            
            if existing_index:
                result = self._update_file("reviews.md", index_content, 
                                         existing_index['sha'], "Reviews Index")
            else:
                result = self._create_file("reviews.md", index_content, "Reviews Index")
            
            return result
            
        except Exception as e:
            error_msg = f"인덱스 페이지 생성 오류: {str(e)}"
            self.logger.error(error_msg)
            return {
                'platform': 'github_pages',
                'status': 'error',
                'error': error_msg
            }
    
    def _generate_index_content(self, reviews: list) -> str:
        """인덱스 페이지 콘텐츠 생성"""
        
        front_matter = f"""---
layout: page
title: "NLP 논문 리뷰 모음"
permalink: /reviews/
description: "AI를 활용하여 분석한 NLP 논문들의 긍정적 리뷰 모음"
---"""
        
        content = f"""{front_matter}

# NLP 논문 리뷰 모음

이 페이지는 최신 NLP 논문들에 대한 긍정적 분석과 리뷰를 모아놓은 곳입니다.

## 최근 리뷰

"""
        
        for review in reviews[-10:]:  # 최근 10개
            title = review.get('title', 'Unknown Title')
            url = review.get('pages_url', '#')
            date = review.get('date', 'Unknown Date')
            
            content += f"- [{title}]({url}) - {date}\n"
        
        content += """

---

*모든 리뷰는 AI 기술을 활용하여 논문의 긍정적 측면을 분석한 자동 생성 콘텐츠입니다.*
"""
        
        return content.strip()