import os
import queue
import random

import basic_comms
from utils.execute_funcs import *

# Load current key-action configuration into a global dictionary
# to be used by the action executing functions
CONFIG_FILE = "config/configs.json"
with open(CONFIG_FILE, "r") as f:
    CMD_DICT = json.load(f)

MAX_CLIENTS = 5
threads = []
HOST = "0.0.0.0"
PORT = 65431

# Initialize the main connection socket. Bind and listen
# will be called on it resulting in client connection sockets.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)

FILENAME = "media/wanda.jpg"
DEFAULT_CLIENT_DOWNLOAD_FOLDER = "/init_icons"

"""In the context of file transfers the server sends a packet then
waits for confirmation before sending the next one. The queue is used to
store incoming confirmations. Thus, the client thread blocks performing a
get operation while waiting for a packet's acknowledgment."""
ack_queue = queue.Queue()

"""The acknowledgement process is defined as follows:

The client receives a server request identified by the cmd_id field
It checks the message against the provided and self-computed CRC32 values
then it responds with a verdict:

The value of the acknowledgement is the initial server cmd_id if the check 
succeeded or `-1` otherwise."""
def check_ack(req_id):
    ack = ack_queue.get()
    if int(ack) == req_id:
        print(f"ack successful for req_id {req_id} and server_id {basic_comms.server_cmd_id}\n")
        return True
    elif int(ack) == -1:
        print(f"ACK process failed! Requesting resend")
        return False
    else:
        print(f"ACK got unexpected value {ack} while expecting {req_id} / {basic_comms.server_cmd_id}")
        return False

"""Opens the upload source file and sends predefined sized chunks of data to client.

The first send contains an `upload start flag` alongside the file size and file name(on the client side).
Then `file_size/CHUNK_SIZE` file contents sends follow. Finally when EOF is encountered
on the server side, an `upload end flag` is sent to the client to stop the transfer. 
"""
def handle_upload(client_socket, filename, client_location):
    print("STARTED UPLOAD\n")
    file_size = os.path.getsize(filename)
    client_filename = client_location + "/" + filename.split('/')[-1]
    print(f'writing to {client_filename}')

    #send the upload initiating request
    req_cmd = basic_comms.server_cmd_id
    send_request(client_socket, SDCF, req_cmd, file_size, len(client_filename), client_filename)

    #TODO: ack could be on each message so the resending could happen withing the send_request function?
    #wait for confirmation
    while not check_ack(req_cmd):
        send_request(client_socket, SDCF, req_cmd,  file_size, len(client_filename), client_filename)
    try:
        file_obj = open(filename, 'rb')
        while True:
            data = file_obj.read(CHUNK_SIZE)
            req_cmd = basic_comms.server_cmd_id
            #send transfer ending request
            if not data:
                data = "EOF"
                send_request(client_socket, EDCF, req_cmd, 0, len(data), data)
                # TODO: retry for a fixed number of times?
                while not check_ack(req_cmd):
                    send_request(client_socket, EDCF, req_cmd, 0, len(data), data)
                break
            #send the following file contents request
            else:
                send_request(client_socket, FTCF, req_cmd, 0, len(data), data)
                while not check_ack(req_cmd):
                    send_request(client_socket, FTCF, req_cmd, 0, len(data), data)

    except IOError as e:
        print("Could not open or read file.\n" + e.strerror)

"""Executes the action associated with the id of a pressed button.
It checks the existence of the requested button id then calls the associated action
with the proper arguments.

Actions are functions mapped to an action name field in the config of every button.
The arguments are also defined within the button configuration."""
def execute_command(client_socket, cmd_dict, command_id, request_contents):
    # print(ACT_DICT.keys())
    #check for button existence and validity
    if not any(button["button_id"] == request_contents for button in cmd_dict["buttons"]):
        raise ValueError("Invalid command id")

    #get button actions
    actions = []
    for button in cmd_dict["buttons"]:
        if button["button_id"] == request_contents:
            actions = button["actions"]
            break

    #get action arguments and execute the action
    for action in actions:
        print(action["command_id"])
        if action["command_id"] in ACT_DICT.keys():
            print(action["command_args"])
            ACT_DICT[action["command_id"]](client_socket, command_id, *action["command_args"])
        else:
            print("Invalid command id in dictionary")

"""Function to continuously check for the status of the connection."""
#TODO: interrupt functions when connection drops
def check_connection(client_socket):
    try:
        data = client_socket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
        if len(data) == 0:
            return False
    except BlockingIOError as e:
        print(e)
        return True    #socket is open and reading from it would block
    except ConnectionResetError as e:
        print(e)        #socket was closed
        return False
    except Exception as e:
        print(e)
        return True
    return True

"""Reads the configuration file, validates it and sends all the icons to the deck.
This function should be called when the connection is first initiated.

Still working on it :)"""
def initialize_deck(client_socket):
    #get all images and send them to esp one by one
    btn_id = 0
    try:
        for button in CMD_DICT["buttons"]:
            if button["button_id"] != btn_id:
                raise ValueError("Missing button ids")
            file_path = button["image_path"]
            print(file_path)
            handle_upload(client_socket, file_path, DEFAULT_CLIENT_DOWNLOAD_FOLDER)
            btn_id += 1
    except ValueError as e:
        print(e)
        return False

"""Receives a request header from the client. Parses the header converting it
from network byte order (`!` format element) to host order.

Once the payload length is decoded, it attempts to retrieve the payload contents 
from the socket. Finally, it checks the command type:

If the message is a confiermation message (CFCF flag) then the request is passed to the ack queue
If the message is a macro command (MCCF flag) then the request is forwarded to the execute function
"""
def handle_request(request, client_socket):
    #parse header
    header = struct.unpack("!iiiiI", request)
    command_type = int(header[0])
    command_id = int(header[1])
    opt_arg = int(header[2])
    req_len = int(header[3])
    crc_value = int(header[4])

    try:
        print(f'REQUEST has type {command_type}, id {command_id}, opt_arg {opt_arg}, len {req_len}, CRC {hex(crc_value)}')

        #get payload contents
        req_contents = read_all(client_socket, req_len)
        readable_req_contents = req_contents.decode("utf-8")

        print(f'REQUEST_CONTENTS: {readable_req_contents}')
        #executing command associated to the button id
        if command_type == CFCF:
            ack_queue.put(readable_req_contents)
            # print(f"put {readable_req_contents} in queue")
        elif command_type == MCCF:
            #TODO: change macros to have button id in the payload
            execute_command(client_socket, CMD_DICT, command_id, opt_arg)
    except ValueError as e:
        print(e)

"""Function to be called by the reader thread. It loops indefinitely listening for 
client request headers."""
def handle_new_connection(client_socket, client_addr):
    print(f'Created new thread for client {client_addr}')
    while True:
        req = read_all(client_socket, HEADER_SIZE)

        if not req:
            client_socket.close()
            print("Client has requested disconnect")
            return None
        print(f'Client {client_addr} requested: {req}')
        handle_request(req, client_socket)

"""Function to be called by the writer thread. It will deal with listening to and 
performing user requests."""
def handle_server_send(client_socket, client_addr):
    responses = ["hey dude thanks for letting me know",
                 "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
                 "hyaimamanannanan"]

    while True:
        user_input = input(">")

        if user_input == "u":
            handle_upload(client_socket, FILENAME, DEFAULT_CLIENT_DOWNLOAD_FOLDER)
        if user_input == "f":
            initialize_deck(client_socket)
        if user_input == "m":
            msg_index = random.randint(0, len(responses) - 1)
            print(f'server cmd id = {basic_comms.server_cmd_id}')
            send_request(client_socket, INTF, basic_comms.server_cmd_id, 0, len(responses[msg_index]), responses[msg_index])
            # print(hex(binascii.crc32(responses[msg_index].encode()) & 0xffffffff))