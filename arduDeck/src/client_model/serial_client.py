from .base_client import BaseClient
import socket
from ..server_params import CHUNK_SIZE, logger
import serial
import time
# open serial port (adjust port name and baud to match ESP32)

class SerialClient(BaseClient):
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.serial = serial.Serial(port, baudrate, timeout=None)
        logger.debug('Serial client connected')
        data = self.serial.readline()
        # while data != 'serial_start\n':
        while data != b'serial_start\n':
            logger.debug(data.decode("utf-8"))
            data = self.serial.readline()
        logger.debug("Starting effective communication")

    def read_all(self, req_len: int) -> bytes:
        if req_len > CHUNK_SIZE:
            raise ValueError("Payload length exceeds chunk size")
        # return self.serial.readline()
        data = b""

        #read call blocks so while is prolly not necessary
        while len(data) < req_len:
            chunk = self.serial.read(req_len - len(data))
            if not chunk:
                logger.warning("serial port read timed out")
                continue
            data += chunk
        return data

    def write_all(self, data: bytes) -> None:
        total_sent = 0
        packets = 0
        ser_buff = 200
        while total_sent < len(data):
            sub_chunk = total_sent
            max_index = min(sub_chunk + ser_buff, len(data))
            data_sub_chunk = data[sub_chunk:max_index]
            sent = self.serial.write(data_sub_chunk)
            self.serial.flush()
            if sent == 0:
                logger.exception("Serial port write timed out")
                break
            total_sent += sent
            packets += 1
            time.sleep(0.4)
            #send chunks slower
            #send individual characters
            #min(available, chunk) and higher priority for read
        logger.debug(f'finished sending in {packets} packs')

    def close(self) -> None:
        logger.warning("Closed serial connection")
        self.serial.close()