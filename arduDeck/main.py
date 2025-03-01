#multithreaded server : https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
import binascii
import socket
import struct
import threading

MAX_CLIENTS = 5
threads = []
HOST = "0.0.0.0"
PORT = 65432
FILENAME = "test_img.jpg"
CHUNK_SIZE = 1024
HEADER_SIZE = 16
#download/upload        command_code = 1(int)| command_id = cid(int)| file_id = fid(int) | message_length = len(int)| contents = ...(byte array)
#macro_command          command_code = 0(int)| command_id = cid(int)| __________________ | message_length = len(int)| filename = ...(char array)
ACK_SIZE = 4

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

def recv_all(sock, num_bytes):
    buf = b""
    while len(buf) < num_bytes:
        chunk = sock.recv(num_bytes - len(buf))
        if not chunk:
            # Connection closed or error occurred
            break
        buf += chunk
    return buf

#what about confirmations?
def send_request(client_socket, cmd_type, cmd_id, file_id, req_len, req):
    #format: < = small endian (! for network = bigendian)
    packet = struct.pack("!iiii", cmd_type, cmd_id, file_id, req_len) + str.encode(req)
    # print(f"sending packet of size {req_len}:\n" + req.decode("utf-8"))
    print(f"sending packet of size {len(req)}:" + req)
    client_socket.sendall(packet)

def handle_request(request, client_socket):
    header = struct.unpack("!iiii", request)
    command_type = int(header[0])
    command_id = int(header[1])
    file_id = int(header[2])
    req_len = int(header[3])
    print(f'Command has type {command_type}, id {command_id}, fid {file_id}, len {req_len}')
    req_contents = client_socket.recv(req_len)
    # print(f'Command contents was {req_contents.decode("utf-8")}')
    print(f'Command contents was {req_contents}')

def handle_new_connection(client_socket, client_addr):
    print(f'Created new thread for client {client_addr}')
    while True:
        req = client_socket.recv(HEADER_SIZE)
        # req = recv_all(client_socket, HEADER_SIZE)
        if not req:
            client_socket.close()
            print("Client has requested disconnect")
            return None
        print(f'Client {client_addr} requested: {req}')
        #make this an interface
        handle_request(req, client_socket)

        msg = "salut inapoi fratelor 25"
        # hex_msg = binascii.hexlify(msg)
        send_request(client_socket, 12, 22, 55, len(msg), msg)

while True:
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    thread = threading.Thread(target=handle_new_connection, args=(conn, addr))
    threads.append(thread)

    thread.start()

for thread in threads:
    thread.join()
s.close()

# #creating socket/connection for bidirectional communication
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     #binding socket to host address and port and performing a blocking wait for incoming connections
#
#     s.bind((HOST, PORT))
#     s.listen()
#     conn, addr = s.accept()
#     print(f"Connected by {addr}")
#     with conn:
#         try:
#             #opening in read binary mode because we are (eventually) sending an image.
#             try:
#                 with open(FILENAME, "rb") as file_obj:
#                     packet_index = 0
#                     while True:
#                         #read data in chunks
#                         data = file_obj.read(CHUNK_SIZE)
#                         if not data:
#                             #signaling end of file on the server side
#                             eof_packet = struct.pack("!ii", packet_index, 0)
#                             conn.sendall(eof_packet)
#                             break
#                         else:
#                             #format: < = small endian (! for network = bigendian), integer, integer
#                             packet = struct.pack("!ii", packet_index, len(data)) + data
#                             # print(f"sending packet of size {len(data)}:\n" + data.decode("utf-8"))
#                             print(f"sending packet of size {len(data)}:\n" + data.hex())
#                             conn.sendall(packet)
#
#                             #wait for the acknowledgement flag
#                             ack_bytes = conn.recv(ACK_SIZE)
#                             ack = struct.unpack("!i", ack_bytes)[0]
#                             if int(ack) == packet_index:
#                                 print(f'received confirmation for packet {packet_index}\n')
#                             packet_index += 1
#             except IOError:
#                 print("Could not open or read file")
#         except (BrokenPipeError, ConnectionResetError):
#             print(f"Client {addr} disconnected.")
