import ctypes
import time
from src.server_params import logger
from config.server_key_codes import key_scancodes, key_vkcodes
SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions 
LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_ulong), ("y", ctypes.c_ulong)]

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

def paste_contents(value):
    for event in keyboard_stream(value):
        SendInput(event)

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
# https://stackoverflow.com/questions/4263608/ctypes-mouse-events
class Mouse:
    """It simulates the mouse"""
    MOUSEEVENTF_MOVE = 0x0001 # mouse move
    MOUSEEVENTF_LEFTDOWN = 0x0002 # left button down
    MOUSEEVENTF_LEFTUP = 0x0004 # left button up
    MOUSEEVENTF_RIGHTDOWN = 0x0008 # right button down
    MOUSEEVENTF_RIGHTUP = 0x0010 # right button up
    MOUSEEVENTF_MIDDLEDOWN = 0x0020 # middle button down
    MOUSEEVENTF_MIDDLEUP = 0x0040 # middle button up
    MOUSEEVENTF_WHEEL = 0x0800 # wheel button rolled
    MOUSEEVENTF_ABSOLUTE = 0x8000 # absolute move
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    def _do_event(self, flags, x_pos, y_pos, data, extra_info):
        """generate a mouse event"""
        x_calc = int(65536 * x_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CXSCREEN)) + 1
        y_calc = int(65536 * y_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CYSCREEN)) + 1
        return ctypes.windll.user32.mouse_event(flags, x_calc, y_calc, data, extra_info)

    def _get_button_value(self, button_name, button_up=False):
        """convert the name of the button into the corresponding value"""
        buttons = 0
        if button_name.find("KEY_RBUTTON") >= 0:
            buttons = self.MOUSEEVENTF_RIGHTDOWN
        if button_name.find("KEY_LBUTTON") >= 0:
            buttons = buttons + self.MOUSEEVENTF_LEFTDOWN
        if button_name.find("KEY_MBUTTON") >= 0:
            buttons = buttons + self.MOUSEEVENTF_MIDDLEDOWN
        if button_up:
            buttons = buttons << 1
        return buttons

    def move_mouse(self, pos):
        """move the mouse to the specified coordinates"""
        (x, y) = pos
        #TODO: old pos is wrong also wrong mouse scaling
        old_pos = self.get_position()
        # x =  x if (x != -1) else old_pos[0]
        # y =  y if (y != -1) else old_pos[1]
        self._do_event(self.MOUSEEVENTF_MOVE + self.MOUSEEVENTF_ABSOLUTE, x, y, 0, 0)
        # ctypes.windll.user32.SetCursorPos(x, y)

    def press_button(self, pos=(-1, -1), button_name="KEY_LBUTTON", button_up=False):
        """push a button of the mouse"""
        self.move_mouse(pos)
        self._do_event(self._get_button_value(button_name, button_up), 0, 0, 0, 0)

    def release_button(self, pos=(-1, -1), button_name="KEY_LBUTTON", button_up=True):
        self.move_mouse(pos)
        self._do_event(self._get_button_value(button_name, button_up), 0, 0, 0, 0)

    def click(self, pos=(-1, -1), button_name= "left"):
        """Click at the specified placed"""
        self.move_mouse(pos)
        self._do_event(self._get_button_value(button_name, False)+self._get_button_value(button_name, True), 0, 0, 0, 0)

    def double_click (self, pos=(-1, -1), button_name="KEY_LBUTTON"):
        """Double click at the specifed placed"""
        for i in range(2):
            self.click(pos, button_name)

    def get_position(self):
        """get mouse position"""
        # return win32api.GetCursorPos()
        point = POINT()
        return ctypes.windll.user32.GetCursorPos(ctypes.pointer(point))