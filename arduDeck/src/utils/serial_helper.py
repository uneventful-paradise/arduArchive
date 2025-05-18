from src.utils.client_utils import set_client, nw_client
from src.server_params import logger
import serial
import serial.tools.list_ports
import time
SERIAL_PORT = 'COM5'

def handle_port_change():
    logger.warning("DETECTED PORT CHANGE - SETTING CLIENT TO NW TYPE")
    set_client(nw_client)
    nw_client.initiate_connection()

def monitor_port_connection():
    prev_con = None
    ports = [p.device for p in list(serial.tools.list_ports.comports())]
    if SERIAL_PORT in ports:
        prev_con = True
    else:
        prev_con = False

    while True:
        ports = [p.device for p in list(serial.tools.list_ports.comports())]
        if SERIAL_PORT in ports and not prev_con:
            prev_con = True
            handle_port_change()
        elif SERIAL_PORT not in ports and prev_con:
            prev_con = False
            handle_port_change()
        else:
            pass
        time.sleep(1)