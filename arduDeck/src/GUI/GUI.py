import tkinter as tk
from tkinter import ttk

from tkinter import filedialog, messagebox
from ..utils.btn_funcs import gui_upload, button_lock
from ..basic_comms import get_client, logger
from .macro_rec import KeyRecorder, rec_callback

#todo add id checking for add and update func
#todo preselect text in command args or register key inputs?

COMMAND_TYPES = ["HARD_KEY_PRESS", "SOFT_KEY_PRESS", "START_URL", "START_PROCESS"]

class StreamDeckGUI(tk.Tk):
    def __init__(self, button_list):
        super().__init__()
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
        self.bind("<Shift-KeyRelease>", lambda event: self.macro_rec_window())

        # Use grid to divide the window equally into left and right.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = tk.Frame(self, bg="gray")
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = tk.Frame(self, bg="lightgray")
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.create_left_frame()
        # Right frame: create a scrollable canvas.
        self.create_right_frame()
        self.create_button_grid()

    def create_left_frame(self):
        # Page navigation 
        nav_frame = tk.Frame(self.left_frame, height=20, bg="grey")
        nav_frame.pack(fill=tk.X, pady=5)

        tk.Button(nav_frame, text="<", command=self.prev_page).place(relx=.45, rely=.5, anchor="center")

        self.page_label = tk.Label(nav_frame, text="Page 0", bg="gray", fg="white")
        self.page_label.place(relx=.5, rely=.5, anchor="center")

        tk.Button(nav_frame, text=">", command=self.next_page).place(relx=.55, rely=.5, anchor="center")

        # Button grid container
        self.button_frame = tk.Frame(self.left_frame, bg="gray")
        self.button_frame.pack(padx=10, pady=100)

        # Add a button
        self.add_button_btn = tk.Button(self.left_frame, text="Add Button", command=self.open_add_button_window)
        self.add_button_btn.pack(pady=5)

    def create_right_frame(self):
        # Configure right_frame to have two rows: one for the canvas (expandable) and one for the fixed upload button.
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=0)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Create the canvas for the scrollable info_frame.
        self.canvas = tk.Canvas(self.right_frame, bg="lightgray")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Create a vertical scrollbar for the canvas.
        self.scrollbar = tk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the info widgets.
        self.info_frame = tk.Frame(self.canvas, bg="lightgray")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.info_frame, anchor="nw")

        # Bind the configuration event to update the scroll region.
        self.info_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))


        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Create the upload button in a fixed row (row 1) of right_frame.
        self.upload_btn = tk.Button(self.right_frame, text="Upload Changes", command=self.upload_changes)
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

                text = f"Button {global_idx}"
                # Create a button
                btn = tk.Button(self.button_frame,
                                text=text,
                                width=10,
                                height=3,
                                command=lambda info=button: self.on_button_click(info))
                btn.grid(row=row, column=col, padx=5, pady=5)
            else:
                # Else draw an empty button placeholder
                placeholder = tk.Button(self.button_frame,
                                    text="Empty",
                                    width=10,
                                    height=3,
                                    command=lambda: None,
                                    bg="darkgray")
                placeholder.grid(row=row, column=col, padx=5, pady=5)


    def on_button_click(self, btn_info):
        # When a non-empty button is pressed, display its info in the right info_frame.
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        title_label = tk.Label(self.info_frame, text=f"Button: {btn_info.get('button_id', 'Unknown')}",
                               font=("Arial", 12), bg="lightgray")
        title_label.pack(pady=5, padx=5, anchor="w")

        # Provide options: Add Action and Delete Button
        action_btn_frame = tk.Frame(self.info_frame, bg="lightgray")
        action_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(action_btn_frame, text="Add Action", command=lambda: self.add_action_window(btn_info)).pack(side=tk.LEFT, padx=5)
        tk.Button(action_btn_frame, text="Delete Button", command=lambda: self.delete_button(btn_info)).pack(side=tk.LEFT, padx=5)

        # Display existing actions
        actions_header = tk.Label(self.info_frame, text="Actions:", font=("Arial", 10, "underline"), bg="lightgray")
        actions_header.pack(pady=(10,5), padx=5, anchor="w")

        # List actions
        with button_lock:
            actions = btn_info.get("actions", [])

        if actions:
            for action in actions:
                action_text = f"Command: {action.get('command_id', 'N/A')}\nArgs: {action.get('command_args', [])}"
                act_btn = tk.Button(self.info_frame, text=action_text,
                                    wraplength=250, justify="center",
                                    command=lambda a=action, i=btn_info: self.edit_action_window(a, i))
                act_btn.pack(fill=tk.X, padx=5, pady=2, anchor="center")
        else:
            no_act_label = tk.Label(self.info_frame, text="No Actions Assigned", bg="lightgray")
            no_act_label.pack(pady=5, padx=5, anchor="w")

        # Display Image Path
        img_btn = tk.Button(self.info_frame, text=f"Image Path: {btn_info.get('image_path', 'N/A')}",
                            borderwidth=2, relief="groove", bg="white",
                            command=lambda: self.update_image_path(btn_info))
        img_btn.pack(pady=5, padx=5, fill=tk.X, anchor="w")
        
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

    def add_action_window(self, btn_info):
        # This window remains open until "Done" is pressed, allowing the user to add multiple actions.
        add_win = tk.Toplevel(self)
        add_win.title("Add Action")
        add_win.geometry("400x250")
        # Make this window transient with respect to the main application window.
        add_win.transient(self) 
        # Grab the focus so that it is modal.
        add_win.grab_set()
        # Force the window to come to the front.
        add_win.focus_force()


        # Row 1: Label and Combobox for Command Type.
        tk.Label(add_win, text="Command Type:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        cmd_id_var = tk.StringVar(value=COMMAND_TYPES[0])
        combobox = ttk.Combobox(add_win, textvariable=cmd_id_var, values=COMMAND_TYPES, state="readonly", width=28)
        combobox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(add_win, text="Command Args:", anchor="ne").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        cmd_args_text = tk.Text(add_win, wrap="word", width=30, height=4)
        cmd_args_text.grid(row=2, column=1, padx=5, pady=5)

        def add_action():
            with button_lock:
                actions = btn_info.get("actions", [])

                action_id = cmd_id_var.get()
                new_action = {"command_id": action_id, "command_args": [cmd_args_text.get("1.0", "end-1c")]}

                actions.append(new_action)
                btn_info["actions"] = actions

            # Clear the entry fields for the next action.
            cmd_id_var.set("")
            cmd_args_text.delete("1.0", "end")

            # Optionally, update the right frame to reflect the newly added action.
            self.on_button_click(btn_info)

        tk.Button(add_win, text="Add Action", command=add_action).grid(row=4, column=0, padx=5, pady=5)

        # "Done" button: closes the window.
        tk.Button(add_win, text="Return to HUB", command=add_win.destroy).grid(row=4, column=1, padx=5, pady=5)

    def macro_rec_window(self):
        mrw = KeyRecorder(self, rec_callback)

    def edit_action_window(self, action, btn_info):
        # Open a Toplevel window for editing an action.
        edit_win = tk.Toplevel(self)
        edit_win.title("Edit Action")
        edit_win.geometry("400x250")
        # Make this window transient with respect to the main application window.
        edit_win.transient(self) 
        # Grab the focus so that it is modal.
        edit_win.grab_set()
        # Force the window to come to the front.
        edit_win.focus_force()

        # Row 1: Label and Combobox for Command Type.
        tk.Label(edit_win, text="Command Type:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        cmd_id_var = tk.StringVar(value=action.get("command_type", COMMAND_TYPES[0]))
        combobox = ttk.Combobox(edit_win, textvariable=cmd_id_var, values=COMMAND_TYPES, state="readonly", width=28)
        combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Command Args: use a Text widget for multi-line input with wrapping.
        tk.Label(edit_win, text="Command Args:", anchor="ne").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        # Create a Text widget
        cmd_args_text = tk.Text(edit_win, wrap="word", width=30, height=5)
        # Insert current command args (convert to string if necessary)
        cmd_args_text.insert("1.0", str(action.get("command_args", "")))
        cmd_args_text.grid(row=1, column=1, padx=5, pady=5)

        # Create a frame for the buttons at the bottom.
        btn_frame = tk.Frame(edit_win)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        def save_changes():
            with button_lock:
                action["command_id"] = cmd_id_var.get()
                action["command_args"] = [cmd_args_text.get("1.0", "end-1c")]
                logger.debug("edited action!")
            edit_win.destroy()
            # Optionally, update the displayed actions.
            self.on_button_click(btn_info)
   

        def remove_action():
            # Remove the action from the button's action list.
            with button_lock:
                actions = btn_info.get("actions", [])
                if action in actions:
                    actions.remove(action)
                    btn_info["actions"] = actions
                    print("removed action!")
            edit_win.destroy()
            self.on_button_click(btn_info)

        save_btn = tk.Button(btn_frame, text="Save", width=12)
        remove_btn = tk.Button(btn_frame, text="Remove Action", width=12)
        save_btn.grid(row=2, column=0, padx=5, pady=10)
        remove_btn.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        # Set the commands
        save_btn.config(command=save_changes)
        remove_btn.config(command=remove_action)
        edit_win.bind("<Return>", lambda event: save_changes())

    def open_add_button_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("Add New Button")
        add_win.geometry("400x250")
        add_win.transient(self) 
        # Grab the focus so that it is modal.
        add_win.grab_set()
        # Force the window to come to the front.
        add_win.focus_force()

        # Calculate the maximum allowed button id.
        total_cells = self.ROWS * self.COLS
        max_allowed = (self.max_pages + 2) * total_cells - 1
        
        tk.Label(add_win, text="Button ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        button_id_var = tk.StringVar()
        tk.Entry(add_win, textvariable=button_id_var).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(add_win, text="Image Path:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        image_path_var = tk.StringVar()
        # Instead of letting the user type the path, provide a button to open a file dialog.
        
        tk.Button(add_win, text="Select Image", command=lambda: image_path_var.set(self.select_image() or "")).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        # Display the selected path:
        path_label = tk.Label(add_win, textvariable=image_path_var)
        path_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        def add_new_button():
            try:
                bid = int(button_id_var.get())
                if bid > max_allowed:
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
            
            # Create a new button entry with an empty actions list.
            new_btn = {
                "button_id": bid,
                "actions": [],
                "image_path": img_path
            }
            with button_lock:
                self.button_list.append(new_btn)
                self.btn_map[bid] = new_btn
                print("added button!")
            # Refresh the left grid
            self.create_button_grid()
            
            # Immediately open the add_action window to let the user add actions.
            self.add_action_window(new_btn)
            button_id_var.set("")
            image_path_var.set("")
        
        tk.Button(add_win, text="Add", command=add_new_button).grid(row=4, column=0, padx=5, pady=5)
        add_win.bind("<Return>", lambda event: add_new_button())
        tk.Button(add_win, text="Done", command=lambda:[add_win.destroy(), self.create_button_grid()]).grid(row=4, column=1, padx=5, pady=5)

    
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

