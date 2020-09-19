import socket
import threading
import time
import concurrent.futures


def tcpHP(local, cPub, cPriv, to=5):
    timeout = time.time() + to
    halt = threading.Event()
    sem = threading.Semaphore()
    # print("Beginning hole punching process")
    # start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        t1 = executor.submit(acceptHP, local[1], halt, sem, timeout)
        t2 = executor.submit(acceptHP, cPub[1], halt, sem, timeout)
        t3 = executor.submit(connectHP, local, cPub, halt, sem, timeout)
        t4 = executor.submit(connectHP, local, cPriv, halt, sem, timeout)

        threads = [t1, t2, t3, t4]
        ret = False
        for thread in threads:
            res = thread.result()
            if res:
                if not ret:
                    ret = res
                else:
                    res[1].close()

    halt.clear()

    if not ret:
        print("Hole punching timed out")
    # print("Connection Acquired in {} seconds".format(time.time() - start))
    return ret


def connectHP(local, addr, halt, sem, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # this may be needed for linux
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.settimeout(1)
    sock.bind(local)
    # print("Connect,", addr)
    while not halt.is_set() and time.time() < timeout:
        # start = time.time()
        try:
            time.sleep(.1)
            sock.connect(addr)
            # print("Connected w/,",sock)
        except socket.error:
            if halt.is_set():
                break
            continue

        sem.acquire()

        if not halt.is_set():
            halt.set()
            sem.release()
            # print("Hole Punched")
            return True, sock, addr
        else:
            # print("Halting")
            sem.release()
            break

    # print("Halting {}, {}s".format(local, time.time()-start))
    return False


def acceptHP(port, halt, sem, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # this may be needed for linux
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(('', port))
    # print("Accept,", port)
    sock.listen(1)
    sock.settimeout(1)
    while not halt.is_set() and time.time() < timeout:
        # start = time.time()
        try:
            conn, addr = sock.accept()
        except socket.timeout:
            if halt.is_set():
                break
            continue

        sem.acquire()

        if not halt.is_set():
            halt.set()
            # print("Hole Punched")
            return True, conn, addr
        else:
            # print("Halting")
            sem.release()
            break
    # print("Halting {}, {}s".format(port, time.time()-start))
    return False
