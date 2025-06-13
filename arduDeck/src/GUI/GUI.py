import json
import os
import queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from src.client_model.network_client import NetworkClient
from src.server_params import MAX_BUTTONS, MAX_FOLDER_BUTTONS, logger
from src.utils.client_utils import get_client
from src.basic_comms import prepare_swap
from src.utils.data_format import gui_queue
from src.GUI.macro_rec import KeyRecorder, rec_callback
from src.utils.btn_funcs import gui_upload, button_lock, soft_upload, CONFIG_FILE, FOLDER_CONFIG_PATH
from src.GUI.themes import apply_theme, make_action_button, BASE, SURFACE
from src.utils.serial_helper import check_port_presence
import copy
#todo add id checking for add and update func

COMMAND_TYPES = ["SOFT_KEY_PRESS", "HARD_KEY_PRESS",  "START_URL", "START_PROCESS", "TOGGLE_ACTIONS"]


def get_folder_path(btn_info):
    if btn_info['button_id'] < MAX_BUTTONS:
        return CONFIG_FILE
    else:
        return f'{FOLDER_CONFIG_PATH}/{int(btn_info['button_id']) // 100 - 1}.json'


def select_image():
    # Open a file dialog to select a .jpg file.
    path = filedialog.askopenfilename(title="Select an Image",
                                      filetypes=[("JPEG Files", "*.jpg")])
    if path:
        if not path.lower().endswith(".jpg"):
            messagebox.showerror("Invalid File", "Please select a file with a .jpg extension.")
            return None
        logger.debug("Selected image: %s", path)  # Debug print
        return path
    return None

def immediate_update(btn_list : list, in_folder : bool = False, folder_list: list = None, folder_path: str = None):
    if in_folder:
        soft_upload(btn_list=None, folder_list=folder_list, folder_config=folder_path)
    else:
        soft_upload(btn_list=btn_list)

def gui_client_swap():
    current_client = get_client()
    if current_client is None or isinstance(current_client, NetworkClient) and current_client.sock is None:
        messagebox.showerror(title="Swap Request Error",
                             message="Cannot swap mode when client is uninitialized. Please try again later.")
        logger.warning("Client is none, aborting swap")
        return
    else:
        if isinstance(current_client, NetworkClient) and not check_port_presence():
            logger.warning("Serial swap requested but cable not connected, aborting swap")
            messagebox.showerror(title="Swap Request error",
                                 message="Connect serial cable before requesting client type swap!")
            return
        prepare_swap(current_client)

class StreamDeckGUI(tk.Tk):
    def __init__(self, button_list):
        super().__init__()
        apply_theme(self)
        self.folder_check_btn = None
        self.open_folder_button = None
        self._last_add_win = None
        self.status_label = None
        self.add_button_btn = None
        self.upload_btn = None
        self.button_frame = None
        self.canvas_window = None
        self.canvas = None
        self.page_label = None
        self.scrollbar = None
        self.info_frame = None
        #folder info
        self.folder_idx = -1
        self.in_folder = False
        #list of files that will need to be uploaded
        self.change_log = []

        self.client = get_client()
        self.geometry("{}x{}".format(1400, 600))
        self.minsize(1400, 600)
        self.title("ArduDeck HUB")
        self.button_list = button_list
        self.folder_list = []

        # Create a button map to have O(1) time of accessing a button
        self.folder_map = {}
        self.btn_map = {}
        for index in range(len(self.button_list)):
            self.btn_map[self.button_list[index]["button_id"]] = self.button_list[index]

        # Hard coded button grid format
        self.ROWS = 3
        self.COLS = 5
        self.current_page = 0
        total_cells = self.ROWS * self.COLS
        self.max_pages = max(button["button_id"] for button in self.button_list) // total_cells

        # Shortcuts for adding a button and quitting program
        # self.bind("<KeyPress-a>", lambda event: self.add_button_window())
        # self.bind("<KeyPress-q>", lambda event: self.quit())
        # self.bind("<Shift-KeyRelease>", lambda event: self.macro_rec_window())

        # Use grid to divide the window equally into left and right.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ttk.Frame(self, style="TFrame")
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = ttk.Frame(self, style="Right.TFrame")
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.create_left_frame()
        # Right frame: create a scrollable canvas.
        self.create_right_frame()
        self.create_button_grid()
        self.receive_queued_gui_updates()

    def receive_queued_gui_updates(self):
        try:
            while True:
                update = gui_queue.get_nowait()
                # logger.debug(f"Got update: {update}")
                if update.startswith("[FAIL]"):
                    fg = "red"
                elif update.startswith("[OK]"):
                    fg = "lime green"
                else:
                    fg = "blue"

                contents = update.split(']', 1)[1]
                # logger.debug(contents)
                self.status_label.config(
                    text=f"Status: {contents}",
                    foreground=fg
                )
        except queue.Empty:
            pass

        self.after(1000, self.receive_queued_gui_updates)

    def create_left_frame(self):
        # Page navigation 
        nav_frame = ttk.Frame(self.left_frame, height=30, style="TFrame")
        nav_frame.pack(fill=tk.X, pady=5)

        ttk.Button(nav_frame, text="◀", command=self.prev_page, style="TButton").place(relx=.40, rely=.5, anchor="center")

        self.page_label = ttk.Label(nav_frame, text="Page 0", style="TLabel")
        self.page_label.place(relx=.5, rely=.5, anchor="center")

        ttk.Button(nav_frame, text="▶", command=self.next_page, style="TButton").place(relx=.60, rely=.5, anchor="center")

        # Button grid container
        self.button_frame = ttk.Frame(self.left_frame, style="Right.TFrame")
        self.button_frame.pack(padx=10, pady=10)

        # self.add_button_btn = ttk.Button(self.left_frame,
        #                                  text="Add Button",
        #                                  command=self.add_button_window,
        #                                  style="Blue.TButton")
        # self.add_button_btn.pack(pady=5)
        bottom_frame = ttk.Frame(self.left_frame, style="TFrame")
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=0)
        bottom_frame.grid_columnconfigure(2, weight=1)
        container_frame = ttk.Frame(bottom_frame, style="TFrame")
        container_frame.grid(row=0, column=1)

        swap_btn = ttk.Button(
            container_frame,
            text="Swap Mode",
            style="TButton",
            command=gui_client_swap
        )
        swap_btn.pack(side="left")

        self.status_label = ttk.Label(
            container_frame,
            text="Status: —",
            style="TLabel" #can be bordered too
        )
        self.status_label.pack(side="left", padx=(10,0))

    def create_right_frame(self):
        # Configure right_frame to have two rows: one for the canvas (expandable) and one for the fixed upload button.
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=0)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Create the canvas for the scrollable info_frame.
        self.canvas = tk.Canvas(self.right_frame,
                                bg=BASE,  # panel background
                                bd=0,  # no border
                                highlightthickness=0,  # no focus-ring
                                relief="flat"  # flat look
                                )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Create a vertical scrollbar for the canvas.
        self.scrollbar = ttk.Scrollbar(self.right_frame,
                                       orient="vertical",
                                       command=self.canvas.yview,
                                       style="Vertical.TScrollbar")

        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the info widgets.
        self.info_frame = ttk.Frame(self.canvas, style="Bordered.TFrame")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.info_frame, anchor="nw")

        # Bind the configuration event to update the scroll region.
        self.info_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", lambda ev: self.canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        # Create the upload button in a fixed row (row 1) of right_frame.
        self.upload_btn = ttk.Button(self.right_frame, text="Upload Changes", command=self.upload_changes, style="TButton")
        self.upload_btn.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # def _on_mousewheel(self, event, canvas):
    #     canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_button_grid(self):
        # Clear previous grid if it exists
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if self.in_folder:
            current_page = 0
            btn_map = self.folder_map
        else:
            current_page = self.current_page
            btn_map = self.btn_map

        total_cells = self.ROWS * self.COLS
        index_start = current_page * total_cells
        for i in range(total_cells):
            row = i // self.COLS
            col = i % self.COLS
            global_idx = index_start + i
            # If button of given id exists then draw it
            if global_idx in btn_map.keys():
                button = btn_map[global_idx]
                image_path = button["image_path"]
                target_px = 100
                img = Image.open(image_path).resize((target_px, target_px), Image.Resampling.LANCZOS)
                image = ImageTk.PhotoImage(img)

                text = f"Button {button['button_id']}"
                # Create a button
                btn = ttk.Button(self.button_frame,
                                text=text,
                                image = image,
                                compound="top",
                                style="Icon.TButton",
                                command=lambda info=button: self.on_button_click(info))
                btn.grid(row=row, column=col, padx=5, pady=5)
                btn.image = image
            else:
                # Else draw an empty button placeholder
                placeholder = ttk.Button(self.button_frame,
                                    text="Empty",
                                    width=10,
                                    command=lambda idx = i: self.add_button_window(self.folder_idx, idx),
                                    style="Icon.TButton")
                placeholder.grid(row=row, column=col, padx=15, pady=57)


    def on_button_click(self, btn_info):
        # When a non-empty button is pressed, display its info in the right info_frame.
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.info_frame, text=f"Button: {btn_info.get('button_id', 'Unknown')}",
                               font=("Arial", 12), style="TLabel")
        title_label.pack(pady=5, padx=5, anchor="w")

        # Provide options: Add Action and Delete Button
        action_btn_frame = ttk.Frame(self.info_frame, style="TFrame")
        action_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        (ttk.Button(action_btn_frame, style="TButton",
                   text="Add Action",
                   command=lambda: self.action_window(btn_info=btn_info))
         .pack(side=tk.LEFT, padx=5))
        (ttk.Button(action_btn_frame,
                   style="TButton",
                   text="Delete Button",
                   command=lambda: self.delete_button(btn_info))
         .pack(side=tk.LEFT, padx=5))
        #create open folder option in case we are not already in a folder
        if not self.in_folder:
            self.open_folder_button = ttk.Button(
                action_btn_frame, style="TButton",
                text="Open Folder",
                command=lambda: self.open_folder_grid(btn_info)
            )
            self.open_folder_button.pack(side=tk.LEFT, padx=5)
            #checkbox state variable
            flag_var = tk.IntVar(value=btn_info.get("folder_flag", 0))

            def _toggle_folder():
                new_val = flag_var.get()
                btn_info["folder_flag"] = new_val
                # optionally persist or inform server here
                soft_upload(btn_list = self.button_list)
                logger.debug(f"folder_flag for {btn_info['button_id']} is {new_val}")

                if new_val:
                    self.open_folder_button.pack(side=tk.LEFT, padx=5, before=self.folder_check_btn)
                else:
                    self.open_folder_button.pack_forget()

                self.add_to_changelog(CONFIG_FILE)

            if not flag_var.get():
                self.open_folder_button.pack_forget()

            self.folder_check_btn=ttk.Checkbutton(
                action_btn_frame,
                text="Enable Folder",
                style="TCheckbutton",
                variable=flag_var,
                command=_toggle_folder
            )
            self.folder_check_btn.pack(side=tk.LEFT, padx=5)
        # Display existing actions
        actions_header = ttk.Label(self.info_frame, text="Actions:", font=("Arial", 10, "underline"), style="TLabel")
        actions_header.pack(pady=(10,5), padx=5, anchor="w")

        # List actions
        with button_lock:
            actions = btn_info.get("actions", [])

        if actions:
            for action in actions:
                action_text = f"Command: {action.get('command_id', 'N/A')}\nArgs: {action.get('command_args', [])}"
                act_btn = make_action_button(
                    self.info_frame,
                    text=action_text,
                    command=lambda a=action, i=btn_info: self.action_window(action=a, btn_info=i)
                )
                act_btn.pack(fill=tk.X, padx=5, pady=2, anchor="center")
        else:
            no_act_label = ttk.Label(self.info_frame, text="No Actions Assigned", style="TLabel")
            no_act_label.pack(pady=5, padx=5, anchor="w")

        # Display Image Path
        img_btn = ttk.Button(self.info_frame, text=f"Image Path: {btn_info.get('image_path', 'N/A')}",
                            style="TButton",
                            command=lambda: self.update_image_path(btn_info))
        img_btn.pack(pady=5, padx=5, fill=tk.X, anchor="w")

        self.canvas.yview_moveto(0.0)

    def open_folder_grid(self, btn_info):
        self.folder_idx = int(btn_info.get("button_id"))
        config_file = f"{FOLDER_CONFIG_PATH}/{self.folder_idx}.json"

        try:
            with open(config_file, "r") as f:
                folder_button_list = json.load(f)
        except FileNotFoundError:
            logger.warning("Config not found, creating it")
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, "w") as f:
                json.dump([], f, indent=2)
            folder_button_list = []

        self.in_folder = True
        self.folder_list = folder_button_list
        self.folder_map = {b["button_id"]%100: b for b in self.folder_list}
        self.create_button_grid()
        #completely clear right frame
        for child in self.right_frame.winfo_children():
            child.destroy()
        self.create_right_frame()

    def update_image_path(self, btn_info):
        new_path = select_image()
        if new_path:
            with button_lock:
                btn_info["image_path"] = new_path
            self.on_button_click(btn_info)
            change_log_file = get_folder_path(btn_info)
            self.add_to_changelog(change_log_file)

    def _start_macro_record(self, target_text_widget):

        self.withdraw()

        if hasattr(self, "_last_add_win") and self._last_add_win.winfo_exists():
            self._last_add_win.withdraw()

        def on_done(history_json, macro_string):
            # put the recorded JSON back into your Text widget
            target_text_widget.delete("1.0", tk.END)
            target_text_widget.insert("1.0", macro_string)

            # show both windows again
            self.deiconify()
            if hasattr(self, "_last_add_win") and self._last_add_win.winfo_exists():
                self._last_add_win.deiconify()

        KeyRecorder(self, on_done)

    def action_window(self, btn_info, action=None):
        win = tk.Toplevel(self)
        self._last_add_win = win
        win.title("Add Action")
        win.geometry("900x600")
        win.transient(self)
        win.grab_set()
        # win.focus_force()
        container = ttk.Frame(win, style="Right.TFrame")
        container.pack(fill="both", expand=True)
        notebook = ttk.Notebook(container, style="TNotebook")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        #SOFT_KEY_PRESS tab
        soft_frame = ttk.Frame(notebook, style="TFrame")
        notebook.add(soft_frame, text="SOFT_KEY_PRESS")
        ttk.Label(soft_frame, text="Soft Key Sequence:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        soft_text = tk.Text(soft_frame, height=3, wrap="word")
        soft_text.pack(fill="x", padx=5, pady=5)
        soft_btn = ttk.Button(
            soft_frame,
            text="Record…",
            command=lambda: self._start_macro_record(soft_text),
            style="TButton"
        )
        soft_btn.pack(padx=5)

        # HARD_KEY_PRESS tab
        hard_frame = ttk.Frame(notebook)
        notebook.add(hard_frame, text="HARD_KEY_PRESS")
        ttk.Label(hard_frame, text="Hard Key Code(s):", anchor="w").pack(anchor="w", padx=5, pady=(5, 0))
        hard_entry = tk.Entry(hard_frame, font=('Arial', 10, 'bold'))
        hard_entry.pack(fill="x", padx=5, pady=5)

        # START_URL tab
        url_frame = ttk.Frame(notebook)
        notebook.add(url_frame, text="START_URL")
        ttk.Label(url_frame, text="URL to open:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        url_entry = tk.Entry(url_frame, font=('Arial', 10, 'bold'))
        url_entry.pack(fill="x", padx=5, pady=5)

        # START_PROCESS tab
        proc_frame = ttk.Frame(notebook)
        notebook.add(proc_frame, text="START_PROCESS")
        ttk.Label(proc_frame, text="Executable path:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        proc_var = tk.StringVar()
        proc_entry = tk.Entry(proc_frame, textvariable=proc_var, font=('Arial', 10, 'bold'))
        proc_entry.pack(fill="x", padx=5, pady=5)
        ttk.Button(proc_frame, text="Browse…", style="TButton",
                  command=lambda: proc_var.set(filedialog.askopenfilename(
                      title="Select EXE", filetypes=[("EXE", "*.exe"), ("All", "*.*")]) or "")
                  ).pack(padx=5)
        # TOGGLE_ACTIONS tab
        toggle_frame = ttk.Frame(notebook)
        toggle_canvas = tk.Canvas(toggle_frame, background=SURFACE, bd=0, highlightthickness=0)
        toggle_scroll = ttk.Scrollbar(toggle_frame, orient="vertical", command=toggle_canvas.yview,
                                      style="Vertical.TScrollbar")
        toggle_inner = ttk.Frame(toggle_canvas, style="TFrame")

        notebook.add(toggle_frame, text="TOGGLE_ACTIONS")

        # lay out canvas + scrollbar
        toggle_scroll.pack(side="right", fill="y")
        toggle_canvas.pack(side="left", fill="both", expand=True)

        # embed the inner frame in the canvas
        canvas_window = toggle_canvas.create_window((0, 0), window=toggle_inner, anchor="nw")

        toggle_canvas.bind("<Enter>", lambda e: toggle_canvas.bind_all(
            "<MouseWheel>", lambda ev: toggle_canvas.yview_scroll(int(-1*(ev.delta/120)), "units")
        ))
        toggle_canvas.bind("<Leave>", lambda e: toggle_canvas.unbind_all("<MouseWheel>"))

        def on_frame_configure(event):
            toggle_canvas.configure(scrollregion=toggle_canvas.bbox("all"))

        toggle_inner.bind("<Configure>", on_frame_configure)

        # let the canvas grow with the tab
        def on_canvas_configure(event):
            toggle_canvas.itemconfig(canvas_window, width=event.width)

        toggle_canvas.bind("<Configure>", on_canvas_configure)

        def load_selected_actions():
            preselected_items = []
            if action is None or action["command_id"] != "TOGGLE_ACTIONS":
                return preselected_items

            child_actions = action["command_args"]
            preselected_items = child_actions
            return preselected_items

        with button_lock:
            actions = btn_info.setdefault("actions", [])

        selected_actions = load_selected_actions()
        removed_actions = []
        selectable_actions = actions + selected_actions
        # logger.debug("actions = %r, selected = %r, removed = %r", actions, selected_actions, removed_actions)
        for act in selectable_actions:
            if act is action:
                continue
            if act in selected_actions:
                default_val = 1
            else:
                default_val = 0

            var = tk.IntVar(value=act.get("enabled", default_val))

            def _on_toggle(a=act, v=var):
                selected = bool(v.get())

                if selected and a not in selected_actions:
                    selected_actions.append(a)
                    if a in removed_actions:
                        removed_actions.remove(a)

                elif not selected and a in selected_actions:
                    selected_actions.remove(a)
                    if a not in removed_actions:
                        removed_actions.append(a)

                else:
                    pass
                # logger.debug("selected = %r, removed = %r", selected_actions, removed_actions)

            cb = ttk.Checkbutton(
                toggle_inner,
                text=f"{act["command_id"]}: {act['command_args']}",
                variable=var,
                command=_on_toggle,
                style="TCheckbutton"
            )
            cb.pack(anchor="w", padx=5, pady=2)

        # bottom buttons
        btn_frame = ttk.Frame(container, style="Right.TFrame")
        btn_frame.pack(fill="x", pady=10)

        tab_index = 0
        if action:
            try:
                tab_index = COMMAND_TYPES.index(action["command_id"])
            except ValueError:
                tab_index = 0
            notebook.select(tab_index)
            try:
                existing_args = action.get("command_args", [""])[0]
            except IndexError:
                existing_args = []
            if tab_index == 0:
                soft_text.insert("1.0", existing_args)
            elif tab_index == 1:
                hard_entry.insert(0, existing_args)
            elif tab_index == 2:
                url_entry.insert(0, existing_args)
            else:
                proc_var.set(existing_args)

        btn_frame = ttk.Frame(container, style="Right.TFrame")
        btn_frame.pack(fill="x", pady=10)
        for col in (0, 5):
            if col == 0 or col == 5:
                weight = 1
            else:
                weight = 0
            btn_frame.grid_columnconfigure(col, weight=weight)

        def save_action():
            sel = notebook.index(notebook.select())
            cmd_type = COMMAND_TYPES[sel]
            if sel == 0:
                args = [soft_text.get("1.0", "end-1c")]
            elif sel == 1:
                args = [hard_entry.get()]
            elif sel == 2:
                args = [url_entry.get()]
            elif sel == 4:
                # logger.debug("selected = %r, removed = %r, old = %r", selected_actions, removed_actions, btn_info["actions"])
                args = copy.deepcopy(selected_actions)
                with button_lock:
                    old_actions = btn_info["actions"]
                    for a in removed_actions:
                        if a not in old_actions:
                            old_actions.append(a)

                    for a in selected_actions:
                        if a in old_actions:
                            old_actions.remove(a)
            else:
                args = [proc_var.get()]

            if action:
                # Edit in place
                action["command_id"] = cmd_type
                action["command_args"] = args
            else:
                # Add new
                new_action = btn_info.setdefault("actions", [])
                new_action.append({
                    "command_id": cmd_type,
                    "command_args": args
                })
            # soft_upload(self.button_list)
            immediate_update(self.button_list, self.in_folder, self.folder_list, get_folder_path(btn_info))
            self.on_button_click(btn_info)
            win.destroy()

        ttk.Button(btn_frame, text="Save" if action else "Add Action", command=save_action, style="TButton").grid(
            row = 0, column = 1, padx=25)
        # ttk.Button(btn_frame, text="Done", command=win.destroy, style="TButton").pack(side="right", padx=15)

        if action:
            def remove_action():
                btn_info["actions"].remove(action)
                immediate_update(self.button_list, self.in_folder, self.folder_list, get_folder_path(btn_info=btn_info))
                self.on_button_click(btn_info)
                win.destroy()

            ttk.Button(btn_frame, text="Delete", command=remove_action, style="TButton").grid(row=0, column=2, padx=25)

        def move_action(direction:int):
            try:
                idx = btn_info["actions"].index(action)
                n = len(actions)
                target_idx = (idx + direction) % n
                logger.debug("idx will be %d", target_idx)

                temp = btn_info["actions"][target_idx]
                btn_info["actions"][target_idx] = btn_info["actions"][idx]
                btn_info["actions"][idx] = temp

                self.on_button_click(btn_info)
            except ValueError:
                logger.error("action is not present in action list")
        ttk.Button(btn_frame, text="Move up", command= lambda:move_action(direction=-1), style="TButton").grid(row=0, column=3, padx=25, pady = 10)
        ttk.Button(btn_frame, text="Move up", command=lambda:move_action(direction=1), style="TButton").grid(row=0, column=4, padx=25)
    def macro_rec_window(self):
        mrw = KeyRecorder(self, rec_callback)

    def add_button_window(self, folder_idx, btn_pos):
        logger.debug('button pos is %s', btn_pos)
        add_win = tk.Toplevel(self)
        add_win.title("Add New Button")
        add_win.geometry("450x200")
        add_win.transient(self)
        add_win.grab_set()
        add_win.focus_force()
        container = ttk.Frame(add_win, style="TFrame")
        container.pack(fill="both", expand=True)

        # Calculate the maximum allowed button id.
        total_cells = self.ROWS * self.COLS
        max_allowed = (self.max_pages + 2) * total_cells - 1
        max_allowed = min(MAX_BUTTONS, max_allowed)
        
        ttk.Label(container, text="Button Index:", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        button_id_var = tk.StringVar()
        button_id_var.set(btn_pos)
        id_entry = tk.Entry(container, textvariable=button_id_var, font=('Arial', 10, 'bold'))
        id_entry.configure(insertbackground="white")
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(container, text="Image Path:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        image_path_var = tk.StringVar()
        # Instead of letting the user type the path, provide a button to open a file dialog.
        
        (ttk.Button(container, text="Select Image",
                    style="TButton",
                    command=lambda: image_path_var.set(select_image() or ""))
         .grid(row=2, column=1, padx=5, pady=5, sticky="w"))
        # Display the selected path:
        path_label = ttk.Label(container, textvariable=image_path_var, wraplength=300, style="TLabel")
        path_label.grid(row=3, column=1, columnspan=2, padx=5, pady=5)
        
        def add_new_button():
            try:
                bid = int(button_id_var.get())
                if self.in_folder and bid >= MAX_BUTTONS:
                    messagebox.showerror("Error", f"Button ID must be ≤ {MAX_FOLDER_BUTTONS}")
                    return
                elif bid >= max_allowed:
                    messagebox.showerror("Error", f"Button ID must be ≤ {max_allowed}")
                    return
            except ValueError:
                messagebox.showerror("Error", "Button ID must be an integer")
                return
            
            if bid >= self.max_pages * self.ROWS * self.COLS - 1:
                self.max_pages += 1

            img_path = image_path_var.get()
            if not img_path:
                messagebox.showerror("Error", "Please select an image (.jpg) for the button")
                return
            
            if self.folder_idx >= 0:
                bid += 100 * (self.folder_idx + 1)

            new_btn = {
                "button_id": bid,
                "folder_flag": 0,
                "actions": [],
                "image_path": img_path
            }

            folder_path = None
            if self.in_folder:
                self.folder_list.append(new_btn)
                self.folder_map[bid%100] = new_btn
                folder_path = f"{FOLDER_CONFIG_PATH}/{folder_idx}.json"
                self.add_to_changelog(folder_path)
                logger.debug("added folder button")
            else:
                self.button_list.append(new_btn)
                self.btn_map[bid] = new_btn
                self.add_to_changelog(CONFIG_FILE)
                logger.debug("added button")

            immediate_update(btn_list=self.button_list, in_folder=self.in_folder, folder_list=self.folder_list, folder_path=folder_path)

            self.create_button_grid()

            self.action_window(btn_info=new_btn)
            button_id_var.set("")
            image_path_var.set("")
        
        # ttk.Button(container, text="Add", command=add_new_button, style="TButton").grid(row=4, column=0, padx=5, pady=5)
        # add_win.bind("<Return>", lambda event: add_new_button())
        (ttk.Button(container,
                  style="TButton",
                  text="Done",
                  command=lambda:[add_new_button(), add_win.destroy()])
         .grid(row=4, column=0, padx=5, pady=5))

    
    def delete_button(self, btn_info):

        if self.in_folder:
            if btn_info in self.folder_list:
                self.folder_list.remove(btn_info)
                self.folder_map.pop(int(btn_info["button_id"])%100)
                print("deleted folder button!")
        else:
            if btn_info in self.button_list:
                self.button_list.remove(btn_info)
                self.btn_map.pop(btn_info["button_id"])
                print("deleted button!")

        path = get_folder_path(btn_info)
        self.add_to_changelog(path)
        immediate_update(btn_list=self.button_list, in_folder=self.in_folder, folder_list=self.folder_list, folder_path=path)
        self.create_button_grid()
        for widget in self.info_frame.winfo_children():
            widget.destroy()

    def close_folder(self):
        self.in_folder = False
        last_btn = self.btn_map[self.folder_idx]
        self.folder_idx = -1
        self.create_button_grid()
        self.on_button_click(last_btn)

    def prev_page(self):
        if self.in_folder:
            self.close_folder()
            return

        if self.current_page > 0:
            self.current_page -= 1
            self.page_label.config(text=f"Page {self.current_page}")
            self.create_button_grid()

    def next_page(self):
        if self.in_folder:
            self.close_folder()
            return

        if self.current_page < self.max_pages:
            self.current_page += 1
            self.page_label.config(text=f"Page {self.current_page}")
            self.create_button_grid()

    def add_to_changelog(self, file:str):
        logger.debug(f"Adding {file} to changelog")
        self.change_log.append(file)

    def remove_from_changelog(self, file: str, remove_all : bool =False):
        if remove_all:
            self.change_log.clear()
            return
        if file in self.change_log:
            self.change_log.remove(file)

    def upload_changes(self):
        # Call your external function to process/upload changes.
        print("Uploading changes!")
        self.client = get_client()
        if self.client is None:
            print("[ERROR]: Client is none!")
            return None
        # write_updates()
        # print(self.button_list)
        gui_upload(client=self.client, btn_list=self.button_list, change_log=self.change_log)

