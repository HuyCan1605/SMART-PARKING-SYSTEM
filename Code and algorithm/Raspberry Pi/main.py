import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pathlib
import paho.mqtt.client as mqtt
import time
import datetime
import read_and_extract_plate
from google.cloud.firestore_v1.base_query import FieldFilter, Or

cred = credentials.Certificate("/home/pi/Documents/Detect_plate/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# K?t n?i t?i Firestore
db = firestore.client()

def on_publish(client, userdata, mid):
    print("message published")

client = mqtt.Client("rpi_client")
client.on_publish = on_publish
client.connect('127.0.0.1', 1883)
client.loop_start()

def send_data_to_esp(message):
    try:
        client.publish(topic='rpi/broadcast', payload=str(message), qos=0)
        time.sleep(1)
    except Exception as e:
        print (e)

def update_car_not_register(license_plates):
    time_in = datetime.datetime.now().time()
    day_in = datetime.datetime.now().date()
    data = {
    license_plates: {"slot": "A1", "time_in": str(time_in),"day_in": str(day_in)}
    }
    db.collection("admin").document("manage_car_not_resgister").set(data, merge = True)

def get_lastest_img_path():
    folder_path = "/var/www/html/uploads"

    #lay duong dan them vao moi nhat
    file_list = os.listdir(folder_path)
    sorted_files = sorted(file_list, key = lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)
    first_file_path = os.path.join(folder_path, sorted_files[0])
    return first_file_path        

def get_all_plate_from_firestore():
    doc_ref = db.collection("user").stream()
    plate_number = []
    for doc in doc_ref :
        doc_dict = doc.to_dict()
        if 'plate_number' in doc_dict:  
            plate_number.append(doc_dict['plate_number'])
    return plate_number
    


def update_car_data_to_firestore(plate_number):
    data = {
    "A1": {"plate_number": str(plate_number), "warning": False}
    }
    db.collection("parking").document("Alpha").set(data, merge = True)

if __name__ == "__main__":
    image_path = get_lastest_img_path()
    license_plates , is_wrong_plate = read_and_extract_plate.read_plate_number(image_path)
    if is_wrong_plate:
        send_data_to_esp(is_wrong_plate) 
        print("wrong plate")
    else:
        send_data_to_esp(is_wrong_plate)
        print("right plate ")
        update_car_data_to_firestore(license_plates)
        db_plate_number = get_all_plate_from_firestore()
        if license_plates not in db_plate_number:
            update_car_not_register(license_plates)
