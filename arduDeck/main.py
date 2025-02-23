import socket
import random
import time
import struct

HOST = "0.0.0.0"
PORT = 65432
FILENAME = "test.txt"
CHUNK_SIZE = 1024
ACK_SIZE = 4

#creating socket/connection for bidirectional communication
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #binding socket to host address and port and performing a blocking wait for incoming connections

    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    with conn:
        try:
            #send random numbers to the client
            # while True:
            #     data = str(random.randint(1, 100)) + "\n"
            #     conn.sendall(data.encode())
            #     print(f"Sent: {data.strip()}")
            #     time.sleep(1)

            #opening in rb so no image character can interrupt the exchange?
            try:
                with open(FILENAME, "rb") as file_obj:
                    packet_index = 0
                    while True:
                        data = file_obj.read(CHUNK_SIZE)
                        if not data:
                            break
                        else:
                            #format: < = small endian (! for network = bigendian), integer, integer
                            packet = struct.pack("!ii", packet_index, len(data)) + data
                            print(f"sending packet of size {len(data)}:\n" + data.decode("utf-8"))
                            conn.sendall(packet)
                            ack_bytes = conn.recv(ACK_SIZE)
                            ack = struct.unpack("!i", ack_bytes)[0]
                            if int(ack) == packet_index:
                                print(f'received confirmation for packet {packet_index}\n')
                            packet_index += 1
            except IOError:
                print("Could not open or read file")
        except (BrokenPipeError, ConnectionResetError):
            print(f"Client {addr} disconnected.")
