from iotknit import *

led1Status = False

init("192.168.1.68")  # use a MQTT broker on localhost

prefix("led")  # all actors below are prefixed with /led


def button1Callback(msg):

   print("received:", msg)

   
button1 = subscriber("test")  # create a Thingi interface that can have
                                 # subscribes only to button/button1
button1.subscribe_change(callback=button1Callback)

run()  # you can also do a while loop here call process() instead