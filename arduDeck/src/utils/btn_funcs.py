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
#todo move config file to btn_funcs? and lock it
CONFIG_FILE = "config/configs.json"
with open(CONFIG_FILE, "r") as f:
    BUTTON_LIST = json.load(f)

def build_client_config_file(client_dir):
    file_contents = ""
    with button_lock:
        for button in BUTTON_LIST:
            line = client_dir + "/" + button["image_path"].split('/')[-1] + " " + str(button["button_id"] + " " + "0")
            if file_contents == "":
                file_contents += line
            else:
                file_contents += "\n" + line
    # logger.debug(file_contents)
    with open(CLIENT_CONFIG_PATH, "w") as f:
        f.write(file_contents)

def add_button(btn_id, actions, image_path, cmd_dict):

    if any(button["button_id"] == btn_id for button in cmd_dict):
        raise ValueError("Button id already in use", btn_id)

    new_btn = {"button_id": btn_id, "actions": []}
    for action in actions:
        new_action = {"command_id": action[0], "command_args": action[1]}
        new_btn["actions"].append(new_action)
    new_btn["image_path"] = image_path

    cmd_dict.append(new_btn)
    #todo: remember to update the cmd_dict file contents

def update_button(btn_id, new_btn_id, new_actions, new_image_path):

    if not any(button["button_id"] == btn_id for button in BUTTON_LIST):
        raise ValueError("Button id does nto exists", btn_id)

    for button in BUTTON_LIST:
        if button["button_id"] == btn_id:
            button["button_id"] = new_btn_id
            button["actions"] = []
            for action in new_actions:
                new_action = {"command_id": action[0], "command_args": action[1]}
                button["actions"].append(new_action)
            button["image_path"] = new_image_path
            break

def delete_button(btn_id):
    if not any(button["button_id"] == btn_id for button in BUTTON_LIST):
        raise ValueError("Button id does nto exists", btn_id)
    
    # for button in CMD_DICT:
    #     if button["button_id"] == btn_id:
    #         CMD_DICT.remove(button)
    #         logger.debug("Removed element of id %d", button["button_id"])
    #         break

    new_CMD_DICT = [button for button in BUTTON_LIST if button["button_id"] != btn_id]
    BUTTON_LIST[:] = new_CMD_DICT  # Replace the contents of CMD_DICT with the new list

def send_new_config(client, client_dir, cmd_id):
    logger.debug("Building new config file")
    build_client_config_file(client_dir)

    with button_lock:
        for button in BUTTON_LIST:
            logger.debug(f"Checking for image {button['image_path']}")
            exists = False
            for image in tracked_images:
                if button["image_path"] == image["image_path"]:
                    exists = True
            if not exists:
                logger.debug("Image not on client. sending and indexing it")
                tracked_images.append({"image_path": button["image_path"]})
                handle_upload(client, button["image_path"], client_dir)
                time.sleep(0.5)
    logger.debug("Sending new config")
    write_updates()
    handle_upload(client, CLIENT_CONFIG_PATH, client_dir, "btn_config.txt")

    logger.debug("Sending request for redraw")
    req_contents = "redraw after upload"
    pd = create_packet(command_type=REDRAW_COMMAND,
                       command_id=cmd_id,
                       length=len(req_contents),
                       crc_value=0,
                       contents=req_contents)
    #todo mutex pe server id?? asta trimite 0 pt ca e cmd e copiat nu referentiat
    send_result = send_request(client, pd)
    if send_result == SUCCESSFUL_CONF:
        logger.debug("Success")
    else:
        logger.error("Unexpected response")

def soft_upload(btn_list: list):
    try:
        with button_lock:
            BUTTON_LIST[:] = btn_list

        with open(CONFIG_FILE, "w") as f:
            json.dump(BUTTON_LIST, f, indent=2)

    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

def gui_upload(client: BaseClient, btn_list: list):
    sid = server_cmd_id.inc()
    with button_lock:
        BUTTON_LIST[:] = btn_list
    send_new_config(client, "/configs", sid)

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