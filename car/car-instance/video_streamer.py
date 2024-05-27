import subprocess
import sys
import time

def stream_webcam(HOST):	
    try:
        _ = subprocess.check_output(["pidof", "mediamtx"]).decode().strip()
    except:
        sys.exit("RTSP server hasn't been started. Read HOW_TO_RUN.txt in /car folder")

    ffmpeg_command = [
        "ffmpeg",
        "-f", "v4l2",
        "-framerate", "60",
        "-re",
        "-stream_loop", "-1",
        "-video_size", "640x480",
        "-input_format", "mjpeg",
        "-i", "/dev/video0",
        "-c", "copy",
        "-f", "rtsp",
        f"rtsp://{HOST}:8554/video_stream"
    ]
    rtsp_stream = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rtsp_stream
