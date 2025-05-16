import threading
from src.client_model.base_client import BaseClient
from src.client_model.network_client import NetworkClient
from src.client_model.serial_client import SerialClient
from src.server_params import *

client_lock = threading.Lock()

client: BaseClient = None
nw_client = NetworkClient(HOST, PORT)
sr_client = SerialClient(port='COM5', baudrate=115200, timeout=1.0)

def read_all(current_client: BaseClient, req_len: int) -> bytes:
    with client_lock:
        return current_client.read_all(req_len)

def write_all(current_client: BaseClient, data: bytes):
    with client_lock:
        current_client.write_all(data)

def set_client(new_client: BaseClient):
    global client
    with client_lock:
        if client is not None:
            # client.close()
            client = None
        client = new_client
    logger.debug("Successfully set client")

def get_client() -> BaseClient:
    global client
    with client_lock:
        if client is None:
            logger.debug("Client is not set")
        return client

def swap_client():
    current_client = get_client()
    if isinstance(current_client, NetworkClient):
        current_client.close()
        set_client(sr_client)
        sr_client.initiate_connection()
    elif isinstance(current_client, SerialClient):
        set_client(nw_client)
        nw_client.initiate_connection()
        sr_client.close()
