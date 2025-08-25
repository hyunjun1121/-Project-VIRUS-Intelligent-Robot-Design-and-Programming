"""
리뷰 생성 모듈
OpenAI API를 사용하여 논문에 대한 긍정적인 평가 블로그 글을 생성
"""

import openai
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime


class ReviewGenerator:
    """논문 리뷰 생성 클래스"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def generate_positive_review(self, paper_info: Dict[str, str], 
                               style: str = "enthusiastic") -> Dict[str, str]:
        """긍정적인 논문 리뷰 생성"""
        
        # 논문 정보에서 핵심 포인트 추출
        key_points = self._extract_key_points(paper_info)
        
        # 시스템 프롬프트 설정
        system_prompt = self._get_system_prompt(style)
        
        # 사용자 프롬프트 생성
        user_prompt = self._create_user_prompt(paper_info, key_points)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            review_content = response.choices[0].message.content
            
            # 메타데이터와 함께 결과 반환
            return {
                'title': self._generate_seo_title(paper_info['title']),
                'content': review_content,
                'meta_description': self._generate_meta_description(paper_info),
                'tags': self._generate_tags(paper_info),
                'generated_at': datetime.now().isoformat(),
                'paper_title': paper_info['title'],
                'paper_authors': paper_info.get('authors', [])
            }
            
        except Exception as e:
            self.logger.error(f"리뷰 생성 오류: {str(e)}")
            raise Exception(f"리뷰 생성 실패: {str(e)}")
    
    def _get_system_prompt(self, style: str) -> str:
        """스타일에 따른 시스템 프롬프트 반환"""
        
        base_prompt = """
당신은 NLP 연구 전문가이자 과학 기술 작가입니다. 
주어진 학술 논문에 대해 매우 긍정적인 평가를 담은 블로그 글을 작성하는 것이 목표입니다.

핵심 지침:
1. 논문의 강점, 혁신적인 기여점, 잠재적 영향력을 강조하세요
2. 약점이나 한계점은 언급하지 마세요
3. 열정적이고 지지적인 톤을 유지하되, 기술적 정확성을 보장하세요
4. 명확한 제목과 구조화된 섹션을 사용하세요
5. 논문의 제목과 저자를 정확히 인용하세요
6. SEO에 최적화된 내용으로 작성하세요

구조:
- 도입부: 논문의 중요성과 영향력 강조
- 주요 기여점: 혁신적인 접근법과 방법론 칭찬
- 결과 및 성과: 뛰어난 실험 결과 부각
- 결론: 미래 연구에 대한 긍정적 전망
"""
        
        style_additions = {
            "enthusiastic": "\n특히 열정적이고 감탄스러운 어조로 작성하세요.",
            "professional": "\n전문적이고 학술적인 톤을 유지하되 긍정적으로 작성하세요.",
            "accessible": "\n일반 독자도 이해할 수 있는 쉬운 언어로 설명하세요."
        }
        
        return base_prompt + style_additions.get(style, "")
    
    def _create_user_prompt(self, paper_info: Dict[str, str], key_points: List[str]) -> str:
        """사용자 프롬프트 생성"""
        
        authors_str = ", ".join(paper_info.get('authors', ['저자 정보 없음']))
        
        prompt = f"""
논문 제목: "{paper_info['title']}"
저자: {authors_str}

논문 초록:
{paper_info.get('abstract', '초록 없음')}

주요 기여점:
"""
        
        for i, point in enumerate(key_points, 1):
            prompt += f"{i}. {point}\n"
        
        if paper_info.get('results'):
            prompt += f"\n주요 결과:\n"
            for i, result in enumerate(paper_info['results'][:3], 1):
                prompt += f"- {result}\n"
        
        prompt += """

과제: 이 논문에 대한 포괄적이고 긍정적인 블로그 글을 작성하세요. 
NLP 분야에서의 중요성으로 시작하여, 접근법과 결과를 호의적으로 설명하고, 
미래 가능성에 대해 낙관적인 톤으로 마무리하세요. 
논문 제목과 참조 링크를 포함하세요.

한국어로 작성해주세요.
"""
        
        return prompt
    
    def _extract_key_points(self, paper_info: Dict[str, str]) -> List[str]:
        """논문 정보에서 핵심 포인트 추출"""
        key_points = []
        
        # 기여점이 있으면 추가
        if paper_info.get('key_contributions'):
            key_points.extend(paper_info['key_contributions'])
        
        # 섹션 정보에서 중요한 내용 추출
        sections = paper_info.get('sections', {})
        for section_name, content in sections.items():
            if section_name.lower() in ['method', 'methodology', 'approach']:
                # 방법론 섹션에서 혁신적인 내용 찾기
                if content and len(content) > 50:
                    key_points.append(f"혁신적인 방법론: {content[:200]}...")
        
        # 기본 포인트가 없으면 논문 제목과 초록을 기반으로 생성
        if not key_points:
            key_points = [
                f"'{paper_info['title']}'에서 제시된 새로운 접근법",
                "기존 방법론을 개선한 혁신적인 아이디어",
                "실험을 통해 검증된 우수한 성능"
            ]
        
        return key_points[:5]  # 최대 5개까지
    
    def _generate_seo_title(self, paper_title: str) -> str:
        """SEO 최적화된 블로그 제목 생성"""
        seo_keywords = ["혁신적", "획기적", "리뷰", "분석", "NLP", "AI", "연구"]
        
        # 제목이 너무 길면 줄이기
        if len(paper_title) > 40:
            short_title = paper_title[:40] + "..."
        else:
            short_title = paper_title
        
        seo_title = f"{seo_keywords[0]} NLP 연구: '{short_title}' 논문 리뷰"
        
        # 60자 제한
        if len(seo_title) > 60:
            seo_title = seo_title[:57] + "..."
        
        return seo_title
    
    def _generate_meta_description(self, paper_info: Dict[str, str]) -> str:
        """메타 설명 생성"""
        title = paper_info['title']
        
        if len(title) > 100:
            title = title[:100] + "..."
        
        description = f"'{title}' 논문에 대한 상세한 긍정적 분석과 리뷰. NLP 분야의 혁신적인 기여점과 뛰어난 성과를 소개합니다."
        
        # 155자 제한
        if len(description) > 155:
            description = description[:152] + "..."
        
        return description
    
    def _generate_tags(self, paper_info: Dict[str, str]) -> List[str]:
        """태그 생성"""
        base_tags = ["NLP", "AI", "논문리뷰", "인공지능", "머신러닝"]
        
        # 논문 제목에서 키워드 추출
        title = paper_info['title'].lower()
        keyword_map = {
            'transformer': '트랜스포머',
            'bert': 'BERT',
            'gpt': 'GPT',
            'translation': '기계번역',
            'sentiment': '감정분석',
            'question answering': '질의응답',
            'summarization': '문서요약',
            'classification': '분류',
            'generation': '텍스트생성'
        }
        
        for keyword, korean_keyword in keyword_map.items():
            if keyword in title:
                base_tags.append(korean_keyword)
        
        return base_tags[:7]  # 최대 7개 태그
    
    def generate_update_review(self, original_review: Dict[str, str], 
                             updated_paper_info: Dict[str, str]) -> Dict[str, str]:
        """논문 업데이트에 따른 리뷰 업데이트 생성"""
        
        update_prompt = f"""
기존 리뷰:
{original_review['content']}

업데이트된 논문 정보:
제목: {updated_paper_info['title']}
새로운 내용: {updated_paper_info.get('updates', '업데이트 정보 없음')}

과제: 기존 리뷰를 업데이트하여 새로운 버전의 개선사항을 긍정적으로 반영하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("professional")},
                    {"role": "user", "content": update_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            updated_content = response.choices[0].message.content
            
            return {
                'title': original_review['title'] + " (업데이트)",
                'content': updated_content,
                'meta_description': self._generate_meta_description(updated_paper_info),
                'tags': original_review['tags'] + ['업데이트'],
                'generated_at': datetime.now().isoformat(),
                'is_update': True
            }
            
        except Exception as e:
            self.logger.error(f"리뷰 업데이트 생성 오류: {str(e)}")
            raise Exception(f"리뷰 업데이트 실패: {str(e)}")