import socket
import struct
import binascii
import logging
import datetime
import os
import sys
import queue

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
log_filename = datetime.datetime.now().strftime("logs/log_%Y-%m-%d_%H-%M-%S.log")

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s',
    datefmt="%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
CHUNK_SIZE = 2048
HEADER_SIZE = 16
MAX_RETRIES = 10

server_cmd_id = 0
"""Predefined constant values used as flags in the protocol"""
MACRO_COMMAND = 0
START_DOWNLOAD = 1
FILE_TRANSFER = 2
END_DOWNLOAD = 3
INITIALIZE_ROUTINE = 4
CONFIRMATION_FLAG = 5
LOG_MESSAGE = 6

"""Acknowledgement flags"""
SUCCESSFUL_CONF = 1
INCORRECT_VALUE = -1
STOP_ACTION = -2

"""Loop to send all data to server.

TCP might not send an entire message at once.
the function makes sure to send the entire chunk of information
by looping until there is nothing left to send"""
def read_all(client_socket, req_len):
    if req_len > CHUNK_SIZE:
        raise ValueError("Payload length exceeds chunk size")
    #TODO: use byte arrays instead of lists for speed
    chunks = []
    bytes_received = 0
    try:
        while bytes_received < req_len:
            chunk = client_socket.recv(min(CHUNK_SIZE, req_len - bytes_received))
            if not chunk:
                logger.error("socket connection broken")
                break
            chunks.append(chunk)
            bytes_received += len(chunk)
    except socket.error as e:
        logger.error("read_all exception: %s", e, exc_info=True)

    return b''.join(chunks)

"""Similar to read_all. Loop until all data has been sent"""
def write_all(client_socket, data):
    try:
        total_sent = 0
        while total_sent < len(data):
            sent = client_socket.send(data[total_sent:])
            if not sent:
                logger.error("socket connection broken")
                break
            total_sent += sent
    except socket.error as e:
        logger.error("write_all exception: %s", e, exc_info=True)


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
        logger.warning("ACK got unexpected value %d while expecting %d/%d\n", ack, req_id, server_cmd_id)
        return False

"""Compose a protocol compliant message and send it to the client.

Compute the CRC32 value of the payload and retrieve the passed header fields.
The function packs the header fields using the network order (big endian) 
format (`!` character). It then appends the payload and sends the message.

The server message id is calculated based on the message id argument.
This is a product of the file transfer resend/confirmation operation. 
In the context of multiple connections this will require a synchronized variable
or an id that increments regardless of the acknowledgement status.
"""
def send_request(client_socket, cmd_type, cmd_id, req_len, req):
    global server_cmd_id
    #format: < = small endian (! for network = big endian)
    if req_len > CHUNK_SIZE:
        logger.warning("send %d exceeded size limit", req_len)
        raise ValueError("Payload length exceeds chunk size")

    enc_type = "hex"
    if isinstance(req, str):
        req = req.encode('utf-8')
        enc_type = "str"

    crc_value = binascii.crc32(req) & 0xffffffff
    packet = struct.pack("!IIII", cmd_type, cmd_id, req_len, crc_value) + req

    if enc_type == "str":
        logger.debug("SENT packet of type %d, id %d, size %d, CRC %s\n%s\n",
                    cmd_type, cmd_id, len(req), hex(crc_value), req.decode('utf-8'))
    else:
        logger.debug("SENT packet of type %d, id %d, size %d, CRC %s\n%s\n",
                    cmd_type, cmd_id, len(req), hex(crc_value), req.hex())

    write_all(client_socket, packet)
    # server_cmd_id+=1 TODO: how should the server message id be incremented in the context of multiple client connections
    result = check_ack(cmd_id)
    retry_counter = 0
    #resend packet until successful confirmation, error or exceeded retry counter
    while result == INCORRECT_VALUE and retry_counter < MAX_RETRIES:
        write_all(client_socket, packet)
        result = check_ack(cmd_id)
        retry_counter += 1

    if retry_counter == MAX_RETRIES and result == INCORRECT_VALUE:
        logger.error("Packet reached MAX_RETRIES. Ending upload")
        result = STOP_ACTION

    server_cmd_id = cmd_id + 1
    return result
