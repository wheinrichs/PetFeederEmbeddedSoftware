from time import sleep
from datetime import datetime, timedelta
import os
import subprocess


drive_file_location = "/home/winstonheinrichs/mnt/GoogleDrive"
days_of_footage_to_keep = 3

def delete_drive_files():
    dateCurrent = datetime.now()
    for filename in os.listdir(drive_file_location):
        file_path = os.path.join(drive_file_location, filename)
        if os.path.isfile(file_path):
            filedate = filename.split("_")[1]
            convertDate = datetime.strptime(filedate, "%Y%m%d")
            if dateCurrent - convertDate > timedelta(days=days_of_footage_to_keep+1):
                subprocess.run(["rclone", "delete", file_path])

if __name__ == '__main__':
    delete_drive_files()