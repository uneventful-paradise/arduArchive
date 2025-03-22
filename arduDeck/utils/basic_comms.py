import socket
import struct
import binascii
import logging
import datetime
import os
import sys

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
log_filename = datetime.datetime.now().strftime("logs/log_%Y-%m-%d_%H-%M-%S.log")

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)  # Optional: also print logs to console
    ]
)
CHUNK_SIZE = 2048
HEADER_SIZE = 20

server_cmd_id = 0

MCCF = 0    #MACRO COMMAND FLAG
SDCF = 1    #START DOWNLOAD COMMAND FLAG
FTCF = 2    #FILE TRANSFER COMMAND FLAG
EDCF = 3    #END OF DOWNLOAD COMMAND FLAG
INTF = 4    #INITIALIZATION FLAG (start of routine)
CFCF = 5    #CONFIRMATION COMMAND FLAG
LGCF = 6    #LOG MESSAGE COMMAND FLAG

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

"""Compose a protocol compliant message and send it to the client.

Compute the CRC32 value of the payload and retrieve the passed header fields.
The function packs the header fields using the network order (big endian) 
format (`!` character). It then appends the payload and sends the message.

The server message id is calculated based on the message id argument.
This is a product of the file transfer resend/confirmation operation. 
In the context of multiple connections this will require a synchronized variable
or an id that increments regardless of the acknowledgement status.
"""
def send_request(client_socket, cmd_type, cmd_id, opt_arg, req_len, req):
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
    packet = struct.pack("!iiiiI", cmd_type, cmd_id, opt_arg, req_len, crc_value) + req

    if enc_type == "str":
        logger.debug("SENT packet of type %s id: %s opt_arg: %d size: %d CRC: %s\n%s\n",
                    cmd_type, cmd_id, opt_arg, len(req), hex(crc_value), req.decode('utf-8'))
    else:
        logger.debug("SENT packet of type %s id: %s opt_arg: %d size: %d CRC: %s\n%s\n",
                    cmd_type, cmd_id, opt_arg, len(req), hex(crc_value), req.hex())

    write_all(client_socket, packet)
    # server_cmd_id+=1 TODO: how should the server message id be incremented in the context of multiple client connections
    server_cmd_id = cmd_id + 1
    # print(f"incrementing srv_id = {server_cmd_id}")
