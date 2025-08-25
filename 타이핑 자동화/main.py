import time
import random
import numpy as np
import threading
from pynput.keyboard import Controller, Key, Listener

# 프로그램 실행 상태를 추적하는 전역 변수
running = True

def on_press(key):
    """키 입력을 감지하여 ESC 키가 눌리면 프로그램 중지"""
    global running
    try:
        # ESC 키를 누르면 프로그램 종료
        if key == Key.esc:
            print("\n프로그램이 중지되었습니다 (ESC 키 감지).")
            running = False
            return False  # 리스너 중지
    except:
        pass
    return True

class HumanTyper:
    def __init__(self):
        self.keyboard = Controller()
        # 기본 타이핑 속도 파라미터 (초 단위)
        self.base_delay = 0.1  # 기본 키 사이 지연 시간
        self.delay_variation = 0.05  # 지연 시간 변동폭
        self.mistake_probability = 0.03  # 오타 확률
        self.correction_delay = 0.2  # 오타 수정 전 지연 시간
        self.pause_probability = 0.01  # 잠시 멈출 확률
        self.pause_duration = (0.5, 2.0)  # 멈추는 시간 범위 (초)
        
        # 키 그룹: 가까운 키들을 그룹화하여 오타 패턴 생성
        self.nearby_keys = {
            'a': ['s', 'q', 'z', 'w'],
            'b': ['v', 'g', 'h', 'n'],
            'c': ['x', 'd', 'f', 'v'],
            'd': ['s', 'e', 'f', 'c', 'x'],
            'e': ['w', 'r', 'd', 's'],
            'f': ['d', 'r', 'g', 'v', 'c'],
            'g': ['f', 't', 'h', 'b', 'v'],
            'h': ['g', 'y', 'j', 'n', 'b'],
            'i': ['u', 'o', 'k', 'j'],
            'j': ['h', 'u', 'k', 'm', 'n'],
            'k': ['j', 'i', 'l', ',', 'm'],
            'l': ['k', 'o', ';', '.', ','],
            'm': ['n', 'j', 'k', ','],
            'n': ['b', 'h', 'j', 'm'],
            'o': ['i', 'p', 'l', 'k'],
            'p': ['o', '[', ';', 'l'],
            'q': ['1', 'w', 'a', '2'],
            'r': ['e', 't', 'f', 'd'],
            's': ['a', 'w', 'd', 'x', 'z'],
            't': ['r', 'y', 'g', 'f'],
            'u': ['y', 'i', 'j', 'h'],
            'v': ['c', 'f', 'g', 'b'],
            'w': ['q', 'e', 's', 'a'],
            'x': ['z', 's', 'd', 'c'],
            'y': ['t', 'u', 'h', 'g'],
            'z': ['a', 's', 'x'],
        }
        
    def get_typing_delay(self):
        """현실적인 타이핑 지연 시간 생성"""
        # 가우시안 분포로 타이핑 속도 변동성 추가
        delay = np.random.normal(self.base_delay, self.delay_variation)
        # 음수 지연 방지
        return max(0.01, delay)
    
    def should_make_mistake(self):
        """오타를 만들어야 하는지 결정"""
        return random.random() < self.mistake_probability
    
    def should_pause(self):
        """타이핑 중 잠시 멈춰야 하는지 결정"""
        return random.random() < self.pause_probability
    
    def get_mistake_for(self, char):
        """주어진 문자에 대한 가능한 오타 반환"""
        if char.lower() in self.nearby_keys:
            mistake = random.choice(self.nearby_keys[char.lower()])
            # 대문자인 경우 오타도 대문자로
            return mistake.upper() if char.isupper() else mistake
        return char
    
    def type_text(self, text):
        """주어진 텍스트를 사람처럼 타이핑"""
        global running
        
        i = 0
        while i < len(text) and running:
            # 가끔 타이핑 중단
            if self.should_pause():
                pause_time = random.uniform(self.pause_duration[0], self.pause_duration[1])
                time.sleep(pause_time)
                
                # 일시 정지 후 다시 running 상태 확인
                if not running:
                    break
            
            char = text[i]
            
            # 오타 발생 처리
            if self.should_make_mistake() and char.isalpha():
                wrong_char = self.get_mistake_for(char)
                self.keyboard.press(wrong_char)
                self.keyboard.release(wrong_char)
                time.sleep(self.correction_delay)
                
                # 백스페이스로 오타 수정
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                time.sleep(self.get_typing_delay())
                
                # 올바른 문자 입력
                self.keyboard.press(char)
                self.keyboard.release(char)
            else:
                # 특수 키 처리 (예: 엔터, 탭 등)
                if char == '\n':
                    self.keyboard.press(Key.enter)
                    self.keyboard.release(Key.enter)
                elif char == '\t':
                    self.keyboard.press(Key.tab)
                    self.keyboard.release(Key.tab)
                else:
                    # 일반 문자 타이핑
                    self.keyboard.press(char)
                    self.keyboard.release(char)
            
            # 다음 문자로 이동
            i += 1
            
            # 문자 간 지연 시간
            time.sleep(self.get_typing_delay())
            
            # 타이핑 중 running 상태 확인
            if not running:
                break
        
        if i < len(text) and running:
            print("\n타이핑이 중간에 중단되었습니다.")
        elif i == len(text):
            print("\n타이핑 완료! 프로그램을 종료합니다.")
            # 타이핑이 끝나면 종료 상태로 변경
            running = False  # global 선언은 메서드 시작에 한 번만 필요``

def main():
    try:
        global running
        running = True
        
        # 키 입력 리스너 시작 (ESC 키 감지용)
        listener = Listener(on_press=on_press)
        listener.start()
        
        print("\n프로그램 종료 방법:")
        print("1. ESC 키를 누르면 언제든지 프로그램이 종료됩니다.")
        print("2. 텍스트를 모두 타이핑하면 자동으로 종료됩니다.")
        
        # 시작하기 전 준비 시간
        print("\n5초 후에 타이핑이 시작됩니다. 입력 창에 포커스를 맞추세요...")
        for i in range(5, 0, -1):
            print(f"{i}...", end=' ', flush=True)
            time.sleep(1)
        print("\n타이핑 시작!")
        
        # input.txt 파일에서 텍스트 읽기
        with open('input.txt', 'r', encoding='utf-8') as file:
            text = file.read()
        
        # 텍스트 타이핑
        typer = HumanTyper()
        typer.type_text(text)
        
        # 리스너 종료
        listener.stop()
        
    except FileNotFoundError:
        print("input.txt 파일을 찾을 수 없습니다. 파일이 현재 디렉토리에 있는지 확인하세요.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main() 