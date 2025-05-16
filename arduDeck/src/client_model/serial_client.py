import time
import serial
import serial.tools.list_ports
from src.utils.data_format import generate_gui_conn_update
from src.basic_comms import send_conf
from src.client_model.base_client import BaseClient
from src.server_params import CHUNK_SIZE, logger

SERIAL_PORT = 'COM5'

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

        self.my_ports = self.list_ports()
        self.my_port = None #not yet opened
        self.connected = False

        # self.serial = serial.Serial(
        #     port=self.port,
        #     baudrate=self.baudrate,
        #     timeout=self.timeout,  # or None for blocking
        #     dsrdtr=False,
        #     rtscts=False,
        #     # do_not_open: if you want to delay .open() call, pass port=None here and assign later
        # )

    @property
    def chunk_size(self) -> int:
        return 240

    def initiate_connection(self):
        logger.debug('initiating serial connection')
        data = b''
        port_name = SERIAL_PORT
        timeout = 30
        start = time.time()

        while True:
            # timeout expiry
            if time.time() - start > timeout:
                generate_gui_conn_update(f"[FAIL] Timed out while waiting for {port_name}")
                logger.error("timeout")
                break
            # port existence
            ports = [p.device for p in serial.tools.list_ports.comports()]
            if port_name not in ports:
                generate_gui_conn_update(f"[FAIL]{port_name} not found.")
                # logger.error("port not found in list")
                time.sleep(2)
                continue

            try:
                if not self.serial.is_open:
                    self.serial.open()
                    data = self.serial.readline()
                    logger.debug(data)
            except FileNotFoundError:
                logger.error("COM Port not found during init")
                generate_gui_conn_update(f"[FAIL]Port {SERIAL_PORT} not found.")
                continue
            except PermissionError:
                logger.error("Permission denied during init")
                generate_gui_conn_update(f"[FAIL]Permission for port {SERIAL_PORT} denied.")
                time.sleep(2)
                continue
            except serial.PortNotOpenError:
                logger.error("Port was not open during init connection attempt")
                generate_gui_conn_update(f"[FAIL]Port {SERIAL_PORT} is not open.")
                time.sleep(2)
                continue
            except serial.SerialException:
                logger.error("Serial connection failed during init")
                generate_gui_conn_update(f"[FAIL]Generic serial exception")
                time.sleep(2)
                continue

            logger.debug("Successfully opened port during initialization")
            break

        #Port is now open. Waiting to receive connection request

        logger.debug('Serial server initialized. Waiting for connection')
        while data != b'serial_start\n':
            try:
                data = self.serial.readline()
                logger.debug(data.decode("utf-8"))
            except FileNotFoundError:
                logger.error("COM Port not found during init read")
                generate_gui_conn_update(f"[FAIL]Port {SERIAL_PORT} not found.")
                continue
            except PermissionError:
                logger.error("Permission denied during init read")
                generate_gui_conn_update(f"[FAIL]Permission for port {SERIAL_PORT} denied.")
                time.sleep(2)
                continue
            except serial.PortNotOpenError:
                logger.error("Port was not open during init read attempt")
                generate_gui_conn_update(f"[FAIL]Port {SERIAL_PORT} is not open.")
                time.sleep(2)
                continue
            except serial.SerialException:
                logger.error("Serial connection failed during init read")
                generate_gui_conn_update(f"[FAIL]Generic serial exception")
                time.sleep(2)
                continue

        send_conf(current_client=self, cmd_id=0)
        self.connected = True
        logger.debug("Serial starting effective communication")

    def list_ports(self) -> list:
        my_ports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        return my_ports

    def check_connection(self) -> bool:
        try:
            self.my_ports = self.list_ports()
            self.my_port = [port for port in self.my_ports if SERIAL_PORT in port][0]
            if self.my_port not in self.my_ports or not self.connected:
                return False
            return True
        except IndexError as e:
            logger.error("Requested port is out of range")
            # logger.exception(e)
            # self.connected = False
            time.sleep(2)

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
    #TODO: add chunking
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
        self.connected = False