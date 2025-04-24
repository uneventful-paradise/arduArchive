# http://www.kbdedit.com/manual/low_level_vk_list.html
key_vkcodes = {
    "KEY_LBUTTON": 0x01,  # Left mouse button
    "KEY_RBUTTON": 0x02,  # Right mouse button
    "KEY_CANCEL": 0x03,  # Control-break processing
    "KEY_MBUTTON": 0x04,  # Middle mouse button (three-button mouse)
    "KEY_XBUTTON1": 0x05,  # X1 mouse button
    "KEY_XBUTTON2": 0x06,  # X2 mouse button
    "KEY_BACKSPACE": 0x08,  # BACKSPACE key
    "KEY_TAB": 0x09,  # TAB key
    "KEY_CLEAR": 0x0C,  # CLEAR key
    "KEY_ENTER": 0x0D,  # ENTER key
    "KEY_SHIFT": 0x10,  # SHIFT key
    "KEY_CONTROL": 0x11,  # CTRL key
    "KEY_ALT": 0x12,  # ALT key
    "KEY_PAUSE": 0x13,  # PAUSE key
    "KEY_CAPSLOCK": 0x14,  # CAPS LOCK key
    "KEY_KANA": 0x15,  # IME Kana mode
    "KEY_HANGUL": 0x15,  # IME Hangul mode (same as VK_KANA)
    "KEY_JUNJA": 0x17,  # IME Junja mode
    "KEY_FINAL": 0x18,  # IME final mode
    "KEY_HANJA": 0x19,  # IME Hanja mode
    "KEY_KANJI": 0x19,  # IME Kanji mode (same as VK_HANJA)
    "KEY_ESCAPE": 0x1B,  # ESC key
    "KEY_CONVERT": 0x1C,  # IME convert
    "KEY_NONCONVERT": 0x1D,  # IME nonconvert
    "KEY_ACCEPT": 0x1E,  # IME accept
    "KEY_MODECHANGE": 0x1F,  # IME mode change request
    "KEY_SPACE": 0x20,  # SPACEBAR
    "KEY_PAGEUP": 0x21,  # PAGE UP key
    "KEY_PAGEDOWN": 0x22,  # PAGE DOWN key
    "KEY_END": 0x23,  # END key
    "KEY_HOME": 0x24,  # HOME key
    "KEY_LEFT": 0x25,  # LEFT ARROW key
    "KEY_UP": 0x26,  # UP ARROW key
    "KEY_RIGHT": 0x27,  # RIGHT ARROW key
    "KEY_DOWN": 0x28,  # DOWN ARROW key
    "KEY_SELECT": 0x29,  # SELECT key
    "KEY_PRINT": 0x2A,  # PRINT key
    "KEY_EXECUTE": 0x2B,  # EXECUTE key
    "KEY_PRINT_SCREEN": 0x2C,  # PRINT SCREEN key
    "KEY_INSERT": 0x2D,  # INS key
    "KEY_DELETE": 0x2E,  # DEL key
    "KEY_HELP": 0x2F,  # HELP key
    "KEY_LWIN": 0x5B,  # Left Windows key
    "KEY_RWIN": 0x5C,  # Right Windows key
    "KEY_APPS": 0x5D,  # Applications key
    "KEY_SLEEP": 0x5F,  # Computer Sleep key
    "KEY_NUMPAD0": 0x60,  # Numeric keypad 0 key
    "KEY_NUMPAD1": 0x61,  # Numeric keypad 1 key
    "KEY_NUMPAD2": 0x62,  # Numeric keypad 2 key
    "KEY_NUMPAD3": 0x63,  # Numeric keypad 3 key
    "KEY_NUMPAD4": 0x64,  # Numeric keypad 4 key
    "KEY_NUMPAD5": 0x65,  # Numeric keypad 5 key
    "KEY_NUMPAD6": 0x66,  # Numeric keypad 6 key
    "KEY_NUMPAD7": 0x67,  # Numeric keypad 7 key
    "KEY_NUMPAD8": 0x68,  # Numeric keypad 8 key
    "KEY_NUMPAD9": 0x69,  # Numeric keypad 9 key
    "KEY_MULTIPLY": 0x6A,  # Multiply key
    "KEY_ADD": 0x6B,  # Add key
    "KEY_SEPARATOR": 0x6C,  # Separator key
    "KEY_SUBTRACT": 0x6D,  # Subtract key
    "KEY_DECIMAL": 0x6E,  # Decimal key
    "KEY_DIVIDE": 0x6F,  # Divide key
    "KEY_F1": 0x70,  # F1 key
    "KEY_F2": 0x71,  # F2 key
    "KEY_F3": 0x72,  # F3 key
    "KEY_F4": 0x73,  # F4 key
    "KEY_F5": 0x74,  # F5 key
    "KEY_F6": 0x75,  # F6 key
    "KEY_F7": 0x76,  # F7 key
    "KEY_F8": 0x77,  # F8 key
    "KEY_F9": 0x78,  # F9 key
    "KEY_F10": 0x79,  # F10 key
    "KEY_F11": 0x7A,  # F11 key
    "KEY_F12": 0x7B,  # F12 key
    "KEY_F13": 0x7C,  # F13 key
    "KEY_F14": 0x7D,  # F14 key
    "KEY_F15": 0x7E,  # F15 key
    "KEY_F16": 0x7F,  # F16 key
    "KEY_F17": 0x80,  # F17 key
    "KEY_F18": 0x81,  # F18 key
    "KEY_F19": 0x82,  # F19 key
    "KEY_F20": 0x83,  # F20 key
    "KEY_F21": 0x84,  # F21 key
    "KEY_F22": 0x85,  # F22 key
    "KEY_F23": 0x86,  # F23 key
    "KEY_F24": 0x87,  # F24 key
    "KEY_NUMLOCK": 0x90,  # NUM LOCK key
    "KEY_SCROLL_LOCK": 0x91,  # SCROLL LOCK key
    "KEY_LSHIFT": 0xA0,            # Left SHIFT key, decimal: 160
    "KEY_RSHIFT": 0xA1,            # Right SHIFT key, decimal: 161
    "KEY_LCONTROL": 0xA2,          # Left CONTROL key, decimal: 162
    "KEY_RCONTROL": 0xA3,          # Right CONTROL key, decimal: 163
    "KEY_LALT": 0xA4,             # Left MENU key, decimal: 164
    "KEY_RALT": 0xA5,             # Right MENU key, decimal: 165
    "KEY_BROWSER_BACK": 0xA6,      # Browser Back key, decimal: 166
    "KEY_BROWSER_FORWARD": 0xA7,   # Browser Forward key, decimal: 167
    "KEY_BROWSER_REFRESH": 0xA8,   # Browser Refresh key, decimal: 168
    "KEY_BROWSER_STOP": 0xA9,      # Browser Stop key, decimal: 169
    "KEY_BROWSER_SEARCH": 0xAA,    # Browser Search key, decimal: 170
    "KEY_BROWSER_FAVORITES": 0xAB, # Browser Favorites key, decimal: 171
    "KEY_BROWSER_HOME": 0xAC,      # Browser Start and Home key, decimal: 172
    "KEY_VOLUME_MUTE": 0xAD,       # Volume Mute key, decimal: 173
    "KEY_VOLUME_DOWN": 0xAE,       # Volume Down key, decimal: 174
    "KEY_VOLUME_UP": 0xAF,         # Volume Up key, decimal: 175
    "KEY_MEDIA_NEXT": 0xB0,  # Next Track key, decimal: 176
    "KEY_MEDIA_PREV": 0xB1,  # Previous Track key, decimal: 177
    "KEY_MEDIA_STOP": 0xB2,        # Stop Media key, decimal: 178
    "KEY_MEDIA_PLAY_PAUSE": 0xB3,  # Play/Pause Media key, decimal: 179
    "KEY_LAUNCH_MAIL": 0xB4,       # Start Mail key, decimal: 180
    "KEY_LAUNCH_MEDIA_SELECT": 0xB5,  # Select Media key, decimal: 181
    "KEY_LAUNCH_APP1": 0xB6,       # Start Application 1 key, decimal: 182
    "KEY_LAUNCH_APP2": 0xB7,       # Start Application 2 key, decimal: 183
    "KEY_OEM_1": 0xBA,             # US keyboard ';:' key, decimal: 186
    "KEY_OEM_PLUS": 0xBB,          # '+' key, decimal: 187
    "KEY_OEM_COMMA": 0xBC,         # ',' key, decimal: 188
    "KEY_OEM_MINUS": 0xBD,         # '-' key, decimal: 189
    "KEY_OEM_PERIOD": 0xBE,        # '.' key, decimal: 190
    "KEY_OEM_2": 0xBF,             # US keyboard '/?' key, decimal: 191
    "KEY_OEM_3": 0xC0,             # US keyboard '`~' key, decimal: 192
    "KEY_OEM_4": 0xDB,             # US keyboard '[{' key, decimal: 219
    "KEY_OEM_5": 0xDC,             # US keyboard '\|' key, decimal: 220
    "KEY_OEM_6": 0xDD,             # US keyboard ']}' key, decimal: 221
    "KEY_OEM_7": 0xDE,             # US keyboard single/double quote key, decimal: 222
    "KEY_OEM_8": 0xDF,             # Miscellaneous, decimal: 223
    "KEY_OEM_102": 0xE2,           # RT 102-key keyboard key, decimal: 226
    "KEY_PROCESSKEY": 0xE5,        # IME PROCESS key, decimal: 229
    "KEY_PACKET": 0xE7,            # Used for Unicode characters, decimal: 231
    "KEY_ATTN": 0xF6,              # Attn key, decimal: 246
    "KEY_CRSEL": 0xF7,             # CrSel key, decimal: 247
    "KEY_EXSEL": 0xF8,             # ExSel key, decimal: 248
    "KEY_EREOF": 0xF9,             # Erase EOF key, decimal: 249
    "KEY_PLAY": 0xFA,              # Play key, decimal: 250
    "KEY_ZOOM": 0xFB,              # Zoom key, decimal: 251
    "KEY_PA1": 0xFD,               # PA1 key, decimal: 253
    "KEY_OEM_CLEAR": 0xFE,         # Clear key, decimal: 254
    # Dictionary for alphanumeric keys (using the top row digits and QWERTY letters)
    # Number row
    "KEY_0": 0x30,
    "KEY_1": 0x31,
    "KEY_2": 0x32,
    "KEY_3": 0x33,
    "KEY_4": 0x34,
    "KEY_5": 0x35,
    "KEY_6": 0x36,
    "KEY_7": 0x37,
    "KEY_8": 0x38,
    "KEY_9": 0x39,

    # Alphabet keys
    "KEY_A": 0x41,
    "KEY_B": 0x42,
    "KEY_C": 0x43,
    "KEY_D": 0x44,
    "KEY_E": 0x45,
    "KEY_F": 0x46,
    "KEY_G": 0x47,
    "KEY_H": 0x48,
    "KEY_I": 0x49,
    "KEY_J": 0x4A,
    "KEY_K": 0x4B,
    "KEY_L": 0x4C,
    "KEY_M": 0x4D,
    "KEY_N": 0x4E,
    "KEY_O": 0x4F,
    "KEY_P": 0x50,
    "KEY_Q": 0x51,
    "KEY_R": 0x52,
    "KEY_S": 0x53,
    "KEY_T": 0x54,
    "KEY_U": 0x55,
    "KEY_V": 0x56,
    "KEY_W": 0x57,
    "KEY_X": 0x58,
    "KEY_Y": 0x59,
    "KEY_Z": 0x5A
}

#todo some keys need extended flag: https://stackoverflow.com/questions/28964684/what-is-the-c-key-scan-code-for-the-windows-button
key_scancodes = {
    # Mouse and non-keyboard keys (no standard scancode)
    "KEY_LBUTTON": None,        # Left mouse button (no scancode)
    "KEY_RBUTTON": None,        # Right mouse button (no scancode)
    "KEY_CANCEL": None,         # Control-break processing (not standard)
    "KEY_MBUTTON": None,        # Middle mouse button (no scancode)
    "KEY_XBUTTON1": None,       # X1 mouse button (no scancode)
    "KEY_XBUTTON2": None,       # X2 mouse button (no scancode)

    # Control and modifier keys
    "KEY_BACK": 0x0E,           # BACKSPACE key, hex 0x0E == 14
    "KEY_TAB": 0x0F,            # TAB key, hex 0x0F == 15
    "KEY_CLEAR": None,          # CLEAR key (ambiguous; often on the numeric keypad)
    "KEY_RETURN": 0x1C,         # ENTER key, hex 0x1C == 28
    "KEY_SHIFT": None,          # Generic SHIFT (use KEY_LSHIFT/KEY_RSHIFT)
    "KEY_CONTROL": None,        # Generic CONTROL (use KEY_LCONTROL/KEY_RCONTROL)
    "KEY_MENU": None,           # Generic ALT (use KEY_LMENU/KEY_RMENU)
    "KEY_PAUSE": "E1_1D45",     # PAUSE key (special multi-byte scancode)
    "KEY_CAPITAL": 0x3A,        # CAPS LOCK key, hex 0x3A == 58

    # IME/Alternate input keys (hardware/driver dependent)
    "KEY_KANA": None,
    "KEY_HANGUL": None,
    "KEY_JUNJA": None,
    "KEY_FINAL": None,
    "KEY_HANJA": None,
    "KEY_KANJI": None,

    "KEY_ESCAPE": 0x01,         # ESC key, hex 0x01 == 1

    "KEY_CONVERT": None,
    "KEY_NONCONVERT": None,
    "KEY_ACCEPT": None,
    "KEY_MODECHANGE": None,

    "KEY_SPACE": 0x39,          # SPACEBAR, hex 0x39 == 57

    # Navigation keys (commonly sent with an E0 prefix)
    "KEY_PRIOR": 0x49,          # PAGE UP, hex 0x49 == 73
    "KEY_NEXT": 0x51,           # PAGE DOWN, hex 0x51 == 81
    "KEY_END": 0x4F,            # END, hex 0x4F == 79
    "KEY_HOME": 0x47,           # HOME, hex 0x47 == 71
    "KEY_LEFT": 0x4B,           # LEFT ARROW, hex 0x4B == 75
    "KEY_UP": 0x48,             # UP ARROW, hex 0x48 == 72
    "KEY_RIGHT": 0x4D,          # RIGHT ARROW, hex 0x4D == 77
    "KEY_DOWN": 0x50,           # DOWN ARROW, hex 0x50 == 80

    "KEY_SELECT": None,         # SELECT key (rarely mapped)
    "KEY_PRINT": None,          # PRINT key (ambiguous with Print Screen)
    "KEY_EXECUTE": None,        # EXECUTE key (not standard)
    "KEY_SNAPSHOT": "E0_2A_E0_37",  # PRINT SCREEN (multi-byte sequence)
    "KEY_INSERT": 0x52,         # INS key, hex 0x52 == 82
    "KEY_DELETE": 0x53,         # DEL key, hex 0x53 == 83
    "KEY_HELP": None,           # HELP key (rarely used)

    # Windows keys
    "KEY_LWIN": 0x5B,           # Left Windows key, hex 0x5B == 91
    "KEY_RWIN": 0x5C,           # Right Windows key, hex 0x5C == 92
    "KEY_APPS": 0x5D,           # Applications key, hex 0x5D == 93
    "KEY_SLEEP": None,

    # Numeric keypad keys (assuming Num Lock is ON; many share codes with navigation keys)
    "KEY_NUMPAD0": 0x52,        # Numpad 0, same as Insert (82)
    "KEY_NUMPAD1": 0x4F,        # Numpad 1, same as End (79)
    "KEY_NUMPAD2": 0x50,        # Numpad 2, same as Down Arrow (80)
    "KEY_NUMPAD3": 0x51,        # Numpad 3, same as Page Down (81)
    "KEY_NUMPAD4": 0x4B,        # Numpad 4, same as Left Arrow (75)
    "KEY_NUMPAD5": 0x4C,        # Numpad 5, hex 0x4C == 76
    "KEY_NUMPAD6": 0x4D,        # Numpad 6, same as Right Arrow (77)
    "KEY_NUMPAD7": 0x47,        # Numpad 7, same as Home (71)
    "KEY_NUMPAD8": 0x48,        # Numpad 8, same as Up Arrow (72)
    "KEY_NUMPAD9": 0x49,        # Numpad 9, same as Page Up (73)
    "KEY_MULTIPLY": 0x37,       # Numpad Multiply, hex 0x37 == 55
    "KEY_ADD": 0x4E,            # Numpad Add, hex 0x4E == 78
    "KEY_SEPARATOR": None,
    "KEY_SUBTRACT": 0x4A,       # Numpad Subtract, hex 0x4A == 74
    "KEY_DECIMAL": 0x53,        # Numpad Decimal, same as Delete (83)
    "KEY_DIVIDE": 0x35,         # Numpad Divide (with E0), hex 0x35 == 53

    # Function keys
    "KEY_F1": 0x3B,             # F1, hex 0x3B == 59
    "KEY_F2": 0x3C,             # F2, hex 0x3C == 60
    "KEY_F3": 0x3D,             # F3, hex 0x3D == 61
    "KEY_F4": 0x3E,             # F4, hex 0x3E == 62
    "KEY_F5": 0x3F,             # F5, hex 0x3F == 63
    "KEY_F6": 0x40,             # F6, hex 0x40 == 64
    "KEY_F7": 0x41,             # F7, hex 0x41 == 65
    "KEY_F8": 0x42,             # F8, hex 0x42 == 66
    "KEY_F9": 0x43,             # F9, hex 0x43 == 67
    "KEY_F10": 0x44,            # F10, hex 0x44 == 68
    "KEY_F11": 0x57,            # F11, hex 0x57 == 87
    "KEY_F12": 0x58,            # F12, hex 0x58 == 88
    "KEY_F13": 0x64,            # F13, hex 0x64 == 100 (if available)
    "KEY_F14": 0x65,            # F14, hex 0x65 == 101 (if available)
    "KEY_F15": 0x66,            # F15, hex 0x66 == 102 (if available)
    "KEY_F16": 0x67,            # F16, hex 0x67 == 103 (if available)
    "KEY_F17": 0x68,            # F17, hex 0x68 == 104 (if available)
    "KEY_F18": 0x69,            # F18, hex 0x69 == 105 (if available)
    "KEY_F19": 0x6A,            # F19, hex 0x6A == 106 (if available)
    "KEY_F20": 0x6B,            # F20, hex 0x6B == 107 (if available)
    "KEY_F21": 0x6C,            # F21, hex 0x6C == 108 (if available)
    "KEY_F22": 0x6D,            # F22, hex 0x6D == 109 (if available)
    "KEY_F23": 0x6E,            # F23, hex 0x6E == 110 (if available)
    "KEY_F24": 0x76,            # F24, hex 0x76 == 118 (if available)

    "KEY_NUMLOCK": 0x45,        # NUM LOCK, hex 0x45 == 69
    "KEY_SCROLL": 0x46,         # SCROLL LOCK, hex 0x46 == 70

    # Specific modifier keys (left/right)
    "KEY_LSHIFT": 0x2A,         # Left SHIFT, hex 0x2A == 42
    "KEY_RSHIFT": 0x36,         # Right SHIFT, hex 0x36 == 54
    "KEY_LCONTROL": 0x1D,       # Left CONTROL, hex 0x1D == 29
    "KEY_RCONTROL": 0x1D,       # Right CONTROL (with E0), hex 0x1D == 29
    "KEY_LMENU": 0x38,          # Left ALT, hex 0x38 == 56
    "KEY_RMENU": 0x38,          # Right ALT (with E0), hex 0x38 == 56

    # Extended/system keys (if available)
    "KEY_BROWSER_BACK": None,
    "KEY_BROWSER_FORWARD": None,
    "KEY_BROWSER_REFRESH": None,
    "KEY_BROWSER_STOP": None,
    "KEY_BROWSER_SEARCH": None,
    "KEY_BROWSER_FAVORITES": None,
    "KEY_BROWSER_HOME": None,
    "KEY_VOLUME_MUTE": None,
    "KEY_VOLUME_DOWN": None,
    "KEY_VOLUME_UP": None,
    "KEY_MEDIA_NEXT_TRACK": None,
    "KEY_MEDIA_PREV_TRACK": None,
    "KEY_MEDIA_STOP": None,
    "KEY_MEDIA_PLAY_PAUSE": None,
    "KEY_LAUNCH_MAIL": None,
    "KEY_LAUNCH_MEDIA_SELECT": None,
    "KEY_LAUNCH_APP1": None,
    "KEY_LAUNCH_APP2": None,

    # OEM keys (whose use/placement may vary)
    "KEY_OEM_1": 0x27,          # OEM 1, hex 0x27 == 39  (';:' on US keyboards)
    "KEY_OEM_PLUS": 0x0D,       # OEM Plus, hex 0x0D == 13 ('=' key; Shift gives '+')
    "KEY_OEM_COMMA": 0x33,      # OEM Comma, hex 0x33 == 51 (',' key)
    "KEY_OEM_MINUS": 0x0C,      # OEM Minus, hex 0x0C == 12 ('-' key)
    "KEY_OEM_PERIOD": 0x34,     # OEM Period, hex 0x34 == 52 ('.' key)
    "KEY_OEM_2": 0x35,          # OEM 2, hex 0x35 == 53 ('/?' on US keyboards)
    "KEY_OEM_3": 0x29,          # OEM 3, hex 0x29 == 41 ('`~' on US keyboards)
    "KEY_OEM_4": 0x1A,          # OEM 4, hex 0x1A == 26 ('[{' on US keyboards)
    "KEY_OEM_5": 0x2B,          # OEM 5, hex 0x2B == 43 ('\\|' on US keyboards)
    "KEY_OEM_6": 0x1B,          # OEM 6, hex 0x1B == 27 (']}' on US keyboards)
    "KEY_OEM_7": 0x28,          # OEM 7, hex 0x28 == 40 (single-quote/double-quote on US keyboards)
    "KEY_OEM_8": None,
    "KEY_OEM_102": None,

    # Other keys not normally mapped directly
    "KEY_PROCESSKEY": None,
    "KEY_PACKET": None,
    "KEY_ATTN": None,
    "KEY_CRSEL": None,
    "KEY_EXSEL": None,
    "KEY_EREOF": None,
    "KEY_PLAY": None,
    "KEY_ZOOM": None,
    "KEY_PA1": None,
    "KEY_OEM_CLEAR": None,
    # Dictionary for alphanumeric keys (top row digits and QWERTY letters)
    # Number row (digits)
    "KEY_1": 0x02,  # 0x02 == 2
    "KEY_2": 0x03,  # 0x03 == 3
    "KEY_3": 0x04,  # 0x04 == 4
    "KEY_4": 0x05,  # 0x05 == 5
    "KEY_5": 0x06,  # 0x06 == 6
    "KEY_6": 0x07,  # 0x07 == 7
    "KEY_7": 0x08,  # 0x08 == 8
    "KEY_8": 0x09,  # 0x09 == 9
    "KEY_9": 0x0A,  # 0x0A == 10
    "KEY_0": 0x0B,  # 0x0B == 11

    # Alphabet keys (letters)
    "KEY_A": 0x1E,  # 0x1E == 30
    "KEY_B": 0x30,  # 0x30 == 48
    "KEY_C": 0x2E,  # 0x2E == 46
    "KEY_D": 0x20,  # 0x20 == 32
    "KEY_E": 0x12,  # 0x12 == 18
    "KEY_F": 0x21,  # 0x21 == 33
    "KEY_G": 0x22,  # 0x22 == 34
    "KEY_H": 0x23,  # 0x23 == 35
    "KEY_I": 0x17,  # 0x17 == 23
    "KEY_J": 0x24,  # 0x24 == 36
    "KEY_K": 0x25,  # 0x25 == 37
    "KEY_L": 0x26,  # 0x26 == 38
    "KEY_M": 0x32,  # 0x32 == 50
    "KEY_N": 0x31,  # 0x31 == 49
    "KEY_O": 0x18,  # 0x18 == 24
    "KEY_P": 0x19,  # 0x19 == 25
    "KEY_Q": 0x10,  # 0x10 == 16
    "KEY_R": 0x13,  # 0x13 == 19
    "KEY_S": 0x1F,  # 0x1F == 31
    "KEY_T": 0x14,  # 0x14 == 20
    "KEY_U": 0x16,  # 0x16 == 22
    "KEY_V": 0x2F,  # 0x2F == 47
    "KEY_W": 0x11,  # 0x11 == 17
    "KEY_X": 0x2D,  # 0x2D == 45
    "KEY_Y": 0x15,  # 0x15 == 21
    "KEY_Z": 0x2C   # 0x2C == 44
}