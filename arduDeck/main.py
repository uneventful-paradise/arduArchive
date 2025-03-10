#multithreaded server : https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
#TODO:acknowledgements after each message? also maybe msg ids should be 3chars strings (CLI_numb)
#TODO: retest/build connection checking loop
#TODO: is popen communicate blocking or is it fine

#TODO: CLIENT add mutex and eliminate busy waiting in handle_request

#TODO: add docs
#TODO: meddle with chunk size

import threading 

from utils.wifi_comms import *

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