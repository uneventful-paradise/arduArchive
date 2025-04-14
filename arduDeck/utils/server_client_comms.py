import random
import time
import basic_comms
from utils.execute_funcs import *
from utils.btn_funcs import *

# Load current key-action configuration into a global dictionary
# to be used by the action executing functions


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

request_queue = queue.Queue()

"""Executes the action associated with the id of a pressed button.
It checks the existence of the requested button id then calls the associated action
with the proper arguments.

Actions are functions mapped to an action name field in the config of every button.
The arguments are also defined within the button configuration."""
def execute_command(client_socket, command_id, request_contents):
    # print(ACT_DICT.keys())
    #check for button existence and validity

    if not any(button["button_id"] == request_contents for button in CMD_DICT):
        raise ValueError("Invalid command id")

    #get button actions
    actions = []
    for button in CMD_DICT:
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

def initialize_deck(client_socket):
    #get all images and send them to esp one by one
    for button in CMD_DICT:

        file_path = button["image_path"]
        client_filename = "{btn_index}.jpg".format(btn_index=button["button_id"])
        logger.debug(f"sending {file_path}")

        handle_upload(client_socket, file_path, DEFAULT_CLIENT_DOWNLOAD_FOLDER, client_filename)

        time.sleep(1)

"""Receives a request header from the client. Parses the header converting it
from network byte order (`!` format element) to host order.

Once the payload length is decoded, it attempts to retrieve the payload contents 
from the socket. Finally, it checks the command type:

If the message is a confirmation message (CFCF flag) then the request is passed to the ack queue
If the message is a macro command (MCCF flag) then the request is forwarded to the execute function
"""
def handle_request(client_socket, addr):
    while True:
        pd = request_queue.get()
        logger.debug("Request has type %d, id %d, len %d, CRC %s, contents: %s\n",
                     pd.header_data.command_type,
                     pd.header_data.command_id,
                     pd.header_data.length,
                     hex(pd.header_data.crc_value),
                     pd.contents)
        # executing command associated to the button id
        if pd.header_data.command_type == MACRO_COMMAND:
            try:
                execute_command(client_socket, pd.header_data.command_id, int(pd.contents))
            except ValueError as e:
                logger.exception(e)
            except Exception as e:
                logger.exception(e)
"""Function to be called by the reader thread. It loops indefinitely listening for 
client request headers."""
def receive_request(client_socket, client_addr):
    logger.debug("Created new thread of client %s", client_addr)
    while True:
        try:
            request = read_all(client_socket, HEADER_SIZE)

            if not request:
                client_socket.close()
                logger.error("Client disconnected")
                return None
            # logger.debug("Client %s requested %s", client_addr, req)

            # parse header
            header = struct.unpack("!IIII", request)
            header_data = HeaderData(int(header[0]), int(header[1]), int(header[2]), int(header[3]))


            logger.debug("Request has type %d, id %d, len %d, CRC %s",
                         header_data.command_type,
                         header_data.command_id,
                         header_data.length,
                         hex(header_data.crc_value))

            # get payload contents
            req_contents = read_all(client_socket, header_data.length)
            readable_req_contents = req_contents.decode("utf-8")

            logger.debug("REQUEST CONTENTS: %s\n", readable_req_contents)
            package_data = PackageData(header_data, readable_req_contents)

            if header_data.command_type == CONFIRMATION_FLAG:
                ack_queue.put(package_data.contents)
                logger.debug(f"put {readable_req_contents} in queue")
            else:
                logger.debug(f"put a pd in queue")
                request_queue.put(package_data)


        except ValueError as e:
            logger.error("Handle request exception: %s", e, exc_info=True)


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
        elif user_input == "i":
            initialize_deck(client_socket)
        elif user_input == "m":
            msg_index = random.randint(0, len(responses) - 1)
            # print(f'server cmd id = {basic_comms.server_cmd_id}')
            send_result = send_request(client_socket, INITIALIZE_ROUTINE, basic_comms.server_cmd_id
                         , len(responses[msg_index]), responses[msg_index])
            if send_result != basic_comms.SUCCESSFUL_CONF:
                logger.error("Message send failed")
        elif user_input == "add1":
            try:
                add_button(
                    46,
                    [("START_PROCESS", ["C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE"]),
                     ("START_URL", ["https://github.com/uneventful-paradise/arduArchive/tree/main"])],
                    "media/icons/obs.jpg",
                    CMD_DICT
                )

                send_new_config(client_socket, "/configs", basic_comms.server_cmd_id)
                write_updates()

            except ValueError as e:
                logger.error("Handle request exception: %s", e, exc_info=True)
        elif user_input == "add2":
            try:
                update_button(5,
                              6,
                              [("HARD_KEY_PRESS", ["pLa revedere frate"])],
                              "media/icons/vscode.jpg")
                send_new_config(client_socket, "/configs", basic_comms.server_cmd_id)
                write_updates()
            except ValueError as e:
                logger.exception(e)
        elif user_input == "add3":
            try:
                delete_button(10)
                send_new_config(client_socket, "/configs", basic_comms.server_cmd_id)
                write_updates()
            except ValueError as e:
                logger.exception(e)
        elif user_input == "add4":
            try:
                add_button(
                    15,
                    [("SOFT_KEY_PRESS", ["dKEY_VOLUME_MUTE+w500+uKEY_VOLUME_MUTE+dKEY_LWIN+dKEY_SHIFT+dKEY_C+r"])],
                    "media/icons/word.jpg",
                    CMD_DICT
                )

                send_new_config(client_socket, "/configs", basic_comms.server_cmd_id)
                write_updates()

            except ValueError as e:
                logger.error("Handle request exception: %s", e, exc_info=True)
        elif user_input == "e":
            client_socket.close()
            s.close()