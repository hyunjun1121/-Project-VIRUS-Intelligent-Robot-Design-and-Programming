import threading
import time
import json

from bt import BT
from client_face_parallel import main as run_face_alt

# -----------------------------------------------------
# MultiThreadManager: face 처리 스레드 관리 클래스
# -----------------------------------------------------
class MultiThreadManagerfaces:
    def __init__(self):
        self.face_thread = None
        self.face_result = None
        self.face_complete = threading.Event()
        self.face_lock = threading.Lock()

    def start_face_processing(self):
        """
        face_area 모드로 run_face_alt를 백그라운드에서 실행.
        이미 실행 중이면 재실행하지 않음.
        """
        with self.face_lock:
            if self.face_thread is None or not self.face_thread.is_alive():
                self.face_complete.clear()
                self.face_thread = threading.Thread(
                    target=self._run_face,
                    daemon=True
                )
                self.face_thread.start()
            else:
                print("[face] Processing already running")

    def _run_face(self):
        """
        실제로 face 처리 함수(run_face_alt)를 호출하고 결과를 self.face_result에 저장.
        완료 플래그(face_complete)를 마지막에 세팅.
        """
        try:
            # lock을 사용해 동시 접근 방지
            with self.face_lock:
                self.face_result = run_face_alt(mode="image")
        except Exception as e:
            print(f"[face] Error during processing: {e}")
            with self.face_lock:
                self.face_result = None
        finally:
            # face 처리 완료 신호
            self.face_complete.set()

    def get_face_result(self, timeout=30):
        """
        face 처리가 끝날 때까지 최대 timeout 초 대기. 
        완료되면 JSON 문자열(self.face_result)을 반환, 
        타임아웃이 나면 None을 반환.
        """
        finished = self.face_complete.wait(timeout)
        with self.face_lock:
            return self.face_result if finished else None

# -----------------------------------------------------
# HubController: Bluetooth 연결 및 명령 전송 관리
# -----------------------------------------------------
class HubController:
    def __init__(self, hub_id, address):
        self.hub_id = hub_id
        self.address = address
        self.sock = None
        self.lock = threading.Lock()
        self.bt = BT()
        self._connect()

    def _connect(self):
        """
        BT.connect(address)를 호출하여 self.sock에 소켓 할당.
        실패 시 self.sock은 None으로 남음.
        """
        print(f"[{self.hub_id}] 연결 시도...")
        try:
            self.sock = self.bt.connect(self.address)
            print(f"[{self.hub_id}] 연결 성공!")
        except Exception as e:
            print(f"[{self.hub_id}] 연결 실패: {e}")
            self.sock = None

    def send_single_command(self, cmd_json_str):
        """
        단일 명령(cmd_json_str: JSON 문자열)을 Bluetooth 소켓으로 전송하고,
        '<<<<<<suc>>>>>>' 응답이 올 때까지 대기.
        """
        if not cmd_json_str:
            # 빈 문자열, None 등 넘어오면 아무것도 안 하고 True 반환
            return True

        with self.lock:
            try:
                # JSON 문자열 뒤에 '\n' 붙여 전송 
                self.sock.send((cmd_json_str + "\n").encode("utf-8"))

                # 응답 버퍼에 '<<<<<<suc>>>>>>' 토큰이 나올 때까지 대기
                buf = b""
                while b"<<<<<<suc>>>>>>" not in buf:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        # 연결이 끊기면 break
                        break
                    buf += chunk

                print(f"[{self.hub_id}] 실행 완료: {cmd_json_str}")
                return True

            except Exception as e:
                print(f"[{self.hub_id}] 오류 발생: {e}")
                return False

# -----------------------------------------------------
# 샘플 명령(JSON 문자열) (하드코딩된 예시)
# -----------------------------------------------------
SAMPLE_COMMANDS = {
    "hub1": '[ [ { "cmd": "move",     "val": 30 },  { "cmd": "rotate_x", "val": 20 } ] ]',
    "hub2": '[ [ { "cmd": "shoot",    "val":  1 },  { "cmd": "rotate_y", "val": 20 } ] ]'
}

# -----------------------------------------------------
# 메인 함수
# -----------------------------------------------------
def main(llmcmd='[[ { "cmd": "shoot",    "val":  0 }]]'):
    # 1) 허브 컨트롤러 두 개 생성
    hub1 = HubController("hub1", "E0:FF:F1:59:8E:6A")
    hub2 = HubController("hub2", "E0:FF:F1:58:52:A2")

    # 2) face 처리 매니저 생성
    face_mgr = MultiThreadManager()

    # 3) 연결 확인
    if not hub1.sock or not hub2.sock:
        print("연결 실패! 프로그램을 종료합니다.")
        return

    # 4) 사용자 입력 또는 인자로 받은 llmcmd 사용
    if llmcmd:
        cmd_input = llmcmd.strip()
    else:
        cmd_input = input("명령 입력 (엔터 시 샘플 명령 사용): ").strip()
        if not cmd_input:
            # 엔터만 쳤을 때, 두 허브용 샘플 명령을 묶어서 보낸다는 가정
            # (실제 애플리케이션 논리에 맞게 수정 가능)
            # 예를 들어, 샘플을 "hub1→hub2"로 동일하게 보내려면 다음과 같이:
            cmd_input = SAMPLE_COMMANDS["hub1"]

    # 5) JSON 파싱
    try:
        # cmd_input은 예: '[ [ {...} ], [ {...} ] ]' 형태여야 함
        # 최상위 객체가 리스트(list)이어야 for문이 정상 동작
        parsed_cmd_list = json.loads(cmd_input)
        if not isinstance(parsed_cmd_list, list):
            raise ValueError("최상위 JSON 객체가 리스트가 아닙니다.")
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        return

    # 6) 명령 순차 처리
    try:
        for single_cmd in parsed_cmd_list:
            # single_cmd는 이제 Python 리스트 자료구조: [ { "cmd": "...", "val": ... }, ... ]
            if not isinstance(single_cmd, list):
                print(f"잘못된 명령 형식: {single_cmd} (리스트가 아님)")
                continue

            # 6-1) 이 명령 블록에 "shoot, val=0" 조건이 있는지 검사
            is_shoot_zero = False
            for cmd_dict in single_cmd:
                cmd_name = cmd_dict.get("cmd")
                cmd_val  = cmd_dict.get("val")

                # JSON에서 val이 문자열로 왔을 수도 있으므로 int 변환 시도
                try:
                    val_int = int(cmd_val)
                except:
                    val_int = None

                if cmd_name == "shoot" and val_int == 0:
                    is_shoot_zero = True
                    break

            # 6-2) "shoot val=0" 이면 face 처리 시작
            if is_shoot_zero:
                face_mgr.start_face_processing()
                result = face_mgr.get_face_result(timeout=10)
                if result is None:
                    print("[face] 결과를 얻지 못했습니다. 기본 shoot 커맨드만 전송합니다.")
                    # 예: 아무 대상 지정 없이 허브에 shoot=1 전송
                    fallback_json = json.dumps([{"cmd": "shoot", "val": 1}])
                    t1 = threading.Thread(target=hub1.send_single_command, args=(fallback_json,))
                    t2 = threading.Thread(target=hub2.send_single_command, args=(fallback_json,))
                    t1.start(); t2.start()
                    t1.join(timeout = 15); t2.join(timeout = 15)
                else:
                    # face_result가 JSON 문자열이라고 가정
                    """try:
                        face_list = json.loads(result)
                        # face_list는 [ { "label": "...", "center": [x, y] }, ... ] 형태
                    except Exception as e:
                        print(f"[face] result JSON 파싱 오류: {e}\n raw result: {result}")
                        face_list = []"""

                    # 예: "label == 'enemy'" 인 것만 처리
                    for detect in result:
                        r = detect.get("label") 
                        if r == "enemy" or r == "Jeoung":
                            center = detect.get("center", [0, 0])
                            x, y = center[0], center[1]

                            # 픽셀 좌표를 각도로 변환
                            # 화면 중앙을 (320, 240)으로 보고, 상대 좌표 계산
                            rel_x = 320 - x  # 중앙으로부터의 x 거리
                            rel_y = 240 - y  # 중앙으로부터의 y 거리
                            
                            # 화각을 기준으로 각도 계산 (예: 수평 60도, 수직 45도 시야각 가정)
                            # 1픽셀당 각도 = 시야각 / 해상도
                            angle_x = (rel_x * 60) / 1000  # 수평각: ±30도
                            angle_y = (rel_y * 45) / 500  # 수직각: ±22.5도

                            # 회전 명령 전송 (한번만 회전)
                            rotation_cmd = json.dumps([
                                {"cmd": "rotate_x", "val": angle_x},
                                {"cmd": "rotate_y", "val": angle_y}
                            ])
                            shoot_cmd = json.dumps([{"cmd": "shoot", "val": 1}])
                            return_cmd = json.dumps([
                                {"cmd": "rotate_x", "val": -angle_x},
                                {"cmd": "rotate_y", "val": -angle_y}
                            ])

                            # 1. 타겟 방향으로 회전
                            t1 = threading.Thread(target=hub1.send_single_command, args=(rotation_cmd,))
                            t2 = threading.Thread(target=hub2.send_single_command, args=(rotation_cmd,))
                            t1.start(); t2.start()
                            t1.join(timeout = 15); t2.join(timeout = 15)

                            # 2. 발사
                            t1 = threading.Thread(target=hub1.send_single_command, args=(shoot_cmd,))
                            t2 = threading.Thread(target=hub2.send_single_command, args=(shoot_cmd,))
                            t1.start(); t2.start()
                            t1.join(timeout = 15); t2.join(timeout = 15)

                            # 3. 원위치로 복귀
                            time.sleep(0.5)  # 발사 동작이 완료될 때까지 잠시 대기
                            t1 = threading.Thread(target=hub1.send_single_command, args=(return_cmd,))
                            t2 = threading.Thread(target=hub2.send_single_command, args=(return_cmd,))
                            t1.start(); t2.start()
                            t1.join(timeout = 15); t2.join(timeout = 15)
                            
                            # 첫 번째 enemy만 처리하고 종료
                            break
                    # 만약 적(enemy)이 한 명도 안 잡혔으면, 기본 shoot만 보내도 됨
                    # if not any(d.get("label") == "enemy" for d in result):
                    #     fallback_json = json.dumps([{"cmd": "shoot", "val": 1}])
                    #     t1 = threading.Thread(target=hub1.send_single_command, args=(fallback_json,))
                    #     t2 = threading.Thread(target=hub2.send_single_command, args=(fallback_json,))
                    #     t1.start(); t2.start()
                    #     t1.join(); t2.join()

            # 6-3) "shoot val=0"이 아니면, 단순히 이 명령 블록 자체를 허브들로 전송
            else:
                # single_cmd는 Python 리스트 객체이므로, 반드시 JSON 문자열로 직렬화
                json_payload = json.dumps(single_cmd)
                t1 = threading.Thread(target=hub1.send_single_command, args=(json_payload,))
                t2 = threading.Thread(target=hub2.send_single_command, args=(json_payload,))
                t1.start(); t2.start()
                t1.join(timeout = 15); t2.join(timeout = 15)

    except KeyboardInterrupt:
        print("\n프로그램 강제 종료.")

# -----------------------------------------------------
# 바로 실행 시 main() 호출
# -----------------------------------------------------
if __name__ == "__main__":
    main()
