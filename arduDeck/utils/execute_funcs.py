import subprocess
import webbrowser

from basic_comms import *

def start_process(client_socket, cmd_id, file_path):
    try:
        command = subprocess.Popen([file_path])
        res = command.communicate()
        if command.returncode != 0:
            raise subprocess.CalledProcessError
    except subprocess.CalledProcessError(command.returncode, file_path):
        print(f"START_PROCESS {cmd_id} failed")
        print(res[1])


def start_url(cmd_id, url):
    if webbrowser.open_new_tab(url):
        print(f"START_URL {cmd_id} successful")
    else:
        print(f"START_URL {cmd_id} failed")

def hard_key_press(client_socket, cmd_id, key_sequence):
    print("entered function")
    keys = key_sequence.split("+")
    #values inbetween separator can be key value or wait time e.g. A+300+B
    #means press A wait 300 ms then press B
    send_request(client_socket, MCCF, cmd_id, 0, len(key_sequence), key_sequence)


ACT_DICT = {
    "START_PROCESS": start_process,
    "START_URL": start_url,
    "HARD_KEY_PRESS": hard_key_press,
}

# path = path.rstrip('\r\n')
# escaped_path = path.encode('unicode_escape').decode()
# escaped_path = escaped_path.rstrip('\r\n')
# print(path)
# print(escaped_path)
# subprocess.Popen(escaped_path)