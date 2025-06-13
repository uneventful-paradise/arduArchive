import threading
from src.server_params import logger
from src.GUI.GUI import StreamDeckGUI
from src.utils.btn_funcs import BUTTON_LIST
from src.utils.client_utils import set_client, get_client, nw_client, sr_client
from src.server_comms import receive_request, handle_server_send, handle_request, check_connection
from src.utils.serial_helper import monitor_port_connection

def start_server():
    MAX_CLIENTS = 5
    threads = []


    conn_thread = threading.Thread(target=check_connection, args=(), daemon=True)
    conn_thread.start()
    port_monitoring_thread = threading.Thread(target=monitor_port_connection, args=(), daemon=True)
    port_monitoring_thread.start()

    set_client(nw_client)
    current_client = get_client()
    current_client.initiate_connection()
    print('finished client setup and starting up threads')
    # threads.append(conn_thread)
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
