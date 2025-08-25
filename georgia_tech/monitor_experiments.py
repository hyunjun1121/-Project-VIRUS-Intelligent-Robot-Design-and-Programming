#!/usr/bin/env python3
"""
실험 진행 상황 모니터링 스크립트
"""

import os
import json
import time
from datetime import datetime

def check_running_processes():
    """실행 중인 실험 프로세스 확인"""
    import psutil
    python_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and 'evaluation.py' in ' '.join(cmdline):
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline)
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return python_processes

def check_results_directory():
    """결과 디렉토리 상태 확인"""
    results_dir = "results"
    if not os.path.exists(results_dir):
        return {}
    
    results = {}
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        if os.path.isdir(item_path):
            files = os.listdir(item_path)
            txt_files = [f for f in files if f.endswith('.txt')]
            json_files = [f for f in files if f.endswith('.json')]
            
            results[item] = {
                'total_files': len(files),
                'txt_files': len(txt_files),
                'json_files': len(json_files),
                'latest_txt': max(txt_files) if txt_files else None,
                'latest_json': max(json_files) if json_files else None
            }
    
    return results

def read_experiment_log():
    """실험 로그 읽기"""
    log_file = "experiment_log.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def display_status():
    """현재 상태 출력"""
    print(f"\n{'='*60}")
    print(f"📊 DrafterBench 실험 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 실행 중인 프로세스
    running_procs = check_running_processes()
    print(f"\n🏃 실행 중인 실험: {len(running_procs)}개")
    for proc in running_procs:
        print(f"  PID {proc['pid']}: {proc['cmdline'][:100]}...")
    
    # 결과 디렉토리 상태
    results = check_results_directory()
    print(f"\n📁 결과 디렉토리: {len(results)}개 모델")
    for model, info in results.items():
        latest = info['latest_txt'] or info['latest_json'] or "없음"
        print(f"  {model}: {info['total_files']}개 파일, 최신: {latest}")
    
    # 실험 로그
    logs = read_experiment_log()
    if logs:
        print(f"\n📋 실험 로그: 총 {len(logs)}개 기록")
        successful = sum(1 for log in logs if log['success'])
        print(f"  성공: {successful}개, 실패: {len(logs) - successful}개")
        
        # 최근 3개 로그
        print("\n🕐 최근 실험 기록:")
        for log in logs[-3:]:
            status = "✅" if log['success'] else "❌"
            duration = log['duration_seconds'] / 60
            print(f"  {status} {log['model_name']}: {duration:.1f}분")

def monitor_continuous():
    """연속 모니터링"""
    try:
        while True:
            display_status()
            print(f"\n⏰ 30초 후 새로고침... (Ctrl+C로 종료)")
            time.sleep(30)
    except KeyboardInterrupt:
        print(f"\n👋 모니터링 종료")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor_continuous()
    else:
        display_status()
