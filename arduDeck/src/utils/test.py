import serial
import struct

# open serial port (adjust port name and baud to match ESP32)
ser = serial.Serial('COM5', 115200, timeout=1)

try:
    while True:
        # read exactly 4 bytes for the length header
        header = ser.read(4)
        if len(header) < 4:
            continue  # timeout or incomplete, retry
        
        # unpack uint32 little‑endian
        msg_len = struct.unpack('<I', header)[0]
        print(f"Incoming message length: {msg_len}")

        # now read the message payload
        payload = ser.read(msg_len)
        if len(payload) < msg_len:
            print("Warning: incomplete payload")
            continue
        
        # decode and use
        text = payload.decode('utf-8', errors='replace')
        print("Received:", text)

except KeyboardInterrupt:
    pass
finally:
    ser.close()
