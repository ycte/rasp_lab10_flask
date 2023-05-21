"""
File: chapter03/flask_api_server.py

A HTTP RESTFul API server to control an LED built using Flask-RESTful.

Dependencies:
  pip3 install gpiozero pigpio flask-restful

Built and tested with Python 3.7 on Raspberry Pi 4 Model B
"""
import random
import logging
from flask import Flask, request, render_template                                    # (1)
from flask_restful import Resource, Api, reqparse, inputs                            # (2)
from gpiozero import PWMLED, Device                                                  # (3)
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import OutputDevice as DC
from gpiozero import Motor
from signal import pause
from time import sleep

# Initialize Logging
logging.basicConfig(level=logging.WARNING)  # Global logging configuration
logger = logging.getLogger('main')  # Logger for this module
logger.setLevel(logging.INFO) # Debugging for this file.


# Initialize GPIOZero
Device.pin_factory = PiGPIOFactory() #set GPIOZero to use PiGPIO by default

# Flask & Flask-RESTful instance variables
app = Flask(__name__) # Core Flask app.                                              # (4)
api = Api(app) # Flask-RESTful extension wrapper                                     # (5)


# Global variables
LED_GPIO_PIN = 17
motorSpeed = Motor(20,21)
led = None # PWMLED Instance. See init_led()
state = {                                                                            # (6)
    'level': 50 # % brightless of LED.
}
motorState = {
    'level': 50
}
temState = {
    'tem':0
}
cvState = {
    'img_stream': 10
}
img_path = '/home/pi/Yunxi/lab10_camera/2.png'

"""
GPIO Related Functions
"""
def init_led():
    """Create and initialise an PWMLED Object"""
    global led
    led = PWMLED(LED_GPIO_PIN)
    led.value = state['level'] / 100                                                 # (7)

def motor():
    # speed = 0.01 - (100/2 - motorState['level'])*0.01/100
    speed = motorState['level'] / 100.0
    print(speed)
    
    motorSpeed.forward(speed)
    # while True:
    #     Af.on()
    #     sleep(speed)
    #     Af.off()
    #     sleep(0.01)

def cv():
    import cv2
    from datetime import datetime
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    timestamp = datetime.now().isoformat()
    cv2.imwrite('%s.jpg' % timestamp, frame,[int(cv2.IMWRITE_JPEG_QUALITY),100])
    print("ok!")
    return '%s.jpg' % timestamp

def getTem():
    return random.randint(0,50)
def return_img_stream(img_local_path):
    """
    工具函数:
    获取本地图片流
    :param img_local_path:文件单张图片的本地绝对路径
    :return: 图片流
    """
    import base64
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream
"""
Flask & Flask-Restful Related Functions
"""
# @app.route applies to the core Flask instance (app).
# Here we are serving a simple web page.
@app.route('/', methods=['GET'])                                                     # (8)
def index():
    """Make sure inde.html is in the templates folder
    relative to this Python file."""
    
    img_stream = return_img_stream(img_path)
    return render_template('index_api_client.html', pin=LED_GPIO_PIN)                # (9)


class MotorControl(Resource):  # (10)

    def __init__(self):
        self.args_parser = reqparse.RequestParser()                                  # (11)

        self.args_parser.add_argument(
            name='level',  # Name of arguement
            required=True,  # Mandatory arguement
            type=inputs.int_range(0, 100),  # Allowed range 0..100                   # (12)
            help='Set motor speed {error_msg}',
            default=None)


    def get(self):
        return motorState  # (13)



    def post(self):
        global motorState                                                                 # (14)

        args = self.args_parser.parse_args()                                         # (15)

        # Set PWM duty cycle to adjust brightness level.
        motorState['level'] = args.level  
        motor()                                                # (16)                                          # (17)
        logger.info("Motor speed is " + str(motorState['level']))

        return motorState                                                                 # (18)

api.add_resource(MotorControl, '/motor')
                                              # (19)
class TemControl(Resource):  # (10)

    def __init__(self):
        self.args_parser = reqparse.RequestParser()                                  # (11)

        self.args_parser.add_argument(
            name='tem',  # Name of arguement
            required=True,  # Mandatory arguement                  # (12)
            help='Get tempurature {error_msg}',
            default=None)


    def get(self):
        temState['tem'] = getTem()
        return temState  # (13)



    def post(self):
        """Handles HTTP POST requests to set LED brightness level."""
        global temState                                                                 # (14)

        args = self.args_parser.parse_args()                                         # (15)

        # Set PWM duty cycle to adjust brightness level.
        state['level'] = args.level                                                  # (16)
        led.value = state['level'] / 100                                             # (17)
        logger.info("LED brightness level is " + str(state['level']))

        return temState  
api.add_resource(TemControl, '/temperature')


class LEDControl(Resource):  # (10)

    def __init__(self):
        self.args_parser = reqparse.RequestParser()                                  # (11)

        self.args_parser.add_argument(
            name='level',  # Name of arguement
            required=True,  # Mandatory arguement
            type=inputs.int_range(0, 100),  # Allowed range 0..100                   # (12)
            help='Set LED brightness level {error_msg}',
            default=None)


    def get(self):
        """ Handles HTTP GET requests to return current LED state."""
        return state  # (13)



    def post(self):
        """Handles HTTP POST requests to set LED brightness level."""
        global state                                                                 # (14)

        args = self.args_parser.parse_args()                                         # (15)

        # Set PWM duty cycle to adjust brightness level.
        state['level'] = args.level                                                  # (16)
        led.value = state['level'] / 100                                             # (17)
        logger.info("LED brightness level is " + str(state['level']))

        return state  

# Initialise Module.
init_led()
# Register Flask-RESTful resource and mount to server end point /led
api.add_resource(LEDControl, '/led')      


# CV
class CVControl(Resource):  

    def __init__(self):
        print("init cv")

    def get(self):
        global img_path, cvState
        img_path = cv()
        print('get cv success'+img_path)
        cvState['img_stream'] = 0
        cvState['level'] = return_img_stream(img_path)
        return cvState

    def post(self):
        global img_path,cvState                                                                                                # (15)
        img_path = cv()
        print('post cv success'+img_path)
        cvState['img_stream'] = 0
        cvState['level'] = return_img_stream(img_path)
        return cvState  

api.add_resource(CVControl, '/opencv') 

if __name__ == '__main__':

    # If you have debug=True and receive the error "OSError: [Errno 8] Exec format error", then:
    # remove the execuition bit on this file from a Terminal, ie:
    # chmod -x flask_api_server.py
    #
    # Flask GitHub Issue: https://github.com/pallets/flask/issues/3189

    app.run(host="0.0.0.0", debug=True)                                              # (20)
