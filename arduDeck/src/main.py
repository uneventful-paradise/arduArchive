#TODO: retest/build connection checking loop
from src.basic_comms import set_client, get_client, nw_client, sr_client
from src.client_model.base_client import BaseClient
from src.client_model.network_client import NetworkClient
from src.client_model.serial_client import SerialClient
from src.server_comms import receive_request, handle_server_send, handle_request
from src.GUI.GUI import StreamDeckGUI
from src.server_params import logger
import threading
from src.utils.btn_funcs import BUTTON_LIST


def start_server():
    MAX_CLIENTS = 5
    threads = []

    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # s.bind((HOST, PORT))
    # s.listen(5)
    # while True:
    #     logger.debug("waiting for clients")
    #     conn, addr = s.accept()
    #     logger.debug("Connected by %s", addr)

    set_client(nw_client)
    current_client = get_client()
    current_client.initiate_connection()
        # addr = "ceva"
        # set_client(new_client)
        # current_client = get_client()


    listener_thread = threading.Thread(target=receive_request, args=(), daemon=True)
    threads.append(listener_thread)
    sender_thread = threading.Thread(target=handle_server_send, args=(), daemon=True)
    threads.append(sender_thread)
    request_handling_thread = threading.Thread(target=handle_request, args=(), daemon=True)
    threads.append(request_handling_thread)

    for thread in threads:
        thread.start()

    logger.debug("exiting starts_server")

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server,daemon=True)
    server_thread.start()
    app = StreamDeckGUI(BUTTON_LIST)
    app.mainloop()
