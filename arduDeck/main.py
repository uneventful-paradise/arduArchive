#multithreaded server : https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
#TODO:acknowledgements after each message? also maybe msg ids should be 3chars strings
#TODO: retest/build connection checking loop
#TODO: is popen communicate blocking or is it fine

#TODO: add error handling to new functions via try catch blocks
#TODO: add file percentage transfer
#TODO: CLIENT add mutex and eliminate busy waiting in handle_request
import socket
import struct
import threading
import json
import os
import random

from utils.execute_funcs import *

MCCF = 0    #MACRO COMMAND FLAG
SDCF = 1    #START DOWNLOAD COMMAND FLAG
FTCF = 2    #FILE TRANSFER COMMAND FLAG
EDCF = 3    #END OF DOWNLOAD COMMAND FLAG
INTF = 4    #INITIALIZATION FLAG (start of routine)

CONFIG_FILE = "config/configs.json"
with open(CONFIG_FILE, "r") as f:
    CMD_DICT = json.load(f)

MAX_CLIENTS = 5
threads = []
HOST = "0.0.0.0"
PORT = 65431

FILENAME = "media/test_steam_img.jpg"
CHUNK_SIZE = 1024
HEADER_SIZE = 16
ACK_SIZE = 4


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

def read_all(client_socket, req_len):
    chunks = []
    bytes_received = 0
    while bytes_received < req_len:
        chunk = client_socket.recv(min(CHUNK_SIZE, req_len - bytes_received))
        if not chunk:
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_received += len(chunk)
    return b''.join(chunks)

def send_all(client_socket, data):
    total_sent = 0
    while total_sent < len(data):
        sent = client_socket.send(data[total_sent:])
        if not sent:
            raise RuntimeError("socket connection broken")
        total_sent += sent

def handle_upload(client_socket, filename):
    print("STARTED UPLOAD\n")
    file_size = str(os.path.getsize(filename))
    # client_filename = "/"+filename.split('/')[-1]
    client_filename = "/test_2_steam.jpg"
    send_request(client_socket, SDCF, 0, 0, len(client_filename), client_filename)
    try:
        with open(filename, "rb") as file_obj:
            while True:
                data = file_obj.read(CHUNK_SIZE)
                if not data:
                    data = "EOF"
                    send_request(client_socket, EDCF, 0, 0, len(data), data)
                    break
                else:
                    send_request(client_socket, FTCF, 0, 0, len(data), data)
                    #resend packet if lost??

    except IOError as e:
        print("Could not open or read file.\n" + e.strerror)


def send_request(client_socket, cmd_type, cmd_id, file_id, req_len, req):
    #format: < = small endian (! for network = big endian)
    if req_len > CHUNK_SIZE:
        print(f"send {cmd_id} exceeded size limit")

    enc_type = "hex"
    if isinstance(req, str):
        req = req.encode('utf-8')
        enc_type = "str"
    packet = struct.pack("!iiii", cmd_type, cmd_id, file_id, req_len) + req

    if enc_type == "str":
        print(f"SENT packet of type {cmd_type} id {cmd_id} fid {file_id} size {len(req)}\nSEND CONTENTS: " + req.decode() + "\n")
    else:
        print(f"SENT packet of type {cmd_type} id {cmd_id} fid {file_id} size {len(req)}\nSEND CONTENTS: " + req.hex() + "\n")

    send_all(client_socket, packet)
    # client_socket.sendall(packet)

def execute_command(cmd_dict, command_id, request_contents):
    if not any(button["button_id"] == request_contents for button in cmd_dict["buttons"]):
        print("Invalid command")
        return

    actions = []
    for button in cmd_dict["buttons"]:
        if button["button_id"] == request_contents:
            actions = button["actions"]
            break

    for action in actions:
        ACT_DICT[action["command_id"]](command_id, *action["command_args"])


def handle_request(request, client_socket):
    header = struct.unpack("!iiii", request)
    command_type = int(header[0])
    command_id = int(header[1])
    file_id = int(header[2])
    req_len = int(header[3])

    print(f'REQUEST has type {command_type}, id {command_id}, fid {file_id}, len {req_len}')
    # req_contents = client_socket.recv(req_len)
    req_contents = read_all(client_socket, req_len)
    readable_req_contents = req_contents.decode("utf-8")
    print(f'REQUEST_CONTENTS: {readable_req_contents}\n')

    #executing command associated to the button id
    execute_command(CMD_DICT, command_id, command_type)


def handle_new_connection(client_socket, client_addr):
    print(f'Created new thread for client {client_addr}')
    while True:
        # req = client_socket.recv(HEADER_SIZE)
        req = read_all(client_socket, HEADER_SIZE)
        #try catch here?
        if not req:
            client_socket.close()
            print("Client has requested disconnect")
            return None
        print(f'Client {client_addr} requested: {req}')
        handle_request(req, client_socket)

def handle_server_send(client_socket, client_addr):
    index = 0
    responses = ["hey dude thanks for letting me know",
                 "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
                 "hyaimamanannanan"]
    while True:
        user_input = input(">")

        if index < 1 and user_input == "upload":
            handle_upload(client_socket, FILENAME)
            index += 1
        if user_input == "fetch":
            print("Fetching data")
        if user_input == "message":
            msg_index = random.randint(0, len(responses) - 1)
            send_request(client_socket, MCCF, msg_index, 0, len(responses[msg_index]), responses[msg_index])

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