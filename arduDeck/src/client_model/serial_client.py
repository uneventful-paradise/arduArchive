from serial.serialutil import SerialException

from .base_client import BaseClient
import socket
from ..server_params import CHUNK_SIZE, logger
import serial
import time
# open serial port (adjust port name and baud to match ESP32)

class SerialClient(BaseClient):
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = serial.Serial()
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = self.port
        self.serial.baudrate = self.baudrate
        self.serial.timeout = None
        # try:
        #     self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=None)
        #     data = self.serial.readline()
        #     logger.debug(data)
        # except SerialException as e:
        #     logger.error(e)

    @property
    def chunk_size(self) -> int:
        return 240 #set this as 240

    def initiate_connection(self):
        try:
            self.serial.open()
            data = self.serial.readline()
            logger.debug(data)
        except SerialException as e:
            logger.error(e)
        logger.debug('Serial server initialized. Waiting for connection')
        data = self.serial.readline()
        # while data != 'serial_start\n':
        while data != b'serial_start\n':
            data = self.serial.readline()
            logger.debug(data.decode("utf-8"))
        logger.debug("Serial starting effective communication")

    def read_all(self, req_len: int) -> bytes:
        if req_len > CHUNK_SIZE:
            raise ValueError("Payload length exceeds chunk size")
        # return self.serial.readline()
        data = b""
        try:
            #read call blocks so while is prolly not necessary
            while len(data) < req_len:
                chunk = self.serial.read(req_len - len(data))
                if not chunk:
                    logger.warning("serial port read timed out")
                    continue
                data += chunk
            return data
        except serial.SerialException as e:
            #no new data from serial port
            logger.error(e)
            return b''
        except TypeError as e:
            logger.error(e)
            #disconnect of USB -> UART occurred

    def write_all(self, data: bytes) -> None:
        total_sent = 0
        packets = 0
        ser_buff = 200
        # while total_sent < len(data):
        #     sub_chunk = total_sent
        #     max_index = min(sub_chunk + ser_buff, len(data))
        #     data_sub_chunk = data[sub_chunk:max_index]
        #     sent = self.serial.write(data_sub_chunk)
        #     self.serial.flush()
        #     if sent == 0:
        #         logger.exception("Serial port write timed out")
        #         break
        #     total_sent += sent
        #     packets += 1
        #     time.sleep(0.4)
        #     #send chunks slower
        #     #send individual characters
        #     #min(available, chunk) and higher priority for read
        try:
            while total_sent < len(data):
                sent = self.serial.write(data[total_sent:])
                self.serial.flush()
                if sent == 0:
                    logger.exception("Serial write timed out")
                    break
                    # raise RuntimeError("Serial port write timed out")
                total_sent += sent
        except serial.SerialException as e:
            logger.exception(e)
            return None
            #should write functions return amount written?
        except TypeError as e:
            logger.exception(e)
            self.serial.close()
            return None

        # logger.debug(f'finished sending in {packets} packs')

    def close(self) -> None:
        logger.warning("Closed serial connection")
        self.serial.close()