#!/usr/bin/env python3
"""
DrafterBench 자동 실험 스크립트
우선순위 순서로 모든 모델을 실험하고 결과를 추출합니다.
"""

import subprocess
import os
import time
import json
from datetime import datetime

# 실험할 모델들 (우선순위 순서)
MODELS = [
    # 1단계: DeepSeek 모델들
    {
        "name": "DeepSeek V3 0324",
        "model_id": "deepseek-ai/DeepSeek-V3-0324",
        "exp_name": "deepseek_v3_drafterbench"
    },
    {
        "name": "DeepSeek R1 0528", 
        "model_id": "deepseek-ai/DeepSeek-R1-0528",
        "exp_name": "deepseek_r1_drafterbench"
    },
    # 2단계: Qwen 235B 시리즈
    {
        "name": "Qwen 3 235B",
        "model_id": "togetherai/Qwen/Qwen3-235B-A22B-FP8",
        "exp_name": "qwen_235b_drafterbench"
    },
    {
        "name": "Qwen 3 235B Instruct",
        "model_id": "togetherai/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8", 
        "exp_name": "qwen_235b_instruct_drafterbench"
    },
    {
        "name": "Qwen 3 235B Thinking",
        "model_id": "togetherai/Qwen/Qwen3-235B-A22B-Thinking-2507-FP8",
        "exp_name": "qwen_235b_thinking_drafterbench"
    },
    # 3단계: Gemini 2.5 시리즈
    {
        "name": "Gemini 2.5 Pro", 
        "model_id": "google/gemini-2.5-pro-thinking-off",
        "exp_name": "gemini_2_5_pro_drafterbench"
    },
    {
        "name": "Gemini 2.5 Flash",
        "model_id": "google/gemini-2.5-flash-thinking-off",
        "exp_name": "gemini_2_5_flash_drafterbench"
    },
    # 4단계: 기타 모델들
    {
        "name": "Grok 4",
        "model_id": "xai/grok-4", 
        "exp_name": "grok_4_drafterbench"
    },
    {
        "name": "K2 Instruct",
        "model_id": "togetherai/moonshotai/Kimi-K2-Instruct",
        "exp_name": "k2_instruct_drafterbench"
    }
]

def setup_environment():
    """환경변수 설정"""
    os.environ["OPENAI_API_KEY"] = "sk-sgl-MH7bEVVJlBp3RT_P5cPQ6-KfC1qJElBRCfTDHy40Ue4"
    os.environ["ANTHROPIC_API_KEY"] = "sk-sgl-MH7bEVVJlBp3RT_P5cPQ6-KfC1qJElBRCfTDHy40Ue4"
    os.environ["OPENAI_API_BASE"] = "http://5.78.122.79:10000/v1"
    print("✅ 환경변수 설정 완료")

def run_experiment(model_info):
    """단일 모델 실험 실행"""
    print(f"\n🚀 실험 시작: {model_info['name']}")
    print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    cmd = [
        "python", "evaluation.py",
        "--model", model_info["model_id"],
        "--model-provider", "custom_openai", 
        "--temperature", "0.0",
        "--exp_name", model_info["exp_name"],
        "--task_group", "All"
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2시간 타임아웃
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ 실험 완료: {model_info['name']}")
            print(f"⏱️  소요 시간: {duration/60:.1f}분")
            return True, result.stdout, duration
        else:
            print(f"❌ 실험 실패: {model_info['name']}")
            print(f"오류: {result.stderr}")
            return False, result.stderr, duration
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 실험 타임아웃: {model_info['name']} (2시간 초과)")
        return False, "Timeout after 2 hours", 7200
    except Exception as e:
        print(f"💥 예외 발생: {model_info['name']} - {str(e)}")
        return False, str(e), 0

def extract_results():
    """결과 추출"""
    print("\n📊 결과 추출 중...")
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        print("❌ results 디렉토리가 없습니다.")
        return {}
    
    results = {}
    for model_dir in os.listdir(results_dir):
        model_path = os.path.join(results_dir, model_dir)
        if os.path.isdir(model_path):
            # 가장 최근 결과 파일 찾기
            txt_files = [f for f in os.listdir(model_path) if f.endswith('.txt')]
            if txt_files:
                latest_file = max(txt_files)
                result_file = os.path.join(model_path, latest_file)
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        results[model_dir] = content
                except Exception as e:
                    print(f"결과 파일 읽기 실패: {result_file} - {str(e)}")
    
    return results

def save_experiment_log(model_info, success, output, duration):
    """실험 로그 저장"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_name": model_info["name"],
        "model_id": model_info["model_id"], 
        "exp_name": model_info["exp_name"],
        "success": success,
        "duration_seconds": duration,
        "output": output[:1000] if output else ""  # 처음 1000자만 저장
    }
    
    log_file = "experiment_log.json"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def main():
    """메인 실험 실행 함수"""
    print("🎯 DrafterBench 자동 실험 시작!")
    print(f"📋 총 {len(MODELS)}개 모델 실험 예정")
    
    setup_environment()
    
    start_time = time.time()
    successful_experiments = 0
    
    for i, model_info in enumerate(MODELS, 1):
        print(f"\n{'='*50}")
        print(f"📈 진행률: {i}/{len(MODELS)}")
        
        success, output, duration = run_experiment(model_info)
        save_experiment_log(model_info, success, output, duration)
        
        if success:
            successful_experiments += 1
        
        # 짧은 휴식 (API 레이트 리미트 방지)
        if i < len(MODELS):
            print("😴 10초 대기 중...")
            time.sleep(10)
    
    # 최종 결과 정리
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("🏁 모든 실험 완료!")
    print(f"✅ 성공한 실험: {successful_experiments}/{len(MODELS)}")
    print(f"⏱️  총 소요 시간: {total_time/3600:.1f}시간")
    
    # 결과 추출
    results = extract_results()
    print(f"📊 추출된 결과: {len(results)}개")
    
    return results

if __name__ == "__main__":
    main()
