from gpiozero import LED, Button
import logging
import picamera
import random
import signal
import socket
import sounddevice as sd
import soundfile as sf
import time

HOST = '0.0.0.0'
PORT = 9876

# socket start
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handler(signum, frame):
    print('\nCTRL-C was pressed. Terminating the program.\n')
    camera.stop_recording()
    camera.close()
    server_socket.close()
    call_light.off()
    exit(1)

signal.signal(signal.SIGINT, handler)

class Sound():
    def __init__(self):
        self.data, self.fs = sf.read(self._get_ringbell_filename())
        print("Sound init'd")
    
    def play_ring_tone(self):
        sd.play(self.data, self.fs)
        sd.wait()

    def _get_ringbell_filename(self):
        bell_num = random.choice([1, 2, 3])
        return '/home/pi/doorbell-{}.wav'.format(bell_num)

class Camera:
    def __init__(self):
        self._handle = picamera.PiCamera()
        self._setupCamera()
        print("Camera init'd")

    def _setupCamera(self):
        self._handle.resolution = (1280, 960)
        self._handle.framerate = 24
        self._handle.exposure_mode = 'auto'
        self._handle.meter_mode = 'spot'

    def record(self, cf):
        self._handle.start_recording(cf, format='h264')

    def is_recording(self):
        return self._handle.recording

class Belldops:
    def __init__(self):
        self._call_button = Button(12)
        self._call_light = LED(14)
        self._camera = Camera()
        self._sound = Sound()

    def run(self):
        try:
             # application loop
            with server_socket:
                server_socket.bind((HOST, PORT))
                server_socket.listen()

                while True:
                    if self._call_button.is_pressed:
                        self._call_light.on()
                        self._sound.play_ring_tone()

                        conn, addr = server_socket.accept()
                        print(f"Connected by {addr}")
                        cf = conn.makefile('wb')

                        if not self._camera.is_recording():
                            self._camera.record(cf)

                        self._call_light.off()
        finally:
            print("All done")


if __name__ == "__main__":
    belldops = Belldops()
    belldops.run()
