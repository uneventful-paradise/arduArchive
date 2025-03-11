import socket
import struct

CHUNK_SIZE = 2048
HEADER_SIZE = 16

server_cmd_id = 0

MCCF = 0    #MACRO COMMAND FLAG
SDCF = 1    #START DOWNLOAD COMMAND FLAG
FTCF = 2    #FILE TRANSFER COMMAND FLAG
EDCF = 3    #END OF DOWNLOAD COMMAND FLAG
INTF = 4    #INITIALIZATION FLAG (start of routine)
CFCF = 5    #CONFIRMATION COMMAND FLAG

#TCP might not send an entire message at once.
#the function makes sure to send the entire chunk of information
#by looping until there is nothing left to send
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
                print("socket connection broken")
                break
            chunks.append(chunk)
            bytes_received += len(chunk)
    except socket.error as e:
        print(e)

    return b''.join(chunks)

#Similar to read_all. Loop until all data has been sent
def write_all(client_socket, data):
    try:
        total_sent = 0
        while total_sent < len(data):
            sent = client_socket.send(data[total_sent:])
            if not sent:
                print("socket connection broken")
                break
            total_sent += sent
    except socket.error as e:
        print(e)

def send_request(client_socket, cmd_type, cmd_id, opt_arg, req_len, req):
    global server_cmd_id
    #format: < = small endian (! for network = big endian)
    if req_len > CHUNK_SIZE:
        print(f"send {cmd_id} exceeded size limit")
        raise ValueError("Payload length exceeds chunk size")

    enc_type = "hex"
    if isinstance(req, str):
        req = req.encode('utf-8')
        enc_type = "str"
    packet = struct.pack("!iiii", cmd_type, cmd_id, opt_arg, req_len) + req

    if enc_type == "str":
        print(f"SENT packet of type {cmd_type} id {cmd_id} opt_arg {opt_arg} size {len(req)}\nSEND CONTENTS: " + req.decode() + "\n")
    else:
        print(f"SENT packet of type {cmd_type} id {cmd_id} opt_arg {opt_arg} size {len(req)}\nSEND CONTENTS: " + req.hex() + "\n")

    write_all(client_socket, packet)
    server_cmd_id+=1
    # client_socket.sendall(packet)
