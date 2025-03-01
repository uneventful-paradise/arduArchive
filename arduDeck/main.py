#multithreaded server : https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
#TODO:acknowledgements after each message? also maybe msg ids should be 3chars strings
#TODO: 2 queues for tasks vs peeking and taking
#TODO: make send/receive an interface

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
    print(f"SENT packet of type {cmd_type} id {cmd_id} fid {file_id} size {len(req)}\nSEND CONTENTS: " + req + "\n")
    client_socket.sendall(packet)

def handle_request(request, client_socket):
    header = struct.unpack("!iiii", request)
    command_type = int(header[0])
    command_id = int(header[1])
    file_id = int(header[2])
    req_len = int(header[3])
    print(f'REQUEST has type {command_type}, id {command_id}, fid {file_id}, len {req_len}')
    req_contents = client_socket.recv(req_len)
    # print(f'Command contents was {req_contents.decode("utf-8")}')
    print(f'REQUEST_CONTENTS: {req_contents}\n')

def handle_new_connection(client_socket, client_addr):
    print(f'Created new thread for client {client_addr}')
    index = 0
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

        responses = ["hey dude thanks for letting me know",
                     "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
                     "hyaimamanannanan"]
        # hex_msg = binascii.hexlify(msg)
        if index < 3:
            send_request(client_socket, 12, index, 55, len(responses[index]), responses[index])
            index+=1

while True:
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    thread = threading.Thread(target=handle_new_connection, args=(conn, addr))
    threads.append(thread)

    thread.start()

for thread in threads:
    thread.join()
s.close()