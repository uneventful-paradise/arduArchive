import subprocess
import webbrowser
import json

from basic_comms import *
#load modifier key codes from file
CONFIG_FILE = "config/key_codes.json"
with open(CONFIG_FILE, "r") as f:
    KEY_CODES = json.load(f)

"""Start a new process using python subprocesses.
It starts the process in a nonblocking manner using `Popen`
so the server is still responsive during this time"""
def start_process(client_socket, cmd_id, file_path):
    try:
        command = subprocess.Popen([file_path])
        res = command.communicate()
        if command.returncode != 0:
            raise subprocess.CalledProcessError
    except subprocess.CalledProcessError(command.returncode, file_path):
        print(f"START_PROCESS {cmd_id} failed")
        print(res[1])

"""Opens a new tab or a new browser instance if none is running currently.
This can be performed using shell but is unsafe and not recommended"""
def start_url(client_socket, cmd_id, url):
    if webbrowser.open_new_tab(url):
        print(f"START_URL {cmd_id} successful")
    else:
        print(f"START_URL {cmd_id} failed")

"""Parses the macro sequence and converts key codes to their decimal value.
The individuals commands of the sequence are separated by the `+` character
and can be any of the following:

wNUMERICAL_VALUE  - wait for `NUMERICAL_VALUE` miliseconds. essentially a delay
dKEY_VALUE        - press down the key represented in decimal value by `KEY_VALUE`
uKEY_VALUE        - release the key represented in decimal value by `KEY_VALUE`
r                 - release all pressed keys
pVALUE            - print VALUE string

Keyboard modifiers (special keys like ALT, ESCAPE etc.) have codes assigned in the
KEY_CODES config file.
"""
def hard_key_press(client_socket, cmd_id, key_sequence):
    keys = key_sequence.split("+")
    new_keys = []
    for key in keys:
        #get command prefix and argument
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
                key = cmd_prefix + str(ord(value))  #get asii decimal value of key
                new_keys.append(key)
            elif len(value) > 1:                    #special key
                print(f'special key {value}')
                key_code = ""
                #get the assigned key code from the config file
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

#maps the commands to executing functions
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