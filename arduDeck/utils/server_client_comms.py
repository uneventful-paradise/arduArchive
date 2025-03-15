import os
import queue
import random

from utils.execute_funcs import *

CONFIG_FILE = "config/configs.json"
with open(CONFIG_FILE, "r") as f:
    CMD_DICT = json.load(f)

MAX_CLIENTS = 5
threads = []
HOST = "0.0.0.0"
PORT = 65432

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

FILENAME = "media/wanda.jpg"
ACK_SIZE = 4

ack_queue = queue.Queue()

def check_ack(req_id):
    ack = ack_queue.get()
    if int(ack) == req_id:
        print("ack successful")
        return True
    else:
        print(f"ACK process failed!! for packet {server_cmd_id} expected {req_id} got {ack} instead")
        return False

def handle_upload(client_socket, filename):

    print("STARTED UPLOAD\n")
    file_size = os.path.getsize(filename)
    # client_filename = "/"+filename.split('/')[-1]
    client_filename = "/wanda_Test_2048.jpg"
    current_server_cmd_id = server_cmd_id
    send_request(client_socket, SDCF, server_cmd_id, file_size, len(client_filename), client_filename)
    if not check_ack(current_server_cmd_id):
        return
    try:
        file_obj = open(filename, 'rb')
        while True:
            data = file_obj.read(CHUNK_SIZE)
            if not data:
                data = "EOF"
                send_request(client_socket, EDCF, server_cmd_id, 0, len(data), data)
                break
            else:
                current_server_cmd_id = server_cmd_id
                send_request(client_socket, FTCF, server_cmd_id, 0, len(data), data)
                #resend packet if lost??
                if not check_ack(current_server_cmd_id):
                    break
    except IOError as e:
        print("Could not open or read file.\n" + e.strerror)

def execute_command(client_socket, cmd_dict, command_id, request_contents):
    # print(ACT_DICT.keys())
    if not any(button["button_id"] == request_contents for button in cmd_dict["buttons"]):
        raise ValueError("Invalid command id")

    actions = []
    for button in cmd_dict["buttons"]:
        if button["button_id"] == request_contents:
            actions = button["actions"]
            break

    for action in actions:
        print(action["command_id"])
        if action["command_id"] in ACT_DICT.keys():
            print(action["command_args"])
            ACT_DICT[action["command_id"]](client_socket, command_id, *action["command_args"])
        else:
            print("Invalid command id in dictionary")


def handle_request(request, client_socket):
    header = struct.unpack("!iiii", request)
    command_type = int(header[0])
    command_id = int(header[1])
    opt_arg = int(header[2])
    req_len = int(header[3])

    #executing command associated to the button id
    try:
        print(f'REQUEST has type {command_type}, id {command_id}, opt_arg {opt_arg}, len {req_len}')
        # req_contents = client_socket.recv(req_len)

        req_contents = read_all(client_socket, req_len)
        readable_req_contents = req_contents.decode("utf-8")

        print(f'REQUEST_CONTENTS: {readable_req_contents}\n')
        if command_type == CFCF:
            ack_queue.put(readable_req_contents)
            # print(f"put {readable_req_contents} in queue")
        elif command_type == MCCF:
            execute_command(client_socket, CMD_DICT, command_id, opt_arg)   #change this to work based on request?
    except ValueError as e:
        print(e)

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
    global server_cmd_id
    responses = ["hey dude thanks for letting me know",
                 "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
                 "hyaimamanannanan"]
    while True:
        user_input = input(">")

        if user_input == "u":
            handle_upload(client_socket, FILENAME)
        if user_input == "f":
            print("Fetching data")
        if user_input == "m":
            server_cmd_id += 1
            msg_index = random.randint(0, len(responses) - 1)
            send_request(client_socket, INTF, server_cmd_id, 0, len(responses[msg_index]), responses[msg_index])