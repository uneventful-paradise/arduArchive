from src.client_model.network_client import NetworkClient
from src.utils.client_utils import set_client, nw_client, get_client
from src.server_params import logger
import serial
import serial.tools.list_ports
import time
SERIAL_PORT = 'COM5' #or com4

def handle_port_change(new_connection:bool):
    logger.warning("DETECTED PORT CHANGE")
    current_client = get_client()
    if new_connection:
        logger.debug("resetting client - cable connected.\n")
        if isinstance(current_client, NetworkClient) and nw_client.sock is None:
            logger.debug("Network client already resetting")
            return

        current_client.close()
        #give client time to reset
        time.sleep(2)
        set_client(nw_client)
        #let the connection thread restart the connection?
        nw_client.initiate_connection()
    else:
        logger.debug("Skipping reset of client - cable disconnected.\n")

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
            handle_port_change(new_connection=True)
        elif SERIAL_PORT not in ports and prev_con:
            prev_con = False
            handle_port_change(new_connection=False)
        else:
            pass
        time.sleep(1)

def check_port_presence():
    ports = [p.device for p in list(serial.tools.list_ports.comports())]
    return SERIAL_PORT in ports