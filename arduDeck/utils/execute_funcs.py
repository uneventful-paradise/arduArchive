import subprocess
import webbrowser
import json

from basic_comms import *

CONFIG_FILE = "config/key_codes.json"
with open(CONFIG_FILE, "r") as f:
    KEY_CODES = json.load(f)

def start_process(client_socket, cmd_id, file_path):
    try:
        command = subprocess.Popen([file_path])
        res = command.communicate()
        if command.returncode != 0:
            raise subprocess.CalledProcessError
    except subprocess.CalledProcessError(command.returncode, file_path):
        print(f"START_PROCESS {cmd_id} failed")
        print(res[1])


def start_url(client_socket, cmd_id, url):
    if webbrowser.open_new_tab(url):
        print(f"START_URL {cmd_id} successful")
    else:
        print(f"START_URL {cmd_id} failed")

def hard_key_press(client_socket, cmd_id, key_sequence):
    keys = key_sequence.split("+")
    new_keys = []
    for key in keys:
        value = key[1:]
        cmd_prefix = key[0]
        # print(value)
        if cmd_prefix == 'p':                       #just a paste command leave as is
            new_keys.append(key)
            continue
        if value.isdigit():
            new_keys.append(key)
        else:
            if len(value) == 1:                     #regular key
                print(f'regular key {value}')
                key = cmd_prefix + str(ord(value))
                new_keys.append(key)
            elif len(value) > 1:                    #special key
                print(f'special key {value}')
                key_code = ""
                for elem in KEY_CODES["keys"]:
                    if elem["key_name"] == value:
                        key_code = cmd_prefix + str(elem["key_code"])
                        print(f'special key is {key_code} of length {len(key_code)}')
                        new_keys.append(key_code)
                if key_code == "":
                    print(f"key code not found in config {key_code}")
            else:                                       #singular character command
                new_keys.append(key)

    hexed_string = '+'.join(new_keys)
    send_request(client_socket, MCCF, cmd_id, 0, len(hexed_string), hexed_string)


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