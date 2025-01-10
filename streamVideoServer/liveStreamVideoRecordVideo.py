from picamera2 import Picamera2
import cv2
from flask import Flask, Response, request, jsonify
import jwt
import os
import threading
import datetime
import time
import subprocess
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

# Picamera2 Initialization
picam2 = Picamera2()
framerate = 30
video_config = picam2.create_video_configuration(raw={"size":(1640,1232)},main={"size": (640, 480)}, controls={"FrameRate": framerate})
picam2.configure(video_config)

# Encoder and Outputs
encoder = H264Encoder(repeat=True, iperiod=15)
output2 = FileOutput()
encoder.output = [output2]
# picam2.start_encoder(encoder)  # Start the encoder
picam2.start()  # Start the camera

VIDEO_SAVE_DIR = "/home/winstonheinrichs/Documents/JarvisFeeder/streamVideoServer/RecordingBufferFolder"
if not os.path.exists(VIDEO_SAVE_DIR):
    os.makedirs(VIDEO_SAVE_DIR)

# Global recording state
global recording
recording = False
recording_lock = threading.Lock()

route_accessed = False
global previous_frame
previous_frame = None

latest_frame = None
frame_lock = threading.Lock()

condition = threading.Condition()

# Motion Detection Function
def motion_detected(frame, previous_frame, threshold=30):
    gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    non_zero_count = cv2.countNonZero(thresh)
    return non_zero_count > 10000

# Start Video Recording
def record_video(filename, duration=60):
    global recording
    with recording_lock:
        if recording:
            return
        recording = True

    print(f"Starting recording: {filename}")
    picam2.start_encoder(encoder)  # Start the encoder

    h264_path = f"{filename}.h264"
    mp4_path = f"{filename}.mp4"
    output2.fileoutput = h264_path

    try:
        output2.start()
        time.sleep(duration)
        output2.stop()
        print(f"Saved video: {h264_path}")

        # Convert H.264 to MP4 using ffmpeg (offloaded)
        threading.Thread(target=convert_and_move_video(mp4_path, h264_path), daemon=True).start()

        picam2.stop_encoder()  # Start the encoder
    except Exception as e:
        print(f"Error: {e}")
    finally:
        with recording_lock:
            recording = False

def convert_and_move_video(mp4_path, h264_path):
    try:
        subprocess.run([
                "ffmpeg", "-y", "-framerate", str(framerate), "-i", h264_path, "-c:v", "copy", "-r", str(framerate), mp4_path
            ])
        print("File converted")

        os.remove(h264_path)
        print("Temporary H.264 file removed.")

        destination_folder = "/home/winstonheinrichs/mnt/GoogleDrive"
        filename = os.path.basename(mp4_path)
        full_path = os.path.join(destination_folder, filename)
        subprocess.run(["rclone", "moveto", mp4_path, full_path])

        print("File moved")
    except Exception as e:
        print(f"Error: {e}")

def motion_and_stream():
    """Unified thread for motion detection and frame sharing."""
    global latest_frame, recording, previous_frame

    while True:
        # Capture the current frame
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Perform motion detection
        if previous_frame is not None and motion_detected(frame, previous_frame) and not recording:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = os.path.join(VIDEO_SAVE_DIR, f"motion_{timestamp}")
            threading.Thread(target=record_video, args=(video_filename, 60)).start()

        previous_frame = frame.copy()

        # Update the shared variable
        with condition:  # Ensure thread-safe access
            latest_frame = frame.copy()
            condition.notify_all()

        time.sleep(0.1)  # Reduce CPU usage

def generate_frames():
    """Generator for Flask streaming."""
    global latest_frame

    while True:
        with condition:  # Ensure thread-safe access
            condition.wait()
            frame = latest_frame

        if frame is None:
            time.sleep(0.1)
            continue

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# JWT Token Decorator
def token_required(f):
    def decorator(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorator

# Flask Route to Stream Video
@app.route('/')
@token_required
def video_feed():
    global route_accessed
    route_accessed = True
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Main
if __name__ == '__main__':
    # Start the unified motion detection and streaming thread
    motion_stream_thread = threading.Thread(target=motion_and_stream, daemon=True)
    motion_stream_thread.start()

    print("Starting Flask app and network stream...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
