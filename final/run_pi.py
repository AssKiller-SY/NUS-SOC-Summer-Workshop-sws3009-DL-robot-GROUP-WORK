#!/usr/bin/python3

# This script combines MJPEG streaming and socket communication with serial device.

import io
import logging
import socket
import socketserver
import serial
import time
from http import server
from threading import Condition, Thread
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
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
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def listen_and_forward(server_socket, ser, address, is_first):
    while True:
        print(f"Waiting for connection from {address}...")
        connection, client_address = server_socket.accept()
        try:
            print(f"Connection from {client_address}")
            while True:
                data = connection.recv(1024)
                if data:
                    command = data.decode('utf-8')
                    print(f"Received data: {command}")
                    if (command.strip().lower() == 'start1' or command.strip().lower() == 'start2') and is_first:
                        print("Received 'start' command, switching port")
                        ser.write(data)
                        connection.close()
                        server_socket.close()
                        return
                    else:
                        response = ser.readline()
                        if response:
                            print(f"Serial device response: {response.decode('utf-8')}")
                            connection.sendall(response)
                else:
                    print(f"Connection from {client_address} closed")
                    break
        finally:
            connection.close()

def communicate_with_server(ser):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('172.25.109.5', 12346)) #本机地址
    while True:
        server_data = server_socket.recv(1024)
        if server_data:
            print(f"Received message from server: {server_data.decode('utf-8')}")
            ser.write(server_data)
            if server_data.decode() == 'end':
                break
    server_socket.close()

def main():
    # Initialize serial port
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    
    # MJPEG streaming setup
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    global output
    output = StreamingOutput()
    picam2.start_recording(MJPEGEncoder(), FileOutput(output))
    
    # Start MJPEG server in a separate thread
    address = ('', 8000)
    mjpeg_server = StreamingServer(address, StreamingHandler)
    mjpeg_thread = Thread(target=mjpeg_server.serve_forever)
    mjpeg_thread.start()

    # Socket communication setup
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    initial_address = ('172.25.96.245', 12345) #树莓派地址
    server_socket.bind(initial_address)
    server_socket.listen(5)
    print(f"Server started, listening on port {initial_address[1]}")

    # First listen and forward
    listen_and_forward(server_socket, ser, initial_address, is_first=True)

    # Continue communication with server
    communicate_with_server(ser)

    # Stop MJPEG server and close serial port
    mjpeg_server.shutdown()
    picam2.stop_recording()
    ser.close()

if __name__ == "__main__":
    main()
