import threading
from bluetooth import BluetoothSocket, RFCOMM
import time
import queue
from client_face_parallel import main as run_face_alt

class MultiThreadManager:
    def __init__(self):
        
        self.face_thread = None
        self.face_result = None
        self.face_complete = threading.Event()
        
        self.face_lock = threading.Lock()
    def start_face_processing(self):
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
        try:
            with self.face_lock:
                self.face_result = run_face_alt(mode="image")
        except Exception as e:
            print(f"face error: {e}")
            with self.face_lock:
                self.face_result = None
        finally:
            self.face_complete.set()
    def get_face_result(self, timeout=30):
        finished = self.face_complete.wait(timeout)
        with self.face_lock:
            return self.face_result if finished else None
HUBDOWN_ADDRESS = "E0:FF:F1:59:8E:6A"
HUBUP_ADDRESS = "E0:FF:F1:58:52:A2"
class BluetoothManager:
    def __init__(self, addr: str, port: int = 1):
        self.addr = addr
        self.port = port
        
        self.sock = None
        self.hub_thread = None
        self.hub_result = None
        self.hub_complete = threading.Event()

        self.lock = threading.Lock()
        self._ensure_connected()

    def _ensure_connected(self):
        with self.lock:
            if self.sock is None:
                s = BluetoothSocket(RFCOMM)
                s.connect((self.addr, self.port))
                self.sock = s
                return
    def start_hub_processing(self, cmd):
        with self.lock:
            print("rn")
            if self.hub_thread is None or not self.hub_thread.is_alive():
                self.hub_complete.clear()
                self.hub_thread = threading.Thread(
                    target=self._run_hub,
                    args = [cmd],
                    daemon=True
                )
                self.hub_thread.start()
            else:
                print("[hub] Processing already running")
    def _run_hub(self, cmd):
        try:
            with self.lock:
                self.hub_result = self.run_hub_alt(cmd)
        except Exception as e:
            print(f"hub error: {e}")
            with self.lock:
                self.hub_result = None
        finally:
            self.hub_complete.set()
    def run_hub_alt(self, cmd):
        buffer = b""
        try:
            self.sock.send((cmd + '\n').encode('utf-8'))
            while True:
                chunk = self.sock.recv(4096)  # 블로킹 또는 타임아웃
                if not chunk:
                    print("[A] 연결 끊김: 빈 바이트 수신")
                    return b""
                buffer += chunk
                if b'<<<<suc>>>>' in buffer:
                    return True
        except Exception as e:
            self.sock.close()
            self.sock = None
            return False
    def get_hub_result(self, timeout=60):
        finished = self.hub_complete.wait(timeout)
        with self.lock:
            return self.hub_result if finished else None
    def close_all(self):
        try:
            if self.sock is not None:
                self.sock.close()
        except:
            pass
        self.sock=None

def main(llmcmd=None):
    hub_up = BluetoothManager(HUBUP_ADDRESS)
    hub_down= BluetoothManager(HUBDOWN_ADDRESS)
    face = MultiThreadManager()
    # 무한 루프: 임의 조건에 따라 A/B 스레드 여러 번 실행
    try:
        cmdup='[[{"cmd":"move","val":"30"},{"cmd":"rotate_x","val":"20"}], [{"cmd":"move","val":"30"},{"cmd":"rotate_x","val":"20"}]]'
        cmddown='[[{"cmd":"shoot","val":"1"},{"cmd":"rotate_y","val":"20"}],[{"cmd":"shoot","val":"1"},{"cmd":"rotate_y","val":"20"}]]'
        
        while True:
            # 사용자 입력을 받아 A 스레드 실행
            if llmcmd:
                cmdup=llmcmd.replace('\n','').replace(' ','')
                cmddown=llmcmd.replace('\n','').replace(' ','')
            hub_up.start_hub_processing(cmdup)
            hub_down.start_hub_processing(cmddown)
            face.start_face_processing()
            r=hub_up.get_hub_result()
            re=hub_down.get_hub_result()
            result = face.get_face_result()
            print(result)
            break
            
    except KeyboardInterrupt:
        pass
    finally:
        # 프로그램 종료 직전에 열린 소켓 닫아 주기
        hub_up.close_all()
        hub_down.close_all()
        print("프로그램 종료. 소켓 닫음.")

if __name__ == "__main__":
    main()

