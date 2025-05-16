import queue

class HeaderData:
    def __init__(self, command_type, command_id, length, crc_value):
        self.command_type = command_type
        self.command_id = command_id
        self.length = length
        self.crc_value = crc_value
class PackageData:
    def __init__(self, header_data, contents):
        self.header_data = header_data
        self.contents = contents

gui_queue = queue.Queue()
def generate_gui_conn_update(update: str):
    gui_queue.put(update)