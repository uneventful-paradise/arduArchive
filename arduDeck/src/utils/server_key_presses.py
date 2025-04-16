import ctypes
import time
from src.basic_comms import logger
from config.server_key_codes import key_scancodes, key_vkcodes
SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions 
LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort

# PUL = ctypes.POINTER(ctypes.c_ulong)
# class KeyBdInput(ctypes.Structure):
#     _fields_ = [("wVk", ctypes.c_ushort),
#                 ("wScan", ctypes.c_ushort),
#                 ("dwFlags", ctypes.c_ulong),
#                 ("time", ctypes.c_ulong),
#                 ("dwExtraInfo", PUL)]

# class HardwareInput(ctypes.Structure):
#     _fields_ = [("uMsg", ctypes.c_ulong),
#                 ("wParamL", ctypes.c_short),
#                 ("wParamH", ctypes.c_ushort)]

# class MouseInput(ctypes.Structure):
#     _fields_ = [("dx", ctypes.c_long),
#                 ("dy", ctypes.c_long),
#                 ("mouseData", ctypes.c_ulong),
#                 ("dwFlags", ctypes.c_ulong),
#                 ("time",ctypes.c_ulong),
#                 ("dwExtraInfo", PUL)]

# class Input_I(ctypes.Union):
#     _fields_ = [("ki", KeyBdInput),
#                  ("mi", MouseInput),
#                  ("hi", HardwareInput)]

# class Input(ctypes.Structure):
#     _fields_ = [("type", ctypes.c_ulong),
#                 ("ii", Input_I)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))
                
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (('wVk', WORD),
                ('wScan', WORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))
                
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (('uMsg', DWORD),
                ('wParamL', WORD),
                ('wParamH', WORD))
                
class _INPUTunion(ctypes.Union):
    _fields_ = (('mi', MOUSEINPUT),
                ('ki', KEYBDINPUT),
                ('hi', HARDWAREINPUT))
                
class INPUT(ctypes.Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))
                
def SendInput(*inputs):
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = ctypes.c_int(ctypes.sizeof(INPUT))
    return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2
    
def Input(structure):
    if isinstance(structure, MOUSEINPUT):
        return INPUT(INPUT_MOUSE, _INPUTunion(mi=structure))
    if isinstance(structure, KEYBDINPUT):
        return INPUT(INPUT_KEYBOARD, _INPUTunion(ki=structure))
    if isinstance(structure, HARDWAREINPUT):
        return INPUT(INPUT_HARDWARE, _INPUTunion(hi=structure))
    raise TypeError('Cannot create INPUT structure!')

WHEEL_DELTA = 120
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_HWHEEL = 0x01000
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_UNICODE = 0x0004

def MouseInput(flags, x, y, data):
    return MOUSEINPUT(x, y, data, flags, 0, None)

def KeybdInput(code, flags):
    return KEYBDINPUT(code, code, flags, 0, None)

def HardwareInput(message, parameter):
    return HARDWAREINPUT(message & 0xFFFFFFFF,
                         parameter & 0xFFFF,
                         parameter >> 16 & 0xFFFF)

def Mouse(flags, x=0, y=0, data=0):
    return Input(MouseInput(flags, x, y, data))

def Keyboard(code, flags=0):
    return Input(KeybdInput(code, flags))

def Hardware(message, parameter=0):
    return Input(HardwareInput(message, parameter))
# Actuals Functions


def KeybdInput(code, flags):
    return KEYBDINPUT(code, code, flags, 0, None)

def HardwareInput(message, parameter):
    return HARDWAREINPUT(message & 0xFFFFFFFF,
                         parameter & 0xFFFF,
                         parameter >> 16 & 0xFFFF)

def Mouse(flags, x=0, y=0, data=0):
    return Input(MouseInput(flags, x, y, data))

def Keyboard(code, flags=0):
    return Input(KeybdInput(code, flags))

def Hardware(message, parameter=0):
    return Input(HardwareInput(message, parameter))

################################################################################

import string

UPPER = frozenset('~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?')
LOWER = frozenset("`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./")
ORDER = string.ascii_letters + string.digits + ' \b\r\t'
ALTER = dict(zip('!@#$%^&*()', '1234567890'))
OTHER = {'`': key_vkcodes['KEY_OEM_3'],
         '~': key_vkcodes['KEY_OEM_3'],
         '-': key_vkcodes['KEY_OEM_MINUS'],
         '_': key_vkcodes['KEY_OEM_MINUS'],
         '=': key_vkcodes['KEY_OEM_PLUS'],
         '+': key_vkcodes['KEY_OEM_PLUS'],
         '[': key_vkcodes['KEY_OEM_4'],
         '{': key_vkcodes['KEY_OEM_4'],
         ']': key_vkcodes['KEY_OEM_6'],
         '}': key_vkcodes['KEY_OEM_6'],
         '\\': key_vkcodes['KEY_OEM_5'],
         '|': key_vkcodes['KEY_OEM_5'],
         ';': key_vkcodes['KEY_OEM_1'],
         ':': key_vkcodes['KEY_OEM_1'],
         "'": key_vkcodes['KEY_OEM_7'],
         '"': key_vkcodes['KEY_OEM_7'],
         ',': key_vkcodes['KEY_OEM_COMMA'],
         '<': key_vkcodes['KEY_OEM_COMMA'],
         '.': key_vkcodes['KEY_OEM_PERIOD'],
         '>': key_vkcodes['KEY_OEM_PERIOD'],
         '/': key_vkcodes['KEY_OEM_2'],
         '?': key_vkcodes['KEY_OEM_2'],}


def keyboard_stream(string):
    mode = False
    for character in string.replace('\r\n', '\r').replace('\n', '\r'):
        # print(character)
        if mode and character in LOWER or not mode and character in UPPER:
            yield Keyboard(key_vkcodes['KEY_SHIFT'], mode and KEYEVENTF_KEYUP)
            mode = not mode
        character = ALTER.get(character, character)
        if character in ORDER:
            code = ord(character.upper())
        elif character in OTHER:
            code = OTHER[character]
        else:
            logger.warning("Unrecognized character")
            continue
            #Or, to abort on unavailable character
            #raise ValueError('String is not understood!')
        yield Keyboard(code)
        yield Keyboard(code, KEYEVENTF_KEYUP)
    if mode:
        yield Keyboard(key_vkcodes['KEY_SHIFT'], KEYEVENTF_KEYUP)

def press_key(dict_key):
    logger.debug(f"press_key: {key_vkcodes[dict_key]}")
    try:
        SendInput(Keyboard(key_vkcodes[dict_key]))
    except KeyError as e:
        logger.exception(e)

def release_key(dict_key):
    logger.debug(f"release_key: {key_vkcodes[dict_key]}")
    try:
        SendInput(Keyboard(key_vkcodes[dict_key], KEYEVENTF_KEYUP))
    except KeyError as e:
        logger.exception(e)

def sc_press(key_code):
    extra = ctypes.c_ulong(0)
    ii_ = _INPUTunion()
    ii_.ki = KEYBDINPUT( 0, key_code, 0x0008, 0, ctypes.pointer(extra) )
    x = INPUT( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def sc_release(key_code):
    extra = ctypes.c_ulong(0)
    ii_ = _INPUTunion   ()
    ii_.ki = KEYBDINPUT( 0, key_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = INPUT( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def sc_print():
    time.sleep(2)
    sc_press(key_scancodes["KEY_M"])
    sc_release(key_scancodes["KEY_M"])
    sc_press(key_scancodes["KEY_A"])
    sc_release(key_scancodes["KEY_A"])
    sc_press(key_scancodes["KEY_T"])
    sc_release(key_scancodes["KEY_T"])
    sc_press(key_scancodes["KEY_A"])
    sc_release(key_scancodes["KEY_A"])

    # sc_press(key_scancodes["KEY_LCONTROL"])
    # time.sleep(0.1)
    # sc_press(key_scancodes["KEY_R"])
    # time.sleep(0.1)
    # sc_release(key_scancodes["KEY_LCONTROL"])
    # time.sleep(0.1)
    # sc_release(key_scancodes["KEY_R"])

def vk_send():
    time.sleep(1.5)
    SendInput(Keyboard(key_vkcodes['KEY_LWIN']))
    time.sleep(0.2)
    SendInput(Keyboard(key_vkcodes['KEY_R']))
    time.sleep(0.2)
    SendInput(Keyboard(key_vkcodes['KEY_LWIN'], KEYEVENTF_KEYUP))
    time.sleep(0.2)
    SendInput(Keyboard(key_vkcodes['KEY_R'], KEYEVENTF_KEYUP))
    time.sleep(1)

    for event in keyboard_stream("C:\\Users\\dante\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"):
        SendInput(event)
        # time.sleep(0.1)
    SendInput(Keyboard(key_vkcodes['KEY_RETURN']))
    time.sleep(0.2)
    SendInput(Keyboard(key_vkcodes['KEY_RETURN'], KEYEVENTF_KEYUP))
# sc_print()
# vk_send()