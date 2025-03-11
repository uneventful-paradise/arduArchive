#TODO: retest/build connection checking loop
#TODO: CLIENT add mutex and eliminate busy waiting in handle_request

import threading 

from utils.server_client_comms import *

if __name__ == '__main__':

    while True:
        # print("waiting for clients")
        conn, addr = s.accept()
        print(f"Connected by {addr}\n")
        listener_thread = threading.Thread(target=handle_new_connection, args=(conn, addr))
        threads.append(listener_thread)
        sender_thread = threading.Thread(target=handle_server_send, args=(conn, addr))
        threads.append(sender_thread)

        listener_thread.start()
        sender_thread.start()

    for thread in threads:
        thread.join()
    s.close()