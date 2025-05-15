import select
import socket
from src.server_params import CHUNK_SIZE, logger
from src.client_model.base_client import BaseClient

class NetworkClient(BaseClient):
    def __init__(self, host:str, port: int):
        self.host = host
        self.port = port

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
        self.sock = conn
    #alternative using nonblocking socket
    # def is_socket_closed(sock: socket.socket) -> bool:
    # # remember the original blocking mode
    # orig_blocking = sock.getblocking()
    # sock.setblocking(False)
    # try:
    #     # peek into the buffer without removing bytes
    #     data = sock.recv(16, socket.MSG_PEEK)
    #     if len(data) == 0:
    #         # orderly shutdown: remote closed
    #         return True
    # except BlockingIOError:
    #     # no data available right now → still open
    #     return False
    # except ConnectionResetError:
    #     # reset by peer
    #     return True
    # except Exception:
    #     logger.exception("Unexpected error checking socket state")
    #     return False
    # finally:
    #     # restore the original mode
    #     sock.setblocking(orig_blocking)
    #
    # return False

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
                data = self.sock.recv(16, socket.MSG_PEEK)
            except BlockingIOError as e:
                logger.exception(e)
                return True  # socket is open and reading from it would block
            except ConnectionResetError as e:
                logger.exception(e)
                return False
            except Exception as e:
                logger.exception(e)
                return True
            if not data:
                return False  # clean EOF
        return True

    """Loop to send all data to server.

    TCP might not send an entire message at once.
    the function makes sure to send the entire chunk of information
    by looping until there is nothing left to send"""
    def read_all(self, req_len: int) -> bytes:
        if req_len > CHUNK_SIZE:
            raise ValueError("Payload length exceeds chunk size")
        chunks = []
        bytes_received = 0
        try:
            while bytes_received < req_len:
                chunk = self.sock.recv(min(CHUNK_SIZE, req_len - bytes_received))
                if not chunk:
                    logger.error("socket connection broken")
                    break
                chunks.append(chunk)
                bytes_received += len(chunk)
        except socket.error as e:
            logger.error("read_all exception: %s", e, exc_info=True)

        return b''.join(chunks)

    """Similar to read_all. Loop until all data has been sent"""
    def write_all(self, data: bytes) -> None:
        try:
            total_sent = 0
            while total_sent < len(data):
                sent = self.sock.send(data[total_sent:])
                if not sent:
                    logger.error("socket connection broken")
                    break
                total_sent += sent
        except socket.error as e:
            logger.error("write_all exception: %s", e, exc_info=True)

    def close(self) -> None:
        logger.warning("Closed network connection")
        self.sock.close()