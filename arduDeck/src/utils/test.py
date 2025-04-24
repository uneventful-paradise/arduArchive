from src.client_model.base_client import BaseClient
import socket
from src.server_params import CHUNK_SIZE, logger
import serial
import time
# open serial port (adjust port name and baud to match ESP32)

class SerialClient(BaseClient):
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.serial = serial.Serial(port, baudrate, timeout=None)
        logger.debug('Serial client connected')
        # data = self.serial.readline()
        # while data != b'serial_start\n':
        #     print(data)
        #     data = self.serial.readline()
        # logger.debug("Starting effective communication")

    def read_all(self, req_len: int) -> bytes:
        if req_len > CHUNK_SIZE:
            raise ValueError("Payload length exceeds chunk size")
        return self.serial.readline().decode('ascii')
        # data = b""
        #
        # #read call blocks so while is prolly not necessary
        # while len(data) < req_len:
        #     chunk = self.serial.read(req_len - len(data))
        #     if not chunk:
        #         logger.warning("serial port read timed out")
        #         continue
        #     data += chunk
        # return data

    def write_all(self, data: bytes) -> None:
        # total_sent = 0
        # while total_sent < len(data):
        #     sent = self.serial.write(data[total_sent:])
        #     self.serial.flush()
        #     if sent == 0:
        #         logger.exception("Serial port write timed out")
        #         break
        #     total_sent += sent
        f = open("testing/long_ipsum.txt", "r")
        packets = 0
        ser_buff = 200
        while True:
            #send chunks slower
            #send individual characters
            #min(available, chunk) and higher priority for read
            d = f.read(1024)
            if not d:
                f.close()
                logger.debug("sent a total of %d packets", packets)
                break
            else:
                sub_chunk = 0
                while sub_chunk < len(d):
                    max_index = min(sub_chunk + ser_buff, len(d))
                    data_sub_chunk = d[sub_chunk:max_index]
                    sent = self.serial.write(data_sub_chunk.encode())
                    sub_chunk += sent
                    logger.debug(f"sent {sent} bytes")

                packets +=1
                time.sleep(0.4)

    def close(self) -> None:
        logger.warning("Closed serial connection")
        self.serial.close()

s = '(2,2)'
pos = (tuple(int(x) for x in s.strip("()").split(',')))
print(pos)