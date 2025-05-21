# theme.py
import tkinter as tk
from tkinter import ttk
from colorsys import rgb_to_hls, hls_to_rgb

def adjust(hex_color: str, factor: float) -> str:
    """Return a lighter (factor>1) or darker (factor<1) version of hex_color."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    h, l, s = rgb_to_hls(r, g, b)
    l = max(0, min(1, l * factor))
    r, g, b = hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

# ---- your new palette ----
BASE        = "#0D0019"  # Ultra-Dark Purple background
SURFACE     = "#2E003E"  # Deep Purple panels
ACCENT_RED  = "#7F001F"  # Crimson Red buttons, highlights
ACCENT_BLUE = "#001F7F"  # Sapphire Blue secondary highlights
HIGHLIGHT   = "#5A2E8A"  # Violet Highlight on hover
BORDER      = "#1A0026"  # Indigo border lines

FG_PRIMARY   = "#E0D4FF"  # Light Lavender text
FG_SECONDARY = "#8E7DAF"  # Muted Gray-Purple subtext

# lighter/darker variants if needed
BG_DARK   = adjust(BASE, 0.8)
BG_LIGHT  = adjust(BASE, 1.2)
ACC_RED_HOV  = adjust(ACCENT_RED, 1.2)
ACC_BLUE_HOV = adjust(ACCENT_BLUE, 1.2)

BOLD_FONT = ("Arial", 10, "bold")

def apply_theme(root: tk.Tk | tk.Toplevel) -> None:
    style = ttk.Style(root)
    style.theme_use('alt')
    style.theme_create(
        "DeepPurple",
        parent="alt",
        settings={
            "TFrame":      {"configure": {"background": SURFACE}},
            "Bordered.TFrame": {
              "configure": {
                "background": SURFACE,
                "borderwidth": 2,
                "bordercolor":  BORDER,
                "relief": "solid",
                "font": BOLD_FONT,
              }
            },
            "Right.TFrame": {"configure": {"background": BASE}},
            "TLabel":      {"configure": {"background": SURFACE, "foreground": FG_SECONDARY, "font": BOLD_FONT}},
            "Bordered.TLabel": {
                "configure": {
                    "background": SURFACE,
                    "borderwidth": 2,
                    "bordercolor": "white",
                    "relief": "solid",
                    "font": BOLD_FONT,
                    "padding": (4,2),
                }
            },
            "TButton":     {
                "configure": {
                    "background": ACCENT_RED,
                    "foreground": FG_PRIMARY,
                    "focuscolor": HIGHLIGHT,
                    "padding": 5,
                    "anchor" : "center",  # center the label in the button’s area
                    "justify" : "center",  # center multi-line text
                },

                "map": {
                    "background": [("active", ACC_RED_HOV)],
                    "foreground": [("disabled", "#555555")]
                }
            },
            # example: a special “Blue” button style
            "Icon.TButton": {
                "configure": {
                    "background": SURFACE,
                    "foreground": FG_SECONDARY,
                    "bordercolor": BORDER,
                    "borderwidth": 2,
                    "focuscolor": ACCENT_BLUE,
                    "padding": (10, 6),
                },
                "map": {
                    "background": [
                        ("disabled", "#555555"),
                        ("pressed", BG_DARK),
                        ("active", ACC_BLUE_HOV)

                    ],
                    "relief": [("pressed", "sunken")],
                    "foreground": [
                        ("disabled", FG_PRIMARY)
                    ]}
            },
            "Blue.TButton": {
                "configure": {
                    "background": ACCENT_BLUE,
                    "foreground": FG_SECONDARY,
                    "bordercolor": BORDER,
                    "borderwidth": 2,
                    "focuscolor": ACCENT_BLUE,
                    "padding": (10,6),
                },
                "map": {
                    "background": [
                        ("disabled", "#555555"),
                        ("pressed",   BG_DARK),
                        ("active",    ACC_BLUE_HOV)

                      ],
                    "relief" : [("pressed", "sunken")],
                    "foreground": [
                        ("disabled", FG_PRIMARY)
                      ]}
            },
            "Vertical.TScrollbar":{
                "configure": {
                    "troughcolor" : BASE,  # the “track” background
                    "background" : SURFACE,  # the draggable thumb fill
                    "bordercolor" : BORDER,  # thumb outline
                    "arrowcolor" : FG_PRIMARY,  # arrow glyphs at ends
                    "gripcount" : 0,  # no little grip dots
                    "relief" : "flat",  # flat look
                    "width" : 12,  # width in pixels
                },
                "map":{
                    "background" : [("active", HIGHLIGHT)],  # thumb on hover
                    "troughcolor" : [("active", BG_LIGHT)],
                    },
            },
            "TNotebook": {
              "configure": {
                   "background": SURFACE,
                   "tabmargins": [2, 2, 2, 0],
                                                 # space around the tab area
                    }
                },
            "TNotebook.Tab": {
               "configure": {
                   "padding": [12, 6],  # x/y padding inside each tab
                   "font": BOLD_FONT,
                    },
               "map": {
                   "background": [("selected", BASE)],
                   "foreground": [("selected", FG_PRIMARY)]
                }
            },
            "TEntry": {
                "configure": {
                    "fieldbackground": SURFACE,  # the panel‐color fill
                    "foreground": FG_PRIMARY,  # the text color
                    "bordercolor": BORDER,  # thin border
                    "borderwidth": 1,
                    "relief": "solid",
                    "padding": (4, 2),  # x/y padding inside the box
                    "font": BOLD_FONT,
                    "insertbackground": HIGHLIGHT,
                },
                "map": {
                   "fieldbackground": [
                       ("disabled", BG_DARK),
                       ("focus", BG_LIGHT),
                       ("!disabled", SURFACE)
                   ],
                   "foreground": [
                       ("disabled", FG_SECONDARY)
                   ]
                }
            },
            "TCheckbutton": {
               "configure": {
                   "background": SURFACE,  # panel-color fill
                   "foreground": FG_PRIMARY,  # label text
                   "font": BOLD_FONT,
                   "padding": (4, 2),  # space around indicator+text
                   "focuscolor": HIGHLIGHT,  # focus ring color
                    },
               "map": {
                    "background": [
                        ("active", BG_LIGHT),
                        ("!active", SURFACE)
                    ],
                    "foreground": [
                        ("disabled", FG_SECONDARY),
                        ("selected", FG_PRIMARY)
                    ],
                    # color of the little tick/indicator when checked
                    "indicatorcolor": [
                        ("selected", ACCENT_BLUE),
                        ("!selected", FG_SECONDARY)
                    ]
                },
            }
        }
    )
    style.theme_use("DeepPurple")

    root.option_add("*Background", BASE)
    root.option_add("*Foreground", FG_SECONDARY)

    root.option_add("*Button.Foreground", FG_PRIMARY)
    root.option_add("*Button.Background", ACCENT_RED)
    root.option_add("*Button.ActiveBackground", HIGHLIGHT)

    root.option_add("*Canvas.background", BASE)
    root.option_add("*Canvas.highlightthickness", 0)
    root.option_add("*Canvas.borderwidth", 0)

    # make all tk.Text widgets pick up your colors/fonts:
    root.option_add("*Text.Background", BASE)
    root.option_add("*Text.Foreground", FG_PRIMARY)
    root.option_add("*Text.InsertBackground", BASE)
    root.option_add("*Text.SelectBackground", HIGHLIGHT)
    root.option_add("*Text.SelectForeground", FG_PRIMARY)
    root.option_add("*Text.HighlightBackground", BORDER)
    root.option_add("*Text.HighlightColor", ACCENT_BLUE)
    root.option_add("*Text.Font", BOLD_FONT)
    root.option_add("*Text.BorderWidth", 0)
    root.option_add("*Text.HighlightThickness", 1)


def make_action_button(parent, text, command):
    btn = tk.Button(
        parent,
        text=text,
        wraplength=250,        # built‐in wrap support
        justify="center",
        bg=ACCENT_RED,         # normal background
        fg=FG_PRIMARY,         # normal text
        activebackground=ACC_RED_HOV,  # when clicked or active
        activeforeground=FG_PRIMARY,
        bd=0,                  # no border by default
        padx=5, pady=2,
        relief="flat",         # flat look
        highlightthickness=0,  # no focus ring
        command=command
    )

    # optional: custom hover color instead of activebackground
    def on_enter(e):
        e.widget.config(bg=ACC_RED_HOV)
    def on_leave(e):
        e.widget.config(bg=ACCENT_RED)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    return btn