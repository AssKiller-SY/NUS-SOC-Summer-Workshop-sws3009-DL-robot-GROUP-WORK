import serial
import cv2
from picamera2 import Picamera2, Preview, MappedArray
import threading
import time
import io
import logging
import socketserver
from http import server
from threading import Condition
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
import json
import requests

# 初始化串口通信
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# 初始化摄像头对象
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

# 用于停止线程的标志
stop_thread = False

green = (0, 255, 0)
red = (255, 0, 0)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2

def apply_timestamp(request):
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, "SWS3009B Day 1", (130, 470), font, scale, red, thickness)
        cv2.putText(m.array, timestamp, (0, 30), font, scale, green, thickness)

picam2.pre_callback = apply_timestamp

response_message = None

def capture_image():
    global response_message
    picam2.capture_file("classPhoto.jpg")
    print("Image captured and saved as classPhoto.jpg")

    url = "http://172.25.97.102:5000/upload"

    file_path = r'/home/pi13/Desktop/classPhoto.jpg'
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, files=files)
        
    response_message = response.json()
    print(response_message)


def serial_communication():
    global stop_thread
    ser.write("testing serial connection\n".encode('utf-8'))
    ser.write("sending via RPi\n".encode('utf-8'))
    
    try:
        while not stop_thread:
            user = input() + '\n'
            if user.strip() == 'p':
                capture_image()
            ser.write(user.encode('utf-8'))
            response = ser.readline()
            if response:
                print(response.decode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

def camera_preview():
    global stop_thread
    try:
        while not stop_thread:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop()

# 设置网络视频流传输
PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control the Robot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .video-stream {
            width: 640px;
            height: 480px;
            border: 1px solid #ccc;
            margin: 0 auto 20px;
        }
        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        .button-group {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        button {
            width: 60px;
            height: 60px;
            font-size: 18px;
            border: none;
            border-radius: 5px;
            background-color: #007bff;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        button:hover, button.active {
            background-color: #0056b3;
        }
        .row1 {
            display: flex;
            justify-content: center;
            gap: 80px;
        }
        .row2 {
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        .response-container {
            margin-top: 20px;
            font-size: 18px;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Control the Robot</h1>
    <div class="video-stream">
        <!-- Placeholder for video stream -->
        <img src="stream.mjpg" width="640" height="480" />
    </div>
    <div class="button-container">
        <div class="button-group">
            <div class="row1">
                <button id="btn-w" onclick="sendKey('w')">W</button>
                <button id="btn-x" onclick="sendKey('x')">X</button>
                <button id="btn-i" onclick="sendKey('i')">I</button>
            </div>
            <div class="row2">
                <button id="btn-a" onclick="sendKey('a')">A</button>
                <button id="btn-s" onclick="sendKey('s')">S</button>
                <button id="btn-d" onclick="sendKey('d')">D</button>
                <button id="btn-p" onclick="sendKey('p')">P</button>
                <button id="btn-j" onclick="sendKey('j')">J</button>
                <button id="btn-k" onclick="sendKey('k')">K</button>
                <button id="btn-l" onclick="sendKey('l')">L</button>
            </div>
        </div>
    </div>
    <div class="response-container" id="response-container">
        Response from server will appear here.
    </div>
    <script>
        function sendKey(key) {
            fetch('/send_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ key: key }),
            });
        }

        function highlightButton(key, highlight) {
            const button = document.getElementById('btn-' + key);
            if (button) {
                if (highlight) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            }
        }

        document.addEventListener('keydown', function(event) {
            const key = event.key.toLowerCase();
            if (['w', 'x', 'i', 'a', 's', 'd', 'p', 'j', 'k', 'l'].includes(key)) {
                sendKey(key);
                highlightButton(key, true);
            }
        });

        document.addEventListener('keyup', function(event) {
            const key = event.key.toLowerCase();
            if (['w', 'x', 'i', 'a', 's', 'd', 'p', 'j', 'k', 'l'].includes(key)) {
                highlightButton(key, false);
            }
        });

        function fetchResponse() {
            fetch('/response')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('response-container').textContent = JSON.stringify(data);
                })
                .catch(error => console.error('Error fetching response:', error));
        }

        setInterval(fetchResponse, 1000);
    </script>
</body>
</html>


"""



class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/response':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            global response_message
            self.wfile.write(json.dumps(response_message).encode('utf-8'))
        else:
            self.send_error(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/send_key':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            key = json.loads(post_data)['key']
            if(key == 'p'):
                capture_image()
            ser.write((key + '\n').encode('utf-8'))
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# 创建并启动串口通信线程
serial_thread = threading.Thread(target=serial_communication)
serial_thread.start()

# 启动摄像头预览
picam2.start_preview(Preview.NULL)  # 改为不显示预览
picam2.start()

output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

# 启动网络视频流服务器
server_thread = threading.Thread(target=lambda: StreamingServer(('', 8000), StreamingHandler).serve_forever())
server_thread.start()

# 当用户按下 Ctrl+C 时，设置停止标志并等待线程结束
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    stop_thread = True
serial_thread.join()
picam2.stop_recording()
