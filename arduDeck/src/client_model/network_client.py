import select
import socket

from src.utils.data_format import generate_gui_conn_update
from src.server_params import CHUNK_SIZE, logger
from src.client_model.base_client import BaseClient
#TODO: add locks to writes and reads?
class NetworkClient(BaseClient):
    def __init__(self, host:str, port: int, timeout: float):
        self.host = host
        self.port = port
        # self.timeout = timeout
        self.timeout = None

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen(1)

        self.server_sock = server_sock
        self.sock = None

    @property
    def chunk_size(self) -> int:
        return 2048

    def initiate_connection(self):
        logger.debug("Network Server initialized. Waiting for clients")
        conn, addr = self.server_sock.accept()
        logger.debug("Connected by %s", addr)
        generate_gui_conn_update("[FAIL]Network client disconnected.")
        self.sock = conn
        self.sock.settimeout(self.timeout)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        SIO_KEEPALIVE_VALS = 0x98000004
        onoff = 1
        idle_socket_timer = 5000  # 10 seconds before sending keepalive probes
        socket_probe_interval = 1000  # 3 seconds between keepalive probes

        self.sock.ioctl(SIO_KEEPALIVE_VALS, (onoff, idle_socket_timer, socket_probe_interval))

    def check_connection(self) -> bool:
        if self.sock is None:
            return False  # socket hasn't been initialized yet
        # print(self.sock, type(self.sock), hasattr(self.sock, 'fileno'))
        try:
            # poll for readability; 0s timeout → non-blocking
            rlist, _, _ = select.select([self.sock], [], [], 0)
        except ValueError:
            # invalid socket → treat as closed
            return False

        if self.sock in rlist:
            # socket is readable: either data waiting or it's closed
            try:
                data = self.sock.recv(1, socket.MSG_PEEK)
            except BlockingIOError as e:
                logger.error("Blocking error.")
                return True  # socket is open and reading from it would block
            except ConnectionResetError as e:
                logger.error("ConnectionResetError. Waiting for new connection")
                return False
            except Exception as e:
                logger.exception(e)
                return True
            if not data:
                logger.debug("Clean EOF")
                return False  # clean EOF
        return True

    def clear_channel(self) -> None:
        orig_blocking = self.sock.getblocking()
        self.sock.setblocking(False)
        read = 0
        try:
            while True:
                chunk = self.sock.recv(self.chunk_size)
                if not chunk:
                    break
                read += len(chunk)
        except BlockingIOError as e:
            logger.exception(e)
            pass
        finally:
            self.sock.setblocking(orig_blocking)

    def read_all(self, req_len: int) -> bytes:
        if self.sock is None:
            raise RuntimeError("Socket not initialized")

        if req_len > CHUNK_SIZE:
            raise ValueError("Payload length exceeds chunk size")

        data = b""
        try:
            while len(data) < req_len:
                chunk = self.sock.recv(min(CHUNK_SIZE, req_len - len(data)))
                if not chunk:
                    logger.error("socket connection broken")
                    raise ConnectionResetError
                data+=chunk

            return data

        except (OSError, socket.error) as e:
            logger.error("read_all exception: %s", e)
            return b''
        except TimeoutError as e:
            #todo: handle this properly - inside the while?
            logger.error("Read operation timed out")

    def write_all(self, data: bytes) -> int:
        if self.sock is None:
            raise RuntimeError("Socket not initialized")

        total_sent = 0
        try:
            while total_sent < len(data):
                sent = self.sock.send(data[total_sent:])
                if not sent:
                    logger.error("socket connection broken")
                    raise ConnectionResetError

                total_sent += sent
        except (OSError, socket.error) as e:
            logger.error("write_all exception: %s. Restarting connection", e, exc_info=True)
            try:
                self.sock.close()
            except (OSError, socket.error):
                logger.error("Error at closing socket")
            self.initiate_connection()
        return total_sent

    def close(self) -> None:
        try:
            self.sock.close()
            self.sock = None
        except (OSError, socket.error):
            logger.error("Error closing socket - already closed or bad state")
        logger.warning("Closed network connection")

    def reset_connection(self):
        self.close()
        self.initiate_connection()