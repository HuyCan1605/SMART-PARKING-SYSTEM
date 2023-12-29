import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import paho.mqtt.client as mqtt
import paho.mqtt.client as mqtt
import time
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter

cred = credentials.Certificate("/home/pi/Documents/Detect_plate/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def on_connect(client, userdata, flags, rc):
   global flag_connected
   flag_connected = 1
   client_subscriptions(client)
   print("Connected to MQTT server")

def on_disconnect(client, userdata, rc):
   global flag_connected
   flag_connected = 0
   print("Disconnected from MQTT server")
   
def update_parking_time_to_user_history(plate_number, day_in, time_in, slot, zone):
    user_ref = db.collection("user").where(filter=FieldFilter("plate_number", "==", plate_number)).limit(1)
    docs = user_ref.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
        time_out = datetime.datetime.now().time().strftime("%H:%M:%S")
        day_out = datetime.datetime.now().date()
        user_doc_ref = doc.reference

        data = {
            "day_in": day_in,
            "day_out": str(day_out),
            "time_in": time_in,
            "time_out": str(time_out),
            "slot": slot
        }
        parking_history_ref = user_doc_ref.collection("parking_history")
        if not parking_history_ref.get():
            parking_history_ref.document().create(data) 
        else:    
            parking_history_db = user_doc_ref.collection("parking_history").document()            
            parking_history_db.set(data)

def update_parking_slot_history(plate_number, day_in, time_in, slot, zone):
    time_out = datetime.datetime.now().time().strftime("%H:%M:%S")
    day_out = datetime.datetime.now().date()
    doc_ref = db.collection("admin").document("manage_slot_history").collection(slot).document()
    data = {
        "day_in": day_in,
        "day_out": str(day_out),
        "time_in": time_in,
        "time_out": str(time_out),
        "slot": slot,
        "plate_number": plate_number,
        "zone": zone
    }
    doc_ref.set(data)
        
       
def callback_rpi_broadcast2(client, userdata, msg):
    message = str(msg.payload.decode('utf-8'))
    print(message)
    slot = message
    
    if message[0] == "A":
        zone= "Alpha"
    elif message[0] == "B":
        zone = "Beta"
    slot_ref = db.collection("parking").document(zone).get().to_dict()

    if slot in slot_ref:
        data = slot_ref[slot]
        plate_number = data.get("plate_number")
        print(plate_number)
        if plate_number != "":
            day_in = data.get("day_in")
            time_in = data.get("time_in")
            update_parking_time_to_user_history(plate_number, day_in, time_in, slot, zone)
            update_parking_slot_history(plate_number, day_in, time_in, slot, zone)
    
    reset_data = { slot:{
        "plate_number": "",
        "has_car": str("0"),
        "time_in": "",
        "day_in": "",
        "warning": False}
        }
    doc_ref = db.collection("parking").document(zone)
    doc_ref.set(reset_data, merge = True)
    
    

def client_subscriptions(client):
    client.subscribe("rpi/broadcast2")

client = mqtt.Client("rpi_client3") #this should be a unique name
flag_connected = 0

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.message_callback_add('rpi/broadcast2', callback_rpi_broadcast2)
client.connect('127.0.0.1',1883)
# start a new thread
client.loop_start()
client_subscriptions(client)
print("......client setup complete............")


while True:
    time.sleep(4)
    if (flag_connected != 1):
        print("trying to connect MQTT server..")
