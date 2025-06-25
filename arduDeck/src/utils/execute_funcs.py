import subprocess
import webbrowser
import json
import shlex

from src.basic_comms import *
from src.utils.server_key_presses import *
#load modifier key codes from file
CONFIG_FILE = "config/key_codes.json"
with open(CONFIG_FILE, "r") as f:
    KEY_CODES = json.load(f)

"""Start a new process using python subprocesses.
It starts the process in a nonblocking manner using `Popen`
so the server is still responsive during this time"""
def start_process(client, cmd_id, args):
    # file_path = args[0]
    # command = subprocess.Popen([file_path])
    # logger.debug("START_PROCESS %d successful", cmd_id)
    #todo find a way to get popen result without blocking - use threads?

    # try:
    #     res = command.communicate()
    #     if command.returncode != 0:
    #         raise subprocess.CalledProcessError
    # except subprocess.CalledProcessError(command.returncode, file_path):
    #     logger.warning("START_PROCESS %d failed", cmd_id)
    #     print(res[1])

    # process = subprocess.Popen([file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # logger.debug("START_PROCESS %d started", cmd_id)
    # stdout, stderr = process.communicate()  # This blocks, but it's in a separate thread
    # if process.returncode != 0:
    #     logger.warning("START_PROCESS %d failed. Error: %s", cmd_id, stderr.decode())
    # else:
    #     logger.debug("START_PROCESS %d successful", cmd_id)
    # thread = threading.Thread(target=process_worker, args=(cmd_id, file_path))

    script = args[0]
    raw_args = args[1:]
    _, ext = os.path.splitext(script.lower())

    script_args = []
    for token in raw_args:
        script_args += shlex.split(token)

    if ext == ".py":
        cmd = [sys.executable, script, *script_args]
        shell = False

    elif ext in (".bat", ".cmd"):
        # cmd.exe /c will run the batch and then exit
        cmd = ["cmd.exe", "/c", script, *script_args]
        shell = False

    elif ext == ".ps1":
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", script,
            *script_args
        ]
        shell = False

    elif ext == ".exe":
        # native executable
        cmd = [script, *script_args]
        shell = False

    else:
        # Let the shell figure it out (via file‐assoc)
        cmd = [script, *script_args]
        shell = True

    # On Windows, pop up an immediate console window
    creation_flags = subprocess.CREATE_NEW_CONSOLE

    try:
        subprocess.Popen(
            cmd,
            shell=shell,
            creationflags=creation_flags
        )
        logger.debug("START_SCRIPT %d launched: %r", cmd_id, cmd)
    except Exception:
        logger.exception("Failed to launch script %r", script)

"""Opens a new tab or a new browser instance if none is running currently.
This can be performed using shell but is unsafe and not recommended"""
def start_url(client, cmd_id, args):
    url = args[0]
    if webbrowser.open_new_tab(url):
        logger.debug("Start_url %d successful", cmd_id)
    else:
        logger.warning("START_URL %d failed", cmd_id)

"""Parses the macro sequence and converts key codes to their decimal value.
The individuals commands of the sequence are separated by the `+` character
and can be any of the following:

wNUMERICAL_VALUE  - wait for `NUMERICAL_VALUE` miliseconds. essentially a delay
dKEY_VALUE        - press down the key represented in decimal value by `KEY_VALUE`
uKEY_VALUE        - release the key represented in decimal value by `KEY_VALUE`
r                 - release all pressed keys
pVALUE            - print VALUE string

Keyboard modifiers (special keys like ALT, ESCAPE etc.) have codes assigned in the
KEY_CODES config file.
"""
#todo send these in chunks
def hard_key_press(client, cmd_id, args):
    key_sequence = args[0]
    keys = key_sequence.split("+")
    new_keys = []
    for key in keys:
        #get command prefix and argument
        value = key[2:]
        cmd_prefix = key[:2]
        # print(value)
        # paste and release commands remain unchanged
        if cmd_prefix in ("pt", "ra"):
            new_keys.append(key)
            continue
        #user gave key code. no conversion needed
        if cmd_prefix == "wt":
            try:
                new_val = int(float(value)*1000)
            except ValueError:
                logger.error("Failed to convert value for delay command")
            else:
                new_keys.append(cmd_prefix+str(new_val))
            finally:
                continue
        if value.isdigit():
            new_keys.append(key)
        #converting special keys or characters
        elif cmd_prefix in ('sd', 'kd', 'su', 'ku'):
            if len(value) == 1:                     #regular key
                logger.debug("regular key %s", value)
                key = cmd_prefix + str(ord(value))  #get ascii decimal value of key
                new_keys.append(key)
            elif len(value) > 1:                    #special key
                logger.debug("special key %s", value)
                key_code = ""
                #get the assigned key code from the config file
                for elem in KEY_CODES["keys"]:
                    try:
                        if elem["key_name"] == value:
                            key_code = cmd_prefix + str(elem["key_code"])
                            logger.debug("special key is %s of length %d", key_code, len(key_code))
                            new_keys.append(key_code)
                    except (KeyError, IndexError):
                        logger.warning("key code not found in config %d", key_code)
            else:
                logger.error("bad length")
        # singular character command
        else:
            new_keys.append(key)

    hexed_string = '+'.join(new_keys)
    pd = create_packet(command_type=MACRO_COMMAND,
                       command_id=cmd_id,
                       length=len(hexed_string),
                       crc_value=0,
                       contents=hexed_string)
    send_result = send_request(client, pd)
    if send_result == SUCCESSFUL_CONF:
        logger.debug("Success")
    else:
        logger.error("Unexpected response")

mouse = Mouse()
def soft_key_press(client, cmd_id, args):
    key_sequence = args[0]
    pressed_keys = []
    keys = key_sequence.split("+")

    for key in keys:
        #get command prefix and argument
        value = key[2:]
        cmd_prefix = key[0:2]
        # print(value)
        #paste contents
        if cmd_prefix == 'pt':
            paste_contents(value)
            # logger.debug("pt %s", value)
            # keyboard_stream(value)
        #key down
        elif cmd_prefix == 'kd':
            press_key(value)
            pressed_keys.append(value)
        #key up
        elif cmd_prefix == 'ku':
            release_key(value)
            try:
                pressed_keys.remove(value)
            except ValueError as e:
                logger.warning("Tried removing non existent key")
                logger.exception(e)
        #release all
        elif cmd_prefix == 'ra':
            for key_val in pressed_keys:
                release_key(key_val)
            pressed_keys.clear()
        #wait time
        elif cmd_prefix == 'wt':
            time.sleep(float(value))
        elif cmd_prefix == 'mm':
            pos = (tuple(int(x) for x in value.strip("()").split(',')))
            mouse.move_mouse(pos)
        elif cmd_prefix == 'md':
            info = value.split('@')
            btn_value = info[0]
            event_pos = info[1]
            pos = (tuple(int(x) for x in event_pos.strip("()").split(',')))
            mouse.press_button(pos, btn_value)
        elif cmd_prefix == 'mu':
            info = value.split('@')
            btn_value = info[0]
            event_pos = info[1]
            pos = (tuple(int(x) for x in event_pos.strip("()").split(',')))
            mouse.release_button(pos, btn_value)
        elif cmd_prefix in ('mv', 'mh'):
            if cmd_prefix == 'mv':
                vert = int(value)
                horiz = 0
            else:
                vert = 0
                horiz = int(value)
            mouse.scroll(vertical=vert, horizontal=horiz)

    logger.debug(f"Finished soft key press of id {cmd_id}")

def toggle_actions(client: BaseClient, cmd_id: int, args):
    actions = args
    logger.debug("toggle actions are: %s", str(actions))
    exec_act = actions.pop(0)
    logger.debug("executing first action of id %s", exec_act["command_id"])
    ACT_DICT[exec_act["command_id"]](client, cmd_id, exec_act["command_args"])
    logger.debug("rotating arguments")
    actions.append(exec_act)
    logger.debug("Successful toggle action of id %d", cmd_id)

#maps the commands to executing functions
ACT_DICT = {
    "START_PROCESS": start_process,
    "START_URL": start_url,
    "HARD_KEY_PRESS": hard_key_press,
    "SOFT_KEY_PRESS": soft_key_press,
    "TOGGLE_ACTIONS": toggle_actions,
}

# path = path.rstrip('\r\n')
# escaped_path = path.encode('unicode_escape').decode()
# escaped_path = escaped_path.rstrip('\r\n')
# print(path)
# print(escaped_path)
# subprocess.Popen(escaped_path)


# act = 'mm(628, 449)+wt0.364+mm(637, 470)+wt0.184+mm(654, 492)+wt0.024+mm(676, 508)+wt0.02+mm(698, 519)+wt0.018+mm(719, 526)+wt0.018+mm(740, 527)+wt0.02+mm(761, 525)+wt0.022+mm(782, 512)+wt0.034+mm(793, 491)+wt0.043+mm(798, 470)+wt0.057+mm(800, 449)+wt0.054+mm(800, 428)+wt0.044+mm(801, 407)+wt0.043+mm(799, 386)+wt0.036+mm(797, 365)+wt0.036+mm(795, 344)+wt0.032+mm(793, 323)+wt0.033+mm(776, 302)+wt0.176+mm(755, 284)+wt0.029+mm(734, 274)+wt0.028+mm(713, 265)+wt0.024+mm(692, 254)+wt0.025+mm(671, 241)+wt0.023+mm(650, 226)+wt0.031+mm(636, 205)+wt0.079+mm(628, 184)+wt0.04+mm(618, 163)+wt0.032+mm(606, 142)+wt0.031+mm(590, 121)+wt0.037+mm(569, 102)+wt0.057+mm(548, 90)+wt0.064+mm(527, 86)+wt0.059+mm(506, 86)+wt0.048+mm(485, 90)+wt0.043+mm(464, 96)+wt0.044+mm(443, 100)+wt0.05+mm(422, 106)+wt0.133+mm(419, 127)+wt0.112+mm(398, 131)+wt0.372+mm(377, 134)+wt0.026+mm(356, 137)+wt0.024+mm(335, 141)+wt0.023+mm(314, 146)+wt0.023+mm(293, 154)+wt0.026+mm(272, 164)+wt0.028+mm(251, 178)+wt0.036+mm(230, 194)+wt0.039+mm(212, 215)+wt0.039+mm(198, 236)+wt0.041+mm(186, 257)+wt0.044+mm(176, 278)+wt0.047+mm(166, 299)+wt0.048+mm(156, 320)+wt0.041+mm(152, 341)+wt0.042+mm(151, 362)+wt0.05+mm(155, 383)+wt0.044+mm(163, 404)+wt0.043+mm(173, 425)+wt0.045+mm(184, 446)+wt0.053+mm(199, 467)+wt0.063+mm(214, 488)+wt0.071+mm(234, 509)+wt0.085+mm(255, 526)+wt0.061+mm(276, 542)+wt0.046+mm(297, 554)+wt0.05+mm(318, 565)+wt0.058+mm(338, 544)+wt0.915+mm(351, 523)+wt0.043+mm(364, 502)+wt0.032+mm(376, 481)+wt0.03+mm(385, 460)+wt0.035+mm(393, 439)+wt0.041+mm(397, 418)+wt0.041+mm(400, 397)+wt0.035+mm(401, 376)+wt0.034+mm(403, 355)+wt0.034+mm(404, 334)+wt0.049+mm(411, 313)+wt0.22+mdKEY_LBUTTON@(411, 313)+wt0.138+muKEY_LBUTTON@(411, 313)+wt0.078'
# soft_key_press(None, 0, act)
