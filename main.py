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

# Class to handle speaking, playing
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

# Class to handle camera
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

    def stop(self):
        self._handle.stop_recording()
        self._handle.close()

    def is_recording(self):
        return self._handle.recording

# Main class
class Belldops:
    def __init__(self):
        self._call_button = Button(12)
        self._call_light = LED(14)
        self._camera = Camera()
        self._sound = Sound()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _sigint_handler(self, signum, frame):
        print('\nCTRL-C was pressed. Terminating the program.\n')

        self._camera.stop()
        self._call_light.off()

        self._server_socket.close()
        exit(1)

    def run(self):
        try:
            signal.signal(signal.SIGINT, self._sigint_handler)

             # application loop
            with self._server_socket:
                self._server_socket.bind((HOST, PORT))
                self._server_socket.listen()

                while True:
                    if self._call_button.is_pressed:
                        self._call_light.on()
                        self._sound.play_ring_tone()

                        conn, addr = self._server_socket.accept()
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
