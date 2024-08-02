import requests
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
LOG_FILE_PATH = '/home/ubuntu/logfiles/cef-log.log'
STATE_FILE_PATH = '/home/ubuntu/logfiles/cef-log.state'
WEBHOOK_URL = 'https://webhook-collector.AWS-REGION.prod.alienvault.cloud/api/1.0/webhook/push' # change this to match your WEBHOOK URL from the USMA web interface. 
API_KEY = 'your_api_key_goes_here'
LOG_WATCHER_OUTPUT = '/home/ubuntu/logfiles/logwatcher_output.log'

class LogHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_position = self.load_state()

    def load_state(self):
        """Load the last processed byte position from the state file."""
        try:
            with open(STATE_FILE_PATH, 'r') as state_file:
                return int(state_file.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_state(self, position):
        """Save the current position to the state file."""
        with open(STATE_FILE_PATH, 'w') as state_file:
            state_file.write(str(position))

    def on_modified(self, event):
        if event.src_path == LOG_FILE_PATH:
            with open(LOG_FILE_PATH, 'r') as log_file:
                log_file.seek(self.last_position)
                new_lines = log_file.readlines()
                for line in new_lines:
                    send_log_to_webhook(line.strip())
                self.last_position = log_file.tell()
                self.save_state(self.last_position)

def send_log_to_webhook(log_message):
    headers = {
        'Content-Type': 'application/json',
        'API_KEY': API_KEY
    }
    data = [{
        'event': log_message
    }]
    response = requests.post(WEBHOOK_URL, json=data, headers=headers)
    with open(LOG_WATCHER_OUTPUT, 'a') as log_file:
        if response.status_code == 200:
            log_file.write(f"Successfully sent log: {log_message}\n")
        else:
            log_file.write(f"Failed to send log: {log_message}, Status Code: {response.status_code}\n")

def monitor_log_file():
    # Check if log file exists
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_WATCHER_OUTPUT, 'a') as log_file:
            log_file.write(f"Log file does not exist: {LOG_FILE_PATH}\n")
        return
    
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(LOG_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    monitor_log_file()
