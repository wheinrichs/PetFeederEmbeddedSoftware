# Automatic Pet Feeder Project

This repository contains the necessary Raspberry Pi configuration and embedded software files to run the [Automatic Pet Feeder Project](https://www.winstonheinrichs.com/overview.html).

## Overview

The project uses a Raspberry Pi 4b to control a motor for dispensing food, recording and managing video feeds, and securely streaming live video. Configuration files for system services, cron jobs, and `rc.local` are included in the `ExampleSystemFiles` folder and should be implemented in the appropriate locations on the user's Raspberry Pi.

## Prerequisites

Before setting up the project, ensure the following dependencies are configured:

1. **Rclone for Google Drive Integration**  
   Follow the instructions [here](https://rclone.org/drive/) to set up Rclone with a Google Drive folder.

2. **Cloudflare Tunnel for Secure Streaming**  
   Set up the Cloudflare tunnel using the `cloudflared` binary by following the directions [here](https://github.com/cloudflare/cloudflared).

---

## Embedded Software Structure

The software is divided into the following components:

### 1. **Motor Control**
- **File:** `webMotorControl.py`  
- **Function:** Retrieves user preferences and controls motor movement.  
- **Startup Configuration:** Add this script to `rc.local` to run it on startup.

### 2. **Camera Control**
- **File:** `liveStreamVideoRecordVideo.py`  
- **Function:**  
  - Provides a live camera feed.  
  - Detects motion and records videos.  
  - Converts and uploads recorded videos to Google Drive.  
- **Startup Configuration:** Add this script to `rc.local` to run it on startup.

### 3. **Live Stream Tunnel**
- **Function:**  
  - Uses Cloudflare to create a secure tunnel to a custom subdomain (e.g., `https://stream.jarvisfeeders1234.win/`).  
  - Enables token-based security for live streaming access.  
- **Startup Configuration:**  
  - Configure the tunnel as a system service (`cloudflared.service`) to connect automatically on startup.

### 4. **Google Drive Configuration**
- **Function:**  
  - Mounts a Google Drive folder using Rclone for storage.  
- **Startup Configuration:**  
  - Set up the connection as a system service (`rclone@GoogleDrive.service`) to mount the folder on startup.

### 5. **Google Drive File Management**
- **File:** `manageDriveFiles.py`  
- **Function:**  
  - Deletes old recorded motion events from Google Drive (keeps the last 4 days of footage).  
- **Schedule Configuration:**  
  - A cron job is set up to run this script daily at 12:01 AM. Configuration details are in the `CronJobFiles.md` file.

---

## Folder Structure

- `ExampleSystemFiles/`: Contains example configuration files for system services, cron jobs, and `rc.local`.  
- `FlaskMotorControl/`: Contains the motor control and web server files. 
- `streamVideoServer/`: Contains camera feed and google drive management files. 

---

## Getting Started

1. Clone the repository to your Raspberry Pi.
2. Set up each component following the instructions in the respective sections above.
3. Test the system to ensure all services and scripts function as expected.

For additional details or troubleshooting, visit the [project overview](https://www.winstonheinrichs.com/overview.html).

---
