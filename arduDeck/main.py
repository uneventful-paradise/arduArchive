#TODO: retest/build connection checking loop
#TODO: CLIENT add mutex and eliminate busy waiting in handle_request

import threading 

from utils.server_client_comms import *

if __name__ == '__main__':

    while True:
        logger.debug("waiting for clients")
        conn, addr = s.accept()
        logger.debug("Connected by %s", addr)
        listener_thread = threading.Thread(target=receive_request, args=(conn, addr))
        threads.append(listener_thread)
        sender_thread = threading.Thread(target=handle_server_send, args=(conn, addr))
        threads.append(sender_thread)
        request_handling_thread = threading.Thread(target=handle_request, args=(conn, addr))
        threads.append(request_handling_thread)

        for thread in threads:
            thread.start()

    for thread in threads:
        thread.join()
    s.close()