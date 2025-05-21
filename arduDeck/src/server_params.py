import os
import sys
import logging
import datetime

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
log_filename = datetime.datetime.now().strftime("logs/log_%Y-%m-%d_%H-%M-%S.log")

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(funcName)s] [%(filename)s:%(lineno)d] %(message)s',
    datefmt="%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
CHUNK_SIZE = 2048
HEADER_SIZE = 16
MAX_RETRIES = 10


"""Predefined constant values used as flags in the protocol"""
MACRO_COMMAND = 0
START_DOWNLOAD = 1
FILE_TRANSFER = 2
END_DOWNLOAD = 3
INITIALIZE_ROUTINE = 4
CONFIRMATION_FLAG = 5
REDRAW_COMMAND = 6
CONNECTION_CHECK = 7
CLIENT_SWAP = 8

"""Acknowledgement flags"""
SUCCESSFUL_CONF = 1
INCORRECT_VALUE = -1
STOP_ACTION = -2

HOST = "0.0.0.0"
PORT = 65432

MAX_BUTTONS = 64
MAX_FOLDER_BUTTONS = 15