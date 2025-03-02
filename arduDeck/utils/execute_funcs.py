import subprocess
import webbrowser

def start_process(cmd_id, file_path):
    try:
        command = subprocess.Popen([file_path])
        res = command.communicate()
        if command.returncode != 0:
            raise subprocess.CalledProcessError
    except subprocess.CalledProcessError(command.returncode, file_path):
        print(f"START_PROCESS {cmd_id} failed")
        print(res[1])


def start_url(cmd_id, url):
    if webbrowser.open_new_tab(url):
        print(f"START_URL {cmd_id} successful")
    else:
        print(f"START_URL {cmd_id} failed")


ACT_DICT = {
    "START_PROCESS": start_process,
    "START_URL": start_url,
}

# path = path.rstrip('\r\n')
# escaped_path = path.encode('unicode_escape').decode()
# escaped_path = escaped_path.rstrip('\r\n')
# print(path)
# print(escaped_path)
# subprocess.Popen(escaped_path)