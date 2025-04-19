import struct
import binascii
import queue

from client_model.base_client import BaseClient
import threading

from src.client_model.network_client import NetworkClient
from utils.data_format import HeaderData, PackageData
from server_params import *

server_cmd_id = 0
client_lock = threading.Lock()

client: BaseClient = None
def read_all(client: BaseClient, req_len: int) -> bytes:
    with client_lock:
        return client.read_all(req_len)

def write_all(client: BaseClient, data: bytes):
    with client_lock:
        client.write_all(data)

def create_packet(command_type: int, command_id: int, length:int, crc_value: int, contents: any) -> PackageData:
    hd = HeaderData(command_type=command_type, command_id=command_id, length=length, crc_value=crc_value)
    pd = PackageData(header_data=hd, contents=contents)
    return pd

def set_client(new_client: BaseClient):
    global client
    with client_lock:
        if client is not None:
            client.close()
            client = None
        client = new_client
    logger.debug("Successfully swapped client")

def get_client() -> BaseClient:
    with client_lock:
        return client

#lock?
def get_server_cmd_id():
    return server_cmd_id

def set_server_cmd_id(new_server_cmd_id: int) -> None:
    global server_cmd_id
    server_cmd_id = new_server_cmd_id

"""In the context of data transfers the server sends a packet then
waits for confirmation before sending the next one. The queue is used to
store incoming confirmations. Thus, the client thread blocks performing a
get operation while waiting for a packet's acknowledgment."""
ack_queue = queue.Queue()

"""The acknowledgement process is defined as follows:

The client receives a server request identified by the cmd_id field
It checks the message against the provided and self-computed CRC32 values
then it responds with a verdict:

The value of the acknowledgement is the initial server cmd_id if the check 
succeeded `INCORRECT_VALUE` in case of need of a resend (e.g. corrupted packet
and `STOP_ACTION` in case of a client_sided error that means a continuous transfer
must be stopped.
"""
#TODO: add timeout in case client never sends acknowledgement
def check_ack(req_id):
    ack = ack_queue.get()
    if int(ack) == req_id:
        logger.debug("ack successful for req_id %d\n", req_id)
        return SUCCESSFUL_CONF
    elif int(ack) == INCORRECT_VALUE:
        logger.warning("ACK process failed! Requesting resend\n")
        return INCORRECT_VALUE
    elif int(ack) == STOP_ACTION:
        return STOP_ACTION
    else:
        logger.warning("ACK got unexpected value %d while expecting %d/%d\n", int(ack), req_id, server_cmd_id)
        return STOP_ACTION

"""Compose a protocol compliant message and send it to the client.

Compute the CRC32 value of the payload and retrieve the passed header fields.
The function packs the header fields using the network order (big endian) 
format (`!` character). It then appends the payload and sends the message.

The server message id is calculated based on the message id argument.
This is a product of the file transfer resend/confirmation operation. 
In the context of multiple connections this will require a synchronized variable
or an id that increments regardless of the acknowledgement status.
"""

def send_request(client: BaseClient, pd: PackageData):
    global server_cmd_id
    req_len = pd.header_data.length
    req_contents = pd.contents
    #format: < = small endian (! for network = big endian)
    if req_len > CHUNK_SIZE:
        logger.warning("send %d exceeded size limit", req_len)
        raise ValueError("Payload length exceeds chunk size")

    enc_type = "hex"
    if isinstance(req_contents, str):
        req_contents = req_contents.encode('utf-8')
        enc_type = "str"

    crc_value = binascii.crc32(req_contents) & 0xffffffff
    pd.header_data.crc_value = crc_value
    packet = struct.pack("!IIII",
                         pd.header_data.command_type,
                         pd.header_data.command_id,
                         pd.header_data.length,
                         pd.header_data.crc_value) + req_contents

    if enc_type == "str":
        logger.debug("SENT packet of type %d, id %d, size %d, CRC %s\n%s\n",
                     pd.header_data.command_type,
                     pd.header_data.command_id,
                     len(req_contents),
                     hex(pd.header_data.crc_value),
                     req_contents.decode('utf-8'))
    else:
        logger.debug("SENT packet of type %d, id %d, size %d, CRC %s\n%s\n",
                    pd.header_data.command_type,
                    pd.header_data.command_id,
                    len(req_contents),
                    hex(pd.header_data.crc_value),
                    req_contents.hex())

    client.write_all(packet)
    # server_cmd_id+=1
    result = check_ack(pd.header_data.command_id)
    retry_counter = 0

    #resend packet until successful confirmation, error or exceeded retry counter
    while result == INCORRECT_VALUE and retry_counter < MAX_RETRIES:
        client.write_all(packet)
        result = check_ack(pd.header_data.command_id)
        retry_counter += 1

    if retry_counter == MAX_RETRIES and result == INCORRECT_VALUE:
        logger.error("Packet reached MAX_RETRIES. Ending upload")
        result = STOP_ACTION

    server_cmd_id = pd.header_data.command_id + 1
    return result


"""Opens the upload source file and sends predefined sized chunks of data to client.

The first send contains an `upload start flag` alongside the file size and file name(on the client side).
Then `file_size/CHUNK_SIZE` file contents sends follow. Finally when EOF is encountered
on the server side, an `upload end flag` is sent to the client to stop the transfer. 
"""
def handle_upload(client: BaseClient, filename: str, client_location: str, client_fname: str = ""):
    logger.debug("Started upload")
    #check for existence of file before starting transfer

    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # filename = os.path.join(base_dir, filename)
    if isinstance(client, NetworkClient):
        print("Salut sunt network client")

    try:
        if not os.path.exists(filename):
            raise FileNotFoundError
    except FileNotFoundError as e:
        logger.exception(e)

    file_size = os.path.getsize(filename)

    if client_fname == "":
        client_filename = client_location + "/" + filename.split('/')[-1] + " " + str(file_size)
    else:
        client_filename = client_location + "/" + client_fname + " " + str(file_size)

    logger.debug("writing to %s", client_filename)

    #send the upload initiating request
    req_cmd = server_cmd_id
    pd = create_packet(command_type=START_DOWNLOAD,
                       command_id=req_cmd,
                       length=len(client_filename),
                       crc_value=0,
                       contents=client_filename)

    send_res = send_request(client, pd)
    if send_res == STOP_ACTION:
        logger.error("Client requested end of UPLOAD by ack flag")
        return
    try:
        file_obj = open(filename, 'rb')
        while True:
            #read a chunk of data from file
            data = file_obj.read(CHUNK_SIZE)
            req_cmd = server_cmd_id

            if not data:
                #send transfer ending request
                data = "EOF"
                pd = create_packet(command_type=END_DOWNLOAD,
                                   command_id=req_cmd,
                                   length=len(data),
                                   crc_value=0,
                                   contents=data)

                send_res = send_request(client, pd)
                if send_res == SUCCESSFUL_CONF:
                    logger.debug("EOF sent successfully. Upload ended.")
                    file_obj.close()
                    break
            else:
                #send the following file contents request
                pd = create_packet(command_type=FILE_TRANSFER,
                                   command_id=req_cmd,
                                   length=len(data),
                                   crc_value=0,
                                   contents=data)
                send_res = send_request(client, pd)
            #stop transfer in case of error
            if send_res == STOP_ACTION:
                logger.error("Received request to end UPLOAD by ack flag")
                break

    except IOError as e:
        logger.exception(e)