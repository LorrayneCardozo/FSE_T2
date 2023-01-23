import RPi.GPIO as GPIO

class Forno:
    def __init__(self):
        GPIO.setwarnings(False)
    
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(23, GPIO.OUT)
        GPIO.setup(24, GPIO.OUT)

        self.aquecedor = GPIO.PWM(23, 1000)
        self.aquecedor.start(0)

        self.ventoinha = GPIO.PWM(24, 1000)
        self.ventoinha.start(0)

    def aquecer(self, pid):
        self.aquecedor.ChangeDutyCycle(pid)

    def resfriar(self, pid):
        self.ventoinha.ChangeDutyCycle(pid)