import paho.mqtt.client as mqtt
import time
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("/home/pi/Documents/Detect_plate/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def on_publish(client, userdata, mid):
    print("message published")

def on_connect(client, userdata, flags, rc):
   global flag_connected
   flag_connected = 1
   client_subscriptions(client)
   print("Connected to MQTT server")

def on_disconnect(client, userdata, rc):
   global flag_connected
   flag_connected = 0
   print("Disconnected from MQTT server")
   
# a callback functions 
def callback_esp32_sensor1(client, userdata, msg):
    print('ESP sensor1 data: ', msg.payload.decode('utf-8'))
    message = str(msg.payload.decode('utf-8'))
    slot_has_car = int(message)
    data = ""
    if slot_has_car == 1:
        time_in = datetime.datetime.now().time().strftime("%H:%M:%S")
        day_in = datetime.datetime.now().date()
        data = {"A1":{"has_car": str("1"),
        "time_in": str(time_in),
        "day_in": str(day_in)}
        }
    elif slot_has_car == 0:
        try:
            client.publish(topic='rpi/broadcast2', payload=str("A1"), qos=0)
            time.sleep(1)
        except Exception as e:
            print (e) 
    elif slot_has_car == 2:
        data = {"A1":{"warning": True}}    

    doc_ref = db.collection("parking").document("Alpha")
    doc_ref.set(data, merge = True)
    

def client_subscriptions(client):
    client.subscribe("esp32/#")

client = mqtt.Client("rpi_client2") #this should be a unique name
flag_connected = 0

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.message_callback_add('esp32/A1', callback_esp32_sensor1)


client.connect('127.0.0.1',1883)
# start a new thread
client.loop_start()
client_subscriptions(client)
print("......client setup complete............")


while True:
    time.sleep(4)
    if (flag_connected != 1):
        print("trying to connect MQTT server..")
