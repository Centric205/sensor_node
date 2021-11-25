import socket
import sys
import time
import math
import threading
import datetime
#import busio
#import digitalio
#import board
#import RPi.GPIO as GPIO
#import adafruit_mcp3xxx.mcp3008 as MCP
#from adafruit_mcp3xxx.analog_in import AnalogIn

################TCP SEND SETUP###########################

#TODO Add code to setup the tcp connection with the correct IP and same port as the tcp_server on the other pi
    #Test this locally before trying to deploy via balena using test messages instead of ADC values
    #Use localmode when deploying to balena and use the advertised local address (using public IPs is possible but more complicated to configure due to the security measures BalenaOS imposes by default.  These are a good thing for real world deployment but over complicate the prac for the immediate purposes

PROGRESS = False
THREAD_STATE = None
SERVER = "127.0.1.1"
PORT = 5000
HEADER = 64
FORMAT = "utf-8"
ADDRESS = (SERVER, PORT)
DISCONNECT_MESSAGE = "DISCONNECTED!"

f = open("../../multicontainer-server/data/adclog.txt", "w+")

file = open('../../multicontainer-server/data/sensorlog.txt', "w+")

state = open('../../multicontainer-server/data/status.txt', 'w+')

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDRESS)

def send(mess):
    message = mess.encode()
    mesg_length = len(message)
    send_length = str(mesg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    

    print("Sensor Node it awake\n")     #Print statements to see what's happening in balena logs
    f.write("Sensor Node it awake\n")   #Write to file statements to see what's happening if you ssh into the device and open the file locally using nano
    f.flush()
   # client.send(b'Sensor Node it awake\n')   #send to transmit an obvious message to show up in the balena logs of the server pi
    client.send(send_length)
    client.send(message)





##################ADC Setup##############################

#TODO using the adafruit circuit python SPI and MCP libraries setup the ADC interface
#Google will supply easy to follow instructions 

# global variables
spi = None
cs = None
mcp = None
chan1 = None
chan2 = None
switch = 17
just = 0

# creates the spi bus
def createSPIBus():
    return busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# creates the cs (chip select)
def createChipset():
    return digitalio.DigitalInOut(board.D5)

# creates the mcp object
def createMCP():
    return MCP.MCP3008(createSPIBus(), createChipset())

def createAnalogInput():
    temp = AnalogIn(createMCP(), MCP.P1)
    ldr = AnalogIn(createMCP(), MCP.P2)
    return temp, ldr

def callback_method():
    print("falling edge detected on pin 17")

def gpioSetup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # If your pin is set to use pull up resistors
    # Connect a button between <channel> and GND
    GPIO.add_event_detect(switch, GPIO.FALLING, callback=callback_function(), bounceTime=200)

def exit():
    GPIO.cleanup()

# Converts the adc value to temperature in degrees celcius
def convert_to_temperature(analogIn):
    millivolts = analogIn.value * (analogIn.voltage * 1000/65535)
    return (millivolts - 500) / 10

def send_adc_values():
    start = time.time()
    thread = threading.Timer(10.0, send_adc_values)
    thread.daemon = True    # Daemon threads exit when the program does
    thread.start()

    end = time.time()
    temp, ldr = createAnalogInput()

    _time_ = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')

    send(_time_) # Data and time of each iteration
    send("LDR") # Command to tell the server that next data is from LDR
    send(ldr)
    send("TEMP")  # Command to tell the server that next data is from TEMP
    send(temp)    # Sends raw temperature values
    send(convert_to_temperature(temp))  # Sends temp values in degree celcius unit
    THREAD_STATE = thread.is_alive  # updates thread status

    while PROGRESS:
        thread.wait()  # PROGRESS IS TRUE IT WILL PAUSE THE THREAD FROM SAMPLING



# Makes use of a thread that prints results every 10 seconds
def print_results():
    
    start = time.time()
    thread = threading.Timer(10.0, print_results)
    thread.daemon = True    # Daemon threads exit when the program does
    thread.start()

    end = time.time()
    temp, ldr = createAnalogInput()
    global just
    if (just == 0):
        just = 1
        print(f"{math.ceil((10 - ((end - start)%10))*0)}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")
        send(f"{math.ceil((10 - ((end - start)%10))*0)}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")
    elif(just == 1):
        just = 2
        print(f"{math.ceil((10 - ((end - start)%10)))}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")
        send(f"{math.ceil((10 - ((end - start)%10)))}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")
    else:
        print(f"{math.ceil((10 - ((end - start)%10))+10)}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")
        send(f"{math.ceil((10 - ((end - start)%10))+10)}s\t <{temp.value}>\t <{math.ceil(convert_to_temperature(temp))}> C  <{ldr.value}>\t")



# ===================== Just Testing Mayne =========================
def test_send():
    dul = ["BLACK CLOVER","DBZ","DEATH NOTE ","POKEMON ","GOD EATER ","YU-GI-OH ","RICK & MORTY ","PARASITE ","ONE PUNCH "]
    for i in range(len(dul)):
        send(dul[i])

# Hanldles incoming messages from the web server
def handle_server():
    print("Connected")
    connect = True
    while connect:
        date_len = client.recv(HEADER).decode(FORMAT)
        print("rizzy", date_len)
        data = None
        if date_len:
            if not isinstance(date_len, str):
                date_len = int(date_len)
                data = client.recv(date_len).decode(FORMAT)
            
            print("Result  ", data )
            if date_len == "STATUS":
                state.write(THREAD_STATE)
            elif date_len == "SENDOFF":
                PROGRESS = True
            else:
                test_send()
        else:
            connect = False
    client.close()

# Starts the handle_server function
def start():
    receive_thread = threading.Thread(target=handle_server)
    receive_thread.start()

# Same as above, but was just testing
def test_start():
    recv_th = threading.Thread(target=test_send)
    recv_th.start()

#########################################################

#print("Sensor Node it awake\n")     #Print statements to see what's happening in balena logs
#f.write("Sensor Node it awake\n")   #Write to file statements to see what's happening if you ssh into the device and open the file locally using nano
#f.flush()
#s.send(b'Sensor Node it awake\n')   #send to transmit an obvious message to show up in the balena logs of the server pi

file.write("Runtime\t Temp Reading\t Temp\t  Light Reading.\n")
file.flush()
#print("Runtime\t Temp Reading\t Temp\t  Light Reading.")

while(True):
   



    #TODO add code to read the ADC values and print them, write them, and send them
    

   #test_start()
   start()
   # print_results()
   #test_send()
   time.sleep(5)


