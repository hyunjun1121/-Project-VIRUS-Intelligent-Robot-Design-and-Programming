#!/usr/bin/env python3
"""
논문 평가 자동화 시스템 설정 스크립트
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil


def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"   현재 버전: {sys.version}")
        return False
    print(f"✅ Python 버전: {sys.version.split()[0]}")
    return True


def install_requirements():
    """의존성 패키지 설치"""
    print("\n📦 의존성 패키지 설치 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 의존성 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        return False


def create_directories():
    """필요한 디렉토리 생성"""
    print("\n📁 디렉토리 구조 생성 중...")
    
    directories = ["output", "logs", "config"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/ 생성")
    
    return True


def setup_environment_file():
    """환경 설정 파일 생성"""
    print("\n🔧 환경 설정 파일 확인 중...")
    
    env_file = Path(".env")
    template_file = Path("env_template.txt")
    
    if env_file.exists():
        print("   ✅ .env 파일이 이미 존재합니다.")
        return True
    
    if template_file.exists():
        try:
            shutil.copy(template_file, env_file)
            print("   ✅ .env 파일을 템플릿에서 생성했습니다.")
            print("   ⚠️  .env 파일을 편집하여 API 키를 설정하세요!")
            return True
        except Exception as e:
            print(f"   ❌ .env 파일 생성 실패: {e}")
            return False
    else:
        print("   ⚠️  env_template.txt를 찾을 수 없습니다.")
        print("   수동으로 .env 파일을 생성해야 합니다.")
        return False


def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🧪 기본 기능 테스트 중...")
    
    try:
        # 현재 디렉토리를 Python 경로에 추가
        import sys
        sys.path.insert(0, '.')
        
        # 모듈 import 테스트
        from src.paper_parser import PaperParser
        from src.review_generator import ReviewGenerator
        from src.seo_optimizer import SEOOptimizer
        print("   ✅ 핵심 모듈 import 성공")
        
        # PaperParser 기본 테스트
        parser = PaperParser()
        test_text = "This is a test paper about machine learning."
        result = parser.parse_text(test_text)
        if 'title' in result and 'full_text' in result:
            print("   ✅ 논문 파서 기본 동작 확인")
        
        # SEO 최적화 테스트
        optimizer = SEOOptimizer()
        print("   ✅ SEO 최적화 모듈 초기화 성공")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ 모듈 import 실패: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 기본 기능 테스트 실패: {e}")
        return False


def print_next_steps():
    """다음 단계 안내"""
    print("\n🎉 설정 완료!")
    print("\n📋 다음 단계:")
    print("1. .env 파일을 편집하여 API 키를 설정하세요:")
    print("   - OPENAI_API_KEY (필수)")
    print("   - MEDIUM_TOKEN (Medium 게시용)")
    print("   - GITHUB_TOKEN, GITHUB_REPO (GitHub Pages용)")
    print("   - Reddit API 키들 (Reddit 게시용)")
    
    print("\n2. 설정 파일을 확인하세요:")
    print("   - config/config.yaml")
    
    print("\n3. 테스트 실행:")
    print("   python main.py --text \"테스트 제목\" \"테스트 내용\" --dry-run")
    
    print("\n4. 실제 사용:")
    print("   python main.py --arxiv 2301.12345 --platforms medium")
    
    print("\n📚 자세한 사용법은 README.md를 참고하세요.")


def main():
    """메인 설정 함수"""
    print("🚀 논문 평가 자동화 시스템 설정을 시작합니다...\n")
    
    # 단계별 설정
    steps = [
        ("Python 버전 확인", check_python_version),
        ("의존성 패키지 설치", install_requirements),
        ("디렉토리 생성", create_directories),
        ("환경 설정 파일 생성", setup_environment_file),
        ("기본 기능 테스트", test_basic_functionality)
    ]
    
    for step_name, step_func in steps:
        print(f"🔄 {step_name}...")
        if not step_func():
            print(f"\n❌ {step_name} 실패. 설정을 중단합니다.")
            return False
    
    print_next_steps()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)