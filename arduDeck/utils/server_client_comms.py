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
PORT = 65432

# Initialize the main connection socket. Bind and listen
# will be called on it resulting in client connection sockets.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)

#FILENAME = "media/haskell-register.log"
#FILENAME = "media/tw.txt"
#FILENAME = "media/pdfs/rtos.pdf"
# FILENAME = "media/pdfs/com.pdf"
FILENAME = "media/images/landscape.jpg"
# FILENAME = "media/images/wanda.jpg"
# FILENAME = "media/txts/haskell-register.log"
DEFAULT_CLIENT_DOWNLOAD_FOLDER = "/init_icons"


"""Opens the upload source file and sends predefined sized chunks of data to client.

The first send contains an `upload start flag` alongside the file size and file name(on the client side).
Then `file_size/CHUNK_SIZE` file contents sends follow. Finally when EOF is encountered
on the server side, an `upload end flag` is sent to the client to stop the transfer. 
"""
def handle_upload(client_socket, filename, client_location):
    logger.debug("Started upload")

    file_size = os.path.getsize(filename)
    client_filename = client_location + "/" + filename.split('/')[-1] + " " + str(file_size)
    logger.debug("writing to %s", client_filename)

    #send the upload initiating request
    req_cmd = basic_comms.server_cmd_id
    send_res = send_request(client_socket, START_DOWNLOAD, req_cmd, len(client_filename), client_filename)
    if send_res == STOP_ACTION:
        logger.ERROR("Client requested end of UPLOAD by ack flag")
        return
    try:
        file_obj = open(filename, 'rb')
        while True:
            #read a chunk of data from file
            data = file_obj.read(CHUNK_SIZE)
            req_cmd = basic_comms.server_cmd_id

            if not data:
                #send transfer ending request
                data = "EOF"
                send_res = send_request(client_socket, END_DOWNLOAD, req_cmd, len(data), data)
                if send_res == SUCCESSFUL_CONF:
                    logger.debug("EOF sent successfully. Upload ended.")
                    break
            else:
                #send the following file contents request
                send_res = send_request(client_socket, FILE_TRANSFER, req_cmd, len(data), data)
            #stop transfer in case of error
            if send_res == STOP_ACTION:
                logger.ERROR("Received request to end UPLOAD by ack flag")
                break

    except IOError as e:
        logger.error("Could not open or read file", exc_info=True)

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
        logger.debug("Action has command_id: %s", action["command_id"])
        if action["command_id"] in ACT_DICT.keys():
            logger.debug("Action has arguments: %s", action["command_args"])
            ACT_DICT[action["command_id"]](client_socket, command_id, *action["command_args"])
        else:
            logger.warning("Invalid command id in dictionary")

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
            logger.debug(file_path)

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
    header = struct.unpack("!IIII", request)
    command_type = int(header[0])
    command_id = int(header[1])
    req_len = int(header[2])
    crc_value = int(header[3])

    try:
        logger.debug("Request has type %d, id %d, len %d, CRC %s", command_type, command_id, req_len, hex(crc_value))
        #get payload contents
        req_contents = read_all(client_socket, req_len)
        readable_req_contents = req_contents.decode("utf-8")

        logger.debug("REQUEST CONTENTS: %s\n", readable_req_contents)

        #executing command associated to the button id
        if command_type == CONFIRMATION_FLAG:
            ack_queue.put(readable_req_contents)
            # print(f"put {readable_req_contents} in queue")
        elif command_type == MACRO_COMMAND:
            execute_command(client_socket, CMD_DICT, command_id, int(readable_req_contents))
    except ValueError as e:
        logger.error("Handle request exception: %s", e, exc_info=True)

"""Function to be called by the reader thread. It loops indefinitely listening for 
client request headers."""
def handle_new_connection(client_socket, client_addr):
    logger.debug("Created new thread of client %s", client_addr)
    while True:
        req = read_all(client_socket, HEADER_SIZE)

        if not req:
            client_socket.close()
            logger.debug("Client disconnected")
            return None
        # logger.debug("Client %s requested %s", client_addr, req)
        handle_request(req, client_socket)

"""Function to be called by the writer thread. It will deal with listening to and 
performing user requests."""
def handle_server_send(client_socket, client_addr):
    responses = ["hey dude thanks for letting me know",
                 "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
                 "hyaimamanannanan",
                 "buna ziuaaa"]

    while True:
        user_input = input(">")

        if user_input == "u":
            handle_upload(client_socket, FILENAME, DEFAULT_CLIENT_DOWNLOAD_FOLDER)
        if user_input == "f":
            initialize_deck(client_socket)
        if user_input == "m":
            msg_index = random.randint(0, len(responses) - 1)
            # print(f'server cmd id = {basic_comms.server_cmd_id}')
            send_result = send_request(client_socket, INITIALIZE_ROUTINE, basic_comms.server_cmd_id
                         , len(responses[msg_index]), responses[msg_index])
            if send_result != basic_comms.SUCCESSFUL_CONF:
                logger.error("Message send failed")
        if user_input == "e":
            client_socket.close()
            s.close()