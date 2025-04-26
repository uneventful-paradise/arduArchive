import tkinter as tk
import time
import json
from config.server_key_codes import key_vkcodes
from pynput import mouse, keyboard
from pynput.keyboard import KeyCode

vk_to_name = {vk: name for name, vk in key_vkcodes.items()}
#TODO detect additional mouse buttons
# https://stackoverflow.com/questions/52577712/how-do-i-use-side-mouse-buttons-with-pynput
MOUSE_SENS = 21
# https://github.com/RMPR/atbswp/blob/master/atbswp/control.py
SPECIAL_KEYS = {keyboard.Key.alt: 'KEY_ALT', keyboard.Key.alt_l: 'KEY_LALT', keyboard.Key.alt_r: 'KEY_RALT',
                keyboard.Key.alt_gr: 'KEY_RALT', keyboard.Key.backspace: 'KEY_BACKSPACE',
                keyboard.Key.caps_lock: 'KEY_CAPSLOCK', keyboard.Key.cmd: 'KEY_LWIN', keyboard.Key.cmd_l: 'KEY_LWIN', keyboard.Key.cmd_r: 'KEY_RWIN',
                keyboard.Key.ctrl: 'KEY_CONTROL', keyboard.Key.ctrl_l: 'KEY_LCONTROL', keyboard.Key.ctrl_r: 'KEY_RCONTROL', keyboard.Key.delete: 'KEY_DELETE',
                keyboard.Key.down: 'KEY_DOWN', keyboard.Key.end: 'KEY_END', keyboard.Key.enter: 'KEY_ENTER',
                keyboard.Key.esc: 'KEY_ESCAPE', keyboard.Key.f1: 'KEY_F1', keyboard.Key.f2: 'KEY_F2', keyboard.Key.f3: 'KEY_F3',
                keyboard.Key.f4: 'KEY_F4', keyboard.Key.f5: 'KEY_F5', keyboard.Key.f6: 'KEY_F6', keyboard.Key.f7: 'KEY_F7',
                keyboard.Key.f8: 'KEY_F8', keyboard.Key.f9: 'KEY_F9', keyboard.Key.f10: 'KEY_F10', keyboard.Key.f11: 'KEY_F11',
                keyboard.Key.f12: 'KEY_F12', keyboard.Key.home: 'KEY_HOME', keyboard.Key.left: 'KEY_LEFT',
                keyboard.Key.page_down: 'KEY_PAGEDOWN', keyboard.Key.page_up: 'KEY_PAGEUP', keyboard.Key.right: 'KEY_RIGHT',
                keyboard.Key.shift: 'KEY_LSHIFT', keyboard.Key.shift_r: 'KEY_RSHIFT', keyboard.Key.space: 'KEY_SPACE',
                keyboard.Key.tab: 'KEY_TAB', keyboard.Key.up: 'KEY_UP', keyboard.Key.media_play_pause: 'KEY_MEDIA_PLAY_PAUSE',
                keyboard.Key.insert: 'KEY_INSERT', keyboard.Key.num_lock: 'KEY_NUMLOCK', keyboard.Key.pause: 'KEY_PAUSE',
                keyboard.Key.print_screen: 'KEY_PRINT_SCREEN', keyboard.Key.scroll_lock: 'KEY_SCROLL_LOCK', keyboard.Key.media_volume_up: 'KEY_VOLUME_UP',
                keyboard.Key.media_volume_down: 'KEY_VOLUME_DOWN', keyboard.Key.media_volume_mute: 'KEY_VOLUME_MUTE',
                keyboard.Key.media_previous: 'KEY_MEDIA_PREVIOUS', keyboard.Key.media_next: 'KEY_MEDIA_NEXT'}

from ctypes import windll

def char2key(c):
    # https://msdn.microsoft.com/en-us/library/windows/desktop/ms646329(v=vs.85).aspx
    result = windll.User32.VkKeyScanW(c)
    shift_state = (result & 0xFF00) >> 8
    vk_key = result & 0xFF

    return vk_key

class KeyRecorder(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.bind_all("<KeyRelease-Control_R>", lambda e: self.finish())
        self.callback = callback
        self.pressed = {}   # keycode -> timestamp
        self.history = []   # list of (keycode, action, time, duration)

        self.title("Record a key combination")
        self.geometry("300x100")
        self.last_time = time.time()


        done_btn = tk.Button(self, text="Done", command=self.finish)
        done_btn.pack(pady=20)

        self.focus_force()
        self.recording = True
        self.last_x = 0
        self.last_y = 0
        self.record()

    def record(self):
        mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll)
        mouse_listener.start()

        kb_listener = keyboard.Listener(
            on_press=self.on_key_down,
            on_release=self.on_key_up)
        kb_listener.start()


    def on_move(self, x, y):
        if not self.recording:
            return False
        #use perfect counter instead?
        t = time.time()
        delta = float(t - self.last_time)
        if delta > 0.0:
            if abs(x - self.last_x) < MOUSE_SENS and abs(y - self.last_y) < MOUSE_SENS:
                return
            else:
                self.history.append({
                    'type': 'MOUSE_MOVE',
                    'x': x,
                    'y': y,
                    't': t,
                    'dt': delta
                })
            self.last_x = x
            self.last_y = y
            print('Pointer moved to {}; it was {}'.format(x, y))
        #use time.perf_counter()
        self.last_time = t

    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return False

        t = time.time()
        delta = float(t - self.last_time)
        if delta > 0.0:
            if pressed:
                if button == mouse.Button.left:
                    self.history.append({
                        'type': 'MOUSE_PRESS',
                        'key_name': 'KEY_LBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                elif button == mouse.Button.right:
                    self.history.append({
                        'type': 'MOUSE_PRESS',
                        'key_name': 'KEY_RBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                elif button == mouse.Button.middle:
                    self.history.append({
                        'type': 'MOUSE_PRESS',
                        'key_name': 'KEY_MBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                else:
                    self.history.append({
                        'type': 'MOUSE_PRESS',
                        'key_name': 'UNKNOWN',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                    print("Unknown mouse button pressed")
            else:
                if button == mouse.Button.left:
                    self.history.append({
                        'type': 'MOUSE_RELEASE',
                        'key_name': 'KEY_LBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                elif button == mouse.Button.right:
                    self.history.append({
                        'type': 'MOUSE_RELEASE',
                        'key_name': 'KEY_RBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                elif button == mouse.Button.middle:
                    self.history.append({
                        'type': 'MOUSE_RELEASE',
                        'key_name': 'KEY_MBUTTON',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                else:
                    self.history.append({
                        'type': 'MOUSE_RELEASE',
                        'key_name': 'UNKNOWN',
                        'x': x,
                        'y': y,
                        't': t,
                        'dt': delta
                    })
                    print("Unknown mouse button released")

            print('{} at {}; it was {}'.format(
                'Pressed' if pressed else 'Released',
                x, y))

        self.last_time = t

    def on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return False
        # t = time.time()
        # delta = float(t - self.last_time)
        self.history.append({
            'type': 'MOUSE_SCROLL',
            'y': y,
            # 't': t,
            # 'dt': delta
        })
        # self.last_time = t
        print('Scrolled {} at {}; it was {}'.format(
            'down' if dy < 0 else 'up',
            x, y))

    def on_key_down(self, key):
        if not self.recording:
            return False

        t = time.time()
        key_name = None
        vk = None
        char_name = None

        if isinstance(key, KeyCode) and key.vk is not None:
            vk = key.vk
            key_name = vk_to_name[vk]
        else:
            key_name = SPECIAL_KEYS.get(key, None)
            if key_name is None:
                print("Key not recognized")
                return
            vk = key_vkcodes[key_name]


        # try:
        #     char_name = key.char
        #     vk = char2key(ord(char_name))
        #     key_name = vk_to_name[vk]
        # except AttributeError:
        #     key_name = SPECIAL_KEYS.get(key, None)
        #     if key_name is None:
        #         print("Key not recognized")
        #         return
        #     vk = key_vkcodes[key_name]
        # except KeyError:
        #     print(f"No corresponding key for vk {vk} of char {char_name}")


        if vk in self.pressed:
            return

        # print(f"Pressed key {key_name if key_name is not None else None} of vk {vk if vk is not None else None}")

        # compute dt = now - last_event_time
        # if self.history:
        #     delta = float(t - self.history[-1]['t'])
        # else:
        #     delta = 0.0
        delta = t - self.last_time
        self.last_time = t

        self.pressed[vk] = t
        self.history.append({
            'type': 'KEY_PRESS',
            'key_name': key_name,
            'vk': vk,
            't': t,
            'dur': None,
            'dt': delta
        })
        # print(f"↓ {key_name} @ {t:.3f}")
        print(f"↓ {key_name} @ {t:.3f}")

    def on_key_up(self, key):
        if not self.recording:
            return False

        t = time.time()

        if isinstance(key, KeyCode) and key.vk is not None:
            vk = key.vk
            key_name = vk_to_name[vk]
        else:
            key_name = SPECIAL_KEYS.get(key, None)
            if key_name is None:
                print("Key not recognized")
                return
            vk = key_vkcodes[key_name]

        # try:
        #     char_name = key.char
        #     vk = char2key(ord(char_name))
        #     key_name = vk_to_name[vk]
        # except AttributeError:
        #     key_name = SPECIAL_KEYS.get(key, None)
        #     if key_name is None:
        #         print("Key not recognized")
        #         return
        #     vk = key_vkcodes[key_name]

        t0 = self.pressed.pop(vk, None)
        dur = (t - t0) if t0 is not None else None

        # delta since last event
        # if self.history:
        #     dt = t - self.history[-1]['t']
        # else:
        #     dt = 0.0
        delta = float(t - self.last_time)
        self.last_time = t

        self.history.append({
            'type': 'KEY_RELEASE',
            'key_name': key_name,
            'vk': vk,
            't': t,
            'dur': dur,
            'dt': delta
        })
        print(f"↑ {key_name} @ {t:.3f}")

    def finish(self):
        # translate to your desired json format, mapping vk → name
        self.recording = False
        combo = []
        for ev in self.history:
            if ev['type'] == 'KEY_PRESS' or ev['type'] == 'KEY_RELEASE':
                vk   = ev['vk']
                name = vk_to_name.get(vk, f"VK_{vk:02X}")    # fallback to hex if unknown
                combo.append({
                    'type': ev['type'],
                    'vk'   : name,
                    'dt'    : round(ev['dt'], 3),
                    'dur'   : round(ev['dur'],3) if ev['dur'] is not None else None
                })
            else:
                combo.append(ev)
        macro_string = self.create_macro_string()
        json_str = json.dumps(combo, indent=2)
        self.callback(json_str, macro_string)
        self.destroy()

    def create_macro_string(self):
        segments = []
        for ev in self.history:
            seq = ''
            if ev['type'] == 'KEY_PRESS':
                seq = 'kd' + ev['key_name'] + '+wt' + str(round(ev['dt'],3))
            elif ev['type'] == 'KEY_RELEASE':
                seq = 'ku' + ev['key_name'] + '+wt' + str(round(ev['dt'],3))
            elif ev['type'] == 'MOUSE_PRESS':
                #first move to that position then press the key
                seq = 'md' + ev['key_name'] + '@' + str((ev['x'], ev['y'])) + '+wt' + str(round(ev['dt'],3))
            elif ev['type'] == 'MOUSE_RELEASE':
                seq = 'mu' + ev['key_name'] + '@' + str((ev['x'], ev['y'])) + '+wt' + str(round(ev['dt'],3))
            elif ev['type'] == 'MOUSE_MOVE':
                seq = 'mm'+ str((ev['x'], ev['y'])) + '+wt' + str(round(ev['dt'],3))
            elif ev['type'] == 'MOUSE_SCROLL':
                seq = 'ms' + str(ev['y'])
            else:
                print("Error during macro string building")
                continue
            segments.append(seq)

        return '+'.join(segments)
def rec_callback(json_str, macro_string):
    print("Final combo JSON:")
    print(macro_string)
    with open("testing/macro_dump", 'w') as f:
        f.write(macro_string)
    print(json_str)