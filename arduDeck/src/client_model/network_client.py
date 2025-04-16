from .base_client import BaseClient
import socket
from ..server_params import CHUNK_SIZE, logger

class NetworkClient(BaseClient):
    def __init__(self, sock:socket.socket):
        self.sock = sock

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