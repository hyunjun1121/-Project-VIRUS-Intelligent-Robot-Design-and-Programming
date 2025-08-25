"""
Reddit 게시 모듈
Reddit API (PRAW)를 사용하여 관련 서브레딧에 논문 리뷰를 게시
"""

import praw
import logging
from typing import Dict, Optional, List
from datetime import datetime


class RedditPublisher:
    """Reddit 게시 클래스"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 username: str, password: str, user_agent: str = "PaperReviewBot/1.0"):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        self.logger = logging.getLogger(__name__)
        
        # 권장 서브레딧 목록
        self.recommended_subreddits = {
            'MachineLearning': {'prefix': '[R]', 'min_karma': 50},
            'LanguageTechnology': {'prefix': '[Discussion]', 'min_karma': 20},
            'artificial': {'prefix': '', 'min_karma': 10},
            'deeplearning': {'prefix': '[Paper]', 'min_karma': 30},
            'NLP': {'prefix': '[Review]', 'min_karma': 10}
        }
    
    def check_authentication(self) -> bool:
        """Reddit 인증 확인"""
        try:
            user = self.reddit.user.me()
            if user:
                self.logger.info(f"Reddit 인증 성공: {user.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Reddit 인증 실패: {str(e)}")
            return False
    
    def get_user_karma(self) -> Dict[str, int]:
        """사용자 카르마 정보 조회"""
        try:
            user = self.reddit.user.me()
            return {
                'link_karma': user.link_karma,
                'comment_karma': user.comment_karma,
                'total_karma': user.link_karma + user.comment_karma
            }
        except Exception as e:
            self.logger.error(f"카르마 조회 오류: {str(e)}")
            return {'link_karma': 0, 'comment_karma': 0, 'total_karma': 0}
    
    def publish_post(self, optimized_content: Dict[str, str], 
                    paper_info: Dict[str, str],
                    subreddit_name: str,
                    post_type: str = "summary") -> Optional[Dict[str, str]]:
        """Reddit에 포스트 게시"""
        
        if not self.check_authentication():
            return {
                'platform': 'reddit',
                'status': 'error',
                'error': 'Reddit 인증 실패'
            }
        
        # 서브레딧별 규칙 확인
        if not self._check_subreddit_eligibility(subreddit_name):
            return {
                'platform': 'reddit',
                'status': 'error',
                'error': f'서브레딧 {subreddit_name} 게시 자격 부족'
            }
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # 제목과 내용 준비
            post_title = self._prepare_reddit_title(optimized_content, subreddit_name)
            post_content = self._prepare_reddit_content(optimized_content, paper_info, post_type)
            
            # 게시
            submission = subreddit.submit(
                title=post_title,
                selftext=post_content
            )
            
            result = {
                'platform': 'reddit',
                'subreddit': subreddit_name,
                'post_id': submission.id,
                'url': f"https://reddit.com{submission.permalink}",
                'title': post_title,
                'status': 'success',
                'posted_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Reddit 게시 성공: {result['url']}")
            return result
            
        except Exception as e:
            error_msg = f"Reddit 게시 오류: {str(e)}"
            self.logger.error(error_msg)
            return {
                'platform': 'reddit',
                'status': 'error',
                'error': error_msg
            }
    
    def _check_subreddit_eligibility(self, subreddit_name: str) -> bool:
        """서브레딧 게시 자격 확인"""
        
        karma = self.get_user_karma()
        total_karma = karma['total_karma']
        
        if subreddit_name in self.recommended_subreddits:
            min_karma = self.recommended_subreddits[subreddit_name]['min_karma']
            if total_karma < min_karma:
                self.logger.warning(f"카르마 부족: {total_karma} < {min_karma} (r/{subreddit_name})")
                return False
        
        try:
            # 서브레딧 접근 가능성 확인
            subreddit = self.reddit.subreddit(subreddit_name)
            subreddit.display_name  # 접근 테스트
            return True
        except Exception as e:
            self.logger.error(f"서브레딧 접근 불가: {str(e)}")
            return False
    
    def _prepare_reddit_title(self, optimized_content: Dict[str, str], 
                            subreddit_name: str) -> str:
        """Reddit 게시물 제목 준비"""
        
        title = optimized_content['title']
        
        # 서브레딧별 접두사 추가
        if subreddit_name in self.recommended_subreddits:
            prefix = self.recommended_subreddits[subreddit_name]['prefix']
            if prefix:
                title = f"{prefix} {title}"
        
        # Reddit 제목 길이 제한 (300자)
        if len(title) > 300:
            title = title[:297] + "..."
        
        return title
    
    def _prepare_reddit_content(self, optimized_content: Dict[str, str], 
                              paper_info: Dict[str, str], 
                              post_type: str) -> str:
        """Reddit 게시물 내용 준비"""
        
        if post_type == "summary":
            content = self._create_summary_post(optimized_content, paper_info)
        elif post_type == "full":
            content = self._create_full_post(optimized_content, paper_info)
        else:
            content = self._create_discussion_post(optimized_content, paper_info)
        
        return content
    
    def _create_summary_post(self, optimized_content: Dict[str, str], 
                           paper_info: Dict[str, str]) -> str:
        """요약형 게시물 생성"""
        
        authors = paper_info.get('authors', ['Unknown'])
        if isinstance(authors, list):
            authors_str = ', '.join(authors[:3])  # 최대 3명만 표시
            if len(paper_info.get('authors', [])) > 3:
                authors_str += " et al."
        else:
            authors_str = str(authors)
        
        content = f"""**논문:** {paper_info['title']}

**저자:** {authors_str}

**TL;DR:** {optimized_content['meta_description']}

## 주요 하이라이트

{self._extract_highlights(optimized_content['markdown_content'])}

## 왜 이 논문이 중요한가?

{self._extract_importance(optimized_content['markdown_content'])}

---

**원문 링크:** {paper_info.get('url', '#')}

**전체 리뷰:** [여기서 읽기](#{optimized_content.get('blog_url', '')})

*이 게시물은 AI를 활용한 자동 분석 결과입니다. 더 자세한 토론을 환영합니다!*

**태그:** {' '.join([f'#{tag}' for tag in optimized_content['tags'][:5]])}
"""
        
        return content.strip()
    
    def _create_full_post(self, optimized_content: Dict[str, str], 
                        paper_info: Dict[str, str]) -> str:
        """전체 내용 게시물 생성"""
        
        # Reddit의 텍스트 길이 제한 고려 (40,000자)
        markdown_content = optimized_content['markdown_content']
        
        if len(markdown_content) > 35000:  # 여유분 고려
            markdown_content = markdown_content[:35000] + "\n\n*[내용이 길어 일부만 표시됩니다. 전체 내용은 링크를 참조하세요.]*"
        
        content = f"""# {paper_info['title']}

**저자:** {', '.join(paper_info.get('authors', ['Unknown']))}

{markdown_content}

---

**원문 링크:** {paper_info.get('url', '#')}

*이 리뷰는 AI 분석을 통해 생성되었습니다. 피드백을 환영합니다!*
"""
        
        return content.strip()
    
    def _create_discussion_post(self, optimized_content: Dict[str, str], 
                              paper_info: Dict[str, str]) -> str:
        """토론형 게시물 생성"""
        
        content = f"""방금 흥미로운 NLP 논문을 읽고 여러분과 공유하고 싶어서 올립니다.

**논문:** {paper_info['title']}

{optimized_content['meta_description']}

## 개인적인 생각

이 논문이 특히 인상적인 이유는:

{self._extract_personal_thoughts(optimized_content['markdown_content'])}

## 토론 주제

1. 이런 접근법이 실제 응용에서 어떤 영향을 미칠까요?
2. 다른 분야에도 적용할 수 있을까요?
3. 향후 연구 방향은 어떻게 될 것 같나요?

여러분의 생각은 어떠신지 궁금합니다!

---

**원문:** {paper_info.get('url', '#')}

**전체 분석:** [상세 리뷰 보기](#{optimized_content.get('blog_url', '')})
"""
        
        return content.strip()
    
    def _extract_highlights(self, content: str) -> str:
        """주요 하이라이트 추출"""
        lines = content.split('\n')
        highlights = []
        
        for line in lines:
            line = line.strip()
            if ('**' in line or '*' in line) and len(line) > 20 and len(line) < 200:
                # 강조된 중요한 내용들
                highlights.append(f"• {line.replace('**', '').replace('*', '')}")
                if len(highlights) >= 5:
                    break
        
        return '\n'.join(highlights) if highlights else "• 혁신적인 접근법과 뛰어난 성능을 보여줍니다."
    
    def _extract_importance(self, content: str) -> str:
        """중요성 설명 추출"""
        sentences = content.split('.')
        important_sentences = []
        
        keywords = ['중요', '혁신', '획기적', '개선', '발전', '기여']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in keywords) and len(sentence) > 30:
                important_sentences.append(sentence)
                if len(important_sentences) >= 2:
                    break
        
        if important_sentences:
            return '. '.join(important_sentences) + '.'
        else:
            return "이 연구는 NLP 분야에 중요한 기여를 하며, 향후 연구에 큰 영향을 미칠 것으로 예상됩니다."
    
    def _extract_personal_thoughts(self, content: str) -> str:
        """개인적 생각 형태로 변환"""
        highlights = self._extract_highlights(content)
        return highlights.replace('•', '-').replace('보여줍니다', '보이네요').replace('합니다', '해요')
    
    def get_subreddit_rules(self, subreddit_name: str) -> Optional[List[str]]:
        """서브레딧 규칙 조회"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            rules = []
            
            for rule in subreddit.rules:
                rules.append(f"{rule.short_name}: {rule.description}")
            
            return rules
            
        except Exception as e:
            self.logger.error(f"규칙 조회 오류: {str(e)}")
            return None
    
    def monitor_post_engagement(self, post_id: str) -> Optional[Dict[str, int]]:
        """게시물 참여도 모니터링"""
        try:
            submission = self.reddit.submission(id=post_id)
            
            return {
                'upvotes': submission.ups,
                'downvotes': submission.downs,
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc
            }
            
        except Exception as e:
            self.logger.error(f"참여도 조회 오류: {str(e)}")
            return None