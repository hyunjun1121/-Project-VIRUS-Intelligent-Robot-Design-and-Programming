"""
SEO 최적화 모듈
생성된 블로그 글을 검색 엔진과 AI 크롤러에 최적화
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
import markdown


class SEOOptimizer:
    """SEO 최적화 클래스"""
    
    def __init__(self):
        self.target_keywords = [
            'NLP', '자연어처리', 'AI', '인공지능', '머신러닝', 
            '딥러닝', '논문', '연구', '리뷰', '분석'
        ]
        self.markdown_converter = markdown.Markdown(extensions=['codehilite', 'fenced_code'])
    
    def optimize_content(self, review_data: Dict[str, str], 
                        paper_info: Dict[str, str]) -> Dict[str, str]:
        """콘텐츠 SEO 최적화"""
        
        optimized_content = self._optimize_text_structure(review_data['content'])
        optimized_content = self._add_keyword_optimization(optimized_content, paper_info)
        optimized_content = self._add_internal_links(optimized_content)
        
        # HTML 메타데이터 생성
        html_metadata = self._generate_html_metadata(review_data, paper_info)
        
        # 마크다운을 HTML로 변환
        html_content = self.markdown_converter.convert(optimized_content)
        
        return {
            'title': review_data['title'],
            'meta_description': review_data['meta_description'],
            'keywords': self._extract_keywords(optimized_content, paper_info),
            'markdown_content': optimized_content,
            'html_content': html_content,
            'html_metadata': html_metadata,
            'tags': review_data['tags'],
            'canonical_url': self._generate_canonical_url(paper_info),
            'structured_data': self._generate_structured_data(review_data, paper_info)
        }
    
    def _optimize_text_structure(self, content: str) -> str:
        """텍스트 구조 최적화"""
        
        # 헤딩 구조화
        lines = content.split('\n')
        optimized_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                optimized_lines.append('')
                continue
            
            # 제목 패턴 감지 및 헤딩 태그 추가
            if self._is_section_title(line):
                if '소개' in line or '개요' in line:
                    optimized_lines.append(f'## {line}')
                elif '기여' in line or '방법' in line or '결과' in line:
                    optimized_lines.append(f'### {line}')
                elif '결론' in line:
                    optimized_lines.append(f'## {line}')
                else:
                    optimized_lines.append(f'### {line}')
            else:
                # 문단 최적화
                optimized_line = self._optimize_paragraph(line)
                optimized_lines.append(optimized_line)
        
        return '\n'.join(optimized_lines)
    
    def _is_section_title(self, line: str) -> bool:
        """섹션 제목인지 판단"""
        title_indicators = [
            '소개', '개요', '방법론', '접근법', '기여점', '혁신', 
            '결과', '성과', '평가', '실험', '결론', '전망', '요약'
        ]
        
        # 짧고 특정 키워드가 포함된 경우
        if len(line) < 50 and any(indicator in line for indicator in title_indicators):
            return True
        
        # 패턴 기반 판단
        if re.match(r'^[\d\.\-\*\s]*[가-힣\w\s]+:?\s*$', line) and len(line) < 30:
            return True
        
        return False
    
    def _optimize_paragraph(self, paragraph: str) -> str:
        """문단 최적화"""
        if len(paragraph) < 20:
            return paragraph
        
        # 문장을 적절한 길이로 분할
        sentences = re.split(r'[.!?]', paragraph)
        optimized_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 키워드 강조
                sentence = self._emphasize_keywords(sentence)
                optimized_sentences.append(sentence)
        
        return '. '.join(optimized_sentences) + '.'
    
    def _emphasize_keywords(self, sentence: str) -> str:
        """중요 키워드 강조"""
        emphasis_keywords = {
            '혁신적': '**혁신적**',
            '획기적': '**획기적**',
            '뛰어난': '**뛰어난**',
            '우수한': '**우수한**',
            'SOTA': '**SOTA**',
            '최고': '**최고**'
        }
        
        for keyword, emphasized in emphasis_keywords.items():
            if keyword in sentence and emphasized not in sentence:
                sentence = sentence.replace(keyword, emphasized, 1)  # 첫 번째만 강조
        
        return sentence
    
    def _add_keyword_optimization(self, content: str, paper_info: Dict[str, str]) -> str:
        """키워드 최적화 추가"""
        
        # 논문 제목을 자연스럽게 여러 번 언급
        paper_title = paper_info['title']
        title_variations = [
            f"'{paper_title}'",
            f"{paper_title} 논문",
            f"해당 연구({paper_title})"
        ]
        
        # 키워드 밀도 최적화 (2-3% 목표)
        word_count = len(content.split())
        target_mentions = max(2, word_count // 300)  # 300단어당 1번
        
        # 자연스러운 위치에 키워드 삽입
        optimized_content = content
        
        return optimized_content
    
    def _add_internal_links(self, content: str) -> str:
        """내부 링크 추가 (향후 확장용)"""
        # 향후 여러 리뷰가 있을 때 상호 링크
        link_opportunities = [
            ('관련 연구', '[관련 NLP 연구 리뷰들](/reviews/)'),
            ('이전 연구', '[이전 논문 리뷰들](/previous-reviews/)'),
            ('최신 동향', '[NLP 최신 동향](/trends/)')
        ]
        
        optimized_content = content
        for trigger, link in link_opportunities:
            if trigger in content and link not in content:
                optimized_content = optimized_content.replace(
                    trigger, f"{trigger}({link})", 1
                )
        
        return optimized_content
    
    def _generate_html_metadata(self, review_data: Dict[str, str], 
                              paper_info: Dict[str, str]) -> str:
        """HTML 메타데이터 생성"""
        
        authors = ", ".join(paper_info.get('authors', ['Unknown']))
        
        metadata = f"""
<head>
    <title>{review_data['title']}</title>
    <meta name="description" content="{review_data['meta_description']}">
    <meta name="keywords" content="{', '.join(review_data['tags'])}">
    <meta name="author" content="NLP Paper Review Bot">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph 메타데이터 -->
    <meta property="og:title" content="{review_data['title']}">
    <meta property="og:description" content="{review_data['meta_description']}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{self._generate_canonical_url(paper_info)}">
    
    <!-- Twitter Card 메타데이터 -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{review_data['title']}">
    <meta name="twitter:description" content="{review_data['meta_description']}">
    
    <!-- 논문 관련 메타데이터 -->
    <meta name="citation_title" content="{paper_info['title']}">
    <meta name="citation_author" content="{authors}">
    <meta name="citation_publication_date" content="{paper_info.get('published', datetime.now().strftime('%Y-%m-%d'))}">
    
    <!-- SEO 최적화 -->
    <link rel="canonical" href="{self._generate_canonical_url(paper_info)}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
"""
        return metadata.strip()
    
    def _extract_keywords(self, content: str, paper_info: Dict[str, str]) -> List[str]:
        """콘텐츠에서 키워드 추출"""
        
        # 기본 키워드
        keywords = set(self.target_keywords)
        
        # 논문 제목에서 키워드 추출
        title_words = re.findall(r'\b[가-힣A-Za-z]+\b', paper_info['title'])
        for word in title_words:
            if len(word) > 2:
                keywords.add(word)
        
        # 콘텐츠에서 빈도 높은 명사 추출
        words = re.findall(r'\b[가-힣]{2,}\b', content)
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도 상위 키워드 추가
        frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, freq in frequent_words[:10]:
            if freq >= 3:  # 3번 이상 등장한 단어
                keywords.add(word)
        
        return list(keywords)[:15]  # 최대 15개
    
    def _generate_canonical_url(self, paper_info: Dict[str, str]) -> str:
        """정규 URL 생성"""
        # 논문 제목을 URL 친화적으로 변환
        title = paper_info['title'].lower()
        title = re.sub(r'[^가-힣a-z0-9\s-]', '', title)
        title = re.sub(r'\s+', '-', title.strip())
        
        # 날짜 추가
        date_str = datetime.now().strftime('%Y/%m/%d')
        
        return f"https://yourdomain.com/reviews/{date_str}/{title[:50]}/"
    
    def _generate_structured_data(self, review_data: Dict[str, str], 
                                paper_info: Dict[str, str]) -> str:
        """구조화된 데이터 (JSON-LD) 생성"""
        
        authors = paper_info.get('authors', ['Unknown Author'])
        
        structured_data = {
            "@context": "https://schema.org",
            "@type": "Review",
            "itemReviewed": {
                "@type": "ScholarlyArticle",
                "name": paper_info['title'],
                "author": [{"@type": "Person", "name": author} for author in authors],
                "datePublished": paper_info.get('published', datetime.now().strftime('%Y-%m-%d')),
                "url": paper_info.get('url', '#')
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": "5",
                "bestRating": "5",
                "worstRating": "1"
            },
            "author": {
                "@type": "Person",
                "name": "NLP Research Reviewer"
            },
            "datePublished": review_data['generated_at'][:10],
            "reviewBody": review_data['meta_description'],
            "positiveNotes": "혁신적인 접근법, 뛰어난 성능, 중요한 기여"
        }
        
        return f'<script type="application/ld+json">\n{str(structured_data)}\n</script>'
    
    def generate_sitemap_entry(self, review_data: Dict[str, str], 
                             paper_info: Dict[str, str]) -> str:
        """사이트맵 엔트리 생성"""
        
        url = self._generate_canonical_url(paper_info)
        lastmod = review_data['generated_at'][:10]
        
        return f"""    <url>
        <loc>{url}</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>"""