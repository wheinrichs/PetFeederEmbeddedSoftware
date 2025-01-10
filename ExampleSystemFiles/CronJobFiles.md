To ensure that old videos are removed at the beginning of every day, the following CRON job needs to be added to the Raspberry Pi running the pet feeder.

Replace the following path with the absolute destination path of the manageDriveFiles.py program

```
01 0 * * * /usr/bin/python /home/winstonheinrichs/Documents/JarvisFeeder/streamVideoServer/manageDriveFiles.py
```