import time
import socket
import threading


class hpSocket:
    def __init__(self):
        self.socket = None
        self.addr = None


class hpGenerator:
    def __init__(self, timeout=5):
        self.timeout = timeout

    def generateSocket(self, local, cPub, cPriv):
        got = threading.Event()
        sockO = hpSocket()

        threading.Thread(target=self.hp, args=(local, cPub, cPriv, got, sockO)).start()

        got.wait()
        return sockO.socket, sockO.addr

    def hp(self, local, cPub, cPriv, got, sockO):
        timeout = time.time() + self.timeout
        halt = threading.Event()
        sem = threading.Semaphore()

        threading.Thread(target=self.acceptHP, args=(local[1], halt, sem, sockO, timeout), daemon=True).start()
        threading.Thread(target=self.acceptHP, args=(cPub[1], halt, sem, sockO, timeout), daemon=True).start()
        threading.Thread(target=self.connectHP, args=(local, cPub, halt, sem, sockO, timeout), daemon=True).start()
        threading.Thread(target=self.connectHP, args=(local, cPriv, halt, sem, sockO, timeout), daemon=True).start()

        halt.wait()
        sem.acquire()
        got.set()
        sem.release()

    def connectHP(self, local, addr, halt, sem, sockO, timeout):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this may be needed for linux
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.settimeout(1)
        sock.bind(local)
        while not halt.is_set() and time.time() < timeout:
            try:
                time.sleep(.05)  # to reduce system load when connections are failing
                sock.connect(addr)
            except socket.error:
                if halt.is_set():
                    break
                continue

            sem.acquire()

            if not halt.is_set():
                halt.set()
                sockO.socket = sock
                sockO.addr = addr
                sem.release()
            else:
                sem.release()
                break

    def acceptHP(self, port, halt, sem, sockO, timeout):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this may be needed for linux
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('', port))
        sock.listen(1)
        sock.settimeout(1)
        while not halt.is_set() and time.time() < timeout:
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                if halt.is_set():
                    break
                continue

            sem.acquire()

            if not halt.is_set():
                halt.set()
                sockO.socket = sock
                sockO.addr = addr
                sem.release()
            else:
                sem.release()
                break
