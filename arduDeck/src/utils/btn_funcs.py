import json
import time

from src.basic_comms import logger, handle_upload, send_request, REDRAW_COMMAND, SUCCESSFUL_CONF, create_packet, server_cmd_id
from src.client_model.base_client import BaseClient
from threading import Lock

button_lock = Lock()

CLIENT_CONFIG_PATH = "config/client_config.txt"
IMG_TRACKER_PATH = "config/tracked_img.json"
with open(IMG_TRACKER_PATH, "r") as f:
    tracked_images = json.load(f)

FOLDER_CONFIG_PATH = "config/folder_configs"
CONFIG_FILE = "config/btn_config.json"
with open(CONFIG_FILE, "r") as f:
    BUTTON_LIST = json.load(f)

def load_folder_buttons(folder_id : int):
    btn_list = []
    folder_path = f"config/folder_configs/{folder_id}.json"
    try:
        with open(folder_path, "r") as f:
            btn_list = json.load(f)
            logger.debug("Loaded file %s", folder_path)
    except FileNotFoundError as e:
        logger.error("File %s not found", folder_path)
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

    return btn_list

#TODO: remove btn lock
def build_client_config_file(client_dir : str, config_path : str, btn_list: list):
    file_contents = ""

    for button in btn_list:
        line = client_dir + "/" + button["image_path"].split('/')[-1] + " " + str(button["button_id"]) + " " + str(button["folder_flag"])
        if file_contents == "":
            file_contents += line
        else:
            file_contents += "\n" + line

    logger.debug("building config for %s. contents:\n%s", config_path, file_contents)

    try:
        with open(CLIENT_CONFIG_PATH, "w") as f:
            f.write(file_contents)
    except FileNotFoundError as e:
        logger.error("File not found")
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

def send_new_config(client : BaseClient, client_dir : str, cmd_id : int, change_log : set):
    for file in change_log:

        try:
            with open(file, "r") as f:
                btn_list = json.load(f)
        except FileNotFoundError as e:
            logger.error("File not found")
        except Exception as e:
            logger.exception(e)

        for button in btn_list:
            # logger.debug(f"Checking for image {button['image_path']}")
            exists = False
            for image in tracked_images:
                if button["image_path"] == image["image_path"]:
                    exists = True
            if not exists:
                logger.debug(f"Image {button['image_path']} not on client. sending and indexing it")
                tracked_images.append({"image_path": button["image_path"]})
                handle_upload(client, button["image_path"], client_dir)
                time.sleep(0.5)

        build_client_config_file(client_dir, file, btn_list)
        #eliminate folder name and change extension
        client_filename = file.split('/')[-1].split('.')[0] + '.txt'
        logger.debug(f"Will send {client_filename}")
        handle_upload(client, CLIENT_CONFIG_PATH, client_dir, client_filename)

    write_updates()

    logger.debug("Sending request for redraw")
    req_contents = "redraw after upload"
    pd = create_packet(command_type=REDRAW_COMMAND,
                       command_id=cmd_id,
                       length=len(req_contents),
                       crc_value=0,
                       contents=req_contents)

    send_result = send_request(client, pd)
    if send_result == SUCCESSFUL_CONF:
        logger.debug("Success")
    else:
        logger.error("Unexpected response")

def soft_upload(btn_list: list = None, folder_config : str = None, folder_list : list = None):
    try:
        with button_lock:
            if btn_list is not None:
                #in place update of list
                BUTTON_LIST[:] = btn_list
                with open(CONFIG_FILE, "w") as f:
                    json.dump(BUTTON_LIST, f, indent=2)
            #update the folder file
            if folder_config and folder_list:
                with open(folder_config, "w") as f:
                    json.dump(folder_list, f, indent=2)
                logger.debug(f"updating {folder_config}")

    except FileNotFoundError as e:
        logger.exception(e)
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

#TODO: check and remove btn_list arg if not needed
def gui_upload(client: BaseClient, btn_list : list, change_log: list):
    sid = server_cmd_id.inc()
    change_log = set(change_log)
    with button_lock:
        BUTTON_LIST[:] = btn_list
    send_new_config(client, "/configs", sid, change_log)

def write_updates():
    logger.debug("Updating configs")
    try:
        with button_lock:
            with open(CONFIG_FILE, "w") as f:
                json.dump(BUTTON_LIST, f, indent=2)
        with open(IMG_TRACKER_PATH, "w") as f:
            json.dump(tracked_images, f, indent=2)
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)