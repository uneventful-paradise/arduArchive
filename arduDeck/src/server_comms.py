import random
from src import basic_comms
from utils.execute_funcs import *
from utils.btn_funcs import *
from client_model.base_client import BaseClient
import socket

#FILENAME = "media/haskell-register.log"
#FILENAME = "media/tw.txt"
# FILENAME = "media/pdfs/rtos.pdf"
# FILENAME = "media/pdfs/com.pdf"
# FILENAME = "media/images/landscape.jpg"
FILENAME = "media/images/wanda2.jpg"
# FILENAME = "media/txts/haskell-register.log"
# FILENAME = "testing/long_ipsum.txt"
DEFAULT_CLIENT_DOWNLOAD_FOLDER = "/init_icons"

request_queue = queue.Queue()

"""Executes the action associated with the id of a pressed button.
It checks the existence of the requested button id then calls the associated action
with the proper arguments.

Actions are functions mapped to an action name field in the config of every button.
The arguments are also defined within the button configuration."""
def execute_command(current_client: BaseClient, command_id: int, request_contents: any):
    # print(ACT_DICT.keys())
    #check for button existence and validity
    with button_lock:
        if not any(button["button_id"] == request_contents for button in BUTTON_LIST):
            raise ValueError("Invalid command id")

        #get button actions
        actions = []
        for button in BUTTON_LIST:
            if button["button_id"] == request_contents:
                actions = button["actions"]
                break

    #get action arguments and execute the action
    for action in actions:
        logger.debug("Action has command_id: %s", action["command_id"])
        if action["command_id"] in ACT_DICT.keys():
            logger.debug("Action has arguments: %s", action["command_args"])
            ACT_DICT[action["command_id"]](current_client, command_id, *action["command_args"])
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

"""Receives a request header from the client. Parses the header converting it
from network byte order (`!` format element) to host order.

Once the payload length is decoded, it attempts to retrieve the payload contents 
from the socket. Finally, it checks the command type:

If the message is a confirmation message (CFCF flag) then the request is passed to the ack queue
If the message is a macro command (MCCF flag) then the request is forwarded to the execute function
"""
def handle_request():
    while True:
        pd = request_queue.get()
        current_client = get_client()
        logger.debug("Request has type %d, id %d, len %d, CRC %s, contents: %s\n",
                     pd.header_data.command_type,
                     pd.header_data.command_id,
                     pd.header_data.length,
                     hex(pd.header_data.crc_value),
                     pd.contents)
        # executing command associated to the button id
        if pd.header_data.command_type == MACRO_COMMAND:
            try:
                execute_command(current_client, pd.header_data.command_id, int(pd.contents))
            except ValueError as e:
                logger.exception(e)
            except Exception as e:
                logger.exception(e)

def receive_request():
    while True:
        current_client = get_client()
        try:
            # data = client.read_all(HEADER_SIZE)
            # logger.debug(data)
            # continue
            request = current_client.read_all(HEADER_SIZE)

            if not request:
                logger.error("read 0")
                current_client.close()
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
            req_contents = current_client.read_all(header_data.length)
            readable_req_contents = req_contents.decode("utf-8")

            logger.debug("REQUEST CONTENTS: %s\n", readable_req_contents)
            package_data = PackageData(header_data, readable_req_contents)

            if header_data.command_type == CONFIRMATION_FLAG:
                ack_queue.put(package_data.contents)
                logger.debug(f"put {readable_req_contents} in queue")
            elif header_data.command_type == CLIENT_SWAP:
                logger.warning("Received request to swap client")
                send_conf(current_client, header_data.command_id)
                swap_client()
            else:
                logger.debug(f"put a pd in queue")
                request_queue.put(package_data)


        except ValueError as e:
            logger.error("Handle request exception: %s", e, exc_info=True)

#TODO: ADD QUEUE FOR SENDING!!
"""Function to be called by the writer thread. It will deal with listening to and 
performing user requests."""
def handle_server_send():
    responses = ["hey dude thanks for letting me know",
                 "Lorem Ipsum is simply dummy text of the printing and typesetting industry. ",
                 "hyaimamanannanan",
                 "buna ziuaaa"]

    while True:
        user_input = input(">")
        current_client = get_client()

        if user_input == "u":
            handle_upload(current_client, FILENAME, DEFAULT_CLIENT_DOWNLOAD_FOLDER)
            redraw_contents="redraw"
            sid = basic_comms.server_cmd_id.inc()
            pd = create_packet(command_type=REDRAW_COMMAND,
                               command_id=sid,
                               length=len(redraw_contents),
                               crc_value=0,
                               contents=redraw_contents)
            send_result = send_request(current_client, pd)
            if send_result != basic_comms.SUCCESSFUL_CONF:
                logger.error("Message send failed")

        elif user_input == "m":
            msg_index = random.randint(0, len(responses) - 1)
            sid = basic_comms.server_cmd_id.inc()
            logger.debug("sid is %d", sid)
            pd = create_packet(command_type=INITIALIZE_ROUTINE,
                               command_id=sid,
                               length=len(responses[msg_index]),
                               crc_value=0,
                               contents=responses[msg_index])

            # print(f'server cmd id = {basic_comms.server_cmd_id.value}')
            send_result = send_request(current_client, pd)

            if send_result != basic_comms.SUCCESSFUL_CONF:
                logger.error("Message send failed")

        elif user_input == "e":
            current_client.close()