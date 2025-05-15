import queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src.server_params import MAX_BUTTONS
from tkinter import filedialog, messagebox
from src.utils.client_utils import get_client
from src.basic_comms import gui_queue, logger
from src.GUI.macro_rec import KeyRecorder, rec_callback
from src.utils.btn_funcs import gui_upload, button_lock, soft_upload
from src.GUI.themes import apply_theme, make_action_button, BASE

#todo add id checking for add and update func
#todo preselect text in command args or register key inputs?

COMMAND_TYPES = ["SOFT_KEY_PRESS", "HARD_KEY_PRESS",  "START_URL", "START_PROCESS"]

class StreamDeckGUI(tk.Tk):
    def __init__(self, button_list):
        super().__init__()
        self.status_label = None
        self.add_button_btn = None
        apply_theme(self)
        self.upload_btn = None
        self.button_frame = None
        self.canvas_window = None
        self.canvas = None
        self.page_label = None
        self.scrollbar = None
        self.info_frame = None

        self.client = get_client()
        self.geometry("{}x{}".format(1200, 600))
        self.minsize(1200, 600)
        self.title("ArduDeck HUB")
        self.button_list = button_list

        # Create a button map to have O(1) time of accessing a button
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
        self.bind("<KeyPress-a>", lambda event: self.open_add_button_window())
        self.bind("<KeyPress-q>", lambda event: self.quit())
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
                if update.startswith("[FAIL]"):
                    fg = "red"
                elif update.startswith("[OK]"):
                    fg = "lime green"
                else:
                    fg = "blue"

                contents = update.split(']', 1)[1]
                logger.debug(contents)
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
        #                                  command=self.open_add_button_window,
        #                                  style="Blue.TButton")
        # self.add_button_btn.pack(pady=5)

        self.status_label = ttk.Label(
            self.left_frame,
            text="Status: —",
            style="TLabel" #can be bordered too
        )
        self.status_label.pack(padx=10, pady=(0, 10))

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


        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Create the upload button in a fixed row (row 1) of right_frame.
        self.upload_btn = ttk.Button(self.right_frame, text="Upload Changes", command=self.upload_changes, style="TButton")
        self.upload_btn.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_button_grid(self):
        # Clear previous grid if it exists
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        total_cells = self.ROWS * self.COLS
        index_start = self.current_page * total_cells
        for i in range(total_cells):
            row = i // self.COLS
            col = i % self.COLS
            global_idx = index_start + i
            # If button of given id exists then draw it
            if global_idx in self.btn_map.keys():
                button = self.btn_map[global_idx]
                image_path = button["image_path"]
                # print("Image path is %s", image_path)
                # image = ImageTk.PhotoImage(Image.open(image_path))
                target_px = 100
                img = Image.open(image_path).resize((target_px, target_px), Image.Resampling.LANCZOS)
                image = ImageTk.PhotoImage(img)

                text = f"Button {global_idx}"
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
                                    command=lambda: self.open_add_button_window(),
                                    style="Icon.TButton")
                placeholder.grid(row=row, column=col, padx=5, pady=5)


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
                   command=lambda: self.add_action_window(btn_info))
         .pack(side=tk.LEFT, padx=5))
        (ttk.Button(action_btn_frame,
                   style="TButton",
                   text="Delete Button",
                   command=lambda: self.delete_button(btn_info))
         .pack(side=tk.LEFT, padx=5))

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
                    command=lambda a=action, i=btn_info: self.edit_action_window(a, i)
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
        
    def update_image_path(self, btn_info):
        # Update image path the image path.
        new_path = self.select_image()
        if new_path:
            # Update button reference information
            with button_lock:
                btn_info["image_path"] = new_path
            # Update the right pane by reloading the current button info.
            self.on_button_click(btn_info)
    
    def select_image(self):
        # Open a file dialog to select a .jpg file.
        path = filedialog.askopenfilename(title="Select an Image",
                                          filetypes=[("JPEG Files", "*.jpg")])
        if path:
            if not path.lower().endswith(".jpg"):
                messagebox.showerror("Invalid File", "Please select a file with a .jpg extension.")
                return None
            print("Selected image:", path)  # Debug print
            return path
        return None


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

    def add_action_window(self, btn_info):
        win = tk.Toplevel(self)
        self._last_add_win = win
        win.title("Add Action")
        win.geometry("800x500")
        win.transient(self)
        win.grab_set()
        # win.focus_force()
        container = ttk.Frame(win, style="Right.TFrame")
        container.pack(fill="both", expand=True)
        notebook = ttk.Notebook(container, style="TNotebook")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 1) Soft Key Press tab
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

        # 2) Hard Key Press tab
        hard_frame = ttk.Frame(notebook)
        notebook.add(hard_frame, text="HARD_KEY_PRESS")
        ttk.Label(hard_frame, text="Hard Key Code(s):", anchor="w").pack(anchor="w", padx=5, pady=(5, 0))
        hard_entry = tk.Entry(hard_frame, font=('Arial', 10, 'bold'))
        hard_entry.pack(fill="x", padx=5, pady=5)

        # 3) Start URL tab
        url_frame = ttk.Frame(notebook)
        notebook.add(url_frame, text="START_URL")
        ttk.Label(url_frame, text="URL to open:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        url_entry = tk.Entry(url_frame, font=('Arial', 10, 'bold'))
        url_entry.pack(fill="x", padx=5, pady=5)

        # 4) Start Process tab
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

        # bottom buttons
        btn_frame = ttk.Frame(container, style="Right.TFrame")
        btn_frame.pack(fill="x", pady=10)

        def add_action():
            tab = notebook.index(notebook.select())
            cmd_type = COMMAND_TYPES[tab]
            if tab == 0:
                args = [soft_text.get("1.0", "end-1c")]
            elif tab == 1:
                args = [hard_entry.get()]
            elif tab == 2:
                args = [url_entry.get()]
            else:
                args = [proc_var.get()]


            actions = btn_info.setdefault("actions", [])
            actions.append({
                "command_id": cmd_type,
                "command_args": args
            })
            soft_upload(self.button_list)

            # refresh right pane
            self.on_button_click(btn_info)
            # clear inputs for next action
            soft_text.delete("1.0", "end")
            hard_entry.delete(0, "end")
            url_entry.delete(0, "end")
            proc_var.set("")


        ttk.Button(btn_frame, text="Add Action", command=add_action, style="TButton").pack(side="left", padx=15)
        ttk.Button(btn_frame, text="Done", command=win.destroy, style="TButton").pack(side="right", padx=15)

    def macro_rec_window(self):
        mrw = KeyRecorder(self, rec_callback)

    def edit_action_window(self, action, btn_info):
        win = tk.Toplevel(self)
        win.title("Edit Action")
        win.geometry("500x300")
        win.transient(self)
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        soft_frame = ttk.Frame(notebook)
        notebook.add(soft_frame, text="SOFT_KEY_PRESS")
        ttk.Label(soft_frame, text="Soft Key Sequence:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        soft_text = tk.Text(soft_frame, height=3, wrap="word")
        soft_text.pack(fill="x", padx=5, pady=5)
        soft_btn = ttk.Button(
            soft_frame,
            style="TButton",
            text="Record…",
            command=lambda: self._start_macro_record(soft_text)
        )
        soft_btn.pack(padx=5)

        hard_frame = ttk.Frame(notebook)
        notebook.add(hard_frame, text="HARD_KEY_PRESS")
        ttk.Label(hard_frame, text="Hard Key Code(s):", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        hard_entry = tk.Entry(hard_frame, font=('Arial', 10, 'bold'))
        hard_entry.pack(fill="x", padx=5, pady=5)

        url_frame = ttk.Frame(notebook)
        notebook.add(url_frame, text="START_URL")
        ttk.Label(url_frame, text="URL to open:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        url_entry = tk.Entry(url_frame, font=('Arial', 10, 'bold'))
        url_entry.pack(fill="x", padx=5, pady=5)

        proc_frame = ttk.Frame(notebook)
        notebook.add(proc_frame, text="START_PROCESS")
        ttk.Label(proc_frame, text="Executable path:", anchor="w", style="TLabel").pack(anchor="w", padx=5, pady=(5, 0))
        proc_var = tk.StringVar()
        proc_entry = tk.Entry(proc_frame, textvariable=proc_var, font=('Arial', 10, 'bold'))
        proc_entry.pack(fill="x", padx=5, pady=5)
        tk.Button(proc_frame, text="Browse…",
                  command=lambda: proc_var.set(filedialog.askopenfilename(
                      title="Select EXE",
                      filetypes=[("EXE", "*.exe"), ("All", "*.*")]) or "")
                  ).pack(padx=5)

        # Pre‐select the right tab and populate fields from `action`
        try:
            tab_index = COMMAND_TYPES.index(action["command_id"])
        except ValueError:
            tab_index = 0
        notebook.select(tab_index)

        # fill the right widget
        existing_args = action.get("command_args", [""])[0]
        if tab_index == 0:
            soft_text.insert("1.0", existing_args)
        elif tab_index == 1:
            hard_entry.insert(0, existing_args)
        elif tab_index == 2:
            url_entry.insert(0, existing_args)
        else:
            proc_var.set(existing_args)


        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", pady=10)

        # Save / update action in place
        def save_action():
            sel = notebook.index(notebook.select())
            cmd_type = COMMAND_TYPES[sel]
            if sel == 0:
                args = [soft_text.get("1.0", "end-1c")]
            elif sel == 1:
                args = [hard_entry.get()]
            elif sel == 2:
                args = [url_entry.get()]
            else:
                args = [proc_var.get()]

            action["command_id"] = cmd_type
            action["command_args"] = args
            soft_upload(self.button_list)

            self.on_button_click(btn_info)
            win.destroy()

        # Remove this action entirely
        def remove_action():
            with button_lock:
                btn_info["actions"].remove(action)
                soft_upload(self.button_list)

            self.on_button_click(btn_info)
            win.destroy()

        tk.Button(btn_frame, text="Save", command=save_action).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", command=remove_action).pack(side="right", padx=5)

    def open_add_button_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("Add New Button")
        add_win.geometry("400x250")
        add_win.transient(self)
        add_win.grab_set()
        add_win.focus_force()

        # Calculate the maximum allowed button id.
        total_cells = self.ROWS * self.COLS
        max_allowed = (self.max_pages + 2) * total_cells - 1
        max_allowed = min(MAX_BUTTONS, max_allowed)
        
        ttk.Label(add_win, text="Button ID:", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        button_id_var = tk.StringVar()
        id_entry = tk.Entry(add_win, textvariable=button_id_var, font=('Arial', 10, 'bold'))
        id_entry.configure(insertbackground="white")
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_win, text="Image Path:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        image_path_var = tk.StringVar()
        # Instead of letting the user type the path, provide a button to open a file dialog.
        
        (ttk.Button(add_win, text="Select Image",
                    style="TButton",
                   command=lambda: image_path_var.set(self.select_image() or ""))
         .grid(row=2, column=1, padx=5, pady=5, sticky="w"))
        # Display the selected path:
        path_label = tk.Label(add_win, textvariable=image_path_var)
        path_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        def add_new_button():
            try:
                bid = int(button_id_var.get())
                if bid >= max_allowed:
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
            

            new_btn = {
                "button_id": bid,
                "actions": [],
                "image_path": img_path
            }
            with button_lock:
                self.button_list.append(new_btn)
                self.btn_map[bid] = new_btn
                print("added button!")

            self.create_button_grid()
            

            self.add_action_window(new_btn)
            button_id_var.set("")
            image_path_var.set("")
        
        ttk.Button(add_win, text="Add", command=add_new_button, style="TButton").grid(row=4, column=0, padx=5, pady=5)
        add_win.bind("<Return>", lambda event: add_new_button())
        (ttk.Button(add_win,
                  style="TButton",
                  text="Done",
                  command=lambda:[add_win.destroy(), self.create_button_grid()])
         .grid(row=4, column=1, padx=5, pady=5))

    
    def delete_button(self, btn_info):
        with button_lock:
            if btn_info in self.button_list:
                self.button_list.remove(btn_info)
                self.btn_map.pop(btn_info["button_id"])
                print("deleted button!")
                self.create_button_grid()
                for widget in self.info_frame.winfo_children():
                    widget.destroy()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.page_label.config(text=f"Page {self.current_page}")
            self.create_button_grid()

    def next_page(self):
        if self.current_page < self.max_pages:
            self.current_page += 1
            self.page_label.config(text=f"Page {self.current_page}")
            self.create_button_grid()

    def upload_changes(self):
        # Call your external function to process/upload changes.
        print("Uploading changes!")
        self.client = get_client()
        if self.client is None:
            print("[ERROR]: Client is none!")
            return None
        # write_updates()
        # print(self.button_list)
        gui_upload(self.client, self.button_list)

