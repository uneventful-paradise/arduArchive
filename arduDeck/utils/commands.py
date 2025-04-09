import json
from basic_comms import logger


def add_button(btn_id, actions, image_path, cmd_dict):

    if any(button["button_id"] == btn_id for button in cmd_dict):
        raise ValueError("Button id already in use", btn_id)

    new_btn = {"button_id": btn_id, "actions": []}
    for action in actions:
        new_action = {"command_id": action[0], "command_args": action[1]}
        new_btn["actions"].append(new_action)
    new_btn["image_path"] = image_path

    cmd_dict.append(new_btn)


def update_button(btn_id, new_btn_id, new_actions, new_image_path, cmd_dict):

    if not any(button["button_id"] == btn_id for button in cmd_dict):
        raise ValueError("Button id does nto exists", btn_id)

    for button in cmd_dict:
        if button["button_id"] == btn_id:
            button["button_id"] = new_btn_id
            button["actions"] = []
            for action in new_actions:
                new_action = {"command_id": action[0], "command_args": action[1]}
                button["actions"].append(new_action)
            button["image_path"] = new_image_path

def write_updates(cmd_dict, cfg_file):
    try:
        with open(cfg_file, "w") as f:
            json.dump(cmd_dict, f)
    except IOError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)