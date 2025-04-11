import json
import time

from basic_comms import logger, handle_upload, send_request, REDRAW_COMMAND, SUCCESSFUL_CONF

CLIENT_CONFIG_PATH = "config/client_config.txt"
IMG_TRACKER_PATH = "config/tracked_img.json"
with open(IMG_TRACKER_PATH, "r") as f:
    tracked_images = json.load(f)
#todo move config file to btn_funcs? and lock it
CONFIG_FILE = "config/configs.json"
with open(CONFIG_FILE, "r") as f:
    CMD_DICT = json.load(f)

def build_client_config_file(client_dir):
    file_contents = ""
    for button in CMD_DICT:
        line = client_dir + "/" + button["image_path"].split('/')[-1] + " " + str(button["button_id"])
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

    if not any(button["button_id"] == btn_id for button in CMD_DICT):
        raise ValueError("Button id does nto exists", btn_id)

    for button in CMD_DICT:
        if button["button_id"] == btn_id:
            button["button_id"] = new_btn_id
            button["actions"] = []
            for action in new_actions:
                new_action = {"command_id": action[0], "command_args": action[1]}
                button["actions"].append(new_action)
            button["image_path"] = new_image_path
            break

def send_new_config(client_socket, client_dir, cmd_id):
    logger.debug("Building new config file")
    build_client_config_file(client_dir)

    for button in CMD_DICT:
        logger.debug(f"Checking for image {button['image_path']}")
        exists = False
        for image in tracked_images:
            if button["image_path"] == image["image_path"]:
                exists = True
        if not exists:
            logger.debug("Image not on client. sending and indexing it")
            tracked_images.append({"image_path": button["image_path"]})
            handle_upload(client_socket, button["image_path"], client_dir)
            time.sleep(0.5)
    logger.debug("Sending new config")
    handle_upload(client_socket, CLIENT_CONFIG_PATH, client_dir, "btn_config.txt")

    req_contents = "redraw after upload"
    logger.debug("Sending request for redraw")
    send_result = send_request(client_socket, REDRAW_COMMAND, cmd_id, len(req_contents), req_contents)
    if send_result == SUCCESSFUL_CONF:
        logger.debug("Success")
    else:
        logger.error("Unexpected response")


def write_updates():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(CMD_DICT, f, indent=2)
        with open(IMG_TRACKER_PATH, "w") as f:
            json.dump(tracked_images, f, indent=2)
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)